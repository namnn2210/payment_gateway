from django.db import models
from bank.models import BankAccount

class CID(models.Model):
    name = models.TextField()
    key = models.TextField(null=True)
    cardtype = models.IntegerField(null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'cid'


        
