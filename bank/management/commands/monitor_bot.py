from django.core.management.base import BaseCommand
from bank.utils import send_telegram_message
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.views import get_env
from datetime import timezone
from django.contrib.auth.models import User
from employee.models import EmployeeWorkingSession
from asgiref.sync import sync_to_async

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        await update.message.reply_text(
            "Nhập thông tin sai. Mẫu: start username số dư hiện tại\nVí dụ:\n/start admin 12345"
        )
        return

    username = args[0]
    if username.isdigit() or username.isdecimal():
         await update.message.reply_text(
            f"Sai tên đăng nhập"
        )

    start_balance = args[1]
    if not start_balance.isdigit():
        await update.message.reply_text(
            f"Sai số dư "
        )
        return
    
    employee = await sync_to_async(lambda: User.objects.filter(username=username).first())()
    undone_session = await sync_to_async(lambda:EmployeeWorkingSession.objects.filter(user=employee, status=False).first())()
    if undone_session:
            update.message.reply_text('Bạn đang trong phiên làm việc. Không thể bắt đầu')
    else:
        start_time = timezone.now()
        EmployeeWorkingSession.objects.create(
            user=employee,
            start_time=start_time,  
            start_balance=start_balance
        )
        await update.message.reply_text(
            f"Nhân viên: {employee.username}\nGiờ bắt đầu: {start_time}\n Số dư bắt đầu: {start_balance}\n"
        )

class Command(BaseCommand):
    help = 'Session Bot Management'

    def handle(self, *args, **kwargs):
        app = Application.builder().token(get_env('MONITORING_BOT_2_API_KEY')).build()
        app.add_handler(CommandHandler('start', start))
        self.stdout.write('Bot running...')
        app.run_polling()
