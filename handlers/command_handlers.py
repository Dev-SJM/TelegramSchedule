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
                    "예시 1: /add 2025-02-14 15:00 팀 미팅\n"
                    "예시 2: /add 2025-02-14 15:00~15:30 팀 미팅\n"
                    "예시 3: /add 2025-02-14 15:00 ~ 15:30 팀 미팅"
                )
                return

            date_str = args[0]
            time_str = args[1]
            
            # 시간 범위에 '~'가 포함된 경우 처리
            if '~' in ' '.join(args[1:4]):  # 시간 부분을 더 넓게 검사
                # "12:00 ~ 14:30 제목" 형식 처리
                time_parts = []
                title_parts = []
                found_tilde = False
                
                for arg in args[1:]:
                    if '~' in arg or found_tilde:
                        time_parts.append(arg)
                        found_tilde = True
                        if len(time_parts) == 3:  # "시작시간 ~ 종료시간" 완성
                            title_parts = args[1+len(time_parts):]
                            break
                    else:
                        time_parts.append(arg)
                
                time_str = ' '.join(time_parts)
                title = ' '.join(title_parts)
            else:
                # 기존 단일 시간 형식 처리
                time_str = args[1]
                title = ' '.join(args[2:])

            # 시간 범위 파싱
            start_dt, end_dt = DateService.parse_datetime_range(date_str, time_str)
            
            # Schedule 객체 생성
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
            
            try:
                await context.bot.pin_chat_message(
                    chat_id=update.effective_chat.id,
                    message_id=sent_message.message_id,
                    disable_notification=True
                )
            except Exception as pin_error:
                logging.warning(f"메시지 고정 실패: {pin_error}")

        except ValueError as e:
            await update.message.reply_text(
                f"에러: {str(e)}\n"
                "날짜: YYYY-MM-DD\n"
                "시간: HH:MM 또는 HH:MM ~ HH:MM"
            )
        except Exception as e:
            logging.error(f"일정 추가 중 오류 발생: {e}")
            print(f"상세 에러: {str(e)}")  # 디버깅용
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

    async def list_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """전체 일정 목록 보기"""
        chat_id = str(update.effective_chat.id)
        message = self.schedule_service.list_schedules(chat_id)
        await update.message.reply_text(message)

    async def delete_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 삭제"""
        chat_id = str(update.effective_chat.id)
        
        try:
            if not context.args:
                await update.message.reply_text(
                    "삭제할 일정 번호를 입력해주세요.\n"
                    "예시: /delete 1\n"
                    "일정 목록 보기: /list"
                )
                return

            display_index = int(context.args[0])
            schedule = self.schedule_service.get_schedule_by_index(chat_id, display_index)
            
            if schedule and self.schedule_service.delete_schedule(chat_id, display_index):
                dt = schedule.datetime.astimezone(Config.TIMEZONE)
                time_str = dt.strftime('%Y-%m-%d %H:%M')
                if schedule.end_time:
                    end_time = schedule.end_time.astimezone(Config.TIMEZONE)
                    time_str += f" ~ {end_time.strftime('%H:%M')}"
                
                await update.message.reply_text(
                    f"✅ 다음 일정이 삭제되었습니다:\n"
                    f"{time_str} {schedule.title}"
                )
                
                # 주간 일정 업데이트 및 고정
                now = datetime.now(Config.TIMEZONE)
                start_date = DateService.get_week_range(now)[0]
                current_week_schedules = self.schedule_service.get_week_schedules(chat_id, now)
                
                message = self.message_service.format_weekly_schedule(current_week_schedules, start_date)
                sent_message = await update.message.reply_text(message)
                
                try:
                    await context.bot.pin_chat_message(
                        chat_id=update.effective_chat.id,
                        message_id=sent_message.message_id,
                        disable_notification=True
                    )
                except Exception as pin_error:
                    logging.warning(f"메시지 고정 실패: {pin_error}")
            else:
                await update.message.reply_text("❌ 해당 번호의 일정을 찾을 수 없습니다.")

        except ValueError:
            await update.message.reply_text("올바른 숫자를 입력해주세요.")
        except Exception as e:
            logging.error(f"일정 삭제 중 오류 발생: {e}")
            await update.message.reply_text("일정 삭제 중 오류가 발생했습니다.")

    async def edit_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일정 수정"""
        chat_id = str(update.effective_chat.id)
        
        try:
            if len(context.args) < 4:
                await update.message.reply_text(
                    "올바른 형식으로 입력해주세요.\n"
                    "예시 1: /edit 1 2025-02-14 15:00 팀 미팅\n"
                    "예시 2: /edit 1 2025-02-14 15:00~15:30 팀 미팅\n"
                    "일정 목록 보기: /list"
                )
                return

            display_index = int(context.args[0])
            date_str = context.args[1]
            time_str = context.args[2]
            title = ' '.join(context.args[3:])

            # 시간 범위 파싱
            start_dt, end_dt = DateService.parse_datetime_range(date_str, time_str)
            
            # 새 일정 생성
            new_schedule = Schedule(
                title=title,
                datetime=start_dt,
                end_time=end_dt
            )
            
            if self.schedule_service.edit_schedule(chat_id, display_index, new_schedule):
                await update.message.reply_text("✅ 일정이 수정되었습니다!")
                
                # 주간 일정 업데이트 및 고정
                now = datetime.now(Config.TIMEZONE)
                start_date = DateService.get_week_range(now)[0]
                current_week_schedules = self.schedule_service.get_week_schedules(chat_id, now)
                
                message = self.message_service.format_weekly_schedule(current_week_schedules, start_date)
                sent_message = await update.message.reply_text(message)
                
                try:
                    await context.bot.pin_chat_message(
                        chat_id=update.effective_chat.id,
                        message_id=sent_message.message_id,
                        disable_notification=True
                    )
                except Exception as pin_error:
                    logging.warning(f"메시지 고정 실패: {pin_error}")
            else:
                await update.message.reply_text("❌ 해당 번호의 일정을 찾을 수 없습니다.")

        except ValueError as e:
            await update.message.reply_text(
                f"에러: {str(e)}\n"
                "올바른 형식으로 입력해주세요.\n"
                "날짜: YYYY-MM-DD\n"
                "시간: HH:MM 또는 HH:MM~HH:MM"
            )
        except Exception as e:
            logging.error(f"일정 수정 중 오류 발생: {e}")
            await update.message.reply_text("일정 수정 중 오류가 발생했습니다.")