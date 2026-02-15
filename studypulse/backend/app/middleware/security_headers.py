"""Security headers middleware for production."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response."""
        # Add request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Track request start time
        start_time = time.time()

        # Process request
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}", exc_info=True)
            raise

        # Calculate request duration
        duration = (time.time() - start_time) * 1000  # in milliseconds

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Add request tracking headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"

        # Log slow requests (>5 seconds)
        if duration > 5000:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration:.2f}ms (request_id: {request_id})"
            )

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks."""

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """
        Initialize middleware.

        Args:
            app: ASGI application
            max_size: Maximum request body size in bytes
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """Check request size before processing."""
        # Check Content-Length header
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    f"Request rejected: body size {content_length} exceeds "
                    f"maximum {self.max_size} bytes"
                )
                return Response(
                    content="Request body too large",
                    status_code=413,
                    headers={"Content-Type": "text/plain"}
                )

        return await call_next(request)
