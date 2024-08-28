from django.urls import path
from .views import list_payout, add_payout, update_payout, webhook, user_payout_statistics, delete_payout, move_payout, list_users

urlpatterns = [
    path('list', list_payout, name='list_payout'),
    path('add', add_payout, name='add_payout'),
    path('update_payout/<str:update_type>', update_payout, name='update_payout'),
    path('delete_payout', delete_payout, name='delete_payout'),
    path('move_payout', move_payout, name='move_payout'),
    path('webhook', webhook, name='payout_webhook'),
    path('user_payout_statistics', user_payout_statistics, name='user_payout_statistics'),
    path('list_users', list_users, name='list_users')
]