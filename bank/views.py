from django.shortcuts import render, redirect
from .models import Bank, BankAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
import json
import requests

# Create your views here.
@login_required(login_url='login')
def list_bank(request):
    list_bank_option = Bank.objects.filter(status=True)
    list_user_bank = BankAccount.objects.filter(user=request.user)
    return render(request=request, template_name='bank.html',context={'list_bank_option':list_bank_option, 'list_user_bank':list_user_bank})

def bank_transaction_history(request, account_number):
    bank_account = BankAccount.objects.filter(account_number=account_number).first()
    histories = get_acb_bank_transaction_history(bank_account)
    # Paginate the data
    paginator = Paginator(histories, 10)  # Show 10 items per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request=request, template_name='bank_transaction_history.html',context={'page_obj':page_obj})

@method_decorator(csrf_exempt, name='dispatch')
class AddBankView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        bank_number = data.get('bankNumber')
        bank_username = data.get('bankUsername')
        bank_password = data.get('bankPassword')
        bank_name = data.get('bankName')

        # Process the data and save to the database
        # (e.g., create a new Bank object and save it)
        bank_account = get_bank(bank_name,bank_number, bank_username, bank_password)
        if bank_account:
            bank = Bank.objects.filter(name=bank_name).first()
            bank_account = BankAccount.objects.create(
                user=request.user,
                bank_name=bank,
                account_number=bank_account.get('accountNumber'),
                account_name=bank_account.get('owner'),
                balance=bank_account.get('balance'),
                username=bank_username,
                password=bank_password
            )
            bank_account.save()
            return JsonResponse({'status': 200, 'message': 'Bank added successfully'})
        
        return JsonResponse({'status': '500', 'message': 'Failed to add bank'})


def get_bank(bank_name,bank_number, bank_username, bank_password):
    if bank_name == 'ACB':
        return get_acb_bank(bank_number, bank_username, bank_password)

def get_acb_bank(bank_number, bank_username, bank_password):
    url = "https://api.httzip.com/api/bank/ACB/balance"
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "login_id": bank_username,
        "login_password": bank_password
    })

    response = requests.post(url=url, headers=headers, data=payload)
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        for bank_account in list_bank_account:
            if bank_account['accountNumber'] == bank_number:
                return bank_account
    return None

def get_acb_bank_transaction_history(bank_account):
    url = 'https://api.httzip.com/api/bank/ACB/transactions'
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "login_id": bank_account.username,
        "login_password": bank_account.password,
        "filter_account":bank_account.account_number
    })
    
    response = requests.post(url=url, headers=headers, data=payload)
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        return list_bank_account
    return None