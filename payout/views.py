from django.shortcuts import render
from .models import Payout, Timeline, UserTimeline
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from bank.utils import send_telegram_message
from bank.views import update_amount_by_date
from bank.models import Bank
from notification.views import send_notification
from dotenv import load_dotenv
from datetime import datetime
from partner.views import update_payout_status_request
from django.db.models import Q, BooleanField, Case, Value, When, IntegerField
from .tasks import update_payout_background
import pytz
import os
import json
import random
import requests
import hashlib

load_dotenv()
# Create your views here.
@login_required(login_url='user_login')
def list_payout(request):
    
    bank_data = json.load(open('bank.json', encoding='utf-8'))
    
    list_payout = Payout.objects.annotate(
            status_priority=Case(
                When(status=False, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('status_priority', '-created_at')
    # paginator = Paginator(list_payout, 10)  # Show 10 items per page

    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    items = [model_to_dict(item) for item in list_payout]
    banks = Bank.objects.filter(status=True)

    return render(request, 'payout.html', {
        'list_payout': list_payout, 'items_json':items, 'bank_data':bank_data, 'banks':banks})

def search_payout(request):
    return render(request=request, template_name='payout_history.html')

@method_decorator(csrf_exempt, name='dispatch')
class AddPayoutView(View):
    def post(self, request, *args, **kwargs):
        decoded_str = request.body.decode('utf-8')
        data = json.loads(decoded_str)
        scode = data.get('scode')
        orderid = data.get('orderid')
        money = data.get('money')
        accountno = data.get('accountno')
        accountname = data.get('accountname')
        bankcode = data.get('bankcode')
        
        try:
            float(money)
        except Exception as ex:
            return JsonResponse({'status': 504, 'message': 'Định dạng tiền không hợp lệ'})
        
        if '.00' not in money:
            return JsonResponse({'status': 503, 'message': 'Số tiền phải có đuôi .00'})
        
        # Check if any bank_account with the same type is ON
        existed_bank_account = Payout.objects.filter(
            orderid=orderid).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Lệnh rút đã tồn tại. Vui lòng kiểm tra mã đơn hàng'})

        #Process the data and save to the database
    
        payout = Payout.objects.create(
            user=request.user,
            scode=scode,
            orderno=orderid,
            orderid=orderid,
            money=int(float(money)),
            accountno=accountno,
            accountname=accountname,
            bankname='',
            bankcode=bankcode,
            updated_by=None,
            is_auto=False,
            is_cancel=False,
            is_report=False,
            created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
        )
        payout.save()
        send_notification('New payout added. Please check and process')
        alert = (
            f'🔴 - THÔNG BÁO PAYOUT\n'
            f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
        )
        send_telegram_message(alert, os.environ.get('PENDING_PAYOUT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
        return JsonResponse({'status': 200, 'message': 'Bank added successfully'})


@csrf_exempt
@require_POST
def update_payout(request, update_type):
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        bank_id = data.get('bank_id')
        request_user_username = model_to_dict(request.user)['username']
        
        update_body = {
            'payout_id':payout_id,
            'bank_id':bank_id,
            'request_user_username':request_user_username,
            'update_type':update_type
        }
        update_payout_background.delay(update_body)
        
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@csrf_exempt 
def webhook(request):
    # {
    #     "scode": "CID16301",
    #     "orderno": "20240717144614RvKcA",
    #     "orderid": "2024071612295974620",
    #     "data": {
    #         "payeebankname": "ACB",
    #         "payeebankbranch": "",
    #         "payeebankbranchcode": "",
    #         "payeeaccountno": "111122223333",
    #         "payeeaccountname": "SHINO GE",
    #         "amount": "1000.00"
    #     },
    #     "sign": "d38737b767c04f0ca72138515ee7bfee"
    # }
    if request.method == 'POST':
        decoded_str = request.body.decode('utf-8')
        data = json.loads(decoded_str)
        scode = data.get('scode')
        orderno = data.get('orderno')
        orderid = data.get('orderid')
        money = data.get('data').get('amount')
        accountno = data.get('data').get('payeeaccountno')
        accountname = data.get('data').get('payeeaccountname')
        bankcode = data.get('data').get('payeebankbranchcode')
        payeebankname = data.get('data').get('payeebankname')
        payeebankbranch = data.get('data').get('payeebankbranch')
        body_sign = data.get('sign')
        
        
        sign_string = f"{scode}|{orderno}|{orderid}|{payeebankname}|{payeebankbranch}|{bankcode}|{accountno}|{accountname}|{money}:{key}"
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        
        if sign != body_sign:
            return JsonResponse({'status': 403, 'message': 'Forbidden'})
        
        try:
            float(money)
        except Exception as ex:
            return JsonResponse({'status': 504, 'message': 'Invalid amount'})
        
        if '.00' not in money:
            return JsonResponse({'status': 503, 'message': 'Amount must ends with .00'})
        
        existed_payout = Payout.objects.filter(
        orderid=orderid).first()
        if existed_payout:
            return JsonResponse({'status': 505, 'message': 'Payout existed'})
        
        # Gán payout ngẫu nhiên cho user theo ca làm
        current_time = datetime.now().time()
        user_timelines = []
        timelines = Timeline.objects.filter(status=True)
        for timeline in timelines:
            start_at = datetime.strptime(timeline.start_at, '%H:%M').time()
            end_at = datetime.strptime(timeline.end_at, '%H:%M').time()
            if start_at <= current_time and current_time <= end_at:
                user_timelines = list(UserTimeline.objects.filter(timeline=timeline, status=True))
                
        
        payout = Payout.objects.create(
                user=random.choice(user_timelines),
                scode=scode,
                orderno=orderno,
                orderid=orderid,
                money=int(float(money)),
                accountno=accountno,
                accountname=accountname,
                bankname='',
                bankcode=bankcode,
                updated_by=None,
                is_auto=True,
                is_cancel=False,
                is_report=False,
                created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
            )
        payout.save()
        send_notification('New payout added. Please check and process')
        alert = (
            f'🔴 - THÔNG BÁO PAYOUT\n'
            f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
        )
        send_telegram_message(alert, os.environ.get('PENDING_PAYOUT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
        return JsonResponse({'status': 200, 'message': 'Payout added successfully'})
    return JsonResponse({'status': 405, 'message': 'Method is not allowed'})

def find_bankcode(bank_name):
    pass
    
    