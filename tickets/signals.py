from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Ticket


def _build_payload_for_ticket(ticket: Ticket):
    # Payload minimal por rol para actualizar solo lo necesario
    base = {
        'event': 'ticket_update',
        'ticket_id': ticket.id,
        'status': ticket.status,
        'assigned_office_id': ticket.assigned_office_id,
        'technician_id': ticket.technician_id,
        'supervisor_id': ticket.supervisor_id,
    }
    return base


def _broadcast_ticket_change(ticket: Ticket):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    payload = _build_payload_for_ticket(ticket)

    # Grupos destinatarios mínimos:
    # - Jefes (global)
    async_to_sync(channel_layer.group_send)('stats_jefes', {
        'type': 'stats_update',
        'payload': payload,
    })

    # - Oficina (supervisores y métricas por oficina)
    if ticket.assigned_office_id:
        async_to_sync(channel_layer.group_send)(f'stats_office_{ticket.assigned_office_id}', {
            'type': 'stats_update',
            'payload': payload,
        })

    # - Técnico asignado (métricas personales)
    if ticket.technician_id:
        async_to_sync(channel_layer.group_send)(f'stats_tech_{ticket.technician_id}', {
            'type': 'stats_update',
            'payload': payload,
        })


@receiver(post_save, sender=Ticket)
def on_ticket_save(sender, instance: Ticket, created, **kwargs):
    _broadcast_ticket_change(instance)


@receiver(post_delete, sender=Ticket)
def on_ticket_delete(sender, instance: Ticket, **kwargs):
    _broadcast_ticket_change(instance)
