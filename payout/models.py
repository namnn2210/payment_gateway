from django.db import models
from django.contrib.auth.models import User
from bank.models import Bank, BankAccount

# Create your models here.
class Payout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    did = models.CharField(max_length=255, default='', null=True)
    scode = models.CharField(max_length=255, null=False)
    orderno = models.CharField(max_length=255, default='', null=False)
    orderid = models.CharField(max_length=255, null=False)
    money = models.BigIntegerField()
    bankname = models.CharField(max_length=255, default='', null=True)
    accountno = models.CharField(max_length=255, null=False)
    accountname = models.CharField(max_length=255, null=False)
    bankcode = models.CharField(max_length=255, default='', null=False)
    partner_bankcode = models.CharField(max_length=10, default='', null=False)
    is_auto = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False)
    is_report = models.BooleanField(default=False)
    process_bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True)
    status = models.BooleanField(default=False,null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_created_by', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payout'
        
class Timeline(models.Model):
    name = models.CharField(max_length=100)
    start_at = models.TimeField()
    end_at = models.TimeField()
    status = models.BooleanField(default=False,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return self.name
    
    class Meta:
        db_table = 'timeline'
        
class UserTimeline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, null=False)
    status = models.BooleanField(default=False,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_timeline'
        
class BalanceTimeline(models.Model):
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, null=False)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, null=False)
    balance = models.BigIntegerField(default=0)
    status = models.BooleanField(default=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'balance_timeline'