from django.urls import path
from .views import employee_deposit, update_deposit,delete_deposit

urlpatterns = [
    path('employee_deposit', employee_deposit, name='employee_deposit'),
    path('update_deposit',update_deposit, name='update_deposit'),
    path('delete_deposit',delete_deposit, name='delete_deposit'),
]