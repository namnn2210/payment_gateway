from django.shortcuts import render
from celery import Celery
from dotenv import load_dotenv
from mb.views import mb_balance, mb_transactions, mb_login
from acb.views import acb_transactions, acb_balance, acb_login
from vietin.views import vietin_login, vietin_balance, vietin_transactions
from bank.utils import send_telegram_message, find_substring
from bank.views import update_amount_by_date, update_transaction_history_status
from bank.models import BankAccount
from partner.views import create_deposit_order
from partner.models import PartnerMapping
from datetime import datetime
import pandas as pd
import json
import os
import pytz
from bank.database import redis_connect

load_dotenv()

def get_balance(bank):
    error_count = 0
    # bank_exists = redis_client.get(bank.account_number)
    print('Fetching bank balance: ', bank.account_name, bank.account_number, bank.bank_name, bank.username, bank.password)
    # Get balance
    if bank.bank_name.name == 'MB':
        bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
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
                f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
            )
            send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
            return
            
        if bank.bank_name.name == 'MB':
            mb_logged_in = mb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'ACB':
            mb_logged_in = acb_login(bank.username, bank.password, bank.account_number)
        elif bank.bank_name.name == 'Vietinbank':
            mb_logged_in = vietin_login(bank.username, bank.password, bank.account_number)
            
        if mb_logged_in:
            if bank.bank_name.name == 'MB':
                bank_balance = mb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'ACB':
                bank_balance = acb_balance(bank.username, bank.password, bank.account_number)
            elif bank.bank_name.name == 'Vietinbank':
                bank_balance = vietin_balance(bank.username, bank.password, bank.account_number)
            else:
                bank_balance = None
                                
    if bank_balance: 
        if int(bank_balance) != int(bank.balance):
            bank.balance = bank_balance
            bank.updated_at = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
            bank.save()
            print('Update for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))

            # Get transactions
            
            get_transaction(bank)
            
        else:
            pass
            # print('No new data for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
    else:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lấy số dư tài khoản {bank.account_number} - {bank.bank_name.name} không thành công\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
        )
        send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))

    
def get_transaction(bank):
    redis_client = redis_connect(1)
    bank_exists = redis_client.get(bank.account_number)
    if bank.bank_name.name == 'MB':
        transactions = mb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'ACB':
        transactions = acb_transactions(bank.username, bank.password, bank.account_number)
    elif bank.bank_name.name == 'Vietinbank':
        transactions = vietin_transactions(bank.username, bank.password, bank.account_number)
    else:
        transactions = None
    new_bank_history = transactions
    new_bank_history_df = pd.DataFrame(new_bank_history)
    if new_bank_history_df.empty:
        alert = (
            f'🔴 - LỖI HỆ THỐNG\n'
            f'Lỗi lấy lịch sử giao dịch từ {bank.account_number} - {bank.bank_name.name} empty\n'
            f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        )
        send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
    final_new_bank_history_df = new_bank_history_df.fillna('')
    if not bank_exists:
        redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
    else:
        # Transform current transactions history and new transaction history
        old_bank_history = json.loads(redis_client.get(bank.account_number))
        old_bank_history_df = pd.DataFrame(old_bank_history)
        old_bank_history_df['amount'] = old_bank_history_df['amount'].astype(int)
        final_new_bank_history_df['amount'] = final_new_bank_history_df['amount'].astype(int)
        # Detect new transactions
        new_transaction_df = pd.concat([old_bank_history_df, final_new_bank_history_df]).drop_duplicates(subset='transaction_number', keep=False)
        # Add new transactions to current history
        updated_df = pd.concat([old_bank_history_df, new_transaction_df])
        # Update Redis
        redis_client.set(bank.account_number, json.dumps(updated_df.to_dict(orient='records'), default=str))
        if not new_transaction_df.empty:
            for _, row in new_transaction_df.iterrows():
                if row['transaction_type'] == 'IN':
                    if bank.bank_type == 'IN':
                        transaction_type = '+'
                        transaction_color = '🟢'  # Green circle emoji for IN transactions
                        formatted_amount = '{:,.2f}'.format(row['amount'])
                        
                        # redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
                        bank_account = BankAccount.objects.filter(account_number=str(row['account_number'])).first()
                        success = False
                        if bank_account:
                            partner_mapping = PartnerMapping.objects.filter(bank=bank_account)
                            if partner_mapping: 
                                for item in partner_mapping:
                                    result = create_deposit_order(row,item)
                                    if result:
                                        if result['msg'] == 'transfercode is null':
                                            update_transaction_history_status(row['account_number'], row['transfer_code'], 'Failed')                                     
                                            alert = (
                                                f'Hi, failed\n'
                                                f'\n'
                                                f'Account: {row['account_number']}'
                                                f'\n'
                                                f'Confirmed by order: \n'
                                                f'\n'
                                                f'Received amount💲: {formatted_amount} VND\n'
                                                f'\n'
                                                f'Memo: {row['description']}\n'
                                                f'\n'
                                                f'Code: {find_substring(row['description'])}\n'
                                                f'\n'
                                                f'Time: {row["transaction_date"]}\n'
                                                f'\n'
                                                f'Reason of not be credited: No transfer code!!!'
                                            )
                                            send_telegram_message(alert, os.environ.get('FAILED_CHAT_ID'), os.environ.get('226PAY_BOT'))
                                            break
                                        
                                        if result['prc'] == '1' and result['errcode'] == '00':
                                            if result['orderno'] == '':
                                                continue                                      
                                            else:
                                                update_transaction_history_status(row['account_number'], row['transfer_code'], 'Success')    
                                                alert = (
                                                    f'🟩🟩🟩 Success!\n'
                                                    f'\n'
                                                    f'Account: {row['account_number']}'
                                                    f'\n'
                                                    f'Confirmed by order: \n'
                                                    f'\n'
                                                    f'Received amount💲: {formatted_amount} VND\n'
                                                    f'\n'
                                                    f'Memo: {row['description']}\n'
                                                    f'\n'
                                                    f'Code: {find_substring(row['description'])}\n'
                                                    f'\n'
                                                    f'Time: {row["transaction_date"]}\n'
                                                )
                                                send_telegram_message(alert, os.environ.get('TRANSACTION_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
                                                update_amount_by_date('IN',row['amount'])
                                                success = True
                                                break 
                                        else:
                                            continue
                                    else:
                                        continue
                                if not success:
                                    update_transaction_history_status(row['account_number'], row['transfer_code'], 'Failed')                                            
                                    alert = (
                                        f'Hi, failed\n'
                                        f'\n'
                                        f'Account: {row['account_number']}'
                                        f'\n'
                                        f'Confirmed by order: \n'
                                        f'\n'
                                        f'Received amount💲: {formatted_amount} VND\n'
                                        f'\n'
                                        f'Memo: {row['description']}\n'
                                        f'\n'
                                        f'Code: {find_substring(row['description'])}\n'
                                        f'\n'
                                        f'Time: {row["transaction_date"]}\n'
                                        f'\n'
                                        f'Reason of not be credited: Order not found!!!'
                                    )
                                    send_telegram_message(alert, os.environ.get('FAILED_CHAT_ID'), os.environ.get('226PAY_BOT'))  
                else:
                    if bank.bank_type == 'OUT':
                        transaction_type = '-'
                        transaction_color = '🔴'  # Red circle emoji for OUT transactions
                        formatted_amount = '{:,.2f}'.format(row['amount'])
                        alert = (
                            f'PAYOUT DONE - Đã trừ tiền\n'
                            f'\n'
                            f'🏦 {bank.account_number} - {bank.account_name}\n'
                            f'\n'
                            f'Nội dung: {row["description"]}\n'
                            f'\n'
                            f'💰 {transaction_color} {transaction_type}{formatted_amount} VND\n'
                            f'\n'
                            f'🕒 {row["transaction_date"]}'
                        )
                        # redis_client.set(bank.account_number, json.dumps(final_new_bank_history_df.to_dict(orient='records'), default=str))
                        send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'), os.environ.get('TRANSACTION_BOT_API_KEY'))
            print('Update transactions for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
        else:
            pass
            # print('No new transactions for bank: %s. Updated at %s' % (bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
