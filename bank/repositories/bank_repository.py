from typing import List, Optional, Dict, Any, Union
from django.db.models import Q

from bank.models import Bank


class BankRepository:
    """
    Repository for Bank model to handle all database operations.
    """
    
    @staticmethod
    def get_all(filters: Optional[Dict[str, Any]] = None, 
                search_query: Optional[str] = None,
                order_by: Optional[str] = None) -> List[Bank]:
        """
        Get all banks with optional filtering, searching and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter on
            search_query: Text to search for in name or bankcode
            order_by: Field to order by (prepend with '-' for descending)
            
        Returns:
            List of Bank objects
        """
        queryset = Bank.objects.all()
        
        # Apply filters
        if filters:
            queryset = queryset.filter(**filters)
        
        # Apply search
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(bankcode__icontains=search_query)
            )
        
        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('name')
            
        return list(queryset)
    
    @staticmethod
    def get_by_id(bank_id: int) -> Optional[Bank]:
        """
        Get a bank by its ID.
        
        Args:
            bank_id: The bank ID
            
        Returns:
            Bank object or None if not found
        """
        try:
            return Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return None
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Bank:
        """
        Create a new bank.
        
        Args:
            data: Dictionary with bank data
            
        Returns:
            Created Bank object
        """
        return Bank.objects.create(**data)
    
    @staticmethod
    def update(bank: Bank, data: Dict[str, Any]) -> Bank:
        """
        Update a bank.
        
        Args:
            bank: Bank object to update
            data: Dictionary with bank data to update
            
        Returns:
            Updated Bank object
        """
        for key, value in data.items():
            setattr(bank, key, value)
        
        bank.save()
        return bank
    
    @staticmethod
    def delete(bank: Bank) -> bool:
        """
        Delete a bank.
        
        Args:
            bank: Bank object to delete
            
        Returns:
            True if successful
        """
        bank.delete()
        return True
    
    @staticmethod
    def toggle_status(bank: Bank) -> Bank:
        """
        Toggle the status of a bank.
        
        Args:
            bank: Bank object to toggle status
            
        Returns:
            Updated Bank object
        """
        bank.status = not bank.status
        bank.save()
        return bank 