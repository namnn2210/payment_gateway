from django.urls import path
from .views import new_transaction, transfer_callback_1, transfer_callback_2

urlpatterns = [
    path('new_transaction', new_transaction, name='new_transaction'),
    path('transfer_callback_1',transfer_callback_1, name='transfer_callback_1'),
    path('transfer_callback_2',transfer_callback_2, name='transfer_callback_2')
]