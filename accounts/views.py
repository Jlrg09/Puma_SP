from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import RegisterForm
from .models import CustomUser, Roles, Notification
from django import forms
from django.core.paginator import Paginator
from django.db import models
from .decorators import jefe_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse


class UserEditForm(forms.ModelForm):
	class Meta:
		model = CustomUser
		fields = ['approved', 'is_active', 'office']  

def is_jefe(user):
	return user.is_authenticated and user.is_jefe


@login_required
@jefe_required
def users_list(request):
	qs = CustomUser.objects.select_related('office').all()
	role = request.GET.get('role')
	office = request.GET.get('office')
	approved = request.GET.get('approved')
	active = request.GET.get('active')
	q = request.GET.get('q')

	if role:
		qs = qs.filter(role=role)
	if office:
		qs = qs.filter(office_id=office)
	if approved in ('0', '1'):
		qs = qs.filter(approved=(approved == '1'))
	if active in ('0', '1'):
		qs = qs.filter(is_active=(active == '1'))
	if q:
		qs = qs.filter(models.Q(username__icontains=q) | models.Q(email__icontains=q))

	qs = qs.order_by('date_joined')
	paginator = Paginator(qs, 10)
	users = paginator.get_page(request.GET.get('page', 1))

	from oficinas.models import Office
	offices = Office.objects.all()
	ctx = {
		'users': users,
		'roles': Roles,
		'offices': offices,
		'filters': {
			'role': role or '',
			'office': int(office) if office else '',
			'approved': approved or '',
			'active': active or '',
			'q': q or '',
		}
	}
	return render(request, 'accounts/users_list.html', ctx)


@login_required
@jefe_required
def user_edit(request, user_id):
	user = get_object_or_404(CustomUser, pk=user_id)
	if request.method == 'POST':
		form = UserEditForm(request.POST, instance=user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Usuario actualizado')
			return redirect('users_list')
	else:
		form = UserEditForm(instance=user)
	return render(request, 'accounts/user_edit.html', {'form': form, 'obj': user})


def register(request):
	if request.method == 'POST':
		form = RegisterForm(request.POST)
		if form.is_valid():
			user: CustomUser = form.save(commit=False)
			user.is_active = True  # activo para poder hacer login si se desea, pero no aprobado
			user.approved = False
			user.role = Roles.UNASSIGNED
			user.save()
			messages.success(request, 'Registro enviado. Espera aprobación del Jefe.')
			return redirect('waiting')
	else:
		form = RegisterForm()
	return render(request, 'accounts/register.html', {'form': form})


@login_required
def waiting(request):
	if request.user.approved:
		return redirect('home')
	return render(request, 'accounts/waiting.html')


@login_required
@jefe_required
def approve_user(request, user_id):
	target = get_object_or_404(CustomUser, pk=user_id)
	target.approved = True
	target.role = Roles.TECNICO  # Asignar automáticamente rol de técnico al aprobar
	target.save()
	messages.success(request, f'Usuario {target.username} aprobado y asignado como Técnico.')
	return redirect('users_list')

# Create your views here.


@login_required
def notifications_list(request):
	qs = Notification.objects.filter(recipient=request.user)
	qs = qs.order_by('-created_at')
	paginator = Paginator(qs, 10)
	page = request.GET.get('page', 1)
	notifications = paginator.get_page(page)
	return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
@require_POST
def notification_mark_read(request, notif_id):
	notif = get_object_or_404(Notification, pk=notif_id, recipient=request.user)
	if notif.read_at is None:
		notif.read_at = timezone.now()
		notif.save()
	return redirect('notifications_list')


@login_required
@require_POST
def notifications_mark_all_read(request):
	Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
	return redirect('notifications_list')


@login_required
def notifications_data(request):
	notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
	unread = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
	return JsonResponse({
		'unread': unread,
		'items': [
			{
				'id': n.id,
				'text': n.text,
				'ticket_id': n.ticket_id,
				'created_at': n.created_at.isoformat(),
			}
			for n in notifs
		]
	})


class ProfileForm(forms.ModelForm):
	class Meta:
		model = CustomUser
		fields = ['first_name', 'last_name', 'email', 'phone', 'id_type', 'id_number', 'birth_date']
		widgets = {
			'birth_date': forms.DateInput(attrs={'type': 'date'}),
			'first_name': forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
			'last_name': forms.TextInput(attrs={'placeholder': 'Tu apellido'}),
			'email': forms.EmailInput(attrs={'placeholder': 'tu@email.com'}),
			'phone': forms.TextInput(attrs={'placeholder': 'Tu número de teléfono'}),
			'id_number': forms.TextInput(attrs={'placeholder': 'Tu número de identificación'}),
			'id_type': forms.Select(attrs={'class': 'form-select'}),
		}
		labels = {
			'first_name': 'Nombres',
			'last_name': 'Apellidos', 
			'email': 'Correo electrónico',
			'phone': 'Teléfono',
			'id_type': 'Tipo de identificación',
			'id_number': 'Número de identificación',
			'birth_date': 'Fecha de nacimiento',
		}

	def clean_id_number(self):
		value = self.cleaned_data.get('id_number', '').strip()
		if not value.isdigit():
			raise forms.ValidationError('El número de identificación debe contener solo dígitos.')
		
		# Verificar unicidad excluyendo el usuario actual
		existing = CustomUser.objects.filter(id_number=value).exclude(pk=self.instance.pk)
		if existing.exists():
			raise forms.ValidationError('Este número de identificación ya está registrado por otro usuario.')
		return value


@login_required
def profile(request):
	if request.method == 'POST':
		form = ProfileForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
			return redirect('profile')
	else:
		form = ProfileForm(instance=request.user)
	
	return render(request, 'accounts/profile.html', {
		'form': form,
		'user': request.user
	})


@login_required
def change_password(request):
	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Mantener la sesión activa
			messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
			return redirect('profile')
	else:
		form = PasswordChangeForm(request.user)
	
	return render(request, 'accounts/change_password.html', {
		'form': form
	})
