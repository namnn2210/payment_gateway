from django.shortcuts import render, redirect
from .models import Bank, BankAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from .utils import get_acb_bank_transaction_history, get_bank, unix_to_datetime
from .database import redis_connect
import json
import redis
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Create your views here.
@login_required(login_url='login')
def list_bank(request):
    list_bank_option = Bank.objects.filter(status=True)
    list_user_bank = BankAccount.objects.filter(user=request.user)
    return render(request=request, template_name='bank.html',context={'list_bank_option':list_bank_option, 'list_user_bank':list_user_bank})

@login_required(login_url='login')
def bank_transaction_history(request, account_number):
    bank_account = BankAccount.objects.filter(account_number=account_number).first()
    histories = get_acb_bank_transaction_history(bank_account)
    columns_to_convert = ['posting_date', 'active_datetime', 'effective_date']
    df = pd.DataFrame(list(histories))
    df[columns_to_convert] = df[columns_to_convert].apply(unix_to_datetime, axis=1)
    df = df.fillna('')
    histories = df.to_dict(orient='records')
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
    

def update_transaction_history(request):
    redis_client = redis_connect()
    bank_accounts = BankAccount.objects.filter(user=request.user)
    
    all_transactions = []

    for bank_account in bank_accounts:
        bank_redis = redis_client.get(bank_account.account_number)
        if bank_redis:
            json_data = json.loads(bank_redis)
            df = pd.DataFrame(json_data)
            df = df[df['type'] == 'IN']
            all_transactions.append(df)

    # Close the Redis connection
    redis_client.close()

    # Concatenate all transaction DataFrames
    if all_transactions:
        all_transactions_df = pd.concat(all_transactions)

        # Convert the 'active_datetime' column to datetime if it's not already
        # if not pd.api.types.is_datetime64_any_dtype(all_transactions_df['active_datetime']):
        #     all_transactions_df['active_datetime'] = pd.to_datetime(all_transactions_df['active_datetime'])

        # Sort by 'active_datetime' in descending order and get the top 10
        sorted_transactions = all_transactions_df.sort_values(by='active_datetime', ascending=False).head(10)

        # Convert the sorted DataFrame to JSON
        top_transactions_json = sorted_transactions.to_json(orient='records', date_format='iso')
    else:
        top_transactions_json = json.dumps([])  # Empty list if no transactions

    return JsonResponse({'status': 200, 'message': 'Done', 'data': json.loads(top_transactions_json)})

