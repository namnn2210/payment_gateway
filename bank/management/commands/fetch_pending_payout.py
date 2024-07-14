from django.core.management.base import BaseCommand
from payout.models import Payout
import time
from dotenv import load_dotenv
from bank.utils import send_telegram_message
from datetime import datetime
import pytz
import os

load_dotenv()


class Command(BaseCommand):
    help = 'Alert pending payouts'

    def handle(self, *args, **kwargs):
        while True:
            # Get all active bank accounts
            try:
                pending_payout = Payout.objects.filter(status=False)
                if len(pending_payout) > 0:
                    pass
                time.sleep(600)
            except Exception as ex:
                alert = (
                    f'🔴 - LỖI HỆ THỐNG\n'
                    f'Lỗi thông báo payout: {str(ex)}\n'
                    f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
                )
                send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))