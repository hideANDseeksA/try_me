from datetime import datetime
import pytz

def format_datetime(dt: datetime, timezone: str = "Asia/Manila") -> str:
    return dt.astimezone(pytz.timezone(timezone)).strftime("%A, %B %d, %Y, %I:%M %p")
