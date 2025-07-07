from django.urls import path
from .views import (
    EmployeeDepositView,
    UpdateDepositAPIView,
    DeleteDepositAPIView,
    EmployeeSessionAPIView,
)

app_name = 'employee'

urlpatterns = [
    path('deposit/', EmployeeDepositView.as_view(), name='employee_deposit'),
    path('api/deposit/update/', UpdateDepositAPIView.as_view(), name='update_deposit_api'),
    path('api/deposit/delete/', DeleteDepositAPIView.as_view(), name='delete_deposit_api'),
    path('api/session/<str:session_type>/', EmployeeSessionAPIView.as_view(), name='employee_session_api'),
]
