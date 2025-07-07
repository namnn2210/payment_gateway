from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SettlePayout
from bank.models import Bank
from bank.utils import send_telegram_message, send_telegram_qr
from config.views import get_env
import json
from datetime import datetime
import pytz

class SettlePayoutListView(LoginRequiredMixin, ListView):
    model = SettlePayout
    template_name = 'settle_payout.html'
    context_object_name = 'list_payout'
    login_url = 'cms:user_login'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', 'Pending')

        if search_query:
            queryset = queryset.filter(
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
            queryset = queryset.filter(status=False, is_cancel=False)
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

        queryset = queryset.annotate(
            status_priority=Case(
                When(status=False, then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('status_priority', 'created_at')

        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, 'settle_payout_list.html', context)
        return super().render_to_response(context, **response_kwargs)

class AddSettlePayoutAPIView(APIView):
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

        if SettlePayout.objects.filter(orderid=orderid).exists():
            return Response({'message': 'Lệnh rút đã tồn tại. Vui lòng kiểm tra mã đơn hàng'}, status=status.HTTP_409_CONFLICT)

        payout = SettlePayout.objects.create(
            user=request.user,
            scode='CID1630' + scode,
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
        try:
            send_telegram_message(alert, get_env('PENDING_PAYOUT_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
        except Exception as e:
            print(str(e))

        return Response({'message': 'Bank added successfully'}, status=status.HTTP_201_CREATED)

class UpdateSettlePayoutAPIView(APIView):
    def post(self, request, update_type, *args, **kwargs):
        data = request.data
        payout_id = data.get('id')
        bank_id = data.get('bank_id', 0)
        reason = data.get('reason', 0)
        payout = get_object_or_404(SettlePayout, id=payout_id)

        formatted_amount = '{:,.2f}'.format(payout.money)
        payout.updated_by = request.user
        payout.updated_at = datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y-%m-%d %H:%M:%S')

        if update_type == 'done':
            payout.status = True
            bank = get_object_or_404(Bank, id=bank_id)
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
                f'\n'
                f'Description: {payout.memo}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            try:
                send_telegram_message(alert, get_env('PAYOUT_CHAT_ID'), get_env('TRANSACTION_BOT_2_API_KEY'))
            except Exception as e:
                print(str(e))
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
            except Exception as e:
                print(str(e))
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
            return Response({'message': 'Invalid update type', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

        payout.save()
        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class DeleteSettlePayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payout = get_object_or_404(SettlePayout, id=request.data.get('id'))
        payout.delete()
        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class EditSettlePayoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        payout = get_object_or_404(SettlePayout, id=data.get('id'))
        bank_code = data.get('bankCode')
        payout.bankcode = bank_code
        payout.save()

        caption = (
            f'{payout.scode}\n'
            f'{payout.orderid}\n'
            f'{payout.bankcode}\n'
            f'{payout.accountno}\n'
            f'{payout.accountname}\n'
            f'{int(float(payout.money)):,}\n'
            f'- - - - - - - - - - - - - -\n'
        )
        memo = 'TQ' + payout.orderno[-11:]
        img_url = f'https://img.vietqr.io/image/{payout.bankcode}-{payout.accountno}-compact.jpg?amount={int(float(payout.money))}&addInfo={memo}&accountName={payout.accountname}'
        send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002888070097', img_url, caption)

        return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)

class CheckSuccessSettleAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payout = get_object_or_404(SettlePayout, id=request.data.get('id'))
        if payout.status:
            return Response({'message': 'Done', 'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Failed', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)