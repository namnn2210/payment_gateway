import uuid
from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from payout.models import Payout
from payout.repositories.payout_repository import PayoutRepository
from bank.repositories.bank_account_repository import BankAccountRepository
from bank.services.bank_account_service import BankAccountService


class PayoutService:
    """
    Service for Payout model to handle business logic.
    """
    
    @staticmethod
    def get_all_payouts(filters: Optional[Dict[str, Any]] = None, 
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
        return PayoutRepository.get_all(
            filters=filters, 
            search_query=search_query, 
            order_by=order_by,
            user=user
        )
    
    @staticmethod
    def get_payout_by_id(payout_id: int, user: Optional[User] = None) -> Optional[Payout]:
        """
        Get a payout by its ID with permission check.
        
        Args:
            payout_id: The payout ID
            user: User requesting the payout (for permission check)
            
        Returns:
            Payout object or None if not found
        """
        payout = PayoutRepository.get_by_id(payout_id)
        
        # Check permissions if user provided
        if payout and user and not user.is_staff and payout.user != user:
            return None
            
        return payout
    
    @staticmethod
    def get_payout_by_reference(reference: str, user: Optional[User] = None) -> Optional[Payout]:
        """
        Get a payout by its reference with permission check.
        
        Args:
            reference: The payout reference
            user: User requesting the payout (for permission check)
            
        Returns:
            Payout object or None if not found
        """
        payout = PayoutRepository.get_by_reference(reference)
        
        # Check permissions if user provided
        if payout and user and not user.is_staff and payout.user != user:
            return None
            
        return payout
    
    @staticmethod
    def create_payout(data: Dict[str, Any], user: User) -> Payout:
        """
        Create a new payout with validation.
        
        Args:
            data: Dictionary with payout data
            user: User who initiated this payout
            
        Returns:
            Created Payout object
        """
        # Validate required fields
        required_fields = ['bank_account_id', 'amount', 'narration']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"{field.replace('_', ' ').title()} is required")
        
        # Validate bank account exists and user has access
        account = BankAccountService.get_account_by_id(data['bank_account_id'], user)
        if not account:
            raise ValueError(f"Bank account with ID {data['bank_account_id']} not found or you don't have permission to use it")
        
        # Validate account is active
        if not account.status:
            raise ValueError("Cannot create payout to inactive bank account")
        
        # Generate unique reference if not provided
        if 'reference' not in data or not data['reference']:
            data['reference'] = f"PO{uuid.uuid4().hex[:12].upper()}"
        else:
            # Check for duplicate reference
            existing = PayoutRepository.get_by_reference(data['reference'])
            if existing:
                raise ValueError(f"Payout with reference '{data['reference']}' already exists")
        
        # Set initial status if not provided
        if 'status' not in data:
            data['status'] = 'pending'
        
        # Create the payout
        with transaction.atomic():
            return PayoutRepository.create(data, user)
    
    @staticmethod
    def update_payout(payout_id: int, data: Dict[str, Any], user: User) -> Payout:
        """
        Update a payout with validation and permission check.
        
        Args:
            payout_id: The payout ID to update
            data: Dictionary with payout data to update
            user: User requesting the update (for permission check)
            
        Returns:
            Updated Payout object
        """
        payout = PayoutRepository.get_by_id(payout_id)
        if not payout:
            raise ValueError(f"Payout with ID {payout_id} not found")
        
        # Check permissions
        if not user.is_staff and payout.user != user:
            raise ValueError("You do not have permission to update this payout")
        
        # Check if payout can be updated
        if payout.status not in ['pending', 'failed']:
            raise ValueError(f"Cannot update payout with status '{payout.status}'")
        
        # Validate bank account if changing
        if 'bank_account_id' in data:
            account = BankAccountService.get_account_by_id(data['bank_account_id'], user)
            if not account:
                raise ValueError(f"Bank account with ID {data['bank_account_id']} not found or you don't have permission to use it")
            
            # Validate account is active
            if not account.status:
                raise ValueError("Cannot update payout to use inactive bank account")
        
        # Check for duplicate reference if changing
        if 'reference' in data and data['reference'] != payout.reference:
            existing = PayoutRepository.get_by_reference(data['reference'])
            if existing:
                raise ValueError(f"Payout with reference '{data['reference']}' already exists")
        
        with transaction.atomic():
            return PayoutRepository.update(payout, data)
    
    @staticmethod
    def delete_payout(payout_id: int, user: User) -> bool:
        """
        Delete a payout with permission check.
        
        Args:
            payout_id: The payout ID to delete
            user: User requesting the deletion (for permission check)
            
        Returns:
            True if successful
        """
        payout = PayoutRepository.get_by_id(payout_id)
        if not payout:
            raise ValueError(f"Payout with ID {payout_id} not found")
        
        # Check permissions
        if not user.is_staff and payout.user != user:
            raise ValueError("You do not have permission to delete this payout")
        
        # Check if payout can be deleted
        if payout.status not in ['pending', 'failed']:
            raise ValueError(f"Cannot delete payout with status '{payout.status}'")
        
        return PayoutRepository.delete(payout)
    
    @staticmethod
    def process_payout(payout_id: int, user: User) -> Payout:
        """
        Process a payout.
        
        Args:
            payout_id: The payout ID to process
            user: User requesting the processing (for permission check)
            
        Returns:
            Updated Payout object
        """
        payout = PayoutRepository.get_by_id(payout_id)
        if not payout:
            raise ValueError(f"Payout with ID {payout_id} not found")
        
        # Check permissions (usually only admin can process)
        if not user.is_staff:
            raise ValueError("You do not have permission to process this payout")
        
        # Check if payout can be processed
        if payout.status != 'pending':
            raise ValueError(f"Cannot process payout with status '{payout.status}'")
        
        # Here you would typically call an external payment processor
        # For demonstration, we'll just update the status
        
        # In a real system, you would have error handling and actual integration
        # with a payment processor API here
        
        # Update payout status to processing
        payout = PayoutRepository.update_status(payout, 'processing', 'Payment is being processed')
        
        # Simulate processing delay and completion
        # In a real system, this would be handled by a callback or webhook
        payout = PayoutRepository.update_status(payout, 'completed', 'Payment successfully processed')
        
        return payout
    
    @staticmethod
    def cancel_payout(payout_id: int, user: User, reason: str = None) -> Payout:
        """
        Cancel a payout.
        
        Args:
            payout_id: The payout ID to cancel
            user: User requesting the cancellation (for permission check)
            reason: Reason for cancellation
            
        Returns:
            Updated Payout object
        """
        payout = PayoutRepository.get_by_id(payout_id)
        if not payout:
            raise ValueError(f"Payout with ID {payout_id} not found")
        
        # Check permissions
        if not user.is_staff and payout.user != user:
            raise ValueError("You do not have permission to cancel this payout")
        
        # Check if payout can be cancelled
        if payout.status not in ['pending', 'processing']:
            raise ValueError(f"Cannot cancel payout with status '{payout.status}'")
        
        # Update status message with reason if provided
        status_message = 'Payout cancelled by user'
        if reason:
            status_message += f": {reason}"
        
        return PayoutRepository.update_status(payout, 'cancelled', status_message)
    
    @staticmethod
    def get_user_payout_stats(user: User) -> Dict[str, Any]:
        """
        Get payout statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            Dictionary with payout statistics
        """
        return PayoutRepository.get_user_payout_stats(user)
    
    @staticmethod
    def process_pending_payouts(admin_user: User) -> Dict[str, Any]:
        """
        Process all pending payouts.
        
        Args:
            admin_user: Admin user to process payouts
            
        Returns:
            Dictionary with processing results
        """
        if not admin_user.is_staff:
            raise ValueError("Only admin users can process pending payouts")
        
        pending_payouts = PayoutRepository.get_pending_payouts()
        processed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for payout in pending_payouts:
            try:
                PayoutService.process_payout(payout.id, admin_user)
                processed_count += 1
            except Exception as e:
                # Update payout with error
                PayoutRepository.update_status(payout, 'failed', str(e))
                failed_count += 1
                
        return {
            'total': len(pending_payouts),
            'processed': processed_count,
            'failed': failed_count,
            'skipped': skipped_count
        } 