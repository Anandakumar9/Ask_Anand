"""Mock Test API — test creation, submission, grading, question rating, history.

Uses the RAG orchestrator for intelligent question generation.
Maintains full API compatibility with the mobile app.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.exam import Exam, Subject, Topic
from app.models.mock_test import MockTest, QuestionResponse
from app.models.question import Question, QuestionRating
from app.models.user import User
from app.rag.orchestrator import orchestrator
from app.schemas.mock_test import (
    AnswerItem,
    MockTestCreate,
    RateQuestionRequest,
    SubmitAnswers,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Start test ────────────────────────────────────────────────


@router.post("/start")
async def start_mock_test(
    test_data: MockTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a mock test — generates questions via RAG pipeline.

    If questions were pre-generated during the study session,
    they are served from Redis cache in milliseconds.
    Otherwise, the full pipeline runs on-demand.
    """
    # Verify topic
    topic = (
        await db.execute(select(Topic).where(Topic.id == test_data.topic_id))
    ).scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Generate via orchestrator (cache-first, then DB+AI)
    result = await orchestrator.generate_test(
        topic_id=test_data.topic_id,
        user_id=current_user.id,
        question_count=test_data.question_count,
        previous_year_ratio=test_data.previous_year_ratio,
        db=db,
    )

    questions = result["questions"]
    if not questions:
        raise HTTPException(
            status_code=503,
            detail="Could not generate questions. Is Ollama running?",
        )

    # Persist test record
    qids = [q["id"] for q in questions]
    test = MockTest(
        user_id=current_user.id,
        topic_id=test_data.topic_id,
        session_id=test_data.session_id,
        question_ids=json.dumps(qids),
        total_questions=len(questions),
        time_limit_seconds=test_data.time_limit_seconds,
        status="in_progress",
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    logger.info(
        f"Test {test.id} started: {len(questions)} Qs, "
        f"cache={result['metadata'].get('cached', False)}, "
        f"{result['metadata'].get('generation_time_ms', 0)}ms"
    )

    return {
        "test_id": test.id,
        "questions": questions,  # answers stripped by orchestrator
        "time_limit_seconds": test_data.time_limit_seconds,
        "total_questions": len(questions),
        "metadata": result.get("metadata", {}),
    }


# ── Submit answers ────────────────────────────────────────────


@router.post("/{test_id}/submit")
async def submit_mock_test(
    test_id: int,
    submission: SubmitAnswers,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers, grade, and return full results."""
    test = (
        await db.execute(
            select(MockTest).where(
                MockTest.id == test_id, MockTest.user_id == current_user.id
            )
        )
    ).scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.status == "completed":
        raise HTTPException(status_code=400, detail="Test already submitted")

    # Load questions
    qids = (
        json.loads(test.question_ids)
        if isinstance(test.question_ids, str)
        else test.question_ids or []
    )
    q_map = {
        q.id: q
        for q in (
            await db.execute(select(Question).where(Question.id.in_(qids)))
        ).scalars().all()
    }

    # Build response lookup
    resp_map = {r.question_id: r.answer for r in (submission.responses or [])}

    correct = wrong = unanswered = 0
    question_results = []

    for qid in qids:
        q = q_map.get(qid)
        if not q:
            continue

        user_ans = resp_map.get(qid)
        is_correct = False

        if not user_ans:
            unanswered += 1
        elif user_ans.strip().upper() == q.correct_answer.strip().upper():
            is_correct = True
            correct += 1
        else:
            wrong += 1

        # Persist individual response
        db.add(
            QuestionResponse(
                mock_test_id=test_id,
                question_id=qid,
                user_answer=user_ans or "",
                is_correct=is_correct,
                time_spent_seconds=0,
            )
        )

        opts = q.options
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except (json.JSONDecodeError, TypeError):
                opts = {}

        question_results.append(
            {
                "id": qid,
                "question_id": qid,
                "question_text": q.question_text,
                "options": opts if isinstance(opts, dict) else {},
                "correct_answer": q.correct_answer,
                "user_answer": user_ans or "",
                "is_correct": is_correct,
                "explanation": q.explanation or "",
                "source": q.source or "PREVIOUS",
            }
        )

    total = len(qids)
    pct = round(correct / total * 100, 1) if total else 0
    star = pct >= settings.STAR_THRESHOLD_PERCENTAGE

    # Speed rating
    tpq = submission.total_time_seconds / total if total else 0
    speed = (
        "lightning" if tpq < 30 else "fast" if tpq < 60 else "steady" if tpq < 90 else "careful"
    )

    # Update test record
    test.status = "completed"
    test.correct_answers = correct
    test.score_percentage = pct
    test.star_earned = star
    test.time_taken_seconds = submission.total_time_seconds
    test.completed_at = datetime.utcnow()

    if star:
        current_user.total_stars = (current_user.total_stars or 0) + 1

    await db.commit()

    # Feedback
    if pct >= 90:
        fb = "Outstanding! You've mastered this topic!"
    elif pct >= settings.STAR_THRESHOLD_PERCENTAGE:
        fb = "Great job! You earned a star!"
    elif pct >= 50:
        fb = "Good effort! Review the explanations and try again."
    else:
        fb = "Keep studying! Review the topic and retake the test."

    return {
        "test_id": test_id,
        "total_questions": total,
        "correct_count": correct,
        "incorrect_count": wrong,
        "unanswered_count": unanswered,
        "score_percentage": pct,
        "star_earned": star,
        "passed": star,
        "time_taken_seconds": submission.total_time_seconds,
        "feedback_message": fb,
        "accuracy": pct,
        "speed_rating": speed,
        "questions": question_results,
    }


# ── Get results ───────────────────────────────────────────────


@router.get("/{test_id}/results")
async def get_test_results(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve graded results for a completed test."""
    test = (
        await db.execute(
            select(MockTest).where(
                MockTest.id == test_id, MockTest.user_id == current_user.id
            )
        )
    ).scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.status != "completed":
        raise HTTPException(status_code=400, detail="Test not yet completed")

    qids = (
        json.loads(test.question_ids)
        if isinstance(test.question_ids, str)
        else test.question_ids or []
    )
    q_map = {
        q.id: q
        for q in (
            await db.execute(select(Question).where(Question.id.in_(qids)))
        ).scalars().all()
    }
    resp_map = {
        r.question_id: r
        for r in (
            await db.execute(
                select(QuestionResponse).where(QuestionResponse.mock_test_id == test_id)
            )
        ).scalars().all()
    }

    question_results = []
    for qid in qids:
        q = q_map.get(qid)
        r = resp_map.get(qid)
        if not q:
            continue
        opts = q.options
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = {}
        question_results.append(
            {
                "id": qid,
                "question_id": qid,
                "question_text": q.question_text,
                "options": opts if isinstance(opts, dict) else {},
                "correct_answer": q.correct_answer,
                "user_answer": r.user_answer if r else "",
                "is_correct": r.is_correct if r else False,
                "explanation": q.explanation or "",
                "source": q.source or "PREVIOUS",
            }
        )

    return {
        "test_id": test_id,
        "total_questions": test.total_questions,
        "correct_count": test.correct_answers or 0,
        "incorrect_count": (test.total_questions or 0) - (test.correct_answers or 0),
        "unanswered_count": 0,
        "score_percentage": test.score_percentage or 0,
        "star_earned": test.star_earned or False,
        "passed": test.star_earned or False,
        "time_taken_seconds": test.time_taken_seconds or 0,
        "feedback_message": "",
        "accuracy": test.score_percentage or 0,
        "speed_rating": "",
        "questions": question_results,
    }


# ── Rate a question ───────────────────────────────────────────


@router.post("/{test_id}/rate")
async def rate_question(
    test_id: int,
    data: RateQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rate an AI-generated question's quality (1-5)."""
    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    q = (
        await db.execute(select(Question).where(Question.id == data.question_id))
    ).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    db.add(
        QuestionRating(
            question_id=data.question_id,
            user_id=current_user.id,
            rating=data.rating,
            feedback_text=data.feedback or "",
        )
    )

    # Update rolling average
    q.rating_count = (q.rating_count or 0) + 1
    total_rating = (q.avg_rating or 0) * (q.rating_count - 1) + data.rating
    q.avg_rating = total_rating / q.rating_count

    await db.commit()
    return {"status": "rated", "question_id": data.question_id, "rating": data.rating}


# ── Test history ──────────────────────────────────────────────


@router.get("/history/all")
async def get_test_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """All completed tests for the current user."""
    tests = (
        await db.execute(
            select(MockTest)
            .where(MockTest.user_id == current_user.id, MockTest.status == "completed")
            .order_by(MockTest.completed_at.desc())
        )
    ).scalars().all()

    out = []
    for t in tests:
        row = (
            await db.execute(
                select(Topic, Subject)
                .join(Subject, Topic.subject_id == Subject.id)
                .where(Topic.id == t.topic_id)
            )
        ).first()
        out.append(
            {
                "id": t.id,
                "topic_name": row[0].name if row else "Unknown",
                "subject_name": row[1].name if row else "Unknown",
                "score_percentage": t.score_percentage or 0,
                "star_earned": t.star_earned or False,
                "total_questions": t.total_questions or 0,
                "correct_count": t.correct_answers or 0,
                "time_taken_seconds": t.time_taken_seconds or 0,
                "completed_at": t.completed_at.isoformat() if t.completed_at else "",
            }
        )
    return out
