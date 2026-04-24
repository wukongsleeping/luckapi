import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import get_settings


async def add_allowed_ips_column():
    """Add allowed_ips column to users table."""
    settings = get_settings()
    url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = :db 
            AND TABLE_NAME = 'users'
            AND COLUMN_NAME = 'allowed_ips'
        """), {"db": settings.MYSQL_DATABASE})

        if result.scalar_one() > 0:
            print("✓ allowed_ips column already exists")
            await engine.dispose()
            return

        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN allowed_ips TEXT NULL
        """))

    print("✓ Added column: allowed_ips")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(add_allowed_ips_column())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
