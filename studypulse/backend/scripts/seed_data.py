"""
Seed script to populate the database with sample data for testing.
Run this after setting up the database.

Usage:
    python -m scripts.seed_data
"""
import asyncio
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, init_db
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from app.models.user import User
from app.core.security import get_password_hash


async def seed_data():
    """Seed the database with sample data."""
    print("🌱 Starting database seeding...")
    
    # Initialize database tables
    await init_db()
    print("✅ Database tables created")
    
    async with AsyncSessionLocal() as db:
        # Check if data already exists
        from sqlalchemy import select
        result = await db.execute(select(Exam))
        if result.scalars().first():
            print("⚠️ Data already exists. Skipping seed.")
            return
        
        # Create sample exams
        exams = [
            Exam(
                name="JEE Main",
                description="Joint Entrance Examination - Main for Engineering Admissions",
                category="Engineering",
                conducting_body="NTA",
                exam_duration_mins=180,
                total_questions=90
            ),
            Exam(
                name="NEET UG",
                description="National Eligibility cum Entrance Test for Medical Admissions",
                category="Medical",
                conducting_body="NTA",
                exam_duration_mins=180,
                total_questions=200
            ),
            Exam(
                name="UPSC Civil Services",
                description="Union Public Service Commission Civil Services Examination",
                category="Government",
                conducting_body="UPSC",
                exam_duration_mins=180,
                total_questions=100
            ),
            Exam(
                name="SSC CGL",
                description="Staff Selection Commission Combined Graduate Level",
                category="Government",
                conducting_body="SSC",
                exam_duration_mins=120,
                total_questions=100
            ),
            Exam(
                name="IBPS PO",
                description="Institute of Banking Personnel Selection - Probationary Officer",
                category="Banking",
                conducting_body="IBPS",
                exam_duration_mins=180,
                total_questions=100
            ),
            Exam(
                name="CAT",
                description="Common Admission Test for MBA",
                category="Management",
                conducting_body="IIM",
                exam_duration_mins=120,
                total_questions=66
            ),
            Exam(
                name="CBSE Class 10",
                description="Central Board of Secondary Education Class 10 Boards",
                category="School",
                conducting_body="CBSE",
                exam_duration_mins=180,
                total_questions=40
            ),
            Exam(
                name="CBSE Class 12",
                description="Central Board of Secondary Education Class 12 Boards",
                category="School",
                conducting_body="CBSE",
                exam_duration_mins=180,
                total_questions=40
            ),
        ]
        
        for exam in exams:
            db.add(exam)
        await db.commit()
        
        # Refresh to get IDs
        for exam in exams:
            await db.refresh(exam)
        
        print(f"✅ Created {len(exams)} exams")
        
        # Create subjects and topics for ALL exams
        all_subjects = []
        all_topics = []
        
        # JEE Main subjects and topics
        jee = exams[0]
        jee_subjects = [
            Subject(exam_id=jee.id, name="Physics", description="Mechanics, Thermodynamics, Electromagnetism, Optics, Modern Physics"),
            Subject(exam_id=jee.id, name="Chemistry", description="Physical, Organic, and Inorganic Chemistry"),
            Subject(exam_id=jee.id, name="Mathematics", description="Algebra, Calculus, Trigonometry, Geometry, Statistics"),
        ]
        all_subjects.extend(jee_subjects)
        
        jee_topics = [
            # Physics topics
            Topic(subject_id=None, name="Laws of Motion", difficulty_level="medium"),
            Topic(subject_id=None, name="Gravitation", difficulty_level="medium"),
            Topic(subject_id=None, name="Thermodynamics", difficulty_level="hard"),
            Topic(subject_id=None, name="Electromagnetic Induction", difficulty_level="hard"),
            Topic(subject_id=None, name="Optics and Wave Theory", difficulty_level="medium"),
            Topic(subject_id=None, name="Modern Physics - Atoms and Nuclei", difficulty_level="hard"),
            # Chemistry topics
            Topic(subject_id=None, name="Chemical Bonding", difficulty_level="medium"),
            Topic(subject_id=None, name="Organic Chemistry Basics", difficulty_level="medium"),
            Topic(subject_id=None, name="Coordination Compounds", difficulty_level="hard"),
            Topic(subject_id=None, name="Electrochemistry", difficulty_level="medium"),
            # Mathematics topics
            Topic(subject_id=None, name="Differential Calculus", difficulty_level="hard"),
            Topic(subject_id=None, name="Integral Calculus", difficulty_level="hard"),
            Topic(subject_id=None, name="Probability and Statistics", difficulty_level="medium"),
            Topic(subject_id=None, name="3D Geometry", difficulty_level="hard"),
            Topic(subject_id=None, name="Complex Numbers", difficulty_level="medium"),
        ]
        
        # NEET subjects and topics
        neet = exams[1]
        neet_subjects = [
            Subject(exam_id=neet.id, name="Physics", description="Mechanics, Optics, Thermodynamics, Modern Physics"),
            Subject(exam_id=neet.id, name="Chemistry", description="Physical, Organic, and Inorganic Chemistry"),
            Subject(exam_id=neet.id, name="Biology", description="Botany and Zoology"),
        ]
        all_subjects.extend(neet_subjects)
        
        neet_topics = [
            # Biology topics
            Topic(subject_id=None, name="Cell Biology", difficulty_level="easy"),
            Topic(subject_id=None, name="Genetics and Evolution", difficulty_level="hard"),
            Topic(subject_id=None, name="Plant Physiology", difficulty_level="medium"),
            Topic(subject_id=None, name="Human Physiology", difficulty_level="medium"),
            Topic(subject_id=None, name="Ecology and Environment", difficulty_level="easy"),
            # Additional Chemistry
            Topic(subject_id=None, name="Biomolecules", difficulty_level="medium"),
        ]
        
        # UPSC subjects and topics
        upsc = exams[2]
        upsc_subjects = [
            Subject(exam_id=upsc.id, name="Geography", description="Physical and Human Geography"),
            Subject(exam_id=upsc.id, name="History", description="Indian and World History"),
            Subject(exam_id=upsc.id, name="Polity", description="Indian Constitution and Governance"),
            Subject(exam_id=upsc.id, name="Economy", description="Indian and World Economy"),
            Subject(exam_id=upsc.id, name="Current Affairs", description="National and International Events"),
        ]
        all_subjects.extend(upsc_subjects)
        
        upsc_topics = [
            # Geography
            Topic(subject_id=None, name="Physical Geography of India", difficulty_level="medium"),
            Topic(subject_id=None, name="Climate and Monsoons", difficulty_level="medium"),
            Topic(subject_id=None, name="Rivers and Drainage", difficulty_level="easy"),
            Topic(subject_id=None, name="Natural Vegetation", difficulty_level="easy"),
            Topic(subject_id=None, name="Mineral Resources", difficulty_level="hard"),
            # History
            Topic(subject_id=None, name="Ancient India", difficulty_level="medium"),
            Topic(subject_id=None, name="Medieval India", difficulty_level="medium"),
            Topic(subject_id=None, name="Modern India", difficulty_level="medium"),
            Topic(subject_id=None, name="Indian Freedom Struggle", difficulty_level="easy"),
            # Polity
            Topic(subject_id=None, name="Fundamental Rights", difficulty_level="easy"),
            Topic(subject_id=None, name="Directive Principles", difficulty_level="medium"),
            Topic(subject_id=None, name="Union Legislature", difficulty_level="medium"),
            Topic(subject_id=None, name="State Legislature", difficulty_level="medium"),
            # Economy
            Topic(subject_id=None, name="Indian Budget", difficulty_level="medium"),
            Topic(subject_id=None, name="Banking System", difficulty_level="medium"),
            Topic(subject_id=None, name="Economic Reforms", difficulty_level="hard"),
        ]
        
        # SSC CGL subjects and topics
        ssc = exams[3]
        ssc_subjects = [
            Subject(exam_id=ssc.id, name="General Intelligence", description="Logical Reasoning and Analytical Ability"),
            Subject(exam_id=ssc.id, name="General Awareness", description="Current Affairs, History, Geography, Science"),
            Subject(exam_id=ssc.id, name="Quantitative Aptitude", description="Mathematics and Data Interpretation"),
            Subject(exam_id=ssc.id, name="English Comprehension", description="Grammar, Vocabulary, Reading Comprehension"),
        ]
        all_subjects.extend(ssc_subjects)
        
        ssc_topics = [
            Topic(subject_id=None, name="Logical Puzzles", difficulty_level="medium"),
            Topic(subject_id=None, name="Number Series", difficulty_level="easy"),
            Topic(subject_id=None, name="Data Interpretation", difficulty_level="hard"),
            Topic(subject_id=None, name="Reading Comprehension", difficulty_level="medium"),
        ]
        
        # IBPS PO subjects and topics
        ibps = exams[4]
        ibps_subjects = [
            Subject(exam_id=ibps.id, name="Reasoning Ability", description="Logical and Analytical Reasoning"),
            Subject(exam_id=ibps.id, name="Quantitative Aptitude", description="Mathematics and Data Analysis"),
            Subject(exam_id=ibps.id, name="English Language", description="Grammar and Comprehension"),
            Subject(exam_id=ibps.id, name="Banking Awareness", description="Banking Concepts and Current Affairs"),
        ]
        all_subjects.extend(ibps_subjects)
        
        ibps_topics = [
            Topic(subject_id=None, name="Banking Terms", difficulty_level="easy"),
            Topic(subject_id=None, name="RBI Functions", difficulty_level="medium"),
            Topic(subject_id=None, name="Seating Arrangements", difficulty_level="hard"),
        ]
        
        # CAT subjects and topics
        cat = exams[5]
        cat_subjects = [
            Subject(exam_id=cat.id, name="Verbal Ability", description="Reading Comprehension and Vocabulary"),
            Subject(exam_id=cat.id, name="Data Interpretation", description="Data Analysis and Logical Reasoning"),
            Subject(exam_id=cat.id, name="Quantitative Ability", description="Mathematics and Problem Solving"),
        ]
        all_subjects.extend(cat_subjects)
        
        cat_topics = [
            Topic(subject_id=None, name="Para Jumbles", difficulty_level="medium"),
            Topic(subject_id=None, name="Data Sufficiency", difficulty_level="hard"),
            Topic(subject_id=None, name="Percentages", difficulty_level="easy"),
        ]
        
        # CBSE Class 10 subjects and topics
        cbse10 = exams[6]
        cbse10_subjects = [
            Subject(exam_id=cbse10.id, name="Mathematics", description="Algebra, Geometry, Trigonometry, Statistics"),
            Subject(exam_id=cbse10.id, name="Science", description="Physics, Chemistry, Biology"),
            Subject(exam_id=cbse10.id, name="Social Science", description="History, Geography, Civics, Economics"),
            Subject(exam_id=cbse10.id, name="English", description="Literature and Grammar"),
        ]
        all_subjects.extend(cbse10_subjects)
        
        cbse10_topics = [
            Topic(subject_id=None, name="Real Numbers", difficulty_level="easy"),
            Topic(subject_id=None, name="Linear Equations", difficulty_level="medium"),
            Topic(subject_id=None, name="Light Reflection and Refraction", difficulty_level="medium"),
            Topic(subject_id=None, name="Chemical Reactions", difficulty_level="easy"),
        ]
        
        # CBSE Class 12 subjects and topics
        cbse12 = exams[7]
        cbse12_subjects = [
            Subject(exam_id=cbse12.id, name="Physics", description="Electrostatics, Optics, Modern Physics"),
            Subject(exam_id=cbse12.id, name="Chemistry", description="Solutions, Electrochemistry, Polymers"),
            Subject(exam_id=cbse12.id, name="Mathematics", description="Calculus, Vectors, Probability"),
            Subject(exam_id=cbse12.id, name="Biology", description="Reproduction, Genetics, Ecology"),
        ]
        all_subjects.extend(cbse12_subjects)
        
        cbse12_topics = [
            Topic(subject_id=None, name="Electric Charges and Fields", difficulty_level="medium"),
            Topic(subject_id=None, name="Solutions", difficulty_level="easy"),
            Topic(subject_id=None, name="Continuity and Differentiability", difficulty_level="hard"),
        ]
        
        # Add all subjects to database
        for subject in all_subjects:
            db.add(subject)
        await db.commit()
        
        # Refresh subjects to get IDs
        for subject in all_subjects:
            await db.refresh(subject)
        
        print(f"✅ Created {len(all_subjects)} subjects across all exams")
        
        # Assign topics to subjects and add to database
        topic_index = 0
        
        # Assign JEE topics
        for i in range(6):  # Physics topics
            jee_topics[topic_index].subject_id = jee_subjects[0].id
            topic_index += 1
        for i in range(4):  # Chemistry topics
            jee_topics[topic_index].subject_id = jee_subjects[1].id
            topic_index += 1
        for i in range(5):  # Mathematics topics
            jee_topics[topic_index].subject_id = jee_subjects[2].id
            topic_index += 1
        
        # Assign NEET topics
        neet_topic_index = 0
        for i in range(5):  # Biology topics
            neet_topics[neet_topic_index].subject_id = neet_subjects[2].id
            neet_topic_index += 1
        neet_topics[5].subject_id = neet_subjects[1].id  # Chemistry
        
        # Assign UPSC topics
        upsc_topic_index = 0
        for i in range(5):  # Geography
            upsc_topics[upsc_topic_index].subject_id = upsc_subjects[0].id
            upsc_topic_index += 1
        for i in range(4):  # History
            upsc_topics[upsc_topic_index].subject_id = upsc_subjects[1].id
            upsc_topic_index += 1
        for i in range(4):  # Polity
            upsc_topics[upsc_topic_index].subject_id = upsc_subjects[2].id
            upsc_topic_index += 1
        for i in range(3):  # Economy
            upsc_topics[upsc_topic_index].subject_id = upsc_subjects[3].id
            upsc_topic_index += 1
        
        # Assign SSC topics
        ssc_topics[0].subject_id = ssc_subjects[0].id
        ssc_topics[1].subject_id = ssc_subjects[0].id
        ssc_topics[2].subject_id = ssc_subjects[2].id
        ssc_topics[3].subject_id = ssc_subjects[3].id
        
        # Assign IBPS topics
        ibps_topics[0].subject_id = ibps_subjects[3].id
        ibps_topics[1].subject_id = ibps_subjects[3].id
        ibps_topics[2].subject_id = ibps_subjects[0].id
        
        # Assign CAT topics
        cat_topics[0].subject_id = cat_subjects[0].id
        cat_topics[1].subject_id = cat_subjects[1].id
        cat_topics[2].subject_id = cat_subjects[2].id
        
        # Assign CBSE 10 topics
        cbse10_topics[0].subject_id = cbse10_subjects[0].id
        cbse10_topics[1].subject_id = cbse10_subjects[0].id
        cbse10_topics[2].subject_id = cbse10_subjects[1].id
        cbse10_topics[3].subject_id = cbse10_subjects[1].id
        
        # Assign CBSE 12 topics
        cbse12_topics[0].subject_id = cbse12_subjects[0].id
        cbse12_topics[1].subject_id = cbse12_subjects[1].id
        cbse12_topics[2].subject_id = cbse12_subjects[2].id
        
        # Combine all topics
        all_topics = jee_topics + neet_topics + upsc_topics + ssc_topics + ibps_topics + cat_topics + cbse10_topics + cbse12_topics
        
        for topic in all_topics:
            db.add(topic)
        await db.commit()
        
        for topic in all_topics:
            await db.refresh(topic)
        
        print(f"✅ Created {len(all_topics)} topics across all subjects")
        
        # Create sample questions for first Geography topic only (to keep seed fast)
        geo_topic = upsc_topics[0]  # Physical Geography of India
        questions = [
            Question(
                topic_id=geo_topic.id,
                question_text="Which mountain range separates India from the Tibetan Plateau?",
                options={"A": "Aravalli", "B": "Himalayas", "C": "Western Ghats", "D": "Vindhyas"},
                correct_answer="B",
                explanation="The Himalayas form a natural barrier between India and the Tibetan Plateau.",
                source="PREVIOUS",
                year=2020,
                difficulty="easy",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="The Deccan Plateau is bounded by which mountain ranges on its western and eastern sides?",
                options={"A": "Himalayas and Aravalli", "B": "Western Ghats and Eastern Ghats", "C": "Vindhyas and Satpura", "D": "Nilgiris and Cardamom Hills"},
                correct_answer="B",
                explanation="The Deccan Plateau is bounded by the Western Ghats in the west and Eastern Ghats in the east.",
                source="PREVIOUS",
                year=2019,
                difficulty="medium",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="Which is the highest peak in peninsular India?",
                options={"A": "Anai Mudi", "B": "Dodda Betta", "C": "Mahendragiri", "D": "Kalsubai"},
                correct_answer="A",
                explanation="Anai Mudi in Kerala at 2,695m is the highest peak in peninsular India.",
                source="PREVIOUS",
                year=2021,
                difficulty="medium",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="The Northern Plains of India are formed by which type of landform?",
                options={"A": "Volcanic plateau", "B": "Alluvial deposits", "C": "Fold mountains", "D": "Block mountains"},
                correct_answer="B",
                explanation="The Northern Plains are formed by alluvial deposits brought by rivers like Ganga, Brahmaputra, and Indus.",
                source="PREVIOUS",
                year=2018,
                difficulty="easy",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="Which of the following is NOT a physiographic division of India?",
                options={"A": "The Northern Mountains", "B": "The Thar Desert", "C": "The Peninsular Plateau", "D": "The Coastal Plains"},
                correct_answer="B",
                explanation="The Thar Desert is part of the Great Indian Desert, not a separate physiographic division. The main divisions are Northern Mountains, Northern Plains, Peninsular Plateau, Coastal Plains, and Islands.",
                source="AI",
                difficulty="hard",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="The Shivalik range is part of which mountain system?",
                options={"A": "Greater Himalayas", "B": "Lesser Himalayas", "C": "Outer Himalayas", "D": "Trans Himalayas"},
                correct_answer="C",
                explanation="The Shivalik range is the outermost range of the Himalayas, also known as the Outer Himalayas.",
                source="PREVIOUS",
                year=2022,
                difficulty="medium",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="Which plateau in India is known as the 'Mineral heartland'?",
                options={"A": "Deccan Plateau", "B": "Chota Nagpur Plateau", "C": "Malwa Plateau", "D": "Meghalaya Plateau"},
                correct_answer="B",
                explanation="The Chota Nagpur Plateau is rich in mineral resources like coal, iron ore, and mica, earning it the title of India's mineral heartland.",
                source="AI",
                difficulty="medium",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="The Western Ghats and the Eastern Ghats meet at which hills?",
                options={"A": "Nilgiri Hills", "B": "Cardamom Hills", "C": "Palani Hills", "D": "Anamalai Hills"},
                correct_answer="A",
                explanation="The Western and Eastern Ghats meet at the Nilgiri Hills in Tamil Nadu.",
                source="PREVIOUS",
                year=2017,
                difficulty="medium",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="The Brahmaputra river originates from which region?",
                options={"A": "Nepal", "B": "Tibet", "C": "Bhutan", "D": "Arunachal Pradesh"},
                correct_answer="B",
                explanation="The Brahmaputra originates from the Angsi Glacier in Tibet, near Mount Kailash.",
                source="PREVIOUS",
                year=2020,
                difficulty="easy",
                is_validated=True
            ),
            Question(
                topic_id=geo_topic.id,
                question_text="Which island group of India is of volcanic origin?",
                options={"A": "Lakshadweep", "B": "Andaman & Nicobar", "C": "Both A and B", "D": "Neither A nor B"},
                correct_answer="B",
                explanation="The Andaman & Nicobar Islands are of volcanic origin, while Lakshadweep is of coral origin.",
                source="AI",
                difficulty="medium",
                is_validated=True
            ),
        ]
        
        for question in questions:
            db.add(question)
        await db.commit()
        
        print(f"✅ Created {len(questions)} sample questions")
        
        # Create a test user targeting JEE Main
        test_user = User(
            email="test@studypulse.com",
            name="Test User",
            hashed_password=get_password_hash("password123"),
            target_exam_id=jee.id,
            total_stars=3
        )
        db.add(test_user)
        await db.commit()
        
        print("✅ Created test user (email: test@studypulse.com, password: password123)")
        
        print("\n🎉 Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"  - {len(exams)} Exams: JEE Main, NEET, UPSC, SSC CGL, IBPS PO, CAT, CBSE 10/12")
        print(f"  - {len(all_subjects)} Subjects across all exams")
        print(f"  - {len(all_topics)} Topics")
        print(f"  - {len(questions)} Sample questions for UPSC Geography")
        print("\nYou can now:")
        print("  1. Run the API: uvicorn app.main:app --reload")
        print("  2. Visit docs: http://localhost:8000/docs")
        print("  3. Login with: test@studypulse.com / password123")


if __name__ == "__main__":
    asyncio.run(seed_data())
