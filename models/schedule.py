from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Any

@dataclass
class Schedule:
    title: str
    datetime: 'datetime'  # 문자열로 타입 힌팅
    end_time: Optional['datetime'] = None  # 문자열로 타입 힌팅

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'datetime': self.datetime,
            'end_time': self.end_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        return cls(
            title=data['title'],
            datetime=data['datetime'],
            end_time=data.get('end_time')
        )