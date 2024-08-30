from django.urls import path
from .views import list_settle_payout, add_settle, update_settle_payout, delete_settle_payout, edit_settle_payout

urlpatterns = [
    path('list', list_settle_payout, name='list_settle_payout'),
    path('add', add_settle, name='add_settle'),
    path('update_payout/<str:update_type>', update_settle_payout, name='update_settle_payout'),
    path('edit_settle_payout', edit_settle_payout, name='edit_settle_payout'),
    path('delete_settle_payout', delete_settle_payout, name='delete_settle_payout'),
]