from django.urls import path
from .views import list_bank, AddBankView, bank_transaction_history, update_transaction_history, update_balance, record_book, get_transaction_history_with_filter, toggle_bank_status

urlpatterns = [
    path('list', list_bank, name='list_bank'),
    path('add', AddBankView.as_view(), name='add_bank'),
    path('history/<str:account_number>', bank_transaction_history, name='bank_transaction_history'),
    path('update_transaction_history', update_transaction_history, name='update_transaction_history'),
    path('toggle_bank_status/', toggle_bank_status, name='toggle_bank_status'),
    path('update_balance', update_balance, name='update_balance'),
    path('record_book/<str:bank_type>', record_book, name='record_book'),
    path('get_transaction_history_with_filter',get_transaction_history_with_filter, name='get_transaction_history_with_filter')
]