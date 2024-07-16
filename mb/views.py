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
import pytz


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
    response = requests.post(os.environ.get("MB_URL"), json=body)
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

def mb2_transactions(username, password, account_number):
    response = requests.get(os.environ.get("MB2_URL"))
    if response.status_code == 200:
        transactions = response.json()
        formatted_transactions = []
        total_amount = 0
        if transactions:
            for transaction in transactions:
                if transaction['account_receiver'] == account_number:
                    total_amount += transaction['amount']
                    if int(transaction['amount']) != 0:
                            transaction_type = 'IN'
                    else:
                        transaction_type = 'OUT'
                    new_formatted_transaction = Transaction(
                        transaction_number=transaction['transaction_id'],
                        transaction_date=convert_to_bangkok_time(transaction['date']),
                        transaction_type= transaction_type,
                        account_number=transaction['account_receiver'],
                        description=transaction['content'],
                        transfer_code=find_substring(transaction['content']),
                        amount=transaction['amount']
                    )
                    formatted_transactions.append(new_formatted_transaction.__dict__())
            return total_amount, formatted_transactions
    return None, None

def convert_to_bangkok_time(utc_time_str):
    # Define the format of the input UTC time string
    utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    
    # Parse the input string to a datetime object
    utc_time = datetime.strptime(utc_time_str, utc_format)
    
    # Set the timezone to UTC
    utc_time = utc_time.replace(tzinfo=pytz.UTC)
    
    # Define the Bangkok timezone
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    
    # Convert UTC time to Bangkok time
    bangkok_time = utc_time.astimezone(bangkok_tz)
    
    # Define the format for the output string
    bangkok_format = "%d/%m/%Y %H:%M:%S"
    
    # Return the formatted Bangkok time string
    return bangkok_time.strftime(bangkok_format)
