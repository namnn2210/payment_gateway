from django.urls import path
from .views import list_bank, AddBankView, bank_transaction_history, update_transaction_history, record_book, get_transaction_history_with_filter

urlpatterns = [
    path('list', list_bank, name='list_bank'),
    path('add', AddBankView.as_view(), name='add_bank'),
    path('history/<str:account_number>', bank_transaction_history, name='bank_transaction_history'),
    path('update_transaction_history', update_transaction_history, name='update_transaction_history'),
    path('record_book', record_book, name='record_book'),
    path('get_transaction_history_with_filter',get_transaction_history_with_filter, name='get_transaction_history_with_filter')
]