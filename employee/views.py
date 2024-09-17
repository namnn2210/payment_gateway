from django.shortcuts import render, redirect, get_object_or_404
from .models import EmployeeDeposit
from bank.models import BankAccount
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from worker.views import get_balance_by_bank
from employee.models import EmployeeWorkingSession
from datetime import datetime
import pytz
import json
from django.utils import timezone

tz = pytz.timezone('Asia/Bangkok')

# Create your views here.
def employee_deposit(request):
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
        return redirect('index')
    if request.user.is_superuser:
        list_deposit_requests = EmployeeDeposit.objects.all()
    else:
        list_deposit_requests = EmployeeDeposit.objects.filter(user=request.user)
    list_deposit_requests = list_deposit_requests.order_by('-created_at')
        
    paginator = Paginator(list_deposit_requests, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    list_deposit_requests = paginator.get_page(page_number)
        
    return render(request=request, template_name='employee/deposit.html', context={'list_deposit_requests':list_deposit_requests})


@csrf_exempt
@require_POST
def update_deposit(request):
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
@require_POST
def delete_deposit(request):
    try:
        data = json.loads(request.body)
        deposit_id = data.get('id')
        deposit = EmployeeDeposit.objects.filter(id=deposit_id).first()
        
        deposit.delete()
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
def calculate_total_balance(bank_accounts):
    total_balance = 0
    for bank_account in bank_accounts:
        total_balance += get_balance_by_bank(bank=bank_account)
    return total_balance

@csrf_exempt
@require_POST
def employee_session(request, session_type):
    # try:
    print(session_type)
    undone_session = EmployeeWorkingSession.objects.filter(user=request.user, status=False).first()
    bank_accounts = BankAccount.objects.filter(user=request.user)
    if session_type == 'start':
        if undone_session:
            return JsonResponse({'status': 502, 'message': 'Đang trong phiên làm việc. Không thể bắt đầu','success': False})
        start_balance = calculate_total_balance(bank_accounts)
            
        EmployeeWorkingSession.objects.create(
            user=request.user,
            start_time=timezone.now(),
            start_balance = start_balance
        )
    elif session_type == 'end':
        print('end', undone_session)
        if undone_session:
            end_balance = calculate_total_balance(bank_accounts)
        
            undone_session.end_time = timezone.now()
            undone_session.end_balance = end_balance
            undone_session.status = True
            undone_session.save()
    else:
        return JsonResponse({'status': 504, 'message': 'Trạng thái không hợp lệ','success': False})
    return JsonResponse({'status': 200, 'message': 'Done','success': True})
    # except Exception as ex:
    #     print(ex)
    #     return JsonResponse({'status': 500, 'message': str(ex),'success': False})