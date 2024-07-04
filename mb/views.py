from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.http import JsonResponse
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def mb_login(username, password, account_number):
    body = {
        "action": "login",
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    response = requests.post(os.environ.get("MB_URL"), json=body).json()
    with open('response.txt', 'w') as file:
        file.write(response.text)
    return False
    
def mb_transactions(request):
    pass


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
        if data['result']['ok']:
            acc_list = data['acct_list']
            for account in acc_list:
                if account['acctNo'] == account_number:
                    return account['currentBalance']
    return 0

def mb_transfer(request):
    pass

