# notification/urls.py

from django.urls import path
from .views import trigger_notification

urlpatterns = [
    path('trigger-notification', trigger_notification, name='trigger-notification'),
]
