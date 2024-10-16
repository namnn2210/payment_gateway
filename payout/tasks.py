from celery import shared_task
from datetime import datetime
from bank.utils import send_telegram_message
from django.shortcuts import get_object_or_404
from bank.views import update_amount_by_date
from bank.models import Bank
from partner.views import update_status_request
from django.contrib.auth.models import User
from payout.models import Payout
import pytz
import os

@shared_task
def update_payout_background(update_body):
    payout_id = update_body['payout_id']
    bank_id = update_body['bank_id']
    update_type = update_body['update_type']
    reason = update_body['reason']
    payout = get_object_or_404(Payout, id=payout_id)
    formatted_amount = '{:,.2f}'.format(payout.money)
    request_user = User.objects.filter(username=update_body['request_user_username']).first()
    payout.updated_by = request_user
    payout.updated_at = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
    # payout.status = True
    bank = Bank.objects.filter(id=bank_id).first()
    payout.process_bank = bank
    formatted_amount = '{:,.2f}'.format(payout.money)
    if  update_type == 'done':
        if payout.is_auto:
            if update_status_request(payout=payout, status='S'):
                payout.status = True
                payout.save()
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
                    f'Done by: {request_user}\n'
                    f'\n'
                    f'Date: {payout.updated_at}'
                )
                send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
                update_amount_by_date('OUT',payout.money)

        else:
            payout.status = True
            payout.save()
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
                f'Done by: {request_user}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
            update_amount_by_date('OUT',payout.money)

    elif update_type == 'report':
        payout.is_report = True
        payout.save()
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
        send_telegram_message(alert, os.environ.get('SUPPORT_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
    elif update_type == 'cancel':
        payout.is_cancel = True
        payout.status = None
        if payout.is_auto:
            if update_status_request(payout=payout, status='F'):
                payout.save()
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
                    f'Done by: {request_user}\n'
                    f'\n'
                    f'Date: {payout.updated_at}'
                )
                send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
        else:
            payout.save()
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
                f'Done by: {request_user}\n'
                f'\n'
                f'Date: {payout.updated_at}'
            )
            send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))

