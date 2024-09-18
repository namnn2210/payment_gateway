from django.shortcuts import render, get_object_or_404
from .models import Payout, Timeline, UserTimeline
from settle_payout.models import SettlePayout
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from bank.utils import send_telegram_message
from bank.models import Bank
from notification.views import send_notification
from dotenv import load_dotenv
from datetime import datetime, time
from django.db.models import Q, Case, Value, When, IntegerField, Sum
from partner.models import PartnerMapping, CID
from django.db.models.functions import TruncDate
from .tasks import update_payout_background
from django.utils.dateparse import parse_date
from employee.models import EmployeeWorkingSession
from django.utils import timezone

import pytz
import os
import json
import random
import hashlib

load_dotenv()

BANK_CODE_MAPPING = {
    'VTB':'ICB',
    'SCM':'STB',
    'VBARD':'VBA',
    'DAB':'DOB',
    'EXIM':'EIB'
}

# Create your views here.
@login_required(login_url='user_login')
def list_payout(request):
    bank_data = json.load(open('bank.json', encoding='utf-8'))
    banks = Bank.objects.filter(status=True)
    users = User.objects.all()
    list_payout = Payout.objects.all()
    status = None

    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'Pending')
    
    employee_filter = request.GET.get('employee')

    if search_query:
        list_payout = list_payout.filter(
            Q(scode__icontains=search_query) |
            Q(orderno__icontains=search_query) |
            Q(orderid__icontains=search_query) |
            Q(money__icontains=search_query) |
            Q(accountno__icontains=search_query) |
            Q(accountname__icontains=search_query) |
            Q(bankcode__icontains=search_query) |
            Q(process_bank__name__icontains=search_query)
        )

    if status_filter == 'Pending':
        status = False
    elif status_filter == 'Done':
        status = True

    if status is not None:
        list_payout = list_payout.filter(status=status, is_cancel=False)
    elif status_filter == 'Canceled':
        list_payout = list_payout.filter(is_cancel=True)
    elif status_filter == 'Reported':
        list_payout = list_payout.filter(is_report=True)
        
    

    today = timezone.now().date().strftime('%d/%m/%Y')

    start_datetime_str = request.GET.get('start_datetime', '')
    end_datetime_str = request.GET.get('end_datetime', '')

    if start_datetime_str:
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
    else:
        start_datetime = datetime.strptime(f'{today} 00:00', '%d/%m/%Y %H:%M')

    if end_datetime_str:
        end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
    else:
        end_datetime = datetime.strptime(f'{today} 23:59', '%d/%m/%Y %H:%M')

    list_payout = list_payout.filter(created_at__gte=start_datetime, created_at__lte=end_datetime)
    
    
    if not employee_filter:
        list_payout = list_payout.filter(user=request.user)
    else:
        if employee_filter != 'All':
            user = User.objects.filter(username=employee_filter).first()
            list_payout = list_payout.filter(user=user)

    list_payout = list_payout.annotate(
        status_priority=Case(
            When(status=False, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('status_priority', '-created_at')

    total_results = len(list_payout)
    total_amount = list_payout.aggregate(Sum('money'))['money__sum'] or 0
    
    print(list_payout)

    paginator = Paginator(list_payout, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'payout_list.html', {
            'list_payout': page_obj,
            'total_results': total_results,
            'total_amount': total_amount,
            'banks': banks,
            'bank_data': bank_data,
        })

    return render(request, 'payout.html', {
        'list_payout': page_obj,
        'bank_data': bank_data,
        'banks': banks,
        'total_results': total_results,
        'total_amount': total_amount,
        'users':users
    })

def search_payout(request):
    return render(request=request, template_name='payout_history.html')

@method_decorator(csrf_exempt, name='dispatch')
class AddPayoutView(View):
    def post(self, request, *args, **kwargs):
        decoded_str = request.body.decode('utf-8')
        data = json.loads(decoded_str)
        scode = data.get('scode').strip()
        orderid = data.get('orderid').strip()
        money = data.get('money')
        accountno = data.get('accountno').strip()
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
            scode='CID1630'+scode,
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
            created_at=timezone.now()
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
@require_POST
def delete_payout(request):
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        payout = get_object_or_404(Payout, id=payout_id)
        payout.delete()
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@csrf_exempt
@require_POST
def edit_payout(request):
    try:
        partner_bankcode = None
        data = json.loads(request.body)
        payout_id = data.get('id')
        bank_code = data.get('bankCode')
        payout = get_object_or_404(Payout, id=payout_id)
        system_bankcode = BANK_CODE_MAPPING.get(bank_code,'')
        partner_bank_data = json.load(open('partner_bank.json', encoding='utf-8'))['banks']
        if not system_bankcode:
            for bank in partner_bank_data:
                if bank['bankname'] == bank_code:
                    system_bankcode = bank['code']
                    partner_bankcode = bank['code']
            if not system_bankcode and not partner_bankcode:
                partner_bankcode = bank_code
                system_bankcode = bank_code
        else:
            partner_bankcode = bank_code
        payout.bankcode = bank_code
        payout.partner_bankcode = partner_bankcode
        payout.save()
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@csrf_exempt
@require_POST
def move_payout(request):
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        payout = get_object_or_404(Payout, id=payout_id)
        
        # Create settle payout from payout
        SettlePayout.objects.create(
            user=payout.user,
            did=payout.did,
            scode=payout.scode,
            orderno=payout.orderno,
            orderid=payout.orderid,
            money=payout.money,
            bankname=payout.bankname,
            accountno=payout.accountno,
            accountname=payout.accountname,
            bankcode=payout.bankcode,
            is_auto=payout.is_auto,
            is_cancel=payout.is_cancel,
            is_report=payout.is_report,
            process_bank=payout.process_bank,
            status=payout.status,
            updated_by=payout.updated_by,
            created_at=payout.created_at,
            updated_at=payout.updated_at,
        )
        
        # Delete payout
        payout.delete()
        return JsonResponse({'status': 200, 'message': 'Done','success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex),'success': False})
    
@csrf_exempt 
def webhook(request):
    if request.method == 'POST':
        
        partner_bank_data = json.load(open('partner_bank.json', encoding='utf-8'))['banks']
        system_bank_data = json.load(open('bank.json', encoding='utf-8'))
        
        decoded_str = request.body.decode('utf-8')
        data = json.loads(decoded_str)
        
        print('webhook request data: ', data)
        
        scode = data.get('scode')
        orderno = data.get('orderno')
        orderid = data.get('orderid')
        money = data.get('data').get('amount')
        accountno = data.get('data').get('payeeaccountno')
        accountname = data.get('data').get('payeeaccountname')
        bankcode = data.get('data').get('payeebankbranchcode','')
        payeebankname = data.get('data').get('payeebankname','')
        payeebankbranch = data.get('data').get('payeebankbranch','')
        body_sign = data.get('sign')
        
        cid = CID.objects.filter(name=scode).first()
        partner_mapping = PartnerMapping.objects.filter(cid=cid).first()
        
        key = partner_mapping.key
        
        
        sign_string = f"{scode}|{orderno}|{orderid}|{payeebankname}|{payeebankbranch}|{bankcode}|{accountno}|{accountname}|{money}:{key}"
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        
        if sign != body_sign:
            print('not match sign')
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
        
        current_sessions = EmployeeWorkingSession.objects.filter(status=False)
        current_working_user = []
        if len(current_sessions) != 0 :
            for session in current_sessions:
                current_working_user.append(session.user)
        else:
            admin_user = User.objects.filter(username='admin-huong').first()
            current_working_user.append(admin_user)
        
                
        system_bankcode = ''
        partner_bankcode = ''
        settle = False
        if bankcode == 'NA' or payeebankbranch == 'NA':
            settle = True
        elif bankcode == '' and payeebankbranch == '':
            settle = True
        # Get bank code
        # Format through bank code dict mapping
        if settle:
            print('settle')
            print(partner_bank_data)
            # Settle
            for bank in partner_bank_data:
                if payeebankname == bank['bankname']:
                    print('get bank code')
                    system_bankcode = bank['code']
                    # partner_bankcode = bank['code']

            admin = User.objects.filter(username="admin").first()
            existed_settle_payout = SettlePayout.objects.filter(orderid=orderid).first()
            if existed_settle_payout:
                return JsonResponse({'status': 505, 'message': 'Settle Payout existed'})
            settle_payout = SettlePayout.objects.create(
                    user=random.choice(current_working_user),
                    scode=scode,
                    orderno=orderno,
                    orderid=orderid,
                    money=int(float(money)),
                    accountno=accountno,
                    accountname=accountname,
                    bankname=payeebankname,
                    bankcode=system_bankcode,
                    # partner_bankcode=partner_bankcode,
                    updated_by=None,
                    is_auto=True,
                    is_cancel=False,
                    is_report=False,
                    created_at=timezone.now()
                )
            settle_payout.save()
            send_notification('New settle payout added. Please check and process')
            alert = (
                f'🔴 - THÔNG BÁO SETTLE PAYOUT\n'
                f'Đã có lệnh settle payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
            )
            send_telegram_message(alert, os.environ.get('PENDING_PAYOUT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))

        else:
            system_bankcode = BANK_CODE_MAPPING.get(bankcode,'')
            if not system_bankcode:
                for bank in partner_bank_data:
                    if bank['bankname'] == payeebankname:
                        system_bankcode = bank['code']
                        partner_bankcode = bank['code']
                if not system_bankcode and not partner_bankcode:
                    partner_bankcode = bankcode
                    system_bankcode = bankcode
            else:
                partner_bankcode = bankcode
        
            payout = Payout.objects.create(
                    user=random.choice(current_working_user),
                    scode=scode,
                    orderno=orderno,
                    orderid=orderid,
                    money=int(float(money)),
                    accountno=accountno,
                    accountname=accountname,
                    bankname=payeebankname,
                    bankcode=system_bankcode,
                    partner_bankcode=partner_bankcode,
                    updated_by=None,
                    is_auto=True,
                    is_cancel=False,
                    is_report=False,
                    created_at=timezone.now()
                )
            payout.save()
            send_notification('New payout added. Please check and process')
            alert = (
                f'🔴 - THÔNG BÁO PAYOUT\n'
                f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
            )
            send_telegram_message(alert, os.environ.get('PENDING_PAYOUT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
        return HttpResponse('success')
    
    
