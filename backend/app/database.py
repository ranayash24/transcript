from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from functools import lru_cache
from .config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def get_session_factory():
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with get_session_factory()() as session:
        yield session
