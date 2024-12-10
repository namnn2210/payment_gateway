from datetime import datetime, timedelta
from telegram import Bot
import re
import pytz


class Transaction:
    def __init__(self, transaction_number, transaction_date, transaction_type, account_number, description,
                 transfer_code, amount) -> None:
        self.transaction_number = str(transaction_number)
        if transaction_date:
            self.transaction_date = datetime.strptime(transaction_date, '%d/%m/%Y %H:%M:%S')
        self.transaction_type = transaction_type
        self.account_number = str(account_number)
        self.description = description
        if transaction_type == 'IN':
            self.transfer_code = transfer_code
        else:
            self.transfer_code = None
        self.status = None
        self.amount = amount
        self.note = None
        self.orderid = None
        self.scode = None
        self.incomingorderid = None

    def __dict__(self) -> dict:
        return {
            'transaction_number': self.transaction_number,
            'transaction_date': self.transaction_date,
            'transaction_type': self.transaction_type,
            'account_number': self.account_number,
            'description': self.description,
            'transfer_code': self.transfer_code,
            'status': self.status,
            'amount': self.amount,
            'note': self.note,
            'orderid': self.orderid,
            'scode': self.scode,
            'incomingorderid': self.incomingorderid
        }


def send_telegram_message(message: str, chat_id, api_key):
    try:
        bot = Bot(token=api_key)
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',  # Use 'Markdown' or 'HTML' depending on your message format
            disable_notification=False  # Set True to send silently
        )
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")


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
    pattern = r'[Zz].{6}'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None


def unix_to_datetime(unix_time):
    # Convert Unix time to datetime with UTC timezone
    dt_utc = datetime.utcfromtimestamp(unix_time / 1000).replace(tzinfo=pytz.utc)
    # Convert to GMT+7
    dt_gmt_plus_7 = dt_utc.astimezone(pytz.timezone('Asia/Bangkok'))
    # Format the datetime
    formatted_dt = dt_gmt_plus_7.strftime('%d/%m/%Y %H:%M:%S')
    return formatted_dt

def format_transaction_list(transaction_list):
    for transaction in transaction_list:
        for key, value in transaction.items():
            if value is None:
                transaction[key] = ''
    return transaction_list

def get_today_date():
    today = datetime.now()
    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_date, end_date
