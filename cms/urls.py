from django.urls import path
from .views import (
    IndexView,
    UserLoginView,
    UserLogoutView,
    ProfileView,
    VerifyOTPView,
    Setup2FAView,
)

app_name = 'cms'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='user_logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('setup_2fa/', Setup2FAView.as_view(), name='setup_2fa'),
    path('verify_otp/', VerifyOTPView.as_view(), name='verify_otp'),
]
