from typing import Optional
from redis.asyncio import Redis
from app.core.config import get_settings

settings = get_settings()

_redis: Optional[Redis] = None


async def get_redis() -> Optional[Redis]:
    global _redis
    if _redis is None:
        _redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
