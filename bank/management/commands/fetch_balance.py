import json
import redis
from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.utils import get_bank_balance, send_telegram_message
import time
import os
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = 'Update all bank balance to mysql'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(status=True)
            for bank in bank_accounts:
                bank_account = get_bank_balance(bank.account_number, bank.username, bank.password, bank.bank_name)
                if bank_account:
                    if bank.balance != bank_account.get('balance'):
                        bank.balance = bank_account.get('balance')
                        bank.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        bank.save()
                        print('Update for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    else:
                        print('No new data for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Get transaction history from {bank.account_number} - {bank.bank_name} empty\n'
                        f'Date: {datetime.now()}'
                    )
                    send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
                    continue
            time.sleep(15)