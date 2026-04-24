import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import get_settings


async def create_group_tables():
    """Create the groups and group_users tables."""
    settings = get_settings()
    url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_async_engine(url, echo=False)
    
    async with engine.begin() as conn:
        # Check if groups table already exists
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = :db 
            AND TABLE_NAME = 'groups'
        """), {"db": settings.MYSQL_DATABASE})
        
        if result.scalar_one() > 0:
            print("✓ Groups tables already exist")
            await engine.dispose()
            return
        
        # Create groups table (use backticks - MySQL reserved word)
        await conn.execute(text("""
            CREATE TABLE `groups` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                model_api_key VARCHAR(500) NULL,
                model_name VARCHAR(100) NULL,
                model_url VARCHAR(500) NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at DATETIME NOT NULL DEFAULT NOW(),
                updated_at DATETIME NOT NULL DEFAULT NOW(),
                UNIQUE KEY uk_groups_name (name),
                INDEX idx_groups_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        
        # Create group_users table
        await conn.execute(text("""
            CREATE TABLE group_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT NOT NULL,
                user_id INT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                assigned_at DATETIME NOT NULL DEFAULT NOW(),
                FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY uk_group_user (group_id, user_id),
                INDEX idx_group_users_group_id (group_id),
                INDEX idx_group_users_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        
    print("✓ Created tables: groups, group_users")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_group_tables())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
