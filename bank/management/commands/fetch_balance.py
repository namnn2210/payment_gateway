import json
import redis
from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.utils import get_bank_balance, send_telegram_message
from mb.views import mb_balance, mb_login
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
                error_count = 0
                print(bank.username, bank.password, bank.bank_name, bank.account_number)      
                if bank.bank_name.name == 'MB':
                    balance = mb_balance(bank.username, bank.password, bank.account_number)
                    while balance is not None:
                        error_count += 1
                        if error_count > 3:
                            break
                        mb_logged_in = mb_login(bank.username, bank.password, bank.account_number)
                        if mb_logged_in:
                            print('MB logged in..')
                            balance = mb_balance(bank.username, bank.password, bank.account_number)
                    if balance == bank.balance:
                        print('No new data for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                        continue
                    if balance != 0 and balance != bank.balance:
                        print('new balance: ', balance)
                        bank.balance = balance
                        bank.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        bank.save()
                        print('Update for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    else:
                        alert = (
                            f'🔴 - SYSTEM ALERT\n'
                            f'Get balance from {bank.account_number} - {bank.bank_name} 0\n'
                            f'Date: {datetime.now()}'
                        )
                        send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
                        continue
            time.sleep(15)