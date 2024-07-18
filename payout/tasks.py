from celery import shared_task
from datetime import datetime
import pytz

@shared_task
def print_payout(payout):
    print(payout)

@shared_task
def print_current_time():
    tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(tz)
    print(f'Current time in UTC+7: {current_time}')
