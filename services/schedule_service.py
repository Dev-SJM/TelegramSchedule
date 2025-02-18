from datetime import datetime
import logging
from typing import List, Optional
from config import Config
from models.schedule import Schedule
from services.date_service import DateService
from services.storage_service import StorageService

class ScheduleService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        self.schedules = self.storage_service.load_schedules()
        self.cleanup_old_schedules()  # 초기화할 때 지난 일정 정리

    def cleanup_old_schedules(self) -> None:
        """지난 일정 정리"""
        now = datetime.now(Config.TIMEZONE)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        any_changes = False
        for chat_id in self.schedules:
            # 현재 시간 이후의 일정만 필터링
            current_schedules = [
                schedule for schedule in self.schedules[chat_id]
                if schedule.datetime.astimezone(Config.TIMEZONE) >= today_start
            ]
            
            # 일정이 필터링되었다면 변경사항 있음
            if len(current_schedules) != len(self.schedules[chat_id]):
                self.schedules[chat_id] = current_schedules
                any_changes = True
        
        # 변경사항이 있는 경우에만 저장
        if any_changes:
            self.storage_service.save_schedules(self.schedules)
            logging.info("지난 일정이 정리되었습니다.")

    def add_schedule(self, chat_id: str, schedule: Schedule) -> None:
        """일정 추가 및 저장"""
        if chat_id not in self.schedules:
            self.schedules[chat_id] = []
        self.schedules[chat_id].append(schedule)
        self.cleanup_old_schedules()  # 새 일정 추가할 때마다 정리
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
        
        filtered_schedules = []
        for schedule in schedules:
            # 일정의 datetime을 현지 시간대로 변환
            schedule_dt = schedule.datetime.astimezone(Config.TIMEZONE)
            if start_date <= schedule_dt <= end_date:
                filtered_schedules.append(schedule)
                
        return filtered_schedules
    
    def get_schedule_by_index(self, chat_id: str, display_index: int) -> Optional[Schedule]:
        """표시 인덱스로 일정 조회 (1부터 시작)"""
        schedules = self.get_schedules(chat_id)
        actual_index = display_index - 1  # 실제 인덱스로 변환
        if 0 <= actual_index < len(schedules):
            return schedules[actual_index]
        return None

    def delete_schedule(self, chat_id: str, display_index: int) -> bool:
        """일정 삭제 (1부터 시작하는 인덱스 사용)"""
        if chat_id not in self.schedules:
            return False
        
        actual_index = display_index - 1  # 실제 인덱스로 변환
        if 0 <= actual_index < len(self.schedules[chat_id]):
            self.schedules[chat_id].pop(actual_index)
            self.storage_service.save_schedules(self.schedules)
            return True
        return False

    def edit_schedule(self, chat_id: str, display_index: int, new_schedule: Schedule) -> bool:
        """일정 수정 (1부터 시작하는 인덱스 사용)"""
        if chat_id not in self.schedules:
            return False
        
        actual_index = display_index - 1  # 실제 인덱스로 변환
        if 0 <= actual_index < len(self.schedules[chat_id]):
            self.schedules[chat_id][actual_index] = new_schedule
            self.storage_service.save_schedules(self.schedules)
            return True
        return False

    def list_schedules(self, chat_id: str) -> str:
        """일정 목록 표시 (1부터 시작하는 인덱스)"""
        schedules = self.get_schedules(chat_id)
        if not schedules:
            return "등록된 일정이 없습니다."

        message = "📋 전체 일정 목록:\n\n"
        for i, schedule in enumerate(schedules, 1):  # 1부터 시작하는 인덱스
            dt = schedule.datetime.astimezone(Config.TIMEZONE)
            time_str = dt.strftime('%Y-%m-%d %H:%M')
            if schedule.end_time:
                end_time = schedule.end_time.astimezone(Config.TIMEZONE)
                time_str += f" ~ {end_time.strftime('%H:%M')}"
            message += f"{i}. {time_str} {schedule.title}\n"
        
        message += "\n💡 일정 삭제: /delete [번호]\n💡 일정 수정: /edit [번호] [날짜] [시간] [제목]"
        return message