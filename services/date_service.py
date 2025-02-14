# services/date_service.py
from datetime import datetime, timedelta
from typing import Tuple, Optional
from config import Config

class DateService:
    @staticmethod
    def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
        """주의 시작일과 종료일 반환"""
        # 입력된 날짜의 timezone 정보 제거
        date = date.replace(tzinfo=None)
        
        start = date - timedelta(days=date.weekday())  # 월요일
        end = start + timedelta(days=6)  # 일요일
        
        start = start.replace(hour=0, minute=0)
        end = end.replace(hour=23, minute=59)
        
        return start, end

    @staticmethod
    def parse_datetime(date_str: str, time_str: str) -> datetime:
        """날짜와 시간 문자열을 datetime으로 변환"""
        dt = datetime.strptime(f"{date_str} {time_str}", Config.DATETIME_FORMAT)
        return Config.TIMEZONE.localize(dt)

    @staticmethod
    def parse_datetime_range(date_str: str, time_str: str) -> Tuple[datetime, Optional[datetime]]:
        """날짜와 시간 범위 문자열을 파싱"""
        # "20:00 ~ 21:30" 형식에서 시작 시간과 종료 시간 분리
        try:
            if '~' in time_str:
                start_time, end_time = map(str.strip, time_str.split('~'))
                start_dt = DateService.parse_datetime(date_str, start_time)
                end_dt = DateService.parse_datetime(date_str, end_time)
                return start_dt, end_dt
            else:
                start_dt = DateService.parse_datetime(date_str, time_str)
                return start_dt, None
        except ValueError as e:
            raise ValueError(f"잘못된 시간 형식입니다: {time_str}")
