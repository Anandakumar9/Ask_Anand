#!/usr/bin/env python3
"""
Import NEET PG Previous Year Papers

This script:
1. Creates "Previous Year Papers" subject under NEET PG exam with topics per year
2. Parses the HTML file and extracts questions per year
3. Imports questions to database with proper topic mapping

HTML File:
- previous papers neet_pg_papers.html (NEET PG 2018-2024)
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

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.question import Question
from app.models.exam import Topic, Subject, Exam


# ============================================================================
# Configuration
# ============================================================================

HTML_FILE = r"C:\Users\anand\Downloads\Telegram Desktop\previous papers neet_pg_papers.html"

SUBJECT_NAME = "Previous Year Papers"
EXAM_NAME = "NEET PG"


# ============================================================================
# AGENT 1: HTML Parser
# ============================================================================

def parse_html_file(file_path: str) -> Dict[str, Any]:
    """
    Parse HTML file and extract questions grouped by year.
    Returns dict with topics and their questions.
    """
    print(f"\n  [PARSING] {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    result = {
        "source": "NEET_PG_Papers",
        "topics": []
    }
    
    # Extract topic sections from navigation buttons
    # Pattern: <button onclick="showTest('test1')">NEET PG 2018</button>
    topic_pattern = r'<button onclick="showTest\(\'test(\d+)\'\)">([^<]+)</button>'
    topic_matches = re.findall(topic_pattern, html_content)
    
    topics_dict = {}
    for test_id, topic_name in topic_matches:
        clean_name = topic_name.replace('_', ' ').replace('__', ', ').strip()
        topics_dict[test_id] = clean_name
        print(f"    Found topic: {clean_name}")
    
    # Extract questions from iframe srcdoc attributes
    # Pattern: <iframe srcdoc="...const questions = [...];..."
    iframe_pattern = r'<iframe srcdoc="([^"]*)"'
    iframe_matches = re.findall(iframe_pattern, html_content)
    
    print(f"    Found {len(iframe_matches)} iframe sections")
    
    for idx, srcdoc in enumerate(iframe_matches):
        # Unescape HTML entities
        unescaped = unescape(srcdoc)
        
        # Debug: Check if questions keyword exists
        has_questions = 'questions' in unescaped
        if idx == 0:
            print(f"    [DEBUG] First iframe: {len(srcdoc)} chars raw, {len(unescaped)} chars unescaped, has_questions={has_questions}")
        
        # Find the questions JSON array
        questions = extract_questions_json(unescaped)
        
        if questions:
            # Get topic name for this section
            test_id = str(idx + 1)
            topic_name = topics_dict.get(test_id, f"Year {test_id}")
            
            result["topics"].append({
                "topic_name": topic_name,
                "questions": questions
            })
            print(f"    Extracted {len(questions)} questions for '{topic_name}'")
        else:
            print(f"    [WARNING] No questions extracted from iframe {idx + 1}")
    
    return result


def extract_questions_json(html_content: str) -> List[Dict]:
    """Extract the questions JSON array from HTML content."""
    
    # Pattern: questions = [{...}];
    # The questions are directly embedded in the HTML as a JS array
    
    # Find all occurrences of questions = [...]
    pattern = r'questions\s*=\s*\['
    
    for match in re.finditer(pattern, html_content):
        start_idx = match.end() - 1  # Position of '['
        
        # Find the matching closing bracket by counting brackets
        bracket_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(html_content[start_idx:]):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = start_idx + i + 1
                    break
        
        json_str = html_content[start_idx:end_idx]
        
        # Skip empty arrays
        if json_str == '[]':
            continue
        
        try:
            questions = json.loads(json_str)
            if questions and len(questions) > 0:
                return questions
        except json.JSONDecodeError as e:
            # Try to fix common issues
            try:
                # Handle trailing commas
                fixed_json = re.sub(r',\s*]', ']', json_str)
                fixed_json = re.sub(r',\s*}', '}', fixed_json)
                questions = json.loads(fixed_json)
                if questions and len(questions) > 0:
                    return questions
            except:
                continue
    
    return []


def transform_question(q: Dict, topic_id: int, year: int = None) -> Dict:
    """Transform a question from HTML format to database format.
    
    Options must be stored as {"A": "...", "B": "...", "C": "...", "D": "..."} 
    for the QuestionCard component to display them correctly.
    """
    
    # Extract question text
    question_text = q.get('text', '')  # New format uses 'text'
    if not question_text:
        question_text = q.get('question', '')
    if not question_text:
        question_text = q.get('question_text', '')
    
    # Extract options - must be stored as dict with A, B, C, D keys
    options_dict = {}
    correct_answer = ''
    
    if 'options' in q and isinstance(q['options'], list):
        for idx, opt in enumerate(q['options']):
            label = chr(ord('A') + idx)  # 0 -> 'A', 1 -> 'B', etc.
            if isinstance(opt, dict):
                # New format: {label: "A", text: "Option text", correct: true/false}
                option_text = opt.get('text', '')
                options_dict[label] = option_text
                if opt.get('correct'):
                    correct_answer = opt.get('label', label).upper()
            else:
                # Plain string option
                options_dict[label] = str(opt)
    elif 'options' in q and isinstance(q['options'], dict):
        # Already in dict format
        for key, value in q['options'].items():
            options_dict[key.upper()] = value
    else:
        # Old format: option_a, option_b, etc.
        for key in ['a', 'b', 'c', 'd', 'e']:
            opt_key = f'option_{key}'
            if opt_key in q:
                options_dict[key.upper()] = q[opt_key]
            elif key in q:
                options_dict[key.upper()] = q[key]
    
    # If correct_answer not found from options, try other fields
    if not correct_answer:
        correct_answer = q.get('correct', q.get('correct_answer', q.get('answer', '')))
        if isinstance(correct_answer, int):
            correct_answer = chr(ord('A') + correct_answer)  # 0 -> 'A', 1 -> 'B', etc.
    
    correct_answer = str(correct_answer).upper().strip()
    # Extract just the letter if it's in format "A. Option text"
    if '.' in correct_answer:
        correct_answer = correct_answer.split('.')[0].strip()
    # Ensure it's a single uppercase letter
    if len(correct_answer) > 1:
        correct_answer = correct_answer[0].upper()
    
    # Extract explanation
    explanation = q.get('explanation', q.get('explanation_text', ''))
    
    # Extract image URLs if present
    question_images = q.get('question_images', [])
    explanation_images = q.get('explanation_images', [])
    
    if not question_images:
        img = q.get('question_image', q.get('image_url', ''))
        if img:
            question_images = [img]
    
    if not explanation_images:
        img = q.get('explanation_image', '')
        if img:
            explanation_images = [img]
    
    return {
        "topic_id": topic_id,
        "question_text": question_text,
        "options": options_dict,  # Store as {"A": "...", "B": "...", ...}
        "correct_answer": correct_answer,  # Uppercase letter: "A", "B", "C", or "D"
        "explanation": explanation,
        "question_images": question_images,
        "explanation_images": explanation_images,
        "difficulty": q.get('difficulty', 'medium'),
        "source": "PREVIOUS_YEAR",
        "year": year,
        "audio_url": q.get('audio', ''),
        "video_url": q.get('video', '')
    }


# ============================================================================
# AGENT 2: Database Setup
# ============================================================================

async def get_or_create_exam(session: AsyncSession) -> Exam:
    """Get or create NEET PG exam."""
    result = await session.execute(
        select(Exam).where(Exam.name.ilike(f"%{EXAM_NAME}%"))
    )
    exam = result.scalar_one_or_none()
    
    if not exam:
        exam = Exam(
            name=EXAM_NAME,
            description="National Eligibility cum Entrance Test - Post Graduate",
            is_active=True
        )
        session.add(exam)
        await session.commit()
        print(f"  [CREATED] Exam: {EXAM_NAME}")
    else:
        print(f"  [FOUND] Exam: {exam.name}")
    
    return exam


async def get_or_create_subject(session: AsyncSession, exam_id: int) -> Subject:
    """Get or create Previous Year Papers subject."""
    result = await session.execute(
        select(Subject).where(
            Subject.exam_id == exam_id,
            Subject.name.ilike(f"%{SUBJECT_NAME}%")
        )
    )
    subject = result.scalar_one_or_none()
    
    if not subject:
        subject = Subject(
            exam_id=exam_id,
            name=SUBJECT_NAME,
            description="NEET PG Previous Year Question Papers",
            is_active=True
        )
        session.add(subject)
        await session.commit()
        print(f"  [CREATED] Subject: {SUBJECT_NAME}")
    else:
        print(f"  [FOUND] Subject: {subject.name}")
    
    return subject


async def get_or_create_topic(session: AsyncSession, subject_id: int, topic_name: str, year: int = None) -> Topic:
    """Get or create a topic."""
    result = await session.execute(
        select(Topic).where(
            Topic.subject_id == subject_id,
            Topic.name == topic_name
        )
    )
    topic = result.scalar_one_or_none()
    
    if not topic:
        topic = Topic(
            subject_id=subject_id,
            name=topic_name,
            description=f"NEET PG Previous Year Paper: {topic_name}",
            is_active=True
        )
        session.add(topic)
        await session.commit()
        print(f"    [CREATED] Topic: {topic_name}")
    else:
        print(f"    [FOUND] Topic: {topic.name}")
    
    return topic


# ============================================================================
# AGENT 3: Question Importer
# ============================================================================

async def import_questions(
    session: AsyncSession,
    topic: Topic,
    questions: List[Dict],
    year: int = None
) -> int:
    """Import questions for a topic."""
    imported = 0
    
    for q in questions:
        try:
            transformed = transform_question(q, topic.id, year)
            
            # Skip if no question text
            if not transformed['question_text']:
                continue
            
            # Check for duplicates
            existing = await session.execute(
                select(Question).where(
                    Question.topic_id == topic.id,
                    Question.question_text == transformed['question_text']
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # Create question
            question = Question(
                topic_id=topic.id,
                question_text=transformed['question_text'],
                options=transformed['options'],
                correct_answer=transformed['correct_answer'],
                explanation=transformed.get('explanation', ''),
                question_images=transformed.get('question_images', []),
                explanation_images=transformed.get('explanation_images', []),
                audio_url=transformed.get('audio_url'),
                video_url=transformed.get('video_url'),
                difficulty=transformed.get('difficulty', 'medium'),
                source=transformed.get('source', 'PREVIOUS_YEAR'),
                year=year
            )
            session.add(question)
            imported += 1
            
        except Exception as e:
            print(f"    [ERROR] Failed to import question: {e}")
            continue
    
    await session.commit()
    return imported


def extract_year_from_topic(topic_name: str) -> int:
    """Extract year from topic name like 'NEET PG 2018'."""
    match = re.search(r'(\d{4})', topic_name)
    if match:
        return int(match.group(1))
    return None


# ============================================================================
# Main Orchestration
# ============================================================================

async def main():
    """Main orchestration function."""
    print("\n" + "="*70)
    print("NEET PG PREVIOUS YEAR PAPERS IMPORT SCRIPT")
    print("="*70)
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Parse HTML file
    print("\n" + "-"*70)
    print("PHASE 1: PARSING HTML FILE")
    print("-"*70)
    
    try:
        parsed = parse_html_file(HTML_FILE)
    except FileNotFoundError:
        print(f"  [ERROR] File not found: {HTML_FILE}")
        return
    except Exception as e:
        print(f"  [ERROR] Failed to parse {HTML_FILE}: {e}")
        return
    
    # Collect all unique topic names
    all_topics = set()
    for topic_data in parsed.get("topics", []):
        all_topics.add(topic_data["topic_name"])
    
    print(f"\n  [SUMMARY] Found {len(all_topics)} unique topics")
    
    # Import to database
    print("\n" + "-"*70)
    print("PHASE 2: DATABASE IMPORT")
    print("-"*70)
    
    async with async_session() as session:
        # Get or create exam and subject
        exam = await get_or_create_exam(session)
        subject = await get_or_create_subject(session, exam.id)
        
        # Create topics
        print(f"\n  [CREATING] Topics for {SUBJECT_NAME}...")
        topic_map = {}
        for topic_name in sorted(all_topics):
            year = extract_year_from_topic(topic_name)
            topic = await get_or_create_topic(session, subject.id, topic_name, year)
            topic_map[topic_name] = (topic, year)
        
        # Import questions
        print(f"\n  [IMPORTING] Questions...")
        total_imported = 0
        
        for topic_data in parsed.get("topics", []):
            topic_name = topic_data["topic_name"]
            questions = topic_data["questions"]
            
            if topic_name in topic_map:
                topic, year = topic_map[topic_name]
                count = await import_questions(
                    session, topic, questions, year
                )
                total_imported += count
                print(f"    {topic_name}: {count} questions imported")
        
        print(f"\n  [COMPLETE] Total questions imported: {total_imported}")
    
    await engine.dispose()
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
