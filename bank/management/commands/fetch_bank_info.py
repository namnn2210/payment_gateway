import json
import redis
from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.utils import get_bank_transaction_history, unix_to_datetime, send_telegram_message
from bank.database import redis_connect
from mb.views import mb_login, mb_transactions
import time
import pandas as pd
import os
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from worker.worker import get_balance

load_dotenv()


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        redis_client = redis_connect()
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(status=True)
            for bank in bank_accounts:
                get_balance.delay(bank=bank, redis=redis_client)
            redis_client.close()
            time.sleep(15)