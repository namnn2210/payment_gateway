import logging
from django.views.decorators.csrf import csrf_exempt
from bank.database import redis_connect
from django.http import JsonResponse
from bank.utils import Transaction
from bank.models import BankAccount
from partner.models import CID
from partner.views import create_deposit_order
from bank.utils import get_dates, find_substring
from bank.views import update_amount_by_date, update_transaction_history_status
import requests
import json
import os
from bank.utils import send_telegram_message
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from django.utils import timezone
import pytz


load_dotenv()
logger = logging.getLogger('django')


def mb_login(username, password, account_number):
    body = {
        "action": "login",
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    print('start login: ', datetime.now())
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if '"ok":true' in response.text:
        print('end login: ', datetime.now())
        return True
    return False

def mb_transactions(username, password, account_number, start=''):
    end_date, start_date = get_dates(start_date=start)
    body = {
        "action": "transactions",
        "begin": start_date,
        "end": end_date,
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if response.status_code == 200:
        if '"ok":true' in response.text:
            json_response = json.loads(response.text)
            if json_response['result']['ok']:
                formatted_transactions = []
                transactions = json_response['transactionHistoryList']
                logger.info(transactions)
                for transaction in transactions:
                    if int(transaction['creditAmount']) != 0:
                        transaction_type = 'IN'
                        amount = int(transaction['creditAmount'])
                    else:
                        transaction_type = 'OUT'
                        amount = int(transaction['debitAmount'])
                    new_formatted_transaction = Transaction(
                        transaction_number=transaction['refNo'],
                        transaction_date=transaction['transactionDate'],
                        transaction_type= transaction_type,
                        account_number=transaction['accountNo'],
                        description=transaction['description'],
                        transfer_code=find_substring(transaction['description']),
                        amount=amount
                    )
                    formatted_transactions.append(new_formatted_transaction.__dict__())
                return formatted_transactions
    return None


def mb_balance(username, password, account_number):
    body = {
        "action": "balance",
        "username": username,
        "accountNumber": account_number,
        "password": password
    }
    response = requests.post(os.environ.get("MB_URL"), json=body, timeout=120)
    if '"ok":true' in response.text:
        data = response.json()
        acc_list = data['acct_list']
        for account in acc_list:
            if account['acctNo'] == account_number:
                return int(account['currentBalance'])
    return None

@csrf_exempt
def mb_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)['data'][0]
        logger.info(data)
        redis_client = redis_connect(1)
        new_formatted_transaction = Transaction(
            transaction_number=data['refNo'],
            transaction_date=data['transactionDate'],
            transaction_type=data['type'],
            account_number=data['accountNo'],
            description=data['description'],
            transfer_code=find_substring(data['description']),
            amount=int(data['amount'])
        )
        new_transaction_dict = new_formatted_transaction.__dict__()

        bank_exists = redis_client.get(new_formatted_transaction.account_number)
        bank = BankAccount.objects.filter(account_number=new_formatted_transaction.account_number).first()
        bank.balance = int(data['availableBalance'])
        bank.save()
        # new_bank_history_df = pd.DataFrame(formatted_transactions)
        # if new_bank_history_df.empty:
        #     alert = (
        #         f'🔴 - LỖI HỆ THỐNG\n'
        #         f'Lỗi lấy lịch sử giao dịch từ {new_formatted_transaction.account_number} - MB empty\n'
        #         f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')}'
        #     )
        #     send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))
        # final_new_bank_history_df = new_bank_history_df.fillna('')
        if not bank_exists:
            new_list_transactions = [new_transaction_dict]
            redis_client.set(new_formatted_transaction.account_number,
                             json.dumps(new_list_transactions, default=str))
        else:
            # Transform current transactions history and new transaction history
            old_bank_history = json.loads(redis_client.get(new_formatted_transaction.account_number))
            if 'Z' in new_formatted_transaction.description and new_formatted_transaction.transaction_type == 'OUT':
                new_formatted_transaction.status = 'Success'
            old_bank_history.append(new_formatted_transaction.__dict__())

            # Update Redis
            redis_client.set(new_formatted_transaction.account_number, json.dumps(old_bank_history, default=str))

            if new_transaction_dict['transaction_type'] == 'IN':
                if bank.bank_type == 'IN':
                    formatted_amount = '{:,.2f}'.format(new_transaction_dict['amount'])
                    balance = '{:,.2f}'.format(int(data['availableBalance']))
                    bank_account = BankAccount.objects.filter(account_number=str(new_transaction_dict['account_number'])).first()
                    success = False
                    reported = False
                    if bank_account:
                        cids = CID.objects.filter(status=True)
                        for item in cids:
                            print('test partner: ', item.name)
                            result = create_deposit_order(new_transaction_dict, item)
                            print('result partner', result)
                            if result:
                                if result['msg'] == 'transfercode is null':
                                    update_transaction_history_status(new_transaction_dict['account_number'],
                                                                      new_transaction_dict['transfer_code'], 'Failed')
                                    alert = (
                                        f'Hi, failed\n'
                                        f'\n'
                                        f'Account: {new_transaction_dict['account_number']}'
                                        f'\n'
                                        f'Confirmed by order: \n'
                                        f'\n'
                                        f'Received amount💲: {formatted_amount} \n'
                                        f'\n'
                                        f'Memo: {new_transaction_dict['description']}\n'
                                        f'\n'
                                        f'Code: {find_substring(new_transaction_dict['description'])}\n'
                                        f'\n'
                                        f'Time: {new_transaction_dict["transaction_date"]}\n'
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
                                        update_transaction_history_status(new_transaction_dict['account_number'],
                                                                          new_transaction_dict['transfer_code'], 'Success')
                                        alert = (
                                            f'🟩🟩🟩 Success! CID: {item.name}\n'
                                            f'\n'
                                            f'Account: {new_transaction_dict['account_number']}'
                                            f'\n'
                                            f'Confirmed by order: \n'
                                            f'\n'
                                            f'Received amount💲: {formatted_amount} \n'
                                            f'\n'
                                            f'Balance💲: {balance} \n'
                                            f'\n'
                                            f'Memo: {new_transaction_dict['description']}\n'
                                            f'\n'
                                            f'Code: {find_substring(new_transaction_dict['description'])}\n'
                                            f'\n'
                                            f'Time: {new_transaction_dict["transaction_date"]}\n'
                                        )
                                        send_telegram_message(alert, os.environ.get('TRANSACTION_CHAT_ID'),
                                                              os.environ.get('TRANSACTION_BOT_API_KEY'))
                                        update_amount_by_date('IN', new_transaction_dict['amount'])
                                        success = True
                                        break
                                else:
                                    continue
                            else:
                                continue
                        if not success and not reported:
                            update_transaction_history_status(new_transaction_dict['account_number'], new_transaction_dict['transfer_code'],
                                                              'Failed')
                            alert = (
                                f'Hi, failed\n'
                                f'\n'
                                f'Account: {new_transaction_dict['account_number']}'
                                f'\n'
                                f'Confirmed by order: \n'
                                f'\n'
                                f'Received amount💲: {formatted_amount} \n'
                                f'\n'
                                f'Memo: {new_transaction_dict['description']}\n'
                                f'\n'
                                f'Code: {find_substring(new_transaction_dict['description'])}\n'
                                f'\n'
                                f'Time: {new_transaction_dict["transaction_date"]}\n'
                                f'\n'
                                f'Reason of not be credited: Order not found!!!'
                            )
                            send_telegram_message(alert, os.environ.get('FAILED_CHAT_ID'),
                                                  os.environ.get('226PAY_BOT'))
            else:
                if bank.bank_type == 'OUT':
                    transaction_type = '-'
                    transaction_color = '🔴'  # Red circle emoji for OUT transactions
                    formatted_amount = '{:,.2f}'.format(new_transaction_dict['amount'])
                    alert = (
                        f'PAYOUT DONE\n'
                        f'\n'
                        f'🏦 {bank.account_number} - {bank.account_name}\n'
                        f'\n'
                        f'Nội dung: {new_transaction_dict["description"]}\n'
                        f'\n'
                        f'💰 {transaction_color} {transaction_type}{formatted_amount} \n'
                        f'\n'
                        f'🕒 {new_transaction_dict["transaction_date"]}'
                    )
                    send_telegram_message(alert, os.environ.get('PAYOUT_CHAT_ID'),
                                          os.environ.get('TRANSACTION_BOT_API_KEY'))
                print('Update transactions for bank: %s. Updated at %s' % (
                bank.account_number, datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')))
        return JsonResponse({'status': 200, 'message': 'Done','success': True, 'data':data})
    return JsonResponse({'status': 500, 'message': 'Invalid request','success': False})