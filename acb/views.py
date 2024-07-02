from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.
@csrf_exempt
def new_transaction(request):
    if request.method == 'POST':
        body_request_json = json.loads(request.body)
        body_requests = body_request_json.get('requests')[0]
        transaction = body_requests.get('requestParams').get('transactions')[0]
        response_body = {
            'timestamp':transaction.get('transactionDate'),
            'responseCode':transaction.get('transactionCode'),
            'message':'Success',
            "responseBody": {
                "index": 1,
                "referenceCode": transaction.get('transactionContent')
            }
        }
        return JsonResponse(response_body)
    return JsonResponse({'status': 405, 'message': 'Error'})

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

