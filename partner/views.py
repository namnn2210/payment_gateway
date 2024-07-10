from django.shortcuts import render
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
import os
import requests
from django.core.cache import cache

load_dotenv()

@csrf_exempt
def create_deposit_order(request):
    try:
        cache.clear()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        scode = 'CID00101'
        payeeaccountno = '11112225541112'
        amount = '2000000.00'
        transfercode = 'Z7BS7R'
        payername = 'PHAN THANH DAI'
        payeraccountno = '0478373733'
        hashid = '453345'
        cardtype = 1
        key = '!QAZ2wsx'
        
        # Create the sign string
        sign_string = f"{scode}|{payeeaccountno}|{amount}|{transfercode}|{payername}|{payeraccountno}|{hashid}|{cardtype}:{key}"
        # Generate MD5 signature
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        print('===')
        print(sign_string)
        print(sign)
        
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
        print(payload)
        print('partner', os.environ.get('PARTNER'))
        # print(os.environ.get('ABC'))
        
        response = requests.post(os.environ.get('PARTNER'), data=payload, headers=headers)
        
        if response.status_code == 200:
            # response_data = response.json()
            print('++++++++++++++++', response.text)
            return JsonResponse({'status': 'success', 'message': 'done', 'data':response.text}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to reach the API'}, status=500)
        
    except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

    