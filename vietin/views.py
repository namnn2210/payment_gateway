from bank.utils import Transaction, find_substring
from datetime import datetime
from config.views import get_env
import requests
import json


# Create your views here.
def vietin_login(username, password, account_number):
    body = {
        "rows": 1,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action": "login"
    }
    response = requests.post(get_env("VIETIN_URL"), json=body, timeout=120)
    if '"message":"success"' in response.text:
        return True
    return False


def vietin_balance(username, password, account_number):
    body = {
        "rows": 10,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action": "balance"
    }
    response = requests.post(get_env("VIETIN_URL"), json=body, timeout=120).json()
    if response:
        if 'error' in response.keys():
            if not response['error']:
                acc_list = response['accounts']
                for account in acc_list:
                    if account['number'] == account_number:
                        return account['accountState']['availableBalance']
    return None


def vietin_transactions(username, password, account_number):
    try:
        page = 0
        fetch_transactions = []
        formatted_transactions = []
        headers = {
            'Content-Type': 'application/json'
        }
        while True:
            body = json.dumps({
                "rows": 1000,
                "username": username,
                "password": password,
                "accountNumber": account_number,
                "page": page,
                "action": "transactions"
            })
            response = requests.post(get_env("VIETIN_URL"), headers=headers, data=body, timeout=120).json()
            transactions = response['transactions']
            if transactions:
                fetch_transactions += transactions
                page += 1
            else:
                break

        for item in fetch_transactions:
            if item['dorC'] == 'C':
                transaction_type = 'IN'
            else:
                transaction_type = 'OUT'
            transaction_date = datetime.strptime(item['processDate'], '%d-%m-%Y %H:%M:%S')
            transaction_date = transaction_date.strftime('%d/%m/%Y %H:%M:%S')  # Ensure timezone aware datetime
            new_formatted_transaction = Transaction(
                transaction_number=item['trxId'],
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                account_number=account_number,
                description=item['remark'],
                transfer_code=find_substring(item['remark']),
                amount=int(item['amount'])
            )
            formatted_transactions.append(new_formatted_transaction.__dict__())
        return formatted_transactions
    except Exception as ex:
        return None
