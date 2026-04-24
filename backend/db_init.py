import asyncio
import sys
import os
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, text
from app.db.session import get_async_session_ctx, Base
from app.models.models import User, ApiKey, UserModel, GlobalModel
from app.core.config import get_settings
from app.core.security import hash_password


DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


async def init_db():
    settings = get_settings()
    
    # Connect to mysql (without specifying database)
    base_url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/"
    engine = create_async_engine(base_url, echo=False)
    
    try:
        # Create database if not exists
        async with engine.begin() as conn:
            await conn.execute(
                text(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} "
                     "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
        print("✓ Database created")
        
        # Create tables with the database-specific URL
        db_url = settings.mysql_url
        table_engine = create_async_engine(db_url, echo=False)
        
        async with table_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await table_engine.dispose()
        print("✓ Tables created: users, api_keys, user_models")
        print(f"  Database: {settings.MYSQL_DATABASE}")
        
        # Create default admin user if not exists
        async with get_async_session_ctx() as db_session:
            existing = await db_session.execute(
                select(User).where(User.username == DEFAULT_USERNAME)
            )
            if not existing.scalar_one_or_none():
                user = User(
                    username=DEFAULT_USERNAME,
                    display_name="Administrator",
                    password_hash=hash_password(DEFAULT_PASSWORD),
                    role="admin",
                    balance=999999,
                )
                db_session.add(user)
                await db_session.commit()
                await db_session.refresh(user)
                
                api_key = "sk-" + secrets.token_hex(24)
                key_obj = ApiKey(
                    user_id=user.id,
                    key=api_key,
                    name="admin key",
                )
                db_session.add(key_obj)
                await db_session.commit()
                print(f"√ Default admin user created")
                print(f"  Username: {DEFAULT_USERNAME}")
                print(f"  Password: {DEFAULT_PASSWORD}")
                print(f"  API Key:  {api_key}")
                print(f"  ⚠ 首次登录后请立即修改密码！")
            else:
                print("ℹ Default admin user already exists, skipping")
        
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)
