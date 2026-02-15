"""Structured logging configuration for StudyPulse."""
import logging
import sys
from datetime import datetime
from pathlib import Path
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        timestamp=True
    )
    
    # Console handler (colored output for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # File handler (JSON format for production analysis)
    log_file = log_path / f"studypulse_{datetime.now().strftime('%Y%m%d')}.json"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Error handler (separate file for errors)
    error_log_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Application loggers
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    
    logging.info("[OK] Logging configured successfully")
    logging.info(f"[INFO] Log file: {log_file}")
    logging.info(f"[ERROR] Error log: {error_log_file}")


# Utility functions for structured logging
def log_api_call(logger: logging.Logger, endpoint: str, user_id: int, **kwargs):
    """Log API call with structured data."""
    logger.info(
        f"API call: {endpoint}",
        extra={
            "event_type": "api_call",
            "endpoint": endpoint,
            "user_id": user_id,
            **kwargs
        }
    )


def log_ai_generation(
    logger: logging.Logger, 
    topic_id: int, 
    question_count: int, 
    duration_seconds: float,
    source: str = "ollama",
    **kwargs
):
    """Log AI question generation with metrics."""
    logger.info(
        f"AI generation completed: {question_count} questions in {duration_seconds:.2f}s",
        extra={
            "event_type": "ai_generation",
            "topic_id": topic_id,
            "question_count": question_count,
            "duration_seconds": duration_seconds,
            "source": source,
            "questions_per_second": question_count / duration_seconds if duration_seconds > 0 else 0,
            **kwargs
        }
    )


def log_cache_hit(logger: logging.Logger, cache_key: str, hit: bool):
    """Log cache hit/miss."""
    logger.debug(
        f"Cache {'HIT' if hit else 'MISS'}: {cache_key}",
        extra={
            "event_type": "cache_access",
            "cache_key": cache_key,
            "hit": hit
        }
    )


def log_test_completion(
    logger: logging.Logger,
    user_id: int,
    topic_id: int,
    score: float,
    star_earned: bool,
    time_taken: int,
    **kwargs
):
    """Log mock test completion with results."""
    logger.info(
        f"Test completed: User {user_id} scored {score}% ({'⭐ STAR' if star_earned else 'No star'})",
        extra={
            "event_type": "test_completion",
            "user_id": user_id,
            "topic_id": topic_id,
            "score": score,
            "star_earned": star_earned,
            "time_taken_seconds": time_taken,
            **kwargs
        }
    )


def log_error_with_context(logger: logging.Logger, error: Exception, context: dict):
    """Log error with full context for debugging."""
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        },
        exc_info=True
    )
