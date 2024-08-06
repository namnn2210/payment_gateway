from django.contrib import admin
from .models import EmployeeDeposit
# Register your models here.

@admin.register(EmployeeDeposit)
class EmployeeDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'bankname','accountno','accountname','note','bankcode','status', 'created_at','updated_by', 'updated_at')
    list_filter = ('user','bankname','bankcode',)
    search_fields = ('name','bankname','bankcode',)
