import logging
from telegram.ext import Application, CommandHandler
from config import Config
from services.storage_service import StorageService
from services.schedule_service import ScheduleService
from services.message_service import MessageService
from handlers.command_handlers import CommandHandlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # 서비스 초기화
    storage_service = StorageService()
    schedule_service = ScheduleService(storage_service)
    message_service = MessageService()
    command_handlers = CommandHandlers(schedule_service, message_service)

    # 봇 애플리케이션 생성
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # 핸들러 등록
    application.add_handler(CommandHandler('start', command_handlers.start))
    application.add_handler(CommandHandler('add', command_handlers.add_schedule))
    application.add_handler(CommandHandler('week', command_handlers.show_weekly_schedule))
    application.add_handler(CommandHandler('next', command_handlers.show_next_week_schedule))
    application.add_handler(CommandHandler('clear', command_handlers.clear_schedules))
    application.add_handler(CommandHandler('list', command_handlers.list_schedules))
    application.add_handler(CommandHandler('delete', command_handlers.delete_schedule))
    application.add_handler(CommandHandler('edit', command_handlers.edit_schedule))
    application.add_handler(CommandHandler('cleanup', command_handlers.cleanup_schedules))

    # 봇 실행
    application.run_polling()

if __name__ == '__main__':
    main()