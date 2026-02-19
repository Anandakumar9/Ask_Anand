"""Check database state."""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.exam import Exam

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Exam.id)))
        count = result.scalar()
        print(f"Exam count in database: {count}")

if __name__ == "__main__":
    asyncio.run(check())
