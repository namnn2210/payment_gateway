from typing import List, Optional, Dict, Any, Union
from django.db.models import Q
from django.contrib.auth.models import User

from payout.models import Payout
from bank.models import BankAccount


class PayoutRepository:
    """
    Repository for Payout model to handle all database operations.
    """
    
    @staticmethod
    def get_all(filters: Optional[Dict[str, Any]] = None, 
                search_query: Optional[str] = None,
                order_by: Optional[str] = None,
                user: Optional[User] = None) -> List[Payout]:
        """
        Get all payouts with optional filtering, searching and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter on
            search_query: Text to search for in reference, account details, etc.
            order_by: Field to order by (prepend with '-' for descending)
            user: If not admin, limit to payouts initiated by this user
            
        Returns:
            List of Payout objects
        """
        queryset = Payout.objects.all()
        
        # Filter by user if not admin
        if user and not user.is_staff:
            queryset = queryset.filter(user=user)
        
        # Apply filters
        if filters:
            queryset = queryset.filter(**filters)
        
        # Apply search
        if search_query:
            queryset = queryset.filter(
                Q(reference__icontains=search_query) | 
                Q(narration__icontains=search_query) |
                Q(bank_account__account_name__icontains=search_query) |
                Q(bank_account__account_number__icontains=search_query) |
                Q(bank_account__bank_name__name__icontains=search_query)
            )
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-created_at')
            
        return list(queryset)
    
    @staticmethod
    def get_by_id(payout_id: int) -> Optional[Payout]:
        """
        Get a payout by its ID.
        
        Args:
            payout_id: The payout ID
            
        Returns:
            Payout object or None if not found
        """
        try:
            return Payout.objects.get(id=payout_id)
        except Payout.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_reference(reference: str) -> Optional[Payout]:
        """
        Get a payout by its reference.
        
        Args:
            reference: The payout reference
            
        Returns:
            Payout object or None if not found
        """
        try:
            return Payout.objects.get(reference=reference)
        except Payout.DoesNotExist:
            return None
    
    @staticmethod
    def create(data: Dict[str, Any], user: User) -> Payout:
        """
        Create a new payout.
        
        Args:
            data: Dictionary with payout data
            user: User who initiated this payout
            
        Returns:
            Created Payout object
        """
        # Handle bank_account_id -> bank_account conversion
        if 'bank_account_id' in data:
            data['bank_account'] = BankAccount.objects.get(id=data.pop('bank_account_id'))
            
        return Payout.objects.create(user=user, **data)
    
    @staticmethod
    def update(payout: Payout, data: Dict[str, Any]) -> Payout:
        """
        Update a payout.
        
        Args:
            payout: Payout object to update
            data: Dictionary with payout data to update
            
        Returns:
            Updated Payout object
        """
        # Handle bank_account_id -> bank_account conversion
        if 'bank_account_id' in data:
            data['bank_account'] = BankAccount.objects.get(id=data.pop('bank_account_id'))
            
        for key, value in data.items():
            setattr(payout, key, value)
        
        payout.save()
        return payout
    
    @staticmethod
    def delete(payout: Payout) -> bool:
        """
        Delete a payout.
        
        Args:
            payout: Payout object to delete
            
        Returns:
            True if successful
        """
        payout.delete()
        return True
    
    @staticmethod
    def update_status(payout: Payout, status: str, status_message: Optional[str] = None) -> Payout:
        """
        Update the status of a payout.
        
        Args:
            payout: Payout object to update
            status: New status
            status_message: Optional status message
            
        Returns:
            Updated Payout object
        """
        payout.status = status
        if status_message:
            payout.status_message = status_message
        payout.save()
        return payout
    
    @staticmethod
    def get_pending_payouts() -> List[Payout]:
        """
        Get all pending payouts.
        
        Returns:
            List of pending Payout objects
        """
        return list(Payout.objects.filter(status='pending'))
    
    @staticmethod
    def get_user_payout_stats(user: User) -> Dict[str, Any]:
        """
        Get payout statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            Dictionary with payout statistics
        """
        user_payouts = Payout.objects.filter(user=user)
        total_count = user_payouts.count()
        successful_count = user_payouts.filter(status='completed').count()
        failed_count = user_payouts.filter(status='failed').count()
        pending_count = user_payouts.filter(status='pending').count()
        
        total_amount = sum(payout.amount for payout in user_payouts)
        successful_amount = sum(payout.amount for payout in user_payouts.filter(status='completed'))
        
        return {
            'total_count': total_count,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'pending_count': pending_count,
            'total_amount': total_amount,
            'successful_amount': successful_amount
        } 