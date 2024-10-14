from django.shortcuts import render
from payout.models import Payout
from settle_payout.models import SettlePayout
from employee.models import EmployeeDeposit
from bank.views import get_all_transactions, get_start_end_datetime
from bank.models import BankAccount
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count
from bank.views import get_transactions_by_key
from django.http import JsonResponse
from employee.models import EmployeeWorkingSession
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import pandas as pd

# Create your views here.

@login_required(login_url='user_login')
def report(request):
    all_transactions_df = get_all_transactions()
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_datetime', '')
    end_date = request.GET.get('end_datetime', '')

    start_date, end_date = get_start_end_datetime(start_date, end_date)

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
        filtered_transactions_df = filtered_transactions_df.fillna('')

        if search_query:
            filtered_transactions_df = filtered_transactions_df[
                filtered_transactions_df.apply(
                    lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)
            ]

        # Separate and sort transactions by type
        in_transactions_df = filtered_transactions_df[filtered_transactions_df['status'] != 'Success'].sort_values(
            by='transaction_date', ascending=False)
        # out_transactions_df = filtered_transactions_df[
        #     filtered_transactions_df['transaction_type'] == 'OUT'].sort_values(by='transaction_date', ascending=False)

        # Calculate total amounts
        total_in_amount = in_transactions_df['amount'].sum()
        # total_out_amount = out_transactions_df['amount'].sum()

        # Pagination for "IN" transactions
        in_paginator = Paginator(in_transactions_df.to_dict(orient='records'), 6)
        in_page_number = request.GET.get('in_page')
        in_page_obj = in_paginator.get_page(in_page_number)

        # Pagination for "OUT" transactions
        # out_paginator = Paginator(out_transactions_df.to_dict(orient='records'), 6)
        # out_page_number = request.GET.get('out_page')
        # out_page_obj = out_paginator.get_page(out_page_number)

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            # Return JSON response for AJAX requests

            total_in_amount = int(float(in_transactions_df['amount'].sum()))
            # total_out_amount = int(float(out_transactions_df['amount'].sum()))

            data = {
                'in_transactions': list(in_page_obj),
                # 'out_transactions': list(out_page_obj),
                'in_page': in_page_obj.number,
                'in_num_pages': in_page_obj.paginator.num_pages,
                # 'out_page': out_page_obj.number,
                # 'out_num_pages': out_page_obj.paginator.num_pages,
                'total_in_amount': total_in_amount,
                # 'total_out_amount': total_out_amount,
            }

            return JsonResponse(data)

        return render(request, 'report.html', {
            'in_page_obj': in_page_obj,
            # 'out_page_obj': out_page_obj,
            'search_query': search_query,
            'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_date.strftime('%Y-%m-%dT%H:%M'),
            'total_in_amount': total_in_amount,
            # 'total_out_amount': total_out_amount,
        })
    return render(request, 'report.html', {
        'in_page_obj': None,
        'out_page_obj': None,
        'search_query': search_query,
        'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
        'end_date': end_date.strftime('%Y-%m-%dT%H:%M'),
        'total_in_amount': 0,
        'total_out_amount': 0,
    })



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

