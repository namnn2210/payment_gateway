from django.urls import path
from .views import login, transactions, balance,transfer

urlpatterns = [
    path('login', login, name='login'),
    path('transactions', transactions, name='transactions'),
    path('balance', balance, name='balance'),
    path('transfer', transfer, name='transfer'),
]