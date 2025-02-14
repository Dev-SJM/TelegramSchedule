from dotenv import load_dotenv
import os
import pytz

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TIMEZONE = pytz.timezone('Asia/Seoul')
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M"
    DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"

    WEEKDAY_MAP = {
        'Mon': '월',
        'Tue': '화',
        'Wed': '수',
        'Thu': '목',
        'Fri': '금',
        'Sat': '토',
        'Sun': '일'
    }