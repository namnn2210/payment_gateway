from django.db import models
from django.contrib.auth.models import User
from bank.models import Bank

# Create your models here.
class SettlePayout(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=False)
    did = models.CharField(max_length=255)
    scode = models.CharField(max_length=255)
    orderno = models.CharField(max_length=255, null=True, default='')
    orderid = models.CharField(max_length=255)
    money = models.BigIntegerField()
    bankname = models.CharField(max_length=255, null=True)
    accountno = models.CharField(max_length=255)
    accountname = models.CharField(max_length=255)
    bankcode = models.CharField(max_length=255)
    is_auto = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False)
    is_report = models.BooleanField(default=False)
    process_bank = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, null=True)
    status = models.BooleanField(default=False,null=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='settle_payout_created_by', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settle_payout'