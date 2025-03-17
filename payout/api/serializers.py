from rest_framework import serializers
from payout.models import Payout, Timeline, UserTimeline, BalanceTimeline
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeline
        fields = '__all__'

class UserTimelineSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    timeline = TimelineSerializer(read_only=True)
    
    class Meta:
        model = UserTimeline
        fields = '__all__'

class BalanceTimelineSerializer(serializers.ModelSerializer):
    timeline = TimelineSerializer(read_only=True)
    
    class Meta:
        model = BalanceTimeline
        fields = '__all__'

class PayoutSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Payout
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PayoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            'scode', 'orderno', 'orderid', 'money', 'bankname', 
            'accountno', 'accountname', 'bankcode', 'memo', 
            'partner_bankcode', 'process_bank'
        ]
    
    def create(self, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        
        # Create the payout with the user
        payout = Payout.objects.create(
            user=user,
            **validated_data
        )
        
        return payout

class PayoutUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            'status', 'is_auto', 'is_cancel', 'is_report', 
            'process_bank', 'bankcode', 'partner_bankcode'
        ]
    
    def update(self, instance, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        
        # Update the payout
        instance.updated_by = user
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance 