from django.db import models
from django.utils.translation import gettext_lazy as _


class Office(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	# supervisor se establece vía relación con usuario con rol SUPERVISOR asignado a esta oficina
	supervisor = models.ForeignKey('accounts.CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='supervisa_oficina')

	def __str__(self):
		return self.name

# Create your models here.
