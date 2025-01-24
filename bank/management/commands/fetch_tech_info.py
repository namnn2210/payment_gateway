from django.core.management.base import BaseCommand
from bank.models import BankAccount
import time
from config.views import get_env
from worker.views import get_balance
from bank.utils import send_telegram_message
from datetime import datetime, timedelta
from django.utils import timezone
from tech.views import tech_login
import pytz
import asyncio


class Command(BaseCommand):
    help = 'Get all bank transaction history to redis'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting bank transaction history fetcher...'))

        while True:
            # Get all active bank accounts
            bank_accounts = BankAccount.objects.filter(bank_name=3, status=True)

            for bank in bank_accounts:
                try:
                    if bank.bank_name.name == "Techcombank":
                        six_hours_ago = timezone.now() - timedelta(hours=6)

                        if bank.last_logged_in is None or bank.last_logged_in <= six_hours_ago:
                            # Await the login asynchronously
                            tech_success = asyncio.run(self.async_tech_login(bank))
                            if tech_success:
                                self.stdout.write(self.style.SUCCESS(f'Logged in as {bank.username} successfully'))
                                bank.last_logged_in = timezone.now()
                                bank.save()
                    # Get balance (keeping synchronous)
                    get_balance(bank=bank)

                except Exception as ex:
                    alert = (
                        f'🔴 - SYSTEM ALERT\n'
                        f'Fetch Techcombank bank info error: {str(ex)}\n'
                        f'Date: {datetime.now(pytz.timezone("Asia/Singapore"))}'
                    )
                    try:
                        send_telegram_message(alert, get_env('MONITORING_CHAT_ID'), get_env('MONITORING_BOT_2_API_KEY'))
                    except Exception as ex:
                        print(str(ex))
                    self.stdout.write(self.style.ERROR(f"Error processing {bank.username}: {str(ex)}"))

            time.sleep(15)

    async def async_tech_login(self, bank):
        """Asynchronous wrapper for tech_login."""
        return await tech_login(bank.username, bank.password)
