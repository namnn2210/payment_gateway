from django.core.management.base import BaseCommand
from bank.utils import send_telegram_qr
from config.views import get_env
class Command(BaseCommand):
    help = 'Test Telegram'

    def handle(self, *args, **kwargs):
        alert = 'haha'
        send_telegram_qr(get_env('MONITORING_BOT_2_API_KEY'), '-1002287492730','https://img.vietqr.io/image/vietinbank-113366668888-compact2.jpg?amount=790000&addInfo=dong%20gop%20quy%20vac%20xin&accountName=Quy%20Vac%20Xin%20Covid',alert)
