import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text as sa_text, select
from app.core.config import get_settings
from app.core.encryption import encrypt_api_key, decrypt_api_key
from app.models.models import UserModel
from app.db.session import async_session as db_session

settings = get_settings()
url = f"mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
engine = create_async_engine(url, echo=False)


async def reencrypt_all_keys():
    """遍历所有 UserModel 记录，重新用当前 key 加密 api_key。

    解决：之前使用随机 Fernet key 加密，key 变更导致 decrypt_api_key 抛出 InvalidToken。
    现在 decrypt_api_key 对解密失败返回原文，但长期应以新 key 加密为准。
    """
    # 取 DB 列名（ORM 属性名 _api_key 映射到 DB 列 api_key）
    api_key_col = UserModel.__table__.c.api_key

    async with db_session() as conn:
        result = await conn.execute(select(UserModel.id, api_key_col))
        rows = result.fetchall()

    if not rows:
        print("No user_models records found.")
        await engine.dispose()
        return

    total = len(rows)
    reencrypted = 0

    async with db_session() as conn:
        for model_id, encrypted_key in rows:
            decrypted = decrypt_api_key(encrypted_key)

            # 长度 < 50 的密文大概率是明文 / 旧随机 key 密文 → 统一重新加密
            if len(encrypted_key) < 50 or decrypted == encrypted_key:
                new_encrypted = encrypt_api_key(decrypted)
                await conn.execute(
                    sa_text(
                        "UPDATE user_models SET api_key = :key WHERE id = :id"
                    ),
                    {"key": new_encrypted, "id": model_id},
                )
                reencrypted += 1
        await conn.commit()

    print(f"Re-encrypted {reencrypted} / {total} records")
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(reencrypt_all_keys())
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)
