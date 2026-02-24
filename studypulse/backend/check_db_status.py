"""Check database status for Gynaecology & Obstetrics import."""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.exam import Subject, Topic
from app.models.question import Question
from sqlalchemy import select, func


async def check_status():
    async with AsyncSessionLocal() as session:
        # Check all subjects
        result = await session.execute(select(Subject))
        subjects = result.scalars().all()
        print(f"Total subjects: {len(subjects)}")
        for s in subjects:
            print(f"  - {s.name} (ID: {s.id})")
        
        # Check Gynaecology subject
        result = await session.execute(select(Subject).where(Subject.name == 'Gynaecology & Obstetrics'))
        subject = result.scalar_one_or_none()
        
        if subject:
            print(f"\nGynaecology & Obstetrics found (ID: {subject.id})")
            
            # Count topics
            result = await session.execute(select(func.count(Topic.id)).where(Topic.subject_id == subject.id))
            topic_count = result.scalar()
            print(f"Topics count: {topic_count}")
            
            # Count questions
            result = await session.execute(select(func.count(Question.id)).join(Topic).where(Topic.subject_id == subject.id))
            question_count = result.scalar()
            print(f"Questions count: {question_count}")
            
            # List topics with question counts
            result = await session.execute(
                select(Topic.name, func.count(Question.id))
                .join(Question, isouter=True)
                .where(Topic.subject_id == subject.id)
                .group_by(Topic.id)
                .order_by(Topic.id)
            )
            topics = result.all()
            print(f"\nTopics breakdown:")
            for name, count in topics:
                print(f"  - {name}: {count} questions")
        else:
            print("\nGynaecology & Obstetrics subject not found")


if __name__ == "__main__":
    asyncio.run(check_status())
