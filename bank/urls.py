from django.urls import path
from .views import list_bank, AddBankView, bank_transaction_history

urlpatterns = [
    path('list', list_bank, name='list_bank'),
    path('add', AddBankView.as_view(), name='add_bank'),
    path('history/<str:account_number>', bank_transaction_history, name='bank_transaction_history'),
]