"""Pytest configuration and shared fixtures for all tests."""
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question


# ──────────────────────────────────────────────────────────────────
# Test Database Configuration
# ──────────────────────────────────────────────────────────────────

# Use in-memory SQLite for tests (fast, isolated)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory database for each test.

    This ensures complete isolation between tests.
    """
    # Create async engine with in-memory SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ──────────────────────────────────────────────────────────────────
# FastAPI Test Client
# ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
async def test_client(test_db: AsyncSession) -> Generator:
    """Create a FastAPI test client with database dependency override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────
# Mock External Services
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ollama():
    """Mock Ollama LLM client for testing AI generation without actual LLM."""
    mock_client = AsyncMock()

    # Mock question generation response
    mock_client.generate_questions.return_value = [
        {
            "question_text": "What is the capital of France?",
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Madrid"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital and largest city of France.",
            "difficulty": "easy"
        }
    ]

    # Mock is_available check
    mock_client.is_available.return_value = True

    with patch("app.core.ollama.ollama_client", mock_client):
        yield mock_client


@pytest.fixture
def mock_vector_store():
    """Mock Qdrant vector store for testing RAG without actual vector DB."""
    mock_store = AsyncMock()

    # Mock search results
    mock_store.search.return_value = [
        {
            "text": "Sample context from PDF",
            "page": 1,
            "score": 0.85
        }
    ]

    mock_store.is_available.return_value = True

    with patch("app.rag.vector_store.vector_store", mock_store):
        yield mock_store


@pytest.fixture
def mock_cache():
    """Mock Redis cache for testing without actual Redis instance."""
    mock_cache_client = MagicMock()

    # Mock cache methods
    mock_cache_client.available = False  # Use in-memory fallback
    mock_cache_client.get_pregenerated_questions = AsyncMock(return_value=None)
    mock_cache_client.cache_pregenerated_questions = AsyncMock()
    mock_cache_client.get_question_pool = MagicMock(return_value=None)
    mock_cache_client.cache_question_pool = AsyncMock()

    with patch("app.core.cache.cache", mock_cache_client):
        yield mock_cache_client


# ──────────────────────────────────────────────────────────────────
# Test User Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        total_stars=10
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession) -> User:
    """Create an admin user in the database."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        total_stars=100
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Generate a JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def admin_user_token(admin_user: User) -> str:
    """Generate a JWT token for the admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Create authorization headers with test user token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(admin_user_token: str) -> dict:
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_user_token}"}


# ──────────────────────────────────────────────────────────────────
# Test Data Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def test_exam(test_db: AsyncSession) -> Exam:
    """Create a test exam."""
    exam = Exam(
        name="UPSC Civil Services",
        description="Union Public Service Commission exam",
        is_active=True
    )
    test_db.add(exam)
    await test_db.commit()
    await test_db.refresh(exam)
    return exam


@pytest.fixture
async def test_subject(test_db: AsyncSession, test_exam: Exam) -> Subject:
    """Create a test subject."""
    subject = Subject(
        exam_id=test_exam.id,
        name="General Studies",
        description="General Studies for UPSC",
        is_active=True
    )
    test_db.add(subject)
    await test_db.commit()
    await test_db.refresh(subject)
    return subject


@pytest.fixture
async def test_topic(test_db: AsyncSession, test_subject: Subject) -> Topic:
    """Create a test topic."""
    topic = Topic(
        subject_id=test_subject.id,
        name="Indian History",
        description="Ancient and Medieval Indian History",
        difficulty_level="medium",
        estimated_study_mins=30
    )
    test_db.add(topic)
    await test_db.commit()
    await test_db.refresh(topic)
    return topic


@pytest.fixture
async def test_questions(test_db: AsyncSession, test_topic: Topic) -> list[Question]:
    """Create test questions for a topic."""
    questions = [
        Question(
            topic_id=test_topic.id,
            question_text="Who was the first emperor of the Maurya dynasty?",
            options={
                "A": "Ashoka",
                "B": "Chandragupta Maurya",
                "C": "Bindusara",
                "D": "Samudragupta"
            },
            correct_answer="B",
            explanation="Chandragupta Maurya founded the Maurya Empire in 322 BCE.",
            difficulty="medium",
            source="previous_year",
            year=2020
        ),
        Question(
            topic_id=test_topic.id,
            question_text="The Indus Valley Civilization was discovered in which year?",
            options={
                "A": "1820",
                "B": "1856",
                "C": "1921",
                "D": "1947"
            },
            correct_answer="C",
            explanation="The Indus Valley Civilization was discovered in 1921 at Harappa.",
            difficulty="medium",
            source="previous_year",
            year=2019
        ),
        Question(
            topic_id=test_topic.id,
            question_text="Which Mughal emperor built the Taj Mahal?",
            options={
                "A": "Akbar",
                "B": "Jahangir",
                "C": "Shah Jahan",
                "D": "Aurangzeb"
            },
            correct_answer="C",
            explanation="Shah Jahan built the Taj Mahal in memory of his wife Mumtaz Mahal.",
            difficulty="easy",
            source="ai_generated"
        ),
    ]

    for question in questions:
        test_db.add(question)

    await test_db.commit()

    for question in questions:
        await test_db.refresh(question)

    return questions


# ──────────────────────────────────────────────────────────────────
# Utility Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_question_data() -> dict:
    """Sample question data for testing validation."""
    return {
        "question_text": "What is the largest planet in our solar system?",
        "options": {
            "A": "Earth",
            "B": "Mars",
            "C": "Jupiter",
            "D": "Saturn"
        },
        "correct_answer": "C",
        "explanation": "Jupiter is the largest planet in our solar system with a mass more than twice that of all other planets combined.",
        "difficulty": "easy"
    }


@pytest.fixture
def invalid_question_data() -> dict:
    """Invalid question data for testing validation errors."""
    return {
        "question_text": "What?",  # Too short
        "options": {
            "A": "Answer 1",
            "B": "Answer 1",  # Duplicate
            "C": "Answer 3"
            # Missing option D
        },
        "correct_answer": "E",  # Invalid option
        "explanation": "Short",  # Too short
        "difficulty": "invalid"  # Invalid difficulty
    }


# ──────────────────────────────────────────────────────────────────
# Performance Testing Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    import time

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.metrics = {}

        def start(self):
            self.start_time = time.time()

        def end(self):
            self.end_time = time.time()

        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def record(self, key: str, value: float):
            self.metrics[key] = value

        def get_metrics(self) -> dict:
            return {
                **self.metrics,
                "total_time": self.elapsed()
            }

    return PerformanceTracker()


# ──────────────────────────────────────────────────────────────────
# Cleanup Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables after each test."""
    yield
    # Reset environment variables if modified during test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
