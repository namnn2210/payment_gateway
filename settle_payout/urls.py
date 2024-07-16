from django.urls import path
from .views import list_settle_payout, AddSettlePayoutView, update_settle_payout

urlpatterns = [
    path('list', list_settle_payout, name='list_settle_payout'),
    path('add', AddSettlePayoutView.as_view(), name='add_settle_payout'),
    path('update_payout/<str:update_type>', update_settle_payout, name='update_settle_payout'),
]