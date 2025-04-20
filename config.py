import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL") + "?prepared_statement_cache_size=0"

SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER"),
    "port": int(os.getenv("SMTP_PORT", 587)),
    "username": os.getenv("SMTP_USERNAME"),
    "password": os.getenv("SMTP_PASSWORD"),
    "sender_email": os.getenv("SMTP_USERNAME"),
}
