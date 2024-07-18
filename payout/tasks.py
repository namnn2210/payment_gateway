# worker/tasks.py

from payment_gateway.celery import app
from datetime import datetime
import pytz

@app.task
def print_payout(payout):
    print(payout)

@app.task
def print_current_time():
    tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(tz)
    print(f'Current time in UTC+7: {current_time}')
