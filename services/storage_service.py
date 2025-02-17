# services/storage_service.py
import json
import os
from datetime import datetime
from typing import Dict, List
from models.schedule import Schedule
from config import Config

class StorageService:
    def __init__(self, file_path: str = "data/schedules.json"):
        # data 디렉토리에 저장하도록 경로 수정
        self.file_path = file_path
        self.ensure_storage_file()

    def ensure_storage_file(self) -> None:
        """스토리지 파일과 디렉토리가 없으면 생성"""
        # 디렉토리 생성
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # 파일이 없으면 생성
        if not os.path.exists(self.file_path):
            self.save_schedules({})

    def datetime_to_str(self, dt: datetime) -> str:
        """datetime 객체를 문자열로 변환"""
        return dt.isoformat() if dt else None

    def str_to_datetime(self, dt_str: str) -> datetime:
        """문자열을 datetime 객체로 변환"""
        return datetime.fromisoformat(dt_str) if dt_str else None

    def serialize_schedule(self, schedule: Schedule) -> Dict:
        """Schedule 객체를 JSON 직렬화 가능한 형태로 변환"""
        return {
            'title': schedule.title,
            'datetime': self.datetime_to_str(schedule.datetime),
            'end_time': self.datetime_to_str(schedule.end_time)
        }

    def deserialize_schedule(self, data: Dict) -> Schedule:
        """JSON 데이터를 Schedule 객체로 변환"""
        return Schedule(
            title=data['title'],
            datetime=self.str_to_datetime(data['datetime']),
            end_time=self.str_to_datetime(data['end_time'])
        )

    def load_schedules(self) -> Dict[str, List[Schedule]]:
        """저장된 모든 일정 불러오기"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    chat_id: [self.deserialize_schedule(s) for s in schedules]
                    for chat_id, schedules in data.items()
                }
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"Warning: {self.file_path} is corrupted. Creating new file.")
            return {}

    def save_schedules(self, schedules: Dict[str, List[Schedule]]) -> None:
        """모든 일정 저장"""
        # 디렉토리가 존재하는지 다시 한번 확인
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        data = {
            chat_id: [self.serialize_schedule(s) for s in chat_schedules]
            for chat_id, chat_schedules in schedules.items()
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)