"""SQLAlchemy 2.0 Async Engine, Session Factory, and Resilient Connection Management."""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.core.config import settings
from app.core.retry import retry_async

logger = logging.getLogger("society.database")

# Build asyncpg connection arguments
# Note: For Supabase Supavisor / PgBouncer connection pooling, setting
# statement_cache_size=0 prevents prepared statement collisions across pooled connections.
connect_args = {
    "statement_cache_size": 0,
    "command_timeout": 30,
}

# Scalable Async Engine with connection pooling and health checks
engine = create_async_engine(
    settings.async_database_url,
    echo=(settings.ENVIRONMENT == "development_verbose"),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Proactively tests connection before handing to session
    connect_args=connect_args,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding a resilient async database session with auto-rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            logger.error(f"Database session exception encountered, rolling back: {exc}")
            await session.rollback()
            raise
        finally:
            await session.close()


@retry_async(
    max_retries=settings.DB_MAX_RETRIES,
    base_delay=settings.DB_RETRY_BASE_DELAY,
    max_delay=settings.DB_RETRY_MAX_DELAY,
)
async def check_db_health() -> bool:
    """Verifies database connectivity with exponential back-off retries."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return result.scalar() == 1
