from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BankViewSet, BankAccountViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'banks', BankViewSet)
router.register(r'accounts', BankAccountViewSet)

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
] 