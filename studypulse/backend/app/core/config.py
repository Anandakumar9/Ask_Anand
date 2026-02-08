"""Application configuration - single source of truth for all settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """StudyPulse settings. Override via .env file or environment variables."""

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "StudyPulse"
    API_VERSION: str = "v1"
    DEBUG: bool = True

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./studypulse.db"

    # ── Authentication ────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-use-a-real-secret-key-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Ollama LLM ────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi4-mini:3.8b-q4_K_M"
    OLLAMA_TIMEOUT: int = 120  # seconds

    # ── Qdrant Vector Database ────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "studypulse_questions"

    # ── Redis Cache ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Embedding Model (FastEmbed / ONNX) ────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # ── RAG Pipeline ──────────────────────────────────────────
    RAG_ENABLED: bool = True
    DEFAULT_QUESTION_COUNT: int = 10
    PREVIOUS_YEAR_RATIO: float = 0.5
    PRE_GENERATION_DELAY_SECONDS: int = 10
    SIMILARITY_DEDUP_THRESHOLD: float = 0.85

    # ── Scoring ───────────────────────────────────────────────
    STAR_THRESHOLD_PERCENTAGE: int = 70

    # ── Optional: OpenRouter fallback ─────────────────────────
    OPENROUTER_API_KEY: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
