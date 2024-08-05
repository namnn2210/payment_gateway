from django.shortcuts import render
from bank.database import redis_connect
from payout.models import Payout
from bank.views import get_all_transactions, get_start_end_datetime, get_start_end_datetime_string
from bank.models import BankAccount
from django.db.models import Sum
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
import pandas as pd
import json
# Create your views here.
def report(request):
    
    start_datetime_str = request.GET.get('start_datetime', '')
    end_datetime_str = request.GET.get('end_datetime', '')
    total_payout_results = 0
    total_payout_amount = 0
    total_transaction_amount = 0
    total_transaction_results = 0
    
    # Get in out data 
    redis_client = redis_connect(3)
    keys = redis_client.keys('*')
    data = {}
    for key in keys:
        data[key.decode('utf-8')] = redis_client.get(key).decode('utf-8')
    sorted_dates = sorted(data.keys())[-5:]
    last_5_days_data = {date: json.loads(data[date]) for date in sorted_dates}

    # Get payout data
    
    start_date, end_date = get_start_end_datetime_string(start_datetime_str, end_datetime_str)
        
    list_payout = Payout.objects.all()
        
    list_payout = list_payout.filter(created_at__gte=start_date, created_at__lte=end_date)
    total_payout_results = len(list_payout)
    total_payout_amount = list_payout.aggregate(Sum('money'))['money__sum'] or 0
    
    # Get transactions data
    
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
        
        
    # Get all user        
    list_users = User.objects.filter(is_superuser=False)
    
    user_info_dict = {}
    
    
    for user in list_users:
        bank_accounts = []
        user_bank_accounts = BankAccount.objects.filter(user=user, status=True)
        for bank_account in user_bank_accounts:   
            bank_accounts.append({
                "account_no":bank_account.account_number,
                "bank_name":bank_account.bank_name.name,
                "balance":bank_account.balance,
                "bank_type":bank_account.bank_type
            })
        user_info_dict[user.username] = {
            "bank_accounts":bank_accounts
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