"""Check NEET PG questions count."""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from sqlalchemy import select, func


async def check_neet_questions():
    async with AsyncSessionLocal() as session:
        # Find NEET PG exam
        result = await session.execute(
            select(Exam).where(Exam.name.ilike("%NEET%PG%"))
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            print("❌ NEET PG exam not found in database")
            return
        
        print(f"\n📋 NEET PG Exam: {exam.name} (ID: {exam.id})")
        
        # Get all subjects for NEET PG
        result = await session.execute(
            select(Subject).where(Subject.exam_id == exam.id)
        )
        subjects = result.scalars().all()
        
        print(f"\n📚 Total Subjects: {len(subjects)}")
        
        total_questions = 0
        total_topics = 0
        
        print("\n" + "="*60)
        print("Subjects & Topics Breakdown:")
        print("="*60)
        
        for subject in subjects:
            # Count topics for this subject
            result = await session.execute(
                select(func.count(Topic.id)).where(Topic.subject_id == subject.id)
            )
            topic_count = result.scalar() or 0
            total_topics += topic_count
            
            # Count questions for this subject
            result = await session.execute(
                select(func.count(Question.id))
                .join(Topic)
                .where(Topic.subject_id == subject.id)
            )
            question_count = result.scalar() or 0
            total_questions += question_count
            
            print(f"\n📖 {subject.name}")
            print(f"   Topics: {topic_count} | Questions: {question_count}")
            
            # List topics with question counts
            result = await session.execute(
                select(Topic.name, func.count(Question.id))
                .join(Question, isouter=True)
                .where(Topic.subject_id == subject.id)
                .group_by(Topic.id)
                .order_by(Topic.id)
            )
            topics = result.all()
            
            for topic_name, q_count in topics:
                if q_count > 0:
                    print(f"   ├── {topic_name}: {q_count} Qs")
                else:
                    print(f"   ├── {topic_name}: (no questions)")
        
        print("\n" + "="*60)
        print(f"📊 TOTAL SUMMARY:")
        print(f"   • Subjects: {len(subjects)}")
        print(f"   • Topics: {total_topics}")
        print(f"   • Questions: {total_questions}")
        print("="*60)
        
        if total_questions == 0:
            print("\n⚠️  No questions found! You need to import questions.")
            print("   Run: python scripts/import_gynaecology_questions.py <html_file>")


if __name__ == "__main__":
    asyncio.run(check_neet_questions())
