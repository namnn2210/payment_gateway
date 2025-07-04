from bank.utils import Transaction, unix_to_datetime, find_substring
from config.views import get_env
import requests
import logging


logger = logging.getLogger('django')


# Create your views here.
def acb_login(username, password, account_number):
    body = {
        "rows": 1,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action": "login"
    }
    response = requests.post(get_env("ACB_URL"), json=body)
    print(response.text)
    if response.status_code == 200:
        data = response.json()
        if 'accessToken' in data.keys():
            if data['accessToken']:
                return True
    return False


def acb_balance(username, password, account_number):
    body = {
        "rows": 10,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action": "balance"
    }
    response = requests.post(get_env("ACB_URL"), json=body)
    response = response.json()
    print(response)
    if response:
        if 'codeStatus' in response.keys():
            if response['codeStatus'] == 200:
                acc_list = response['data']
                for account in acc_list:
                    if account['accountNumber'] == account_number:
                        return account['balance']
    return None


def acb_transactions(username, password, account_number):
    body = {
        "rows": 1000,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "action": "transactions"
    }
    response = requests.post(get_env("ACB_URL"), json=body).json()
    print("acb transactions", response)
    if response['codeStatus'] == 200:
        transactions = response['data']
        formatted_transactions = []
        for transaction in transactions:
            new_formatted_transaction = Transaction(
                transaction_number=transaction['transactionNumber'],
                transaction_date=unix_to_datetime(transaction['activeDatetime']),
                transaction_type=transaction['type'],
                account_number=transaction['account'],
                description=transaction['description'],
                transfer_code=find_substring(transaction['description']),
                amount=transaction['amount'],
                payername=''
            )
            formatted_transactions.append(new_formatted_transaction.__dict__())
        return formatted_transactions
    return None
