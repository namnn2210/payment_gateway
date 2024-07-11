from django.db import models
from datetime import date

# Create your models here.
class AmountInOut(models.Model):
    amount_in = models.IntegerField(default=0)
    amount_out = models.IntegerField(default=0)
    date_record = models.DateField(default=date.today())
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'amount_in_out'