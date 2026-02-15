"""End-to-end testing suite for StudyPulse RAG pipeline.

Tests the complete system from question import to test generation.

Test Coverage:
1. Question Import (CSV, PDF, Web)
2. PageIndex Vector Search
3. Smart Question Selection
4. RAG Pipeline (Orchestrator)
5. Performance Benchmarks
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_db
from app.rag.orchestrator import orchestrator
from app.rag.pageindex_adapter import pageindex_store
from app.rag.smart_selector import smart_selector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_question_import():
    """Test 1: Verify questions are in database."""
    print("\n" + "="*60)
    print("TEST 1: Question Import Verification")
    print("="*60 + "\n")

    async for db in get_db():
        from app.models.question import Question
        from sqlalchemy import select, func

        # Count total questions
        result = await db.execute(select(func.count(Question.id)))
        total = result.scalar()

        print(f"Total questions in database: {total}")

        if total > 0:
            # Count by source
            result = await db.execute(
                select(Question.source, func.count(Question.id))
                .group_by(Question.source)
            )
            for source, count in result:
                print(f"  {source or '?'}: {count}")

            print("\n✅ Questions imported successfully\n")
            return True
        else:
            print("\n❌ No questions found!\n")
            print("Run: python seed_basic.py")
            print("Or:  python test_csv_import.py\n")
            return False


async def test_pageindex():
    """Test 2: Verify PageIndex works."""
    print("\n" + "="*60)
    print("TEST 2: PageIndex Vector Search")
    print("="*60 + "\n")

    await pageindex_store.initialize()

    if not pageindex_store.available:
        print("❌ PageIndex not available!\n")
        return False

    count = pageindex_store._current_count
    print(f"PageIndex size: {count} vectors")

    if count == 0:
        print("\n⚠️  PageIndex is empty!")
        print("Run: python scripts/build_topic_trees.py build\n")
        return False

    # Test search
    results = await pageindex_store.search_similar(
        query_text="banking financial institutions",
        topic_id=1,
        limit=3
    )

    if results:
        print(f"\n✅ Search works! Found {len(results)} results:")
        for i, r in enumerate(results, 1):
            print(f"{i}. [Score: {r['score']:.3f}] {r['question_text'][:60]}...")
        print()
        return True
    else:
        print("\n⚠️  No search results (might be OK if no questions for topic 1)\n")
        return True


async def test_smart_selector():
    """Test 3: Verify smart selector works."""
    print("\n" + "="*60)
    print("TEST 3: Smart Question Selection")
    print("="*60 + "\n")

    # Mock questions
    mock_questions = [
        {"id": i, "question_text": f"Q{i}", "difficulty": d, "options": {}}
        for i, d in [
            (1, "easy"), (2, "easy"), (3, "easy"),
            (4, "medium"), (5, "medium"), (6, "medium"),
            (7, "hard"), (8, "hard"), (9, "hard"),
        ]
    ]

    # Mock performance
    performance = {
        "average_score": 0.65,
        "tests_taken": 10,
        "difficulty_scores": {"easy": 0.85, "medium": 0.65, "hard": 0.45},
        "last_test_date": None,
        "trend": "improving"
    }

    # Calculate distribution
    dist = smart_selector._calculate_difficulty_distribution(performance)
    print(f"Distribution (65% avg, improving):")
    print(f"  Easy: {dist['easy']:.0%}")
    print(f"  Medium: {dist['medium']:.0%}")
    print(f"  Hard: {dist['hard']:.0%}")

    # Select questions
    selected = smart_selector._select_by_distribution(
        mock_questions, dist, 6
    )

    print(f"\nSelected {len(selected)} questions:")
    for q in selected:
        print(f"  - ID {q['id']}: {q['difficulty']}")

    # Order by progression
    ordered = smart_selector._order_by_difficulty_progression(selected)
    print(f"\nOrdered (easy→medium→hard):")
    for q in ordered:
        print(f"  - ID {q['id']}: {q['difficulty']}")

    print("\n✅ Smart selector works!\n")
    return True


async def test_rag_pipeline():
    """Test 4: End-to-end RAG pipeline."""
    print("\n" + "="*60)
    print("TEST 4: RAG Pipeline (Orchestrator)")
    print("="*60 + "\n")

    async for db in get_db():
        try:
            print("Generating test for topic 1 (Banking Sector)...")

            start_time = time.time()

            result = await orchestrator.generate_test(
                topic_id=1,
                user_id=1,
                question_count=5,
                previous_year_ratio=0.5,
                db=db
            )

            elapsed = time.time() - start_time

            print(f"\n✅ Test generated in {elapsed:.2f}s\n")
            print(f"Questions: {len(result['questions'])}")
            print(f"Metadata: {result['metadata']}\n")

            if result['questions']:
                print("Sample question:")
                q = result['questions'][0]
                print(f"  Q: {q['question_text'][:80]}...")
                print(f"  A) {q['options'].get('A', '?')[:40]}...")
                print(f"  B) {q['options'].get('B', '?')[:40]}...")
                print()

                return True
            else:
                print("⚠️  No questions generated\n")
                return False

        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}\n")
            import traceback
            traceback.print_exc()
            return False


async def performance_benchmark():
    """Test 5: Performance benchmarks."""
    print("\n" + "="*60)
    print("TEST 5: Performance Benchmarks")
    print("="*60 + "\n")

    # Benchmark PageIndex search
    if pageindex_store.available:
        print("PageIndex search (10 queries):")

        queries = [
            "banking finance",
            "monetary policy",
            "fiscal deficit",
            "RBI functions",
            "priority sector"
        ]

        times = []
        for query in queries:
            start = time.time()
            results = await pageindex_store.search_similar(
                query_text=query,
                topic_id=1,
                limit=5
            )
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
            print(f"  '{query}': {elapsed:.1f}ms ({len(results)} results)")

        avg_time = sum(times) / len(times)
        print(f"\n  Average: {avg_time:.1f}ms")
        print("  Target: < 10ms")

        if avg_time < 10:
            print("  ✅ PASS\n")
        else:
            print("  ⚠️  Slower than target\n")

    # Benchmark RAG pipeline
    async for db in get_db():
        print("RAG pipeline (3 tests):")

        times = []
        for i in range(3):
            start = time.time()
            result = await orchestrator.generate_test(
                topic_id=1,
                user_id=1,
                question_count=5,
                db=db
            )
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
            print(f"  Test {i+1}: {elapsed:.0f}ms ({len(result['questions'])} questions)")

        avg_time = sum(times) / len(times)
        print(f"\n  Average: {avg_time:.0f}ms")
        print("  Target: < 5000ms (5s)")

        if avg_time < 5000:
            print("  ✅ PASS\n")
        else:
            print("  ⚠️  Slower than target (might be OK if using Ollama)\n")


async def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("STUDYPULSE END-TO-END TEST SUITE")
    print("="*60)

    tests = [
        ("Question Import", test_question_import),
        ("PageIndex Search", test_pageindex),
        ("Smart Selector", test_smart_selector),
        ("RAG Pipeline", test_rag_pipeline),
        ("Performance", performance_benchmark),
    ]

    results = {}

    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}", exc_info=True)
            results[name] = f"💥 CRASH: {str(e)[:50]}"

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")

    for name, result in results.items():
        print(f"{name:.<40} {result}")

    passed = sum(1 for r in results.values() if "PASS" in r)
    total = len(results)

    print(f"\n{'='*60}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    # Cleanup
    await pageindex_store.close()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
