from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone

from payout.models import Payout, Timeline, UserTimeline, BalanceTimeline
from .serializers import (
    PayoutSerializer, PayoutCreateSerializer, PayoutUpdateSerializer,
    TimelineSerializer, UserTimelineSerializer, BalanceTimelineSerializer
)
from payout.services import PayoutService

class PayoutViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payouts.
    """
    queryset = Payout.objects.all().order_by('-created_at')
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['orderid', 'accountno', 'accountname', 'bankcode']
    ordering_fields = ['created_at', 'updated_at', 'money', 'status']
    
    def get_queryset(self):
        """
        Filter payouts based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Get query parameters
        status_filter = self.request.query_params.get('status')
        employee_filter = self.request.query_params.get('employee')
        bank_filter = self.request.query_params.get('bank')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        # Apply filters
        if status_filter:
            if status_filter == 'Pending':
                queryset = queryset.filter(status=False)
            elif status_filter == 'Success':
                queryset = queryset.filter(status=True)
            elif status_filter == 'Canceled':
                queryset = queryset.filter(is_cancel=True)
            elif status_filter == 'Reported':
                queryset = queryset.filter(is_report=True)
        
        if employee_filter:
            queryset = queryset.filter(user_id=employee_filter)
        
        if bank_filter:
            queryset = queryset.filter(process_bank_id=bank_filter)
        
        if date_from and date_to:
            queryset = queryset.filter(created_at__range=[date_from, date_to])
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on the action.
        """
        if self.action == 'create':
            return PayoutCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PayoutUpdateSerializer
        return PayoutSerializer
    
    def perform_create(self, serializer):
        """
        Set the user when creating a payout.
        """
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        """
        Set the updated_by user when updating a payout.
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary statistics for payouts.
        """
        queryset = self.get_queryset()
        
        # Calculate summary statistics
        total_count = queryset.count()
        pending_count = queryset.filter(status=False).count()
        success_count = queryset.filter(status=True).count()
        total_amount = queryset.aggregate(total=Sum('money'))['total'] or 0
        success_amount = queryset.filter(status=True).aggregate(total=Sum('money'))['total'] or 0
        
        return Response({
            'total_count': total_count,
            'pending_count': pending_count,
            'success_count': success_count,
            'total_amount': total_amount,
            'success_amount': success_amount,
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a payout.
        """
        payout = self.get_object()
        
        if payout.status:
            return Response(
                {'detail': 'Cannot cancel a completed payout.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payout.is_cancel = True
        payout.updated_by = request.user
        payout.save()
        
        serializer = self.get_serializer(payout)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """
        Mark a payout as reported.
        """
        payout = self.get_object()
        payout.is_report = True
        payout.updated_by = request.user
        payout.save()
        
        serializer = self.get_serializer(payout)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_success(self, request, pk=None):
        """
        Check if a payout was successful.
        """
        payout = self.get_object()
        
        # Use the service to check success
        is_success = payout.staging_status
        
        return Response({
            'is_success': is_success,
            'status': payout.status,
        })

class TimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing timelines.
    """
    queryset = Timeline.objects.all()
    serializer_class = TimelineSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing user timelines.
    """
    queryset = UserTimeline.objects.all()
    serializer_class = UserTimelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter user timelines to show only the current user's timelines.
        """
        queryset = super().get_queryset()
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset

class BalanceTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing balance timelines.
    """
    queryset = BalanceTimeline.objects.all()
    serializer_class = BalanceTimelineSerializer
    permission_classes = [permissions.IsAuthenticated] 