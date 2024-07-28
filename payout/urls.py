from django.urls import path
from .views import list_payout, AddPayoutView, update_payout, webhook, user_payout_statistics

urlpatterns = [
    path('list', list_payout, name='list_payout'),
    path('add', AddPayoutView.as_view(), name='add_payout'),
    path('update_payout/<str:update_type>', update_payout, name='update_payout'),
    path('webhook', webhook, name='payout_webhook'),
    path('user_payout_statistics', user_payout_statistics, name='user_payout_statistics')
]