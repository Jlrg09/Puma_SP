from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
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
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from urllib.parse import urlencode


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


def logout_view(request):
	"""Vista personalizada de logout que acepta tanto GET como POST"""
	logout(request)
	messages.success(request, '¡Hasta luego! Has cerrado sesión exitosamente.')
	return redirect('login')


# Superuser admin panel: only allow superusers
def superuser_required(view_func):
	return user_passes_test(lambda u: u.is_active and u.is_superuser)(view_func)


@login_required
@superuser_required
def admin_panel(request):
	"""Admin panel with basic filters and pagination for users and tickets."""
	from tickets.models import Ticket
	from oficinas.models import Office

	# Users filtering
	users_qs = CustomUser.objects.select_related('office').all()
	u_role = request.GET.get('role', '')
	u_office = request.GET.get('office', '')
	u_q = request.GET.get('q', '')
	if u_role:
		users_qs = users_qs.filter(role=u_role)
	if u_office:
		try:
			users_qs = users_qs.filter(office_id=int(u_office))
		except Exception:
			pass
	if u_q:
		users_qs = users_qs.filter(models.Q(username__icontains=u_q) | models.Q(email__icontains=u_q) | models.Q(first_name__icontains=u_q) | models.Q(last_name__icontains=u_q))
	users_qs = users_qs.order_by('-date_joined')
	users_page = Paginator(users_qs, 10).get_page(request.GET.get('users_page', 1))

	# Tickets filtering
	tickets_qs = Ticket.objects.select_related('assigned_to', 'office').all()
	t_q = request.GET.get('t_q', '')
	t_office = request.GET.get('t_office', '')
	if t_q:
		tickets_qs = tickets_qs.filter(models.Q(title__icontains=t_q) | models.Q(description__icontains=t_q))
	if t_office:
		try:
			tickets_qs = tickets_qs.filter(office_id=int(t_office))
		except Exception:
			pass
	tickets_qs = tickets_qs.order_by('-created_at')
	tickets_page = Paginator(tickets_qs, 20).get_page(request.GET.get('tickets_page', 1))

	offices = Office.objects.all().order_by('name')

	ctx = {
		'users': users_page,
		'tickets': tickets_page,
		'offices': offices,
		'roles': Roles,
		'user_filters': {'role': u_role, 'office': u_office, 'q': u_q},
		'ticket_filters': {'t_q': t_q, 't_office': t_office},
	}
	# Build querystrings to preserve filters when paginating
	users_params = {}
	if u_role:
		users_params['role'] = u_role
	if u_office:
		users_params['office'] = u_office
	if u_q:
		users_params['q'] = u_q
	ctx['users_querystring'] = '&' + urlencode(users_params) if users_params else ''

	tickets_params = {}
	if t_q:
		tickets_params['t_q'] = t_q
	if t_office:
		tickets_params['t_office'] = t_office
	ctx['tickets_querystring'] = '&' + urlencode(tickets_params) if tickets_params else ''
	return render(request, 'admin_panel.html', ctx)


@login_required
@superuser_required
@require_POST
def admin_delete_ticket(request, ticket_id):
	"""Delete a ticket (superuser only). POST only."""
	from tickets.models import Ticket

	ticket = get_object_or_404(Ticket, pk=ticket_id)
	title = str(ticket)
	ticket.delete()
	messages.success(request, f'Requerimiento {ticket_id} eliminado: {title}')
	return redirect('admin_panel')


@login_required
@superuser_required
@require_POST
def admin_delete_user(request, user_id):
	"""Delete a user (superuser only). Prevent deleting self."""
	target = get_object_or_404(CustomUser, pk=user_id)
	if request.user.pk == target.pk:
		messages.error(request, 'No puedes eliminarte a ti mismo.')
		return redirect('admin_panel')
	# Prevent deletion if the user has open tickets (as technician or supervisor)
	from tickets.models import Ticket, TicketStatus

	tech_open = Ticket.objects.filter(technician=target).exclude(status=TicketStatus.COMPLETED).count()
	sup_open = Ticket.objects.filter(supervisor=target).exclude(status=TicketStatus.COMPLETED).count()
	if tech_open or sup_open:
		parts = []
		if tech_open:
			parts.append(f'{tech_open} requerimiento(s) asignado(s) a este técnico')
		if sup_open:
			parts.append(f'{sup_open} requerimiento(s) donde figura como supervisor')
		msg = 'No se puede eliminar el usuario: ' + ' y '.join(parts) + '. Reasigna o cierra esos requerimientos antes de eliminar.'
		messages.error(request, msg)
		return redirect('admin_panel')

	username = target.username
	target.delete()
	messages.success(request, f'Usuario {username} eliminado.')
	return redirect('admin_panel')


@login_required
@superuser_required
def admin_create_user(request):
	"""Create a user from admin panel. Superuser-only."""
	from .forms import RegisterForm
	from oficinas.models import Office
	from .models import Roles

	if request.method == 'POST':
		form = RegisterForm(request.POST)
		role = request.POST.get('role')
		office_id = request.POST.get('office')
		approved = request.POST.get('approved') == 'on'
		is_active = request.POST.get('is_active') == 'on'
		if form.is_valid():
			user: CustomUser = form.save(commit=False)
			# do not set a usable password here; admin can set password later
			user.set_unusable_password()
			user.role = role or Roles.UNASSIGNED
			if office_id:
				try:
					user.office_id = int(office_id)
				except Exception:
					pass
			user.approved = approved
			user.is_active = is_active
			user.save()
			messages.success(request, f'Usuario {user.username} creado. Establece una contraseña para completar el acceso.')
			return redirect('admin_panel')
	else:
		form = RegisterForm()

	offices = Office.objects.all()
	roles = Roles
	return render(request, 'admin_create_user.html', {'form': form, 'offices': offices, 'roles': roles})


@login_required
@superuser_required
def admin_set_password(request, user_id):
	"""Allow superuser to set password for another user."""
	target = get_object_or_404(CustomUser, pk=user_id)
	if request.method == 'POST':
		form = SetPasswordForm(target, request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, f'Contraseña actualizada para {target.username}.')
			return redirect('admin_panel')
	else:
		form = SetPasswordForm(target)

	return render(request, 'admin_set_password.html', {'form': form, 'target': target})
