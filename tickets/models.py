from django.db import models
from django.utils.translation import gettext_lazy as _


class TicketPriority(models.IntegerChoices):
	P1 = 1, _('Muy baja')
	P2 = 2, _('Baja')
	P3 = 3, _('Media')
	P4 = 4, _('Alta')
	P5 = 5, _('Urgente')


class TicketStatus(models.TextChoices):
	DRAFT = 'DRAFT', _('Borrador')
	ASSIGNED = 'ASSIGNED', _('Asignado')
	IN_PROGRESS = 'IN_PROGRESS', _('En curso')
	PENDING_SUPPLIES = 'PENDING_SUPPLIES', _('Pendiente por insumos')
	COMPLETED = 'COMPLETED', _('Completado')


class Ticket(models.Model):
	requester_name = models.CharField(max_length=150, verbose_name=_('Nombre del solicitante'))
	requester_office = models.ForeignKey('oficinas.Office', related_name='tickets_requested', on_delete=models.PROTECT, verbose_name=_('Oficina que solicita (catálogo)'), null=True, blank=True)
	requester_office_text = models.CharField(max_length=150, verbose_name=_('Oficina que solicita'), blank=True)
	description = models.TextField(verbose_name=_('Descripción del servicio'))
	priority = models.IntegerField(choices=TicketPriority.choices, default=TicketPriority.P3, verbose_name=_('Prioridad'))
	assigned_office = models.ForeignKey('oficinas.Office', related_name='tickets_assigned', on_delete=models.PROTECT, verbose_name=_('Oficina asignada'))
	supervisor = models.ForeignKey('accounts.CustomUser', related_name='tickets_supervised', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Supervisor'))
	technician = models.ForeignKey('accounts.CustomUser', related_name='tickets_assigned_to', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Técnico'))
	equipment_code = models.CharField(max_length=120, blank=True, verbose_name=_('Código del equipo'))
	status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.DRAFT, verbose_name=_('Estado'))
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.requester_name} - {self.get_priority_display()} ({self.get_status_display()})"


class TicketNote(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='notes')
	author = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Nota {self.id} para Ticket {self.ticket_id}"


class Evidence(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='evidences')
	image = models.ImageField(upload_to='evidences/')
	uploaded_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Evidencia {self.id} Ticket {self.ticket_id}"

# Create your models here.
