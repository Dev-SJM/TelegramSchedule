from datetime import datetime
from typing import List
from models.schedule import Schedule
from services.date_service import DateService
from services.storage_service import StorageService

class ScheduleService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        self.schedules = self.storage_service.load_schedules()

    def add_schedule(self, chat_id: str, schedule: Schedule) -> None:
        """일정 추가 및 저장"""
        if chat_id not in self.schedules:
            self.schedules[chat_id] = []
        self.schedules[chat_id].append(schedule)
        self.storage_service.save_schedules(self.schedules)

    def get_schedules(self, chat_id: str) -> List[Schedule]:
        """특정 채팅방의 모든 일정 조회"""
        return self.schedules.get(chat_id, [])

    def clear_schedules(self, chat_id: str) -> None:
        """특정 채팅방의 모든 일정 초기화 및 저장"""
        self.schedules[chat_id] = []
        self.storage_service.save_schedules(self.schedules)

    def get_week_schedules(self, chat_id: str, base_date: datetime) -> List[Schedule]:
        """특정 주의 일정만 필터링"""
        start_date, end_date = DateService.get_week_range(base_date)
        schedules = self.get_schedules(chat_id)
        
        # timezone 설정이 있는 datetime을 naive datetime으로 변환
        start_date = start_date.replace(tzinfo=None)
        end_date = end_date.replace(tzinfo=None)
        
        filtered_schedules = []
        for schedule in schedules:
            schedule_dt = schedule.datetime.replace(tzinfo=None)
            if start_date <= schedule_dt <= end_date:
                filtered_schedules.append(schedule)
                
        return filtered_schedules