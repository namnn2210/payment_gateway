from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.database import redis_connect
import time
from dotenv import load_dotenv
from worker.views import get_balance

load_dotenv()


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        redis_client = redis_connect()
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(status=True)
            for bank in bank_accounts:
                get_balance(bank=bank)
            redis_client.close()
            time.sleep(30)