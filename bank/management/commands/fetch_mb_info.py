from django.core.management.base import BaseCommand
from bank.models import BankAccount
from worker.views import get_balance
from bank.utils import send_telegram_message
from datetime import datetime
from config.views import get_env
import time
import pytz



class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts

                bank_accounts = BankAccount.objects.filter(bank_name=2,status=True)
                for bank in bank_accounts:
                    try:
                        get_balance(bank=bank)
                    except Exception as ex:
                        alert = (
                            f'🔴 - SYSTEM ALERT\n'
                            f'Fetch MB bank info error: {str(ex)}\n'
                            f'Date: {datetime.now(pytz.timezone('Asia/Singapore'))}'
                        )
                        try:
                            send_telegram_message(alert, get_env('MONITORING_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
                        except Exception as ex:
                            print(str(ex))
                time.sleep(45)
