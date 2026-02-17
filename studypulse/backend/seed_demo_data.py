"""Seed demo data for Railway deployment - comprehensive exam data."""
import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Exam, Subject, Topic, Question

logger = logging.getLogger(__name__)


async def seed_demo_data():
    """Seed comprehensive demo data into the database."""
    logger.info("=" * 80)
    logger.info("STARTING DATABASE SEEDING")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            result = await session.execute(select(Exam))
            existing_exams = result.scalars().all()

            if existing_exams:
                logger.info(f"Database already has {len(existing_exams)} exams. Skipping seed.")
                return

            logger.info("Database is empty. Starting seeding process...")

            # ========== EXAM 1: UPSC Civil Services ==========
            logger.info("Creating UPSC Civil Services exam...")
            upsc_exam = Exam(
                name="UPSC Civil Services",
                description="Union Public Service Commission Civil Services Examination",
                category="Government",
                conducting_body="UPSC",
                exam_duration_mins=180,
                total_questions=100,
                is_active=True
            )
            session.add(upsc_exam)
            await session.flush()

            # UPSC Subject: General Studies
            logger.info("  Creating General Studies subject...")
            gs_subject = Subject(
                exam_id=upsc_exam.id,
                name="General Studies",
                description="Covers History, Geography, Polity, Economy, Environment",
                is_active=True
            )
            session.add(gs_subject)
            await session.flush()

            # Topics for General Studies
            logger.info("    Creating topics for General Studies...")
            history_topic = Topic(
                subject_id=gs_subject.id,
                name="Indian History",
                description="Ancient, Medieval and Modern Indian History",
                difficulty_level="medium",
                estimated_study_mins=120,
                is_active=True
            )
            geography_topic = Topic(
                subject_id=gs_subject.id,
                name="Indian Geography",
                description="Physical, Economic and Social Geography of India",
                difficulty_level="medium",
                estimated_study_mins=100,
                is_active=True
            )
            polity_topic = Topic(
                subject_id=gs_subject.id,
                name="Indian Polity",
                description="Constitution, Political System, Panchayati Raj, Public Policy",
                difficulty_level="hard",
                estimated_study_mins=150,
                is_active=True
            )
            session.add_all([history_topic, geography_topic, polity_topic])
            await session.flush()

            # Questions for Indian History
            logger.info("      Creating questions for Indian History...")
            history_q1 = Question(
                topic_id=history_topic.id,
                question_text="Who was the first Mughal Emperor of India?",
                options={
                    "A": "Humayun",
                    "B": "Babur",
                    "C": "Akbar",
                    "D": "Shah Jahan"
                },
                correct_answer="B",
                explanation="Babur founded the Mughal Empire in India in 1526 after defeating Ibrahim Lodi at the Battle of Panipat.",
                source="PREVIOUS",
                year=2022,
                difficulty="easy",
                is_validated=True,
                is_active=True
            )

            history_q2 = Question(
                topic_id=history_topic.id,
                question_text="The Quit India Movement was launched in which year?",
                options={
                    "A": "1940",
                    "B": "1942",
                    "C": "1945",
                    "D": "1947"
                },
                correct_answer="B",
                explanation="The Quit India Movement was launched by Mahatma Gandhi on August 8, 1942, demanding an end to British rule in India.",
                source="PREVIOUS",
                year=2021,
                difficulty="medium",
                is_validated=True,
                is_active=True
            )

            # Questions for Indian Geography
            logger.info("      Creating questions for Indian Geography...")
            geo_q1 = Question(
                topic_id=geography_topic.id,
                question_text="Which is the longest river in India?",
                options={
                    "A": "Yamuna",
                    "B": "Godavari",
                    "C": "Ganges",
                    "D": "Brahmaputra"
                },
                correct_answer="C",
                explanation="The Ganges is the longest river in India, flowing approximately 2,525 km from the Himalayas to the Bay of Bengal.",
                source="PREVIOUS",
                year=2023,
                difficulty="easy",
                is_validated=True,
                is_active=True
            )

            geo_q2 = Question(
                topic_id=geography_topic.id,
                question_text="The Western Ghats run parallel to which coast?",
                options={
                    "A": "Eastern Coast",
                    "B": "Western Coast",
                    "C": "Northern Coast",
                    "D": "Southern Coast"
                },
                correct_answer="B",
                explanation="The Western Ghats, also known as Sahyadri, run parallel to the western coast of the Indian peninsula.",
                source="PREVIOUS",
                year=2022,
                difficulty="easy",
                is_validated=True,
                is_active=True
            )

            # Questions for Indian Polity
            logger.info("      Creating questions for Indian Polity...")
            polity_q1 = Question(
                topic_id=polity_topic.id,
                question_text="Which article of the Indian Constitution deals with Right to Equality?",
                options={
                    "A": "Article 12",
                    "B": "Article 14",
                    "C": "Article 19",
                    "D": "Article 21"
                },
                correct_answer="B",
                explanation="Article 14 of the Indian Constitution provides for equality before law and equal protection of laws within the territory of India.",
                source="PREVIOUS",
                year=2023,
                difficulty="medium",
                is_validated=True,
                is_active=True
            )

            polity_q2 = Question(
                topic_id=polity_topic.id,
                question_text="The President of India is elected by which method?",
                options={
                    "A": "Direct election by people",
                    "B": "Indirect election by Electoral College",
                    "C": "Nomination by Prime Minister",
                    "D": "Selection by Parliament"
                },
                correct_answer="B",
                explanation="The President of India is elected indirectly by an Electoral College consisting of elected members of both Houses of Parliament and elected members of the Legislative Assemblies of States.",
                source="PREVIOUS",
                year=2021,
                difficulty="hard",
                is_validated=True,
                is_active=True
            )

            session.add_all([history_q1, history_q2, geo_q1, geo_q2, polity_q1, polity_q2])

            # ========== EXAM 2: SSC CGL ==========
            logger.info("Creating SSC CGL exam...")
            ssc_exam = Exam(
                name="SSC CGL",
                description="Staff Selection Commission Combined Graduate Level Examination",
                category="Government",
                conducting_body="Staff Selection Commission",
                exam_duration_mins=120,
                total_questions=100,
                is_active=True
            )
            session.add(ssc_exam)
            await session.flush()

            # SSC Subject: Quantitative Aptitude
            logger.info("  Creating Quantitative Aptitude subject...")
            quant_subject = Subject(
                exam_id=ssc_exam.id,
                name="Quantitative Aptitude",
                description="Mathematics for competitive exams",
                is_active=True
            )
            session.add(quant_subject)
            await session.flush()

            # Topics for Quantitative Aptitude
            logger.info("    Creating topics for Quantitative Aptitude...")
            arithmetic_topic = Topic(
                subject_id=quant_subject.id,
                name="Arithmetic",
                description="Percentages, Profit & Loss, Simple & Compound Interest",
                difficulty_level="medium",
                estimated_study_mins=90,
                is_active=True
            )
            session.add(arithmetic_topic)
            await session.flush()

            # Questions for Arithmetic
            logger.info("      Creating questions for Arithmetic...")
            arith_q1 = Question(
                topic_id=arithmetic_topic.id,
                question_text="If 20% of a number is 40, what is the number?",
                options={
                    "A": "100",
                    "B": "150",
                    "C": "200",
                    "D": "250"
                },
                correct_answer="C",
                explanation="Let the number be x. Then 20% of x = 40, which means 0.2x = 40, so x = 40/0.2 = 200.",
                source="PREVIOUS",
                year=2023,
                difficulty="easy",
                is_validated=True,
                is_active=True
            )

            arith_q2 = Question(
                topic_id=arithmetic_topic.id,
                question_text="A shopkeeper marks his goods 40% above cost price but allows 20% discount. What is his profit percentage?",
                options={
                    "A": "8%",
                    "B": "10%",
                    "C": "12%",
                    "D": "15%"
                },
                correct_answer="C",
                explanation="Let CP = 100. MP = 140 (40% above CP). After 20% discount, SP = 140 × 0.8 = 112. Profit% = (112-100)/100 × 100 = 12%.",
                source="PREVIOUS",
                year=2022,
                difficulty="medium",
                is_validated=True,
                is_active=True
            )

            session.add_all([arith_q1, arith_q2])

            # ========== EXAM 3: JEE Main ==========
            logger.info("Creating JEE Main exam...")
            jee_exam = Exam(
                name="JEE Main",
                description="Joint Entrance Examination for Engineering",
                category="Engineering",
                conducting_body="NTA",
                exam_duration_mins=180,
                total_questions=75,
                is_active=True
            )
            session.add(jee_exam)
            await session.flush()

            # JEE Subject: Physics
            logger.info("  Creating Physics subject...")
            physics_subject = Subject(
                exam_id=jee_exam.id,
                name="Physics",
                description="Physics for JEE Main",
                is_active=True
            )
            session.add(physics_subject)
            await session.flush()

            # Topics for Physics
            logger.info("    Creating topics for Physics...")
            mechanics_topic = Topic(
                subject_id=physics_subject.id,
                name="Mechanics",
                description="Laws of Motion, Work Energy Power",
                difficulty_level="hard",
                estimated_study_mins=150,
                is_active=True
            )
            session.add(mechanics_topic)
            await session.flush()

            # Questions for Mechanics
            logger.info("      Creating questions for Mechanics...")
            mech_q1 = Question(
                topic_id=mechanics_topic.id,
                question_text="What is the SI unit of force?",
                options={
                    "A": "Joule",
                    "B": "Newton",
                    "C": "Watt",
                    "D": "Pascal"
                },
                correct_answer="B",
                explanation="The SI unit of force is Newton (N), named after Isaac Newton. 1 Newton = 1 kg⋅m/s².",
                source="PREVIOUS",
                year=2023,
                difficulty="easy",
                is_validated=True,
                is_active=True
            )

            mech_q2 = Question(
                topic_id=mechanics_topic.id,
                question_text="A body of mass 5 kg is accelerating at 2 m/s². What is the net force acting on it?",
                options={
                    "A": "7 N",
                    "B": "10 N",
                    "C": "3 N",
                    "D": "2.5 N"
                },
                correct_answer="B",
                explanation="Using Newton's second law F = ma, where m = 5 kg and a = 2 m/s². Therefore, F = 5 × 2 = 10 N.",
                source="PREVIOUS",
                year=2022,
                difficulty="medium",
                is_validated=True,
                is_active=True
            )

            session.add_all([mech_q1, mech_q2])

            # Commit all changes
            await session.commit()

            logger.info("=" * 80)
            logger.info("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info("Summary:")
            logger.info(f"  - Created 3 exams: UPSC Civil Services, SSC CGL, JEE Main")
            logger.info(f"  - Created 4 subjects")
            logger.info(f"  - Created 5 topics")
            logger.info(f"  - Created 12 questions (PREVIOUS year questions)")
            logger.info("=" * 80)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding database: {str(e)}")
            raise


async def main():
    """Main function for running seed script directly."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())
