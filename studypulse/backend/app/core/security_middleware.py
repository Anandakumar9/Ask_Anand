"""Security middleware for production hardening."""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        start_time = time.time()

        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Add processing time header for monitoring
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks."""

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """
        Initialize middleware.

        Args:
            app: ASGI application
            max_size: Maximum request body size in bytes (default 10MB)
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """Check request size before processing."""
        # Check Content-Length header
        if "content-length" in request.headers:
            content_length = int(request.headers["content-length"])
            if content_length > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Maximum size is {self.max_size / (1024 * 1024):.1f}MB"
                    }
                )

        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Timeout middleware to prevent slow requests from hanging."""

    def __init__(self, app: ASGIApp, timeout: float = 30.0):
        """
        Initialize middleware.

        Args:
            app: ASGI application
            timeout: Request timeout in seconds (default 30)
        """
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        """Execute request with timeout."""
        import asyncio

        try:
            # Create a timeout for the request
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request timeout after {self.timeout} seconds. "
                              "Please try again or contact support if the issue persists."
                }
            )
