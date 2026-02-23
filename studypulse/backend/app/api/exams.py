"""Exams, Subjects, and Topics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from app.schemas.exam import ExamResponse, ExamBrief, SubjectResponse, SubjectBrief, TopicResponse

router = APIRouter()


@router.get("/", response_model=List[ExamBrief])
async def list_exams(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available exams.
    
    - **category**: Filter by exam category (e.g., "Government", "Engineering")
    - **search**: Search exams by name
    """
    query = select(Exam).where(Exam.is_active == True)
    
    if category:
        query = query.where(Exam.category == category)
    
    if search:
        query = query.where(Exam.name.ilike(f"%{search}%"))
    
    query = query.order_by(Exam.name)
    
    result = await db.execute(query)
    exams = result.scalars().all()
    
    # Add subject count and total questions
    exam_list = []
    for exam in exams:
        count_query = select(func.count(Subject.id)).where(Subject.exam_id == exam.id)
        count_result = await db.execute(count_query)
        subject_count = count_result.scalar() or 0
        
        # Get total questions across all topics using a single query
        q_count_query = select(func.count(Question.id)).join(Topic).join(Subject).where(Subject.exam_id == exam.id)
        q_count_result = await db.execute(q_count_query)
        total_questions = q_count_result.scalar() or 0
        
        exam_list.append(ExamBrief(
            id=exam.id,
            name=exam.name,
            category=exam.category,
            icon_url=exam.icon_url,
            subject_count=subject_count,
            total_questions=total_questions
        ))
    
    return exam_list


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    """Get exam details with subjects."""
    query = select(Exam).where(Exam.id == exam_id, Exam.is_active == True)
    result = await db.execute(query)
    exam = result.scalar_one_or_none()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Get subjects with topic count
    subjects_query = select(Subject).where(
        Subject.exam_id == exam_id,
        Subject.is_active == True
    ).order_by(Subject.name)
    
    subjects_result = await db.execute(subjects_query)
    subjects = subjects_result.scalars().all()
    
    subject_list = []
    for subject in subjects:
        count_query = select(func.count(Topic.id)).where(Topic.subject_id == subject.id)
        count_result = await db.execute(count_query)
        topic_count = count_result.scalar()
        
        subject_list.append(SubjectBrief(
            id=subject.id,
            exam_id=subject.exam_id,
            name=subject.name,
            icon_url=subject.icon_url,
            topic_count=topic_count
        ))
    
    return ExamResponse(
        id=exam.id,
        name=exam.name,
        description=exam.description,
        category=exam.category,
        conducting_body=exam.conducting_body,
        exam_duration_mins=exam.exam_duration_mins,
        total_questions=exam.total_questions,
        icon_url=exam.icon_url,
        subjects=subject_list
    )


@router.get("/{exam_id}/subjects", response_model=List[SubjectBrief])
async def list_subjects(exam_id: int, db: AsyncSession = Depends(get_db)):
    """List all subjects for an exam."""
    # Verify exam exists
    exam_query = select(Exam).where(Exam.id == exam_id)
    exam_result = await db.execute(exam_query)
    if not exam_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    query = select(Subject).where(
        Subject.exam_id == exam_id,
        Subject.is_active == True
    ).order_by(Subject.name)
    
    result = await db.execute(query)
    subjects = result.scalars().all()
    
    subject_list = []
    for subject in subjects:
        count_query = select(func.count(Topic.id)).where(Topic.subject_id == subject.id)
        count_result = await db.execute(count_query)
        topic_count = count_result.scalar()
        
        subject_list.append(SubjectBrief(
            id=subject.id,
            exam_id=subject.exam_id,
            name=subject.name,
            icon_url=subject.icon_url,
            topic_count=topic_count
        ))
    
    return subject_list


@router.get("/{exam_id}/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    exam_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get subject details with topics."""
    query = select(Subject).where(
        Subject.id == subject_id,
        Subject.exam_id == exam_id,
        Subject.is_active == True
    ).options(selectinload(Subject.topics))
    
    result = await db.execute(query)
    subject = result.scalar_one_or_none()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


@router.get("/{exam_id}/subjects/{subject_id}/topics", response_model=List[TopicResponse])
async def list_topics(
    exam_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all topics for a subject."""
    # Verify subject exists and belongs to exam
    subject_query = select(Subject).where(
        Subject.id == subject_id,
        Subject.exam_id == exam_id
    )
    subject_result = await db.execute(subject_query)
    if not subject_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    query = select(Topic).where(
        Topic.subject_id == subject_id,
        Topic.is_active == True
    ).order_by(Topic.name)
    
    result = await db.execute(query)
    topics = result.scalars().all()
    
    topic_list = []
    for t in topics:
        q_count_query = select(func.count(Question.id)).where(Question.topic_id == t.id)
        q_count_result = await db.execute(q_count_query)
        q_count = q_count_result.scalar() or 0
        
        topic_list.append(TopicResponse(
            id=t.id,
            subject_id=t.subject_id,
            name=t.name,
            description=t.description,
            difficulty_level=t.difficulty_level,
            estimated_study_mins=t.estimated_study_mins,
            icon_url=t.icon_url,
            question_count=q_count
        ))
    
    return topic_list


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get topic details."""
    query = select(Topic).where(Topic.id == topic_id, Topic.is_active == True)
    result = await db.execute(query)
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    return topic
