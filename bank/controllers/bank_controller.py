from typing import Dict, Any, List
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from bank.models import Bank
from bank.services.bank_service import BankService
from bank.api.serializers import BankSerializer


class BankController(APIView):
    """
    Controller for bank-related API endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, bank_id: int = None) -> Response:
        """
        Get a list of all banks or a specific bank by ID.
        
        Args:
            request: The HTTP request
            bank_id: Optional bank ID to retrieve a specific bank
            
        Returns:
            Response with bank(s) data
        """
        try:
            # Get specific bank by ID
            if bank_id:
                bank = BankService.get_bank_by_id(bank_id)
                if not bank:
                    return Response(
                        {"error": f"Bank with ID {bank_id} not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = BankSerializer(bank)
                return Response(serializer.data)
            
            # Get all banks with filters, search, and ordering
            filters = {}
            search_query = request.query_params.get('search')
            order_by = request.query_params.get('order_by')
            
            # Apply status filter if provided
            if 'status' in request.query_params:
                filters['status'] = request.query_params.get('status') == 'true'
            
            banks = BankService.get_all_banks(
                filters=filters,
                search_query=search_query,
                order_by=order_by
            )
            
            serializer = BankSerializer(banks, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request: Request) -> Response:
        """
        Create a new bank.
        
        Args:
            request: The HTTP request with bank data
            
        Returns:
            Response with created bank data
        """
        # Only admin users can create banks
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to create banks"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            bank = BankService.create_bank(request.data, request.user)
            serializer = BankSerializer(bank)
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
    
    def put(self, request: Request, bank_id: int) -> Response:
        """
        Update an existing bank.
        
        Args:
            request: The HTTP request with bank data
            bank_id: The bank ID to update
            
        Returns:
            Response with updated bank data
        """
        # Only admin users can update banks
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to update banks"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            bank = BankService.update_bank(bank_id, request.data)
            serializer = BankSerializer(bank)
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
    
    def delete(self, request: Request, bank_id: int) -> Response:
        """
        Delete a bank.
        
        Args:
            request: The HTTP request
            bank_id: The bank ID to delete
            
        Returns:
            Response with success or error message
        """
        # Only admin users can delete banks
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to delete banks"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            BankService.delete_bank(bank_id)
            return Response(
                {"message": f"Bank with ID {bank_id} deleted successfully"},
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


class BankStatusController(APIView):
    """
    Controller for toggling bank status.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request: Request, bank_id: int) -> Response:
        """
        Toggle the status of a bank.
        
        Args:
            request: The HTTP request
            bank_id: The bank ID to toggle status
            
        Returns:
            Response with updated bank data
        """
        try:
            bank = BankService.toggle_bank_status(bank_id)
            serializer = BankSerializer(bank)
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