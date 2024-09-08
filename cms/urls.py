from django.urls import path, include
from .views import index, user_login, user_logout, profile, verify_otp,submit_otp

urlpatterns = [
    path('', index, name='index'),
    path('user_login', user_login, name='user_login'),
    path('profile', profile, name='profile'),
    path('verify_otp',verify_otp, name='verify_otp'),
    path('submit_otp',submit_otp, name='submit_otp'),
    path('user/logout', user_logout, name='user_logout'),
]