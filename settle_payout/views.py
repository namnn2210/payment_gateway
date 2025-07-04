from django.shortcuts import render
from .models import SettlePayout
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from bank.utils import send_telegram_message
from bank.models import Bank
from datetime import datetime
from django.db.models import Q, Case, Value, When, IntegerField, Sum
from django.utils import timezone
from config.views import get_env

import pytz
import json


# Create your views here.
@login_required(login_url='user_login')
def list_settle_payout(request):
    bank_data = json.load(open('bank.json', encoding='utf-8'))
    banks = Bank.objects.filter(status=True)
    list_payout = SettlePayout.objects.all()
    status = None

    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'Pending')

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

    list_payout = list_payout.annotate(
        status_priority=Case(
            When(status=False, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('status_priority', 'created_at')

    total_results = len(list_payout)
    total_amount = list_payout.aggregate(Sum('money'))['money__sum'] or 0

    paginator = Paginator(list_payout, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'settle_payout_list.html', {
            'list_payout': page_obj,
            'total_results': total_results,
            'total_amount': total_amount,
            'banks': banks,
            'bank_data': bank_data,
        })

    return render(request, 'settle_payout.html', {
        'list_payout': page_obj,
        'bank_data': bank_data,
        'banks': banks,
        'total_results': total_results,
        'total_amount': total_amount
    })


@method_decorator(csrf_exempt, name='dispatch')
class AddSettlePayoutView(View):
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
        existed_bank_account = SettlePayout.objects.filter(
            orderid=orderid).first()
        if existed_bank_account:
            return JsonResponse({'status': 505, 'message': 'Lệnh rút đã tồn tại. Vui lòng kiểm tra mã đơn hàng'})

        # Process the data and save to the database

        payout = SettlePayout.objects.create(
            user=request.user,
            scode='CID1630' + scode,
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
        alert = (
            f'🔴 - THÔNG BÁO PAYOUT\n'
            f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
        )
        try:
            send_telegram_message(alert, get_env('PENDING_PAYOUT_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
        except Exception as ex:
            print(str(ex))
        return JsonResponse({'status': 200, 'message': 'Bank added successfully'})


@csrf_exempt
@require_POST
def delete_settle_payout(request):
    try:
        data = json.loads(request.body)
        settle_payout_id = data.get('id')
        settle_payout = get_object_or_404(SettlePayout, id=settle_payout_id)
        settle_payout.delete()
        return JsonResponse({'status': 200, 'message': 'Done', 'success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex), 'success': False})


@csrf_exempt
@require_POST
def edit_settle_payout(request):
    try:
        data = json.loads(request.body)
        settle_payout_id = data.get('id')
        bank_code = data.get('bankCode')
        settle_payout = get_object_or_404(SettlePayout, id=settle_payout_id)
        settle_payout.bankcode = bank_code
        settle_payout.save()
        return JsonResponse({'status': 200, 'message': 'Done', 'success': True})
    except Exception as ex:
        return JsonResponse({'status': 500, 'message': str(ex), 'success': False})


@csrf_exempt
@require_POST
def check_success_settle(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payout_id = data.get('id')
        payout = get_object_or_404(SettlePayout, id=payout_id)
        if payout.status:
            return JsonResponse({'status': 200, 'message': 'Done', 'success': True})
        else:
            return JsonResponse({'status': 500, 'message': 'Failed', 'success': False})


@csrf_exempt
@require_POST
def update_settle_payout(request, update_type):
    try:
        data = json.loads(request.body)
        payout_id = data.get('id')
        bank_id = data.get('bank_id', 0)
        reason = data.get('reason', 0)
        payout = SettlePayout.objects.filter(id=payout_id).first()

        formatted_amount = '{:,.2f}'.format(payout.money)
        payout.updated_by = request.user
        payout.updated_at = datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y-%m-%d %H:%M:%S')
        if update_type == 'done':
            payout.status = True
            payout.save()
            bank = Bank.objects.filter(id=bank_id).first()
            # Show how much success payout by this account
            # start_of_day = datetime.now(pytz.timezone('Asia/Singapore')).replace(hour=0, minute=0, second=0,
            #                                                                      microsecond=0)
            # total_money = SettlePayout.objects.filter(
            #     user=payout.user,
            #     created_at__gte=start_of_day
            # ).aggregate(total=Sum('money'))
            # print(total_money)
            payout.process_bank = bank
            alert = (
                f'🟢🟢🟢{payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} \n'
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
                # f'\n'
                # f'Total success today: {'{:,.2f}'.format(total_money)}\n'
                # f'\n'
                f'\n'
                f'Description: {payout.memo}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            try:
                send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_2_API_KEY'))
            except Exception as ex:
                print(str(ex))
        elif update_type == 'report':
            payout.is_report = True
            reason_text = ''
            if reason == 1:
                reason_text = 'Invalid receiving account number!'
            elif reason == 2:
                reason_text = 'Invalid receiving bank!'
            elif reason == 3:
                reason_text = 'Invalid receiving account name!'
            alert = (
                f'Hi team !\n'
                f'Please check this payout :\n'
                f'\n'
                f'Order ID: {payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} \n'
                f'\n'
                f'Bank name: {payout.bankcode}\n'
                f'\n'
                f'Account name: {payout.accountname}\n'
                f'\n'
                f'Account number: {payout.accountno}\n'
                f'\n'
                f'Reason: {reason_text}'
            )
            try:
                send_telegram_message(alert, get_env('SUPPORT_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
            except Exception as ex:
                print(str(ex))
        elif update_type == 'cancel':
            payout.is_cancel = True
            payout.status = False
            alert = (
                f'🔴🔴🔴Failed🔴🔴🔴\n'
                f'\n'
                f'Order ID: {payout.orderid}\n'
                f'\n'
                f'Amount: {formatted_amount} \n'
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
            send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_2_API_KEY'))
        else:
            return JsonResponse({'status': 422, 'message': 'Done', 'success': False})
        payout.save()
        return JsonResponse({'status': 200, 'message': 'Done', 'success': True})
    except Exception as ex:
        print(str(ex))
        return JsonResponse({'status': 500, 'message': str(ex), 'success': False})
