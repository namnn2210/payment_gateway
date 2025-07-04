from django.core.management.base import BaseCommand
from bank.utils import send_telegram_message
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.views import get_env

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am your Django Telegram Bot.')

class Command(BaseCommand):
    help = 'Session Bot Management'

    def handle(self, *args, **kwargs):
        app = Application.builder().token('MONITORING_BOT_2_API_KEY').build()
        app.add_handler(CommandHandler('start', start))
        self.stdout.write('Bot running...')
        app.run_polling()
