from django.db import models


# Create your models here.
class TransactionHistory(models.Model):
    account_number = models.CharField(max_length=255, null=False)
    amount = models.BigIntegerField(null=False)
    description = models.CharField(max_length=1000, null=False)
    incomingorderid = models.CharField(max_length=255, unique=True, null=True)
    note = models.CharField(max_length=255, null=True)
    orderid = models.CharField(max_length=255, unique=True, null=True)
    scode = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=True)
    transaction_type = models.CharField(max_length=255,null=False)
    transaction_number = models.CharField(max_length=255, null=False, default='')
    transfer_code = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transaction_history'
        unique_together = ('account_number', 'transaction_number')
