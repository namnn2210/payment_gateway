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
    response = requests.post(os.environ.get("MB_URL"), json=body)
    print(response.text)
    
    return False
    
