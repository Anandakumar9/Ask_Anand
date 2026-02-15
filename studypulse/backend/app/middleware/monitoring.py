"""Performance monitoring middleware for request tracking."""
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Context variable to store request ID across async calls
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[int] = ContextVar("user_id", default=0)

# Performance metrics storage (in-memory)
request_metrics = {
    "total_requests": 0,
    "slow_requests": 0,
    "errors": 0,
    "total_duration_seconds": 0.0,
}


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_var.get()


def get_user_id() -> int:
    """Get current user ID from context."""
    return user_id_var.get()


def get_metrics() -> dict:
    """Get current performance metrics."""
    total_requests = request_metrics["total_requests"]
    avg_duration = 0.0
    if total_requests > 0:
        avg_duration = round(
            request_metrics["total_duration_seconds"] / total_requests, 3
        )

    return {
        **request_metrics,
        "average_duration_seconds": avg_duration,
        "slow_request_percentage": round(
            (request_metrics["slow_requests"] / max(1, total_requests)) * 100, 2
        ),
        "error_percentage": round(
            (request_metrics["errors"] / max(1, total_requests)) * 100, 2
        ),
    }


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for performance monitoring and request tracking.

    Features:
    - Adds unique request ID to all requests
    - Tracks request duration
    - Logs slow requests (>5 seconds)
    - Tracks error rates
    - Adds request context to logs (user_id, endpoint)
    """

    def __init__(self, app: ASGIApp, slow_threshold_seconds: float = 5.0):
        super().__init__(app)
        self.slow_threshold = slow_threshold_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)

        # Extract user ID if available (from JWT or session)
        user_id = 0
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
            user_id_var.set(user_id)

        # Start timing
        start_time = time.time()

        # Add request ID to response headers
        response = None
        error_occurred = False

        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Check if this was an error response
            if response.status_code >= 500:
                error_occurred = True
                request_metrics["errors"] += 1

        except Exception as e:
            # Catch any unhandled exceptions
            error_occurred = True
            request_metrics["errors"] += 1
            logger.error(
                f"Unhandled exception in request",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Update metrics
            request_metrics["total_requests"] += 1
            request_metrics["total_duration_seconds"] += duration

            # Check if this was a slow request
            is_slow = duration > self.slow_threshold
            if is_slow:
                request_metrics["slow_requests"] += 1

            # Prepare log data
            log_data = {
                "request_id": request_id,
                "user_id": user_id if user_id > 0 else None,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code if response else 500,
                "duration_ms": duration_ms,
                "duration_seconds": round(duration, 3),
                "is_slow": is_slow,
                "error": error_occurred,
            }

            # Log based on severity
            if error_occurred:
                logger.error(f"Request failed", extra=log_data)
            elif is_slow:
                logger.warning(f"Slow request detected", extra=log_data)
            else:
                logger.info(f"Request completed", extra=log_data)

        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and store user context in request state.

    This allows other middleware and request handlers to access user info.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Try to extract user from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Import here to avoid circular imports
                from app.core.security import get_current_user_from_token

                token = auth_header.replace("Bearer ", "")
                user = await get_current_user_from_token(token)
                if user:
                    request.state.user_id = user.id
                    user_id_var.set(user.id)
            except Exception as e:
                # Token validation failed or user not found - continue without user context
                logger.debug(f"Token validation failed in monitoring middleware: {e}")

        response = await call_next(request)
        return response
