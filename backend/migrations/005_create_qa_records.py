import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import get_settings


async def create_qa_records_table():
    """Create qa_records table for saving Q&A conversation data."""
    settings = get_settings()
    url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_async_engine(url)

    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = :db 
            AND TABLE_NAME = 'qa_records'
        """), {"db": settings.MYSQL_DATABASE})

        if result.scalar_one() > 0:
            print("✓ qa_records table already exists")
            await engine.dispose()
            return

        await conn.execute(text("""
            CREATE TABLE qa_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                api_key_id INT NULL,
                target_model VARCHAR(100) NOT NULL,
                method VARCHAR(10) NOT NULL DEFAULT 'POST',
                request_body TEXT NOT NULL,
                response_body TEXT NULL,
                upstream_status INT NULL,
                request_tokens INT NULL,
                response_tokens INT NULL,
                total_tokens INT NULL,
                latency_ms INT NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'success',
                client_ip VARCHAR(45) NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_api_key_id (api_key_id),
                INDEX idx_target_model (target_model),
                INDEX idx_created_at (created_at),
                INDEX idx_status_created (status, created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

    print("✓ Created table: qa_records")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_qa_records_table())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
