"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import logging
import sys

# Railway deployment: 2026-02-16

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
        "pool_size": getattr(settings, 'DB_POOL_SIZE', 5),
        "max_overflow": getattr(settings, 'DB_MAX_OVERFLOW', 10),
        "pool_timeout": getattr(settings, 'DB_POOL_TIMEOUT', 30),
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,   # Recycle connections after 1 hour
    })
    pool_size = getattr(settings, 'DB_POOL_SIZE', 5)
    max_overflow = getattr(settings, 'DB_MAX_OVERFLOW', 10)
    logger.info(f"Using PostgreSQL with connection pool (size={pool_size}, max_overflow={max_overflow})")

# Create engine with error handling
try:
    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
    logger.info(f"✓ Database engine created successfully (type: {'SQLite' if is_sqlite else 'PostgreSQL'})")
except Exception as e:
    logger.error(f"Failed to create database engine!")
    logger.error(f"DATABASE_URL scheme: {settings.DATABASE_URL.split('://')[0] if '://' in settings.DATABASE_URL else 'unknown'}")
    logger.error(f"Error: {str(e)}")
    sys.stderr.write(f"\n❌ DATABASE CONNECTION ERROR:\n")
    sys.stderr.write(f"   URL Scheme: {settings.DATABASE_URL.split('://')[0] if '://' in settings.DATABASE_URL else 'INVALID'}\n")
    sys.stderr.write(f"   Error: {str(e)}\n")
    sys.stderr.write(f"\n   Possible fixes:\n")
    sys.stderr.write(f"   1. Ensure DATABASE_URL starts with 'postgresql+asyncpg://' (not 'postgresql://' or 'postgres://')\n")
    sys.stderr.write(f"   2. Check if password contains special characters - they need URL encoding\n")
    sys.stderr.write(f"   3. Verify database credentials are correct\n\n")
    raise

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
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
