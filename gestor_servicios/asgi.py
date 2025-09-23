"""
ASGI config for gestor_servicios project with Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from .consumers import StatsConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_servicios.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    path('ws/stats/', StatsConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
