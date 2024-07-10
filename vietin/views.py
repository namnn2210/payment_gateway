from django.shortcuts import render
from django.http import JsonResponse
from bank.utils import Transaction, unix_to_datetime
import requests
from django.views.decorators.csrf import csrf_exempt
import os
from dotenv import load_dotenv


load_dotenv()

# Create your views here.
def vietin_login(username, password, account_number):
    body = {
        "rows": 1,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action":"login"
    }
    response = requests.post(os.environ.get("VIETIN_URL"), json=body)
    if response.status_code == 200:
        data = response.json()
        if 'success' in data.keys():
            if data['success']:
                return True
    return False
    
    
def vietin_balance(username, password, account_number):
    body = {
        "rows": 10,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action":"balance"
    }
    response = requests.post(os.environ.get("VIETIN_URL"), json=body).json()
    if response:
        if 'error' in response.keys(): 
            if not response['error']:
                acc_list = response['accounts']
                for account in acc_list:
                    if account['number'] == account_number:
                        return account['accountState']['availableBalance']
    return None

def vietin_transactions(username,password,account_number):
    
    page = 0
    fetch_transactions = []
    formatted_transactions = []
    while True:
        body = {
            "rows": 1000,
            "username": username,
            "password": password,
            "accountNo": account_number,
            "page": page,
            "action": "transactions"
        }
        response = requests.post(os.environ.get("VIETIN_URL"), json=body).json()
        print(response)
        if response:
            if 'error' in response.keys():
                if not response['error']:
                    transactions = response['transactions']
                    if not transactions:  # If the transactions list is empty, break the loop
                        break
                    fetch_transactions += transactions
                    page += 1  # Increment the page number
                else:
                    break  # If there's an error, stop fetching
            else:
                break  # If 'error' key is missing, stop fetching
        else:
            break  # If response is empty, stop fetching
        
    for transaction in fetch_transactions:
        if transaction['sendingBankId'] == '':
            transaction_type='IN'
        else:
            transaction_type='OUT'
        new_formatted_transaction = Transaction(
            transaction_number=transaction['trxId'],
            transaction_date=transaction['processDate'],
            transaction_type=transaction_type,
            account_number=account_number,
            description=transaction['remark'],
            amount=transaction['amount']
        )
        formatted_transactions.append(new_formatted_transaction.to_dict())
    return formatted_transactions
    