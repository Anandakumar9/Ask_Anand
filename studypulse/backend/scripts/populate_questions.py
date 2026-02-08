"""Populate database with questions for all topics."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.exam import Topic, Subject, Exam
from app.models.question import Question
from sqlalchemy import select, func
import json


# Sample questions template for different subjects
QUESTION_TEMPLATES = {
    "Mathematics": [
        {
            "question_text": "If 2x + 5 = 15, what is the value of x?",
            "options": {"A": "5", "B": "7.5", "C": "10", "D": "15"},
            "correct_answer": "A",
            "explanation": "Solving: 2x + 5 = 15, 2x = 10, x = 5",
            "difficulty": "easy"
        },
        {
            "question_text": "What is the value of π (pi) approximately?",
            "options": {"A": "2.14", "B": "3.14", "C": "4.14", "D": "5.14"},
            "correct_answer": "B",
            "explanation": "π (pi) is approximately equal to 3.14159...",
            "difficulty": "easy"
        },
    ],
    "English": [
        {
            "question_text": "Which of the following is a noun?",
            "options": {"A": "Run", "B": "Quickly", "C": "Book", "D": "Beautiful"},
            "correct_answer": "C",
            "explanation": "A noun is a person, place, thing, or idea. 'Book' is a thing.",
            "difficulty": "easy"
        },
    ],
    "Science": [
        {
            "question_text": "What is the chemical formula for water?",
            "options": {"A": "H2O", "B": "CO2", "C": "O2", "D": "H2SO4"},
            "correct_answer": "A",
            "explanation": "Water consists of two hydrogen atoms and one oxygen atom: H2O",
            "difficulty": "easy"
        },
    ],
    "History": [
        {
            "question_text": "In which year did India gain independence?",
            "options": {"A": "1942", "B": "1947", "C": "1950", "D": "1952"},
            "correct_answer": "B",
            "explanation": "India gained independence from British rule on August 15, 1947",
            "difficulty": "medium"
        },
    ],
    "Geography": [
        {
            "question_text": "Which is the largest continent by area?",
            "options": {"A": "Africa", "B": "Asia", "C": "North America", "D": "Europe"},
            "correct_answer": "B",
            "explanation": "Asia is the largest continent with an area of about 44.58 million km²",
            "difficulty": "easy"
        },
    ],
    "Economics": [
        {
            "question_text": "What does GDP stand for?",
            "options": {
                "A": "Gross Domestic Product",
                "B": "General Development Plan",
                "C": "Global Distribution Process",
                "D": "Gross Debt Payment"
            },
            "correct_answer": "A",
            "explanation": "GDP stands for Gross Domestic Product, the total value of goods and services produced in a country",
            "difficulty": "easy"
        },
    ],
    "Banking": [
        {
            "question_text": "What is the full form of RBI?",
            "options": {
                "A": "Reserve Bank of India",
                "B": "Regional Bank of India",
                "C": "Retail Banking Institute",
                "D": "Rural Banking Initiative"
            },
            "correct_answer": "A",
            "explanation": "RBI stands for Reserve Bank of India, the central banking institution of India",
            "difficulty": "easy"
        },
    ],
}


def generate_variations(base_questions, count=50):
    """Generate variations of base questions to reach target count."""
    questions = []
    num_base = len(base_questions)
    
    for i in range(count):
        base = base_questions[i % num_base].copy()
        base['question_text'] = base['question_text'] + f" (Variation {i // num_base + 1})"
        questions.append(base)
    
    return questions


async def populate_questions():
    """Populate database with sample questions."""
    print("🚀 Starting question population...")
    
    async with AsyncSessionLocal() as db:
        # Get all topics
        topics_result = await db.execute(
            select(Topic, Subject, Exam)
            .join(Subject, Topic.subject_id == Subject.id)
            .join(Exam, Subject.exam_id == Exam.id)
        )
        topics = topics_result.all()
        
        print(f"📚 Found {len(topics)} topics to populate\n")
        
        total_added = 0
        
        for topic_row in topics:
            topic, subject, exam = topic_row
            
            # Check existing questions
            existing_count = (await db.execute(
                select(func.count(Question.id)).where(Question.topic_id == topic.id)
            )).scalar()
            
            if existing_count >= 50:
                print(f"✓ {exam.name} / {subject.name} / {topic.name}: Already has {existing_count} questions")
                continue
            
            # Find matching template
            template_key = None
            for key in QUESTION_TEMPLATES.keys():
                if key.lower() in subject.name.lower() or key.lower() in topic.name.lower():
                    template_key = key
                    break
            
            if not template_key:
                # Use default template
                template_key = "Mathematics"
            
            base_questions = QUESTION_TEMPLATES[template_key]
            questions_to_add = generate_variations(base_questions, 50 - existing_count)
            
            print(f"📝 {exam.name} / {subject.name} / {topic.name}")
            print(f"   Adding {len(questions_to_add)} questions...")
            
            for q_data in questions_to_add:
                question = Question(
                    topic_id=topic.id,
                    question_text=q_data['question_text'],
                    options=q_data['options'],  # Already a dict, no need to json.dumps
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data.get('explanation', ''),
                    difficulty=q_data.get('difficulty', 'medium'),
                    source='PREVIOUS',
                    year=2023,
                    is_validated=True
                )
                db.add(question)
            
            total_added += len(questions_to_add)
            
            # Commit in batches
            await db.commit()
            print(f"   ✅ Added {len(questions_to_add)} questions (Total now: {existing_count + len(questions_to_add)})")
        
        print(f"\n🎉 Complete! Added {total_added} new questions total")
        
        # Show summary
        total_questions = (await db.execute(select(func.count(Question.id)))).scalar()
        total_topics = (await db.execute(select(func.count(func.distinct(Question.topic_id))))).scalar()
        print(f"\n📊 Database now has {total_questions} questions across {total_topics} topics")


if __name__ == "__main__":
    asyncio.run(populate_questions())
