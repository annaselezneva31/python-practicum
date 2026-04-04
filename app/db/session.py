from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass

_engine = None
_AsyncSessionMaker = None

def get_engine():
    global _engine, _AsyncSessionMaker
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, future=True)
        _AsyncSessionMaker = async_sessionmaker(_engine, expire_on_commit=True, autoflush=True)
    return _engine, _AsyncSessionMaker

async def get_session() -> AsyncIterator[AsyncSession]:
    _, async_session_maker = get_engine()
    async with async_session_maker() as session:
        yield session