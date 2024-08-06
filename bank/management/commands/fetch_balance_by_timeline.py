from django.core.management.base import BaseCommand
from bank.models import BankAccount
from worker.views import get_balance_by_bank
from dotenv import load_dotenv
from bank.utils import send_telegram_message
from datetime import datetime, time
from payout.models import Timeline, UserTimeline, BalanceTimeline
import pytz


load_dotenv()


class Command(BaseCommand):
    help = 'Get Balance By Timeline'

    def handle(self, *args, **kwargs):
        try:
            print('Get Balance By Timeline')
            timezone = pytz.timezone('Asia/Bangkok')
            current_time = datetime.now(timezone).time()
            print('Current datetime:', current_time)
            current_timeline_name = None
            current_user_timelines = []
            
            # Checking current online users
            timelines = [
                {'name': 'Sáng', 'start_at': time(6, 0), 'end_at': time(14, 0)},
                {'name': 'Chiều', 'start_at': time(14, 0), 'end_at': time(22, 0)},
                {'name': 'Tối', 'start_at': time(22, 0), 'end_at': time(23, 59, 59)},
                {'name': 'Đêm', 'start_at': time(0, 0), 'end_at': time(6, 0)}
            ]
            
            for timeline in timelines:
                start_at = timeline['start_at']
                end_at = timeline['end_at']

                if start_at <= end_at:
                    if start_at <= current_time <= end_at:
                        current_timeline_name = timeline['name']
                        break
                else:  
                    if current_time >= start_at or current_time <= end_at:
                        current_timeline_name = timeline['name']
                        break
            
            if current_timeline_name:
                # Get the active timelines from the database
                if current_timeline_name == 'Tối' or current_timeline_name == 'Đêm':
                    current_timeline_name = 'Đêm'
                active_timeline = Timeline.objects.filter(status=True, name=current_timeline_name).first()
                
                current_user_timelines = list(UserTimeline.objects.filter(timeline=active_timeline, status=True))
                
            if current_user_timelines:
                for user_timeline in current_user_timelines:
                    bank_account = BankAccount.objects.filter(user=user_timeline.user).first()
                    balance = get_balance_by_bank(bank=bank_account)
                    BalanceTimeline.objects.create(
                      timeline=user_timeline.timeline,
                      bank_account=bank_account,
                      balance=balance  
                    )
        except Exception as ex:
            alert = (
                f'🔴 - LỖI HỆ THỐNG\n'
                f'Lỗi thông báo fetch balance by timeline: {str(ex)}\n'
                f'Thời gian: {datetime.now(pytz.timezone('Asia/Bangkok'))}'
            )
            send_telegram_message(alert, os.environ.get('MONITORING_CHAT_ID'), os.environ.get('MONITORING_BOT_API_KEY'))