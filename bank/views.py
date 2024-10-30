from OpenSSL.rand import status
from django.shortcuts import render, redirect
from settle_payout.models import SettlePayout
from .models import Bank, BankAccount
from payout.models import UserTimeline, Payout
from employee.models import EmployeeDeposit
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.forms.models import model_to_dict
from .utils import get_start_end_datetime_by_timeline
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from .database import redis_connect
from datetime import datetime
import json
import pandas as pd
import requests
import os
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from dotenv import load_dotenv
from django.utils import timezone
import openpyxl
from django.http import HttpResponse
from io import BytesIO

load_dotenv()

# Create your views here.
@login_required(login_url='user_login')
def list_bank(request):
    list_bank_option = Bank.objects.filter(status=True)
    if request.user.is_superuser:
        list_user_bank = BankAccount.objects.all()
    else:
        list_user_bank = BankAccount.objects.filter(user=request.user)
    return render(request=request, template_name='bank.html',context={'list_bank_option':list_bank_option, 'list_user_bank':list_user_bank})

@login_required(login_url='user_login')
def record_book(request):
    
    all_transactions_df = get_all_transactions()
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_datetime', '')
    end_date = request.GET.get('end_datetime', '')
    status = request.GET.get('status', '')

    print("record book status", status)

    start_date, end_date = get_start_end_datetime(start_date, end_date)

    # Convert the 'transaction_date' column to datetime format if it exists
    if 'transaction_date' in all_transactions_df.columns:
        all_transactions_df['transaction_date'] = pd.to_datetime(all_transactions_df['transaction_date'], format='%d/%m/%Y %H:%M:%S')

    # Get form inputs

    # Filter transactions based on form input
    filtered_transactions_df = all_transactions_df[
        (all_transactions_df['transaction_date'] >= start_date) &
        (all_transactions_df['transaction_date'] <= end_date)
    ]

    if status == 'Success':
        filtered_transactions_df = filtered_transactions_df[filtered_transactions_df['status'] == 'Success']
    if status == 'Failed':
        filtered_transactions_df = filtered_transactions_df[filtered_transactions_df['status'] == 'Failed' or filtered_transactions_df['status'] == '']

    if search_query:
        filtered_transactions_df = filtered_transactions_df[
            filtered_transactions_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)
        ]

    # Separate and sort transactions by type
    in_transactions_df = filtered_transactions_df[filtered_transactions_df['transaction_type'] == 'IN'].sort_values(by='transaction_date', ascending=False).fillna('')
    out_transactions_df = filtered_transactions_df[filtered_transactions_df['transaction_type'] == 'OUT'].sort_values(by='transaction_date', ascending=False).fillna('')

    # Calculate total amounts
    total_in_amount = in_transactions_df['amount'].sum()
    total_out_amount = out_transactions_df['amount'].sum()


    # Pagination for "IN" transactions
    in_paginator = Paginator(in_transactions_df.to_dict(orient='records'), 6)
    in_page_number = request.GET.get('in_page')
    in_page_obj = in_paginator.get_page(in_page_number)

    # Pagination for "OUT" transactions
    out_paginator = Paginator(out_transactions_df.to_dict(orient='records'), 6)
    out_page_number = request.GET.get('out_page')
    out_page_obj = out_paginator.get_page(out_page_number)

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        # Return JSON response for AJAX requests

        total_in_amount = int(float(in_transactions_df['amount'].sum()))
        total_out_amount = int(float(out_transactions_df['amount'].sum()))



        data = {
            'in_transactions': list(in_page_obj),
            'out_transactions': list(out_page_obj),
            'in_page': in_page_obj.number,
            'in_num_pages': in_page_obj.paginator.num_pages,
            'out_page': out_page_obj.number,
            'out_num_pages': out_page_obj.paginator.num_pages,
            'total_in_amount': total_in_amount,
            'total_out_amount': total_out_amount,
        }

        print("=========", data)

        return JsonResponse(data)


    return render(request, 'record_book.html', {
        'in_page_obj': in_page_obj,
        'out_page_obj': out_page_obj,
        'search_query': search_query,
        'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
        'end_date': end_date.strftime('%Y-%m-%dT%H:%M'),
        'total_in_amount': total_in_amount,
        'total_out_amount': total_out_amount,
    })

@method_decorator(csrf_exempt, name='dispatch')
class AddBankView(View):
    def post(self, request, *args, **kwargs):
        # try:
        data = json.loads(request.body)
        bank_number = data.get('bankNumber')
        bank_accountname = data.get('bankAccountName')
        bank_username = data.get('bankUsername')
        bank_password = data.get('bankPassword')
        bank_type = data.get('bankType')
        bank_name = data.get('bankName')

        # Check if any bank_account with the same type is ON
        existed_bank_account = BankAccount.objects.filter(
            user=request.user,
            account_number=bank_number,
            bank_type=bank_type).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Existed bank. Please try again'})


        bank = Bank.objects.filter(name=bank_name).first()

        BankAccount.objects.create(
            user=request.user,
            bank_name=bank,
            account_number=bank_number,
            account_name=bank_accountname,
            balance=0,
            bank_type=bank_type,
            username=bank_username,
            password=bank_password
        )


        return JsonResponse({'status': 200, 'message': 'Bank added successfully'})
        # except Exception as ex:
        #     print(str(ex))
        #     return JsonResponse({'status': 500, 'message': 'Failed to add bank'})
    
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
            # if bank_account.bank_name.name == 'MB':
            #     if data['status'] == 'ON':
            #         login_logout_mb(bank_account.username, bank_account.password, bank_account.account_number, 'ON')
            #     else:
            #         login_logout_mb(bank_account.username, bank_account.password, bank_account.account_number, 'OFF')
            return JsonResponse({'status': 200, 'message': 'Status updated successfully'})
        except BankAccount.DoesNotExist:
            return JsonResponse({'status': 404, 'message': 'Bank account not found'})
    return JsonResponse({'status': 400, 'message': 'Invalid request'})

def login_logout_mb(username, password, account_number, toggle_status):

    if toggle_status == 'ON':
        payload = json.dumps({
            "username": username,
            "password": password,
            "accountNo": account_number,
            "webhook": "https://gateway.226pay.com/en/bank/mb_webhook"
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(f'{os.environ.get('MB_WEBHOOK')}doLogin', headers=headers,
                                 data=payload).json()

        if response['type'] != 'success':
            return JsonResponse({'status': 500, 'message': 'Failed to login MB Bank'})
    else:
        payload = json.dumps({
            "username": username,
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(f'{os.environ.get('MB_WEBHOOK')}doDelete', headers=headers,
                                 data=payload).json()

        if response['type'] != 'success':
            return JsonResponse({'status': 500, 'message': 'Failed to delete MB Bank'})
    return JsonResponse({'status': 200, 'message': 'Success'})


def update_transaction_history(request):
    # all_transactions = get_all_transactions(request)
    redis_client = redis_connect(1)
    if request.user.is_superuser:
        bank_accounts = BankAccount.objects.filter(status=True)
    else:
        bank_accounts = BankAccount.objects.filter(user=request.user, status=True)
    
    list_df_in = []
    list_df_out = []

    for bank_account in bank_accounts:
        bank_redis = redis_client.get(bank_account.account_number)
        if bank_redis:
            json_data = json.loads(bank_redis)
            df = pd.DataFrame(json_data)
            if request.user.is_superuser:
                if bank_account.bank_type == 'IN':
                    if not df.empty:
                        in_transaction_df = df[df['transaction_type'] == 'IN']
                        if not in_transaction_df.empty:
                            list_df_in.append(in_transaction_df)
                else:
                    if not df.empty:
                        out_transaction_df = df[df['transaction_type'] == 'OUT']
                        if not out_transaction_df.empty:
                            list_df_out.append(out_transaction_df)
            else:
                if not df.empty:
                    in_transaction_df = df[df['transaction_type'] == 'IN']
                    out_transaction_df = df[df['transaction_type'] == 'OUT']
                    if not in_transaction_df.empty:
                        list_df_in.append(in_transaction_df)
                        list_df_out.append(out_transaction_df)

    if len(list_df_in) > 0:
        df_in = pd.concat(list_df_in)
        df_in = df_in.sort_values(by=['transaction_number', 'status', df_in.index], ascending=[True, False, True])
        df_in = df_in.drop_duplicates(subset=['transaction_number'], keep='last')
        df_in['transaction_date'] = pd.to_datetime(df_in['transaction_date'], format='%d/%m/%Y %H:%M:%S')
        sorted_transactions_in = df_in.sort_values(by='transaction_date', ascending=False).head(5)
        sorted_transactions_in['transaction_date'] = sorted_transactions_in['transaction_date'].dt.strftime('%d/%m/%Y %H:%M:%S')
        top_transactions_json_in = sorted_transactions_in.to_json(orient='records', date_format='iso')
        top_transactions_json_in = json.loads(top_transactions_json_in)
    else:
        top_transactions_json_in = {}

    if len(list_df_out) > 0:
        df_out = pd.concat(list_df_out)
        df_out = df_out.sort_values(by=['transaction_number', 'status', df_out.index], ascending=[True, False, True])
        df_out = df_out.drop_duplicates(subset=['transaction_number'], keep='last')
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
    if request.user.is_superuser:
        bank_accounts = BankAccount.objects.all()
    else:
        bank_accounts = BankAccount.objects.filter(user=request.user)
    
    list_dict_accounts = []
    for bank_account in bank_accounts:
        list_dict_accounts.append(model_to_dict(bank_account))
    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'balance':list_dict_accounts}})

def update_amount_by_date(transaction_type, amount):
    redis_client = redis_connect(3)
    today_str = timezone.now().strftime('%Y-%m-%d')
    
    # Initialize today's key if it doesn't exist
    if not redis_client.exists(today_str):
        initial_value = json.dumps({'in': 0, 'out': 0})
        redis_client.set(today_str, initial_value)
        
    # Retrieve current totals
    current_totals = json.loads(redis_client.get(today_str))
    
    # Update totals based on payout status
    if transaction_type == 'OUT':  # Assuming status False indicates an "out" payout
        current_totals['out'] += amount
    else:  # Assuming any other status indicates an "in" payout
        current_totals['in'] += amount

    # Save updated totals back to Redis
    redis_client.set(today_str, json.dumps(current_totals))

def check_success_payout(transaction):
    latest_payout = Payout.objects.order_by('-created_at')[:10]
    latest_settle = SettlePayout.objects.order_by('-created_at')[:10]

    for payout in latest_payout:
        if payout.money == transaction['amount']:
            # memo = 'Z'+payout.accountname
            # if memo in transaction['transfer_code']:
            return True

    for settle in latest_settle:
        if settle.money == transaction['amount']:
            # memo = 'Z'+settle.accountname
            # if memo in transaction['transfer_code']:
            return True

    return False
    
def get_amount_today(request):
    if request.user.is_superuser:
        redis_client = redis_connect(3)
        today_str = timezone.now().strftime('%Y-%m-%d')
        if redis_client.exists(today_str):
            current_totals = json.loads(redis_client.get(today_str))
            return JsonResponse({'status': 200, 'message': 'Done', 'data': current_totals})
        else:
            return JsonResponse({'status': 500, 'message': 'Invalid request'})
    else:
        try:
            user_timeline = UserTimeline.objects.filter(user=request.user).first()
            start_at = user_timeline.timeline.start_at
            end_at = user_timeline.timeline.end_at
            start_datetime, end_datetime = get_start_end_datetime_by_timeline(start_at,end_at)
            time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)
            payouts = Payout.objects.filter(user=request.user, status=True).filter(time_range_query)
            total_out = payouts.aggregate(total_money=Sum('money'))['total_money'] or 0
            deposit = EmployeeDeposit.objects.filter(user=request.user, status=True).filter(time_range_query)
            total_in = deposit.aggregate(total_money=Sum('amount'))['total_money'] or 0
            return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in':total_in,'out':total_out}})
        except Exception as ex:
            return JsonResponse({'status': 500, 'message': 'Invalid request'})
        
    

def update_transaction_history_status(account_number, transfer_code, orderid, scode, incomingorderid, status):
    redis_client = redis_connect(1)
    transactions = json.loads(redis_client.get(account_number))
    for transaction in transactions:
        if transaction['transfer_code'] == transfer_code:
            print(transaction)
            transaction['orderid'] = orderid
            transaction['scode'] = scode
            transaction['incomingorderid'] = incomingorderid
            transaction['status'] = status
            break

    redis_client.set(account_number, json.dumps(transactions))

def update_out_transaction_history_status(transaction_number, account_number):
    redis_client = redis_connect(1)
    transactions = json.loads(redis_client.get(account_number))
    for transaction in transactions:
        print(transaction)
        if transaction['transaction_number'] == transaction_number:
            transaction['status'] = 'Success'
            break

    redis_client.set(account_number, json.dumps(transactions))
    
def get_all_transactions():
    redis_client = redis_connect(1)
    
    list_banks = redis_client.scan_iter('*')

    all_transactions = []
    for bank in list_banks:
        transactions_str = redis_client.get(bank)
        if transactions_str:
            all_transactions += json.loads(transactions_str)
    all_transactions_df = pd.DataFrame(all_transactions)
    
    return all_transactions_df

def get_transactions_by_key(account_number):
    redis_client = redis_connect(1)
    transactions_str = redis_client.get(account_number)
    all_transactions = []
    if transactions_str:
        all_transactions += json.loads(transactions_str)
    transactions_df = pd.DataFrame(all_transactions)
    return transactions_df


def get_start_end_datetime(start_datetime, end_datetime):
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)

    if start_datetime:
        start_datetime = parse_datetime(start_datetime)
    else:
        start_datetime = today_start

    if end_datetime:
        end_datetime = parse_datetime(end_datetime)
    else:
        end_datetime = today_end

    return start_datetime, end_datetime

def get_start_end_datetime_string(start_datetime, end_datetime):
    today = timezone.now().date().strftime('%d/%m/%Y')

    if start_datetime:
        start_datetime = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M')
    else:
        start_datetime = datetime.strptime(f'{today} 00:00', '%d/%m/%Y %H:%M')

    if end_datetime:
        end_datetime = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M')
    else:
        end_datetime = datetime.strptime(f'{today} 23:59', '%d/%m/%Y %H:%M')
        
    return start_datetime, end_datetime



@csrf_exempt
@require_POST    
def record_book_report(request):
    if request.method == 'POST':
        account_number = request.POST.get('account_no')
        transaction_df = get_transactions_by_key(account_number)

        if not transaction_df.empty:
            # Convert the 'transaction_date' column to datetime format if it exists
            if 'transaction_date' in transaction_df.columns:
                transaction_df['transaction_date'] = pd.to_datetime(transaction_df['transaction_date'], format='%d/%m/%Y %H:%M:%S')
            transaction_df = transaction_df.sort_values(by='transaction_date', ascending=False)
            data = {
                'transactions': transaction_df.to_dict(orient='records'),
            }

            return JsonResponse(data)

    return JsonResponse({'error': 'Invalid request method'})

def export_to_excel(request):
    # Fetch all transactions as a DataFrame
    all_transactions_df = get_all_transactions()

    # Get search query and date range from the request
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_datetime', '')
    end_date = request.GET.get('end_datetime', '')

    # Convert start_date and end_date to actual datetime objects (utility function)
    start_date, end_date = get_start_end_datetime(start_date, end_date)

    # Ensure we have transactions to filter
    if not all_transactions_df.empty:

        # Convert the 'transaction_date' column to datetime format for filtering
        if 'transaction_date' in all_transactions_df.columns:
            all_transactions_df['transaction_date'] = pd.to_datetime(
                all_transactions_df['transaction_date'], format='%d/%m/%Y %H:%M:%S'
            )

        # Filter transactions based on the date range (if start_date and end_date are valid)
        filtered_transactions_df = all_transactions_df[
            (all_transactions_df['transaction_date'] >= start_date) &
            (all_transactions_df['transaction_date'] <= end_date)
        ]

        # Apply the search query filter if provided
        if search_query:
            filtered_transactions_df = filtered_transactions_df[
                filtered_transactions_df.apply(
                    lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1
                )
            ]

        # Prepare the Excel file for download
        if not filtered_transactions_df.empty:
            # Create an in-memory buffer
            buffer = BytesIO()

            # Use Pandas to write the filtered DataFrame to an Excel file in memory
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_transactions_df.to_excel(writer, sheet_name='Transactions', index=False)

            # Set the buffer's file position to the beginning
            buffer.seek(0)

            # Create an HTTP response with the Excel file
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=filtered_transactions.xlsx'

            return response
        else:
            # Return an empty Excel file or an error response
            return HttpResponse('No transactions found for the specified filters.', content_type='text/plain')

    else:
        # Handle the case where there are no transactions to export
        return HttpResponse('No transactions available to export.', content_type='text/plain')


            


    
    