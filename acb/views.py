from django.shortcuts import render
from django.http import JsonResponse
from bank.utils import Transaction
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
    print(response.text)
    match = re.search(r'{"refNo".*', response.text)
    if match:
        extracted_text = match.group(0)
        json_response = json.loads(extracted_text)
        if json_response['result']['ok']:
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
    response = requests.post(os.environ.get("MB_URL"), json=body)
    print(response.text)
    # if response.status_code == 200:
    #     data = response.json()
    #     if data:
    #         if data['result']:
    #             if data['result']['ok']:
    #                 acc_list = data['acct_list']
    #                 for account in acc_list:
    #                     if account['acctNo'] == account_number:
    #                         return account['currentBalance']
    return None
