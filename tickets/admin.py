from django.contrib import admin
from .models import Ticket, TicketNote, Evidence


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
	list_display = ('id', 'requester_name', 'requester_office_text', 'requester_office', 'assigned_office', 'priority', 'status', 'technician', 'created_at')
	list_filter = ('priority', 'status', 'assigned_office')
	search_fields = ('requester_name', 'description', 'equipment_code')


@admin.register(TicketNote)
class TicketNoteAdmin(admin.ModelAdmin):
	list_display = ('id', 'ticket', 'author', 'created_at')


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
	list_display = ('id', 'ticket', 'uploaded_at')

# Register your models here.
