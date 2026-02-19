"""Question Orchestrator — the heart of the StudyPulse RAG pipeline.

Coordinates between DB, vector store (Qdrant or PageIndex), Redis cache, and Ollama LLM
to produce high-quality, non-repeating exam questions.

Pipeline:
  1. Check Redis cache for pre-generated questions (instant return)
  2. Retrieve previous-year questions from SQLite/Postgres
  3. Search vector store for semantic context (style reference for AI)
  4. Generate AI questions via Ollama (async, non-blocking)
  5. Save new questions to DB + index in vector store
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
from app.rag.smart_selector import smart_selector

# Dynamic vector store selection (Qdrant or PageIndex)
if settings.USE_PAGEINDEX:
    from app.rag.pageindex_adapter import pageindex_store as vector_store
    logger = logging.getLogger(__name__)
    logger.info("Using PageIndex for vector search (lightweight, embedded)")
else:
    from app.rag.vector_store import vector_store
    logger = logging.getLogger(__name__)
    logger.info("Using Qdrant for vector search (server-based)")


class QuestionOrchestrator:
    """Orchestrates the full RAG pipeline for test generation."""

    def __init__(self):
        self._generator = QuestionGenerator()
        self.metrics = {
            "total_tests_generated": 0,
            "total_ai_questions": 0,
            "total_db_questions": 0,
            "ai_generation_failures": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_generation_time_ms": 0,
        }

    # ── Public API ────────────────────────────────────────────

    async def generate_test(
        self,
        topic_id: int,
        user_id: int,
        question_count: int | None = None,
        previous_year_ratio: float | None = None,
        db: AsyncSession | None = None,
        extra_exclude_ids: list[int] | None = None,
    ) -> dict:
        """Generate a complete test for a user on a specific topic.

        FULL RAG-ENABLED VERSION:
        - **Checks cache first** for pre-generated questions (instant return)
        - Fetches questions from database
        - Generates AI questions if needed (RAG enabled)
        - Uses SmartSelector for adaptive difficulty
        - Persists AI questions to DB
        - Returns optimally selected questions

        Returns:
            {"questions": [...], "metadata": {...}}
        """
        t0 = time.time()
        question_count = question_count or settings.DEFAULT_QUESTION_COUNT
        previous_year_ratio = previous_year_ratio if previous_year_ratio is not None else settings.PREVIOUS_YEAR_RATIO

        # Ensure minimum 10 questions
        question_count = max(question_count, 10)

        # ── Step 0: Check cache for pre-generated questions ───
        cached_data = await cache.get_pregenerated_questions(topic_id, user_id)
        if cached_data and len(cached_data) > 0:
            # Extract questions and metadata from cache entry
            cache_entry = cached_data[0] if isinstance(cached_data[0], dict) and "questions" in cached_data[0] else None

            if cache_entry:
                questions = cache_entry.get("questions", [])
                metadata = cache_entry.get("metadata", {})

                # Check if cache has enough questions and is valid (not an error cache)
                if len(questions) >= question_count and metadata.get("status") != "failed":
                    # Format questions for client
                    formatted = self._format_for_client(questions[:question_count])
                    ms = int((time.time() - t0) * 1000)

                    self.metrics["cache_hits"] += 1
                    logger.info(
                        f"✅ CACHE HIT: Returning {len(formatted)} pre-generated questions "
                        f"for topic={topic_id} user={user_id} in {ms}ms"
                    )

                    return {
                        "questions": formatted,
                        "metadata": {
                            **metadata,
                            "cached": True,
                            "cache_hit": True,
                            "retrieval_time_ms": ms,
                            "total_questions": len(formatted),
                        }
                    }
                else:
                    logger.info(
                        f"⚠️ Cache entry exists but insufficient/invalid: "
                        f"{len(questions)} questions (need {question_count}), "
                        f"status={metadata.get('status', 'ok')} - regenerating"
                    )
            else:
                # Old format cache (backward compatibility)
                questions = cached_data
                if len(questions) >= question_count:
                    formatted = self._format_for_client(questions[:question_count])
                    ms = int((time.time() - t0) * 1000)

                    self.metrics["cache_hits"] += 1
                    logger.info(
                        f"✅ CACHE HIT (legacy): Returning {len(formatted)} questions "
                        f"for topic={topic_id} user={user_id} in {ms}ms"
                    )

                    return {
                        "questions": formatted,
                        "metadata": {
                            "cached": True,
                            "cache_hit": True,
                            "retrieval_time_ms": ms,
                            "total_questions": len(formatted),
                            "format": "legacy"
                        }
                    }

        # Cache miss - proceed with full generation
        self.metrics["cache_misses"] += 1
        logger.info(f"📭 CACHE MISS: Generating questions for topic={topic_id} user={user_id}")

        # ── Step 1: Resolve topic hierarchy ───────────────────
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
            f"Generating test: {exam_name} / {subject_name} / {topic_name} "
            f"count={question_count} user={user_id} ratio={previous_year_ratio}"
        )

        # ── Step 1: Get user history (for deduplication) ──────
        history_ids = await self._user_history(user_id, topic_id, db)
        # Merge in any client-supplied IDs (from previous sessions in this browser)
        if extra_exclude_ids:
            history_ids = list(set(history_ids) | set(extra_exclude_ids))

        # ── Step 2: Fetch questions from database ─────────────
        db_target_count = int(question_count * previous_year_ratio) if settings.RAG_ENABLED else question_count
        db_questions = await self._prev_year_questions(
            topic_id, db_target_count * 2, history_ids, db  # Oversample for SmartSelector
        )

        # Track if we're using fallback questions
        using_fallback = False
        fallback_source = None

        # Fallback: If topic has no questions, try similar topics
        if not db_questions:
            logger.warning(
                f"Topic {topic_id} ('{topic_name}') has no questions. "
                f"Attempting fallback to similar topics..."
            )
            db_questions = await self._get_similar_topic_questions(
                topic_id, db_target_count * 2, history_ids, db
            )
            if db_questions:
                using_fallback = True
                fallback_source = "similar_topics"
                logger.info(
                    f"Successfully fetched {len(db_questions)} questions from similar topics!"
                )

        # ── Step 3: Generate AI questions if RAG enabled ──────
        ai_questions = []
        if settings.RAG_ENABLED:
            # Check if Ollama is available before attempting AI generation
            from app.core.ollama import ollama_client
            ollama_available = await ollama_client.is_available()

            if not ollama_available:
                logger.warning(
                    f"⚠️  Ollama not available. RAG is ENABLED but LLM is not running. "
                    f"Falling back to DB questions only."
                )
                # Increase DB question count to compensate for missing AI questions
                ai_target_count = question_count - db_target_count
                if ai_target_count > 0:
                    additional_questions = await self._prev_year_questions(
                        topic_id, ai_target_count, history_ids + [q["id"] for q in db_questions], db
                    )
                    db_questions.extend(additional_questions)
                    logger.info(
                        f"Ollama unavailable - fetched {len(additional_questions)} additional DB questions "
                        f"(total: {len(db_questions)})"
                    )
            else:
                # Ollama is available, proceed with AI generation
                ai_target_count = question_count - db_target_count

                try:
                    # Get context questions from vector store (style reference)
                    context = await vector_store.search_similar(
                        query_text=f"{exam_name} {subject_name} {topic_name} questions",
                        limit=5,
                        topic_id=topic_id
                    )
                    context_questions = [{"question_text": c.get("question_text", "")} for c in context] if context else None

                    # Generate AI questions
                    logger.info(f"Generating {ai_target_count} AI questions...")
                    ai_generated = await self._generator.generate(
                        exam_name=exam_name,
                        subject_name=subject_name,
                        topic_name=topic_name,
                        count=ai_target_count,
                        context_questions=context_questions,
                        excluded_summaries=[q["question_text"][:80] for q in db_questions],
                    )

                    # Persist AI questions to DB
                    if ai_generated:
                        ai_questions = await self._persist_ai_questions(
                            ai_generated, topic_id, exam_id, subject_id, db
                        )
                        logger.info(f"Generated and saved {len(ai_questions)} AI questions")
                        self.metrics["total_ai_questions"] += len(ai_questions)

                        # Check if AI generated enough questions
                        if len(ai_questions) < ai_target_count:
                            shortage = ai_target_count - len(ai_questions)
                            logger.warning(
                                f"⚠️  AI only generated {len(ai_questions)}/{ai_target_count} questions. "
                                f"Fetching {shortage} additional DB questions as fallback."
                            )
                            # Fetch additional DB questions to meet target (only if DB has questions)
                            if len(db_questions) > 0 or db_target_count > 0:
                                additional_questions = await self._prev_year_questions(
                                    topic_id, shortage, history_ids + [q["id"] for q in db_questions], db
                                )
                                db_questions.extend(additional_questions)
                                logger.info(f"Added {len(additional_questions)} DB questions as fallback")
                    else:
                        logger.warning("AI generation returned no questions - using DB fallback")
                        self.metrics["ai_generation_failures"] += 1
                        # Only fetch DB fallback if topic actually has DB questions
                        if len(db_questions) > 0 or db_target_count > 0:
                            # Fetch all questions from DB as fallback
                            additional_questions = await self._prev_year_questions(
                                topic_id, ai_target_count, history_ids + [q["id"] for q in db_questions], db
                            )
                            db_questions.extend(additional_questions)
                            logger.info(f"AI failed - using {len(additional_questions)} DB questions as fallback")
                        else:
                            logger.error(
                                f"❌ Topic '{topic_name}' has no DB questions and AI generation failed. "
                                f"Cannot generate test!"
                            )

                except Exception as e:
                    logger.error(f"AI generation failed: {e} - falling back to DB questions only")
                    self.metrics["ai_generation_failures"] += 1
                    # Only fetch DB fallback if topic actually has DB questions
                    if len(db_questions) > 0 or db_target_count > 0:
                        # Fallback: fetch more DB questions if AI generation fails
                        additional_questions = await self._prev_year_questions(
                            topic_id, ai_target_count, history_ids + [q["id"] for q in db_questions], db
                        )
                        db_questions.extend(additional_questions)
                        logger.info(f"Exception in AI - using {len(additional_questions)} DB questions as fallback")
                    else:
                        logger.error(
                            f"❌ Topic '{topic_name}' has no DB questions and AI generation threw exception: {e}"
                        )

        # ── Step 4: Combine and use SmartSelector ─────────────
        all_available = db_questions + ai_questions

        # Final safety check: ensure we have at least the minimum required questions
        if len(all_available) < question_count:
            logger.warning(
                f"⚠️  Only {len(all_available)} questions available (target: {question_count}). "
                f"Attempting to fetch more from database..."
            )
            # Try to fetch more questions without history filter if needed
            shortage = question_count - len(all_available)
            final_fallback = await self._prev_year_questions(
                topic_id, shortage, [q["id"] for q in all_available], db
            )
            all_available.extend(final_fallback)
            logger.info(f"Final fallback added {len(final_fallback)} questions. Total: {len(all_available)}")

        if len(all_available) < question_count:
            logger.error(
                f"❌ CRITICAL: Only {len(all_available)} questions available (target: {question_count}). "
                f"Cannot meet minimum requirement!"
            )
            selected_questions = all_available  # Use all available
        else:
            # Use SmartSelector for adaptive difficulty selection
            selected_questions = await smart_selector.select_questions(
                available_questions=all_available,
                user_id=user_id,
                topic_id=topic_id,
                target_count=question_count,
                db=db
            )

        # ── Step 5: Format and return ─────────────────────────
        formatted_questions = self._format_for_client(selected_questions)

        ms = int((time.time() - t0) * 1000)

        # Update metrics
        self.metrics["total_tests_generated"] += 1
        self.metrics["total_db_questions"] += min(len(db_questions), len(formatted_questions))
        self.metrics["avg_generation_time_ms"] = (
            (self.metrics["avg_generation_time_ms"] * (self.metrics["total_tests_generated"] - 1) + ms)
            / self.metrics["total_tests_generated"]
        ) if self.metrics["total_tests_generated"] > 0 else ms

        logger.info(
            f"Generated {len(formatted_questions)} questions "
            f"(DB: {len(db_questions)}, AI: {len(ai_questions)}) in {ms}ms"
        )

        return {
            "questions": formatted_questions,
            "metadata": {
                "total_questions": len(formatted_questions),
                "from_db": min(len(db_questions), len(formatted_questions)),
                "from_ai": len(ai_questions),
                "cached": False,
                "generation_time_ms": ms,
                "topic": topic_name,
                "subject": subject_name,
                "exam": exam_name,
                "rag_enabled": settings.RAG_ENABLED,
                "using_fallback": using_fallback,
                "fallback_source": fallback_source,
            },
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
            # Oversample with LIMIT to reduce memory usage (fetch 3x requested count)
            # This provides enough variety while avoiding loading entire table
            oversample_limit = max(count * 3, 50)  # At least 50 for variety

            q = select(Question).where(
                Question.topic_id == topic_id,
                Question.source != "AI",
            )
            if exclude_ids:
                q = q.where(Question.id.notin_(exclude_ids))

            # Add LIMIT for performance optimization
            q = q.limit(oversample_limit)

            rows = (await db.execute(q)).scalars().all()

            # Convert to list and use Python's random.sample for better randomization
            all_questions = [
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

            # Use random.sample to pick unique questions without SQL randomness
            if len(all_questions) <= count:
                return all_questions
            return random.sample(all_questions, count)

        except Exception as e:
            logger.error(f"Prev-year query failed: {e}")
            return []

    async def _get_similar_topic_questions(
        self,
        topic_id: int,
        count: int,
        exclude_ids: list[int],
        db: AsyncSession,
    ) -> list[dict]:
        """Fetch questions from similar topics when the requested topic has no questions.

        Fallback hierarchy:
        1. Same subject, different topics
        2. Same exam, different subjects
        3. Any topic from the database
        """
        try:
            # Get topic info
            topic_info = await self._resolve_topic(topic_id, db)
            if not topic_info:
                logger.error(f"Cannot resolve topic {topic_id} for fallback")
                return []

            subject_id = topic_info["subject_id"]
            exam_id = topic_info["exam_id"]

            logger.info(
                f"Topic {topic_id} has no questions. "
                f"Attempting fallback to similar topics..."
            )

            # Strategy 1: Try other topics in the same subject
            same_subject_topics = (
                await db.execute(
                    select(Topic.id)
                    .where(Topic.subject_id == subject_id, Topic.id != topic_id)
                )
            ).scalars().all()

            if same_subject_topics:
                logger.info(
                    f"Fallback strategy 1: Fetching from {len(same_subject_topics)} "
                    f"topics in same subject (subject_id={subject_id})"
                )
                q = select(Question).where(
                    Question.topic_id.in_(same_subject_topics),
                    Question.source != "AI"
                )
                if exclude_ids:
                    q = q.where(Question.id.notin_(exclude_ids))
                q = q.limit(max(count * 3, 50))

                rows = (await db.execute(q)).scalars().all()
                if rows:
                    questions = self._format_question_list(rows)
                    return random.sample(questions, min(count, len(questions)))

            # Strategy 2: Try other subjects in the same exam
            same_exam_subjects = (
                await db.execute(
                    select(Subject.id)
                    .where(Subject.exam_id == exam_id, Subject.id != subject_id)
                )
            ).scalars().all()

            if same_exam_subjects:
                logger.info(
                    f"Fallback strategy 2: Fetching from {len(same_exam_subjects)} "
                    f"subjects in same exam (exam_id={exam_id})"
                )
                # Get topics from those subjects
                related_topics = (
                    await db.execute(
                        select(Topic.id)
                        .where(Topic.subject_id.in_(same_exam_subjects))
                    )
                ).scalars().all()

                if related_topics:
                    q = select(Question).where(
                        Question.topic_id.in_(related_topics),
                        Question.source != "AI"
                    )
                    if exclude_ids:
                        q = q.where(Question.id.notin_(exclude_ids))
                    q = q.limit(max(count * 3, 50))

                    rows = (await db.execute(q)).scalars().all()
                    if rows:
                        questions = self._format_question_list(rows)
                        return random.sample(questions, min(count, len(questions)))

            # Strategy 3: Last resort - fetch from any available topic
            logger.info("Fallback strategy 3: Fetching from any available topic")
            q = select(Question).where(Question.source != "AI")
            if exclude_ids:
                q = q.where(Question.id.notin_(exclude_ids))
            q = q.limit(max(count * 3, 50))

            rows = (await db.execute(q)).scalars().all()
            if rows:
                questions = self._format_question_list(rows)
                return random.sample(questions, min(count, len(questions)))

            logger.error("No questions found in database at all")
            return []

        except Exception as e:
            logger.error(f"Similar topic fallback failed: {e}")
            return []

    @staticmethod
    def _format_question_list(rows) -> list[dict]:
        """Convert SQLAlchemy Question rows to dict format."""
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

            # Single flush after all questions added (faster than per-question flush)
            await db.flush()

            # Build saved list after flush (now all rows have IDs)
            for row in db.new:
                if isinstance(row, Question):
                    saved.append(
                        {
                            "id": row.id,
                            "question_text": row.question_text,
                            "options": row.options,
                            "correct_answer": row.correct_answer,
                            "explanation": row.explanation or "",
                            "difficulty": row.difficulty or "medium",
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

    def get_metrics(self) -> dict:
        """Get RAG pipeline performance metrics."""
        generator_metrics = self._generator.get_metrics()
        return {
            "orchestrator": {
                "total_tests_generated": self.metrics["total_tests_generated"],
                "total_db_questions": self.metrics["total_db_questions"],
                "ai_generation_failures": self.metrics["ai_generation_failures"],
                "cache_hits": self.metrics["cache_hits"],
                "cache_misses": self.metrics["cache_misses"],
                "avg_generation_time_ms": round(self.metrics["avg_generation_time_ms"], 2),
            },
            "generator": generator_metrics,
            "ai_questions_total": self.metrics["total_ai_questions"],
            "success_rate": (
                (self.metrics["total_tests_generated"] - self.metrics["ai_generation_failures"])
                / self.metrics["total_tests_generated"] * 100
            ) if self.metrics["total_tests_generated"] > 0 else 100.0,
        }


# Singleton
orchestrator = QuestionOrchestrator()
