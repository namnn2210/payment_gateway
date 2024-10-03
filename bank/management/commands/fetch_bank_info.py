from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import json
from bank.database import redis_connect
from bank.views import BankAccount
from partner.models import CID
from partner.views import create_deposit_order
from bank.utils import send_telegram_message, find_substring
from bank.views import update_amount_by_date, update_transaction_history_status
import os
import pandas as pd
load_dotenv()


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        redis_client = redis_connect(1)
        value = redis_client.get('5410118608842').decode('utf-8')
        value_json = json.loads(value)
        df = pd.DataFrame(value_json)
        # get transactions on 2024-10-02
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d/%m/%Y %H:%M:%S')

        # Filtering transactions for October 2nd, 2024
        start_date = pd.to_datetime('2024-10-02 00:00:00')
        end_date = pd.to_datetime('2024-10-02 23:59:59')

        # Filtering transactions for October 2nd, 2024 between 00:00:00 and 23:59:59
        filtered_df = df[(df['transaction_date'] >= start_date) & (df['transaction_date'] <= end_date)]
        print(filtered_df)
        a = filtered_df.to_dict(orient='records')
        print(type(a))
        for row in a:
            if row['transfer_code'] and len(row['transfer_code']) == 7:
                if row['transaction_type'] == 'IN' and row['status'] != 'Success'and row['status'] != 'Failed':
                    print(row['transaction_date'], row['transfer_code'], row['amount'], row['transaction_type'], row['status'])
                    formatted_amount = '{:,.2f}'.format(row['amount'])
                    bank_account = BankAccount.objects.filter(account_number=str(row['account_number'])).first()
                    success = False
                    reported = False
                    if bank_account:
                        cids = CID.objects.filter(name="CID16302", status=True)
                        for item in cids:
                            print(item)
                            result = create_deposit_order(row, item)
                            print(result)
                            if result:
                                if result['msg'] == 'transfercode is null':
                                    update_transaction_history_status(row['account_number'],
                                                                      row['transfer_code'],
                                                                      'Failed')
                                    alert = (
                                        f'Hi, failed\n'
                                        f'\n'
                                        f'Account: {row['account_number']}'
                                        f'\n'
                                        f'Confirmed by order: \n'
                                        f'\n'
                                        f'Received amount💲: {formatted_amount} \n'
                                        f'\n'
                                        f'Memo: {row['description']}\n'
                                        f'\n'
                                        f'Code: {find_substring(row['description'])}\n'
                                        f'\n'
                                        f'Time: {row["transaction_date"]}\n'
                                        f'\n'
                                        f'Reason of not be credited: No transfer code!!!'
                                    )
                                    send_telegram_message(alert, os.environ.get('FAILED_CHAT_ID'),
                                                          os.environ.get('226PAY_BOT'))
                                    reported = True
                                    break

                                if result['prc'] == '1' and result['errcode'] == '00':
                                    if result['orderno'] == '':
                                        continue
                                    else:
                                        print(row['transfer_code'])
                                        update_transaction_history_status(row['account_number'],
                                                                          row['transfer_code'], 'Success')
                                        alert = (
                                            f'🟩🟩🟩 Success! CID: {item.name}\n'
                                            f'\n'
                                            f'Account: {row['account_number']}'
                                            f'\n'
                                            f'Confirmed by order: \n'
                                            f'\n'
                                            f'Received amount💲: {formatted_amount} \n'
                                            f'\n'
                                            f'Memo: {row['description']}\n'
                                            f'\n'
                                            f'Code: {find_substring(row['description'])}\n'
                                            f'\n'
                                            f'Time: {row["transaction_date"]}\n'
                                        )
                                        send_telegram_message(alert, os.environ.get('TRANSACTION_CHAT_ID'),
                                                              os.environ.get('TRANSACTION_BOT_API_KEY'))
                                        update_amount_by_date('IN', row['amount'])
                                        success = True
                                        break
                                else:
                                    continue
                            else:
                                continue
                        if not success and not reported:
                            if bank.bank_name.name != 'MB':
                                update_transaction_history_status(row['account_number'], row['transfer_code'],
                                                                  'Failed')
                                alert = (
                                    f'Hi, failed\n'
                                    f'\n'
                                    f'Account: {row['account_number']}'
                                    f'\n'
                                    f'Confirmed by order: \n'
                                    f'\n'
                                    f'Received amount💲: {formatted_amount} \n'
                                    f'\n'
                                    f'Memo: {row['description']}\n'
                                    f'\n'
                                    f'Code: {find_substring(row['description'])}\n'
                                    f'\n'
                                    f'Time: {row["transaction_date"]}\n'
                                    f'\n'
                                    f'Reason of not be credited: Order not found!!!'
                                )
                                send_telegram_message(alert, os.environ.get('FAILED_CHAT_ID'),
                                                      os.environ.get('226PAY_BOT'))