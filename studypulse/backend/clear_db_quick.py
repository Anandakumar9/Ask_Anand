"""Quick script to clear database."""
import asyncio
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question, QuestionRating
from app.models.user import User
from app.models.mock_test import StudySession, MockTest, QuestionResponse

async def clear():
    async with AsyncSessionLocal() as session:
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
        print("Database cleared successfully")

asyncio.run(clear())
