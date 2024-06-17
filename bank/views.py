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
from datetime import datetime, timedelta
import json
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

@login_required(login_url='login')
def record_book(request):
    list_user_bank = BankAccount.objects.filter(user=request.user)
    return render(request=request, template_name='record_book.html', context={'list_user_bank':list_user_bank})

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
        existed_bank_account = BankAccount.objects.filter(user=request.user, bank_type=bank_type, status=True).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Existed bank account with the same type. Please switch off the current bank account'})

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
                bank_type=bank_type,
                username=bank_username,
                password=bank_password
            )
            bank_account.save()
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

def filter_data(df, filter_type):
    filtered_df = df.copy()
    filtered_df = filtered_df.sort_values(by='active_datetime', ascending=False)
    now = datetime.now()
    filtered_df['active_datetime'] = pd.to_datetime(filtered_df['active_datetime'], format='%Y-%m-%d %H:%M:%S')
    if filter_type == "10_last_histories":
        filtered_df = filtered_df.head(10)
        # filtered_df = filtered_df.head(10)
    elif filter_type == "today":
        filtered_df = filtered_df[filtered_df['active_datetime'].dt.date == now.date()]
    elif filter_type == "yesterday":
        yesterday = now - timedelta(1)
        filtered_df = filtered_df[filtered_df['active_datetime'].dt.date == yesterday.date()]
    elif filter_type == "7_latest_days":
        last_week = now - timedelta(7)
        filtered_df = filtered_df[filtered_df['active_datetime'] >= last_week]
    elif filter_type == "this_week":
        start_of_week = now - timedelta(days=now.weekday())
        filtered_df = filtered_df[filtered_df['active_datetime'] >= start_of_week]
    elif filter_type == "last_week":
        start_of_last_week = (now - timedelta(days=now.weekday() + 7))
        end_of_last_week = start_of_last_week + timedelta(days=6)
        filtered_df = filtered_df[(filtered_df['active_datetime'] >= start_of_last_week) & (filtered_df['active_datetime'] <= end_of_last_week)]
    elif filter_type == "30_latest_days":
        last_month = now - timedelta(30)
        filtered_df = filtered_df[filtered_df['active_datetime'] >= last_month]
    elif filter_type == "all_time":
        pass  # No filtering needed for all time
    filtered_df['active_datetime'] = filtered_df['active_datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    filtered_df = filtered_df.fillna('')
    return filtered_df.to_dict(orient='records')

def get_transaction_history_with_filter(request):
    if request.method == 'POST':
        list_bank_account = BankAccount.objects.filter(user=request.user)
        all_transactions = []
        for bank_account in list_bank_account:
            histories = get_acb_bank_transaction_history(bank_account)
            columns_to_convert = ['posting_date', 'active_datetime', 'effective_date']
            df = pd.DataFrame(list(histories))
            df[columns_to_convert] = df[columns_to_convert].apply(unix_to_datetime, axis=1)
            df = df.fillna('')
            all_transactions.append(df)
        if all_transactions:
            all_transactions_df = pd.concat(all_transactions)
            all_transactions_df.to_csv('a.csv', index=False)
            data = json.loads(request.body)
            filter = data.get('filter')
            bank_account = data.get('account')
            print(bank_account, filter)
            if bank_account == 'ALL':
                filtered_data = filter_data(all_transactions_df, filter)
                return JsonResponse({'status': 200, 'message': 'Done', 'data': filtered_data})
            else:
                filtered_data = filter_data(all_transactions_df[all_transactions_df['account'] == int(bank_account)], filter)
                return JsonResponse({'status': 200, 'message': 'Done', 'data': filtered_data})
    return JsonResponse({'status': 500, 'message': 'Error'})


def update_transaction_history(request):
    # all_transactions = get_all_transactions(request)
    redis_client = redis_connect()
    bank_accounts = BankAccount.objects.filter(user=request.user)
    
    in_transaction_df = pd.DataFrame([])
    out_transaction_df = pd.DataFrame([])

    for bank_account in bank_accounts:
        bank_redis = redis_client.get(bank_account.account_number)
        print(bank_redis)
        if bank_redis:
            json_data = json.loads(bank_redis)
            df = pd.DataFrame(json_data)
            if bank_account.bank_type == 'IN':
                in_transaction_df = df[df['type'] == 'IN']
                if not in_transaction_df.empty:
                    sorted_transactions_in = in_transaction_df.sort_values(by='active_datetime', ascending=False).head(10)
                    top_transactions_json_in = sorted_transactions_in.to_json(orient='records', date_format='iso')
                else:
                     top_transactions_json_in = json.dumps([])  # Empty list if no transactions
            else:
                out_transaction_df = df[df['type'] == 'OUT']
                if not out_transaction_df.empty:
                    sorted_transactions_out = out_transaction_df.sort_values(by='active_datetime', ascending=False).head(10)
                    top_transactions_json_out = sorted_transactions_out.to_json(orient='records', date_format='iso')
                else:
                    top_transactions_json_out = json.dumps([])

        
    # Close the Redis connection
    redis_client.close()

    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in':json.loads(top_transactions_json_in), 'out':json.loads(top_transactions_json_out)}})

def update_balance(request):
    bank_accounts = BankAccount.objects.filter(user=request.user)
    in_balance = 0
    out_balance = 0
    for bank_account in bank_accounts:
        if bank_account.bank_type == 'IN':
            in_balance = int(bank_account.balance)
        else:
            out_balance = int(bank_account.balance)
    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in':in_balance, 'out':out_balance}})