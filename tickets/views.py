from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db import models
from django.core.paginator import Paginator
from accounts.models import Roles, CustomUser
from oficinas.models import Office
from .models import Ticket, TicketStatus
from accounts.decorators import jefe_required, supervisor_required, tecnico_required
from .forms import TicketCreateForm, TechnicianUpdateForm, TicketNoteForm, EvidenceForm
from accounts.models import Notification
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse


def is_jefe(user):
	return user.is_authenticated and user.is_jefe


def is_supervisor(user):
	return user.is_authenticated and user.is_supervisor


def is_tecnico(user):
	return user.is_authenticated and user.is_tecnico


@login_required
def index(request):
	# Role-aware base queryset
	if request.user.is_jefe:
		qs = Ticket.objects.select_related('assigned_office', 'technician').all()
	elif request.user.is_supervisor:
		qs = Ticket.objects.filter(assigned_office=request.user.office)
	else:
		qs = Ticket.objects.filter(technician=request.user)

	# Filters
	status = request.GET.get('status')
	priority = request.GET.get('priority')
	office = request.GET.get('office')
	tech = request.GET.get('tech')
	q = request.GET.get('q')

	if status:
		qs = qs.filter(status=status)
	if priority:
		qs = qs.filter(priority=priority)
	if office:
		qs = qs.filter(assigned_office_id=office)
	if tech:
		qs = qs.filter(technician_id=tech)
	if q:
		qs = qs.filter(models.Q(requester_name__icontains=q) | models.Q(description__icontains=q))

	# Sorting
	sort_by = request.GET.get('sort', '-created_at')  # Default: newest first
	valid_sorts = [
		'-created_at',  # Newest first
		'created_at',   # Oldest first
		'-updated_at',  # Recently updated first
		'updated_at',   # Least recently updated first
		'-priority',    # High priority first
		'priority',     # Low priority first
		'status',       # Status alphabetical
		'-status'       # Status reverse alphabetical
	]
	
	if sort_by in valid_sorts:
		qs = qs.order_by(sort_by)
	else:
		qs = qs.order_by('-created_at')

	# Pagination
	page = request.GET.get('page', 1)
	paginator = Paginator(qs, 10)
	tickets = paginator.get_page(page)

	# Workload for supervisors view
	tech_counts = None
	tecnicos = None
	offices = None
	if request.user.is_supervisor:
		tech_counts = (
			CustomUser.objects.filter(office=request.user.office, role=Roles.TECNICO)
			.annotate(asignados=Count('tickets_assigned_to', filter=models.Q(tickets_assigned_to__status__in=[TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING_SUPPLIES])))
		)
		tecnicos = CustomUser.objects.filter(office=request.user.office, role=Roles.TECNICO)
	if request.user.is_jefe:
		offices = Office.objects.all()
		tecnicos = CustomUser.objects.filter(role=Roles.TECNICO)

	context = {
		'tickets': tickets,
		'tech_counts': tech_counts,
		'priority_choices': ['1','2','3','4','5'],
		'filters': {
			'status': status or '',
			'priority': priority or '',
			'office': int(office) if office else '',
			'tech': int(tech) if tech else '',
			'q': q or '',
			'sort': sort_by,
		},
		'tecnicos': tecnicos,
		'offices': offices,
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('partial') == 'tbody':
		html = render_to_string('tickets/_table_body.html', context | {'no_layout': True}, request=request)
		return JsonResponse({'html': html})
	return render(request, 'tickets/index.html', context)


@login_required
@jefe_required
def create(request):
	if request.method == 'POST':
		form = TicketCreateForm(request.POST)
		if form.is_valid():
			ticket = form.save(commit=False)
			# Initial state after creation: ASSIGNED to office (supervisor will assign technician)
			ticket.status = TicketStatus.ASSIGNED
			# Set supervisor inferred from office if exists
			assigned_office: Office = ticket.assigned_office
			ticket.supervisor = assigned_office.supervisor if assigned_office else None
			ticket.save()
			
			# Crear notificaciones para nuevos requerimientos
			# Notificar a todos los jefes
			jefes = CustomUser.objects.filter(role=Roles.JEFE, is_active=True)
			for jefe in jefes:
				Notification.objects.create(
					recipient=jefe,
					ticket=ticket,
					text=f"🆕 NUEVO REQUERIMIENTO - #{ticket.id}: {ticket.requester_name} solicita servicio en {ticket.assigned_office}"
				)
			
			# Notificar al supervisor de la oficina asignada (si existe y no es jefe)
			if ticket.supervisor and ticket.supervisor.role != Roles.JEFE:
				Notification.objects.create(
					recipient=ticket.supervisor,
					ticket=ticket,
					text=f"🆕 Nuevo requerimiento asignado a tu oficina - #{ticket.id}: {ticket.requester_name}"
				)
			
			messages.success(request, 'Requerimiento creado y asignado a oficina')
			return redirect('tickets_index')
	else:
		form = TicketCreateForm()
	return render(request, 'tickets/create.html', {'form': form})


@login_required
@supervisor_required
def assign(request, ticket_id):
	ticket = get_object_or_404(Ticket, pk=ticket_id, assigned_office=request.user.office)
	if ticket.status == TicketStatus.COMPLETED:
		messages.warning(request, 'El requerimiento ya está completado y no se puede (re)asignar.')
		return redirect('tickets_index')
	if request.method == 'POST':
		tech_id = request.POST.get('technician')
		if tech_id == 'self':
			ticket.technician = request.user
		else:
			ticket.technician = get_object_or_404(CustomUser, pk=tech_id, office=request.user.office, role=Roles.TECNICO)
		# When assigned to someone, move status to IN_PROGRESS
		ticket.status = TicketStatus.IN_PROGRESS
		ticket.supervisor = request.user
		ticket.save()
		# Notify the assigned technician (or supervisor if self)
		assignee = ticket.technician or request.user
		Notification.objects.create(
			recipient=assignee,
			ticket=ticket,
			text=f"Nuevo requerimiento asignado #{ticket.id}: {ticket.description[:80]}"
		)
		# Optional email notification
		try:
			if assignee.email:
				send_mail(
					subject=f"Nuevo requerimiento asignado #{ticket.id}",
					message=(
						f"Hola {assignee.username},\n\n"
						f"Se te ha asignado el requerimiento #{ticket.id}.\n"
						f"Descripción: {ticket.description}\n"
						f"Prioridad: {ticket.get_priority_display()}\n"
						f"Estado: {ticket.get_status_display()}\n"
					),
					from_email=None,
					recipient_list=[assignee.email],
					fail_silently=True,
				)
		except Exception:
			pass
		messages.success(request, 'Ticket asignado')
		return redirect('tickets_index')
	tecnicos = CustomUser.objects.filter(office=request.user.office, role=Roles.TECNICO, is_active=True, approved=True)
	return render(request, 'tickets/assign.html', {'ticket': ticket, 'tecnicos': tecnicos})


@login_required
def update_status(request, ticket_id):
	ticket = get_object_or_404(Ticket, pk=ticket_id)
	# Only the assigned technician (which may be a supervisor who self-assigned) can update status
	if ticket.technician_id != request.user.id:
		from django.core.exceptions import PermissionDenied
		raise PermissionDenied('No autorizado para actualizar este ticket')
	if ticket.status == TicketStatus.COMPLETED:
		messages.info(request, 'El requerimiento ya está completado y no se puede actualizar.')
		return redirect('tickets_index')
	if request.method == 'POST':
		form = TechnicianUpdateForm(request.POST, instance=ticket)
		if form.is_valid():
			old_status = ticket.status  # Guardar el estado anterior
			updated_ticket = form.save()
			note_text = form.cleaned_data.get('note')
			if note_text:
				from .models import TicketNote
				TicketNote.objects.create(ticket=updated_ticket, author=request.user, text=note_text)
			
			# Enviar notificaciones si se cambió a PENDING_SUPPLIES
			if old_status != TicketStatus.PENDING_SUPPLIES and updated_ticket.status == TicketStatus.PENDING_SUPPLIES:
				# Obtener la nota más reciente que debería contener la información de insumos
				recent_note = ""
				if note_text:
					recent_note = f" - Insumos solicitados: {note_text}"
				
				# Notificar a todos los jefes
				jefes = CustomUser.objects.filter(role=Roles.JEFE, is_active=True)
				for jefe in jefes:
					Notification.objects.create(
						recipient=jefe,
						ticket=updated_ticket,
						text=f"🔧 INSUMOS SOLICITADOS - Requerimiento #{updated_ticket.id}: {updated_ticket.requester_name} ({updated_ticket.assigned_office}){recent_note}"
					)
				
				# Notificar al supervisor de la oficina (si existe)
				if updated_ticket.assigned_office and updated_ticket.assigned_office.supervisor:
					supervisor = updated_ticket.assigned_office.supervisor
					# Evitar notificación duplicada si el supervisor también es jefe
					if supervisor.role != Roles.JEFE:
						Notification.objects.create(
							recipient=supervisor,
							ticket=updated_ticket,
							text=f"🔧 INSUMOS SOLICITADOS - Tu técnico {request.user.username} requiere insumos para el requerimiento #{updated_ticket.id}{recent_note}"
						)
			
			messages.success(request, 'Estado actualizado')
			return redirect('tickets_index')
	else:
		form = TechnicianUpdateForm(instance=ticket)
	return render(request, 'tickets/update_status.html', {'form': form, 'ticket': ticket})


@login_required
def ticket_detail(request, ticket_id):
	from .models import TicketNote, Evidence
	ticket = get_object_or_404(Ticket, pk=ticket_id)
	
	# Check permissions: jefes can see all, supervisors can see tickets from their office, technicians can see their assigned tickets
	if not (
		request.user.is_jefe
		or (request.user.is_supervisor and ticket.assigned_office_id == request.user.office_id)
		or (ticket.technician_id and request.user.id == ticket.technician_id)
		or (ticket.supervisor_id and request.user.id == ticket.supervisor_id)
	):
		from django.core.exceptions import PermissionDenied
		raise PermissionDenied("No autorizado para ver este ticket")
	
	notes = TicketNote.objects.filter(ticket=ticket).select_related('author').order_by('-created_at')
	evidences = Evidence.objects.filter(ticket=ticket).order_by('-uploaded_at')
	
	context = {
		'ticket': ticket,
		'notes': notes,
		'evidences': evidences,
	}
	return render(request, 'tickets/detail.html', context)


@login_required
def add_note(request, ticket_id):
	from .models import TicketNote
	ticket = get_object_or_404(Ticket, pk=ticket_id)
	# Only assigned technician, ticket's supervisor, or supervisors of the office can add notes (NOT jefes)
	if not (
		(ticket.technician_id and request.user.id == ticket.technician_id)
		or (ticket.supervisor_id and request.user.id == ticket.supervisor_id)
		or (request.user.is_supervisor and ticket.assigned_office_id == request.user.office_id)
	):
		from django.core.exceptions import PermissionDenied
		raise PermissionDenied('No autorizado para agregar notas a este ticket')
	if request.method == 'POST':
		form = TicketNoteForm(request.POST)
		if form.is_valid():
			TicketNote.objects.create(ticket=ticket, author=request.user, text=form.cleaned_data['text'])
			messages.success(request, 'Observación agregada')
			return redirect('tickets_index')
	else:
		form = TicketNoteForm()
	return render(request, 'tickets/add_note.html', {'form': form, 'ticket': ticket})


@login_required
def add_evidence(request, ticket_id):
	from .models import Evidence
	ticket = get_object_or_404(Ticket, pk=ticket_id)
	# Only the assigned technician, the ticket's supervisor, or supervisors of the office can upload evidence (NOT jefes)
	if not (
		(ticket.technician_id and request.user.id == ticket.technician_id)
		or (ticket.supervisor_id and request.user.id == ticket.supervisor_id)
		or (request.user.is_supervisor and ticket.assigned_office_id == request.user.office_id)
	):
		from django.core.exceptions import PermissionDenied
		raise PermissionDenied("No autorizado para subir evidencias de este ticket")
	if request.method == 'POST':
		form = EvidenceForm(request.POST, request.FILES)
		if form.is_valid():
			Evidence.objects.create(ticket=ticket, image=form.cleaned_data['image'])
			messages.success(request, 'Evidencia subida')
			return redirect('tickets_index')
	else:
		form = EvidenceForm()
	return render(request, 'tickets/add_evidence.html', {'form': form, 'ticket': ticket})

# Create your views here.
