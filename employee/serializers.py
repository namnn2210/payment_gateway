from rest_framework import serializers
from .models import EmployeeDeposit, EmployeeWorkingSession
from cms.serializers import UserSerializer

class DepositSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = EmployeeDeposit
        fields = ('id', 'user', 'amount', 'bankname', 'accountno', 'accountname', 'bankcode', 'note', 'status', 'created_at','updated_by', 'updated_at')

class EmployeeSessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = EmployeeWorkingSession
        fields = ('id', 'user', 'start_time', 'end_time', 'status')

