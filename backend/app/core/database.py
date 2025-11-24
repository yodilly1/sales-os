"""
Database configuration and session management.

Provides SQLAlchemy async engine and session factory.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .config import settings

# Create async engine with connection pooling
# Use the guaranteed async URL from settings
database_url = settings.async_database_url

engine = create_async_engine(
    database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Enable connection health checks
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields a database session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
