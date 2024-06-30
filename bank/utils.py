import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
bank_data = json.load(open('bank.json'))

def get_bank(bank_name,bank_number, bank_username, bank_password):
    return get_bank_balance(bank_number, bank_username, bank_password, bank_name)

def get_bank_balance(bank_number, bank_username, bank_password, bank_name):
    url = f"https://api.httzip.com/api/bank/{bank_name}/balance"
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
    print(response.json())
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        if isinstance(list_bank_account, list):
            for bank_account in list_bank_account:
                if bank_account['accountNumber'] == bank_number:
                    return bank_account
        elif isinstance(list_bank_account, dict):
            if list_bank_account['accountNumber'] == bank_number:
                    return list_bank_account
        else:
            return None
    return None

def get_bank_transaction_history(bank_account):
    url = f'https://api.httzip.com/api/bank/{bank_account.bank_name}/transactions'
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        "login_id": bank_account.username,
        "login_password": bank_account.password,
        "filter_account":bank_account.account_number,
        "last_x_day":30
    })
    
    response = requests.post(url=url, headers=headers, data=payload)
    if response.status_code == 200:
        list_bank_account = response.json()['data']
        return list_bank_account
    return None

def check_bank_info(row):
    url = 'https://api.httzip.com/api/bank/id-lookup-prod'
    headers = {
        'x-api-key': '4bc524c2-9b8a-4168-b7ea-a149dbc2e03ckey',
        'x-api-secret': 'f48dc692-3a82-4fdd-a43e-b180c7ba7176secret',
        'Content-Type': 'application/json'
    }
    if row['bank_code'] is not None:
        data = {
            'bank':row['bank_code'],
            'account':str(row['accountno'])
        }
        response = requests.post(url=url, headers=headers, json=data)
        # if response.status_code == 200:
        data = response.json()
        print(data)
        if data['success']:
            response_name = data['data']['ownerName']
            if response_name.lower() == row['accountname'].lower():
                return True
    return False

def find_bank_code(bankname):
    bank_mapping_extended = {bank['short_name'].lower(): bank for bank in bank_data}
    bank_mapping_extended.update({bank['code'].lower(): bank for bank in bank_data})
    bank_object = bank_mapping_extended.get(bankname.lower(), None)
    return bank_object['code'] if bank_object else None



def unix_to_datetime(unix_time):
    # Convert Unix time to datetime with UTC timezone
    dt_utc = pd.to_datetime(unix_time, unit='ms', utc=True)
    # Convert to GMT+7
    dt_gmt_plus_7 = dt_utc.dt.tz_convert(tz='Asia/Bangkok')
    formatted_dt = dt_gmt_plus_7.dt.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_dt

def send_telegram_message(message: str, chat_id, api_key):
    data_dict = {'chat_id': chat_id,
                 'text': message,
                 'parse_mode': 'HTML',
                 'disable_notification': True}
    headers = {'Content-Type': 'application/json',
               'Proxy-Authorization': 'Basic base64'}
    data = json.dumps(data_dict)
    params = {
        'parse_mode': 'Markdown'
    }
    API_KEY = os.environ.get('API_KEY')
    url = f'https://api.telegram.org/bot{api_key}/sendMessage'
    response = requests.post(url,
                             data=data,
                             headers=headers,
                             params=params,
                             verify=False)
    return response