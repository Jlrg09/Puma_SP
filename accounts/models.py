from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class Roles(models.TextChoices):
	UNASSIGNED = 'UNASSIGNED', _('Sin Rol')
	JEFE = 'JEFE', _('Jefe')
	SUPERVISOR = 'SUPERVISOR', _('Supervisor')
	TECNICO = 'TECNICO', _('Técnico')


class CustomUser(AbstractUser):
	approved = models.BooleanField(default=False, help_text=_('Aprobado por Jefe'))
	role = models.CharField(max_length=16, choices=Roles.choices, default=Roles.UNASSIGNED)
	# Asignación de oficina se define más tarde (FK a Office) tras crear modelo Office
	office = models.ForeignKey('oficinas.Office', null=True, blank=True, on_delete=models.SET_NULL, related_name='users')

	class IdentificationType(models.TextChoices):
		CC = 'CC', _('Cédula de ciudadanía')
		CE = 'CE', _('Cédula de extranjería')
		TI = 'TI', _('Tarjeta de identidad')
		PAS = 'PAS', _('Pasaporte')
		NIT = 'NIT', _('NIT')
		PEP = 'PEP', _('Permiso especial de permanencia')

	id_type = models.CharField(
		max_length=5,
		choices=IdentificationType.choices,
		null=True,
		blank=True,
		verbose_name=_('Tipo de identificación'),
	)
	id_number = models.CharField(
		max_length=32,
		null=True,
		blank=True,
		unique=True,
		verbose_name=_('Número de identificación'),
	)
	birth_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha de nacimiento'))
	phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('Teléfono'))

	@property
	def is_jefe(self):
		return self.role == Roles.JEFE

	@property
	def is_supervisor(self):
		return self.role == Roles.SUPERVISOR

	@property
	def is_tecnico(self):
		return self.role == Roles.TECNICO

	def __str__(self):
		return f"{self.username} ({self.get_role_display()})"

	def save(self, *args, **kwargs):
		# Lógica automática para asignación de roles
		# Solo se mantiene la lógica para volver a técnico si se remueve la oficina de un supervisor
		if not self.office and self.role == Roles.SUPERVISOR:
			# Si se remueve la oficina de un supervisor, vuelve a ser técnico
			self.role = Roles.TECNICO
		super().save(*args, **kwargs)

# Create your models here.


class Notification(models.Model):
	recipient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
	ticket = models.ForeignKey('tickets.Ticket', on_delete=models.CASCADE, null=True, blank=True)
	text = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)
	read_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Notificación para {self.recipient} - {self.text}"
