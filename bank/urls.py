from django.urls import path
from .views import list_bank, AddBankView, update_transaction_history, update_balance, record_book, toggle_bank_status, get_amount_today,record_book_report,export_to_excel


urlpatterns = [
    path('list', list_bank, name='list_bank'),
    path('add', AddBankView.as_view(), name='add_bank'),
    path('update_transaction_history', update_transaction_history, name='update_transaction_history'),
    path('toggle_bank_status/', toggle_bank_status, name='toggle_bank_status'),
    path('update_balance', update_balance, name='update_balance'),
    path('record_book', record_book, name='record_book'),
    path('record_book_report', record_book_report, name='record_book_report'),
    path('get_amount_today',get_amount_today, name='get_amount_today'),
    path('export_to_excel',export_to_excel,name='export_to_excel')
]