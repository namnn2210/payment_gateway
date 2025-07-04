import requests
import os
from datetime import datetime, timedelta, timezone
from bank.utils import Transaction, find_substring
import httpx

async def tech_login(username, password):
    body = {
        "username": username,
        "password": password,
    }
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(f"{os.environ.get('TECH_URL')}login", json=body)
            response_data = response.json()
            if response_data.get('success'):
                return True
            return False
    except httpx.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
        return False

def tech_balance(username, password, account_number):
    body = {
        "username": username,
        "password": password,
        "accountNumber": account_number,
    }

    response = requests.post(f'{os.environ.get("TECH_URL")}balance', json=body , timeout=300).json()
    print(response)
    if type(response) == list :
        for item in response:
            if item['BBAN'] == account_number:
                print("balance", item['availableBalance'])
                return item['availableBalance']
    if type(response) == dict :

        if 'message' in response.keys() and response['message'] == 'Request failed with status code 401':
            return None
        if 'success' in response.keys() and not response['success']:
            return None
    return None

def tech_refresh_token(username):
    body = {
        "username": username,
    }
    response = requests.post(f'{os.environ.get("TECH_URL")}refresh-token', json=body, timeout=300).json()
    print(response)
    if response['success']:
        return True
    else:
        return False

def tech_transactions(username, password, account_number):
    formatted_transactions = []
    # Get today's date
    end_date = datetime.now(timezone(timedelta(hours=7)))

    # Calculate the date 30 days ago
    begin_date = end_date - timedelta(days=30)

    # Format the dates as "DD/MM/YYYY"
    begin_str = begin_date.strftime("%d/%m/%Y")
    end_str = end_date.strftime("%d/%m/%Y")

    # Example payload
    body = {
        "begin": begin_str,
        "end": end_str,
        "username": username,
        "password": password,
        "accountNumber": account_number,
        "size": 100
    }

    print(body)

    response = requests.post(f'{os.environ.get("TECH_URL")}', json=body, timeout=300).json()
    if response['success']:
        transactions = response['transactions']
        transaction_type = ''
        print(transactions)
        for transaction in transactions:
            if transaction['type'] == "DBIT":
                transaction_type = "OUT"
            elif transaction['type'] == "CRDT":
                transaction_type = "IN"
            transaction_date = datetime.fromisoformat(transaction['creationTime'])
            transaction_date = transaction_date.astimezone(timezone(timedelta(hours=8)))
            transaction_date = transaction_date.strftime('%d/%m/%Y %H:%M:%S')
            new_formatted_transaction = Transaction(
                transaction_number=transaction['reference'],
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                account_number=account_number,
                description=transaction['description'],
                transfer_code=find_substring(transaction['description']),
                amount=int(transaction['transactionAmountCurrency']['amount']),
                payername=''
            )
            formatted_transactions.append(new_formatted_transaction.__dict__())
        return formatted_transactions
    return None
