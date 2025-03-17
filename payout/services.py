from .models import Payout
from django.db.models import Sum

class PayoutService:
    """
    Service class for payout-related business logic.
    """
    
    @staticmethod
    def get_payout_by_id(payout_id):
        """
        Get a payout by its ID.
        """
        try:
            return Payout.objects.get(id=payout_id)
        except Payout.DoesNotExist:
            return None
    
    @staticmethod
    def get_payout_by_orderid(orderid):
        """
        Get a payout by its order ID.
        """
        try:
            return Payout.objects.get(orderid=orderid)
        except Payout.DoesNotExist:
            return None
    
    @staticmethod
    def get_total_amount(status=True):
        """
        Get the total amount of payouts with the given status.
        """
        return Payout.objects.filter(status=status).aggregate(total=Sum('money'))['total'] or 0
    
    @staticmethod
    def cancel_payout(payout_id, user):
        """
        Cancel a payout.
        """
        payout = PayoutService.get_payout_by_id(payout_id)
        if not payout:
            return False, "Payout not found"
        
        if payout.status:
            return False, "Cannot cancel a completed payout"
        
        payout.is_cancel = True
        payout.updated_by = user
        payout.save()
        
        return True, "Payout canceled successfully"
    
    @staticmethod
    def report_payout(payout_id, user):
        """
        Mark a payout as reported.
        """
        payout = PayoutService.get_payout_by_id(payout_id)
        if not payout:
            return False, "Payout not found"
        
        payout.is_report = True
        payout.updated_by = user
        payout.save()
        
        return True, "Payout reported successfully" 