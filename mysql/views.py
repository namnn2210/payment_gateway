from django.db.models import Q
from transaction.models import TransactionHistory
from django.apps import apps
from bank.utils import send_telegram_message
from bank.utils import format_transaction_list, get_today_date
from config.views import get_env
from django.db.models import Sum
import re
import logging

logger = logging.getLogger('django')

def get_transactions_by_account_number(account_number, transaction_type=None, status=None, date_start=None,
                                       date_end=None, order_by=None, limit_number=None, search_text=None):
    query_filters = Q()

    # Filter by account number
    if isinstance(account_number, str):
        query_filters &= Q(account_number=account_number)
    elif isinstance(account_number, list):
        query_filters &= Q(account_number__in=account_number)

    print(date_start, date_end)

    # Filter by transaction date range
    if date_start is not None and date_end is not None:
        query_filters &= Q(created_at__range=[date_start, date_end])

    # Filter by transaction type
    if transaction_type is not None:
        if isinstance(transaction_type, str):
            query_filters &= Q(transaction_type=transaction_type)
        elif isinstance(transaction_type, list):
            query_filters &= Q(transaction_type__in=transaction_type)

    # Filter by status
    if status is not None:
        if status == 'Blank':
            query_filters &= Q(status__isnull=True)
        elif status != 'All':
            query_filters &= Q(status=status)

    # Search text filtering (case-insensitive search on multiple fields)
    if search_text:
        search_text = search_text.strip()
        query_filters &= (
            Q(transaction_number__icontains=search_text) |
            Q(description__icontains=search_text) |
            Q(account_number__icontains=search_text) |
            Q(transfer_code__icontains=search_text)
        )

    # Query the database
    transactions = TransactionHistory.objects.filter(query_filters)

    transactions = transactions.order_by("-created_at")
    

    # Apply limit
    if limit_number is not None and limit_number > 0:
        transactions = transactions[:limit_number]

    # Convert to a list of dictionaries (if needed)
    transaction_list = list(transactions.values())

    return transaction_list

def get_transaction_by_transaction_number(transaction_number):
    return TransactionHistory.objects.filter(transaction_number=transaction_number).first()

def get_transaction_by_description(description_substring):
    return TransactionHistory.objects.filter(description__icontains=description_substring).first()

def get_new_transactions(transactions, account_number):
    existing_transaction_numbers = TransactionHistory.objects.filter(account_number=account_number).values_list('transaction_number', flat=True)

    new_transactions = [txn for txn in transactions if txn['transaction_number'] not in existing_transaction_numbers]

    # Check if transaction is OUT and contains Z -> success
    # for txn in new_transactions:
    #     if txn['transaction_type'] == 'OUT':
    #         txn['status'] = 'Success'

    return new_transactions

def get_unprocessed_transactions(account_number):
    start_date, end_date = get_today_date()
    return TransactionHistory.objects.filter(
        account_number=account_number,
        transaction_type='IN',
        created_at__range=(start_date, end_date),
        status='',
    ).exclude(transfer_code='').values()

def update_transaction_status(account_number, transaction_number, update_fields):
    TransactionHistory.objects.filter(transaction_number=transaction_number, account_number=account_number).update(**update_fields)


def insert_all(transaction_list):
    TransactionHistory.objects.bulk_create([
        TransactionHistory(**txn) for txn in transaction_list
    ], ignore_conflicts=True)

def get_total_amount(date_start, date_end, transaction_type):
    result = TransactionHistory.objects.filter(
        created_at__range=(date_start, date_end),
        transaction_type__in=transaction_type,
        status="Success"
    ).aggregate(total_amount=Sum('amount'))

    return result['total_amount'] or 0