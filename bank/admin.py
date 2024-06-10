from django.contrib import admin
from .models import Bank

# Register your models here.
@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon','status', 'created_at', 'updated_at')
    list_filter = ('name',)
    search_fields = ('name',)