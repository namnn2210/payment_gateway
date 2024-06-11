from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Bank(models.Model):
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'bank'


class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=False)
    bank_name = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, null=False)
    account_number = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255, default='')
    username = models.CharField(max_length=255, default='')
    password = models.CharField(max_length=255, default='')
    balance = models.BigIntegerField(default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_account'

