from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payout
from settle_payout.models import SettlePayout
from bank.models import Bank
from partner.models import CID
from employee.models import EmployeeWorkingSession
from .tasks import update_payout_background
from bank.utils import send_telegram_message, send_telegram_qr
from config.views import get_env
import json
import random
import hashlib
import requests
from datetime import datetime

BANK_CODE_MAPPING = {
    'VTB': 'ICB',
    'SCM': 'STB',
    'VBARD': 'VBA',
    'DAB': 'DOB',
    'EXIM': 'EIB'
}

class PayoutListView(LoginRequiredMixin, ListView):
    model = Payout
    template_name = 'payout.html'
    context_object_name = 'list_payout'
    login_url = 'user_login'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', 'Pending')
        employee_filter = self.request.GET.get('employee')

        if search_query:
            queryset = queryset.filter(
                Q(scode__icontains=search_query) |
                Q(orderno__icontains=search_query) |
                Q(orderid__icontains=search_query) |
                Q(money__icontains=search_query) |
                Q(accountno__icontains=search_query) |
                Q(accountname__icontains=search_query) |
                Q(bankcode__icontains=search_query) |
                Q(process_bank__name__icontains=search_query) |
                Q(memo__icontains=search_query)
            )

        if status_filter == 'Pending':
            queryset = queryset.filter(status=False, is_cancel=False, is_report=False)
        elif status_filter == 'Done':
            queryset = queryset.filter(status=True)
        elif status_filter == 'Canceled':
            queryset = queryset.filter(is_cancel=True)
        elif status_filter == 'Reported':
            queryset = queryset.filter(is_report=True)

        today = timezone.now().date().strftime('%d/%m/%Y')
        start_datetime_str = self.request.GET.get('start_datetime', '')
        end_datetime_str = self.request.GET.get('end_datetime', '')

        if start_datetime_str:
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
        else:
            start_datetime = datetime.strptime(f'{today} 00:00', '%d/%m/%Y %H:%M')

        if end_datetime_str:
            end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
        else:
            end_datetime = datetime.strptime(f'{today} 23:59', '%d/%m/%Y %H:%M')

        queryset = queryset.filter(created_at__gte=start_datetime, created_at__lte=end_datetime)

        if not employee_filter or employee_filter == 'All':
            pass
        else:
            user = User.objects.filter(username=employee_filter).first()
            queryset = queryset.filter(user=user)

        queryset = queryset.annotate(
            status_priority=Case(
                When(status=False, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('status_priority', 'created_at')

        for payout in queryset:
            payout.memo = payout.accountname.split(' ')[-1] + ' ' + 'Z' + payout.orderno[-11:]

        print(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_data'] = json.load(open('bank.json', encoding='utf-8'))
        context['banks'] = Bank.objects.filter(status=True)
        context['users'] = User.objects.all()
        context['total_results'] = self.get_queryset().count()
        context['total_amount'] = self.get_queryset().aggregate(Sum('money'))['money__sum'] or 0
        return context

class AddPayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        scode = data.get('scode', '').strip()
        orderid = data.get('orderid', '').strip()
        money = data.get('money', '')
        accountno = data.get('accountno', '').strip()
        accountname = data.get('accountname', '')
        bankcode = data.get('bankcode', '')

        try:
            money_float = float(money)
        except ValueError:
            return Response({'message': 'Định dạng tiền không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        if '.00' not in money:
            return Response({'message': 'Số tiền phải có đuôi .00'}, status=status.HTTP_400_BAD_REQUEST)

        if Payout.objects.filter(orderid=orderid).exists():
            return Response({'message': 'Lệnh rút đã tồn tại. Vui lòng kiểm tra mã đơn hàng'}, status=status.HTTP_409_CONFLICT)

        payout = Payout.objects.create(
            user=request.user,
            scode='CID1910' + scode,
            orderno=orderid,
            orderid=orderid,
            money=int(money_float),
            accountno=accountno,
            accountname=accountname,
            bankname='',
            bankcode=bankcode,
            created_at=timezone.now()
        )

        alert = (
            f'🔴 - THÔNG BÁO PAYOUT\n'
            f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!'
        )
        caption = (
            f'{scode}\n'
            f'{orderid}\n'
            f'{bankcode}\n'
            f'{accountno}\n'
            f'{accountname}\n'
            f'{int(money_float)}\n'
            f'- - - - - - - - - - - - - -\n'
        )
        memo = 'TQ' + orderid[-11:]
        send_telegram_message(alert, get_env('PENDING_PAYOUT_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
        img_url = f'https://img.vietqr.io/image/{bankcode}-{accountno}-compact.jpg?amount={int(money_float)}&addInfo={memo}&accountName={accountname}'
        send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002287492730', img_url, caption)

        return Response({'message': 'Bank added successfully'}, status=status.HTTP_201_CREATED)

class UpdatePayoutAPIView(APIView):
    def post(self, request, update_type, *args, **kwargs):
        data = request.data
        payout_id = data.get('id')
        bank_id = data.get('bank_id')
        reason = data.get('reason', 1)

        update_body = {
            'payout_id': payout_id,
            'bank_id': bank_id,
            'request_user_username': request.user.username,
            'update_type': update_type,
            'reason': int(reason)
        }

        update_success = update_payout_background(update_body)

        if update_success:
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Update payout failed', 'success': False}, status=status.HTTP_410_GONE)

class DeletePayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payout = get_object_or_404(Payout, id=request.data.get('id'))
        payout.delete()
        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class EditPayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        payout = get_object_or_404(Payout, id=data.get('id'))
        bank_code = data.get('bankCode')

        system_bankcode = BANK_CODE_MAPPING.get(bank_code, '')
        partner_bank_data = json.load(open('partner_bank.json', encoding='utf-8'))['banks']
        partner_bankcode = bank_code

        if not system_bankcode:
            for bank in partner_bank_data:
                if bank['bankname'] == bank_code:
                    system_bankcode = bank['code']
                    break
            if not system_bankcode:
                system_bankcode = bank_code

        payout.bankcode = bank_code
        payout.partner_bankcode = partner_bankcode
        payout.save()

        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class MovePayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payout = get_object_or_404(Payout, id=request.data.get('id'))

        SettlePayout.objects.create(
            user=payout.user,
            did=payout.did,
            scode=payout.scode,
            orderno=payout.orderno,
            orderid=payout.orderid,
            money=payout.money,
            bankname=payout.bankname,
            accountno=payout.accountno,
            memo=payout.memo,
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

        payout.delete()
        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class CheckSuccessPayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payout = get_object_or_404(Payout, id=request.data.get('id'))
        if payout.staging_status:
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Failed', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PayoutWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data
        scode = data.get('scode')
        orderno = data.get('orderno')
        orderid = data.get('orderid')
        money = data.get('data', {}).get('amount')
        accountno = data.get('data', {}).get('payeeaccountno')
        accountname = data.get('data', {}).get('payeeaccountname')
        bankcode = data.get('data', {}).get('payeebankbranchcode', '')
        payeebankname = data.get('data', {}).get('payeebankname', '')
        payeebankbranch = data.get('data', {}).get('payeebankbranch', '')
        body_sign = data.get('sign')

        system_bankcode = ''
        partner_bankcode = ''

        cid = CID.objects.filter(name=scode).first()
        if not cid:
            return Response({'message': 'Invalid scode'}, status=status.HTTP_400_BAD_REQUEST)

        key = cid.key
        sign_string = f"{scode}|{orderno}|{orderid}|{payeebankname}|{payeebankbranch}|{bankcode}|{accountno}|{accountname}|{money}:{key}"
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()

        if sign != body_sign:
            return Response({'message': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        try:
            money_float = float(money)
        except (ValueError, TypeError):
            return Response({'message': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        if Payout.objects.filter(orderid=orderid).exists() or SettlePayout.objects.filter(orderid=orderid).exists():
            return HttpResponse("existed", content_type="text/plain")
            
        current_sessions = EmployeeWorkingSession.objects.filter(status=False)
        current_working_user = [session.user for session in current_sessions] if current_sessions else [User.objects.filter(username='admin-tqa').first()]

        settle = bankcode in ['NA', '', '-'] or payeebankbranch in ['NA', '', '-']

        partner_bank_data = json.load(open('partner_bank.json', encoding='utf-8'))['banks']
        if settle:
            # print('settle')
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
            memo = 'TQ' + orderno[-11:]
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
                memo=memo,
                # partner_bankcode=partner_bankcode,
                updated_by=None,
                is_auto=True,
                is_cancel=False,
                is_report=False,
                created_at=timezone.now()
            )
            settle_payout.save()
            alert = (
                f'🔴 - THÔNG BÁO SETTLE PAYOUT\n'
                f'Đã có lệnh settle payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
            )
            caption = (
                f'{scode}\n'
                f'{orderid}\n'
                f'{system_bankcode}\n'
                f'{accountno}\n'
                f'{accountname}\n'
                f'{int(float(money)):,}\n'
                f'- - - - - - - - - - - - - -\n'
            )
            memo = 'TQ' + orderno[-11:]
            img_url = f'https://img.vietqr.io/image/{system_bankcode}-{accountno}-compact.jpg?amount={int(float(money))}&addInfo={memo}&accountName={accountname}'
            send_telegram_message(alert, get_env('PENDING_PAYOUT_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
            send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002888070097', img_url, caption)
        else:
            system_bankcode = BANK_CODE_MAPPING.get(bankcode, '')
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

            memo = 'TQ' + orderno[-11:]

            payout = Payout.objects.create(
                user=random.choice(current_working_user),
                scode=scode,
                orderno=orderno,
                orderid=orderid,
                money=int(float(money)),
                accountno=accountno,
                accountname=accountname,
                bankname=payeebankname,
                memo=memo,
                bankcode=system_bankcode,
                partner_bankcode=partner_bankcode,
                updated_by=None,
                is_auto=True,
                is_cancel=False,
                is_report=False,
                created_at=timezone.now()
            )
            payout.save()
            alert = (
                f'🔴 - THÔNG BÁO PAYOUT\n'
                f'Đã có lệnh payout mới. Vui lòng kiểm tra và hoàn thành !!"\n'
            )

            caption = (
                f'{scode}\n'
                f'{orderid}\n'
                f'{system_bankcode}\n'
                f'{accountno}\n'
                f'{accountname}\n'
                f'{int(float(money)):,}\n'
                f'- - - - - - - - - - - - - -\n'
            )
            img_url = f'https://img.vietqr.io/image/{system_bankcode}-{accountno}-compact.jpg?amount={int(float(money))}&addInfo={memo}&accountName={accountname}'
            send_telegram_message(alert, get_env('PENDING_PAYOUT_CHAT_ID'),
                                  get_env('MONITORING_BOT_2_API_KEY'))
            send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002287492730', img_url, caption)

        return HttpResponse("success", content_type="text/plain")

class TelegramWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data
        if 'callback_query' in data:
            callback = data['callback_query']
            message = callback['message']
            chat_id = message['chat']['id']
            message_id = message['message_id']
            callback_data = callback['data']
            callback_id = callback['id']
            username = callback['from']['username']

            bot_token = get_env('MONITORING_BOT_2_API_KEY')

            requests.post(f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery', data={'callback_query_id': callback_id})
            requests.post(f'https://api.telegram.org/bot{bot_token}/deleteMessage', data={'chat_id': chat_id, 'message_id': message_id})

            if callback_data in ['remove_success', 'remove_failed']:
                old_caption = message.get('caption', '')
                suffix = "✅" if callback_data == 'remove_success' else "❌"
                final_caption = old_caption + '\n' + suffix + timezone.now().strftime("%d-%m-%Y %H:%M:%S") + '\n' + '@' + username
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data={'chat_id': chat_id, 'text': final_caption, 'parse_mode': 'HTML'})

        return Response({"status": "ok"}, status=status.HTTP_200_OK)