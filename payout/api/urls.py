from django.urls import path
from payout.controllers.payout_controller import (
    PayoutController, 
    PayoutProcessController, 
    PayoutCancelController,
    PayoutBulkProcessController,
    PayoutStatsController
)

urlpatterns = [
    # Payout URLs
    path('payouts/', PayoutController.as_view(), name='payout-list'),
    path('payouts/<int:payout_id>/', PayoutController.as_view(), name='payout-detail'),
    path('payouts/<int:payout_id>/process/', PayoutProcessController.as_view(), name='payout-process'),
    path('payouts/<int:payout_id>/cancel/', PayoutCancelController.as_view(), name='payout-cancel'),
    path('payouts/process-all/', PayoutBulkProcessController.as_view(), name='payout-process-all'),
    path('payouts/stats/', PayoutStatsController.as_view(), name='payout-stats'),
] 