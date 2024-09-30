from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.http import JsonResponse
from bank.utils import Transaction
from bank.utils import get_dates, find_substring
import requests
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime
from django.utils import timezone
import pytz


load_dotenv()


def mb_login(username, password, account_number):
    body = {
        "action": "login",
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    print('start login: ', datetime.now())
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if '"ok":true' in response.text:
        print('end login: ', datetime.now())
        return True
    return False
    
def mb_transactions(username, password, account_number, start=''):
    end_date, start_date = get_dates(start_date=start)
    body = {
        "action": "transactions",
        "begin": start_date,
        "end": end_date,
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if response.status_code == 200:
        if '"ok":true' in response.text:
            json_response = json.loads(response.text)
            if json_response['result']['ok']:
                formatted_transactions = []
                transactions = json_response['transactionHistoryList']
                for transaction in transactions:
                    if int(transaction['creditAmount']) != 0:
                        transaction_type = 'IN'
                        amount = int(transaction['creditAmount'])
                    else:
                        transaction_type = 'OUT'
                        amount = int(transaction['debitAmount'])
                    new_formatted_transaction = Transaction(
                        transaction_number=transaction['refNo'],
                        transaction_date=transaction['transactionDate'],
                        transaction_type= transaction_type,
                        account_number=transaction['accountNo'],
                        description=transaction['description'],
                        transfer_code=find_substring(transaction['description']),
                        amount=amount
                    )
                    formatted_transactions.append(new_formatted_transaction.__dict__())
                return formatted_transactions
    return None


def mb_balance(username, password, account_number):
    body = {
        "action": "balance",
        "username": username,
        "accountNumber": account_number,
        "password": password
    }
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if '"ok":true' in response.text:
        data = response.json()
        acc_list = data['acct_list']
        for account in acc_list:
            if account['acctNo'] == account_number:
                return int(account['currentBalance'])
    return None

@csrf_exempt
def mb_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        return JsonResponse({'status': 200, 'message': 'Done','success': True, 'data':data})
    return JsonResponse({'status': 500, 'message': 'Invalid request','success': False})