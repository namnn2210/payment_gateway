from django.urls import path
from .views import list_payout, AddPayoutView, update_payout

urlpatterns = [
    path('list', list_payout, name='list_payout'),
    path('add', AddPayoutView.as_view(), name='add_payout'),
    path('update_payout/<str:update_type>', update_payout, name='update_payout'),
]