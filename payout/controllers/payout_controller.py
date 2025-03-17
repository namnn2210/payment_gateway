from typing import Dict, Any, List
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from payout.models import Payout
from payout.services.payout_service import PayoutService
from payout.api.serializers import PayoutSerializer


class PayoutController(APIView):
    """
    Controller for payout-related API endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, payout_id: int = None) -> Response:
        """
        Get a list of all payouts or a specific payout by ID.
        
        Args:
            request: The HTTP request
            payout_id: Optional payout ID to retrieve a specific payout
            
        Returns:
            Response with payout(s) data
        """
        try:
            # Get specific payout by ID
            if payout_id:
                payout = PayoutService.get_payout_by_id(payout_id, request.user)
                if not payout:
                    return Response(
                        {"error": f"Payout with ID {payout_id} not found or you don't have permission to view it"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = PayoutSerializer(payout)
                return Response(serializer.data)
            
            # Get all payouts with filters, search, and ordering
            filters = {}
            search_query = request.query_params.get('search')
            order_by = request.query_params.get('order_by')
            
            # Apply status filter if provided
            if 'status' in request.query_params:
                filters['status'] = request.query_params.get('status')
            
            # Apply bank account filter if provided
            if 'bank_account' in request.query_params:
                filters['bank_account__id'] = request.query_params.get('bank_account')
            
            payouts = PayoutService.get_all_payouts(
                filters=filters,
                search_query=search_query,
                order_by=order_by,
                user=request.user  # For permission filtering
            )
            
            serializer = PayoutSerializer(payouts, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request: Request) -> Response:
        """
        Create a new payout.
        
        Args:
            request: The HTTP request with payout data
            
        Returns:
            Response with created payout data
        """
        try:
            payout = PayoutService.create_payout(request.data, request.user)
            serializer = PayoutSerializer(payout)
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
    
    def put(self, request: Request, payout_id: int) -> Response:
        """
        Update an existing payout.
        
        Args:
            request: The HTTP request with payout data
            payout_id: The payout ID to update
            
        Returns:
            Response with updated payout data
        """
        try:
            payout = PayoutService.update_payout(payout_id, request.data, request.user)
            serializer = PayoutSerializer(payout)
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
    
    def delete(self, request: Request, payout_id: int) -> Response:
        """
        Delete a payout.
        
        Args:
            request: The HTTP request
            payout_id: The payout ID to delete
            
        Returns:
            Response with success or error message
        """
        try:
            PayoutService.delete_payout(payout_id, request.user)
            return Response(
                {"message": f"Payout with ID {payout_id} deleted successfully"},
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


class PayoutProcessController(APIView):
    """
    Controller for processing payouts.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request: Request, payout_id: int) -> Response:
        """
        Process a specific payout.
        
        Args:
            request: The HTTP request
            payout_id: The payout ID to process
            
        Returns:
            Response with processed payout data
        """
        try:
            payout = PayoutService.process_payout(payout_id, request.user)
            serializer = PayoutSerializer(payout)
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


class PayoutCancelController(APIView):
    """
    Controller for cancelling payouts.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request, payout_id: int) -> Response:
        """
        Cancel a payout.
        
        Args:
            request: The HTTP request
            payout_id: The payout ID to cancel
            
        Returns:
            Response with cancelled payout data
        """
        try:
            reason = request.data.get('reason')
            payout = PayoutService.cancel_payout(payout_id, request.user, reason)
            serializer = PayoutSerializer(payout)
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


class PayoutBulkProcessController(APIView):
    """
    Controller for bulk processing of payouts.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request: Request) -> Response:
        """
        Process all pending payouts.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response with processing results
        """
        try:
            results = PayoutService.process_pending_payouts(request.user)
            return Response(results)
            
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


class PayoutStatsController(APIView):
    """
    Controller for payout statistics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        """
        Get payout statistics for the current user.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response with payout statistics
        """
        try:
            stats = PayoutService.get_user_payout_stats(request.user)
            return Response(stats)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 