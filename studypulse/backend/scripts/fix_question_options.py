#!/usr/bin/env python3
"""
Fix Question Options Format

This script fixes questions that have options stored as arrays instead of dicts.
The QuestionCard component expects options as {"A": "...", "B": "...", "C": "...", "D": "..."}
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async def fix_question_options():
    """Fix questions with array options to dict format."""
    
    print("\n" + "="*60)
    print("FIX QUESTION OPTIONS FORMAT")
    print("="*60)
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    fixed_count = 0
    error_count = 0
    skipped_count = 0
    
    async with async_session() as session:
        # Get all questions using raw SQL to handle JSON errors
        result = await session.execute(text("SELECT id, options, correct_answer FROM questions"))
        rows = result.fetchall()
        
        print(f"\n[INFO] Found {len(rows)} questions in database")
        
        for row in rows:
            q_id = row[0]
            options_raw = row[1]
            correct_answer_raw = row[2]
            
            try:
                # Parse options JSON
                if options_raw is None:
                    skipped_count += 1
                    continue
                    
                if isinstance(options_raw, str):
                    options = json.loads(options_raw)
                else:
                    options = options_raw
                
                needs_update = False
                new_options = None
                new_correct_answer = correct_answer_raw
                
                # Check if options is a list (wrong format)
                if isinstance(options, list):
                    # Convert list to dict
                    options_dict = {}
                    for idx, opt in enumerate(options):
                        label = chr(ord('A') + idx)  # 0 -> 'A', 1 -> 'B', etc.
                        if isinstance(opt, dict):
                            # Handle dict option
                            options_dict[label] = opt.get('text', str(opt))
                        else:
                            options_dict[label] = str(opt)
                    
                    new_options = json.dumps(options_dict)
                    needs_update = True
                
                elif isinstance(options, dict):
                    # Check if keys are lowercase (should be uppercase)
                    keys = list(options.keys())
                    if keys and keys[0].islower():
                        # Convert keys to uppercase
                        options_dict = {}
                        for key, value in options.items():
                            upper_key = key.upper()
                            options_dict[upper_key] = value
                        new_options = json.dumps(options_dict)
                        needs_update = True
                
                # Fix correct_answer to be uppercase
                if correct_answer_raw:
                    correct = str(correct_answer_raw).upper().strip()
                    if '.' in correct:
                        correct = correct.split('.')[0].strip()
                    if len(correct) > 1:
                        correct = correct[0].upper()
                    if correct != correct_answer_raw:
                        new_correct_answer = correct
                        needs_update = True
                
                if needs_update:
                    if new_options:
                        await session.execute(
                            text("UPDATE questions SET options = :options, correct_answer = :correct WHERE id = :id"),
                            {"options": new_options, "correct": new_correct_answer, "id": q_id}
                        )
                    else:
                        await session.execute(
                            text("UPDATE questions SET correct_answer = :correct WHERE id = :id"),
                            {"correct": new_correct_answer, "id": q_id}
                        )
                    fixed_count += 1
                    
                    if fixed_count % 100 == 0:
                        print(f"  [PROGRESS] Fixed {fixed_count} questions...")
                        
            except json.JSONDecodeError as e:
                print(f"  [ERROR] Question {q_id}: JSON decode error - {e}")
                error_count += 1
                continue
            except Exception as e:
                print(f"  [ERROR] Question {q_id}: {e}")
                error_count += 1
                continue
        
        await session.commit()
    
    await engine.dispose()
    
    print(f"\n[COMPLETE] Fixed {fixed_count} questions")
    print(f"[SKIPPED] {skipped_count} questions skipped (null options)")
    print(f"[ERRORS] {error_count} errors encountered")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(fix_question_options())
