#!/usr/bin/env python3
"""
End-to-End Test for Question Ingestion Pipeline

This script tests the complete question ingestion workflow:
1. HTML parsing
2. JSON transformation
3. API import
4. Database verification
5. Frontend display (via API response)

Usage:
    python tests/test_question_ingestion.py
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, engine, Base
from app.models.question import Question
from app.models.exam import Topic, Subject, Exam
from app.services.question_importer import importer
from app.schemas.question_import import QuestionImport, BulkQuestionImport


# Test data
SAMPLE_HTML = '''
<!DOCTYPE html>
<html>
<body>
    <button onclick="showTest('test1')">Test_Topic_1</button>
    <iframe srcdoc="
        <script>
        questions = [
            {
                "text": "What is the most common histological type of cervical cancer?",
                "options": [
                    {"label": "A", "text": "Adenocarcinoma", "correct": false},
                    {"label": "B", "text": "Squamous cell carcinoma", "correct": true},
                    {"label": "C", "text": "Small cell carcinoma", "correct": false},
                    {"label": "D", "text": "Clear cell carcinoma", "correct": false}
                ],
                "correct_answer": "B. Squamous cell carcinoma",
                "question_images": ["https://example.com/q-image.jpg"],
                "explanation_images": ["https://example.com/e-image.jpg"],
                "explanation": "<p>Squamous cell carcinoma is the most common type.</p><p style='font-size: 10px; color: #808080; font-style: italic;'>@test_bot</p>",
                "audio": "https://example.com/audio.mp3",
                "video": ""
            }
        ];
        </script>
    "></iframe>
</body>
</html>
'''

SAMPLE_QUESTION_IMPORT = {
    "topic_id": 1,
    "question_text": "Test question with images",
    "options": {
        "A": {"text": "Option A", "image": "https://example.com/option-a.jpg"},
        "B": {"text": "Option B", "image": None},
        "C": {"text": "Option C", "image": None},
        "D": {"text": "Option D", "image": None}
    },
    "correct_answer": "A",
    "explanation": "Test explanation",
    "source": "TEST",
    "difficulty": "medium",
    "question_images": ["https://example.com/q1.jpg", "https://example.com/q2.jpg"],
    "explanation_images": ["https://example.com/e1.jpg"],
    "audio_url": "https://example.com/audio.mp3",
    "video_url": None
}


async def setup_test_database():
    """Create test database tables and seed data."""
    print("🔧 Setting up test database...")
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        # Check if exam exists
        exam = await db.scalar(select(Exam).where(Exam.name == "Test Exam"))
        if not exam:
            exam = Exam(
                name="Test Exam",
                description="Test exam for ingestion testing",
                is_active=True
            )
            db.add(exam)
            await db.flush()
        
        # Check if subject exists
        subject = await db.scalar(select(Subject).where(Subject.name == "Test Subject"))
        if not subject:
            subject = Subject(
                exam_id=exam.id,
                name="Test Subject",
                description="Test subject",
                is_active=True
            )
            db.add(subject)
            await db.flush()
        
        # Check if topic exists
        topic = await db.scalar(select(Topic).where(Topic.name == "Test Topic 1"))
        if not topic:
            topic = Topic(
                subject_id=subject.id,
                name="Test Topic 1",
                description="Test topic for ingestion",
                is_active=True
            )
            db.add(topic)
            await db.flush()
        
        await db.commit()
        print(f"✅ Test database ready. Topic ID: {topic.id}")
        return topic.id


async def test_html_parser():
    """Test the HTML parser script."""
    print("\n📝 Testing HTML Parser...")
    
    # Import the parser
    from scripts.html_question_parser import QuestionHTMLParser, generate_import_json
    
    # Parse the sample HTML
    parser = QuestionHTMLParser(SAMPLE_HTML, source_name="test")
    questions = parser.parse()
    
    assert len(questions) > 0, "No questions parsed from HTML"
    print(f"   ✓ Parsed {len(questions)} questions from HTML")
    
    # Check question structure
    q = questions[0]
    assert "text" in q, "Question missing 'text' field"
    assert "options" in q, "Question missing 'options' field"
    assert "correct_answer" in q, "Question missing 'correct_answer' field"
    print("   ✓ Question structure validated")
    
    # Transform for import
    transformed = parser.transform_for_import(questions, topic_id_map={"Test Topic 1": 1})
    assert len(transformed) > 0, "No questions transformed"
    print(f"   ✓ Transformed {len(transformed)} questions for import")
    
    # Check transformed structure
    t = transformed[0]
    assert "topic_id" in t, "Transformed question missing 'topic_id'"
    assert "options" in t, "Transformed question missing 'options'"
    assert isinstance(t["options"], dict), "Options should be a dict"
    assert set(t["options"].keys()) == {"A", "B", "C", "D"}, "Options should have A, B, C, D keys"
    print("   ✓ Transformed structure validated")
    
    return transformed


async def test_question_import(topic_id: int):
    """Test the question import service."""
    print("\n📥 Testing Question Import...")
    
    async with async_session_maker() as db:
        # Create question import object
        question = QuestionImport(
            topic_id=topic_id,
            question_text=SAMPLE_QUESTION_IMPORT["question_text"],
            options=SAMPLE_QUESTION_IMPORT["options"],
            correct_answer=SAMPLE_QUESTION_IMPORT["correct_answer"],
            explanation=SAMPLE_QUESTION_IMPORT["explanation"],
            source=SAMPLE_QUESTION_IMPORT["source"],
            difficulty=SAMPLE_QUESTION_IMPORT["difficulty"],
            question_images=SAMPLE_QUESTION_IMPORT["question_images"],
            explanation_images=SAMPLE_QUESTION_IMPORT["explanation_images"],
            audio_url=SAMPLE_QUESTION_IMPORT["audio_url"],
            video_url=SAMPLE_QUESTION_IMPORT["video_url"]
        )
        
        # Import the question
        success, question_id, error = await importer.import_single(question, db)
        
        assert success, f"Import failed: {error}"
        assert question_id is not None, "No question ID returned"
        print(f"   ✓ Question imported with ID: {question_id}")
        
        return question_id


async def test_database_verification(question_id: int):
    """Verify the question was stored correctly in the database."""
    print("\n🔍 Testing Database Verification...")
    
    async with async_session_maker() as db:
        # Fetch the question
        question = await db.scalar(select(Question).where(Question.id == question_id))
        
        assert question is not None, f"Question {question_id} not found in database"
        print(f"   ✓ Question found in database")
        
        # Verify fields
        assert question.question_text == SAMPLE_QUESTION_IMPORT["question_text"]
        print("   ✓ Question text matches")
        
        assert question.correct_answer == SAMPLE_QUESTION_IMPORT["correct_answer"]
        print("   ✓ Correct answer matches")
        
        # Verify image fields
        assert question.question_images == SAMPLE_QUESTION_IMPORT["question_images"]
        print(f"   ✓ Question images stored: {question.question_images}")
        
        assert question.explanation_images == SAMPLE_QUESTION_IMPORT["explanation_images"]
        print(f"   ✓ Explanation images stored: {question.explanation_images}")
        
        assert question.audio_url == SAMPLE_QUESTION_IMPORT["audio_url"]
        print("   ✓ Audio URL stored")
        
        # Verify options with images
        options = question.options
        assert "A" in options
        assert isinstance(options["A"], dict)
        assert options["A"]["text"] == "Option A"
        assert options["A"]["image"] == "https://example.com/option-a.jpg"
        print("   ✓ Options with images stored correctly")
        
        return question


async def test_bulk_import(topic_id: int):
    """Test bulk import of multiple questions."""
    print("\n📦 Testing Bulk Import...")
    
    questions = [
        QuestionImport(
            topic_id=topic_id,
            question_text=f"Bulk test question {i}",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            source="BULK_TEST",
            difficulty="easy",
            question_images=[f"https://example.com/bulk-q{i}.jpg"]
        )
        for i in range(5)
    ]
    
    async with async_session_maker() as db:
        result = await importer.import_bulk(questions, db)
        
        assert result.success, f"Bulk import failed: {result.errors}"
        assert result.imported_count == 5, f"Expected 5 imports, got {result.imported_count}"
        print(f"   ✓ Imported {result.imported_count} questions in bulk")
        
        return result.question_ids


async def test_import_stats(topic_id: int):
    """Test import statistics."""
    print("\n📊 Testing Import Stats...")
    
    async with async_session_maker() as db:
        stats = await importer.get_import_stats(topic_id, db)
        
        print(f"   Total questions: {stats['total']}")
        print(f"   Test questions: {stats.get('test', 0)}")
        print(f"   Bulk test questions: {stats.get('bulk_test', 0)}")
        
        assert stats['total'] >= 6, "Expected at least 6 questions"
        print("   ✓ Stats retrieved successfully")


async def cleanup_test_data():
    """Clean up test data from database."""
    print("\n🧹 Cleaning up test data...")
    
    async with async_session_maker() as db:
        # Delete test questions
        from sqlalchemy import delete
        await db.execute(delete(Question).where(Question.source.in_(["TEST", "BULK_TEST"])))
        await db.commit()
        print("   ✓ Test data cleaned up")


async def run_all_tests():
    """Run all tests in sequence."""
    print("=" * 60)
    print("🚀 Starting Question Ingestion E2E Tests")
    print("=" * 60)
    
    try:
        # Setup
        topic_id = await setup_test_database()
        
        # Test HTML Parser
        transformed = await test_html_parser()
        
        # Test Single Import
        question_id = await test_question_import(topic_id)
        
        # Verify Database
        await test_database_verification(question_id)
        
        # Test Bulk Import
        await test_bulk_import(topic_id)
        
        # Test Stats
        await test_import_stats(topic_id)
        
        # Cleanup
        await cleanup_test_data()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
