from typing import List, Optional, Dict, Any
from django.contrib.auth.models import User

from bank.models import BankAccount
from bank.repositories.bank_account_repository import BankAccountRepository
from bank.repositories.bank_repository import BankRepository


class BankAccountService:
    """
    Service for BankAccount model to handle business logic.
    """
    
    @staticmethod
    def get_all_accounts(filters: Optional[Dict[str, Any]] = None, 
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
        return BankAccountRepository.get_all(
            filters=filters, 
            search_query=search_query, 
            order_by=order_by,
            user=user
        )
    
    @staticmethod
    def get_account_by_id(account_id: int, user: Optional[User] = None) -> Optional[BankAccount]:
        """
        Get a bank account by its ID with permission check.
        
        Args:
            account_id: The bank account ID
            user: User requesting the account (for permission check)
            
        Returns:
            BankAccount object or None if not found
        """
        account = BankAccountRepository.get_by_id(account_id)
        
        # Check permissions if user provided
        if account and user and not user.is_staff and account.user != user:
            return None
            
        return account
    
    @staticmethod
    def create_account(data: Dict[str, Any], user: User) -> BankAccount:
        """
        Create a new bank account with validation.
        
        Args:
            data: Dictionary with bank account data
            user: User who owns this account
            
        Returns:
            Created BankAccount object
        """
        # Validate required fields
        required_fields = ['account_number', 'account_name', 'bank_name_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"{field.replace('_', ' ').title()} is required")
        
        # Validate bank exists
        bank = BankRepository.get_by_id(data['bank_name_id'])
        if not bank:
            raise ValueError(f"Bank with ID {data['bank_name_id']} not found")
        
        # Check for duplicate account number for this bank
        existing_accounts = BankAccountRepository.get_all({
            'account_number': data['account_number'],
            'bank_name': bank
        })
        
        if existing_accounts:
            raise ValueError(f"Account number '{data['account_number']}' already exists for this bank")
        
        # Create the account
        return BankAccountRepository.create(data, user)
    
    @staticmethod
    def update_account(account_id: int, data: Dict[str, Any], user: User) -> BankAccount:
        """
        Update a bank account with validation and permission check.
        
        Args:
            account_id: The bank account ID to update
            data: Dictionary with bank account data to update
            user: User requesting the update (for permission check)
            
        Returns:
            Updated BankAccount object
        """
        account = BankAccountRepository.get_by_id(account_id)
        if not account:
            raise ValueError(f"Bank account with ID {account_id} not found")
        
        # Check permissions
        if not user.is_staff and account.user != user:
            raise ValueError("You do not have permission to update this account")
        
        # Check for duplicate account number if changing number or bank
        if ('account_number' in data and data['account_number'] != account.account_number) or \
           ('bank_name_id' in data):
            
            bank_id = data.get('bank_name_id', account.bank_name.id if account.bank_name else None)
            account_number = data.get('account_number', account.account_number)
            
            bank = BankRepository.get_by_id(bank_id)
            if not bank:
                raise ValueError(f"Bank with ID {bank_id} not found")
                
            existing_accounts = BankAccountRepository.get_all({
                'account_number': account_number,
                'bank_name': bank
            })
            
            if existing_accounts and existing_accounts[0].id != account.id:
                raise ValueError(f"Account number '{account_number}' already exists for this bank")
        
        return BankAccountRepository.update(account, data)
    
    @staticmethod
    def delete_account(account_id: int, user: User) -> bool:
        """
        Delete a bank account with permission check.
        
        Args:
            account_id: The bank account ID to delete
            user: User requesting the deletion (for permission check)
            
        Returns:
            True if successful
        """
        account = BankAccountRepository.get_by_id(account_id)
        if not account:
            raise ValueError(f"Bank account with ID {account_id} not found")
        
        # Check permissions
        if not user.is_staff and account.user != user:
            raise ValueError("You do not have permission to delete this account")
        
        # Check if account has any payouts (should be done in a separate module, added here as an example)
        # if account.payouts.exists():
        #     raise ValueError("Cannot delete account with associated payouts")
        
        return BankAccountRepository.delete(account)
    
    @staticmethod
    def toggle_account_status(account_id: int, user: User) -> BankAccount:
        """
        Toggle the status of a bank account with permission check.
        
        Args:
            account_id: The bank account ID to toggle status
            user: User requesting the toggle (for permission check)
            
        Returns:
            Updated BankAccount object
        """
        account = BankAccountRepository.get_by_id(account_id)
        if not account:
            raise ValueError(f"Bank account with ID {account_id} not found")
        
        # Check permissions
        if not user.is_staff and account.user != user:
            raise ValueError("You do not have permission to toggle this account's status")
        
        return BankAccountRepository.toggle_status(account)
    
    @staticmethod
    def update_account_balance(account_id: int, balance: int, user: User) -> BankAccount:
        """
        Update the balance of a bank account with permission check.
        
        Args:
            account_id: The bank account ID to update
            balance: New balance amount
            user: User requesting the update (for permission check)
            
        Returns:
            Updated BankAccount object
        """
        account = BankAccountRepository.get_by_id(account_id)
        if not account:
            raise ValueError(f"Bank account with ID {account_id} not found")
        
        # Check permissions - typically only admin should update balance
        if not user.is_staff:
            raise ValueError("You do not have permission to update account balance")
        
        return BankAccountRepository.update_balance(account, balance) 