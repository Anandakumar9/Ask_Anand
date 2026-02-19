"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import logging
import sys

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
    logger.info(f"[OK] Database engine created successfully (type: {'SQLite' if is_sqlite else 'PostgreSQL'})")
except Exception as e:
    logger.error(f"Failed to create database engine!")
    logger.error(f"DATABASE_URL scheme: {settings.DATABASE_URL.split('://')[0] if '://' in settings.DATABASE_URL else 'unknown'}")
    logger.error(f"Error: {str(e)}")
    sys.stderr.write(f"\n[ERROR] DATABASE CONNECTION ERROR:\n")
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
    """Initialize database tables and seed demo data if database is empty."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified successfully")

    # Check if database needs seeding (Railway first deployment)
    try:
        from sqlalchemy import select, func as sql_func
        from app.models.exam import Exam

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(sql_func.count(Exam.id)))
            exam_count = result.scalar()

            if exam_count == 0:
                logger.info("=" * 80)
                logger.info("EMPTY DATABASE DETECTED - STARTING AUTOMATIC SEEDING")
                logger.info("This is a first deployment - seeding comprehensive demo data")
                logger.info("=" * 80)

                # Import and run seeding function from seed_complete_demo.py
                try:
                    import sys
                    from pathlib import Path

                    # Add backend root to path
                    backend_root = Path(__file__).parent.parent.parent
                    sys.path.insert(0, str(backend_root))

                    # Import the comprehensive seeding functions
                    from seed_complete_demo import (
                        create_exams_subjects_topics,
                        create_questions,
                        create_users,
                        create_study_sessions,
                        create_mock_tests,
                        create_question_ratings
                    )

                    logger.info("Starting comprehensive data seeding...")

                    # Create exam hierarchy
                    exam_map, subject_map, topic_list = await create_exams_subjects_topics(session)

                    # Create questions
                    total_questions = await create_questions(session, topic_list)

                    # Create users
                    users = await create_users(session)

                    # Create study sessions
                    sessions = await create_study_sessions(session, users, topic_list)

                    # Create mock tests
                    tests = await create_mock_tests(session, users, topic_list)

                    # Create question ratings
                    ratings = await create_question_ratings(session, users)

                    logger.info("=" * 80)
                    logger.info("AUTOMATIC SEEDING COMPLETED - RAILWAY DEPLOYMENT READY")
                    logger.info("=" * 80)
                    logger.info(f"Summary:")
                    logger.info(f"  - Exams: {len(exam_map)}")
                    logger.info(f"  - Subjects: {len(subject_map)}")
                    logger.info(f"  - Topics: {len(topic_list)}")
                    logger.info(f"  - Questions: {total_questions}")
                    logger.info(f"  - Users: {len(users)}")
                    logger.info(f"  - Study Sessions: {len(sessions)}")
                    logger.info(f"  - Mock Tests: {len(tests)}")
                    logger.info(f"  - Question Ratings: {len(ratings)}")
                    logger.info("=" * 80)

                except Exception as seed_error:
                    logger.error("=" * 80)
                    logger.error("ERROR DURING AUTOMATIC SEEDING")
                    logger.error(f"Error: {str(seed_error)}")
                    logger.error(f"Error type: {type(seed_error).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    logger.error("=" * 80)
                    # Don't raise - let the app continue even if seeding fails
                    logger.warning("App will continue without demo data")
            else:
                logger.info(f"Database already contains {exam_count} exams - skipping automatic seeding")

            # Always ensure the test user exists (idempotent)
            try:
                from app.models.user import User
                from app.core.security import get_password_hash
                test_email = "test@studypulse.com"
                result = await session.execute(select(User).where(User.email == test_email))
                if result.scalar_one_or_none() is None:
                    test_user = User(
                        email=test_email,
                        name="Test User",
                        hashed_password=get_password_hash("Test@1234"),
                        is_active=True,
                        total_stars=0
                    )
                    session.add(test_user)
                    await session.commit()
                    logger.info(f"[OK] Test user created: {test_email}")
                else:
                    logger.info(f"[OK] Test user already exists: {test_email}")
            except Exception as user_error:
                logger.error(f"Failed to create test user: {user_error}")

    except Exception as check_error:
        logger.error(f"Error checking database for seeding: {str(check_error)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.warning("Continuing without seeding check")
