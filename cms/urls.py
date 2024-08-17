from django.urls import path, include
from .views import index, user_login, user_logout, profile, convert

urlpatterns = [
    path('', index, name='index'),
    path('convert', convert, name='convert'),
    path('user_login', user_login, name='user_login'),
    path('profile', profile, name='profile'),
    path('user/logout', user_logout, name='user_logout'),
]