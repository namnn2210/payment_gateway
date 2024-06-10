from django.urls import path
from .views import index, login, user_logout

urlpatterns = [
    path('', index, name='index'),
    path('login', login, name='login'),
    path('user/logout', user_logout, name='user_logout'),
]