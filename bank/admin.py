from django.contrib import admin
from django import forms
from .models import Bank, BankAccount

# Register your models here.
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon','status', 'created_at', 'updated_at')
    list_filter = ('name',)
    search_fields = ('name',)

class BankAccountForm(forms.ModelForm):
    TYPE_CHOICES = [
        ('IN', 'IN'),
        ('OUT', 'OUT'),
    ]

    bank_type = forms.ChoiceField(choices=TYPE_CHOICES)

    class Meta:
        model = BankAccount
        fields = '__all__'
    
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    form = BankAccountForm
    list_display = ('user', 'account_name', 'account_number', 'balance', 'bank_name', 'username','password', 'status', 'created_at', 'updated_at')
    list_filter = ('user', 'bank_type', 'bank_name_id','created_at',)
    search_fields = ('account_name', 'account_number','bank_type')
    
    # def user_username(self, obj):
    #     return obj.user.username
