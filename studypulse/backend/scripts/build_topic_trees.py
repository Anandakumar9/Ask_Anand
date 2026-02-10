"""Build PageIndex trees for all UPSC and NEET topics.

This script:
1. Fetches all existing questions from database
2. Groups by topic
3. Builds PageIndex vector trees for each topic
4. Saves indexes to disk

This pre-builds the indexes so the RAG pipeline can use them immediately.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from app.rag.pageindex_adapter import pageindex_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def build_topic_trees():
    """Build PageIndex trees for all topics with questions."""

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Step 1: Get all exams and their topics
        result = await db.execute(
            select(Exam, Subject, Topic)
            .join(Subject, Exam.id == Subject.exam_id)
            .join(Topic, Subject.id == Topic.subject_id)
            .order_by(Exam.name, Subject.name, Topic.name)
        )
        topics_data = result.all()

        print("\n" + "="*60)
        print("BUILDING PAGEINDEX TREES FOR ALL TOPICS")
        print("="*60 + "\n")

        # Step 2: Initialize PageIndex
        print("Initializing PageIndex...")
        await pageindex_store.initialize()

        if not pageindex_store.available:
            print("❌ PageIndex initialization failed!")
            return

        print("✅ PageIndex ready\n")

        # Step 3: Process each topic
        total_topics = len(topics_data)
        total_questions = 0
        topics_with_questions = 0

        for idx, (exam, subject, topic) in enumerate(topics_data, 1):
            print(f"[{idx}/{total_topics}] {exam.name} → {subject.name} → {topic.name}")

            # Fetch questions for this topic
            result = await db.execute(
                select(Question)
                .where(Question.topic_id == topic.id)
            )
            questions = result.scalars().all()

            if not questions:
                print(f"  ⚠️  No questions found\n")
                continue

            # Convert to dict format for PageIndex
            question_dicts = [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "options": q.options if isinstance(q.options, dict) else {},
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation or "",
                    "topic_id": topic.id,
                    "subject_id": subject.id,
                    "exam_id": exam.id,
                    "difficulty": q.difficulty or "medium",
                    "is_previous_year": q.source != "AI",
                    "source": q.source or "UNKNOWN",
                }
                for q in questions
            ]

            # Add to PageIndex
            count = await pageindex_store.add_questions(question_dicts)

            print(f"  ✅ Indexed {count} questions\n")
            total_questions += count
            topics_with_questions += 1

        # Step 4: Summary
        print("="*60)
        print("BUILD COMPLETE")
        print("="*60)
        print(f"Total topics processed: {total_topics}")
        print(f"Topics with questions: {topics_with_questions}")
        print(f"Total questions indexed: {total_questions}")
        print(f"PageIndex size: {pageindex_store._current_count} vectors")
        print("="*60 + "\n")

        # Save final state
        await pageindex_store._save()

        # Close
        await pageindex_store.close()

    await engine.dispose()


async def verify_indexes():
    """Verify that PageIndex can search across all topics."""

    print("\n" + "="*60)
    print("VERIFYING PAGEINDEX SEARCH")
    print("="*60 + "\n")

    # Initialize
    await pageindex_store.initialize()

    if not pageindex_store.available:
        print("❌ PageIndex not available!")
        return

    print(f"✅ PageIndex loaded: {pageindex_store._current_count} vectors\n")

    # Test searches
    test_queries = [
        ("Banking questions", 1, "UPSC Banking Sector"),
        ("Anatomy questions", 12, "NEET Upper Limb"),
        ("Monetary policy", 3, "UPSC Monetary Policy"),
    ]

    for query, topic_id, description in test_queries:
        print(f"Test: '{query}' (Topic {topic_id}: {description})")

        results = await pageindex_store.search_similar(
            query_text=query,
            topic_id=topic_id,
            limit=3
        )

        if results:
            print(f"  ✅ Found {len(results)} results")
            for i, r in enumerate(results, 1):
                print(f"  {i}. [Score: {r['score']:.3f}] {r['question_text'][:60]}...")
        else:
            print(f"  ⚠️  No results")

        print()

    await pageindex_store.close()

    print("="*60)
    print("VERIFICATION COMPLETE")
    print("="*60 + "\n")


async def show_statistics():
    """Show statistics about indexed questions."""

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60 + "\n")

        # Get question counts by exam
        from sqlalchemy import func
        result = await db.execute(
            select(
                Exam.name,
                func.count(Question.id).label("question_count")
            )
            .select_from(Question)
            .join(Topic, Question.topic_id == Topic.id)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Exam, Subject.exam_id == Exam.id)
            .group_by(Exam.name)
        )

        for exam_name, count in result:
            print(f"{exam_name}: {count} questions")

        # Get question counts by source
        print("\nBy Source:")
        result = await db.execute(
            select(
                Question.source,
                func.count(Question.id).label("count")
            )
            .group_by(Question.source)
        )

        for source, count in result:
            print(f"  {source or 'UNKNOWN'}: {count}")

        # Get question counts by difficulty
        print("\nBy Difficulty:")
        result = await db.execute(
            select(
                Question.difficulty,
                func.count(Question.id).label("count")
            )
            .group_by(Question.difficulty)
        )

        for difficulty, count in result:
            print(f"  {difficulty or 'UNKNOWN'}: {count}")

        print("\n" + "="*60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "build":
            asyncio.run(build_topic_trees())
        elif command == "verify":
            asyncio.run(verify_indexes())
        elif command == "stats":
            asyncio.run(show_statistics())
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python build_topic_trees.py build   - Build PageIndex for all topics")
            print("  python build_topic_trees.py verify  - Verify PageIndex search works")
            print("  python build_topic_trees.py stats   - Show database statistics")
    else:
        # Default: build
        asyncio.run(build_topic_trees())
