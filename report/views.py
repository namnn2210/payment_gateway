from django.shortcuts import render
from bank.database import redis_connect
from payout.models import Payout
from bank.views import get_all_transactions, get_start_end_datetime, get_start_end_datetime_string
from datetime import datetime
from django.db.models import Sum
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
    
    report_data = {
        "payout": {
            "total_amount":total_payout_amount,
            "total_results":total_payout_results
        },
        "transactions":{
            "total_amount":total_transaction_amount,
            "total_results":total_transaction_results
        }
    }
    
    return render(request=request, template_name='report.html', context={'last_5_days_data': json.dumps(last_5_days_data), 'report_data':report_data})