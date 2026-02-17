"""Clear database and run seeding."""
import asyncio
from sqlalchemy import select, func, delete
from app.core.database import AsyncSessionLocal, engine
from app.core.database import Base
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question, QuestionRating
from app.models.user import User
from app.models.mock_test import StudySession, MockTest, QuestionResponse
from seed_complete_demo import (
    create_exams_subjects_topics,
    create_questions,
    create_users,
    create_study_sessions,
    create_mock_tests,
    create_question_ratings
)

async def clear_database():
    """Clear all data from database."""
    print("Clearing database...")
    async with AsyncSessionLocal() as session:
        # Delete in reverse order of dependencies
        await session.execute(delete(QuestionResponse))
        await session.execute(delete(QuestionRating))
        await session.execute(delete(MockTest))
        await session.execute(delete(StudySession))
        await session.execute(delete(Question))
        await session.execute(delete(Topic))
        await session.execute(delete(Subject))
        await session.execute(delete(Exam))
        await session.execute(delete(User))
        await session.commit()
    print("[OK] Database cleared")

async def main():
    """Clear and seed database."""
    print("\n" + "="*60)
    print("  Clear and Seed Database")
    print("="*60)

    # Clear existing data
    await clear_database()

    # Seed new data
    print("\nSeeding database...")
    async with AsyncSessionLocal() as db:
        # Step 1: Create exam hierarchy
        exam_map, subject_map, topic_list = await create_exams_subjects_topics(db)

        # Step 2: Create questions
        total_questions = await create_questions(db, topic_list)

        # Step 3: Create users
        users = await create_users(db)

        # Step 4: Create study sessions
        sessions = await create_study_sessions(db, users, topic_list)

        # Step 5: Create mock tests
        tests = await create_mock_tests(db, users, topic_list)

        # Step 6: Create question ratings
        ratings = await create_question_ratings(db, users)

        print("\n" + "="*60)
        print("  [SUCCESS] Database Seeded!")
        print("="*60)
        print(f"\n  Summary:")
        print(f"    - Exams: {len(exam_map)}")
        print(f"    - Subjects: {len(subject_map)}")
        print(f"    - Topics: {len(topic_list)}")
        print(f"    - Questions: {total_questions}")
        print(f"    - Users: {len(users)}")
        print(f"    - Study Sessions: {len(sessions)}")
        print(f"    - Mock Tests: {len(tests)}")
        print(f"    - Question Ratings: {len(ratings)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
