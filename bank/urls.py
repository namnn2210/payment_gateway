from django.urls import path
from .views import list_bank, AddBankView

urlpatterns = [
    path('list', list_bank, name='list_bank'),
    path('add', AddBankView.as_view(), name='add_bank'),
]