from django.urls import path, include
from .views import api_login

urlpatterns = [
    path('api/login', api_login, name='api_login'),
]