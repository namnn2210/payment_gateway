import requests
import json
import pandas as pd
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
bank_data = json.load(open('bank.json'))


class Transaction:
    def __init__(self, transaction_number, transaction_date, transaction_type, account_number, description, amount) -> None:
        self.transaction_number = transaction_number
        self.transaction_date = transaction_date
        self.transaction_type = transaction_type
        self.account_number = account_number
        self.description = description
        self.amount = amount

    def __dict__(self) -> dict:
        return {
            'transaction_number':self.transaction_number,
            'transaction_date':self.transaction_date,
            'transaction_type':self.transaction_type,
            'account_number':self.account_number,
            'description':self.description, 
            'amount':self.amount
        }
        
        
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


def get_dates(start_date=''):
    # If start_date is empty, use the current date
    if start_date == '':
        start_date = datetime.now()
    else:
        # Parse the provided start date
        start_date = datetime.strptime(start_date, '%d/%m/%Y')
    
    # Calculate the date 30 days before the start date
    date_30_days_before = start_date - timedelta(days=30)
    
    # Return the results in the specified format
    return start_date.strftime('%d/%m/%Y'), date_30_days_before.strftime('%d/%m/%Y')

def find_substring(text):
    # Regex pattern to find a substring starting with 'Z' and having 7 characters
    pattern = r'Z.{6}'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None
    
def unix_to_datetime(unix_time):
    # Convert Unix time to datetime with UTC timezone
    dt_utc = pd.to_datetime(unix_time, unit='ms', utc=True)
    # Convert to GMT+7
    dt_gmt_plus_7 = dt_utc.dt.tz_convert(tz='Asia/Bangkok')
    formatted_dt = dt_gmt_plus_7.dt.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_dt