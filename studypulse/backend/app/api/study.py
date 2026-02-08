"""Study Session API — timer management and background pre-generation.

When a user starts a study session, we kick off a background task that
pre-generates questions via the RAG pipeline. By the time the user
finishes studying, questions are waiting in Redis cache and can be
served in milliseconds.
"""
import asyncio
import logging
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
    """Start a study session and trigger background question pre-generation.

    The pre-generation runs after a short delay (configurable) so the
    study session is properly saved first.  It uses its own DB session
    to survive after this HTTP request completes.
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

    # Fire background pre-generation (non-blocking)
    asyncio.create_task(
        _pre_generate_background(data.topic_id, current_user.id)
    )

    logger.info(
        f"Study session {session.id} started: topic={data.topic_id} "
        f"duration={data.duration_mins}min user={current_user.id}"
    )

    return {
        "session_id": session.id,
        "user_id": current_user.id,
        "topic_id": data.topic_id,
        "topic_name": topic.name,
        "duration_mins": data.duration_mins,
        "completed": False,
        "started_at": session.started_at.isoformat() if session.started_at else "",
        "pre_generation": "started",
    }


# ── Complete study session ────────────────────────────────────


@router.post("/sessions/{session_id}/complete")
async def complete_study_session(
    session_id: int,
    body: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a study session as completed."""
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


# ── Background pre-generation ─────────────────────────────────


async def _pre_generate_background(topic_id: int, user_id: int):
    """Pre-generate questions in the background using its own DB session.

    IMPORTANT: This task outlives the HTTP request, so it MUST create
    its own database session via AsyncSessionLocal — NOT reuse the
    request-scoped session from get_db().
    """
    delay = settings.PRE_GENERATION_DELAY_SECONDS
    logger.info(
        f"Pre-gen: waiting {delay}s before generating for "
        f"topic={topic_id} user={user_id}"
    )
    await asyncio.sleep(delay)

    try:
        async with AsyncSessionLocal() as db:
            await orchestrator.pre_generate(
                topic_id=topic_id,
                user_id=user_id,
                question_count=settings.DEFAULT_QUESTION_COUNT,
                db=db,
            )
    except Exception as e:
        logger.error(f"Background pre-gen failed: {e}", exc_info=True)
