"""
Admin API Endpoints for Production Operations

This module provides admin endpoints for:
- Importing questions from JSON files
- Database maintenance
- System status checks
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.question import Question
from app.models.exam import Topic, Subject, Exam

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ImportStatus(BaseModel):
    status: str
    imported: int = 0
    skipped: int = 0
    errors: int = 0
    message: str = ""


class ImportRequest(BaseModel):
    exam_name: str = "NEET PG"
    subject_name: str = "Gynaecology & Obstetrics"
    json_files: List[str] = [
        "data/gynaecology_obstetrics_import.json",
        "data/neet_cereb_gynae_import.json",
        "data/neet_obgyn_edition8_import.json",
        "data/neet_prepx_gynae_import.json",
    ]


# ============================================================================
# Topic Mapping
# ============================================================================

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


# ============================================================================
# Helper Functions
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
        logger.info(f"[CREATED] Exam: {name}")
    
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
        logger.info(f"[CREATED] Subject: {name}")
    
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
        logger.info(f"[CREATED] Topic: {name}")
    
    return topic


async def create_topic_structure(session: AsyncSession, subject_id: int) -> Dict[int, Topic]:
    """Create the standard topic structure and return a mapping."""
    topic_map = {}
    
    for topic_id, topic_name in TOPIC_MAPPING.items():
        topic = await get_or_create_topic(session, subject_id, topic_name)
        topic_map[topic_id] = topic
    
    return topic_map


async def import_question(session: AsyncSession, topic: Topic, q_data: Dict) -> bool:
    """Import a single question using nested transaction (SAVEPOINT)."""
    # Extract question text
    question_text = q_data.get('question_text', '') or q_data.get('question', '')
    if not question_text:
        return False
    
    # Extract options
    options = q_data.get('options', {})
    if isinstance(options, list):
        options_dict = {}
        for idx, opt in enumerate(options):
            label = chr(ord('A') + idx)
            if isinstance(opt, dict):
                options_dict[label] = opt.get('text', str(opt))
            else:
                options_dict[label] = str(opt)
        options = options_dict
    
    # Extract correct answer
    correct_answer = q_data.get('correct_answer', '') or q_data.get('correct', '')
    if isinstance(correct_answer, int):
        correct_answer = chr(ord('A') + correct_answer)
    correct_answer = str(correct_answer).upper().strip()[:1]  # Take first char only
    
    # Use nested transaction (SAVEPOINT) for proper error handling
    async with session.begin_nested():  # Creates a SAVEPOINT
        try:
            # Check for duplicates
            existing = await session.execute(
                select(Question).where(
                    Question.topic_id == topic.id,
                    Question.question_text == question_text[:500]
                ).limit(1)
            )
            if existing.scalar():
                return False  # Will rollback the SAVEPOINT
            
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
            await session.flush()
            return True  # SAVEPOINT will be committed
            
        except Exception as e:
            logger.debug(f"[SKIP] Question import failed: {e}")
            # SAVEPOINT will be automatically rolled back
            raise  # Re-raise to trigger SAVEPOINT rollback
    
    return False


async def import_from_json_file(
    session: AsyncSession,
    json_path: str,
    topic_map: Dict[int, Topic],
    default_topic: Topic
) -> Dict[str, int]:
    """Import questions from a JSON file."""
    
    logger.info(f"[PROCESSING] {json_path}")
    
    if not os.path.exists(json_path):
        logger.warning(f"[SKIP] File not found: {json_path}")
        return {"imported": 0, "skipped": 0, "errors": 0}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get questions list
    questions = data.get('questions', [])
    if not questions:
        questions = data.get('data', [])
    if not questions:
        questions = data if isinstance(data, list) else []
    
    logger.info(f"[FOUND] {len(questions)} questions in file")
    
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
            logger.info(f"[PROGRESS] Imported {imported} questions...")
    
    await session.commit()
    
    return {"imported": imported, "skipped": skipped, "errors": errors}


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status")
async def get_admin_status(db: AsyncSession = Depends(get_db)):
    """Get admin status including question counts."""
    
    # Get total questions
    result = await db.execute(text("SELECT COUNT(*) FROM questions"))
    total_questions = result.scalar()
    
    # Get questions by source
    result = await db.execute(text("""
        SELECT source, COUNT(*) as count 
        FROM questions 
        GROUP BY source
    """))
    by_source = {row[0]: row[1] for row in result.fetchall()}
    
    # Get exams
    result = await db.execute(select(Exam))
    exams = result.scalars().all()
    
    # Get subjects per exam
    exam_data = []
    for exam in exams:
        result = await db.execute(
            select(Subject).where(Subject.exam_id == exam.id)
        )
        subjects = result.scalars().all()
        
        subject_data = []
        for subject in subjects:
            result = await db.execute(
                select(Topic).where(Topic.subject_id == subject.id)
            )
            topics = result.scalars().all()
            
            topic_data = []
            for topic in topics:
                result = await db.execute(
                    text(f"SELECT COUNT(*) FROM questions WHERE topic_id = {topic.id}")
                )
                count = result.scalar()
                topic_data.append({
                    "name": topic.name,
                    "question_count": count
                })
            
            subject_data.append({
                "name": subject.name,
                "topics": topic_data
            })
        
        exam_data.append({
            "name": exam.name,
            "subjects": subject_data
        })
    
    return {
        "total_questions": total_questions,
        "by_source": by_source,
        "exams": exam_data
    }


class JsonImportRequest(BaseModel):
    """Request body for importing questions from JSON data directly."""
    exam_name: str = "NEET PG"
    subject_name: str = "Gynaecology & Obstetrics"
    questions: List[Dict[str, Any]]  # List of question objects
    topic_mapping: Optional[Dict[int, str]] = None  # Optional topic ID to name mapping


@router.post("/import", response_model=ImportStatus)
async def import_questions(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from JSON files.
    
    This endpoint triggers a background import task.
    """
    
    # Setup exam/subject structure
    exam = await get_or_create_exam(db, request.exam_name)
    subject = await get_or_create_subject(db, exam.id, request.subject_name)
    topic_map = await create_topic_structure(db, subject.id)
    
    # Get default topic
    default_topic = list(topic_map.values())[0] if topic_map else None
    
    if not default_topic:
        raise HTTPException(status_code=500, detail="Failed to create topic structure")
    
    # Import from JSON files
    total_stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    for json_file in request.json_files:
        # Get the data directory
        data_dir = Path(__file__).parent.parent / "data"
        json_path = data_dir / json_file.split('/')[-1]
        
        stats = await import_from_json_file(
            db,
            str(json_path),
            topic_map,
            default_topic
        )
        
        total_stats["imported"] += stats["imported"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["errors"] += stats["errors"]
    
    return ImportStatus(
        status="completed",
        imported=total_stats["imported"],
        skipped=total_stats["skipped"],
        errors=total_stats["errors"],
        message=f"Imported {total_stats['imported']} questions successfully"
    )


@router.post("/import-json", response_model=ImportStatus)
async def import_questions_json(
    request: JsonImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from JSON data directly.
    
    This endpoint accepts question data in the request body,
    useful when JSON files are not on the server.
    """
    
    logger.info(f"[IMPORT] Starting import for {request.exam_name} - {request.subject_name}")
    logger.info(f"[IMPORT] Received {len(request.questions)} questions")
    logger.info(f"[IMPORT] Topic mapping: {request.topic_mapping}")
    
    # Setup exam/subject structure
    exam = await get_or_create_exam(db, request.exam_name)
    subject = await get_or_create_subject(db, exam.id, request.subject_name)
    
    # Use provided topic mapping or default
    if request.topic_mapping:
        # Create topics from mapping
        # Note: JSON serialization converts int keys to strings, so handle both
        topic_map = {}
        for topic_id, topic_name in request.topic_mapping.items():
            # Convert string keys to int if needed
            if isinstance(topic_id, str):
                try:
                    topic_id = int(topic_id)
                except ValueError:
                    pass
            topic = await get_or_create_topic(db, subject.id, topic_name)
            topic_map[topic_id] = topic
            logger.info(f"[IMPORT] Created topic {topic_id}: {topic_name} (ID: {topic.id})")
    else:
        topic_map = await create_topic_structure(db, subject.id)
    
    logger.info(f"[IMPORT] Topic map keys: {list(topic_map.keys())}")
    
    # Get default topic
    default_topic = list(topic_map.values())[0] if topic_map else None
    
    if not default_topic:
        raise HTTPException(status_code=500, detail="Failed to create topic structure")
    
    logger.info(f"[IMPORT] Default topic: {default_topic.name} (ID: {default_topic.id})")
    
    # Import questions
    imported = 0
    skipped = 0
    errors = 0
    
    for idx, q in enumerate(request.questions[:5]):  # Log first 5 for debugging
        logger.info(f"[IMPORT] Sample Q{idx}: topic_id={q.get('topic_id')}, text={q.get('question_text', '')[:50]}...")
    
    for q in request.questions:
        # Determine topic
        topic_id = q.get('topic_id')
        # Try to find topic by int or string key
        topic = None
        if topic_id is not None:
            topic = topic_map.get(topic_id) or topic_map.get(str(topic_id)) or topic_map.get(int(topic_id) if str(topic_id).isdigit() else None)
        if not topic:
            topic = default_topic
        
        try:
            result = await import_question(db, topic, q)
            if result:
                imported += 1
            else:
                skipped += 1
        except Exception:
            # SAVEPOINT was rolled back, question was skipped
            skipped += 1
        
        # Commit progress every 100 questions
        if imported % 100 == 0 and imported > 0:
            try:
                await db.commit()
                logger.info(f"[PROGRESS] Imported {imported} questions...")
            except Exception:
                pass
    
    # Final commit
    try:
        await db.commit()
    except Exception:
        pass
    
    logger.info(f"[IMPORT] Complete: imported={imported}, skipped={skipped}, errors={errors}")
    
    logger.info(f"[IMPORT] Complete: imported={imported}, skipped={skipped}, errors={errors}")
    
    return ImportStatus(
        status="completed",
        imported=imported,
        skipped=skipped,
        errors=errors,
        message=f"Imported {imported} questions successfully"
    )


@router.post("/import/file", response_model=ImportStatus)
async def import_from_file(
    file_path: str,
    exam_name: str = "NEET PG",
    subject_name: str = "Gynaecology & Obstetrics",
    db: AsyncSession = Depends(get_db)
):
    """
    Import questions from a specific JSON file.
    """
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    # Setup exam/subject structure
    exam = await get_or_create_exam(db, exam_name)
    subject = await get_or_create_subject(db, exam.id, subject_name)
    topic_map = await create_topic_structure(db, subject.id)
    
    # Get default topic
    default_topic = list(topic_map.values())[0] if topic_map else None
    
    if not default_topic:
        raise HTTPException(status_code=500, detail="Failed to create topic structure")
    
    # Import from file
    stats = await import_from_json_file(
        db,
        file_path,
        topic_map,
        default_topic
    )
    
    return ImportStatus(
        status="completed",
        imported=stats["imported"],
        skipped=stats["skipped"],
        errors=stats["errors"],
        message=f"Imported {stats['imported']} questions from {file_path}"
    )


@router.delete("/clear")
async def clear_questions(
    exam_name: str = "NEET PG",
    confirm: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all questions for an exam.
    
    WARNING: This is a destructive operation!
    """
    
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to proceed with deletion"
        )
    
    # Find exam
    result = await db.execute(
        select(Exam).where(Exam.name.ilike(f"%{exam_name}%"))
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam '{exam_name}' not found")
    
    # Get subjects
    result = await db.execute(
        select(Subject).where(Subject.exam_id == exam.id)
    )
    subjects = result.scalars().all()
    
    deleted_questions = 0
    deleted_topics = 0
    deleted_subjects = len(subjects)
    
    for subject in subjects:
        # Get topics
        result = await db.execute(
            select(Topic).where(Topic.subject_id == subject.id)
        )
        topics = result.scalars().all()
        
        for topic in topics:
            # Count questions
            result = await db.execute(
                text(f"SELECT COUNT(*) FROM questions WHERE topic_id = {topic.id}")
            )
            deleted_questions += result.scalar()
            deleted_topics += 1
        
        # Delete subject (cascade will handle topics and questions)
        await db.execute(
            text(f"DELETE FROM subjects WHERE id = {subject.id}")
        )
    
    await db.commit()
    
    return {
        "status": "completed",
        "deleted_questions": deleted_questions,
        "deleted_topics": deleted_topics,
        "deleted_subjects": deleted_subjects
    }
