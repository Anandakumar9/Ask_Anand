"""Cache statistics and health check API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.rag.orchestrator import orchestrator

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
):
    """
    Get cache performance metrics and statistics.

    Returns:
    - Hit/miss rates for all cache layers
    - Cache sizes
    - Error counts
    - Overall hit rate percentage
    """
    return {
        "status": "success",
        "data": cache.get_metrics(),
    }


@router.get("/health")
async def cache_health_check():
    """
    Check Redis cache health status.

    Returns:
    - Status: healthy, degraded, or unhealthy
    - Backend type: redis or memory
    - Latency and connection info (if Redis)
    """
    health = await cache.health_check()
    return {
        "status": "success",
        "data": health,
    }


@router.post("/clear/profile/{user_id}")
async def clear_profile_cache(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear cached profile stats for a specific user."""
    cache.invalidate_profile_stats(user_id)
    return {
        "status": "success",
        "message": f"Profile cache cleared for user {user_id}",
    }


@router.post("/clear/questions/{topic_id}")
async def clear_question_pool(
    topic_id: int,
    current_user: User = Depends(get_current_user),
):
    """Clear cached question pool for a specific topic."""
    cache.invalidate_question_pool(topic_id)
    return {
        "status": "success",
        "message": f"Question pool cache cleared for topic {topic_id}",
    }


@router.get("/rag/metrics")
async def get_rag_metrics(
    current_user: User = Depends(get_current_user),
):
    """
    Get RAG pipeline performance metrics.

    Returns:
    - Orchestrator metrics (tests generated, cache performance)
    - Generator metrics (questions generated, success rate)
    - Overall AI generation statistics
    """
    return {
        "status": "success",
        "data": orchestrator.get_metrics(),
    }
