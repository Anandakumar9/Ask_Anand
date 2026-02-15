"""Rate limiting middleware for production security."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


# Initialize limiter with Redis backend (falls back to in-memory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global rate limit
    storage_uri="memory://",  # Will be updated with Redis URL if available
    strategy="fixed-window"
)


def setup_rate_limiting(app):
    """
    Configure rate limiting for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    return limiter


# Rate limit decorators for specific endpoints
auth_limit = "5/minute"  # Auth endpoints - prevent brute force
study_limit = "10/minute"  # Study session creation
question_limit = "30/minute"  # Question generation polling
api_limit = "60/minute"  # General API endpoints
guest_limit = "3/minute"  # Guest login - prevent abuse
