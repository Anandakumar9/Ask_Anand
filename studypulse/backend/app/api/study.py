"""Study Session API — Timer with background question pre-generation.

When a study session starts, questions are immediately generated in the
background and cached. When the session ends, questions are retrieved
from cache and returned instantly.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.models.exam import Topic
from app.models.mock_test import StudySession
from app.models.user import User
from app.rag.orchestrator import orchestrator
from app.schemas.mock_test import StudySessionCreate

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Start study session ───────────────────────────────────────


@router.post("/sessions")
async def start_study_session(
    data: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a study session and trigger background question generation.
    
    Questions are generated immediately in background and cached.
    """
    # Verify topic
    topic = (
        await db.execute(select(Topic).where(Topic.id == data.topic_id))
    ).scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    session = StudySession(
        user_id=current_user.id,
        topic_id=data.topic_id,
        duration_mins=data.duration_mins,
        completed=False,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Trigger background question generation immediately
    asyncio.create_task(
        _generate_and_cache_questions(
            data.topic_id, current_user.id, session.id, data.previous_question_ids
        )
    )

    logger.info(
        f"Study session {session.id} started: topic={data.topic_id} "
        f"duration={data.duration_mins}min user={current_user.id} - "
        f"Background question generation triggered"
    )

    return {
        "session_id": session.id,
        "user_id": current_user.id,
        "topic_id": data.topic_id,
        "topic_name": topic.name,
        "duration_mins": data.duration_mins,
        "completed": False,
        "started_at": session.started_at.isoformat() if session.started_at else "",
    }


# ── Check question generation status ──────────────────────


@router.get("/sessions/{session_id}/question-status")
async def get_question_generation_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll pre-generation status during study session.

    Returns the current status of background question generation:
    - pending: Generation not started or status unknown
    - started: Generation in progress
    - completed: Questions ready in cache
    - failed: Generation encountered an error

    Also returns question count, metadata, and estimated time if available.
    """
    # Verify session exists and belongs to user
    session = (
        await db.execute(
            select(StudySession).where(
                StudySession.id == session_id,
                StudySession.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check cache for pre-generation status
    from app.core.cache import cache

    status = await cache.get_pregen_status(session.topic_id, current_user.id)

    # If no status in cache, check if questions are already cached
    cached_data = await cache.get_pregenerated_questions(
        session.topic_id, current_user.id
    )

    # Extract questions and metadata
    questions = []
    metadata = {}
    if cached_data and len(cached_data) > 0:
        # New format: [{questions: [...], metadata: {...}}]
        if isinstance(cached_data[0], dict) and "questions" in cached_data[0]:
            cache_entry = cached_data[0]
            questions = cache_entry.get("questions", [])
            metadata = cache_entry.get("metadata", {})
        else:
            # Old format: direct question list
            questions = cached_data

    # Check if this is an error cache entry
    if cached_data:
        if metadata.get("status") == "failed":
            return {
                "session_id": session_id,
                "status": "failed",
                "question_count": 0,
                "estimated_time_remaining_seconds": 0,
                "message": metadata.get("error", "Question generation failed"),
                "metadata": metadata,
            }

        return {
            "session_id": session_id,
            "status": "completed",
            "question_count": len(questions),
            "estimated_time_remaining_seconds": 0,
            "message": f"{len(questions)} questions ready",
            "metadata": metadata,
        }

    # Return status based on cache entry
    if status == "started":
        # Rough estimate: 10-30 seconds for question generation
        return {
            "session_id": session_id,
            "status": "started",
            "question_count": 0,
            "estimated_time_remaining_seconds": 20,
            "message": "Generating questions...",
        }
    elif status == "failed":
        return {
            "session_id": session_id,
            "status": "failed",
            "question_count": 0,
            "estimated_time_remaining_seconds": 0,
            "message": "Question generation failed",
        }
    else:
        # No status or "pending"
        return {
            "session_id": session_id,
            "status": "pending",
            "question_count": 0,
            "estimated_time_remaining_seconds": None,
            "message": "Question generation pending",
        }


# ── Complete study session ────────────────────────────────────


@router.post("/sessions/{session_id}/complete")
async def complete_study_session(
    session_id: int,
    body: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete session and return cached questions instantly."""
    session = (
        await db.execute(
            select(StudySession).where(
                StudySession.id == session_id,
                StudySession.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.completed = True
    session.ended_at = datetime.utcnow()
    if body and "actual_duration_mins" in body:
        session.actual_duration_mins = body["actual_duration_mins"]

    await db.commit()
    logger.info(f"Study session {session_id} completed")

    return {
        "session_id": session.id,
        "completed": True,
        "duration_mins": session.duration_mins,
        "actual_duration_mins": session.actual_duration_mins or session.duration_mins,
        "ended_at": session.ended_at.isoformat() if session.ended_at else "",
    }


# ── Background question generation ────────────────────────────


async def _generate_and_cache_questions(
    topic_id: int, user_id: int, session_id: int, previous_question_ids: list[int] | None = None
):
    """Generate questions in background and cache them with robust error handling.

    Features:
    - Status tracking (started, completed, failed)
    - Retry logic (up to 2 retries with exponential backoff)
    - Detailed timing information
    - Edge case handling (no questions, Ollama down, etc.)
    - Metadata storage with questions

    This runs immediately when session starts.
    Questions are ready when session ends.
    """
    from app.core.cache import cache

    start_time = time.time()
    max_retries = 2
    retry_count = 0
    last_error = None

    logger.info(
        f"🔄 Background generation STARTED: session={session_id} "
        f"topic={topic_id} user={user_id}"
    )

    # Set initial status
    try:
        await cache.set_pregen_status(topic_id, user_id, "started")
    except Exception as e:
        logger.warning(f"Failed to set initial status: {e}")

    while retry_count <= max_retries:
        attempt_start = time.time()

        try:
            async with AsyncSessionLocal() as db:
                # Verify topic exists and get topic details
                topic = (
                    await db.execute(select(Topic).where(Topic.id == topic_id))
                ).scalar_one_or_none()

                if not topic:
                    error_msg = f"Topic {topic_id} not found"
                    logger.error(f"❌ {error_msg}")
                    await cache.set_pregen_status(topic_id, user_id, "failed")
                    return

                # Check Ollama availability (if it's being used)
                try:
                    from app.core.ollama import ollama_client
                    if not await ollama_client.is_available():
                        raise Exception("Ollama service is unavailable")
                except Exception as ollama_error:
                    logger.warning(f"⚠️ Ollama health check failed: {ollama_error}")
                    if retry_count < max_retries:
                        raise  # Retry if Ollama is down
                    # On last attempt, continue anyway (fallback may work)

                # Generate questions (target 10, but accept whatever is available)
                gen_start = time.time()
                result = await orchestrator.generate_test(
                    topic_id=topic_id,
                    user_id=user_id,
                    question_count=10,
                    db=db,
                    extra_exclude_ids=previous_question_ids or [],
                )
                gen_time = time.time() - gen_start

                questions = result.get("questions", [])
                metadata = {
                    "session_id": session_id,
                    "topic_id": topic_id,
                    "topic_name": topic.name,
                    "user_id": user_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "generation_time_seconds": round(gen_time, 2),
                    "question_count": len(questions),
                    "attempt_number": retry_count + 1,
                    "source": result.get("source", "unknown"),
                }

                logger.info(
                    f"📊 Generated {len(questions)} questions for session={session_id} "
                    f"in {gen_time:.2f}s (attempt {retry_count + 1}/{max_retries + 1})"
                )

                # Handle edge cases
                if len(questions) == 0:
                    logger.warning(
                        f"⚠️ No questions available: session={session_id} "
                        f"topic={topic_id} ({topic.name}) - This topic has no questions in database!"
                    )
                    await cache.set_pregen_status(topic_id, user_id, "failed")

                    # Cache empty result with metadata for debugging
                    cache_data = {
                        "questions": [],
                        "metadata": {
                            **metadata,
                            "error": "No questions available for this topic",
                            "total_time_seconds": round(time.time() - start_time, 2),
                        }
                    }
                    await cache.cache_pregenerated_questions(
                        topic_id=topic_id,
                        user_id=user_id,
                        questions=[cache_data],  # Wrap in list for compatibility
                        ttl=3600,
                    )
                    return

                # Cache questions with metadata
                cache_data = {
                    "questions": questions,
                    "metadata": {
                        **metadata,
                        "total_time_seconds": round(time.time() - start_time, 2),
                        "cached_at": datetime.utcnow().isoformat(),
                    }
                }

                await cache.cache_pregenerated_questions(
                    topic_id=topic_id,
                    user_id=user_id,
                    questions=[cache_data],  # Wrap in list for storage
                    ttl=3600,  # 1 hour
                )

                # Set success status
                await cache.set_pregen_status(topic_id, user_id, "completed")

                total_time = time.time() - start_time
                logger.info(
                    f"✅ Background generation COMPLETED: session={session_id} "
                    f"cached {len(questions)} questions | "
                    f"gen_time={gen_time:.2f}s total_time={total_time:.2f}s "
                    f"attempts={retry_count + 1}"
                )
                return  # Success - exit function

        except Exception as e:
            last_error = e
            retry_count += 1
            attempt_time = time.time() - attempt_start

            logger.error(
                f"❌ Background generation attempt {retry_count}/{max_retries + 1} FAILED: "
                f"session={session_id} error={str(e)} attempt_time={attempt_time:.2f}s",
                exc_info=True
            )

            if retry_count <= max_retries:
                # Exponential backoff: 1s, 2s, 4s
                backoff_time = 2 ** (retry_count - 1)
                logger.info(
                    f"🔄 Retrying in {backoff_time}s... "
                    f"(attempt {retry_count + 1}/{max_retries + 1})"
                )
                await asyncio.sleep(backoff_time)
            else:
                # All retries exhausted
                total_time = time.time() - start_time
                logger.error(
                    f"❌ Background generation FAILED after {retry_count} attempts: "
                    f"session={session_id} total_time={total_time:.2f}s error={str(last_error)}"
                )

                # Set failed status
                try:
                    await cache.set_pregen_status(topic_id, user_id, "failed")

                    # Cache error metadata for debugging
                    error_data = {
                        "questions": [],
                        "metadata": {
                            "session_id": session_id,
                            "topic_id": topic_id,
                            "user_id": user_id,
                            "generated_at": datetime.utcnow().isoformat(),
                            "error": str(last_error),
                            "error_type": type(last_error).__name__,
                            "attempts": retry_count,
                            "total_time_seconds": round(total_time, 2),
                            "status": "failed",
                        }
                    }
                    await cache.cache_pregenerated_questions(
                        topic_id=topic_id,
                        user_id=user_id,
                        questions=[error_data],
                        ttl=600,  # 10 minutes for error cache
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache error metadata: {cache_error}")


# ── List sessions ─────────────────────────────────────────────


@router.get("/sessions")
async def list_study_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List study sessions for the current user (most recent first)."""
    sessions = (
        await db.execute(
            select(StudySession)
            .where(StudySession.user_id == current_user.id)
            .order_by(StudySession.started_at.desc())
            .limit(50)
        )
    ).scalars().all()

    return [
        {
            "session_id": s.id,
            "topic_id": s.topic_id,
            "duration_mins": s.duration_mins,
            "completed": s.completed,
            "started_at": s.started_at.isoformat() if s.started_at else "",
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        }
        for s in sessions
    ]


# ── Get single session ───────────────────────────────────────


@router.get("/sessions/{session_id}")
async def get_study_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific study session."""
    session = (
        await db.execute(
            select(StudySession).where(
                StudySession.id == session_id,
                StudySession.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.id,
        "topic_id": session.topic_id,
        "duration_mins": session.duration_mins,
        "completed": session.completed,
        "started_at": session.started_at.isoformat() if session.started_at else "",
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }
