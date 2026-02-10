"""End-to-end RAG pipeline test.

Tests the full flow: DB questions + AI generation via Ollama.
Run from backend directory: python scripts/test_pipeline.py
"""
import asyncio
import sys
import time

# Add parent to path so 'app' is importable
sys.path.insert(0, ".")


async def main():
    from app.core.database import AsyncSessionLocal
    from app.rag.orchestrator import orchestrator
    from app.core.ollama import ollama_client

    print("\n" + "=" * 60)
    print("  StudyPulse RAG Pipeline Test")
    print("=" * 60)

    # 1. Check Ollama
    print("\n[1/4] Checking Ollama availability...")
    available = await ollama_client.is_available()
    print(f"  Ollama: {'READY' if available else 'NOT AVAILABLE'}")
    if not available:
        print("  ERROR: Ollama not running. Start it first.")
        return

    # 2. Quick JSON generation test (direct Ollama call)
    print("\n[2/4] Testing Ollama JSON generation (direct call)...")
    t0 = time.time()
    result = await ollama_client.generate_json(
        prompt='Generate 2 MCQ questions about Indian History. Return a JSON array: [{"question_text": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct_answer": "A", "explanation": "...", "difficulty": "medium"}]',
        system="You are an exam question generator. Respond with ONLY valid JSON.",
        temperature=0.4,
    )
    elapsed = time.time() - t0
    if result:
        items = result if isinstance(result, list) else [result]
        print(f"  SUCCESS: Got {len(items)} questions in {elapsed:.1f}s")
        for i, q in enumerate(items[:2], 1):
            txt = q.get("question_text", "NO TEXT")[:80]
            print(f"    Q{i}: {txt}")
    else:
        print(f"  FAILED: No JSON output after {elapsed:.1f}s")
        print("  The AI generation won't work. Check Ollama logs.")
        return

    # 3. Full pipeline test via orchestrator
    print("\n[3/4] Testing full orchestrator pipeline (topic_id=67)...")
    print("  Requesting 5 questions with 50/50 DB/AI split...")
    print("  This may take 30-60 seconds...")

    t0 = time.time()
    async with AsyncSessionLocal() as db:
        test_result = await orchestrator.generate_test(
            topic_id=67,
            user_id=999,  # Test user
            question_count=5,
            previous_year_ratio=0.5,
            db=db,
        )
    elapsed = time.time() - t0

    questions = test_result.get("questions", [])
    metadata = test_result.get("metadata", {})

    print(f"\n  Pipeline completed in {elapsed:.1f}s")
    print(f"  Total questions: {len(questions)}")
    print(f"  From DB: {metadata.get('previous_year', 0)}")
    print(f"  AI generated: {metadata.get('ai_generated', 0)}")
    print(f"  Cached: {metadata.get('cached', False)}")

    # 4. Validate questions
    print("\n[4/4] Validating question quality...")
    seen = set()
    duplicates = 0
    has_variation = 0
    ai_count = 0
    db_count = 0

    for q in questions:
        txt = q.get("question_text", "")
        src = q.get("source", "UNKNOWN")

        if src == "AI":
            ai_count += 1
        else:
            db_count += 1

        key = txt.strip().lower()[:80]
        if key in seen:
            duplicates += 1
        seen.add(key)

        if "Variation" in txt or "variation" in txt:
            has_variation += 1

    print(f"  AI questions: {ai_count}")
    print(f"  DB questions: {db_count}")
    print(f"  Duplicates: {duplicates}")
    print(f"  'Variation' pattern: {has_variation}")

    print("\n  Questions:")
    for i, q in enumerate(questions, 1):
        src = q.get("source", "?")
        txt = q.get("question_text", "")[:90]
        diff = q.get("difficulty", "?")
        print(f"    {i}. [{src:>8}] [{diff:>6}] {txt}")

    # Summary
    print("\n" + "=" * 60)
    if ai_count > 0 and duplicates == 0 and has_variation == 0:
        print("  PASS: AI generation working, no duplicates!")
    elif ai_count > 0:
        print("  PARTIAL: AI working but has quality issues")
    else:
        print("  FAIL: No AI questions generated")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
