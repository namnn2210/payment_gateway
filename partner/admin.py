from django.contrib import admin
from .models import CID

# Register your models here.
@admin.register(CID)
class CIDAdmin(admin.ModelAdmin):
    list_display = ('name', 'status','key','cardtype', 'created_at', 'updated_at')
    list_filter = ('name','status','key','cardtype',)
    search_fields = ('name','key',)
    