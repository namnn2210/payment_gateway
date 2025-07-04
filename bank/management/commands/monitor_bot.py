from django.core.management.base import BaseCommand
from bank.utils import send_telegram_message
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.views import get_env
from django.utils import timezone
from django.contrib.auth.models import User
from employee.models import EmployeeWorkingSession
from asgiref.sync import sync_to_async

from asgiref.sync import sync_to_async
from django.utils import timezone

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "Nhập thông tin sai. Mẫu: start username số dư hiện tại\nVí dụ:\n/start admin 12345"
        )
        return

    username = args[0]
    if username.isdigit() or username.isdecimal():
        await update.message.reply_text("Sai tên đăng nhập")
        return

    start_balance = args[1]
    if not start_balance.isdigit():
        await update.message.reply_text("Sai số dư")
        return

    start_balance_int = int(start_balance)

    employee = await sync_to_async(lambda: User.objects.filter(username=username).first())()
    if not employee:
        await update.message.reply_text(f"Không tìm thấy nhân viên có username '{username}'.")
        return

    undone_session = await sync_to_async(
        lambda: EmployeeWorkingSession.objects.filter(user=employee, status=False).first()
    )()

    if undone_session:
        await update.message.reply_text('Bạn đang trong phiên làm việc. Không thể bắt đầu')
        return

    
    start_time = timezone.now()
    await sync_to_async(EmployeeWorkingSession.objects.create)(
        user=employee,
        start_time=start_time,
        start_balance=start_balance_int
    )

    await update.message.reply_text(
        f"Nhân viên: {employee.username}\nGiờ bắt đầu: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\nSố dư bắt đầu: {start_balance_int}"
    )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    # 1️⃣ Kiểm tra đủ tham số
    if len(args) < 2:
        await update.message.reply_text(
            "Nhập thông tin sai. Mẫu: deposit username số tiền nạp\nVí dụ:\n/in admin 5000"
        )
        return

    username = args[0]
    amount_str = args[1]

    if username.isdigit() or username.isdecimal():
        await update.message.reply_text("Sai tên đăng nhập")
        return

    if not amount_str.isdigit():
        await update.message.reply_text("Sai số tiền nạp")
        return

    amount = int(amount_str)

    user = await sync_to_async(lambda: User.objects.filter(username=username).first())()
    if not user:
        await update.message.reply_text(f"Không tìm thấy nhân viên '{username}'.")
        return

    session = await sync_to_async(
        lambda: EmployeeWorkingSession.objects.filter(user=user, status=False).first()
    )()

    if not session:
        await update.message.reply_text(
            f"Nhân viên '{username}' hiện không có phiên làm việc đang mở."
        )
        return

    session.deposit += amount
    await sync_to_async(session.save)()

    await update.message.reply_text(
        f"Đã nạp thành công cho {username}.\nSố tiền vừa nạp: {amount}\nTổng nạp hiện tại: {session.deposit}"
    )

class Command(BaseCommand):
    help = 'Session Bot Management'

    def handle(self, *args, **kwargs):
        app = Application.builder().token(get_env('MONITORING_BOT_2_API_KEY')).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('in', deposit))
        self.stdout.write('Bot running...')
        app.run_polling()
