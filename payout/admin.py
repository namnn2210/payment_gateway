from django.contrib import admin
from .models import Payout, Timeline, UserTimeline

# Register your models here.
@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'did','scode','orderno', 'orderid', 'money', 'bankname', 'accountno','accountname', 'bankcode', 'status', 'created_at', 'updated_at')
    list_filter = ('user', 'bankcode', 'status','created_at',)
    search_fields = ('orderno', 'orderid','scode', 'did', 'accountno', 'accountname',)
    
@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_at','end_at', 'status', 'created_at', 'updated_at')
    list_filter = ('name', 'start_at', 'end_at','status',)
    search_fields = ('name', 'start_at','end_at',)
    
@admin.register(UserTimeline)
class UserTimelineAdmin(admin.ModelAdmin):
    list_display = ('user', 'timeline', 'status', 'created_at', 'updated_at')
    list_filter = ('user', 'timeline', 'status','created_at',)
    search_fields = ('user',)