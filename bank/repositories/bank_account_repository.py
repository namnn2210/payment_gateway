from typing import List, Optional, Dict, Any, Union
from django.db.models import Q
from django.contrib.auth.models import User

from bank.models import BankAccount, Bank


class BankAccountRepository:
    """
    Repository for BankAccount model to handle all database operations.
    """
    
    @staticmethod
    def get_all(filters: Optional[Dict[str, Any]] = None, 
                search_query: Optional[str] = None,
                order_by: Optional[str] = None,
                user: Optional[User] = None) -> List[BankAccount]:
        """
        Get all bank accounts with optional filtering, searching and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter on
            search_query: Text to search for in account name, number or bank name
            order_by: Field to order by (prepend with '-' for descending)
            user: If not admin, limit to accounts owned by this user
            
        Returns:
            List of BankAccount objects
        """
        queryset = BankAccount.objects.all()
        
        # Filter by user if not admin
        if user and not user.is_staff:
            queryset = queryset.filter(user=user)
        
        # Apply filters
        if filters:
            queryset = queryset.filter(**filters)
        
        # Apply search
        if search_query:
            queryset = queryset.filter(
                Q(account_number__icontains=search_query) | 
                Q(account_name__icontains=search_query) |
                Q(bank_name__name__icontains=search_query)
            )
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-created_at')
            
        return list(queryset)
    
    @staticmethod
    def get_by_id(account_id: int) -> Optional[BankAccount]:
        """
        Get a bank account by its ID.
        
        Args:
            account_id: The bank account ID
            
        Returns:
            BankAccount object or None if not found
        """
        try:
            return BankAccount.objects.get(id=account_id)
        except BankAccount.DoesNotExist:
            return None
    
    @staticmethod
    def create(data: Dict[str, Any], user: User) -> BankAccount:
        """
        Create a new bank account.
        
        Args:
            data: Dictionary with bank account data
            user: User who owns this account
            
        Returns:
            Created BankAccount object
        """
        # Handle bank_name_id -> bank_name conversion
        if 'bank_name_id' in data:
            data['bank_name'] = Bank.objects.get(id=data.pop('bank_name_id'))
            
        return BankAccount.objects.create(user=user, **data)
    
    @staticmethod
    def update(account: BankAccount, data: Dict[str, Any]) -> BankAccount:
        """
        Update a bank account.
        
        Args:
            account: BankAccount object to update
            data: Dictionary with bank account data to update
            
        Returns:
            Updated BankAccount object
        """
        # Handle bank_name_id -> bank_name conversion
        if 'bank_name_id' in data:
            data['bank_name'] = Bank.objects.get(id=data.pop('bank_name_id'))
            
        for key, value in data.items():
            setattr(account, key, value)
        
        account.save()
        return account
    
    @staticmethod
    def delete(account: BankAccount) -> bool:
        """
        Delete a bank account.
        
        Args:
            account: BankAccount object to delete
            
        Returns:
            True if successful
        """
        account.delete()
        return True
    
    @staticmethod
    def toggle_status(account: BankAccount) -> BankAccount:
        """
        Toggle the status of a bank account.
        
        Args:
            account: BankAccount object to toggle status
            
        Returns:
            Updated BankAccount object
        """
        account.status = not account.status
        account.save()
        return account
    
    @staticmethod
    def update_balance(account: BankAccount, balance: int) -> BankAccount:
        """
        Update the balance of a bank account.
        
        Args:
            account: BankAccount object to update
            balance: New balance amount
            
        Returns:
            Updated BankAccount object
        """
        account.balance = balance
        account.save()
        return account 