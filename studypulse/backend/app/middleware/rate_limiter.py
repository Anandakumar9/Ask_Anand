"""Rate limiting middleware for production security."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings

# Initialize limiter (storage set in setup_rate_limiting)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_GLOBAL],
    storage_uri="memory://",
    strategy="fixed-window",
)


def setup_rate_limiting(app):
    """
    Configure rate limiting for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Prefer Redis in production if configured (supports multi-replica deployments)
    if settings.REDIS_URL and settings.REDIS_URL.startswith("redis://"):
        limiter.storage_uri = settings.REDIS_URL

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    return limiter


# Rate limit decorators for specific endpoints
auth_limit = settings.RATE_LIMIT_AUTH  # Auth endpoints - prevent brute force
study_limit = settings.RATE_LIMIT_STUDY  # Study session creation
question_limit = settings.RATE_LIMIT_QUESTIONS  # Question generation polling
api_limit = settings.RATE_LIMIT_GLOBAL  # General API endpoints
guest_limit = "3/minute"  # Guest login - prevent abuse
