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
from django.http import JsonResponse
import pandas as pd
import json
import pytz

# Create your views here.

timezone = pytz.timezone('UTC')


def report(request):
    start_datetime_str = request.GET.get('start_datetime', '')
    end_datetime_str = request.GET.get('end_datetime', '')
    total_payout_results = 0
    total_payout_amount = 0
    total_transaction_amount = 0
    total_transaction_results = 0

    # Get in-out data for home
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
    current_time = datetime.now().time()
    current_timeline_name = None

    # Checking current online users
    timelines = [
        {'name': 'Sáng', 'start_at': time(6, 0), 'end_at': time(14, 0)},
        {'name': 'Chiều', 'start_at': time(14, 0), 'end_at': time(22, 0)},
        {'name': 'Tối', 'start_at': time(22, 0), 'end_at': time(23, 59, 59)},
        {'name': 'Đêm', 'start_at': time(0, 0), 'end_at': time(6, 0)}
    ]

    for timeline in timelines:
        start_at = timeline['start_at']
        end_at = timeline['end_at']

        if start_at <= end_at:
            if start_at <= current_time <= end_at:
                current_timeline_name = timeline['name']
                break
        else:
            if current_time >= start_at or current_time <= end_at:
                current_timeline_name = timeline['name']
                break

    current_user_timelines = []
    if current_timeline_name:
        if current_timeline_name == 'Tối' or current_timeline_name == 'Đêm':
            current_timeline_name = 'Đêm'
        active_timeline = Timeline.objects.filter(status=True, name=current_timeline_name).first()

        current_user_timelines = list(UserTimeline.objects.filter(timeline=active_timeline, status=True))

    user_info_dict = {}
    for user in list_users:
        timeline_info = {}
        current_payout_info = {}
        bank_accounts = []
        user_bank_accounts = BankAccount.objects.filter(user=user, status=True)

        # Timeline
        for user_timeline in current_user_timelines:
            if user == user_timeline.user:
                online = True
                timeline_info = {
                    'name': user_timeline.timeline.name,
                    'start_at': user_timeline.timeline.start_at,
                    'end_at': user_timeline.timeline.end_at
                }
                break
            else:
                timeline_info = {}
                online = False

        user_timeline = UserTimeline.objects.filter(user=user, status=True).first()
        if user_timeline:
            user_start_time = user_timeline.timeline.start_at
            user_end_time = user_timeline.timeline.end_at

            if not timeline_info:
                timeline_info = {
                    'name': user_timeline.timeline.name,
                    'start_at': user_start_time,
                    'end_at': user_end_time
                }

            # Current payout data in timeline
            now = datetime.now()
            current_day = now.date()

            if user_start_time < user_end_time:
                start_datetime = datetime.combine(current_day, user_start_time)
                end_datetime = datetime.combine(current_day, user_end_time)
            else:  # Over midnight scenario
                start_datetime = datetime.combine(current_day - timedelta(days=1), user_start_time)
                end_datetime = datetime.combine(current_day, user_end_time)

            time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)
            payouts = Payout.objects.filter(user=user, status=True).filter(time_range_query)

            current_payout_info['current_total_amount_payout'] = payouts.aggregate(total_money=Sum('money'))[
                                                                     'total_money'] or 0
            current_payout_info['curent_total_count_payout'] = payouts.aggregate(payout_count=Count('id'))[
                                                                   'payout_count'] or 0

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
            "timeline": timeline_info,
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
        print(username)
        user = User.objects.filter(username=username).first()
        user_timeline = UserTimeline.objects.filter(user=user, status=True).first()

        start_time = user_timeline.timeline.start_at
        end_time = user_timeline.timeline.end_at

        print(start_time, end_time)

        # Get the oldest created_at date for Payout
        oldest_payout_date = Payout.objects.filter(user=user, status=True).aggregate(oldest_date=Min('created_at'))['oldest_date']

        if not oldest_payout_date:
            return JsonResponse([], safe=False)

        # Ensure the current time is without timezone
        now = datetime.now()
        current_day = now.date()

        results = []

        while True:
            if start_time < end_time:
                start_datetime = datetime.combine(current_day, start_time)
                end_datetime = datetime.combine(current_day, end_time)
            else:  # Over midnight scenario
                start_datetime = datetime.combine(current_day - timedelta(days=1), start_time)
                end_datetime = datetime.combine(current_day, end_time)

            if oldest_payout_date.tzinfo is not None:
                oldest_payout_date = oldest_payout_date.replace(tzinfo=None)
            # Break the loop if start_datetime is less than the oldest_date
            if start_datetime < oldest_payout_date:
                break

            time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)

            # Payout
            payouts = Payout.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_payout = payouts.aggregate(total_money=Sum('money'))['total_money']
            total_count_payout = payouts.aggregate(payout_count=Count('id'))['payout_count']
            print(start_datetime, end_datetime)
            print(total_amount_payout, total_count_payout)

            # Settle Payout
            settle = SettlePayout.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_settle = settle.aggregate(total_money=Sum('money'))['total_money']
            total_count_settle = settle.aggregate(payout_count=Count('id'))['payout_count']

            # Employee Deposit
            deposit = EmployeeDeposit.objects.filter(user=user, status=True).filter(time_range_query)
            total_amount_deposit = deposit.aggregate(total_money=Sum('amount'))['total_money']

            # Balance Timeline
            bank_accounts = BankAccount.objects.filter(user=user, status=True)
            start_balance = 0

            # Valid payout has Z
            total_amount_valid_payout = 0
            total_count_valid_payout = 0
            for bank_account in bank_accounts:
                # Get start balance
                balance_timeline = BalanceTimeline.objects.filter(bank_account=bank_account).filter(
                    time_range_query).first()
                if balance_timeline:
                    start_balance += balance_timeline.balance
                else:
                    start_balance += 0

                # Get transactions
                bank_transations_df = get_transactions_by_key(bank_account.account_number)
                bank_transations_df['transaction_date'] = pd.to_datetime(
                    bank_transations_df['transaction_date'], format="%d/%m/%Y %H:%M:%S")

                # Filter the DataFrame
                start_date = pd.to_datetime(start_datetime)
                end_date = pd.to_datetime(end_datetime)
                filtered_df = bank_transations_df[(bank_transations_df['transaction_type'] == 'OUT') &
                                                  (bank_transations_df['description'].str.contains('Z', case=True, na=False)) &
                                                  (bank_transations_df['transaction_date'] >= start_date) &
                                                  (bank_transations_df['transaction_date'] <= end_date)
                                                  ]

                total_amount_valid_payout += filtered_df['amount'].sum()

                # Get the total count of rows
                total_count_valid_payout += filtered_df.shape[0]

            if not total_amount_deposit:
                total_amount_deposit = 0
            if not total_amount_payout:
                total_amount_payout = 0
            if not total_amount_settle:
                total_amount_settle = 0

            estimate_end_timeline_amount = start_balance + total_amount_deposit - total_amount_payout - total_amount_settle

            results.append({
                'date': current_day.strftime('%d/%m/%Y'),
                'start_datetime': start_datetime.strftime('%H:%M'),
                'end_datetime': end_datetime.strftime('%H:%M'),
                'start_balance': start_balance or 0,
                'deposit': total_amount_deposit or 0,
                'total_amount_payout': total_amount_payout,
                'total_count_payout': total_count_payout or 0,
                'total_amount_settle': total_amount_settle,
                'total_count_settle': total_count_settle or 0,
                'total_amount_valid_payout': int(total_amount_valid_payout),
                'total_count_valid_payout': int(total_count_valid_payout),
                'estimate_end_timeline_amount': estimate_end_timeline_amount
            })

            current_day -= timedelta(days=1)

        return JsonResponse(results, safe=False)

