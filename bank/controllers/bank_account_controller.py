from typing import Dict, Any, List
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from bank.models import BankAccount
from bank.services.bank_account_service import BankAccountService
from bank.api.serializers import BankAccountSerializer


class BankAccountController(APIView):
    """
    Controller for bank account-related API endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, account_id: int = None) -> Response:
        """
        Get a list of all bank accounts or a specific bank account by ID.
        
        Args:
            request: The HTTP request
            account_id: Optional bank account ID to retrieve a specific account
            
        Returns:
            Response with bank account(s) data
        """
        try:
            # Get specific bank account by ID
            if account_id:
                account = BankAccountService.get_account_by_id(account_id, request.user)
                if not account:
                    return Response(
                        {"error": f"Bank account with ID {account_id} not found or you don't have permission to view it"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = BankAccountSerializer(account)
                return Response(serializer.data)
            
            # Get all bank accounts with filters, search, and ordering
            filters = {}
            search_query = request.query_params.get('search')
            order_by = request.query_params.get('order_by')
            
            # Apply status filter if provided
            if 'status' in request.query_params:
                filters['status'] = request.query_params.get('status') == 'true'
            
            # Apply bank filter if provided
            if 'bank_name' in request.query_params:
                filters['bank_name__id'] = request.query_params.get('bank_name')
            
            accounts = BankAccountService.get_all_accounts(
                filters=filters,
                search_query=search_query,
                order_by=order_by,
                user=request.user  # For permission filtering
            )
            
            serializer = BankAccountSerializer(accounts, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request: Request) -> Response:
        """
        Create a new bank account.
        
        Args:
            request: The HTTP request with bank account data
            
        Returns:
            Response with created bank account data
        """
        try:
            account = BankAccountService.create_account(request.data, request.user)
            serializer = BankAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request: Request, account_id: int) -> Response:
        """
        Update an existing bank account.
        
        Args:
            request: The HTTP request with bank account data
            account_id: The bank account ID to update
            
        Returns:
            Response with updated bank account data
        """
        try:
            account = BankAccountService.update_account(account_id, request.data, request.user)
            serializer = BankAccountSerializer(account)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request: Request, account_id: int) -> Response:
        """
        Delete a bank account.
        
        Args:
            request: The HTTP request
            account_id: The bank account ID to delete
            
        Returns:
            Response with success or error message
        """
        try:
            BankAccountService.delete_account(account_id, request.user)
            return Response(
                {"message": f"Bank account with ID {account_id} deleted successfully"},
                status=status.HTTP_200_OK
            )
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BankAccountStatusController(APIView):
    """
    Controller for toggling bank account status.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request, account_id: int) -> Response:
        """
        Toggle the status of a bank account.
        
        Args:
            request: The HTTP request
            account_id: The bank account ID to toggle status
            
        Returns:
            Response with updated bank account data
        """
        try:
            account = BankAccountService.toggle_account_status(account_id, request.user)
            serializer = BankAccountSerializer(account)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BankAccountBalanceController(APIView):
    """
    Controller for updating bank account balance.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request, account_id: int) -> Response:
        """
        Update the balance of a bank account.
        
        Args:
            request: The HTTP request
            account_id: The bank account ID to update balance
            
        Returns:
            Response with updated bank account data
        """
        try:
            if 'balance' not in request.data:
                return Response(
                    {"error": "Balance is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            balance = int(request.data['balance'])
            account = BankAccountService.update_account_balance(account_id, balance, request.user)
            serializer = BankAccountSerializer(account)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 