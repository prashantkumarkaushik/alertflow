from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Engine — one per application, reused across all requests
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,  # checks connection is alive before using it
    echo=settings.ENVIRONMENT == "local",  # logs all SQL in local dev only
)

# Session factory — call this to get a new session
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # don't expire objects after commit
)


# Base class — all our SQLAlchemy models will inherit from this
class Base(DeclarativeBase):
    pass


# FastAPI dependency — used in routes like: db: AsyncSession = Depends(get_db)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
