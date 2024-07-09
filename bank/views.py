from django.shortcuts import render, redirect
from .models import Bank, BankAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from .utils import unix_to_datetime, send_telegram_message
from .database import redis_connect
from datetime import datetime, timedelta
import json
import pandas as pd
import os
from django.core.paginator import Paginator
from dotenv import load_dotenv

load_dotenv()

# Create your views here.
@login_required(login_url='user_login')
def list_bank(request):
    list_bank_option = Bank.objects.filter(status=True)
    list_user_bank = BankAccount.objects.all()
    return render(request=request, template_name='bank.html',context={'list_bank_option':list_bank_option, 'list_user_bank':list_user_bank})

@login_required(login_url='user_login')
def record_book(request):
    redis_client = redis_connect()
    
    list_banks = BankAccount.objects.all()
    all_transactions = []
    for bank in list_banks:
        transactions_str = redis_client.get(bank.account_number)
        all_transactions += json.loads(transactions_str)
    all_transactions_df = pd.DataFrame(all_transactions)
    # Convert the 'transaction_date' column to datetime format if it exists
    if 'transaction_date' in all_transactions_df.columns:
        all_transactions_df['transaction_date'] = pd.to_datetime(all_transactions_df['transaction_date'], format='%d/%m/%Y %H:%M:%S')

    # Sort the dataframe by 'transaction_date' in descending order if the column exists
    if 'transaction_date' in all_transactions_df.columns:
        sorted_transactions_new = all_transactions_df.sort_values(by='transaction_date', ascending=False)
    else:
        sorted_transactions_new = all_transactions_df  # If no 'transaction_date', do not sort
    
    page_obj = sorted_transactions_new.to_dict(orient='records')
    
    return render(request=request, template_name='record_book.html', context={'page_obj': page_obj})

@method_decorator(csrf_exempt, name='dispatch')
class AddBankView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        bank_number = data.get('bankNumber')
        bank_username = data.get('bankUsername')
        bank_password = data.get('bankPassword')
        bank_type = data.get('bankType')
        bank_name = data.get('bankName')
        
        # Check if any bank_account with the same type is ON
        existed_bank_account = BankAccount.objects.filter(
            user=request.user,
            account_number=bank_number,
            username=bank_username,
            password=bank_password).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Existed bank. Please try again'})

        # Process the data and save to the database
        # (e.g., create a new Bank object and save it)
        # bank_account = get_bank(bank_name,bank_number, bank_username, bank_password)
        # if bank_account:
        #     bank = Bank.objects.filter(name=bank_name).first()
        #     bank_account = BankAccount.objects.create(
        #         user=request.user,
        #         bank_name=bank,
        #         account_number=bank_account.get('accountNumber'),
        #         account_name=bank_account.get('owner'),
        #         balance=bank_account.get('balance'),
        #         bank_type=bank_type,
        #         username=bank_username,
        #         password=bank_password
        #     )
        #     bank_account.save()
            return JsonResponse({'status': 200, 'message': 'Bank added successfully'})
        
        return JsonResponse({'status': 500, 'message': 'Failed to add bank'})
    
@csrf_exempt
def toggle_bank_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            bank_account = BankAccount.objects.get(id=data['id'])
            new_status = False
            if data['status'] == 'ON':
                new_status = True
            bank_account.status = new_status
            bank_account.save()
            return JsonResponse({'status': 200, 'message': 'Status updated successfully'})
        except BankAccount.DoesNotExist:
            return JsonResponse({'status': 404, 'message': 'Bank account not found'})
    return JsonResponse({'status': 400, 'message': 'Invalid request'})




def update_transaction_history(request):
    # all_transactions = get_all_transactions(request)
    redis_client = redis_connect()
    bank_accounts = BankAccount.objects.filter(status=True)
    
    list_df_in = []
    list_df_out = []

    for bank_account in bank_accounts:
        bank_redis = redis_client.get(bank_account.account_number)
        if bank_redis:
            json_data = json.loads(bank_redis)
            df = pd.DataFrame(json_data)
            if bank_account.bank_type == 'IN':
                in_transaction_df = df[df['transaction_type'] == 'IN']
                if not in_transaction_df.empty:
                    list_df_in.append(in_transaction_df)
            else:
                out_transaction_df = df[df['transaction_type'] == 'OUT']
                if not out_transaction_df.empty:
                    list_df_out.append(out_transaction_df)

    if len(list_df_in) > 0:
        df_in = pd.concat(list_df_in)
        df_in['transaction_date'] = pd.to_datetime(df_in['transaction_date'], format='%d/%m/%Y %H:%M:%S')
        sorted_transactions_in = df_in.sort_values(by='transaction_date', ascending=False).head(5)
        sorted_transactions_in['transaction_date'] = sorted_transactions_in['transaction_date'].dt.strftime('%d/%m/%Y %H:%M:%S')
        top_transactions_json_in = sorted_transactions_in.to_json(orient='records', date_format='iso')
        top_transactions_json_in = json.loads(top_transactions_json_in)
    else:
        top_transactions_json_in = {}

    if len(list_df_out) > 0:
        df_out = pd.concat(list_df_out)
        df_out['transaction_date'] = pd.to_datetime(df_out['transaction_date'], format='%d/%m/%Y %H:%M:%S')
        sorted_transactions_out = df_out.sort_values(by='transaction_date', ascending=False).head(5)
        sorted_transactions_out['transaction_date'] = sorted_transactions_out['transaction_date'].dt.strftime('%d/%m/%Y %H:%M:%S')
        top_transactions_json_out = sorted_transactions_out.to_json(orient='records', date_format='iso')
        top_transactions_json_out = json.loads(top_transactions_json_out)
    else:
        top_transactions_json_out = {}
    
    # Close the Redis connection
    redis_client.close()

    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in':top_transactions_json_in, 'out':top_transactions_json_out}})

def update_balance(request):
    bank_accounts = BankAccount.objects.filter(status=True)
    list_dict_accounts = []
    for bank_account in bank_accounts:
        list_dict_accounts.append(model_to_dict(bank_account))
    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'balance':list_dict_accounts}})