from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.errors import AppError


@lru_cache
def get_engine() -> AsyncEngine | None:
    settings = get_settings()
    if not settings.database_url:
        return None
    return create_async_engine(settings.database_url, pool_pre_ping=True)


async def get_session() -> AsyncIterator[AsyncSession]:
    engine = get_engine()
    if engine is None:
        raise AppError(503, "Database belum dikonfigurasi")
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
