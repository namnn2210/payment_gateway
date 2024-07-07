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

load_dotenv()


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'
    
    def find_substring(self, text):
        # Regex pattern to find a substring starting with 'Z' and having 7 characters
        pattern = r'Z.{6}'
        match = re.search(pattern, text)
        if match:
            return match.group()
        else:
            return None

    def handle(self, *args, **kwargs):
        redis_client = redis_connect()
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(status=True)
            for bank in bank_accounts:
                error_count = 0
                bank_exists = redis_client.get(bank.account_number)
                print(bank.account_name, bank.account_number, bank.bank_name.name, bank.username, bank.password)
                if bank.bank_name.name == 'MB':
                    transactions = mb_transactions(bank.username, bank.password, bank.account_number)
                    while transactions is None:
                        error_count += 1
                        print('Retry logging in: ', error_count)
                        if error_count > 3:
                            break
                        mb_logged_in = mb_login(bank.username, bank.password, bank.account_number)
                        if mb_logged_in:
                            transactions = mb_transactions(bank.username, bank.password, bank.account_number)
                    new_bank_history = transactions
                if bank.bank_name.name == 'ACB':
                    new_bank_history = get_bank_transaction_history(bank)
                new_bank_history_df = pd.DataFrame(new_bank_history)
                if new_bank_history_df.empty:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Get transaction history from {bank.account_number} - {bank.bank_name} empty\n'
                        f'Date: {datetime.now()}'
                    )
                    send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
                    continue
                # Convert Unix timestamp to datetime and replace nan values
                # if bank.bank_name.name == 'ACB':
                #     new_bank_history_df[columns_to_convert] = new_bank_history_df[columns_to_convert].apply(unix_to_datetime, axis=1)
                final_new_bank_history_df = new_bank_history_df.fillna('')
                if not bank_exists:
                    redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
                else:
                    # Get data from redis by key, load data as json and convert to dataframe, compare with final_new_bank_history_df, if differences is found, update redis
                    old_bank_history = json.loads(redis_client.get(bank.account_number))
                    old_bank_history_df = pd.DataFrame(old_bank_history)
                    # Compare 2 dataframes using equals
                    differences = old_bank_history_df.equals(final_new_bank_history_df)
                    if not differences:
                        diff = old_bank_history_df.merge(final_new_bank_history_df, how='outer', indicator=True)
                        unique_rows_new = diff[diff['_merge'] == 'right_only'].drop(columns=['_merge'])
                        
                        for _, row in unique_rows_new.iterrows():
                            if row['transaction_type'] == 'IN':
                                transaction_type = '+'
                                transaction_color = '🟢'  # Green circle emoji for IN transactions
                                formatted_amount = '{:,.2f}'.format(row['amount'])
                                alert = (
                                    f'Hi,\n'
                                    f'\n'
                                    f'Account: {row['account_number']}'
                                    f'\n'
                                    f'Confirmed by order: {row['transaction_number']}\n'
                                    f'\n'
                                    f'Received amount💲: {formatted_amount} VND\n'
                                    f'\n'
                                    f'Memo: {row['description']}\n'
                                    f'\n'
                                    f'Code: {self.find_substring(row['description'])}\n'
                                    f'\n'
                                    f'Time: {row["transaction_date"]}\n'
                                    f'\n'
                                    f'Reason of not be credited: Order not found!!!'
                                )
                                send_telegram_message(alert, os.environ.get('TRANSACTION_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
                            else:
                                transaction_type = '-'
                                transaction_color = '🔴'  # Red circle emoji for OUT transactions
                                formatted_amount = '{:,.2f}'.format(row['amount'])
                                alert = (
                                    f'🏦 {bank.account_number} - {bank.account_name}\n'
                                    f'📝 {row["description"]}\n'
                                    f'💰 {transaction_color} {transaction_type}{formatted_amount} VND\n'
                                    f'🔍 {row["transaction_type"]}\n'
                                    f'🕒 {row["transaction_date"]}'
                                )
                                send_telegram_message(alert, os.environ.get('BANK_OUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
                            
                        redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
                        print('Update for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    else:
                        print('No new data for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            redis_client.close()
            time.sleep(15)