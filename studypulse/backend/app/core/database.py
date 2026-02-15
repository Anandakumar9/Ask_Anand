"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Determine database type
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
is_postgres = settings.DATABASE_URL.startswith("postgresql")

# Create async engine with appropriate settings
engine_kwargs = {
    "echo": False,  # Disable SQL logging to reduce noise
    "future": True
}

# SQLite needs connect_args for check_same_thread
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    logger.info("Using SQLite database (development mode)")

# PostgreSQL connection pooling (production)
elif is_postgres:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,   # Recycle connections after 1 hour
    })
    logger.info(f"Using PostgreSQL with connection pool (size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW})")

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error, rolling back: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
