from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from bank.models import Bank, BankAccount
from .serializers import (
    BankSerializer, BankAccountSerializer,
    BankAccountCreateSerializer, BankAccountUpdateSerializer
)

class BankViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing banks.
    """
    queryset = Bank.objects.all().order_by('name')
    serializer_class = BankSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'bankcode']
    ordering_fields = ['name', 'created_at', 'status']
    
    def get_queryset(self):
        """
        Filter banks based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Get query parameters
        status_filter = self.request.query_params.get('status')
        
        # Apply filters
        if status_filter:
            if status_filter.lower() == 'true':
                queryset = queryset.filter(status=True)
            elif status_filter.lower() == 'false':
                queryset = queryset.filter(status=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        Toggle the status of a bank.
        """
        bank = self.get_object()
        bank.status = not bank.status
        bank.save()
        
        serializer = self.get_serializer(bank)
        return Response(serializer.data)

class BankAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing bank accounts.
    """
    queryset = BankAccount.objects.all().order_by('-created_at')
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['account_number', 'account_name', 'bank_name__name']
    ordering_fields = ['created_at', 'balance', 'status']
    
    def get_queryset(self):
        """
        Filter bank accounts based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Get query parameters
        status_filter = self.request.query_params.get('status')
        bank_filter = self.request.query_params.get('bank')
        bank_type = self.request.query_params.get('bank_type')
        
        # Apply filters
        if status_filter:
            if status_filter.lower() == 'true':
                queryset = queryset.filter(status=True)
            elif status_filter.lower() == 'false':
                queryset = queryset.filter(status=False)
        
        if bank_filter:
            queryset = queryset.filter(bank_name_id=bank_filter)
        
        if bank_type:
            queryset = queryset.filter(bank_type=bank_type)
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return BankAccountCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BankAccountUpdateSerializer
        return BankAccountSerializer
    
    def perform_create(self, serializer):
        """
        Set the user when creating a bank account.
        """
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        Toggle the status of a bank account.
        """
        bank_account = self.get_object()
        bank_account.status = not bank_account.status
        bank_account.save()
        
        serializer = self.get_serializer(bank_account)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_balance(self, request, pk=None):
        """
        Update the balance of a bank account.
        """
        bank_account = self.get_object()
        
        # Get the new balance from the request
        new_balance = request.data.get('balance')
        if new_balance is None:
            return Response(
                {'detail': 'Balance is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bank_account.balance = int(new_balance)
            bank_account.save()
            
            serializer = self.get_serializer(bank_account)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'detail': 'Invalid balance value.'},
                status=status.HTTP_400_BAD_REQUEST
            ) 