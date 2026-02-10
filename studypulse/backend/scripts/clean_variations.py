"""Clean up legacy 'Variation X' questions from the database.
Replaces them with clean question text.
"""
import asyncio
import sys
import re

sys.path.insert(0, ".")


async def main():
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.question import Question

    async with AsyncSessionLocal() as db:
        # Count variation questions
        result = await db.execute(
            select(func.count(Question.id)).where(
                Question.question_text.like("%Variation%")
            )
        )
        count = result.scalar()
        print(f"Found {count} questions with 'Variation' in text")

        if count == 0:
            print("Nothing to clean!")
            return

        # Fetch them
        rows = (
            await db.execute(
                select(Question).where(
                    Question.question_text.like("%Variation%")
                )
            )
        ).scalars().all()

        cleaned = 0
        for q in rows:
            # Remove " (Variation 21)" or " Variation 5" patterns
            new_text = re.sub(r"\s*\(?Variation\s*\d+\)?\s*$", "", q.question_text).strip()
            if new_text != q.question_text:
                q.question_text = new_text
                cleaned += 1

        await db.commit()
        print(f"Cleaned {cleaned} questions (removed 'Variation X' suffix)")

        # Check for exact duplicates now
        result = await db.execute(
            select(Question.question_text, func.count(Question.id).label("cnt"))
            .group_by(Question.question_text)
            .having(func.count(Question.id) > 1)
        )
        dupes = result.all()
        print(f"Found {len(dupes)} duplicate question texts after cleanup")

        # Remove duplicates, keeping the lowest ID
        removed = 0
        for text, cnt in dupes:
            dupe_rows = (
                await db.execute(
                    select(Question)
                    .where(Question.question_text == text)
                    .order_by(Question.id)
                )
            ).scalars().all()
            # Keep first, delete rest
            for dupe in dupe_rows[1:]:
                await db.delete(dupe)
                removed += 1

        await db.commit()
        print(f"Removed {removed} duplicate questions")

        # Final count
        total = (await db.execute(select(func.count(Question.id)))).scalar()
        print(f"Total questions remaining: {total}")


if __name__ == "__main__":
    asyncio.run(main())
