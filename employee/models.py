from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class EmployeeDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=False)
    amount = models.BigIntegerField()
    bankname = models.CharField(max_length=255, default='', null=True)
    accountno = models.CharField(max_length=255, null=False, default='')
    accountname = models.CharField(max_length=255, null=False, default='')
    bankcode = models.CharField(max_length=255, default='', null=False)
    note = models.CharField(max_length=255, null=True, default='')
    status = models.BooleanField(default=False,null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_updated_by', default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employee_deposit'