"""Comprehensive Demo Data Seeder for StudyPulse.

Creates realistic demo data for testing:
- 8 Exams (UPSC, NEET PG, IBPS PO, SSC CGL, JEE Main, CAT, CBSE 12, GATE)
- ~200 Topics across all exams
- ~10,000+ Questions (mix of PREVIOUS, CSV, and AI)
- 20 Demo Users with realistic activity
- 50-100 Study Sessions
- 30-50 Mock Tests with results
- 50+ Question Ratings

Usage:
    python seed_complete_demo.py
"""
import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question, QuestionRating
from app.models.user import User
from app.models.mock_test import StudySession, MockTest, QuestionResponse

# ── Demo Data Definitions ──────────────────────────────────────

DEMO_EXAMS = {
    "UPSC Civil Services": {
        "subjects": {
            "General Studies I": ["Ancient India", "Medieval India", "Modern India", "World History", "Geography - Physical",
                                   "Geography - Indian", "Indian Society", "Art & Culture"],
            "General Studies II": ["Governance", "Constitution", "Polity", "Social Justice", "International Relations",
                                    "Public Policy", "Development", "Rights Issues"],
            "General Studies III": ["Economy", "Agriculture", "Science & Technology", "Environment", "Internal Security",
                                     "Disaster Management", "Infrastructure", "Energy"],
            "General Studies IV": ["Ethics Foundations", "Public Service Values", "Emotional Intelligence", "Case Studies",
                                    "Aptitude", "Integrity"],
            "CSAT": ["Comprehension", "Logical Reasoning", "Analytical Ability", "Decision Making", "Data Interpretation",
                      "Basic Numeracy", "Mental Ability", "Problem Solving"]
        }
    },
    "NEET PG": {
        "subjects": {
            "Anatomy": ["Gross Anatomy", "Embryology", "Histology", "Neuroanatomy", "Applied Anatomy"],
            "Physiology": ["General Physiology", "Respiratory System", "Cardiovascular System", "Nervous System",
                           "Endocrine System", "Renal System"],
            "Pathology": ["General Pathology", "Systemic Pathology", "Clinical Pathology", "Hematology",
                          "Microbiology"],
            "Medicine": ["Cardiology", "Respiratory Medicine", "Gastroenterology", "Nephrology", "Infectious Diseases",
                         "Rheumatology", "Endocrinology"],
            "Surgery": ["General Surgery", "Orthopedics", "Ophthalmology", "ENT", "Neurosurgery",
                        "Urology", "Pediatric Surgery"]
        }
    },
    "IBPS PO": {
        "subjects": {
            "Quantitative Aptitude": ["Number System", "Simplification", "Data Interpretation", "Profit & Loss",
                                       "Time & Work", "Ratio & Proportion", "Average", "Percentage"],
            "Reasoning Ability": ["Logical Reasoning", "Verbal Reasoning", "Analytical Reasoning", "Puzzles",
                                   "Seating Arrangement", "Blood Relations", "Direction Sense"],
            "English Language": ["Reading Comprehension", "Grammar", "Vocabulary", "Error Spotting", "Cloze Test",
                                  "Para Jumbles", "Sentence Correction"],
            "Banking Awareness": ["Banking Terms", "RBI Functions", "Banking Reforms", "Financial Institutions",
                                   "Digital Banking", "Banking Regulations"],
            "Current Affairs": ["National News", "International News", "Banking News", "Economic Affairs",
                                "Awards & Honors", "Sports", "Obituaries"]
        }
    },
    "SSC CGL": {
        "subjects": {
            "General Intelligence": ["Analogies", "Similarities", "Differences", "Space Visualization", "Problem Solving",
                                      "Analysis", "Judgment", "Decision Making"],
            "General Awareness": ["History", "Geography", "Economics", "Polity", "Science", "Current Affairs",
                                   "Static GK"],
            "Quantitative Aptitude": ["Arithmetic", "Algebra", "Geometry", "Trigonometry", "Statistics",
                                       "Data Interpretation"],
            "English Comprehension": ["Vocabulary", "Grammar", "Sentence Structure", "Reading Comprehension",
                                       "Synonyms & Antonyms", "Idioms & Phrases"]
        }
    },
    "JEE Main": {
        "subjects": {
            "Physics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Modern Physics",
                        "Waves & Oscillations", "Properties of Matter"],
            "Chemistry": ["Physical Chemistry", "Inorganic Chemistry", "Organic Chemistry", "Environmental Chemistry",
                          "Nuclear Chemistry", "Coordination Chemistry"],
            "Mathematics": ["Algebra", "Calculus", "Coordinate Geometry", "Trigonometry", "Probability & Statistics",
                            "Vector Algebra", "3D Geometry", "Differential Equations"]
        }
    },
    "CAT": {
        "subjects": {
            "Quantitative Ability": ["Number System", "Algebra", "Geometry", "Arithmetic", "Modern Math",
                                      "Mensuration", "Trigonometry"],
            "Verbal Ability": ["Reading Comprehension", "Para Jumbles", "Para Summary", "Sentence Correction",
                                "Critical Reasoning", "Vocabulary"],
            "Data Interpretation": ["Tables", "Bar Graphs", "Line Graphs", "Pie Charts", "Caselets", "Mixed Graphs"],
            "Logical Reasoning": ["Arrangements", "Selections", "Binary Logic", "Games & Tournaments",
                                   "Networks", "Venn Diagrams"]
        }
    },
    "CBSE Class 12": {
        "subjects": {
            "Physics": ["Electrostatics", "Current Electricity", "Magnetism", "Optics", "Modern Physics",
                        "Electromagnetic Induction", "Waves"],
            "Chemistry": ["Solid State", "Solutions", "Electrochemistry", "Chemical Kinetics", "Coordination Compounds",
                          "Haloalkanes", "Alcohols Phenols Ethers"],
            "Mathematics": ["Relations & Functions", "Matrices", "Determinants", "Continuity", "Differentiation",
                            "Integration", "Vectors", "3D Geometry", "Linear Programming"],
            "Biology": ["Reproduction", "Genetics", "Evolution", "Human Health", "Ecology", "Biotechnology",
                        "Organisms & Populations"]
        }
    },
    "GATE": {
        "subjects": {
            "Engineering Mathematics": ["Linear Algebra", "Calculus", "Differential Equations", "Probability",
                                         "Numerical Methods", "Complex Variables"],
            "Digital Logic": ["Boolean Algebra", "Combinational Circuits", "Sequential Circuits", "Number Systems",
                              "Logic Gates"],
            "Computer Organization": ["Instruction Set", "CPU Design", "Memory Hierarchy", "I/O Interface",
                                       "Pipelining", "Cache"],
            "Algorithms": ["Sorting", "Searching", "Graph Algorithms", "Greedy", "Dynamic Programming",
                           "Divide & Conquer"],
            "Data Structures": ["Arrays", "Linked Lists", "Stacks & Queues", "Trees", "Graphs", "Hashing"]
        }
    }
}

# Sample questions templates (will be varied programmatically)
QUESTION_TEMPLATES = {
    "UPSC": {
        "question": "Which of the following statements about {topic} is/are correct?\n1. Statement 1\n2. Statement 2\n3. Statement 3",
        "options": {"A": "1 only", "B": "1 and 2", "C": "2 and 3", "D": "1, 2 and 3"},
        "difficulty_dist": {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    },
    "NEET PG": {
        "question": "A 45-year-old patient presents with {symptom}. What is the most likely diagnosis related to {topic}?",
        "options": {"A": "Diagnosis 1", "B": "Diagnosis 2", "C": "Diagnosis 3", "D": "Diagnosis 4"},
        "difficulty_dist": {"easy": 0.2, "medium": 0.5, "hard": 0.3}
    },
    "IBPS PO": {
        "question": "If {condition} related to {topic}, then what is the value?",
        "options": {"A": "100", "B": "150", "C": "200", "D": "250"},
        "difficulty_dist": {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    },
    "SSC CGL": {
        "question": "Which of the following is true about {topic}?",
        "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
        "difficulty_dist": {"easy": 0.4, "medium": 0.4, "hard": 0.2}
    },
    "JEE Main": {
        "question": "A problem involving {topic}. Calculate the value.",
        "options": {"A": "10", "B": "20", "C": "30", "D": "40"},
        "difficulty_dist": {"easy": 0.2, "medium": 0.5, "hard": 0.3}
    },
    "CAT": {
        "question": "Based on {topic}, determine the correct answer.",
        "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        "difficulty_dist": {"easy": 0.25, "medium": 0.5, "hard": 0.25}
    },
    "CBSE Class 12": {
        "question": "Explain the concept of {topic} and choose the correct option.",
        "options": {"A": "Answer 1", "B": "Answer 2", "C": "Answer 3", "D": "Answer 4"},
        "difficulty_dist": {"easy": 0.4, "medium": 0.4, "hard": 0.2}
    },
    "GATE": {
        "question": "Consider the {topic}. What is the time complexity?",
        "options": {"A": "O(1)", "B": "O(n)", "C": "O(n log n)", "D": "O(n²)"},
        "difficulty_dist": {"easy": 0.2, "medium": 0.5, "hard": 0.3}
    }
}

DEMO_USERS = [
    {"name": "Rahul Sharma", "email": "rahul@demo.com", "stars": 120},
    {"name": "Priya Singh", "email": "priya@demo.com", "stars": 95},
    {"name": "Amit Patel", "email": "amit@demo.com", "stars": 150},
    {"name": "Sneha Gupta", "email": "sneha@demo.com", "stars": 85},
    {"name": "Vikas Kumar", "email": "vikas@demo.com", "stars": 110},
    {"name": "Divya Reddy", "email": "divya@demo.com", "stars": 75},
    {"name": "Arjun Mehta", "email": "arjun@demo.com", "stars": 130},
    {"name": "Kavya Iyer", "email": "kavya@demo.com", "stars": 90},
    {"name": "Ravi Verma", "email": "ravi@demo.com", "stars": 105},
    {"name": "Anjali Shah", "email": "anjali@demo.com", "stars": 80},
    {"name": "Karthik Nair", "email": "karthik@demo.com", "stars": 140},
    {"name": "Neha Joshi", "email": "neha@demo.com", "stars": 70},
    {"name": "Sanjay Desai", "email": "sanjay@demo.com", "stars": 115},
    {"name": "Pooja Rao", "email": "pooja@demo.com", "stars": 95},
    {"name": "Manish Kulkarni", "email": "manish@demo.com", "stars": 125},
    {"name": "Ritika Bose", "email": "ritika@demo.com", "stars": 85},
    {"name": "Abhishek Jain", "email": "abhishek@demo.com", "stars": 100},
    {"name": "Swati Pillai", "email": "swati@demo.com", "stars": 90},
    {"name": "Nikhil Sinha", "email": "nikhil@demo.com", "stars": 135},
]


# ── Helper Functions ────────────────────────────────────────────

async def create_exams_subjects_topics(db: AsyncSession):
    """Create exam hierarchy."""
    print("\n1. Creating Exams, Subjects, and Topics...")

    exam_map = {}
    subject_map = {}
    topic_list = []

    for exam_name, exam_data in DEMO_EXAMS.items():
        # Create exam
        exam = Exam(name=exam_name, description=f"Full syllabus for {exam_name}")
        db.add(exam)
        await db.flush()
        exam_map[exam_name] = exam
        print(f"  [OK] {exam_name} (ID: {exam.id})")

        # Create subjects
        for subject_name, topics in exam_data["subjects"].items():
            subject = Subject(
                exam_id=exam.id,
                name=subject_name,
                description=f"{subject_name} - {exam_name}"
            )
            db.add(subject)
            await db.flush()
            subject_map[f"{exam_name}::{subject_name}"] = subject
            print(f"    [OK] {subject_name} (ID: {subject.id})")

            # Create topics
            for topic_name in topics:
                topic = Topic(
                    subject_id=subject.id,
                    name=topic_name,
                    description=f"Study material for {topic_name}",
                    difficulty_level=random.choice(["Easy", "Medium", "Hard"]),
                    estimated_study_mins=random.randint(15, 120)
                )
                db.add(topic)
                await db.flush()
                topic_list.append((topic, exam_name, subject_name))

    await db.commit()
    print(f"\n  Created: {len(exam_map)} exams, {len(subject_map)} subjects, {len(topic_list)} topics")
    return exam_map, subject_map, topic_list


async def create_questions(db: AsyncSession, topic_list: List[tuple]):
    """Create 50-100 questions per topic (~10,000+ total)."""
    print("\n2. Creating Questions (~10,000+)...")

    total_questions = 0

    for topic, exam_name, subject_name in topic_list:
        # Get question template for this exam
        template = QUESTION_TEMPLATES.get(exam_name.split()[0], QUESTION_TEMPLATES["UPSC"])
        difficulty_dist = template["difficulty_dist"]

        # Generate 50-100 questions per topic
        question_count = random.randint(50, 100)

        for i in range(question_count):
            # Determine difficulty based on distribution
            rand = random.random()
            if rand < difficulty_dist["easy"]:
                difficulty = "easy"
            elif rand < difficulty_dist["easy"] + difficulty_dist["medium"]:
                difficulty = "medium"
            else:
                difficulty = "hard"

            # Determine source (60% PREVIOUS, 30% CSV, 10% AI)
            rand_source = random.random()
            if rand_source < 0.6:
                source = "PREVIOUS"
                year = random.randint(2015, 2024) if random.random() > 0.3 else None
            elif rand_source < 0.9:
                source = "CSV"
                year = None
            else:
                source = "AI"
                year = None

            # Create question text (varied)
            question_text = f"Question {i+1} on {topic.name}: " + template["question"].replace("{topic}", topic.name)

            # Randomize correct answer
            correct_answer = random.choice(["A", "B", "C", "D"])

            # Create question
            question = Question(
                topic_id=topic.id,
                question_text=question_text,
                options=template["options"].copy(),
                correct_answer=correct_answer,
                explanation=f"Explanation for {topic.name} question {i+1}. The correct answer is {correct_answer} because...",
                difficulty=difficulty,
                source=source,
                year=year
            )
            db.add(question)
            total_questions += 1

        if total_questions % 500 == 0:
            await db.commit()
            print(f"    Progress: {total_questions} questions created...")

    await db.commit()
    print(f"  [OK] Created {total_questions} questions")
    return total_questions


async def create_users(db: AsyncSession):
    """Create 19 demo users."""
    print("\n3. Creating Demo Users...")

    users = []
    join_date_start = datetime.now() - timedelta(days=180)  # Last 6 months

    for user_data in DEMO_USERS:
        # Random join date in last 6 months
        days_ago = random.randint(0, 180)
        join_date = join_date_start + timedelta(days=days_ago)

        user = User(
            email=user_data["email"],
            name=user_data["name"],
            hashed_password="$2b$12$demopasswordhash",  # Demo password
            total_stars=user_data["stars"],
            is_active=True,
            is_first_login=False,
            created_at=join_date
        )
        db.add(user)
        users.append(user)

    await db.commit()
    print(f"  [OK] Created {len(users)} demo users")
    return users


async def create_study_sessions(db: AsyncSession, users: List[User], topic_list: List[tuple]):
    """Create 50-100 study sessions."""
    print("\n4. Creating Study Sessions...")

    session_count = random.randint(50, 100)
    sessions = []

    for i in range(session_count):
        user = random.choice(users)
        topic, _, _ = random.choice(topic_list)

        # Random date in last 3 months
        days_ago = random.randint(0, 90)
        started_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

        # Random duration
        duration_mins = random.choice([15, 30, 45, 60, 90, 120])

        # 80% completed, 20% incomplete
        completed = random.random() < 0.8

        session = StudySession(
            user_id=user.id,
            topic_id=topic.id,
            duration_mins=duration_mins,
            actual_duration_mins=duration_mins if completed else random.randint(5, duration_mins),
            started_at=started_at,
            ended_at=started_at + timedelta(minutes=duration_mins) if completed else None,
            completed=completed
        )
        db.add(session)
        sessions.append(session)

    await db.commit()
    print(f"  [OK] Created {len(sessions)} study sessions")
    return sessions


async def create_mock_tests(db: AsyncSession, users: List[User], topic_list: List[tuple]):
    """Create 30-50 mock tests with results."""
    print("\n5. Creating Mock Tests...")

    test_count = random.randint(30, 50)
    tests = []

    for i in range(test_count):
        user = random.choice(users)
        topic,_, _ = random.choice(topic_list)

        # Get questions for this topic
        result = await db.execute(
            select(Question).where(Question.topic_id == topic.id).limit(10)
        )
        questions = result.scalars().all()

        if len(questions) < 10:
            continue  # Skip if insufficient questions

        # Random test date in last 2 months
        days_ago = random.randint(0, 60)
        started_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

        # Generate realistic score (40-95%)
        score_percentage = random.randint(40, 95)
        correct_count = int(10 * score_percentage / 100)
        incorrect_count = 10 - correct_count

        # Time taken (8-15 minutes for 10 questions)
        time_taken = random.randint(480, 900)  # seconds

        test = MockTest(
            user_id=user.id,
            topic_id=topic.id,
            total_questions=10,
            correct_answers=correct_count,
            score_percentage=score_percentage,
            time_taken_seconds=time_taken,
            star_earned=(score_percentage >= 70),
            status="completed",
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=time_taken),
            question_ids=[q.id for q in questions[:10]]
        )
        db.add(test)
        await db.flush()
        tests.append(test)

        # Add responses for each question
        for j, question in enumerate(questions[:10]):
            is_correct = j < correct_count
            user_answer = question.correct_answer if is_correct else random.choice([a for a in ["A", "B", "C", "D"] if a != question.correct_answer])

            response = QuestionResponse(
                mock_test_id=test.id,
                question_id=question.id,
                user_answer=user_answer,
                is_correct=is_correct,
                time_spent_seconds=random.randint(30, 120)
            )
            db.add(response)

    await db.commit()
    print(f"  [OK] Created {len(tests)} mock tests with results")
    return tests


async def create_question_ratings(db: AsyncSession, users: List[User]):
    """Create 50+ question ratings."""
    print("\n6. Creating Question Ratings...")

    # Get AI questions
    result = await db.execute(
        select(Question).where(Question.source == "AI").limit(50)
    )
    ai_questions = result.scalars().all()

    ratings = []

    for question in ai_questions:
        # Random user
        user = random.choice(users)

        # Distribution: 70% good (7-10), 20% medium (5-6), 10% poor (1-4)
        rand = random.random()
        if rand < 0.7:
            rating = random.randint(7, 10)
            feedback = random.choice([
                "Great question!",
                "Very relevant",
                "Helpful for exam prep",
                None
            ])
        elif rand < 0.9:
            rating = random.randint(5, 6)
            feedback = random.choice([
                "Good but could be clearer",
                "Average question",
                None
            ])
        else:
            rating = random.randint(1, 4)
            feedback = random.choice([
                "Confusing options",
                "Not relevant",
                "Poor quality"
            ])

        rating_obj = QuestionRating(
            question_id=question.id,
            user_id=user.id,
            rating=rating
        )
        db.add(rating_obj)
        ratings.append(rating_obj)

    await db.commit()
    print(f"  [OK] Created {len(ratings)} question ratings")
    return ratings


async def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("  StudyPulse Comprehensive Demo Data Seeder")
    print("="*60)

    # Initialize database
    print("\nInitializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Check if data already exists
        result = await db.execute(select(func.count(Exam.id)))
        exam_count = result.scalar()

        if exam_count > 0:
            print("\n[WARNING] Database already contains data!")
            print(f"Found {exam_count} exams. Run cleanup_demo_data.py first to clear.")
            return

        try:
            # Step 1: Create exam hierarchy
            exam_map, subject_map, topic_list = await create_exams_subjects_topics(db)

            # Step 2: Create questions
            total_questions = await create_questions(db, topic_list)

            # Step 3: Create users
            users = await create_users(db)

            # Step 4: Create study sessions
            sessions = await create_study_sessions(db, users, topic_list)

            # Step 5: Create mock tests
            tests = await create_mock_tests(db, users, topic_list)

            # Step 6: Create question ratings
            ratings = await create_question_ratings(db, users)

            print("\n" + "="*60)
            print("  [SUCCESS] Demo Data Seeding Complete!")
            print("="*60)
            print(f"\n  Summary:")
            print(f"    - Exams: {len(exam_map)}")
            print(f"    - Subjects: {len(subject_map)}")
            print(f"    - Topics: {len(topic_list)}")
            print(f"    - Questions: {total_questions}")
            print(f"    - Users: {len(users)}")
            print(f"    - Study Sessions: {len(sessions)}")
            print(f"    - Mock Tests: {len(tests)}")
            print(f"    - Question Ratings: {len(ratings)}")
            print(f"\n  The system is now ready for testing!")
            print("="*60 + "\n")

        except Exception as e:
            print(f"\n[ERROR] Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
