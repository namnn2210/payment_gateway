from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
import hashlib
import pandas as pd
import os
import requests

load_dotenv()

def create_deposit_order(transaction):
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        key_df = pd.read_csv(os.environ.get('MID_KEY'))
        scode = key_df[key_df['bankno'] == transaction['account_number']]['scode'].iloc[0]
        cardtype = key_df[key_df['bankno'] == transaction['account_number']]['cardtype'].iloc[0]
        key = key_df[key_df['bankno'] == transaction['account_number']]['key'].iloc[0]
        
        payeeaccountno = str(transaction['account_number'])
        amount = f'{str(transaction['amount'])}.00'
        
        transfercode = transaction['transfer_code']
        payername = 'NA'
        payeraccountno = str(transaction['account_number'])[-4:]
        
        hashid = str(transaction['transaction_number'])
        
        # Create the sign string
        sign_string = f"{scode}|{payeeaccountno}|{amount}|{transfercode}|{payername}|{payeraccountno}|{hashid}|{cardtype}:{key}"
        # Generate MD5 signature
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        
        payload = {
            'scode': scode,
            'payeeaccountno': payeeaccountno,
            'cardtype': cardtype,
            'amount': amount,
            'payername': payername,
            'payeraccountno': payeraccountno,
            'transfercode': transfercode,
            'hashid': hashid,
            'sign': sign,
        }
        
        response = requests.post(os.environ.get('PARTNER'), data=payload, headers=headers)
        print(response.json())
        if response.status_code == 200:
            response_data = response.json()
            return JsonResponse(response_data, status=200)
        else:
            return JsonResponse({'status': 'error', 'msg': 'Failed to reach the API'}, status=500)
        
    except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)
    

    