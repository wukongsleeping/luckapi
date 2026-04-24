import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import get_settings


async def migrate_global_models_api_key_nullable():
    """Make api_key column nullable in global_models table."""
    settings = get_settings()
    url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT COLUMN_TYPE, IS_NULLABLE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db
            AND TABLE_NAME = 'global_models'
            AND COLUMN_NAME = 'api_key'
        """), {"db": settings.MYSQL_DATABASE})
        row = result.fetchone()

        if row and row[1] == 'YES':
            print("✓ api_key column is already nullable")
            await engine.dispose()
            return

        await conn.execute(text("""
            ALTER TABLE global_models
            MODIFY COLUMN api_key VARCHAR(500) NULL
        """))

    print("✓ api_key column in global_models is now nullable")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(migrate_global_models_api_key_nullable())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
