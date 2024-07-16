from django.shortcuts import render
from .models import Payout
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views import View
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
from django.db.models import Q, BooleanField, Case, Value, When, IntegerField
import pytz
import os
import json

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
            return JsonResponse({'status': 504, 'message': 'Invalid amount value'})
        
        if '.00' not in money:
            return JsonResponse({'status': 503, 'message': 'Amount must be end with .00'})
        
        # Check if any bank_account with the same type is ON
        existed_bank_account = Payout.objects.filter(
            orderid=orderid).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Existed payout. Please try again'})

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
    # if request.method == 'POST':
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        bank_id = data.get('bank_id')
        payout = get_object_or_404(Payout, id=payout_id)
        formatted_amount = '{:,.2f}'.format(payout.money)
        payout.updated_by = request.user
        payout.updated_at = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
        if update_type == 'done':
            payout.status = True
            bank = Bank.objects.filter(id=bank_id).first()
            payout.process_bank = bank
            alert = (
                f'🟢🟢🟢Success🟢🟢🟢\n'
                f'\n'
                f'Order ID: {payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} VND\n'
                f'\n'
                f'Bank name: {payout.bankcode}\n'
                f'\n'
                f'Account name: {payout.accountname}\n'
                f'\n'
                f'Account number: {payout.accountno}\n'
                f'\n'
                f'Process bank: {payout.process_bank.name}\n'
                f'\n'
                f'Created by: {payout.user}\n'
                f'\n'
                f'Done by: {request.user}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
            update_amount_by_date('OUT',payout.money)
        elif update_type == 'report':
            payout.is_report = True
            alert = (
                f'Hi team !\n'
                f'Please check this payout :\n'
                f'\n'
                f'Order ID: {payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} VND\n'
                f'\n'
                f'Bank name: {payout.bankcode}\n'
                f'\n'
                f'Account name: {payout.accountname}\n'
                f'\n'
                f'Account number: {payout.accountno}\n'
                f'\n'
                f'Reason: The receiving account information is incorrect!'
            )
            send_telegram_message(alert, os.environ.get('SUPPORT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
        elif update_type == 'cancel':
            payout.is_cancel = True
            payout.status = None
            alert = (
                f'🔴🔴🔴Failed🔴🔴🔴\n'
                f'\n'
                f'Order ID: {payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} VND\n'
                f'\n'
                f'Bank name: {payout.bankcode}\n'
                f'\n'
                f'Account name: {payout.accountname}\n'
                f'\n'
                f'Account number: {payout.accountno}\n'
                f'\n'
                f'Created by: {payout.user}\n'
                f'\n'
                f'Done by: {request.user}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
        else:
            return JsonResponse({'status': 422, 'message': 'Done','success': False})
        payout.save()
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@csrf_exempt 
def webhook(request):
    pass
    