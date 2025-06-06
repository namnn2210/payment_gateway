from config.views import get_env
from datetime import datetime
from bank.utils import Transaction
from bank.utils import get_dates, find_substring
import requests
import json
import logging

logger = logging.getLogger('django')


def mb_login(username, password, account_number):
    body = {
        "action": "login",
        "username": username,
        "password": password,
        "accountNumber": account_number
    }
    response = requests.post(f'{get_env("MBB_URL")}/login', json=body, timeout=120).json()
    print(response)
    if response['result']['ok']:
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
    response = requests.post(get_env("MBB_URL"), json=body, timeout=120)
    if response.status_code == 200:
        if '"ok":true' in response.text:
            json_response = json.loads(response.text)
            if json_response['result']['ok']:
                formatted_transactions = []
                transactions = json_response['transactionHistoryList']
                print("mb transaction", transactions)
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
                        transaction_type=transaction_type,
                        account_number=transaction['accountNo'],
                        description=transaction['description'],
                        transfer_code=find_substring(transaction['description']),
                        amount=amount,
                        payername=''
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
    response = requests.post(get_env("MBB_URL_BALANCE"), json=body, timeout=120)
    print("mb balance", response)
    if '"ok":true' in response.text:
        data = response.json()
        acc_list = data['acct_list']
        for account in acc_list:
            if account['acctNo'] == account_number:
                return int(account['currentBalance'])
    return None
