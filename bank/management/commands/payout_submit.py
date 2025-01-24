from django.core.management.base import BaseCommand
from payout.models import Payout
from partner.views import update_status_request
from bank.utils import send_telegram_message
from datetime import datetime, time as datetime_time
from config.views import get_env
import pytz
import time
import random


class Command(BaseCommand):
    help = 'Submit payout'

    def handle(self, *args, **kwargs):
        while True:
            self.stdout.write(self.style.NOTICE('Fetching pending payouts...'))
            start_date = datetime.combine(datetime.now().date(), datetime_time.min)
            pending_payouts = Payout.objects.filter(partner_status=False,created_at__gte=start_date)
            for payout in pending_payouts:
                try:
                    if update_status_request(payout=payout, status='S'):
                        current_state_payout = Payout.objects.get(id=payout.id)
                        print(current_state_payout.orderid)
                        current_state_payout.partner_status = True
                        current_state_payout.save()
                except Exception as ex:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Submit payout error: {str(ex)}\n'
                        f'Date: {datetime.now(pytz.timezone('Asia/Singapore'))}'
                    )
                    send_telegram_message(alert, get_env('MONITORING_CHAT_ID'),
                                          get_env('MONITORING_BOT_2_API_KEY'))
            time.sleep(15)
