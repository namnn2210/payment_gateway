"""
ASGI config for payment_gateway project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""


from django.core.asgi import get_asgi_application
django_application = get_asgi_application()
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import payment_gateway.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_gateway.settings')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(
            payment_gateway.routing.websocket_urlpatterns
        ))
    ),
})
