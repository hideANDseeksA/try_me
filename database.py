import asyncpg
from config import SUPABASE_DB_URL

async def get_db():
    conn = await asyncpg.connect(SUPABASE_DB_URL, statement_cache_size=0)  # Disable statement cache
    try:
        yield conn
    finally:
        await conn.close()
