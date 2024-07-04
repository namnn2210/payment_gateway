from django.urls import path
from .views import mb_login, transactions, balance,transfer

urlpatterns = [
    path('mb_login', mb_login, name='mb_login'),
    path('transactions', transactions, name='transactions'),
    path('balance', balance, name='balance'),
    path('transfer', transfer, name='transfer'),
]