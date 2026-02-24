import requests
import json

# Test with a single question
test_data = {
    "exam_name": "NEET PG",
    "subject_name": "Gynaecology & Obstetrics",
    "questions": [
        {
            "topic_id": 1,
            "question_text": "Test question for import verification",
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A",
            "source": "TEST"
        }
    ],
    "topic_mapping": {1: "Cervical Carcinoma"}
}

print("Sending test import request...")
response = requests.post(
    "http://localhost:8000/api/v1/admin/import-json",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
