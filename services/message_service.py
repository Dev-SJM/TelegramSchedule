from datetime import datetime, timedelta
from typing import List, Dict
from models.schedule import Schedule
from config import Config

class MessageService:
    @staticmethod
    def format_weekly_schedule(schedules: List[Schedule], start_date: datetime) -> str:
        """주간 일정을 포맷팅"""
        if not schedules:
            return "이번 주 등록된 일정이 없습니다."

        daily_schedules: Dict[str, List[Schedule]] = {}
        week_start = start_date.astimezone(Config.TIMEZONE)
        week_end = week_start + timedelta(days=6)
        week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        for schedule in sorted(schedules, key=lambda x: x.datetime):
            schedule_date = schedule.datetime.astimezone(Config.TIMEZONE)
            if week_start <= schedule_date <= week_end:
                date_str = schedule_date.strftime('%Y-%m-%d (%a)')
                for eng, kor in Config.WEEKDAY_MAP.items():
                    date_str = date_str.replace(f'({eng})', f'({kor})')
                
                if date_str not in daily_schedules:
                    daily_schedules[date_str] = []
                daily_schedules[date_str].append(schedule)

        if not daily_schedules:
            return "이번 주 등록된 일정이 없습니다."

        message = f"📅 {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')} 주간 일정\n\n"
        
        for date, day_schedules in daily_schedules.items():
            message += f"📌 {date}\n"
            for schedule in day_schedules:
                schedule_time = schedule.datetime.astimezone(Config.TIMEZONE)
                time_str = schedule_time.strftime('%H:%M')
                if schedule.end_time:
                    end_time = schedule.end_time.astimezone(Config.TIMEZONE)
                    time_str = f"{time_str} ~ {end_time.strftime('%H:%M')}"
                message += f"    ⌚️ {time_str} {schedule.title}\n"
            message += "\n"

        return message