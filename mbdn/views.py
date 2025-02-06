from config.views import get_env
from datetime import datetime
from bank.utils import Transaction
from bank.utils import get_dates, find_substring
import requests
import json
import logging

logger = logging.getLogger('django')

# Create your views here.
def mbdn_transactions(transactions):
    formatted_transactions = []
    for transaction in transactions:
        payername = ''
        if int(transaction['creditAmount']) != 0 and transaction['sign'] == 'C':
            transaction_type = 'IN'
            amount = int(transaction['creditAmount'])
            payername = transaction.get('reciprocalAcctName','')
        else:
            transaction_type = 'OUT'
            amount = int(transaction['debitAmount'])
        new_formatted_transaction = Transaction(
            transaction_number=transaction['transactionRefNo'],
            transaction_date=transaction['transactionDate'],
            transaction_type=transaction_type,
            account_number=transaction['accountNo'],
            description=transaction['description'],
            transfer_code=find_substring(transaction['description']),
            payername=payername,
            amount=amount
        )
        formatted_transactions.append(new_formatted_transaction.__dict__())
    if len(formatted_transactions) == 0:
        return None
    return formatted_transactions


def mbdn_balance(username, password, account_number, corp_id, start=''):
    end_date, start_date = get_dates(start_date=start)
    body = {
        "begin": start_date,
        "end": end_date,
        "username": username,
        "password": password,
        "accountNo": account_number,
        "corp_id": corp_id
    }
    response = requests.post(get_env("MBDN_URL"), json=body, timeout=120)
    if response.status_code == 200:
        if '"ok":true' in response.text:
            json_response = json.loads(response.text)
            print(json_response)
            if json_response['data']['result']['ok']:
                transactions = json_response['data']['transactionHistoryList']
                return transactions[0]['availableBalance'], transactions
    return None, None