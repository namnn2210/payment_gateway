from django.shortcuts import render
from bank.database import redis_connect
from payout.models import Payout
from settle_payout.models import SettlePayout
from employee.models import EmployeeDeposit
from bank.views import get_all_transactions, get_start_end_datetime, get_transactions_by_key
from bank.models import BankAccount
from payout.models import Timeline, UserTimeline, BalanceTimeline
from django.db.models import Sum
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from datetime import datetime, time
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count, Min
from datetime import datetime, timedelta, time
from bank.views import get_transactions_by_key
from django.http import JsonResponse
from employee.models import EmployeeWorkingSession
from django.utils import timezone
import pandas as pd
import json
import pytz

# Create your views here.

timezone = pytz.timezone('Asia/Bangkok')


def report(request):
    start_datetime_str = request.GET.get('start_datetime', '')
    end_datetime_str = request.GET.get('end_datetime', '')
    total_payout_results = 0
    total_payout_amount = 0
    total_transaction_amount = 0
    total_transaction_results = 0

    # Get in out data for home
    redis_client = redis_connect(3)
    keys = redis_client.keys('*')
    data = {}
    for key in keys:
        data[key.decode('utf-8')] = redis_client.get(key).decode('utf-8')
    sorted_dates = sorted(data.keys())[-5:]
    last_5_days_data = {date: json.loads(data[date]) for date in sorted_dates}

    # Get transactions data for home

    all_transactions_df = get_all_transactions()
    start_date, end_date = get_start_end_datetime(start_datetime_str, end_datetime_str)
    filtered_transactions_df = pd.DataFrame()
    if not all_transactions_df.empty:

        # Convert the 'transaction_date' column to datetime format if it exists
        if 'transaction_date' in all_transactions_df.columns:
            all_transactions_df['transaction_date'] = pd.to_datetime(all_transactions_df['transaction_date'],
                                                                     format='%d/%m/%Y %H:%M:%S')

        # Get form inputs

        # Filter transactions based on form input
        filtered_transactions_df = all_transactions_df[
            (all_transactions_df['transaction_date'] >= start_date) &
            (all_transactions_df['transaction_date'] <= end_date)
            ]

        filtered_transactions_df = filtered_transactions_df[filtered_transactions_df['status'] == 'Success']

    if not filtered_transactions_df.empty:
        total_transaction_amount = int(float(filtered_transactions_df['amount'].sum()))
        total_transaction_results = filtered_transactions_df.shape[0]

    # User info      
    list_users = User.objects.filter(is_superuser=False)

    user_info_dict = {}
    for user in list_users:
        current_payout_info = {}
        online = False
        bank_accounts = []
        user_bank_accounts = BankAccount.objects.filter(user=user, status=True)

        user_working_session = EmployeeWorkingSession.objects.filter(user=user).order_by('-start_time').first()
        if user_working_session:
            user_start_time = user_working_session.start_time
            user_end_time = user_working_session.end_time

            if not user_end_time:
                online = True
                user_end_time = datetime.now(timezone)
                
            start_time = pd.to_datetime(user_start_time, format='%Y-%m-%d %H:%M:%S.%f').tz_localize(None)
            end_time = pd.to_datetime(user_end_time, format='%Y-%m-%d %H:%M:%S.%f').tz_localize(None)

            time_range_query = Q(created_at__gte=start_time) & Q(created_at__lt=end_time)
            payouts = Payout.objects.filter(user=user, status=True).filter(time_range_query)
            
            
            total_valid_transactions = 0
            
            for accounts in user_bank_accounts:
                transactions_df = get_transactions_by_key(account_number=accounts.account_number)

                # Convert 'transaction_date' to datetime64[ns] and ensure no timezone
                transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'], format="%d/%m/%Y %H:%M:%S").dt.tz_localize(None)

                # Filter the DataFrame between start_time and end_time
                filtered_df = transactions_df[
                    (transactions_df['transaction_date'] >= start_time) &
                    (transactions_df['transaction_date'] <= end_time) &
                    (transactions_df['transaction_type'] == 'OUT') &
                    (transactions_df['status'] == 'Success')
                ]
                
                total_valid_transactions += len(filtered_df)
                # total_amount += filtered_df['amount'].sum()

            current_payout_info['current_total_done_payout'] = len(payouts) or 0
            current_payout_info['current_total_valid_transaction'] = total_valid_transactions or 0

        # Bank accounts data
        for bank_account in user_bank_accounts:
            bank_accounts.append({
                "account_no": bank_account.account_number,
                "bank_name": bank_account.bank_name.name,
                "balance": bank_account.balance,
                "bank_type": bank_account.bank_type
            })

        user_info_dict[user.username] = {
            "bank_accounts": bank_accounts,
            "online": online,
            "payout": current_payout_info
        }

    report_data = {
        "chart": json.dumps(last_5_days_data),
        "payout": {
            "total_amount": total_payout_amount,
            "total_results": total_payout_results
        },
        "transactions": {
            "total_amount": total_transaction_amount,
            "total_results": total_transaction_results
        },
        "users": user_info_dict
    }

    return render(request=request, template_name='report.html', context={'report_data': report_data})


@csrf_exempt
@require_POST
def report_payout_by_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user = User.objects.filter(username=username).first()
        report_data = []
        working_sessions = EmployeeWorkingSession.objects.filter(user=user)

        for session in working_sessions:
            # Convert start_time_str and end_time_str to pd.Timestamp
            start_time_str = session.start_time
            end_time_str = session.end_time

            if not end_time_str:
                end_time_str = timezone.now()

            # Convert start_time_str and end_time_str to datetime64[ns] and remove timezone
            start_time = pd.to_datetime(start_time_str, format='%Y-%m-%d %H:%M:%S.%f').tz_localize(None)
            end_time = pd.to_datetime(end_time_str, format='%Y-%m-%d %H:%M:%S.%f').tz_localize(None)

            time_range_query = Q(created_at__gte=start_time) & Q(created_at__lt=end_time)

            # Payout
            payouts = Payout.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_payout = payouts.aggregate(total_money=Sum('money'))['total_money']
            total_count_payout = payouts.aggregate(payout_count=Count('id'))['payout_count']

            # Settle Payout
            settle = SettlePayout.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_settle = settle.aggregate(total_money=Sum('money'))['total_money']
            total_count_settle = settle.aggregate(payout_count=Count('id'))['payout_count']

            # Employee Deposit
            deposit = EmployeeDeposit.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_deposit = deposit.aggregate(total_money=Sum('amount'))['total_money']
            
            # Valid bank transaction
            bank_accounts = BankAccount.objects.filter(user=session.user)
            total_valid_transactions = 0
            total_amount = 0
            for accounts in bank_accounts:
                transactions_df = get_transactions_by_key(account_number=accounts.account_number)

                # Convert 'transaction_date' to datetime64[ns] and ensure no timezone
                transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'], format="%d/%m/%Y %H:%M:%S").dt.tz_localize(None)

                # Filter the DataFrame between start_time and end_time
                filtered_df = transactions_df[
                    (transactions_df['transaction_date'] >= start_time) &
                    (transactions_df['transaction_date'] <= end_time) &
                    (transactions_df['transaction_type'] == 'OUT') &
                    (transactions_df['status'] == 'Success')
                ]
                
                total_valid_transactions += len(filtered_df)
                total_amount += filtered_df['amount'].sum()
            
            if not total_amount_deposit:
                total_amount_deposit = 0
            if not total_amount_payout:
                total_amount_payout = 0
            if not total_amount_settle:
                total_amount_settle = 0
            
            calculate_total = session.start_balance + int(total_amount_deposit) - int(total_amount_payout) - int(total_amount_settle)
            
            report_data.append({
                'start_datetime': str(start_time),  # Already in datetime64[ns]
                'end_datetime': str(end_time),      # Already in datetime64[ns]
                'start_balance': session.start_balance or 0,
                'deposit': total_amount_deposit or 0,
                'total_amount_payout': float(total_amount_payout or 0),
                'total_count_payout': int(total_count_payout or 0),
                'total_amount_settle': float(total_amount_settle or 0),
                'total_count_settle': int(total_count_settle or 0),
                'total_count_valid_payout': int(total_valid_transactions or 0),
                'total_amount_valid_payout': float(total_amount or 0),
                'end_balance': session.end_balance or 0,
                'calculate_total':calculate_total or 0
            })

        return JsonResponse({'status': 200, 'message': 'Done', 'data': {'report_data': report_data}})

