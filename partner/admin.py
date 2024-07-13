from django.contrib import admin
from .models import CID, PartnerMapping

# Register your models here.
@admin.register(CID)
class CIDAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at', 'updated_at')
    list_filter = ('name','status',)
    search_fields = ('name')
    

@admin.register(PartnerMapping)
class PartnerMappingAdmin(admin.ModelAdmin):
    list_display = ('cid', 'key', 'cardtype', 'bank', 'status', 'created_at', 'updated_at')
    list_filter = ('cid','cardtype', 'bank',)
    search_fields = ('cid','bank',)