from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import json
import pandas as pd
import os
import time
from bank.database import redis_connect
from bank.utils import send_telegram_message
from django.utils import timezone
from bank.views import get_all_transactions

load_dotenv()
class Command(BaseCommand):
    help = 'Get report'

    def handle(self, *args, **kwargs):
        while True:
            redis_client = redis_connect(3)
            today_str = timezone.now().strftime('%Y-%m-%d')
            a = redis_client.get(today_str)
            if a:
                current_totals = json.loads(a)
                total_amount_payout_settle = current_totals['out']
            else:
                total_amount_payout_settle = 0

            all_transactions_df = get_all_transactions()
            all_transactions_df['transaction_date'] = pd.to_datetime(all_transactions_df['transaction_date'],
                                                                     format='%d/%m/%Y %H:%M:%S')

            # Get OUT transactions today
            today = timezone.now().date()

            # Filter the DataFrame for "OUT" transactions that occurred today
            out_transactions_today_df = all_transactions_df[
                (all_transactions_df['transaction_type'] == 'OUT') &
                (all_transactions_df['transaction_date'].dt.date == today) &
                (all_transactions_df['status'] == 'Success')  # Assuming 'SUCCESS' indicates successful transactions
                ]

            total_out_today = out_transactions_today_df['amount'].sum() or 0

            print(total_amount_payout_settle, total_out_today)

            alert = (
                f'Cập nhật: {today}\n'
                f'\n'
                f'Tổng khối lượng lệnh payout: {'{:,.2f}'.format(total_amount_payout_settle)}\n'
                f'\n'
                f'Tổng khối lượng lệnh giao dịch out: {'{:,.2f}'.format(total_out_today)}\n'
                f'\n'
            )
            send_telegram_message(alert, os.environ.get('REPORT_CHAT_ID'),
                                  os.environ.get('226PAY_BOT'))

            time.sleep(3600)







