from django.shortcuts import render, redirect, get_object_or_404
from .models import EmployeeDeposit
from bank.models import BankAccount
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json

# Create your views here.
def employee_deposit(request):
    if request.method == 'POST':
        deposit_amount = int(request.POST.get('deposit', 0))
        bank_id = int(request.POST.get('bank'))
        bank = BankAccount.objects.filter(id=bank_id).first()
        system_bank_data = json.load(open('bank.json', encoding='utf-8'))
        bank_code = ''
        for bank_data in system_bank_data:
            if bank.bank_name.name == bank_data['short_name']:
                bank_code = bank_data['code']
        EmployeeDeposit.objects.create(
            user = request.user,
            amount = deposit_amount,
            bankname = bank.bank_name,
            accountno = bank.account_number,
            accountname = bank.account_name,
            bankcode = bank_code
        )
        return redirect('index')
    if request.user.is_superuser:
        list_deposit_requests = EmployeeDeposit.objects.all()
    else:
        list_deposit_requests = EmployeeDeposit.objects.filter(user=request.user)
        
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