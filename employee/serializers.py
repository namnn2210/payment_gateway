from rest_framework import serializers
from .models import EmployeeDeposit

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDeposit
        fields = ('id', 'amount', 'bankname', 'accountno', 'accountname', 'bankcode', 'note', 'status', 'created_at', 'updated_at')