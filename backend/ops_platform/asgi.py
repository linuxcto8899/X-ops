"""
ASGI config for ops_platform project.

Supports both HTTP (Django) and WebSocket (Channels) for the online terminal.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ops_platform.settings')

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.urls import path  # noqa: E402
from terminal.consumers import TerminalConsumer  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(URLRouter([
        path('ws/terminal/', TerminalConsumer.as_asgi()),
    ])),
})
