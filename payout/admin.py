from django.contrib import admin
from django import forms
from .models import Payout, Timeline, UserTimeline, BalanceTimeline, LicenseKeys
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse
from django.contrib.auth.models import User

# Register your models here.
class UpdateUserForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)  # To keep track of selected rows
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Select a new user")  # Dropdown to select a user

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('user','scode','orderno', 'orderid', 'status', 'money', 'bankname', 'accountno','accountname', 'bankcode','partner_bankcode', 'created_at', 'updated_at')
    list_filter = ('user','is_report','is_cancel', 'status',)
    search_fields = ('orderno', 'orderid','scode', 'did', 'accountno', 'accountname','memo',)

    def update_user(self, request, queryset):
        form = None

        # If the form has been submitted
        if 'apply' in request.POST:
            form = UpdateUserForm(request.POST)

            if form.is_valid():
                # Get the selected user from the form
                new_user = form.cleaned_data['user']

                # Update the user field for the selected records
                updated_count = queryset.update(user=new_user)

                # Inform the user of how many objects were updated
                self.message_user(request, f"{updated_count} payouts were successfully updated with the new user.")

                # Return None to redirect back to the changelist view
                return None

        if not form:
            form = UpdateUserForm(initial={
                '_selected_action': request.POST.getlist(ACTION_CHECKBOX_NAME)
            })

        # Render the custom action form template
        return TemplateResponse(request, 'update_user_action.html', {
            'payouts': queryset,
            'action_form': form,
            'title': 'Transfer payout user',
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'queryset': queryset,
        })

    update_user.short_description = "Transfer payout user"

    # Register the custom action
    actions = ['update_user']


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
    
    
@admin.register(BalanceTimeline)
class BalanceTimelineAdmin(admin.ModelAdmin):
    list_display = ('id','timeline', 'bank_account', 'balance', 'status', 'created_at', 'updated_at')
    list_filter = ('timeline', 'bank_account', 'status','created_at',)
    search_fields = ('bank_account',)


@admin.register(LicenseKeys)
class LicenseKeysAdmin(admin.ModelAdmin):
    list_display = ('id','key', 'mac', 'status', 'created_at', 'updated_at')
    list_filter = ('status','created_at')
    search_fields = ('key','mac',)