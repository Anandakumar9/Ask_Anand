"""Comprehensive health check endpoints for production monitoring."""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.cache import cache
from app.core.ollama import ollama_client
from app.core.database import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()

# Track application start time for uptime metrics
APP_START_TIME = datetime.utcnow()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()

        # Test database connection with a simple query
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "type": "sqlite",
            "url": settings.DATABASE_URL.split("///")[-1]  # Hide full path
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "type": "sqlite"
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis cache connectivity and performance."""
    try:
        health_info = await cache.health_check()
        metrics = cache.get_metrics()

        return {
            **health_info,
            "hit_rate_percentage": metrics.get("hit_rate_percentage", 0),
            "total_requests": metrics.get("total_requests", 0)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "backend": "unknown",
            "error": str(e)
        }


async def check_ollama() -> Dict[str, Any]:
    """Check Ollama LLM availability and performance."""
    try:
        start_time = time.time()
        available = await ollama_client.is_available()
        latency_ms = round((time.time() - start_time) * 1000, 2)

        if available:
            return {
                "status": "healthy",
                "model": settings.OLLAMA_MODEL,
                "base_url": settings.OLLAMA_BASE_URL,
                "latency_ms": latency_ms
            }
        else:
            return {
                "status": "unavailable",
                "model": settings.OLLAMA_MODEL,
                "base_url": settings.OLLAMA_BASE_URL,
                "message": "Ollama service not responding"
            }
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "model": settings.OLLAMA_MODEL,
            "error": str(e)
        }


@router.get("/health", tags=["Health"])
async def basic_health_check():
    """
    Basic liveness check - returns 200 if service is running.

    Use this for simple uptime monitoring (UptimeRobot, etc.)
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check - comprehensive check of all critical dependencies.

    Returns:
        - 200 if all critical components are healthy
        - 503 if any critical component is down
        - 200 with degraded status if non-critical components are down
    """
    # Run all checks in parallel for faster response
    db_check, redis_check, ollama_check = await asyncio.gather(
        check_database(),
        check_redis(),
        check_ollama(),
        return_exceptions=True
    )

    # Handle exceptions in parallel checks
    if isinstance(db_check, Exception):
        db_check = {"status": "unhealthy", "error": str(db_check)}
    if isinstance(redis_check, Exception):
        redis_check = {"status": "unhealthy", "error": str(redis_check)}
    if isinstance(ollama_check, Exception):
        ollama_check = {"status": "unhealthy", "error": str(ollama_check)}

    # Determine overall status
    overall_status = "healthy"
    http_status = status.HTTP_200_OK

    # Database is CRITICAL - must be healthy
    if db_check.get("status") != "healthy":
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # Redis degradation is acceptable (in-memory fallback exists)
    elif redis_check.get("status") in ["degraded", "unhealthy"]:
        overall_status = "degraded"
        logger.warning("Service running in degraded mode: Redis unavailable")

    # Ollama is non-critical (fallback to database questions)
    if ollama_check.get("status") in ["unavailable", "error"]:
        if overall_status == "healthy":
            overall_status = "degraded"
        logger.warning("Service running in degraded mode: Ollama unavailable")

    # Calculate uptime
    uptime_seconds = (datetime.utcnow() - APP_START_TIME).total_seconds()

    response_data = {
        "status": overall_status,
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "components": {
            "database": db_check,
            "cache": redis_check,
            "ollama": ollama_check
        },
        "features": {
            "rag_enabled": settings.RAG_ENABLED,
            "ai_generation": ollama_check.get("status") == "healthy"
        }
    }

    return JSONResponse(
        status_code=http_status,
        content=response_data
    )


@router.get("/health/metrics", tags=["Health"])
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.

    Returns application metrics in Prometheus text format.
    Can be scraped by Prometheus for monitoring dashboards.
    """
    # Get cache metrics
    cache_metrics = cache.get_metrics()

    # Calculate uptime
    uptime_seconds = (datetime.utcnow() - APP_START_TIME).total_seconds()

    # Build Prometheus metrics format
    metrics = []

    # Application info
    metrics.append(f'# HELP studypulse_info Application information')
    metrics.append(f'# TYPE studypulse_info gauge')
    metrics.append(f'studypulse_info{{version="{settings.API_VERSION}",app="{settings.APP_NAME}"}} 1')

    # Uptime
    metrics.append(f'# HELP studypulse_uptime_seconds Application uptime in seconds')
    metrics.append(f'# TYPE studypulse_uptime_seconds counter')
    metrics.append(f'studypulse_uptime_seconds {uptime_seconds}')

    # Cache metrics
    metrics.append(f'# HELP studypulse_cache_hit_rate_percentage Cache hit rate percentage')
    metrics.append(f'# TYPE studypulse_cache_hit_rate_percentage gauge')
    metrics.append(f'studypulse_cache_hit_rate_percentage {cache_metrics.get("hit_rate_percentage", 0)}')

    metrics.append(f'# HELP studypulse_cache_requests_total Total cache requests')
    metrics.append(f'# TYPE studypulse_cache_requests_total counter')
    metrics.append(f'studypulse_cache_requests_total {cache_metrics.get("total_requests", 0)}')

    metrics.append(f'# HELP studypulse_cache_hits_total Total cache hits')
    metrics.append(f'# TYPE studypulse_cache_hits_total counter')
    redis_hits = cache_metrics.get("redis_hits", 0)
    memory_hits = cache_metrics.get("memory_hits", 0)
    pool_hits = cache_metrics.get("pool_hits", 0)
    metrics.append(f'studypulse_cache_hits_total{{type="redis"}} {redis_hits}')
    metrics.append(f'studypulse_cache_hits_total{{type="memory"}} {memory_hits}')
    metrics.append(f'studypulse_cache_hits_total{{type="pool"}} {pool_hits}')

    metrics.append(f'# HELP studypulse_cache_misses_total Total cache misses')
    metrics.append(f'# TYPE studypulse_cache_misses_total counter')
    redis_misses = cache_metrics.get("redis_misses", 0)
    memory_misses = cache_metrics.get("memory_misses", 0)
    pool_misses = cache_metrics.get("pool_misses", 0)
    metrics.append(f'studypulse_cache_misses_total{{type="redis"}} {redis_misses}')
    metrics.append(f'studypulse_cache_misses_total{{type="memory"}} {memory_misses}')
    metrics.append(f'studypulse_cache_misses_total{{type="pool"}} {pool_misses}')

    # Cache errors
    metrics.append(f'# HELP studypulse_cache_errors_total Total cache errors')
    metrics.append(f'# TYPE studypulse_cache_errors_total counter')
    metrics.append(f'studypulse_cache_errors_total {cache_metrics.get("errors", 0)}')

    # Join all metrics with newlines
    return "\n".join(metrics) + "\n"


@router.get("/health/live", tags=["Health"])
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application process is running.
    Does not check dependencies (faster than readiness).
    """
    return {"status": "alive"}


@router.get("/health/startup", tags=["Health"])
async def startup_probe():
    """
    Kubernetes startup probe endpoint.

    Returns 200 once the application has completed initialization.
    """
    # Check if critical components are initialized
    db_initialized = engine is not None
    cache_initialized = cache is not None

    if db_initialized and cache_initialized:
        return {
            "status": "ready",
            "message": "Application startup completed"
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "starting",
                "message": "Application still initializing"
            }
        )
