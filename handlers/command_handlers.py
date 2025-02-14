import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from config import Config
from services.schedule_service import ScheduleService
from services.message_service import MessageService
from services.date_service import DateService
from models.schedule import Schedule

class CommandHandlers:
    def __init__(self, schedule_service: ScheduleService, message_service: MessageService):
        self.schedule_service = schedule_service
        self.message_service = message_service

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = (
            "안녕하세요! 주간 일정 관리 봇입니다.\n\n"
            "📌 명령어 목록:\n"
            "/add [날짜] [시간] [일정] - 일정 추가\n"
            "예시: /add 2024-02-14 15:00 팀 미팅\n\n"
            "/week - 이번 주 일정 보기\n"
            "/next - 다음 주 일정 보기\n"
            "/clear - 모든 일정 초기화\n\n"
            "💡 일정을 추가하면 자동으로 주간 일정이 업데이트되고 고정됩니다!"
        )
        await update.message.reply_text(welcome_message)

    async def add_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        
        try:
            args = context.args
            if len(args) < 3:
                await update.message.reply_text(
                    "올바른 형식으로 입력해주세요.\n"
                    "예시 1: /add 2024-02-14 15:00 팀 미팅\n"
                    "예시 2: /add 2024-02-14 15:00~15:30 팀 미팅"
                )
                return

            date_str = args[0]
            time_str = args[1]
            title = ' '.join(args[2:])  # 제목에서 시간 정보 제외

            # 시간 범위 파싱
            start_dt, end_dt = DateService.parse_datetime_range(date_str, time_str)
            
            # Schedule 객체 생성 (시작 시간과 종료 시간 분리)
            schedule = Schedule(
                title=title,
                datetime=start_dt,
                end_time=end_dt
            )
            
            self.schedule_service.add_schedule(chat_id, schedule)
            
            now = datetime.now(Config.TIMEZONE)
            start_date = DateService.get_week_range(now)[0]
            current_week_schedules = self.schedule_service.get_week_schedules(chat_id, now)
            
            message = "✅ 일정이 추가되었습니다!\n\n"
            message += self.message_service.format_weekly_schedule(current_week_schedules, start_date)
            
            sent_message = await update.message.reply_text(message)
            await context.bot.pin_chat_message(
                chat_id=update.effective_chat.id,
                message_id=sent_message.message_id,
                disable_notification=True
            )

        except ValueError as e:
            await update.message.reply_text(
                f"에러: {str(e)}\n"
                "날짜: YYYY-MM-DD\n"
                "시간: HH:MM 또는 HH:MM~HH:MM"
            )
        except Exception as e:
            logging.error(f"일정 추가 중 오류 발생: {e}")
            await update.message.reply_text("일정 추가 중 오류가 발생했습니다.")

    async def show_weekly_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        now = datetime.now(Config.TIMEZONE)
        schedules = self.schedule_service.get_week_schedules(chat_id, now)
        message = self.message_service.format_weekly_schedule(
            schedules,
            DateService.get_week_range(now)[0]
        )
        await update.message.reply_text(message)

    async def show_next_week_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        next_week = datetime.now(Config.TIMEZONE) + timedelta(days=7)
        schedules = self.schedule_service.get_week_schedules(chat_id, next_week)
        message = self.message_service.format_weekly_schedule(
            schedules,
            DateService.get_week_range(next_week)[0]
        )
        await update.message.reply_text(message)

    async def clear_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        self.schedule_service.clear_schedules(chat_id)
        await update.message.reply_text("모든 일정이 초기화되었습니다.")