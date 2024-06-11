from django.shortcuts import render, redirect
from .models import Bank, BankAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from .utils import get_acb_bank_transaction_history, get_bank
import json

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


