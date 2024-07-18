from celery import shared_task
from datetime import datetime
from bank.utils import send_telegram_message
from bank.views import update_amount_by_date
from payout.models import Payout
import pytz
import os

@shared_task
def update_payout_background(payout, bank, user):
    print('aaaaaa')
    formatted_amount = '{:,.2f}'.format(payout['money'])
    print
    alert = (
        f'🟢🟢🟢Success🟢🟢🟢\n'
        f'\n'
        f'Order ID: {payout['orderid']}\n'
        f'\n'
        f'Amount: {formatted_amount} VND\n'
        f'\n'
        f'Bank name: {payout['bankcode']}\n'
        f'\n'
        f'Account name: {payout['accountname']}\n'
        f'\n'
        f'Account number: {payout['accountno']}\n'
        f'\n'
        f'Process bank: {bank['name']}\n'
        f'\n'
        # f'Created by: {payout['user_id']}\n'
        f'\n'
        f'Done by: {user['username']}\n'
        f'\n'
        f'Date: {payout['updated_at']}'
    )
    send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
    update_amount_by_date('OUT',payout['money'])
    payout_model = Payout(**payout)
    payout_model.save()

@shared_task
def print_current_time():
    tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(tz)
    print(f'Current time in UTC+7: {current_time}')
