<<<<<<< HEAD
<<<<<<< HEAD
"""Database session management."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
=======
"""Database session configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef

# Create async engine
engine = create_async_engine(
    settings.database_url,
<<<<<<< HEAD
    poolclass=NullPool,
    echo=settings.debug,
=======
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
=======
"""Database session and engine configuration."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Session factory
async_session_maker = async_sessionmaker(
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
<<<<<<< HEAD
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
=======
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK


async def init_db() -> None:
    """Initialize database tables."""
<<<<<<< HEAD
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
=======
>>>>>>> origin/claude/auth-security-jwt-01NGdma4oBRc5QyZNZQsX6Ef
=======
    from app.db.base import Base
    # Import all models to register them
    from app.models import activity  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
