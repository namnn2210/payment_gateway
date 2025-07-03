from django.core.management.base import BaseCommand
from bank.utils import send_telegram_qr, send_telegram_message
from config.views import get_env


class Command(BaseCommand):
    help = 'Test Telegram'

    def handle(self, *args, **kwargs):
        alert = 'haha'
        msg = {
            "chat_id": "-1002287492730",
            "text": "aaa",
            "parse_mode": "HTML",
            "disable_notification": False
        }
        send_telegram_message(alert, '-1002287492730',
                         get_env('MONITORING_BOT_2_API_KEY'))
