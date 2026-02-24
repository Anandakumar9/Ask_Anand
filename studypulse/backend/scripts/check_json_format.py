#!/usr/bin/env python3
"""Check JSON file format for debugging."""

import json
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

files = [
    "gynaecology_obstetrics_import.json",
    "neet_cereb_gynae_import.json",
]

for filename in files:
    filepath = data_dir / filename
    if not filepath.exists():
        print(f"[SKIP] {filename} not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"FILE: {filename}")
    print('='*60)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get structure
    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
        questions = data.get('questions', data.get('data', []))
    else:
        questions = data
    
    print(f"Total questions: {len(questions)}")
    
    # Sample first 3 questions
    for i, q in enumerate(questions[:3]):
        print(f"\n--- Question {i+1} ---")
        print(f"  topic_id: {q.get('topic_id')} (type: {type(q.get('topic_id')).__name__})")
        print(f"  question_text: {q.get('question_text', '')[:80]}...")
        print(f"  correct_answer: {q.get('correct_answer')}")
        options = q.get('options', {})
        print(f"  options type: {type(options).__name__}")
        if isinstance(options, dict):
            print(f"  options keys: {list(options.keys())[:4]}")
        elif isinstance(options, list):
            print(f"  options count: {len(options)}")
