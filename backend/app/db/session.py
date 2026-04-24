from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.mysql_url, echo=False, pool_size=30, max_overflow=60
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


def get_async_session_ctx():
    """Return an async context manager for single-use database sessions.

    Ensures rollback on exception and proper cleanup.
    """

    class AsyncSessionCtx:
        def __init__(self):
            self._session = None
            self._exc_info = None

        async def __aenter__(self):
            self._session = async_session()
            await self._session.__aenter__()
            return self._session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type is not None:
                    await self._session.rollback()
                else:
                    await self._session.commit()
            except Exception:
                try:
                    await self._session.rollback()
                except Exception:
                    pass
                raise
            finally:
                await self._session.close()

    return AsyncSessionCtx()
