import json
import redis
from django.core.management.base import BaseCommand
from bank.models import BankAccount
from bank.utils import get_acb_bank_transaction_history, unix_to_datetime, send_telegram_message
from bank.database import redis_connect
import time
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        redis_client = redis_connect()
        columns_to_convert = ['posting_date', 'active_datetime', 'effective_date']
        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(status=True)
            for bank in bank_accounts:
                bank_exists = redis_client.get(bank.account_number)
                new_bank_history = get_acb_bank_transaction_history(bank)
                new_bank_history_df = pd.DataFrame(new_bank_history)
                if new_bank_history_df.empty:
                    continue
                # Convert Unix timestamp to datetime and replace nan values
                new_bank_history_df[columns_to_convert] = new_bank_history_df[columns_to_convert].apply(unix_to_datetime, axis=1)
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
                            if row['type'] == 'IN':
                                transaction_type = '+'
                                transaction_color = '🟢'  # Green circle emoji for IN transactions
                            else:
                                transaction_type = '-'
                                transaction_color = '🔴'  # Red circle emoji for OUT transactions

                            formatted_amount = '{:,.2f}'.format(row['amount'])
                            alert = (
                                f'🏦 {bank.account_number} - {bank.account_name}\n'
                                f'📝 {row["description"]}\n'
                                f'💰 {transaction_color} {transaction_type}{formatted_amount} VND\n'
                                f'🔍 {row["type"]}\n'
                                f'🕒 {row["active_datetime"]}'
                            )
                            send_telegram_message(alert)
                        redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
                        print('Update for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    else:
                        print('No new data for bank: %s - %s. Updated at %s' % (bank.account_number, bank.bank_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            redis_client.close()
            time.sleep(15)