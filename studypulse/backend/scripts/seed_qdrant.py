"""Seed existing questions from the database into Qdrant vector store.

Run once after setting up Qdrant to index all existing questions
for semantic search and deduplication.

Usage:
    cd studypulse/backend
    python -m scripts.seed_qdrant
"""
import asyncio
import logging
import sys
import os

# Add parent dir to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal, engine
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from app.rag.vector_store import vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def seed_qdrant():
    """Load all questions from DB and index them in Qdrant."""
    logger.info("Initializing vector store...")
    await vector_store.initialize()

    if not vector_store.available:
        logger.error("Qdrant not available. Is it running on localhost:6333?")
        return

    async with AsyncSessionLocal() as db:
        # Count questions
        total = (await db.execute(select(func.count(Question.id)))).scalar()
        logger.info(f"Found {total} questions in database")

        if total == 0:
            logger.warning("No questions to index. Run seed_data.py first.")
            return

        # Fetch all questions with their topic → subject → exam hierarchy
        result = await db.execute(
            select(Question, Topic, Subject, Exam)
            .join(Topic, Question.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Exam, Subject.exam_id == Exam.id)
        )

        batch = []
        batch_size = 50
        indexed = 0

        for row in result.all():
            q, topic, subject, exam = row

            opts = q.options
            if isinstance(opts, str):
                import json
                try:
                    opts = json.loads(opts)
                except Exception:
                    opts = {}

            batch.append({
                "id": q.id,
                "question_text": q.question_text,
                "options": opts if isinstance(opts, dict) else {},
                "correct_answer": q.correct_answer,
                "explanation": q.explanation or "",
                "exam_id": exam.id,
                "subject_id": subject.id,
                "topic_id": topic.id,
                "difficulty": q.difficulty or "medium",
                "is_previous_year": q.source != "AI",
            })

            if len(batch) >= batch_size:
                n = await vector_store.add_questions(batch)
                indexed += n
                logger.info(f"Indexed {indexed}/{total} questions...")
                batch = []

        # Index remaining
        if batch:
            n = await vector_store.add_questions(batch)
            indexed += n

        logger.info(f"✅ Done! Indexed {indexed}/{total} questions in Qdrant")

    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(seed_qdrant())
