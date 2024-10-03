from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.database import redis_connect
import time
from dotenv import load_dotenv
from worker.views import get_balance
from bank.utils import send_telegram_message
from datetime import datetime
import pytz
import os

load_dotenv()


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts
            # try:
                bank_accounts = BankAccount.objects.filter(bank_name=1,status=True)
                for bank in bank_accounts:
                    get_balance(bank=bank)
                time.sleep(15)
            # except Exception as ex:
            #     alert = (
            #         f'🔴 - SYSTEM ALERT\n'
            #         f'Fetch ACB bank info error: {str(ex)}\n'
            #         f'Date: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
            #     )
            #     send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))