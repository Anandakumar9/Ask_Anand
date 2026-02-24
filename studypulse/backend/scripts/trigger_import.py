#!/usr/bin/env python3
"""Trigger question import on production server by sending JSON data."""

import requests
import json
import os
from pathlib import Path

API_URL = "https://askanand-simba.up.railway.app"

# Topic mapping for Gynaecology & Obstetrics (integer keys to match JSON)
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

# JSON files to import
JSON_FILES = [
    "data/gynaecology_obstetrics_import.json",
    "data/neet_cereb_gynae_import.json",
    "data/neet_obgyn_edition8_import.json",
    "data/neet_prepx_gynae_import.json",
]


def check_status():
    """Check current database status."""
    print("Checking current status...")
    response = requests.get(f"{API_URL}/api/v1/admin/status")
    if response.status_code == 200:
        data = response.json()
        print(f"Total questions: {data['total_questions']}")
        print(f"By source: {data['by_source']}")
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def import_from_file(json_path: str):
    """Import questions from a local JSON file to production."""
    
    if not os.path.exists(json_path):
        print(f"[SKIP] File not found: {json_path}")
        return {"imported": 0, "skipped": 0, "errors": 0}
    
    print(f"\n[PROCESSING] {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get questions list
    questions = data.get('questions', [])
    if not questions:
        questions = data.get('data', [])
    if not questions:
        questions = data if isinstance(data, list) else []
    
    print(f"  [FOUND] {len(questions)} questions in file")
    
    if not questions:
        return {"imported": 0, "skipped": 0, "errors": 0}
    
    # Send to API
    print(f"  [SENDING] {len(questions)} questions to production...")
    
    response = requests.post(
        f"{API_URL}/api/v1/admin/import-json",
        json={
            "exam_name": "NEET PG",
            "subject_name": "Gynaecology & Obstetrics",
            "questions": questions,
            "topic_mapping": TOPIC_MAPPING
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  [RESULT] Imported: {result['imported']}, Skipped: {result['skipped']}, Errors: {result['errors']}")
        return result
    else:
        print(f"  [ERROR] {response.status_code} - {response.text}")
        return {"imported": 0, "skipped": 0, "errors": len(questions)}


def main():
    """Main import function."""
    
    # Check initial status
    print("="*60)
    print("PRODUCTION QUESTION IMPORT")
    print("="*60)
    
    initial_status = check_status()
    
    # Get data directory
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / "data"
    
    # Import from each file
    total_stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    for json_file in JSON_FILES:
        json_path = data_dir / json_file.split('/')[-1]
        stats = import_from_file(str(json_path))
        total_stats["imported"] += stats["imported"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["errors"] += stats["errors"]
    
    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total imported: {total_stats['imported']}")
    print(f"Total skipped:  {total_stats['skipped']}")
    print(f"Total errors:   {total_stats['errors']}")
    
    # Check final status
    print("\n" + "="*60)
    print("FINAL STATUS")
    print("="*60)
    final_status = check_status()
    
    if final_status:
        # Find NEET PG exam
        for exam in final_status['exams']:
            if 'NEET' in exam['name']:
                print(f"\n{exam['name']} subjects:")
                for subject in exam['subjects']:
                    total = sum(t['question_count'] for t in subject['topics'])
                    print(f"  {subject['name']}: {total} questions")


if __name__ == "__main__":
    main()
