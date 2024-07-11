# payment_gateway/routing.py

from django.urls import path
from notification.consumers import NotificationConsumer

websocket_urlpatterns = [
    path('ws/', NotificationConsumer.as_asgi()),
]
