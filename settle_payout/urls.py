from django.urls import path
from .views import (
    SettlePayoutListView,
    AddSettlePayoutAPIView,
    UpdateSettlePayoutAPIView,
    DeleteSettlePayoutAPIView,
    EditSettlePayoutAPIView,
    CheckSuccessSettleAPIView,
)

app_name = 'settle_payout'

urlpatterns = [
    path('list/', SettlePayoutListView.as_view(), name='list_settle_payout'),
    path('api/add/', AddSettlePayoutAPIView.as_view(), name='add_settle_payout_api'),
    path('api/update/<str:update_type>/', UpdateSettlePayoutAPIView.as_view(), name='update_settle_payout_api'),
    path('api/delete/', DeleteSettlePayoutAPIView.as_view(), name='delete_settle_payout_api'),
    path('api/edit/', EditSettlePayoutAPIView.as_view(), name='edit_settle_payout_api'),
    path('api/check_success/', CheckSuccessSettleAPIView.as_view(), name='check_success_settle_api'),
]
