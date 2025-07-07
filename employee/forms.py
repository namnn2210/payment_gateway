from django import forms
from bank.models import BankAccount

class DepositForm(forms.Form):
    deposit = forms.IntegerField()
    bank = forms.ModelChoiceField(queryset=BankAccount.objects.all())
