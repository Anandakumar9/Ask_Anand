"""Application configuration - single source of truth for all settings."""
import os
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import urlparse, urlunparse, quote


class Settings(BaseSettings):
    """StudyPulse settings. Override via .env file or environment variables."""

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = "StudyPulse"
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"  # Default False for security
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # production, staging, development

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./studypulse.db"

    # PostgreSQL connection pool settings (production)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    def __init__(self, **kwargs):
        """Initialize settings and fix DATABASE_URL for asyncpg if needed."""
        super().__init__(**kwargs)

        # CRITICAL DEBUG: Print what DATABASE_URL we received (Railway debugging)
        print(f"🔍 [CONFIG DEBUG] DATABASE_URL received: {self.DATABASE_URL[:50]}..." if len(self.DATABASE_URL) > 50 else f"🔍 [CONFIG DEBUG] DATABASE_URL received: '{self.DATABASE_URL}'")
        print(f"🔍 [CONFIG DEBUG] DATABASE_URL length: {len(self.DATABASE_URL)}")
        print(f"🔍 [CONFIG DEBUG] DATABASE_URL type: {type(self.DATABASE_URL)}")

        # Railway provides postgresql:// but SQLAlchemy async needs postgresql+asyncpg://
        if self.DATABASE_URL.startswith("postgresql://"):
            print(f"✅ [CONFIG DEBUG] Converting postgresql:// to postgresql+asyncpg://")
            # Convert to asyncpg dialect
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Additional check for Railway's internal URLs (postgres:// scheme)
        elif self.DATABASE_URL.startswith("postgres://"):
            print(f"✅ [CONFIG DEBUG] Converting postgres:// to postgresql+asyncpg://")
            # Convert postgres:// to postgresql+asyncpg://
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

        # Print final DATABASE_URL
        print(f"🔍 [CONFIG DEBUG] DATABASE_URL after conversion: {self.DATABASE_URL[:50]}..." if len(self.DATABASE_URL) > 50 else f"🔍 [CONFIG DEBUG] DATABASE_URL after conversion: '{self.DATABASE_URL}'")

        # Validate the URL can be parsed (debug logging)
        if not self.DATABASE_URL.startswith("sqlite"):
            try:
                parsed = urlparse(self.DATABASE_URL)
                print(f"✓ Database URL scheme: {parsed.scheme}")
                print(f"✓ Database host: {parsed.hostname}")
            except Exception as e:
                print(f"⚠️  Warning: Could not validate DATABASE_URL: {e}")
                print(f"   URL scheme: {self.DATABASE_URL.split('://')[0] if '://' in self.DATABASE_URL else 'unknown'}")

    # ── Authentication ────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-use-a-real-secret-key-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── CORS Configuration ────────────────────────────────────
    # Comma-separated list of allowed origins (e.g., "http://localhost:3000,https://app.example.com")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

    # ── Security Configuration ────────────────────────────────
    # Rate Limiting (requests per minute)
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_STUDY: str = "10/minute"
    RATE_LIMIT_QUESTIONS: str = "30/minute"

    # Request Limits
    MAX_REQUEST_SIZE_MB: int = 10  # Maximum request body size in MB
    REQUEST_TIMEOUT_SECONDS: int = 30  # Request timeout in seconds

    # Password Requirements
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_PASSWORD_DIGIT: bool = True
    REQUIRE_PASSWORD_SPECIAL: bool = True

    # ── Ollama LLM ────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi4-mini:3.8b-q4_K_M"
    OLLAMA_TIMEOUT: int = 300  # 5 minutes for multiple question generation

    # ── Qdrant Vector Database ────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "studypulse_questions"

    # ── PageIndex (Lightweight alternative to Qdrant) ─────────
    USE_PAGEINDEX: bool = False  # Use PageIndex instead of Qdrant (lighter, embedded)
    PAGEINDEX_STORAGE_PATH: str = "./data/pageindex"

    # ── Redis Cache ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Embedding Model (FastEmbed / ONNX) ────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # ── RAG Pipeline ──────────────────────────────────────────
    RAG_ENABLED: bool = True  # Enabled for AI question generation
    DEFAULT_QUESTION_COUNT: int = 10  # Minimum 10 questions per mock test

    # ── Parallel Question Generation (Performance Tuning) ────
    # Number of questions to generate per LLM call (reduce for smaller models)
    QUESTION_BATCH_SIZE: int = int(os.getenv("QUESTION_BATCH_SIZE", "3"))
    # Number of parallel LLM agents (increase for faster generation, decrease if CPU/RAM limited)
    PARALLEL_QUESTION_AGENTS: int = int(os.getenv("PARALLEL_QUESTION_AGENTS", "4"))
    PREVIOUS_YEAR_RATIO: float = 0.3  # 30% DB questions, 70% AI when RAG enabled
    PRE_GENERATION_DELAY_SECONDS: int = 0  # Immediate generation when timer starts
    SIMILARITY_DEDUP_THRESHOLD: float = 0.85

    # ── Scoring ───────────────────────────────────────────────
    STAR_THRESHOLD_PERCENTAGE: int = 70

    # ── Optional: OpenRouter fallback ─────────────────────────
    OPENROUTER_API_KEY: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_security(self):
        """Validate security settings on startup."""
        errors = []
        warnings = []

        # Check if DEBUG is enabled in production
        if self.DEBUG and self.ENVIRONMENT == "production":
            errors.append("DEBUG=True is not allowed in production environment!")

        # Check if default secret key is being used
        if self.SECRET_KEY == "change-this-in-production-use-a-real-secret-key-min-32-chars":
            if self.ENVIRONMENT == "production":
                errors.append("Default SECRET_KEY detected in production! Set a secure key in .env")
            else:
                warnings.append("Using default SECRET_KEY. Set a secure key in .env for production!")

        # Validate secret key length (minimum 64 characters for production)
        if self.ENVIRONMENT == "production":
            if len(self.SECRET_KEY) < 64:
                errors.append("SECRET_KEY must be at least 64 characters long in production!")
        else:
            if len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY must be at least 32 characters long!")

        # Check for hardcoded localhost in CORS origins in production
        if self.ENVIRONMENT == "production":
            if "localhost" in self.CORS_ORIGINS.lower() or "127.0.0.1" in self.CORS_ORIGINS:
                warnings.append("Localhost detected in CORS_ORIGINS in production environment!")

        # Check if wildcard CORS is being used in production
        if self.ENVIRONMENT == "production" and self.CORS_ORIGINS == "*":
            errors.append("Wildcard CORS (*) is not allowed in production!")

        # Print warnings
        for warning in warnings:
            print(f"⚠️  WARNING: {warning}")

        # Raise errors
        if errors:
            error_msg = "\n".join([f"❌ {error}" for error in errors])
            raise ValueError(f"Security validation failed:\n{error_msg}")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

# Validate security on import
settings.validate_security()
