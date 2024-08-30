from rest_framework import serializers
from .models import SettlePayout
from cms.serializers import UserSerializer
from bank.serializers import BankSerializer

class SettlePayoutSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    process_bank = BankSerializer(read_only=True)
    class Meta:
        model = SettlePayout
        fields = ('id','user','did', 'scode', 'orderno', 'orderid', 'money', 'bankname', 'accountno', 'accountname','bankcode','is_auto','is_cancel','is_report', 'process_bank', 'status', 'created_at', 'updated_at','updated_by')