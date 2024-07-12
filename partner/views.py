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
        scode = key_df[key_df['bankno'] == transaction['account_number']]['scode'].values
        cardtype = key_df[key_df['bankno'] == transaction['account_number']]['cardtype'].values
        key = key_df[key_df['bankno'] == transaction['account_number']]['key'].values
        
        print(transaction['account_number'], scode, cardtype, key)
        payeeaccountno = transaction['account_number']
        amount = f'{str(transaction['amount'])}.00'
        
        transfercode = transaction['transfer_code']
        payername = 'NA'
        payeraccountno = transaction['account_number'][-4:]
        
        hashid = transaction['transaction_number']
        
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
        
        if response.status_code == 200:
            response_data = response.json()
            return JsonResponse(response_data, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to reach the API'}, status=500)
        
    except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

    