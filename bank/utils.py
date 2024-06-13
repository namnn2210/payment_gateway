import requests
import json
import pandas as pd

def get_bank(bank_name,bank_number, bank_username, bank_password):
    if bank_name == 'ACB':
        return get_acb_bank(bank_number, bank_username, bank_password)

def get_acb_bank(bank_number, bank_username, bank_password):
    url = "https://api.httzip.com/api/bank/ACB/balance"
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "login_id": bank_username,
        "login_password": bank_password
    })

    response = requests.post(url=url, headers=headers, data=payload)
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        for bank_account in list_bank_account:
            if bank_account['accountNumber'] == bank_number:
                return bank_account
    return None

def get_acb_bank_transaction_history(bank_account):
    url = 'https://api.httzip.com/api/bank/ACB/transactions'
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "login_id": bank_account.username,
        "login_password": bank_account.password,
        "filter_account":bank_account.account_number
    })
    
    response = requests.post(url=url, headers=headers, data=payload)
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        return list_bank_account
    return None

def unix_to_datetime(unix_time):
    # Convert Unix time to datetime with UTC timezone
    dt_utc = pd.to_datetime(unix_time, unit='ms', utc=True)
    # Convert to GMT+7
    dt_gmt_plus_7 = dt_utc.dt.tz_convert(tz='Asia/Bangkok')
    formatted_dt = dt_gmt_plus_7.dt.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_dt

CHAT_ID = '-1002160999380'
API_KEY = '7402362257:AAHpTt7prptyy5fbvAWlMbYVNKUi0B5aZV8'

def send_telegram_message(message: str):
    data_dict = {'chat_id': CHAT_ID,
                 'text': message,
                 'parse_mode': 'HTML',
                 'disable_notification': True}
    headers = {'Content-Type': 'application/json',
               'Proxy-Authorization': 'Basic base64'}
    data = json.dumps(data_dict)
    params = {
        'parse_mode': 'Markdown'
    }
    url = f'https://api.telegram.org/bot{API_KEY}/sendMessage'
    response = requests.post(url,
                             data=data,
                             headers=headers,
                             params=params,
                             verify=False)
    return response