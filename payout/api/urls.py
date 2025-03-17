from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PayoutViewSet, TimelineViewSet, 
    UserTimelineViewSet, BalanceTimelineViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'payouts', PayoutViewSet)
router.register(r'timelines', TimelineViewSet)
router.register(r'user-timelines', UserTimelineViewSet)
router.register(r'balance-timelines', BalanceTimelineViewSet)

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] 