# services/date_service.py
from datetime import datetime, timedelta
from typing import Tuple, Optional
from config import Config

class DateService:
    @staticmethod
    def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
        """주의 시작일과 종료일 반환"""
        # 입력된 날짜를 현지 시간대로 변환
        local_date = date.astimezone(Config.TIMEZONE)
        
        # 주의 시작일 계산 (월요일)
        start = local_date - timedelta(days=local_date.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 주의 종료일 계산 (일요일)
        end = start + timedelta(days=6)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return start, end

    @staticmethod
    def parse_datetime(date_str: str, time_str: str) -> datetime:
        """날짜와 시간 문자열을 datetime으로 변환"""
        dt = datetime.strptime(f"{date_str} {time_str}", Config.DATETIME_FORMAT)
        return Config.TIMEZONE.localize(dt)

    @staticmethod
    def parse_datetime_range(date_str: str, time_range_str: str) -> Tuple[datetime, Optional[datetime]]:
        """날짜와 시간 범위 문자열을 파싱"""
        try:
            # 시간 문자열에서 불필요한 공백 제거
            time_range_str = ' '.join(time_range_str.split())
            
            if '~' in time_range_str:
                # 시작 시간과 종료 시간 분리
                start_time, end_time = map(str.strip, time_range_str.split('~'))
                
                # 각각 datetime으로 변환
                start_dt = DateService.parse_datetime(date_str, start_time)
                end_dt = DateService.parse_datetime(date_str, end_time)
                
                return start_dt, end_dt
            else:
                # 단일 시간인 경우
                start_dt = DateService.parse_datetime(date_str, time_range_str)
                return start_dt, None
                
        except ValueError as e:
            raise ValueError(f"잘못된 시간 형식입니다: {time_range_str}")
