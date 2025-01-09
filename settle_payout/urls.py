from django.urls import path
from .views import list_settle_payout, AddSettlePayoutView, update_settle_payout, delete_settle_payout, edit_settle_payout,check_success_settle

urlpatterns = [
    path('list', list_settle_payout, name='list_settle_payout'),
    path('add', AddSettlePayoutView.as_view(), name='add_settle_payout'),
    path('update_payout/<str:update_type>', update_settle_payout, name='update_settle_payout'),
    path('edit_settle_payout', edit_settle_payout, name='edit_settle_payout'),
    path('delete_settle_payout', delete_settle_payout, name='delete_settle_payout'),
    path('check_success_settle', check_success_settle, name='check_success_settle'),
]