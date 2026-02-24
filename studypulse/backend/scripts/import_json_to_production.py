#!/usr/bin/env python3
"""
Import Questions from JSON Files to Production Database

This script imports questions from JSON data files to the production database.
It creates the necessary exam/subject/topic structure and maps questions accordingly.

Usage:
    # Set DATABASE_URL to production database
    export DATABASE_URL="postgresql://user:pass@host:port/db"
    
    # Run the script
    python scripts/import_json_to_production.py

JSON Files:
    - data/gynaecology_obstetrics_import.json
    - data/neet_cereb_gynae_import.json
    - data/neet_obgyn_edition8_import.json
    - data/neet_prepx_gynae_import.json
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.question import Question
from app.models.exam import Topic, Subject, Exam


# ============================================================================
# Configuration
# ============================================================================

# Default exam/subject structure for NEET PG Gynaecology
DEFAULT_EXAM_NAME = "NEET PG"
DEFAULT_SUBJECT_NAME = "Gynaecology & Obstetrics"

# Topic name mapping (for questions without topic_id or with numeric IDs)
TOPIC_MAPPING = {
    1: "Cervical Carcinoma",
    2: "Ovarian Tumors",
    3: "Endometrial Cancer",
    4: "Menstrual Disorders",
    5: "Infertility",
    6: "Pregnancy Complications",
    7: "Labour & Delivery",
    8: "Postpartum Care",
    9: "Gynaecological Infections",
    10: "Contraception",
    11: "Reproductive Endocrinology",
    12: "Benign Gynecological Conditions",
    13: "Urogynaecology",
}

# JSON files to import (in order)
JSON_FILES = [
    "data/gynaecology_obstetrics_import.json",
    "data/neet_cereb_gynae_import.json",
    "data/neet_obgyn_edition8_import.json",
    "data/neet_prepx_gynae_import.json",
]


# ============================================================================
# Database Operations
# ============================================================================

async def get_or_create_exam(session: AsyncSession, name: str) -> Exam:
    """Get or create an exam by name."""
    result = await session.execute(
        select(Exam).where(Exam.name.ilike(f"%{name}%"))
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        exam = Exam(
            name=name,
            description=f"{name} Medical Entrance Examination",
            is_active=True
        )
        session.add(exam)
        await session.commit()
        print(f"  [CREATED] Exam: {name}")
    else:
        print(f"  [FOUND] Exam: {exam.name}")
    
    return exam


async def get_or_create_subject(session: AsyncSession, exam_id: int, name: str) -> Subject:
    """Get or create a subject."""
    result = await session.execute(
        select(Subject).where(
            Subject.exam_id == exam_id,
            Subject.name.ilike(f"%{name}%")
        )
    )
    subject = result.scalar_one_or_none()
    
    if not subject:
        subject = Subject(
            exam_id=exam_id,
            name=name,
            description=f"{name} questions for medical entrance exams",
            is_active=True
        )
        session.add(subject)
        await session.commit()
        print(f"  [CREATED] Subject: {name}")
    else:
        print(f"  [FOUND] Subject: {subject.name}")
    
    return subject


async def get_or_create_topic(session: AsyncSession, subject_id: int, name: str) -> Topic:
    """Get or create a topic."""
    result = await session.execute(
        select(Topic).where(
            Topic.subject_id == subject_id,
            Topic.name == name
        )
    )
    topic = result.scalar_one_or_none()
    
    if not topic:
        topic = Topic(
            subject_id=subject_id,
            name=name,
            description=f"Questions about {name}",
            is_active=True
        )
        session.add(topic)
        await session.commit()
        print(f"    [CREATED] Topic: {name}")
    else:
        print(f"    [FOUND] Topic: {topic.name}")
    
    return topic


async def create_topic_structure(session: AsyncSession, exam_id: int, subject_id: int) -> Dict[int, Topic]:
    """Create the standard topic structure and return a mapping."""
    topic_map = {}
    
    print(f"\n  [SETTING UP] Topic structure...")
    
    for topic_id, topic_name in TOPIC_MAPPING.items():
        topic = await get_or_create_topic(session, subject_id, topic_name)
        topic_map[topic_id] = topic
    
    return topic_map


async def import_question(session: AsyncSession, topic: Topic, q_data: Dict) -> bool:
    """Import a single question."""
    try:
        # Extract question text
        question_text = q_data.get('question_text', '')
        if not question_text:
            question_text = q_data.get('question', '')
        if not question_text:
            return False
        
        # Check for duplicates
        existing = await session.execute(
            select(Question).where(
                Question.topic_id == topic.id,
                Question.question_text == question_text[:500]  # Check first 500 chars
            )
        )
        if existing.scalar_one_or_none():
            return False
        
        # Extract options
        options = q_data.get('options', {})
        if isinstance(options, list):
            # Convert list to dict
            options_dict = {}
            for idx, opt in enumerate(options):
                label = chr(ord('A') + idx)
                if isinstance(opt, dict):
                    options_dict[label] = opt.get('text', str(opt))
                else:
                    options_dict[label] = str(opt)
            options = options_dict
        
        # Extract correct answer
        correct_answer = q_data.get('correct_answer', '')
        if not correct_answer:
            correct_answer = q_data.get('correct', '')
            if isinstance(correct_answer, int):
                correct_answer = chr(ord('A') + correct_answer)
        correct_answer = str(correct_answer).upper().strip()
        if len(correct_answer) > 1:
            correct_answer = correct_answer[0]
        
        # Create question
        question = Question(
            topic_id=topic.id,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=q_data.get('explanation', ''),
            difficulty=q_data.get('difficulty', 'medium'),
            source=q_data.get('source', 'IMPORT'),
            year=q_data.get('year'),
            question_images=q_data.get('question_images', []),
            explanation_images=q_data.get('explanation_images', []),
            is_active=True,
            is_validated=True,
        )
        
        session.add(question)
        return True
        
    except Exception as e:
        print(f"    [ERROR] Failed to import question: {e}")
        return False


async def import_from_json_file(
    session: AsyncSession,
    json_path: str,
    topic_map: Dict[int, Topic],
    default_topic: Topic
) -> Dict[str, int]:
    """Import questions from a JSON file."""
    
    print(f"\n  [PROCESSING] {json_path}")
    
    if not os.path.exists(json_path):
        print(f"    [SKIP] File not found: {json_path}")
        return {"imported": 0, "skipped": 0, "errors": 0}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get questions list
    questions = data.get('questions', [])
    if not questions:
        # Try alternative keys
        questions = data.get('data', [])
    if not questions:
        questions = data if isinstance(data, list) else []
    
    print(f"    [FOUND] {len(questions)} questions in file")
    
    imported = 0
    skipped = 0
    errors = 0
    
    for q in questions:
        # Determine topic
        topic_id = q.get('topic_id')
        if topic_id and topic_id in topic_map:
            topic = topic_map[topic_id]
        else:
            topic = default_topic
        
        result = await import_question(session, topic, q)
        if result:
            imported += 1
        else:
            skipped += 1
        
        # Commit in batches
        if imported % 100 == 0 and imported > 0:
            await session.commit()
            print(f"    [PROGRESS] Imported {imported} questions...")
    
    await session.commit()
    
    return {"imported": imported, "skipped": skipped, "errors": errors}


# ============================================================================
# Main Orchestration
# ============================================================================

async def main():
    """Main orchestration function."""
    print("\n" + "="*70)
    print("PRODUCTION QUESTION IMPORT SCRIPT")
    print("="*70)
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("\n  [ERROR] DATABASE_URL environment variable not set!")
        print("  Set it to your production database connection string.")
        return
    
    # Convert to async URL if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    
    print(f"\n  [DATABASE] Connecting to production database...")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    total_stats = {
        "imported": 0,
        "skipped": 0,
        "errors": 0
    }
    
    async with async_session() as session:
        # Setup exam/subject structure
        print("\n" + "-"*70)
        print("PHASE 1: DATABASE SETUP")
        print("-"*70)
        
        exam = await get_or_create_exam(session, DEFAULT_EXAM_NAME)
        subject = await get_or_create_subject(session, exam.id, DEFAULT_SUBJECT_NAME)
        topic_map = await create_topic_structure(session, exam.id, subject.id)
        
        # Get default topic (first one)
        default_topic = list(topic_map.values())[0] if topic_map else None
        
        if not default_topic:
            print("\n  [ERROR] Failed to create topic structure!")
            return
        
        # Import from JSON files
        print("\n" + "-"*70)
        print("PHASE 2: IMPORT QUESTIONS")
        print("-"*70)
        
        # Get the data directory
        script_dir = Path(__file__).parent.parent
        data_dir = script_dir / "data"
        
        for json_file in JSON_FILES:
            json_path = data_dir / json_file.split('/')[-1]
            
            stats = await import_from_json_file(
                session,
                str(json_path),
                topic_map,
                default_topic
            )
            
            total_stats["imported"] += stats["imported"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["errors"] += stats["errors"]
        
        # Print summary
        print("\n" + "-"*70)
        print("PHASE 3: SUMMARY")
        print("-"*70)
        print(f"  Total imported: {total_stats['imported']}")
        print(f"  Total skipped:  {total_stats['skipped']}")
        print(f"  Total errors:   {total_stats['errors']}")
        
        # Verify counts
        print("\n  [VERIFYING] Database counts...")
        for topic_id, topic in topic_map.items():
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM questions WHERE topic_id = {topic.id}")
            )
            count = count_result.scalar()
            print(f"    {topic.name}: {count} questions")
    
    await engine.dispose()
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
