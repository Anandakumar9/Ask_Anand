#!/usr/bin/env python3
"""
Multi-Agent Question Import Script for Gynaecology & Obstetrics

This script:
1. Clears existing NEET PG exam topics and questions
2. Creates Gynaecology & Obstetrics subject with 13 topics
3. Parses HTML file and extracts questions per topic
4. Imports questions to database with proper topic mapping

Agent Specialization:
- Agent 1: Database Cleanup (clears existing data)
- Agent 2: Subject/Topic Creator (creates new structure)
- Agent 3: HTML Parser (extracts questions from HTML)
- Agent 4: Question Importer (maps and imports to database)
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from html import unescape
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.question import Question
from app.models.exam import Topic, Subject, Exam


# ============================================================================
# AGENT 1: Database Cleanup Specialist
# ============================================================================

async def agent_cleanup_database(session: AsyncSession) -> Dict[str, int]:
    """
    Agent 1: Clears existing NEET PG exam topics and questions.
    Returns count of deleted records.
    """
    print("\n" + "="*60)
    print("AGENT 1: Database Cleanup Specialist")
    print("="*60)
    
    # Find NEET PG exam
    result = await session.execute(
        select(Exam).where(Exam.name.ilike("%NEET%PG%"))
    )
    neet_exam = result.scalar_one_or_none()
    
    if not neet_exam:
        print("  [INFO] No NEET PG exam found - nothing to clean")
        return {"deleted_questions": 0, "deleted_topics": 0, "deleted_subjects": 0}
    
    exam_id = neet_exam.id
    
    # Get subjects for this exam
    subject_result = await session.execute(
        select(Subject).where(Subject.exam_id == exam_id)
    )
    subjects = subject_result.scalars().all()
    subjects_to_delete = len(subjects)
    
    # Count topics and questions (simplified - just count)
    total_topics = 0
    total_questions = 0
    
    for subject in subjects:
        topic_result = await session.execute(
            select(Topic).where(Topic.subject_id == subject.id)
        )
        topics = topic_result.scalars().all()
        total_topics += len(topics)
        
        for topic in topics:
            # Use raw count to avoid JSON parsing issues
            from sqlalchemy import text
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM questions WHERE topic_id = {topic.id}")
            )
            count = count_result.scalar()
            total_questions += count
    
    # Delete subjects (cascade will handle topics and questions)
    await session.execute(
        delete(Subject).where(Subject.exam_id == exam_id)
    )
    
    await session.commit()
    
    print(f"  [OK] Deleted {total_questions} questions")
    print(f"  [OK] Deleted {total_topics} topics")
    print(f"  [OK] Deleted {subjects_to_delete} subjects")
    
    return {
        "deleted_questions": total_questions,
        "deleted_topics": total_topics,
        "deleted_subjects": subjects_to_delete
    }


# ============================================================================
# AGENT 2: Subject/Topic Creator
# ============================================================================

TOPICS_LIST = [
    "Adnexal_Mass_and_Gyne_Cancers",
    "Anovulation__Hormonal_Disorders_and_Amenorrheas",
    "Antepartum_Hemorrhage_and_Complications",
    "Clinical_Conditions_of_Reproductive_Age_Group",
    "Early_Pregnancy_Complications",
    "High_Risk_Obstetrics",
    "Labor_and_Delivery",
    "Mixed_Bag_Topics",
    "OBG_Basics",
    "Prolapse_and_Contraception",
    "Relevant_Clinical_Anatomy",
    "Relevant_Clinical_Embryology_and_Associated_Disorders",
    "Reproductive_Physiology_and_Clinical_Conditions"
]

async def agent_create_structure(session: AsyncSession) -> Dict[str, Any]:
    """
    Agent 2: Creates Gynaecology & Obstetrics subject with 13 topics.
    Returns created subject and topic mappings.
    """
    print("\n" + "="*60)
    print("AGENT 2: Subject/Topic Creator")
    print("="*60)
    
    # Find or create NEET PG exam
    result = await session.execute(
        select(Exam).where(Exam.name.ilike("%NEET%PG%"))
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        exam = Exam(
            name="NEET PG",
            description="National Eligibility cum Entrance Test - Post Graduate",
            year=2024,
            active=True
        )
        session.add(exam)
        await session.flush()
        print(f"  [OK] Created exam: NEET PG")
    else:
        print(f"  [OK] Found existing exam: {exam.name}")
    
    # Create Subject
    subject = Subject(
        exam_id=exam.id,
        name="Gynaecology & Obstetrics",
        description="Gynaecology and Obstetrics for NEET PG",
        is_active=True
    )
    session.add(subject)
    await session.flush()
    print(f"  [OK] Created subject: Gynaecology & Obstetrics")
    
    # Create Topics
    topic_map = {}  # topic_name -> topic_object
    for i, topic_name in enumerate(TOPICS_LIST):
        # Convert underscores to spaces for display
        display_name = topic_name.replace("_", " ").replace("__", " - ")
        
        topic = Topic(
            subject_id=subject.id,
            name=display_name,
            description=f"NEET PG questions on {display_name}",
            is_active=True
        )
        session.add(topic)
        await session.flush()
        topic_map[topic_name] = topic
        print(f"  [OK] Created topic {i+1}: {display_name}")
    
    await session.commit()
    
    return {
        "exam_id": exam.id,
        "subject_id": subject.id,
        "topic_map": topic_map
    }


# ============================================================================
# AGENT 3: HTML Parser Specialist
# ============================================================================

def extract_questions_from_iframe(iframe_content: str) -> List[Dict[str, Any]]:
    """
    Extract questions from an iframe srcdoc content.
    The questions are in format: questions = [{...}];
    """
    # Unescape HTML entities
    unescaped = unescape(iframe_content)
    
    # Find all questions = [...] patterns
    pattern = r'questions\s*=\s*\['
    
    questions = []
    
    for match in re.finditer(pattern, unescaped):
        start_pos = match.end() - 1  # Position of [
        
        # Find matching closing bracket
        bracket_count = 0
        end_pos = start_pos
        
        for i, char in enumerate(unescaped[start_pos:], start_pos):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i + 1
                    break
        
        json_str = unescaped[start_pos:end_pos]
        
        # Skip empty arrays
        if len(json_str) <= 2:
            continue
        
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list) and len(parsed) > 0:
                # Check if this is actual question data (has text field)
                if isinstance(parsed[0], dict) and 'text' in parsed[0]:
                    questions = parsed
                    break
        except json.JSONDecodeError:
            continue
    
    return questions


def transform_question(q: Dict[str, Any], topic_name: str) -> Dict[str, Any]:
    """
    Transform a question from HTML format to database format.
    """
    # Extract options
    options = q.get('options', [])
    
    # Build options dict
    options_dict = {}
    correct_answer = None
    
    for opt in options:
        label = opt.get('label', '')
        text = opt.get('text', '')
        is_correct = opt.get('correct', False)
        
        # Check for image in option
        if 'image' in opt:
            options_dict[label] = {
                'text': text,
                'image': opt['image']
            }
        else:
            options_dict[label] = text
        
        if is_correct:
            correct_answer = label
    
    # Build question object
    question_data = {
        'text': q.get('text', ''),
        'options': options_dict,
        'correct_answer': correct_answer or 'A',
        'explanation': q.get('explanation', ''),
        'difficulty': 'medium',
        'question_images': q.get('images', []),
        'explanation_images': [],
        'audio_url': q.get('audio'),
        'video_url': q.get('video'),
        'source': 'Prep_RR_Qb_Gynaecology_Obstetrics',
        'topic_name': topic_name
    }
    
    return question_data


def agent_parse_html(html_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Agent 3: Parses HTML file and extracts questions per topic.
    Returns dict mapping topic_name -> list of questions.
    """
    print("\n" + "="*60)
    print("AGENT 3: HTML Parser Specialist")
    print("="*60)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Find all test containers
    # Pattern: <div id="testN" class="iframe-container"...> ... <iframe srcdoc="..."> ...
    topic_questions = {}
    
    # Find all topic buttons to get topic names
    button_pattern = r"<button onclick=\"showTest\('test(\d+)'\)\">([^<]+)</button>"
    topic_mapping = {}  # test_id -> topic_name
    
    for match in re.finditer(button_pattern, html_content):
        test_id = match.group(1)
        topic_name = match.group(2).strip()
        topic_mapping[f"test{test_id}"] = topic_name
    
    print(f"  [OK] Found {len(topic_mapping)} topics in HTML")
    
    # Find all iframe srcdoc contents
    iframe_pattern = r'<div id="(test\d+)"[^>]*>.*?<iframe srcdoc="([^"]*)"'
    
    for match in re.finditer(iframe_pattern, html_content, re.DOTALL):
        test_id = match.group(1)
        iframe_content = match.group(2)
        
        topic_name = topic_mapping.get(test_id, f"Unknown_{test_id}")
        
        # Extract questions from iframe
        questions = extract_questions_from_iframe(iframe_content)
        
        if questions:
            # Transform questions
            transformed = [transform_question(q, topic_name) for q in questions]
            topic_questions[topic_name] = transformed
            print(f"  [OK] Extracted {len(transformed)} questions from: {topic_name}")
        else:
            print(f"  [WARN] No questions found for: {topic_name}")
    
    return topic_questions


# ============================================================================
# AGENT 4: Question Importer
# ============================================================================

async def agent_import_questions(
    session: AsyncSession,
    topic_questions: Dict[str, List[Dict[str, Any]]],
    topic_map: Dict[str, Topic]
) -> Dict[str, int]:
    """
    Agent 4: Imports questions to database with proper topic mapping.
    Returns import statistics.
    """
    print("\n" + "="*60)
    print("AGENT 4: Question Importer")
    print("="*60)
    
    stats = {
        "total_questions": 0,
        "imported": 0,
        "failed": 0,
        "by_topic": {}
    }
    
    for topic_name, questions in topic_questions.items():
        # Find matching topic in database
        topic = None
        for db_topic_name, db_topic in topic_map.items():
            # Match by normalized name
            html_name_normalized = topic_name.replace("_", " ").replace("__", " - ")
            db_name_normalized = db_topic_name.replace("_", " ").replace("__", " - ")
            
            if html_name_normalized.lower() == db_name_normalized.lower():
                topic = db_topic
                break
        
        if not topic:
            print(f"  [WARN] No matching topic found for: {topic_name}")
            stats["failed"] += len(questions)
            continue
        
        topic_imported = 0
        
        for q_data in questions:
            try:
                question = Question(
                    topic_id=topic.id,
                    question_text=q_data['text'],
                    options=q_data['options'],
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data.get('explanation', ''),
                    difficulty=q_data.get('difficulty', 'medium'),
                    question_images=q_data.get('question_images', []),
                    explanation_images=q_data.get('explanation_images', []),
                    audio_url=q_data.get('audio_url'),
                    video_url=q_data.get('video_url'),
                    source=q_data.get('source', 'import'),
                    is_active=True
                )
                session.add(question)
                topic_imported += 1
                stats["imported"] += 1
            except Exception as e:
                print(f"  [ERROR] Failed to import question: {e}")
                stats["failed"] += 1
        
        stats["by_topic"][topic_name] = topic_imported
        stats["total_questions"] += len(questions)
        print(f"  [OK] Imported {topic_imported}/{len(questions)} questions to: {topic.name}")
    
    await session.commit()
    
    return stats


# ============================================================================
# ORCHESTRATOR
# ============================================================================

async def main(html_path: str):
    """
    Main orchestrator that coordinates all agents.
    """
    print("\n" + "="*60)
    print("MULTI-AGENT QUESTION IMPORT SYSTEM")
    print("="*60)
    print(f"HTML File: {html_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Agent 1: Cleanup
        cleanup_stats = await agent_cleanup_database(session)
        
        # Agent 2: Create Structure
        structure = await agent_create_structure(session)
        
        # Agent 3: Parse HTML
        topic_questions = agent_parse_html(html_path)
        
        # Agent 4: Import Questions
        import_stats = await agent_import_questions(
            session,
            topic_questions,
            structure["topic_map"]
        )
    
    # Final Summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Questions Deleted: {cleanup_stats['deleted_questions']}")
    print(f"Topics Deleted: {cleanup_stats['deleted_topics']}")
    print(f"Subjects Deleted: {cleanup_stats['deleted_subjects']}")
    print("-"*40)
    print(f"Total Questions Parsed: {import_stats['total_questions']}")
    print(f"Questions Imported: {import_stats['imported']}")
    print(f"Questions Failed: {import_stats['failed']}")
    print("-"*40)
    print("By Topic:")
    for topic, count in import_stats['by_topic'].items():
        print(f"  {topic}: {count}")
    print("="*60)
    
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_gynaecology_questions.py <html_file_path>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    if not Path(html_path).exists():
        print(f"Error: File not found: {html_path}")
        sys.exit(1)
    
    asyncio.run(main(html_path))
