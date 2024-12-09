from io import BytesIO

from django.shortcuts import render
from .models import Bank, BankAccount
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.forms.models import model_to_dict
from datetime import datetime
from django.core.paginator import Paginator
from mongodb.views import update_transaction_status, get_transactions_by_account_number, get_total_amount

import json
import pandas as pd


# Create your views here.
@login_required(login_url='user_login')
def list_bank(request):
    list_bank_option = Bank.objects.filter(status=True)
    if request.user.is_superuser:
        list_user_bank = BankAccount.objects.all()
    else:
        list_user_bank = BankAccount.objects.filter(user=request.user)
    return render(request=request, template_name='bank.html',
                  context={'list_bank_option': list_bank_option, 'list_user_bank': list_user_bank})


@login_required(login_url='user_login')
def record_book(request):
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_datetime', None)
    end_date = request.GET.get('end_datetime', None)
    status = request.GET.get('status', None)

    if not start_date or not end_date:
        today = datetime.now()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_date_str = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_str = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

        start_date_str = start_date
        end_date_str = end_date

    bank_accounts = BankAccount.objects.all()
    account_number = [item.account_number for item in bank_accounts]
    order_by = ("transaction_date", -1)
    list_transactions_in = get_transactions_by_account_number(account_number, transaction_type='IN', status=status,
                                                              date_start=start_date, date_end=end_date,
                                                              order_by=order_by, search_text=search_query)
    list_transactions_out = get_transactions_by_account_number(account_number, transaction_type='OUT', status=status,
                                                               date_start=start_date, date_end=end_date,
                                                               order_by=order_by, search_text=search_query)

    # Calculate total amounts
    total_in_amount = sum(txn.get('amount', 0) for txn in list_transactions_in)
    total_out_amount = sum(txn.get('amount', 0) for txn in list_transactions_out)

    # Pagination for "IN" transactions
    in_paginator = Paginator(list_transactions_in, 6)
    in_page_number = request.GET.get('in_page')
    in_page_obj = in_paginator.get_page(in_page_number)

    # Pagination for "OUT" transactions
    out_paginator = Paginator(list_transactions_out, 6)
    out_page_number = request.GET.get('out_page')
    out_page_obj = out_paginator.get_page(out_page_number)

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':

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

        return JsonResponse(data)

    return render(request, 'record_book.html', {
        'in_page_obj': in_page_obj,
        'out_page_obj': out_page_obj,
        'search_query': search_query,
        'start_date': start_date_str.strftime('%Y-%m-%dT%H:%M'),
        'end_date': end_date_str.strftime('%Y-%m-%dT%H:%M'),
        'total_in_amount': total_in_amount,
        'total_out_amount': total_out_amount,
    })


@method_decorator(csrf_exempt, name='dispatch')
class AddBankView(View):
    def post(self, request, *args, **kwargs):
        try:
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
        except Exception as ex:
            print(str(ex))
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
    if request.user.is_superuser:
        bank_accounts = BankAccount.objects.filter(status=True)
    else:
        bank_accounts = BankAccount.objects.filter(user=request.user, status=True)

    account_number = [item.account_number for item in bank_accounts]
    order_by = ("transaction_date", -1)
    list_df_in = get_transactions_by_account_number(account_number, transaction_type='IN', order_by=order_by,
                                                    limit_number=5)
    list_df_out = get_transactions_by_account_number(account_number, transaction_type='OUT',
                                                     order_by=order_by, limit_number=5)
    return JsonResponse(
        {'status': 200, 'message': 'Done', 'data': {'in': list_df_in, 'out': list_df_out}})


def update_balance(request):
    if request.user.is_superuser:
        bank_accounts = BankAccount.objects.all()
    else:
        bank_accounts = BankAccount.objects.filter(user=request.user)

    list_dict_accounts = []
    for bank_account in bank_accounts:
        list_dict_accounts.append(model_to_dict(bank_account))
    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'balance': list_dict_accounts}})


def get_amount_today(request):
    total_in = 0
    total_out = 0
    if request.user.is_superuser:
        today = datetime.now()
        date_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        total_in = get_total_amount(date_start, date_end, "IN")
        total_out = get_total_amount(date_start, date_end, "OUT")
    # else:
    #     try:
    #         user_timeline = UserTimeline.objects.filter(user=request.user).first()
    #         start_at = user_timeline.timeline.start_at
    #         end_at = user_timeline.timeline.end_at
    #         start_datetime, end_datetime = get_start_end_datetime_by_timeline(start_at, end_at)
    #         time_range_query = Q(created_at__gte=start_datetime) & Q(created_at__lt=end_datetime)
    #         payouts = Payout.objects.filter(user=request.user, status=True).filter(time_range_query)
    #         total_out = payouts.aggregate(total_money=Sum('money'))['total_money'] or 0
    #         deposit = EmployeeDeposit.objects.filter(user=request.user, status=True).filter(time_range_query)
    #         total_in = deposit.aggregate(total_money=Sum('amount'))['total_money'] or 0
    #         return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in': total_in, 'out': total_out}})
    #     except Exception as ex:
    #         return JsonResponse({'status': 500, 'message': 'Invalid request'})
    return JsonResponse({'status': 200, 'message': 'Done', 'data': {'in': total_in, 'out': total_out}})


def update_transaction_history_status(account_number, transaction_number, transfer_code, orderid, scode,
                                      incomingorderid, status):
    update_transaction_status(account_number, transaction_number, transfer_code, orderid, scode, incomingorderid,
                              status)


def export_to_excel(request):
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_datetime', None)
    end_date = request.GET.get('end_datetime', None)
    status = request.GET.get('status', None)

    if not start_date or not end_date:
        today = datetime.now()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

    bank_accounts = BankAccount.objects.all()
    account_number = [item.account_number for item in bank_accounts]
    order_by = ("transaction_date", -1)
    list_transactions = get_transactions_by_account_number(account_number, status=status,
                                                           date_start=start_date, date_end=end_date,
                                                           order_by=order_by, search_text=search_query)

    filtered_transactions_df = pd.DataFrame(list_transactions)

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
        response = HttpResponse(buffer,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=filtered_transactions.xlsx'

        return response
    else:
        # Return an empty Excel file or an error response
        return HttpResponse('No transactions found for the specified filters.', content_type='text/plain')
