import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import get_settings


async def add_expires_at_column():
    """Add the expires_at column to api_keys table."""
    settings = get_settings()
    url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_async_engine(url, echo=False)
    
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = :db 
            AND TABLE_NAME = 'api_keys' 
            AND COLUMN_NAME = 'expires_at'
        """), {"db": settings.MYSQL_DATABASE})
        
        has_column = result.scalar_one() > 0
        if has_column:
            print("✓ Column 'expires_at' already exists in api_keys table")
            await engine.dispose()
            return
        
        # Add the column
        await conn.execute(text("""
            ALTER TABLE api_keys 
            ADD COLUMN expires_at DATETIME NULL DEFAULT NULL 
            AFTER status
        """))
        
    print("✓ Added column 'expires_at' to api_keys table")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(add_expires_at_column())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
