from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.http import JsonResponse
from bank.utils import Transaction
import requests
import json
import os
import re
from dotenv import load_dotenv


load_dotenv()


def mb_login(username, password, account_number):
    body = {
        "action": "login",
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    response = requests.post(os.environ.get("MB_URL"), json=body)
    match = re.search(r'{"refNo".*', response.text)
    if match:
        extracted_text = match.group(0)
        json_response = json.loads(extracted_text)
        if json_response['result']['ok']:
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
    response = requests.post(os.environ.get("MB_URL"), json=body)
    if response.status_code == 200:
        match = re.search(r'{"refNo".*', response.text)
        if match:
            extracted_text = match.group(0)
            json_response = json.loads(extracted_text)
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
    response = requests.post(os.environ.get("MB_URL"), json=body)
    print(response.text)
    if response.status_code == 200:
        data = response.json()
        if data:
            if data['result']:
                if data['result']['ok']:
                    acc_list = data['acct_list']
                    for account in acc_list:
                        if account['acctNo'] == account_number:
                            return account['currentBalance']
    return None

def mb_transfer(request):
    pass

def get_dates(start_date=''):
    # If start_date is empty, use the current date
    if start_date == '':
        start_date = datetime.now()
    else:
        # Parse the provided start date
        start_date = datetime.strptime(start_date, '%d/%m/%Y')
    
    # Calculate the date 30 days before the start date
    date_30_days_before = start_date - timedelta(days=30)
    
    # Return the results in the specified format
    return start_date.strftime('%d/%m/%Y'), date_30_days_before.strftime('%d/%m/%Y')

