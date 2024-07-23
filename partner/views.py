from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
import hashlib
import pandas as pd
import os
import requests

load_dotenv()

def create_deposit_order(transaction,partner_mapping):
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        # key_df = pd.read_csv(os.environ.get('MID_KEY'))
        scode = partner_mapping.cid
        cardtype = partner_mapping.cardtype
        key = partner_mapping.key
        
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
        
        response = requests.post(os.environ.get('DEPOSIT_URL'), data=payload, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:
            return None
        
    except Exception as e:
            return None
    


def update_status_request(payout, status='S'):
    key = '!QAZ2wsx'
    sign_string = f"{payout.scode}|{payout.orderno}:{key}"
    # Generate MD5 signature
    sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    request_body = {
        "scode": payout.scode,
        "data": [
            {
                "orderno": payout.orderno,
                "amount": f'{payout.amount}.00',
                "payerbankname": payout.bankcode,
                "payeraccountno": "226662",
                "payeraccountname": "226 pay",
                "status": status
            }
        ],
        "sign": sign
    }
    
    response = requests.post(os.environ.get('DEPOSIT_URL'), body=request_body)
    if response.status_code == 200:
        response_data = response.json()
        if response_data['msg'] == 'SUCCESS':
            update_success_list = response_data.get('updatescuuesslist')
            for item in update_success_list:
                if item == payout.orderno:
                    return True
    return False