from django.shortcuts import render
from django.http import JsonResponse
from bank.utils import Transaction, unix_to_datetime
import requests
from datetime import datetime, timedelta
import json
import os
import re
from dotenv import load_dotenv


load_dotenv()

# Create your views here.
def acb_login(username, password, account_number):
    body = {
        "rows": 1,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action":"login"
    }
    response = requests.post(os.environ.get("ACB_URL"), json=body)
    if response.status_code == 200:
        data = response.json()
        if data['accessToken']:
            return True
    return False
    
    
def acb_balance(username, password, account_number):
    body = {
        "rows": 10,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action":"balance"
    }
    response = requests.post(os.environ.get("ACB_URL"), json=body).json()
    if response['codeStatus'] == 200:
        acc_list = response['data']
        for account in acc_list:
            if account['accountNumber'] == account_number:
                return account['balance']
    return None

def acb_transactions(username,password,account_number):
    body = {
        "rows": 1000,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action":"transactions"
    }
    response = requests.post(os.environ.get("ACB_URL"), json=body).json()
    if response['codeStatus'] == 200:
        transactions = response['data']
        formatted_transactions = []
        for transaction in transactions:
            new_formatted_transaction = Transaction(
                transaction_number=transaction['transactionNumber'],
                transaction_date=unix_to_datetime(transaction['activeDatetime']),
                transaction_type=transaction['type'],
                account_number=transaction['account'],
                description=transaction['description']
            )
            formatted_transactions.append(new_formatted_transaction.__dict__())
            return formatted_transactions
    return None
