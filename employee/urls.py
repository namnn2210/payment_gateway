from django.urls import path
from .views import employee_deposit, update_deposit,delete_deposit, employee_session,list_employee_session

urlpatterns = [
    path('employee_deposit', employee_deposit, name='employee_deposit'),
    path('update_deposit',update_deposit, name='update_deposit'),
    path('delete_deposit',delete_deposit, name='delete_deposit'),
    path('employee_session/<str:session_type>', employee_session, name='employee_session'),
    path('list_employee_session',list_employee_session,name='list_employee_session')
]