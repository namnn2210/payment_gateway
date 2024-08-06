from django.shortcuts import render
from bank.database import redis_connect
from payout.models import Payout
from settle_payout.models import SettlePayout
from employee.models import EmployeeDeposit
from bank.views import get_all_transactions, get_start_end_datetime, get_start_end_datetime_string
from bank.models import BankAccount
from payout.models import Timeline, UserTimeline
from django.db.models import Sum
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from datetime import datetime, time
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count,Min
from datetime import datetime, timedelta, time
from django.http import JsonResponse
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
            all_transactions_df['transaction_date'] = pd.to_datetime(all_transactions_df['transaction_date'], format='%d/%m/%Y %H:%M:%S')

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
    timelines = Timeline.objects.filter(status=True)
    current_time = datetime.now(timezone).time()
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
    
    if current_timeline_name:
        # Get the active timelines from the database
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
                    'name':user_timeline.timeline.name,
                    'start_at':user_timeline.timeline.start_at,
                    'end_at':user_timeline.timeline.end_at
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
                    'name':user_timeline.timeline.name,
                    'start_at':user_start_time,
                    'end_at':user_end_time
                }
        
            # Current payout data in timeline
            now = datetime.now(timezone)
            current_day = now.date()
            
            if user_start_time < user_end_time:
                start_datetime = datetime.combine(current_day, user_start_time).replace(tzinfo=timezone)
                end_datetime = datetime.combine(current_day, user_end_time).replace(tzinfo=timezone)
            else:  # Over midnight scenario
                start_datetime = datetime.combine(current_day - timedelta(days=1), user_start_time).replace(tzinfo=timezone)
                end_datetime = datetime.combine(current_day, user_end_time).replace(tzinfo=timezone)
            time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)
            payouts = Payout.objects.filter(user=user, status=True).filter(time_range_query)
            
            current_payout_info['current_total_amount_payout'] = payouts.aggregate(total_money=Sum('money'))['total_money'] or 0
            current_payout_info['curent_total_count_payout'] = payouts.aggregate(payout_count=Count('id'))['payout_count'] or 0
            
        # Bank accounts data
        for bank_account in user_bank_accounts:   
            bank_accounts.append({
                "account_no":bank_account.account_number,
                "bank_name":bank_account.bank_name.name,
                "balance":bank_account.balance,
                "bank_type":bank_account.bank_type
            })
            
        user_info_dict[user.username] = {
            "bank_accounts":bank_accounts,
            "online":online,
            "timeline":timeline_info,
            "payout":current_payout_info
        }
    
    report_data = {
        "chart":json.dumps(last_5_days_data),
        "payout": {
            "total_amount":total_payout_amount,
            "total_results":total_payout_results
        },
        "transactions":{
            "total_amount":total_transaction_amount,
            "total_results":total_transaction_results
        },
        "users":user_info_dict
    }
    
    return render(request=request, template_name='report.html', context={'report_data':report_data})

@csrf_exempt
@require_POST
def report_payout_by_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user = User.objects.filter(username=username).first()
        user_timeline = UserTimeline.objects.filter(user=user).first()
        start_time = user_timeline.timeline.start_at
        end_time = user_timeline.timeline.end_at
        
        # Get the oldest created_at date for Payout
        oldest_payout_date = Payout.objects.filter(user=user).aggregate(oldest_date=Min('created_at'))['oldest_date']

        if not oldest_payout_date:
            return JsonResponse([], safe=False)
        
        oldest_payout_date = oldest_payout_date.astimezone(timezone)

        # Ensure the current time is timezone-aware
        now = datetime.now(timezone)
        current_day = now.date()

        results = []

        while True:
            if start_time < end_time:
                start_datetime = datetime.combine(current_day, start_time).replace(tzinfo=timezone)
                end_datetime = datetime.combine(current_day, end_time).replace(tzinfo=timezone)
            else:  # Over midnight scenario
                start_datetime = datetime.combine(current_day - timedelta(days=1), start_time).replace(tzinfo=timezone)
                end_datetime = datetime.combine(current_day, end_time).replace(tzinfo=timezone)

            # Break the loop if start_datetime is less than the oldest_date
            if start_datetime < oldest_payout_date:
                break
            

            time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)

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

            results.append({
                'date': current_day.strftime('%d/%m/%Y'),
                'start_datetime': start_datetime.strftime('%H:%M'),
                'end_datetime': end_datetime.strftime('%H:%M'),
                'deposit':total_amount_deposit or 0,
                'total_amount_payout': total_amount_payout or 0,
                'total_count_payout': total_count_payout or 0,
                'total_amount_settle':total_amount_settle or 0,
                'total_count_settle':total_count_settle or 0
            })

            current_day -= timedelta(days=1)

        return JsonResponse(results, safe=False)