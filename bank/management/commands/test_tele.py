from django.core.management.base import BaseCommand
from bank.utils import send_telegram_qr
from config.views import get_env
class Command(BaseCommand):
    help = 'Test Telegram'

    def handle(self, *args, **kwargs):
        alert = 'haha'
        send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002287492730','https://placehold.co/128/png',alert)
