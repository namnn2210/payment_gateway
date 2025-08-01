from django.core.management.base import BaseCommand
from bank.models import BankAccount
from worker.views import get_balance
from bank.utils import send_telegram_message
from datetime import datetime
from config.views import get_env
import pytz
import time


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(bank_name=2, status=True)
            for bank in bank_accounts:
                get_balance(bank=bank)
            time.sleep(15)
