from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

@receiver(post_save, sender=Notification)
def on_notification_save(sender, instance: Notification, created, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    payload = {
        'event': 'notification_update',
        'notification_id': instance.id,
        'ticket_id': instance.ticket_id,
        'text': instance.text,
        'created_at': instance.created_at.isoformat(),
    }
    # Emitir al grupo del usuario
    async_to_sync(channel_layer.group_send)(f'user_{instance.recipient_id}', {
        'type': 'notification_update',  # Usar el tipo correcto que espera el frontend
        'data': payload,
    })
