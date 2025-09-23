from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from accounts.models import Roles, CustomUser
from django.core.paginator import Paginator
from django.db import models
from .models import Office
from accounts.decorators import jefe_required

def is_jefe(user):
	return user.is_authenticated and user.is_jefe


class OfficeForm(forms.ModelForm):
	class Meta:
		model = Office
		fields = ['name', 'description']


@login_required
def index(request):
	qs = Office.objects.select_related('supervisor').all()
	q = request.GET.get('q')
	supervisor = request.GET.get('supervisor')

	if q:
		qs = qs.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))
	if supervisor:
		qs = qs.filter(supervisor_id=supervisor)

	qs = qs.order_by('name')
	paginator = Paginator(qs, 10)
	offices = paginator.get_page(request.GET.get('page', 1))

	supervisors = CustomUser.objects.filter(role=Roles.SUPERVISOR, is_active=True, approved=True).order_by('username')
	ctx = {
		'offices': offices,
		'supervisors': supervisors,
		'filters': {
			'q': q or '',
			'supervisor': int(supervisor) if supervisor else '',
		},
	}
	return render(request, 'oficinas/index.html', ctx)


@login_required
@jefe_required
def create(request):
	if request.method == 'POST':
		form = OfficeForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Oficina creada')
			return redirect('oficinas_index')
	else:
		form = OfficeForm()
	return render(request, 'oficinas/form.html', {'form': form, 'title': 'Crear oficina'})


@login_required
@jefe_required
def edit(request, office_id):
	office = get_object_or_404(Office, pk=office_id)
	if request.method == 'POST':
		form = OfficeForm(request.POST, instance=office)
		if form.is_valid():
			form.save()
			# Supervisor assignment: choose among active users in this office with role SUPERVISOR
			supervisor_id = request.POST.get('supervisor')
			# Allow clearing supervisor and selecting any active/approved supervisor, regardless of current office
			if supervisor_id is not None:
				supervisor_id = supervisor_id.strip()
				if supervisor_id == '':
					office.supervisor = None
				else:
					supervisor = CustomUser.objects.filter(
						pk=supervisor_id,
						is_active=True,
						approved=True,
					).first()
					if supervisor:
						office.supervisor = supervisor
						# Si es técnico, promoverlo a supervisor
						if supervisor.role == Roles.TECNICO:
							supervisor.role = Roles.SUPERVISOR
						# Asegurar que el supervisor pertenece a esta oficina
						if supervisor.office_id != office.id:
							supervisor.office = office
						supervisor.save()
				office.save()
			messages.success(request, 'Oficina actualizada')
			return redirect('oficinas_index')
	else:
		form = OfficeForm(instance=office)
	# Mostrar técnicos asignados a esta oficina y supervisores existentes como candidatos
	# Los técnicos asignados a esta oficina pueden ser promovidos a supervisor
	candidates = CustomUser.objects.filter(
		models.Q(office=office, role=Roles.TECNICO) | 
		models.Q(role=Roles.SUPERVISOR),
		is_active=True, 
		approved=True
	).order_by('username')
	return render(request, 'oficinas/form.html', {
		'form': form,
		'title': f'Editar oficina: {office.name}',
		'office': office,
		'candidates': candidates,
	})


@login_required
@jefe_required
def delete(request, office_id):
	office = get_object_or_404(Office, pk=office_id)
	if request.method == 'POST':
		office.delete()
		messages.success(request, 'Oficina eliminada')
		return redirect('oficinas_index')
	return render(request, 'oficinas/confirm_delete.html', {'office': office})

