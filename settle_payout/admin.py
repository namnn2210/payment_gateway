from django.contrib import admin
from .models import SettlePayout

# Register your models here.
@admin.register(SettlePayout)
class SettlePayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'did','scode','orderno', 'orderid', 'money', 'bankname', 'accountno','accountname', 'bankcode', 'status', 'created_at', 'updated_at')
    list_filter = ('user', 'bankcode', 'status','created_at',)
    search_fields = ('orderno', 'orderid','scode', 'did', 'accountno', 'accountname',)