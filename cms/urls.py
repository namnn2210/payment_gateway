from django.urls import path
from .views import index, login, user_logout, user_callback, profile

urlpatterns = [
    path('', index, name='index'),
    path('login', login, name='login'),
    path('profile', profile, name='profile'),
    path('user/logout', user_logout, name='user_logout'),
    path('callback', user_callback, name='user_callback'),
]