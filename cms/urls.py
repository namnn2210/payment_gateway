from django.urls import path
from .views import index, user_login, user_logout, user_callback, profile, webhook

urlpatterns = [
    path('', index, name='index'),
    path('user_login', user_login, name='user_login'),
    path('profile', profile, name='profile'),
    path('user/logout', user_logout, name='user_logout'),
    path('callback', user_callback, name='user_callback'),
    path('webhook/', webhook, name='webhook'),
]