from django.urls import path
from .views import list_payout, update_payout, search_payout

urlpatterns = [
    path('list', list_payout, name='list_payout'),
    path('update', update_payout, name='update_payout'),
    path('list/search', search_payout, name='search_payout')
]