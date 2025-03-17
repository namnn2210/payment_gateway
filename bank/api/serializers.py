from rest_framework import serializers
from bank.models import Bank, BankAccount
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    bank_name = BankSerializer(read_only=True)
    
    class Meta:
        model = BankAccount
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_logged_in']

class BankAccountCreateSerializer(serializers.ModelSerializer):
    bank_name_id = serializers.PrimaryKeyRelatedField(
        queryset=Bank.objects.all(),
        source='bank_name',
        write_only=True
    )
    
    class Meta:
        model = BankAccount
        fields = [
            'bank_name_id', 'account_number', 'account_name', 
            'username', 'password', 'corp_id', 'bank_type', 'status'
        ]
    
    def create(self, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        
        # Create the bank account with the user
        bank_account = BankAccount.objects.create(
            user=user,
            **validated_data
        )
        
        return bank_account

class BankAccountUpdateSerializer(serializers.ModelSerializer):
    bank_name_id = serializers.PrimaryKeyRelatedField(
        queryset=Bank.objects.all(),
        source='bank_name',
        required=False
    )
    
    class Meta:
        model = BankAccount
        fields = [
            'bank_name_id', 'account_name', 'username', 
            'password', 'corp_id', 'balance', 'bank_type', 'status'
        ]
        read_only_fields = ['account_number'] 