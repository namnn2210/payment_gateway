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
    match = re.search(r'{"refNo".*', response.text)
    if match:
        extracted_text = match.group(0)
        json_response = json.loads(extracted_text)
        if json_response['result']['ok']:
            return True
    
    return False
    
