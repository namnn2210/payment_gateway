from django.urls import path
from .views import list_payout, AddPayoutView, update_payout, webhook, delete_payout, move_payout, edit_payout, \
    check_success_payout, tele_webhook

urlpatterns = [
    path('list', list_payout, name='list_payout'),
    path('add', AddPayoutView.as_view(), name='add_payout'),
    path('update_payout/<str:update_type>', update_payout, name='update_payout'),
    path('delete_payout', delete_payout, name='delete_payout'),
    path('move_payout', move_payout, name='move_payout'),
    path('edit_payout', edit_payout, name='edit_payout'),
    path('check_success_payout', check_success_payout, name='check_success_payout'),
    path('webhook', webhook, name='payout_webhook'),
    path('tele_webhook', tele_webhook, name='tele_webhook'),
]
