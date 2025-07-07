from django.urls import path
from .views import (
    PayoutListView,
    AddPayoutAPIView,
    UpdatePayoutAPIView,
    DeletePayoutAPIView,
    EditPayoutAPIView,
    MovePayoutAPIView,
    CheckSuccessPayoutAPIView,
    PayoutWebhookAPIView,
    TelegramWebhookAPIView,
)

app_name = 'payout'

urlpatterns = [
    path('list/', PayoutListView.as_view(), name='list_payout'),
    path('api/add/', AddPayoutAPIView.as_view(), name='add_payout_api'),
    path('api/update/<str:update_type>/', UpdatePayoutAPIView.as_view(), name='update_payout_api'),
    path('api/delete/', DeletePayoutAPIView.as_view(), name='delete_payout_api'),
    path('api/edit/', EditPayoutAPIView.as_view(), name='edit_payout_api'),
    path('api/move/', MovePayoutAPIView.as_view(), name='move_payout_api'),
    path('api/check_success/', CheckSuccessPayoutAPIView.as_view(), name='check_success_payout_api'),
    path('webhook/', PayoutWebhookAPIView.as_view(), name='payout_webhook'),
    path('tele_webhook/', TelegramWebhookAPIView.as_view(), name='tele_webhook'),
]