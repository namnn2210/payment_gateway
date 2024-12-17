from django.core.management.base import BaseCommand
from bank.models import BankAccount
import time
from config.views import get_env
from worker.views import get_balance
from bank.utils import send_telegram_message
from datetime import datetime, timedelta
from tech.views import tech_login
import pytz



class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(bank_name=3,status=True)
            for bank in bank_accounts:
                try:
                    if bank.bank_name.name == "Techcombank":
                        six_hours_ago = datetime.now(pytz.timezone('Asia/Bangkok')) - timedelta(hours=6)
                        if bank.last_logged_in is None or bank.last_logged_in >= six_hours_ago:
                            tech_success = tech_login(bank.username, bank.password)
                            if tech_success:
                                print('Logged in as Techcombank successfully')
                                bank.updated_at = datetime.now(pytz.timezone('Asia/Bangkok'))
                                bank.save()
                    get_balance(bank=bank)
                except Exception as ex:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Fetch Techcombank bank info error: {str(ex)}\n'
                        f'Date: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
                    )
                    send_telegram_message(alert, get_env('MONITORING_CHAT_ID'),
                                          get_env('MONITORING_BOT_API_KEY'))
            time.sleep(15)
