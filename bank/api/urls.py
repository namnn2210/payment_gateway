from django.urls import path
from bank.controllers.bank_controller import BankController, BankStatusController
from bank.controllers.bank_account_controller import BankAccountController, BankAccountStatusController, BankAccountBalanceController

urlpatterns = [
    # Bank URLs
    path('banks/', BankController.as_view(), name='bank-list'),
    path('banks/<int:bank_id>/', BankController.as_view(), name='bank-detail'),
    path('banks/<int:bank_id>/toggle-status/', BankStatusController.as_view(), name='bank-toggle-status'),
    
    # Bank Account URLs
    path('accounts/', BankAccountController.as_view(), name='bank-account-list'),
    path('accounts/<int:account_id>/', BankAccountController.as_view(), name='bank-account-detail'),
    path('accounts/<int:account_id>/toggle-status/', BankAccountStatusController.as_view(), name='bank-account-toggle-status'),
    path('accounts/<int:account_id>/update-balance/', BankAccountBalanceController.as_view(), name='bank-account-update-balance'),
] 