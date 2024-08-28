from rest_framework import serializers
from .models import BankAccount, Bank

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('id', 'bank_name', 'account_number', 'account_name', 'username', 'password', 'balance', 'bank_type', 'status', 'created_at', 'updated_at')

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ('id', 'name', 'icon', 'bankcode', 'status', 'created_at', 'updated_at')