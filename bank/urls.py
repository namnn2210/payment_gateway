from django.urls import path
from .views import (
    BankListView,
    RecordBookView,
    ExportTransactionsExcelView,
    AddBankAPIView,
    ToggleBankStatusAPIView,
    ToggleTransactionStatusAPIView,
    TransactionHistoryAPIView,
    BalanceAPIView,
    TodayAmountAPIView,
    RecordBookDataAPIView,
)

app_name = 'bank'

urlpatterns = [
    # Django CBVs for HTML rendering
    path('list', BankListView.as_view(), name='list_bank'),
    path('record_book', RecordBookView.as_view(), name='record_book'),
    path('export_to_excel', ExportTransactionsExcelView.as_view(), name='export_to_excel'),

    # DRF APIViews for JSON responses
    path('api/add', AddBankAPIView.as_view(), name='add_bank_api'),
    path('api/toggle_status', ToggleBankStatusAPIView.as_view(), name='toggle_bank_status_api'),
    path('api/toggle_transaction_status', ToggleTransactionStatusAPIView.as_view(), name='toggle_transaction_status_api'),
    path('api/transaction_history', TransactionHistoryAPIView.as_view(), name='transaction_history_api'),
    path('api/balance', BalanceAPIView.as_view(), name='update_balance_api'),
    path('api/today_amount', TodayAmountAPIView.as_view(), name='get_amount_today_api'),
    path('api/record_book_data', RecordBookDataAPIView.as_view(), name='record_book_data_api'),
]
