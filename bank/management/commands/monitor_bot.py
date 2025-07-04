from django.core.management.base import BaseCommand
from bank.utils import send_telegram_message
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.views import get_env
from django.utils import timezone
from django.contrib.auth.models import User
from employee.models import EmployeeWorkingSession
from asgiref.sync import sync_to_async
from payout.models import Payout
from settle_payout.models import SettlePayout
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime

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
        f"Nhân viên: {employee.username}\nGiờ bắt đầu: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\nSố dư bắt đầu: {start_balance_int:,}"
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
        f"Đã nạp thành công cho {username}.\nSố tiền vừa nạp: {amount:,}\nTổng nạp hiện tại: {session.deposit:,}"
    )

from asgiref.sync import sync_to_async
from django.utils import timezone

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "Nhập thông tin sai. Mẫu: end username số dư cuối\nVí dụ:\n/end admin 54321"
        )
        return

    username = args[0]
    end_balance_str = args[1]

    if username.isdigit() or username.isdecimal():
        await update.message.reply_text("Sai tên đăng nhập")
        return

    if not end_balance_str.isdigit():
        await update.message.reply_text("Sai số dư cuối")
        return

    end_balance = int(end_balance_str)

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

    session.end_time = timezone.now()

    # ✅ Dùng datetime object trực tiếp khi filter
    list_payout = await sync_to_async(lambda: list(
        Payout.objects.filter(
            user=user, 
            created_at__gte=session.start_time, 
            created_at__lte=session.end_time, 
            status=True
        )
    ))()

    list_settle = await sync_to_async(lambda: list(
        SettlePayout.objects.filter(
            user=user, 
            created_at__gte=session.start_time, 
            created_at__lte=session.end_time, 
            status=True
        )
    ))()

    # ✅ Tính tổng bằng Python, không cần await
    session.total_payout = len(list_payout)
    session.total_amount_payout = sum(p.money for p in list_payout)
    session.total_settle = len(list_settle)
    session.total_amount_settle = sum(p.money for p in list_settle)

    session.end_balance = end_balance
    session.status = True

    await sync_to_async(session.save)()

    amount_left = session.start_balance + session.deposit - session.total_amount_payout - session.total_amount_settle

    # ✅ Định dạng giờ để hiển thị
    start_datetime_str = session.start_time.strftime('%Y-%m-%d %H:%M')
    end_datetime_str = session.end_time.strftime('%Y-%m-%d %H:%M')

    amount_different = end_balance - amount_left

    await update.message.reply_text(
        f"Tổng kết {username}\n"
        f"Giờ bắt đầu: {start_datetime_str}\n"
        f"Giờ kết thúc: {end_datetime_str}\n"
        f"==================================\n"
        f"Payout: {session.total_payout}\n"
        f"Tổng tiền: {session.total_amount_payout:,}\n"
        f"Settle: {session.total_settle}\n"
        f"Tổng tiền: {session.total_amount_settle:,}\n"
        f"==================================\n"
        f"Số dư còn lại dự tính: {amount_left:,}\n"
        f"Số dư: {end_balance:,}\n"
        f"Lệch: {amount_different:,}"
        f"Vui lòng kiểm tra số dư\n"
        f"-----------END SESSION-----------"
    )

class Command(BaseCommand):
    help = 'Session Bot Management'

    def handle(self, *args, **kwargs):
        app = Application.builder().token(get_env('MONITORING_BOT_2_API_KEY')).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('in', deposit))
        app.add_handler(CommandHandler('end', end))
        self.stdout.write('Bot running...')
        app.run_polling()
