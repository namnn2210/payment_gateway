from django.contrib import admin
from .models import SettlePayout
from django import forms
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse
from django.contrib.auth.models import User

class UpdateUserForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)  # To keep track of selected rows
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Select a new user")  # Dropdown to select a user

@admin.register(SettlePayout)
class SettlePayoutAdmin(admin.ModelAdmin):
    list_display = ('user','scode','orderno', 'orderid', 'status', 'money', 'bankname', 'accountno','accountname', 'bankcode','process_bank', 'created_at', 'updated_at')
    list_filter = ('user', 'bankcode', 'status','created_at',)
    search_fields = ('orderno', 'orderid','scode', 'did', 'accountno', 'accountname',)

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
            'title': 'Transfer settle user',
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'queryset': queryset,
        })

    update_user.short_description = "Transfer settle user"

    # Register the custom action
    actions = ['update_user']