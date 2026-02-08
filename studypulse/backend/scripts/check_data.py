import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.exam import Exam, Subject, Topic

async def count_data():
    async with AsyncSessionLocal() as db:
        exams = (await db.execute(select(Exam))).scalars().all()
        subjects = (await db.execute(select(Subject))).scalars().all()
        topics = (await db.execute(select(Topic))).scalars().all()
        
        print(f'\n📊 Database Summary:')
        print(f'  Exams: {len(exams)}')
        print(f'  Subjects: {len(subjects)}')
        print(f'  Topics: {len(topics)}\n')
        
        for exam in exams:
            exam_subjects = [s for s in subjects if s.exam_id == exam.id]
            print(f'{exam.name}: {len(exam_subjects)} subjects')
            for subj in exam_subjects:
                subj_topics = [t for t in topics if t.subject_id == subj.id]
                print(f'  - {subj.name}: {len(subj_topics)} topics')

asyncio.run(count_data())
