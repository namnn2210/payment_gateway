from django.contrib import admin
from .models import TransactionHistory

# Register your models here.
@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_number', 'amount','description','incomingorderid','note','orderid','scode','transaction_type','transaction_number','transfer_code','payername','status', 'created_at', 'updated_at')
    list_filter = ('account_number',)
    search_fields = ('account_number','description',)