from .models import EmployeeDeposit
from bank.models import BankAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .serializers import DepositSerializer, EmployeeSessionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from cms.views import jwt_auth_check
from rest_framework.response import Response
from rest_framework import status
from cms.models import APIResponse
from bank.models import BankAccount
from worker.views import get_balance_by_bank
from employee.models import EmployeeWorkingSession
from datetime import datetime
from django.contrib.auth.models import User
import json
import pytz

tz = pytz.timezone('Asia/Ho_Chi_Minh')

# Create your views here.
@csrf_exempt
@permission_classes([IsAuthenticated])
def employee_deposit(request):
    user = jwt_auth_check(request=request)

    if request.method == 'POST':
        deposit_amount = int(request.POST.get('deposit', 0))
        bank_id = int(request.POST.get('bank'))
        bank = BankAccount.objects.filter(id=bank_id).first()
        EmployeeDeposit.objects.create(
            user = request.user,
            amount = deposit_amount,
            bankname = bank.bank_name,
            accountno = bank.account_number,
            accountname = bank.account_name,
            bankcode = bank.bank_name.bankcode
        )
        return Response(APIResponse(success=True, message="").__dict__(), status=status.HTTP_201_CREATED)
    if user.is_superuser:
        list_deposit_requests = EmployeeDeposit.objects.all()
    else:
        list_deposit_requests = EmployeeDeposit.objects.filter(user=user)
    list_deposit_requests = list_deposit_requests.order_by('-created_at')
        
    deposit_serializer = DepositSerializer(list_deposit_requests, many=True).data

    return JsonResponse({'success': True, 'data': {'list_deposit': deposit_serializer}, 'message': ""}, status=200)



@csrf_exempt
@permission_classes([IsAuthenticated])
def update_deposit(request):
    _ = jwt_auth_check(request=request)
    try:
        data = json.loads(request.body)
        deposit_id = data.get('id')
        deposit = EmployeeDeposit.objects.filter(id=deposit_id).first()
        deposit.status = True
        deposit.save()
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
    
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_deposit(request):
    _ = jwt_auth_check(request=request)
    try:
        data = json.loads(request.body)
        deposit_id = data.get('id')
        deposit = EmployeeDeposit.objects.filter(id=deposit_id).first()
        
        deposit.delete()
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    

@csrf_exempt
@permission_classes([IsAuthenticated])
def employee_session(request, session_type):
    user = jwt_auth_check(request=request)
    try:
        undone_session = EmployeeWorkingSession.objects.filter(user=user, status=False).first()
        bank_accounts = BankAccount.objects.filter(user=user)
        if session_type == 'start':
            if undone_session:
                return JsonResponse({'status': 502, 'message': 'Đang trong phiên làm việc. Không thể bắt đầu','success': False})
            start_balance = 0
            for bank_account in bank_accounts:
                start_balance += get_balance_by_bank(bank=bank_account)
            EmployeeWorkingSession.objects.create(
                user=user,
                start_time=datetime.now(tz=tz),
                start_balance = start_balance
            )
        elif session_type == 'end':
            if undone_session:
                end_balance = 0
                for bank_account in bank_accounts:
                    end_balance += get_balance_by_bank(bank=bank_account)
                undone_session.end_time = datetime.now(tz=tz)
                undone_session.end_balance = end_balance
                undone_session.status = True
                undone_session.save()
        else:
            return JsonResponse({'status': 504, 'message': 'Trạng thái không hợp lệ','success': False})
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@permission_classes([IsAuthenticated])
def list_employee_session(request):
    user = jwt_auth_check(request=request)
    try:
        employee_sessions = EmployeeWorkingSession.objects.all()
        if user.is_superuser:
            status_filter = request.GET.get('status', 'Working')
            employee_filter = request.GET.get('employee')
            if status_filter == 'Working':
                status = False
            elif status_filter == 'Done':
                status = True
            
            if status is not None:
                employee_sessions = employee_sessions.filter(status=status)
            today = datetime.now().date().strftime('%d/%m/%Y')

            start_datetime_str = request.GET.get('start_datetime', '')
            end_datetime_str = request.GET.get('end_datetime', '')

            if start_datetime_str:
                start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M:%S')
            else:
                start_datetime = datetime.strptime(f'{today} 00:00', '%d/%m/%Y %H:%M')

            if end_datetime_str:
                end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M:%S')
            else:
                end_datetime = datetime.strptime(f'{today} 23:59', '%d/%m/%Y %H:%M')

            employee_sessions = employee_sessions.filter(start_time__gte=start_datetime, start_time__lte=end_datetime)

            if employee_filter != 'All':
                user_obj = User.objects.filter(username=employee_filter).first()
                employee_sessions = employee_sessions.filter(user=user_obj)
            employee_session_serializer = EmployeeSessionSerializer(employee_sessions, many=True).data
            return JsonResponse({'status': 200, 'message': 'Done','data': {'list_sessions':employee_session_serializer}})
        return JsonResponse({'status': 403, 'message': 'Permission denied','success': False})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})