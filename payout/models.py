from django.db import models
from django.contrib.auth.models import User
from bank.models import Bank

# Create your models here.
class Payout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    did = models.CharField(max_length=255, blank=True)
    scode = models.CharField(max_length=255)
    orderno = models.CharField(max_length=255, null=True, default='')
    orderid = models.CharField(max_length=255)
    money = models.BigIntegerField()
    bankname = models.CharField(max_length=255, null=True)
    accountno = models.CharField(max_length=255)
    accountname = models.CharField(max_length=255)
    bankcode = models.CharField(max_length=255)
    partner_bankcode = models.CharField(max_length=10, null=True)
    is_auto = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False)
    is_report = models.BooleanField(default=False)
    process_bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True, blank=False)
    status = models.BooleanField(default=False,null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_created_by', null=True, blank=False)
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
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=False)
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, null=False)
    status = models.BooleanField(default=False,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_timeline'
    

        

        
    
    