from django.urls import path
from .views import new_transaction

urlpatterns = [
    path('new_transaction', new_transaction, name='new_transaction'),
]