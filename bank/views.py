from io import BytesIO
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import model_to_dict
from datetime import datetime
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Bank, BankAccount
from mysql.views import (
    update_transaction_status,
    get_transactions_by_account_number,
    get_total_amount,
)
from bank.utils import get_today_date, clean_text
import pandas as pd

# Helper function (not a view)
def update_transaction_history_status(
    account_number, transaction_number, transfer_code, orderid, scode,
    incomingorderid, status, payer_name
):
    update_fields = {
        "orderid": orderid,
        "scode": scode,
        "incomingorderid": incomingorderid,
        "payername": payer_name,
        "status": status,
    }
    update_transaction_status(account_number, transaction_number, update_fields)

# --- Django Class-Based Views (for HTML rendering) ---

class BankListView(LoginRequiredMixin, ListView):
    model = BankAccount
    template_name = 'bank.html'
    context_object_name = 'list_user_bank'
    login_url = 'cms:user_login'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_bank_option'] = Bank.objects.filter(status=True)
        return context

class RecordBookView(LoginRequiredMixin, TemplateView):
    template_name = 'record_book.html'
    login_url = 'cms:user_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date = get_today_date()
        context.update({
            'search_query': '',
            'start_date': start_date.strftime('%Y-%m-%dT%H:%M'),
            'end_date': end_date.strftime('%Y-%m-%dT%H:%M'),
            'total_in_amount': 0, # Will be loaded by AJAX
            'total_out_amount': 0, # Will be loaded by AJAX
        })
        return context

class ExportTransactionsExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '')
        start_date_str = request.GET.get('start_datetime')
        end_date_str = request.GET.get('end_datetime')
        status_filter = request.GET.get('status')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        else:
            start_date, end_date = get_today_date()

        bank_accounts = BankAccount.objects.all()
        account_numbers = [item.account_number for item in bank_accounts]
        order_by = ("transaction_date", -1)

        list_transactions = get_transactions_by_account_number(
            account_numbers,
            status=status_filter,
            date_start=start_date,
            date_end=end_date,
            order_by=order_by,
            search_text=search_query
        )

        df = pd.DataFrame(list_transactions).applymap(clean_text)

        if not df.empty:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Transactions', index=False)
            buffer.seek(0)
            response = HttpResponse(
                buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=filtered_transactions.xlsx'
            return response
        return HttpResponse('No transactions found for the specified filters.', content_type='text/plain')


# --- DRF API Views (for AJAX/JSON responses) ---

class AddBankAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            bank = Bank.objects.filter(name=data.get('bankName')).first()
            if not bank:
                return Response({'message': 'Bank not found'}, status=status.HTTP_400_BAD_REQUEST)

            if BankAccount.objects.filter(user=request.user, account_number=data.get('bankNumber'), bank_type=data.get('bankType')).exists():
                return Response({'message': 'Existed bank. Please try again'}, status=status.HTTP_409_CONFLICT)

            BankAccount.objects.create(
                user=request.user,
                bank_name=bank,
                account_number=data.get('bankNumber'),
                account_name=data.get('bankAccountName'),
                username=data.get('bankUsername'),
                password=data.get('bankPassword'),
                bank_type=data.get('bankType'),
                corp_id=data.get('corpId', ''),
                balance=0,
            )
            return Response({'message': 'Bank added successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'message': f'Failed to add bank: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ToggleBankStatusAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            bank_account = BankAccount.objects.get(id=request.data.get('id'))
            bank_account.status = request.data.get('status') == 'ON'
            bank_account.save()
            return Response({'message': 'Status updated successfully'}, status=status.HTTP_200_OK)
        except BankAccount.DoesNotExist:
            return Response({'message': 'Bank account not found'}, status=status.HTTP_404_NOT_FOUND)

class ToggleTransactionStatusAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            update_transaction_status(
                request.data.get('accountNumber'),
                request.data.get('transactionNumber'),
                {"status": "Success"}
            )
            return Response({'message': 'Status updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f'Failed to update status: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransactionHistoryAPIView(APIView):
    def get(self, request, *args, **kwargs):
        bank_accounts = BankAccount.objects.filter(user=request.user, status=True) if not request.user.is_superuser else BankAccount.objects.filter(status=True)
        account_numbers = [item.account_number for item in bank_accounts]
        order_by = ("transaction_date", -1)
        
        list_df_in = get_transactions_by_account_number(account_numbers, transaction_type=['IN', 'ALL'], order_by=order_by, limit_number=5)
        list_df_out = get_transactions_by_account_number(account_numbers, transaction_type=['OUT', 'ALL'], order_by=order_by, limit_number=5)
        
        return Response({'in': list_df_in, 'out': list_df_out}, status=status.HTTP_200_OK)

class BalanceAPIView(APIView):
    def get(self, request, *args, **kwargs):
        bank_accounts = BankAccount.objects.filter(user=request.user) if not request.user.is_superuser else BankAccount.objects.all()
        data = [model_to_dict(acc) for acc in bank_accounts]
        return Response({'balance': data}, status=status.HTTP_200_OK)

class TodayAmountAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            start_date, end_date = get_today_date()
            total_in = get_total_amount(start_date, end_date, ["IN", "ALL"])
            total_out = get_total_amount(start_date, end_date, ["OUT", "ALL"])
            return Response({'in': total_in, 'out': total_out}, status=status.HTTP_200_OK)
        # Add logic for non-superusers if needed, otherwise it will fall through and return an empty response
        return Response({'in': 0, 'out': 0}, status=status.HTTP_200_OK)

class RecordBookDataAPIView(APIView):
    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        start_date_str = request.query_params.get('start_datetime')
        end_date_str = request.query_params.get('end_datetime')
        status_filter = request.query_params.get('status')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        else:
            start_date, end_date = get_today_date()

        order_by = None
        
        # Fetch all transactions first
        list_transactions_in = get_transactions_by_account_number(None, transaction_type='IN', status=status_filter, date_start=start_date, date_end=end_date, order_by=order_by, search_text=search_query)
        list_transactions_out = get_transactions_by_account_number(None, transaction_type='OUT', status=status_filter, date_start=start_date, date_end=end_date, order_by=order_by, search_text=search_query)

        # Clean transaction numbers
        for item in list_transactions_in:
            item['transaction_number'] = item.get('transaction_number', '').replace('\\BNK', '')
        for item in list_transactions_out:
            item['transaction_number'] = item.get('transaction_number', '').replace('\\BNK', '')

        # Calculate totals
        total_in_amount = sum(txn.get('amount', 0) for txn in list_transactions_in)
        total_out_amount = sum(txn.get('amount', 0) for txn in list_transactions_out)

        # Paginate results
        page_size = int(request.query_params.get('page_size', 10))  # Default to 20 items per page

        in_paginator = Paginator(list_transactions_in, page_size)
        in_page_obj = in_paginator.get_page(request.query_params.get('in_page'))
        
        out_paginator = Paginator(list_transactions_out, page_size)
        out_page_obj = out_paginator.get_page(request.query_params.get('out_page'))

        data = {
            'in_transactions': in_page_obj.object_list,
            'out_transactions': out_page_obj.object_list,
            'in_page': in_page_obj.number,
            'in_num_pages': in_paginator.num_pages,
            'out_page': out_page_obj.number,
            'out_num_pages': out_paginator.num_pages,
            'total_in_amount': total_in_amount,
            'total_out_amount': total_out_amount,
        }
        return Response(data)