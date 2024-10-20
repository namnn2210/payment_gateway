import json

from django.shortcuts import render
import requests
import os
from datetime import datetime, timedelta
from bank.utils import Transaction, find_substring
# Create your views here.
def tech_login(username, password, account_number):
    body = {
        "username": username,
        "password": password,
        "accountNumber": account_number,
    }
    response = requests.post(f'{os.environ.get("TECH_URL")}login', json=body, timeout=120).json()
    if response['success']:
        return True
    return False

def tech_balance(username, password, account_number):
    body = {
        "username": username,
        "password": password,
        "accountNumber": account_number,
    }

    response = requests.post(f'{os.environ.get("TECH_URL")}balance', json=body , timeout=120).json()
    if response:
       for item in response:
           print(type(item))
           account = json.loads(item)
           if account['BBAN'] == account_number:
               return account['availableBalance']
    return None

def tech_transactions(username, password, account_number):
    formatted_transactions = []
    # Get today's date
    end_date = datetime.now()

    # Calculate the date 30 days ago
    begin_date = end_date - timedelta(days=30)

    # Format the dates as "DD/MM/YYYY"
    begin_str = begin_date.strftime("%d/%m/%Y")
    end_str = end_date.strftime("%d/%m/%Y")

    # Example payload
    body = {
        "begin": begin_str,
        "end": end_str,
        "username": username,
        "password": password,
        "accountNumber": account_number,
        "size": "500"
    }

    response = requests.post(f'{os.environ.get("TECH_URL")}', json=body, timeout=120).json()
    if response['success']:
        transactions = response['transactions']
        transaction_type = ''
        for transaction in transactions:
            print(transaction)
            if 'category' not in transaction.keys():
                continue
            if transaction['category'] == "Spending":
                transaction_type = "OUT"
            elif transaction['category'] == "Income":
                transaction_type = "IN"
            print(transaction_type)
            transaction_date = datetime.fromisoformat(transaction['creationTime'])
            transaction_date = transaction_date.strftime('%d/%m/%Y %H:%M:%S')
            new_formatted_transaction = Transaction(
                transaction_number=transaction['reference'],
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                account_number=account_number,
                description=transaction['description'],
                transfer_code=find_substring(transaction['description']),
                amount=int(transaction['transactionAmountCurrency']['amount'])
            )
            formatted_transactions.append(new_formatted_transaction.__dict__())
        return formatted_transactions
    return None