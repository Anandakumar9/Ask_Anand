"""StudyPulse FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.cache import cache
from app.core.database import init_db
from app.core.ollama import ollama_client

# Dynamic vector store selection (Qdrant or PageIndex)
if settings.USE_PAGEINDEX:
    from app.rag.pageindex_adapter import pageindex_store as vector_store
else:
    from app.rag.vector_store import vector_store

# All routers use SQLAlchemy (single consistent database)
from app.api import (
    auth_router,
    exams_router,
    study_router,
    mock_test_router,
    dashboard_router,
)
from app.api.leaderboard import router as leaderboard_router
from app.api.profile import router as profile_router
from app.api.questions import router as questions_router
from app.api.cache_stats import router as cache_router

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} API...")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"Ollama: {settings.OLLAMA_MODEL}")
    logger.info(f"RAG Pipeline: {'Enabled' if settings.RAG_ENABLED else 'Disabled'}")
    logger.info(f"Star Threshold: {settings.STAR_THRESHOLD_PERCENTAGE}%")
    
    # Initialize SQLite database tables
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Initialize Redis cache
    logger.info("Initializing Redis cache...")
    await cache.initialize()
    
    # Initialize Qdrant vector store + FastEmbed
    logger.info("Initializing Qdrant vector store...")
    await vector_store.initialize()
    
    # Initialize Ollama async client
    logger.info("Initializing Ollama LLM client...")
    await ollama_client.initialize()
    available = await ollama_client.is_available()
    if available:
        logger.info(f"Ollama model '{settings.OLLAMA_MODEL}' ready")
    else:
        logger.warning("Ollama not available — AI question generation disabled")
    
    yield
    
    # Shutdown
    logger.info(f"[SHUTDOWN] Shutting down {settings.APP_NAME} API...")
    await vector_store.close()
    await ollama_client.close()
    await cache.close()
    logger.info("[OK] Cleanup completed")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    **StudyPulse** - AI-Powered Exam Preparation Platform
    
    StudyPulse helps students prepare for competitive exams through:
    - 📚 Structured study sessions with timers
    - 📝 Smart mock tests with previous year + AI questions  
    - ⭐ Gamified learning with star rewards
    - 📊 Detailed progress analytics
    
    ## Authentication
    Most endpoints require authentication via JWT Bearer token.
    Use `/api/v1/auth/login` to get a token.
    """,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Use configured origins from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(
    auth_router, 
    prefix="/api/v1/auth", 
    tags=["🔐 Authentication"]
)
app.include_router(
    exams_router, 
    prefix="/api/v1/exams", 
    tags=["📚 Exams"]
)
app.include_router(
    study_router, 
    prefix="/api/v1/study", 
    tags=["⏱️ Study Sessions"]
)
app.include_router(
    mock_test_router, 
    prefix="/api/v1/mock-test", 
    tags=["📝 Mock Tests"]
)
app.include_router(
    dashboard_router, 
    prefix="/api/v1/dashboard", 
    tags=["📊 Dashboard"]
)
app.include_router(
    leaderboard_router,
    prefix="/api/v1/leaderboard",
    tags=["🏆 Leaderboard"]
)
app.include_router(
    profile_router,
    prefix="/api/v1/profile",
    tags=["👤 Profile"]
)
app.include_router(
    questions_router,
    prefix="/api/v1",
    tags=["📥 Question Import"]
)
app.include_router(
    cache_router,
    prefix="/api/v1",
    tags=["🔧 Cache Management"]
)


@app.get("/", tags=["🏠 Root"])
async def root():
    """API root endpoint with welcome message."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["🏠 Root"])
async def health_check():
    """Health check endpoint for monitoring."""
    from app.rag.orchestrator import orchestrator

    # Check all system components
    health_status = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "components": {
            "database": "healthy",
            "cache": "unknown",
            "ollama": "unknown",
            "vector_store": "unknown",
        }
    }

    # Check cache
    try:
        cache_health = await cache.health_check()
        health_status["components"]["cache"] = cache_health.get("status", "unknown")
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["components"]["cache"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check Ollama
    try:
        ollama_available = await ollama_client.is_available()
        health_status["components"]["ollama"] = "healthy" if ollama_available else "unavailable"
        if not ollama_available and settings.RAG_ENABLED:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        health_status["components"]["ollama"] = "error"

    # Check vector store
    try:
        health_status["components"]["vector_store"] = "healthy"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        health_status["components"]["vector_store"] = "error"

    return health_status
