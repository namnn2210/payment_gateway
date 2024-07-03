from django.shortcuts import render
import json
import re
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime
from bank.views import send_telegram_message

# Create your views here.
@csrf_exempt
def new_transaction(request):
    if request.method == 'POST':
        body_request_json = json.loads(request.body)
        body_requests = body_request_json.get('requests')[0]
        transactions = body_requests.get('requestParams').get('transactions')
        for transaction in transactions:
            formatted_amount = '{:,.2f}'.format(transaction['amount'])
            dt_object = datetime.strptime(transaction["transactionDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            alert = (
                f'Hi,\n'
                f'\n'
                f'Account: {transaction['accountNumber']}\n'
                f'\n'
                f'Confirmed by order: {transaction['transactionCode']}\n'
                f'\n'
                f'Received amount💲: {formatted_amount} VND\n'
                f'\n'
                f'Memo: {transaction['transactionContent']}\n'
                f'\n'
                f'Code: {find_substring(transaction['transactionContent'])}\n'
                f'\n'
                f'Time: {formatted_datetime}\n'
                f'\n'
                f'Reason of not be credited: Order not found!!!'
            )
            send_telegram_message(alert, os.environ.get('TRANSACTION_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
    return JsonResponse({'status': 200, 'message': 'OK'})
@csrf_exempt
def transfer_callback_1(request):
    if request.method == 'POST':
        return JsonResponse({'status': 200, 'message': 'Transfer callback 1 successful'})
    return JsonResponse({'status': 405, 'message': 'Error'})

@csrf_exempt
def transfer_callback_2(request):
    if request.method == 'POST':
        return JsonResponse({'status': 200, 'message': 'Transfer callback 2 successful'})
    return JsonResponse({'status': 405, 'message': 'Error'})

def find_substring(text):
        # Regex pattern to find a substring starting with 'Z' and having 7 characters
        pattern = r'Z.{6}'
        match = re.search(pattern, text)
        if match:
            return match.group()
        else:
            return None

