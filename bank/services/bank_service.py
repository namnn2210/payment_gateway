from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User

from bank.models import Bank
from bank.repositories.bank_repository import BankRepository


class BankService:
    """
    Service for Bank model to handle business logic.
    """
    
    @staticmethod
    def get_all_banks(filters: Optional[Dict[str, Any]] = None, 
                      search_query: Optional[str] = None,
                      order_by: Optional[str] = None) -> List[Bank]:
        """
        Get all banks with optional filtering, searching and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter on
            search_query: Text to search for in bank name or code
            order_by: Field to order by (prepend with '-' for descending)
            
        Returns:
            List of Bank objects
        """
        return BankRepository.get_all(filters=filters, search_query=search_query, order_by=order_by)
    
    @staticmethod
    def get_bank_by_id(bank_id: int) -> Optional[Bank]:
        """
        Get a bank by its ID.
        
        Args:
            bank_id: The bank ID
            
        Returns:
            Bank object or None if not found
        """
        return BankRepository.get_by_id(bank_id)
    
    @staticmethod
    def create_bank(data: Dict[str, Any], user: User) -> Bank:
        """
        Create a new bank with validation.
        
        Args:
            data: Dictionary with bank data
            user: User creating the bank
            
        Returns:
            Created Bank object
        """
        # Validate bank data
        if 'name' not in data or not data['name']:
            raise ValueError('Bank name is required')
        
        if 'code' not in data or not data['code']:
            raise ValueError('Bank code is required')
        
        # Check for duplicate bank code
        existing = BankRepository.get_by_code(data['code'])
        if existing:
            raise ValueError(f"Bank with code '{data['code']}' already exists")
        
        # Create the bank
        return BankRepository.create(data)
    
    @staticmethod
    def update_bank(bank_id: int, data: Dict[str, Any]) -> Bank:
        """
        Update a bank with validation.
        
        Args:
            bank_id: The bank ID to update
            data: Dictionary with bank data to update
            
        Returns:
            Updated Bank object
        """
        bank = BankRepository.get_by_id(bank_id)
        if not bank:
            raise ValueError(f"Bank with ID {bank_id} not found")
        
        # Check for duplicate bank code if changing code
        if 'code' in data and data['code'] != bank.code:
            existing = BankRepository.get_by_code(data['code'])
            if existing:
                raise ValueError(f"Bank with code '{data['code']}' already exists")
        
        return BankRepository.update(bank, data)
    
    @staticmethod
    def delete_bank(bank_id: int) -> bool:
        """
        Delete a bank with validation.
        
        Args:
            bank_id: The bank ID to delete
            
        Returns:
            True if successful
        """
        bank = BankRepository.get_by_id(bank_id)
        if not bank:
            raise ValueError(f"Bank with ID {bank_id} not found")
        
        # Check if bank has any bank accounts
        if bank.bank_accounts.exists():
            raise ValueError("Cannot delete bank with associated bank accounts")
        
        return BankRepository.delete(bank)
    
    @staticmethod
    def toggle_bank_status(bank_id: int) -> Bank:
        """
        Toggle the status of a bank.
        
        Args:
            bank_id: The bank ID to toggle status
            
        Returns:
            Updated Bank object
        """
        bank = BankRepository.get_by_id(bank_id)
        if not bank:
            raise ValueError(f"Bank with ID {bank_id} not found")
        
        return BankRepository.toggle_status(bank) 