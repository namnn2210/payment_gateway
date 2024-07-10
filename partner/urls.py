from django.urls import path
from .views import create_deposit_order

urlpatterns = [
    path('create_deposit_order', create_deposit_order, name='create_deposit_order'),
]