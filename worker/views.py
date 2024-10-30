from django.shortcuts import render
from celery import Celery
import logging
from dotenv import load_dotenv
from mb.views import mb_balance, mb_transactions, mb_login
from acb.views import acb_transactions, acb_balance, acb_login
from vietin.views import vietin_login, vietin_balance, vietin_transactions
from tech.views import tech_login, tech_balance, tech_transactions
from bank.utils import send_telegram_message, find_substring
from bank.views import update_amount_by_date, update_transaction_history_status, update_out_transaction_history_status
from bank.models import BankAccount
from partner.views import create_deposit_order
from partner.models import CID
from datetime import datetime
import pandas as pd
import json
import os
import pytz
from bank.database import redis_connect
from django.utils import timezone
import time
from bank.views import check_success_payout

load_dotenv()
logger = logging.getLogger('django')


def get_balance(bank):
    error_count = 0
    # bank_exists = redis_client.get(bank.account_number)
    print('Fetching bank balance: ', bank.account_name, bank.account_number, bank.bank_name, bank.username,
          bank.password)
    # Get balance
    if bank.bank_name.name == 'MB':
        bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == "Techcombank":
        bank_balance = tech_balance(bank.username, bank.password, bank.account_number)
    else:
        bank_balance = None
    while bank_balance is None:
        print('Error fetching bank balance, try to login')
        error_count += 1
        print('Retry logging in: ', error_count)
        if error_count > 3:
            alert = (
                f'🔴 - LỖI HỆ THỐNG\n'
                f'Dữ liệu tài khoản: {bank.account_number} trống\n'
                f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
            )
            send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
            return

        bank_logged_in = None

        if bank.bank_name.name == 'MB':
            bank_logged_in = mb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'ACB':
            bank_logged_in = acb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Vietinbank':
            bank_logged_in = vietin_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Techcombank':
            bank_logged_in = tech_login(bank.username, bank.password, bank.account_number)

        if bank_logged_in:
            if bank.bank_name.name == 'MB':
                bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'ACB':
                bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Vietinbank':
                bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Techcombank':
                bank_balance = tech_balance(bank.username, bank.password, bank.account_number)
            else:
                bank_balance = None

    if bank_balance:
        if int(bank_balance) != int(bank.balance):
            bank.balance = bank_balance
            bank.updated_at = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
            bank.save()
            print('Update for bank: %s. Updated at %s' % (
                bank.account_number, timezone.now().strftime('%Y-%m-%d %H:%M:%S')))

            # Get transactions
            if bank.bank_name.name == 'MB':
                time.sleep(60)

            get_transaction(bank)

        else:
            pass
            # print('No new data for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
    elif bank_balance is None:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lấy số dư tài khoản {bank.account_number} - {bank.bank_name.name} không thành công\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        )
        send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))


def get_transaction(bank):
    redis_client = redis_connect(1)
    bank_exists = redis_client.get(bank.account_number)
    if bank.bank_name.name == 'MB':
        new_transactions = mb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        new_transactions = acb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        new_transactions = vietin_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Techcombank':
        new_transactions = tech_transactions(bank.username, bank.password, bank.account_number)
    else:
        new_transactions = None

    if not new_transactions:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lỗi lấy lịch sử giao dịch từ {bank.account_number} - {bank.bank_name.name} empty\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        )
        send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))

    if not bank_exists:
        redis_client.set(bank.account_number,
                         json.dumps(new_transactions, default=str))
    else:
        # Transform current transactions history and new transaction history
        old_bank_history = json.loads(redis_client.get(bank.account_number))
        list_old_transaction_numbers = [item['transaction_number'] for item in old_bank_history]

        different_transactions = [item for item in new_transactions if
                                  item['transaction_number'] not in list_old_transaction_numbers]
        # Add new transactions to current history
        logger.info(different_transactions)
        for transaction in different_transactions:
            # Check for success out
            if transaction['transaction_type'] == 'OUT':
                if 'Z' in transaction['description']:
                    transaction['status'] = 'Success'
        updated_transactions = old_bank_history + different_transactions
        # Update Redis
        redis_client.set(bank.account_number, json.dumps(updated_transactions, default=str))
        if different_transactions:
            for row in different_transactions:
                bank_account = BankAccount.objects.filter(account_number=str(row['account_number'])).first()
                if not datetime.strptime(row["transaction_date"], '%d/%m/%Y %H:%M:%S').date() >= timezone.now().date():
                    continue
                if row['transaction_type'] == 'IN':
                    formatted_amount = '{:,.2f}'.format(row['amount'])
                    memo_transfer_check = 'C' + bank_account.account_name
                    memo_deposit_check = 'D' + bank_account.account_name
                    if memo_transfer_check in row['description'] or memo_deposit_check in row['description']:
                        continue
                    success = False
                    reported = False
                    if bank_account:
                        cids = CID.objects.filter(status=True)
                        for item in cids:
                            logger.info(item.name)
                            result = create_deposit_order(row, item)
                            logger.info(result)
                            if result:
                                if result['msg'] == 'transfercode is null':
                                    update_transaction_history_status(row['account_number'], row['transfer_code'], '',
                                                                      '', '', 'Failed')
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

                                if result['prc'] == '1' and result['errcode'] == '00' and result['msg'] == "SUCCESS":
                                    if result['orderno'] == '':
                                        continue
                                    else:
                                        update_transaction_history_status(row['account_number'],
                                                                          row['transfer_code'], result['orderid'],
                                                                          result['scode'], result['incomingorderid'],
                                                                          'Success')
                                        alert = (
                                            f'🟩🟩🟩 Success! CID: {item.name}\n'
                                            f'\n'
                                            f'Account: {row['account_number']}'
                                            f'\n'
                                            f'Confirmed by order: {result['incomingorderid']}\n'
                                            f'\n'
                                            f'Received amount💲: {formatted_amount} \n'
                                            f'\n'
                                            f'Memo: {row['description']}\n'
                                            f'\n'
                                            f'Order ID: {result['orderid']}\n'
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
                            update_transaction_history_status(row['account_number'], row['transfer_code'], '', '', '',
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
                else:
                    transaction_type = '-'
                    transaction_color = '🔴'  # Red circle emoji for OUT transactions
                    formatted_amount = '{:,.2f}'.format(row['amount'])

                    alert = (
                        f'💰 {transaction_color} {transaction_type}{formatted_amount} \n'
                        f'\n'
                        f'Nội dung: {row["description"]}\n'
                        f'\n'
                        f'🏦 {bank.account_number} - {bank.account_name}\n'
                        f'\n'
                        f'🕒 {row["transaction_date"]}'
                    )

                    bank_accounts = BankAccount.objects.filter(status=True)
                    set_name = set([bank_account.account_name for bank_account in bank_accounts])
                    for name in set_name:
                        first_name = name.split(' ')[-1]
                        memo_transfer_check = 'W' + first_name
                        memo_deposit_check = 'D' + first_name
                        if memo_transfer_check in row['description'] or memo_deposit_check in row['description']:
                            send_telegram_message(alert, os.environ.get('INTERNAL_CHAT_ID'),
                                                  os.environ.get('TRANSACTION_BOT_API_KEY'))
                            break
                        else:
                            send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'),
                                                  os.environ.get('TRANSACTION_BOT_API_KEY'))
            print('Update transactions for bank: %s. Updated at %s' % (
                bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            pass
            # print('No new transactions for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))


def get_balance_by_bank(bank):
    bank_balance = 0
    error_count = 0
    print('Fetching bank balance: ', bank.account_name, bank.account_number, bank.bank_name, bank.username,
          bank.password)
    # Get balance
    if bank.bank_name.name == 'MB':
        bank_balance = bank.balance
    elif bank.bank_name.name == 'ACB':
        bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
    else:
        bank_balance = 0
    while bank_balance is None:
        print('Error fetching bank balance, try to login')
        error_count += 1
        bank_logged_in = None
        print('Retry logging in: ', error_count)
        if error_count > 3:
            alert = (
                f'🔴 - LỖI HỆ THỐNG\n'
                f'Dữ liệu tài khoản: {bank.account_number} trống\n'
                f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
            )
            send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
            return 0

        if bank.bank_name.name == 'MB':
            bank_logged_in = mb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'ACB':
            bank_logged_in = acb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Vietinbank':
            bank_logged_in = vietin_login(bank.username, bank.password, bank.account_number)

        if bank_logged_in:
            if bank.bank_name.name == 'ACB':
                bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Vietinbank':
                bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
            else:
                bank_balance = 0

    return bank_balance
