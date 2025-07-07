from django import forms

class OTPForm(forms.Form):
    otp_code = forms.CharField(label="OTP Code", max_length=6, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
