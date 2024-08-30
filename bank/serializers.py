from rest_framework import serializers
from .models import BankAccount, Bank
from cms.serializers import UserSerializer
class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ('id', 'name', 'icon', 'bankcode', 'status', 'created_at', 'updated_at')

class BankAccountSerializer(serializers.ModelSerializer):
    bank_name = BankSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    class Meta:
        model = BankAccount
        fields = ('id','user', 'bank_name', 'account_number', 'account_name', 'username', 'password', 'balance', 'bank_type', 'status', 'created_at', 'updated_at')