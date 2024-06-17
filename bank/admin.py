from django.contrib import admin
from .models import Bank, BankAccount

# Register your models here.
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon','status', 'created_at', 'updated_at')
    list_filter = ('name',)
    search_fields = ('name',)
    
    
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_name', 'account_number', 'balance', 'bank_name', 'username','password','bank_type', 'created_at', 'updated_at')
    list_filter = ('user', 'bank_type', 'bank_name_id','created_at',)
    search_fields = ('account_name', 'account_number','bank_type')
    
    # def user_username(self, obj):
    #     return obj.user.username
