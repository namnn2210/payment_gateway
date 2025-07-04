from django.contrib import admin
from .models import EmployeeDeposit, EmployeeWorkingSession
# Register your models here.

@admin.register(EmployeeDeposit)
class EmployeeDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'bankname','accountno','accountname','note','bankcode','status', 'created_at','updated_by', 'updated_at')
    list_filter = ('user','bankname','bankcode',)
    search_fields = ('name','bankname','bankcode',)

@admin.register(EmployeeWorkingSession)
class EmployeeWorkingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'start_balance', 'deposit','total_payout','total_amount_payout', 'end_time', 'end_balance','status')
    list_filter = ('user',)
    search_fields = ('user',)
