"""Question Orchestrator — the heart of the StudyPulse RAG pipeline.

Coordinates between DB, Qdrant vector store, Redis cache, and Ollama LLM
to produce high-quality, non-repeating exam questions.

Pipeline:
  1. Check Redis cache for pre-generated questions (instant return)
  2. Retrieve previous-year questions from SQLite/Postgres
  3. Search Qdrant for semantic context (style reference for AI)
  4. Generate AI questions via Ollama (async, non-blocking)
  5. Save new questions to DB + index in Qdrant
  6. Combine, shuffle, return
"""
import json
import logging
import random
import time
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.models.exam import Exam, Subject, Topic
from app.models.mock_test import MockTest
from app.models.question import Question
from app.rag.question_generator import QuestionGenerator
from app.rag.vector_store import vector_store

logger = logging.getLogger(__name__)


class QuestionOrchestrator:
    """Orchestrates the full RAG pipeline for test generation."""

    def __init__(self):
        self._generator = QuestionGenerator()

    # ── Public API ────────────────────────────────────────────

    async def generate_test(
        self,
        topic_id: int,
        user_id: int,
        question_count: int | None = None,
        previous_year_ratio: float | None = None,
        db: AsyncSession | None = None,
    ) -> dict:
        """Generate a complete test for a user on a specific topic.

        Returns:
            {"questions": [...], "metadata": {...}}
        """
        t0 = time.time()
        question_count = question_count or settings.DEFAULT_QUESTION_COUNT
        previous_year_ratio = (
            previous_year_ratio
            if previous_year_ratio is not None
            else settings.PREVIOUS_YEAR_RATIO
        )

        # ── Step 0: Resolve topic hierarchy ───────────────────
        info = await self._resolve_topic(topic_id, db)
        if not info:
            logger.error(f"Topic {topic_id} not found")
            return {"questions": [], "metadata": {"error": "Topic not found"}}

        topic_name = info["topic_name"]
        subject_name = info["subject_name"]
        exam_name = info["exam_name"]
        exam_id = info["exam_id"]
        subject_id = info["subject_id"]

        logger.info(
            f"Pipeline: {exam_name} / {subject_name} / {topic_name} "
            f"count={question_count} user={user_id}"
        )

        # ── Step 1: Check cache ───────────────────────────────
        cached = await cache.get_pregenerated_questions(topic_id, user_id)
        if cached and len(cached) >= question_count:
            ms = int((time.time() - t0) * 1000)
            logger.info(f"CACHE HIT — {question_count} Qs in {ms}ms")
            return {
                "questions": cached[:question_count],
                "metadata": self._meta(
                    question_count, 0, question_count, True, ms,
                    topic_name, subject_name, exam_name,
                ),
            }

        # ── Step 2: User history (dedup) ──────────────────────
        history_ids = await self._user_history(user_id, topic_id, db)

        # ── Step 3: Previous-year questions ───────────────────
        # Get ALL questions from DB (AI generation disabled, so fetch full count)
        prev_target = question_count  # Changed: fetch all from DB instead of split
        prev_qs = await self._prev_year_questions(topic_id, prev_target, history_ids, db)
        actual_prev = len(prev_qs)
        ai_target = max(0, question_count - actual_prev)  # Will be 0 if we have enough DB questions

        # ── Step 4: Semantic context from Qdrant ──────────────
        context_qs: list[dict] = []
        if vector_store.available:
            context_qs = await vector_store.search_similar(
                query_text=f"{exam_name} {subject_name} {topic_name} questions",
                topic_id=topic_id,
                exam_id=exam_id,
                exclude_ids=history_ids,
                limit=5,
            )

        # ── Step 5: AI generation ─────────────────────────────
        ai_qs: list[dict] = []
        # DISABLED: Using only database questions (4700+ available) for fast response
        # AI generation with Ollama causes timeouts - enable only if needed
        if False and ai_target > 0 and settings.RAG_ENABLED:
            excluded_summaries = [q["question_text"][:100] for q in prev_qs]
            raw = await self._generator.generate(
                exam_name=exam_name,
                subject_name=subject_name,
                topic_name=topic_name,
                count=ai_target + 2,  # extras for quality headroom
                context_questions=context_qs or prev_qs[:3],
                excluded_summaries=excluded_summaries,
            )
            if raw:
                ai_qs = await self._persist_ai_questions(
                    raw[:ai_target], topic_id, exam_id, subject_id, db
                )
                # Index asynchronously in Qdrant (best-effort)
                if vector_store.available and ai_qs:
                    try:
                        await vector_store.add_questions(
                            [
                                {
                                    **q,
                                    "exam_id": exam_id,
                                    "subject_id": subject_id,
                                    "topic_id": topic_id,
                                    "is_previous_year": False,
                                }
                                for q in ai_qs
                            ]
                        )
                    except Exception as e:
                        logger.warning(f"Qdrant index failed (non-fatal): {e}")

        # ── Step 6: Combine, format, shuffle ──────────────────
        all_qs = self._format_for_client(prev_qs + ai_qs)
        random.shuffle(all_qs)
        all_qs = all_qs[:question_count]

        ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Pipeline done: {len(all_qs)} Qs "
            f"(prev={actual_prev} ai={len(ai_qs)}) {ms}ms"
        )
        return {
            "questions": all_qs,
            "metadata": self._meta(
                len(all_qs), actual_prev, len(ai_qs), False, ms,
                topic_name, subject_name, exam_name,
            ),
        }

    async def pre_generate(
        self,
        topic_id: int,
        user_id: int,
        question_count: int | None = None,
        db: AsyncSession | None = None,
    ):
        """Background pre-generation: run pipeline and store result in Redis."""
        question_count = question_count or settings.DEFAULT_QUESTION_COUNT
        try:
            await cache.set_pregen_status(topic_id, user_id, "started")
            result = await self.generate_test(
                topic_id=topic_id,
                user_id=user_id,
                question_count=question_count,
                db=db,
            )
            if result["questions"]:
                await cache.cache_pregenerated_questions(
                    topic_id, user_id, result["questions"], ttl=3600
                )
                await cache.set_pregen_status(topic_id, user_id, "completed")
                logger.info(
                    f"Pre-gen OK: {len(result['questions'])} Qs "
                    f"topic={topic_id} user={user_id}"
                )
            else:
                await cache.set_pregen_status(topic_id, user_id, "failed")
        except Exception as e:
            await cache.set_pregen_status(topic_id, user_id, "failed")
            logger.error(f"Pre-gen failed: {e}")

    # ── Private helpers ───────────────────────────────────────

    async def _resolve_topic(self, topic_id: int, db: AsyncSession) -> dict | None:
        row = (
            await db.execute(
                select(Topic, Subject, Exam)
                .join(Subject, Topic.subject_id == Subject.id)
                .join(Exam, Subject.exam_id == Exam.id)
                .where(Topic.id == topic_id)
            )
        ).first()
        if not row:
            return None
        t, s, e = row
        return {
            "topic_name": t.name,
            "subject_name": s.name,
            "exam_name": e.name,
            "exam_id": e.id,
            "subject_id": s.id,
        }

    async def _user_history(
        self, user_id: int, topic_id: int, db: AsyncSession
    ) -> list[int]:
        try:
            rows = (
                await db.execute(
                    select(MockTest.question_ids).where(
                        MockTest.user_id == user_id,
                        MockTest.topic_id == topic_id,
                    )
                )
            ).scalars().all()
            ids: set[int] = set()
            for row in rows:
                if isinstance(row, list):
                    ids.update(row)
                elif isinstance(row, str):
                    try:
                        parsed = json.loads(row)
                        if isinstance(parsed, list):
                            ids.update(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass
            return list(ids)
        except Exception as e:
            logger.warning(f"History lookup failed: {e}")
            return []

    async def _prev_year_questions(
        self,
        topic_id: int,
        count: int,
        exclude_ids: list[int],
        db: AsyncSession,
    ) -> list[dict]:
        try:
            q = select(Question).where(
                Question.topic_id == topic_id,
                Question.source != "AI",
            )
            if exclude_ids:
                q = q.where(Question.id.notin_(exclude_ids))
            q = q.order_by(func.random()).limit(count)

            rows = (await db.execute(q)).scalars().all()
            return [
                {
                    "id": r.id,
                    "question_text": r.question_text,
                    "options": r.options if isinstance(r.options, dict) else {},
                    "correct_answer": r.correct_answer,
                    "explanation": r.explanation or "",
                    "difficulty": r.difficulty or "medium",
                    "source": r.source or "PREVIOUS",
                    "year": r.year,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Prev-year query failed: {e}")
            return []

    async def _persist_ai_questions(
        self,
        questions: list[dict],
        topic_id: int,
        exam_id: int,
        subject_id: int,
        db: AsyncSession,
    ) -> list[dict]:
        saved: list[dict] = []
        try:
            for q in questions:
                row = Question(
                    topic_id=topic_id,
                    question_text=q["question_text"],
                    options=q["options"],
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", "medium"),
                    source="AI",
                )
                db.add(row)
                await db.flush()
                saved.append(
                    {
                        "id": row.id,
                        "question_text": q["question_text"],
                        "options": q["options"],
                        "correct_answer": q["correct_answer"],
                        "explanation": q.get("explanation", ""),
                        "difficulty": q.get("difficulty", "medium"),
                        "source": "AI",
                    }
                )
            await db.commit()
            logger.info(f"Saved {len(saved)} AI questions to DB")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist AI questions: {e}")
            # Return unsaved questions so the test can still proceed
            for q in questions:
                if not any(s["question_text"] == q["question_text"] for s in saved):
                    saved.append(
                        {
                            "id": abs(hash(q["question_text"])) % 100_000 + 100_000,
                            "question_text": q["question_text"],
                            "options": q["options"],
                            "correct_answer": q["correct_answer"],
                            "explanation": q.get("explanation", ""),
                            "difficulty": q.get("difficulty", "medium"),
                            "source": "AI",
                        }
                    )
        return saved

    @staticmethod
    def _format_for_client(questions: list[dict]) -> list[dict]:
        """Strip answers — client only sees questions during the test."""
        return [
            {
                "id": q.get("id", 0),
                "question_text": q.get("question_text", ""),
                "options": q.get("options", {}),
                "difficulty": q.get("difficulty", "medium"),
                "source": q.get("source", "PREVIOUS"),
                "marks": q.get("marks", 1),
            }
            for q in questions
        ]

    @staticmethod
    def _meta(total, prev, ai, cached, ms, topic, subject, exam):
        return {
            "total": total,
            "previous_year": prev,
            "ai_generated": ai,
            "cached": cached,
            "generation_time_ms": ms,
            "topic": topic,
            "subject": subject,
            "exam": exam,
        }


# Singleton
orchestrator = QuestionOrchestrator()
