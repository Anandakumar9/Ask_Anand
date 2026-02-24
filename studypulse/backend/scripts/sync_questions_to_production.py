#!/usr/bin/env python3
"""
Sync Questions from JSON Files to Production Database

This script reads questions from JSON data files and imports them
to the production database via the production API.

Usage:
    python scripts/sync_questions_to_production.py

Environment Variables:
    PRODUCTION_API_URL - Production API base URL (default: https://askanand-simba.up.railway.app)
"""

import asyncio
import json
import os
import sys
import aiohttp
from pathlib import Path
from typing import Dict, List, Any


# ============================================================================
# Configuration
# ============================================================================

PRODUCTION_API_URL = os.getenv("PRODUCTION_API_URL", "https://askanand-simba.up.railway.app")

# JSON files to import
JSON_FILES = [
    "data/gynaecology_obstetrics_import.json",
]

# Topic ID mapping: local topic_id -> production topic name
TOPIC_ID_TO_NAME = {
    "1": "Cervical Carcinoma",
    "2": "Ovarian Tumors",
    "3": "Endometrial Cancer",
    "4": "Menstrual Disorders",
    "5": "Infertility",
    "6": "Pregnancy Complications",
    "7": "Labour & Delivery",
    "8": "Postpartum Care",
    "9": "Gynaecological Infections",
    "10": "Contraception",
    "11": "Reproductive Endocrinology",
    "12": "Benign Gynecological Conditions",
    "13": "Urogynaecology",
}


# ============================================================================
# API Operations
# ============================================================================

async def get_production_topics(session: aiohttp.ClientSession) -> Dict[str, int]:
    """Fetch all topics from production API and create a name -> ID mapping."""
    topics_map = {}
    
    try:
        async with session.get(f"{PRODUCTION_API_URL}/api/v1/exams/") as response:
            exams = await response.json()
            
            for exam in exams:
                exam_id = exam["id"]
                
                async with session.get(f"{PRODUCTION_API_URL}/api/v1/exams/{exam_id}/subjects") as resp:
                    subjects = await resp.json()
                    
                    for subject in subjects:
                        subject_id = subject["id"]
                        
                        async with session.get(f"{PRODUCTION_API_URL}/api/v1/exams/{exam_id}/subjects/{subject_id}/topics") as resp2:
                            topics = await resp2.json()
                            
                            for topic in topics:
                                topics_map[topic["name"]] = topic["id"]
    except Exception as e:
        print(f"  [ERROR] Failed to fetch production topics: {e}")
    
    return topics_map


async def import_questions_batch(
    session: aiohttp.ClientSession,
    questions: List[Dict],
    topic_id: int
) -> tuple:
    """Import a batch of questions to production."""
    
    if not questions:
        return 0, 0
    
    # Prepare bulk payload
    payload = {
        "questions": [
            {
                "topic_id": topic_id,
                "question_text": q["question_text"],
                "options": q["options"] if isinstance(q["options"], dict) else eval(q["options"]),
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation", ""),
                "difficulty": q.get("difficulty", "medium"),
                "source": q.get("source", "MANUAL"),
            }
            for q in questions
        ]
    }
    
    try:
        async with session.post(
            f"{PRODUCTION_API_URL}/api/v1/questions/import/bulk",
            json=payload
        ) as response:
            result = await response.json()
            if response.status in [200, 201] and result.get("success"):
                return result.get("imported_count", len(questions)), 0
            else:
                errors = result.get("errors", [])
                print(f"  [ERROR] Import failed: {response.status}")
                for err in errors[:3]:  # Show first 3 errors
                    print(f"         {err[:150]}")
                return 0, len(questions)
    except Exception as e:
        print(f"  [ERROR] Exception during import: {e}")
        return 0, len(questions)


# ============================================================================
# Main
# ============================================================================

async def main():
    print("=" * 60)
    print("StudyPulse - Sync Questions to Production")
    print("=" * 60)
    print()
    
    # Change to backend directory
    os.chdir(Path(__file__).parent.parent)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Get production topics
        print("[1/3] Fetching production topics...")
        prod_topics = await get_production_topics(session)
        print(f"      Found {len(prod_topics)} topics in production")
        
        # Step 2: Load questions from JSON files
        print()
        print("[2/3] Loading questions from JSON files...")
        
        all_questions_by_topic = {}  # topic_name -> [questions]
        
        for json_file in JSON_FILES:
            if not Path(json_file).exists():
                print(f"  [SKIP] File not found: {json_file}")
                continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            questions = data.get("questions", [])
            print(f"  [OK] Loaded {len(questions)} questions from {json_file}")
            
            # Group by topic
            for q in questions:
                local_topic_id = str(q.get("topic_id", "0"))
                topic_name = TOPIC_ID_TO_NAME.get(local_topic_id, "Unknown")
                
                if topic_name not in all_questions_by_topic:
                    all_questions_by_topic[topic_name] = []
                all_questions_by_topic[topic_name].append(q)
        
        # Step 3: Import to production
        print()
        print("[3/3] Importing questions to production...")
        
        total_imported = 0
        total_errors = 0
        total_skipped = 0
        
        for topic_name, questions in all_questions_by_topic.items():
            prod_topic_id = prod_topics.get(topic_name)
            
            if not prod_topic_id:
                print(f"  [SKIP] Topic not found in production: {topic_name}")
                total_skipped += len(questions)
                continue
            
            print(f"  [SYNC] {topic_name} ({len(questions)} questions)...")
            
            # Import in batches of 50
            batch_size = 50
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                imported, errors = await import_questions_batch(session, batch, prod_topic_id)
                total_imported += imported
                total_errors += errors
            
            print(f"  [OK] Imported {len(questions)} questions to {topic_name}")
        
        # Summary
        print()
        print("=" * 60)
        print("Summary:")
        print(f"  - Questions imported: {total_imported}")
        print(f"  - Questions skipped: {total_skipped}")
        print(f"  - Errors: {total_errors}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
