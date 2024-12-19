from django.core.management.base import BaseCommand
from payout.models import Payout
from partner.views import update_status_request
from bank.utils import send_telegram_message
from datetime import datetime
from config.views import get_env
import pytz
import time
import random


class Command(BaseCommand):
    help = 'Submit payout'

    def handle(self, *args, **kwargs):
        while True:
            self.stdout.write(self.style.NOTICE('Fetching pending payouts...'))
            pending_payouts = Payout.objects.filter(status=False)
            for payout in pending_payouts:
                try:
                    sleep_time = random.randint(1,10)
                    time.sleep(sleep_time)
                    if update_status_request(payout=payout, status='S'):
                        payout.partner_status = True
                        payout.save()
                except Exception as ex:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Submit payout error: {str(ex)}\n'
                        f'Date: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
                    )
                    send_telegram_message(alert, get_env('MONITORING_CHAT_ID'),
                                          get_env('MONITORING_BOT_API_KEY'))
            time.sleep(300)
