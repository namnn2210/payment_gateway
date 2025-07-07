from django import forms

class SettlePayoutForm(forms.Form):
    scode = forms.CharField(max_length=100)
    orderid = forms.CharField(max_length=100)
    money = forms.CharField(max_length=100)
    accountno = forms.CharField(max_length=100)
    accountname = forms.CharField(max_length=100)
    bankcode = forms.CharField(max_length=100)
