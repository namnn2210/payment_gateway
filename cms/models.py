from django.db import models
from datetime import date
from django.contrib.auth.models import User

# Create your models here.
class AmountInOut(models.Model):
    amount_in = models.IntegerField(default=0)
    amount_out = models.IntegerField(default=0)
    # date_record = models.DateField(default=date.today())
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'amount_in_out'

class User2Fa(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(max_length=100, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
    class Meta:
        db_table = 'user_2fa'
