"""
Comprehensive seed script with realistic mock data for all features.
Includes: Users, Study Sessions, Mock Tests, Rankings, Profile Stats, Real Questions
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal, init_db
from app.models.exam import Exam, Subject, Topic
from app.models.question import Question
from app.models.user import User
from app.models.mock_test import StudySession, MockTest
from app.core.security import get_password_hash

# Real questions sourced from public domains
REAL_QUESTIONS = {
    "UPSC": {
        "Polity": [
            {
                "text": "Which Article of the Constitution deals with the election of the President?",
                "options": ["Article 52", "Article 54", "Article 56", "Article 58"],
                "correct": 1,
                "explanation": "Article 54 deals with the election of the President by an electoral college."
            },
            {
                "text": "The concept of 'Basic Structure' was established in which case?",
                "options": ["Golaknath Case", "Kesavananda Bharati Case", "Minerva Mills Case", "Maneka Gandhi Case"],
                "correct": 1,
                "explanation": "Kesavananda Bharati v. State of Kerala (1973) established the basic structure doctrine."
            },
            {
                "text": "Who appoints the Chief Election Commissioner?",
                "options": ["Prime Minister", "President", "Parliament", "Supreme Court"],
                "correct": 1,
                "explanation": "The President appoints the Chief Election Commissioner."
            },
            {
                "text": "Which Part of the Constitution deals with Directive Principles?",
                "options": ["Part II", "Part III", "Part IV", "Part V"],
                "correct": 2,
                "explanation": "Part IV of the Constitution contains Directive Principles of State Policy."
            },
            {
                "text": "How many members can be nominated to Rajya Sabha by the President?",
                "options": ["10", "12", "14", "15"],
                "correct": 1,
                "explanation": "The President can nominate 12 members to the Rajya Sabha."
            }
        ],
        "History": [
            {
                "text": "The Quit India Movement was launched in which year?",
                "options": ["1940", "1942", "1944", "1946"],
                "correct": 1,
                "explanation": "The Quit India Movement was launched on 8 August 1942."
            },
            {
                "text": "Who founded the Indian National Congress?",
                "options": ["A.O. Hume", "Dadabhai Naoroji", "Bal Gangadhar Tilak", "Gopal Krishna Gokhale"],
                "correct": 0,
                "explanation": "A.O. Hume founded the Indian National Congress in 1885."
            },
            {
                "text": "The Battle of Plassey was fought in which year?",
                "options": ["1757", "1764", "1857", "1885"],
                "correct": 0,
                "explanation": "The Battle of Plassey was fought in 1757 between British and Siraj-ud-Daulah."
            },
            {
                "text": "Who was the first Governor-General of independent India?",
                "options": ["Lord Mountbatten", "C. Rajagopalachari", "Warren Hastings", "Lord Curzon"],
                "correct": 0,
                "explanation": "Lord Mountbatten was the first Governor-General of independent India."
            },
            {
                "text": "The Non-Cooperation Movement was withdrawn after which incident?",
                "options": ["Jallianwala Bagh", "Chauri Chaura", "Dandi March", "Partition of Bengal"],
                "correct": 1,
                "explanation": "The Non-Cooperation Movement was withdrawn after the Chauri Chaura incident in 1922."
            }
        ],
        "Geography": [
            {
                "text": "Which river is known as the 'Sorrow of Bihar'?",
                "options": ["Gandak", "Kosi", "Ganga", "Son"],
                "correct": 1,
                "explanation": "The Kosi River is called the 'Sorrow of Bihar' due to frequent floods."
            },
            {
                "text": "The Tropic of Cancer passes through how many Indian states?",
                "options": ["6", "7", "8", "9"],
                "correct": 2,
                "explanation": "The Tropic of Cancer passes through 8 Indian states."
            },
            {
                "text": "Which is the highest peak in India?",
                "options": ["Kanchenjunga", "Nanda Devi", "Mount Everest", "K2"],
                "correct": 0,
                "explanation": "Kanchenjunga is the highest peak completely within India."
            },
            {
                "text": "The Sundarbans mangrove forest is located in which state?",
                "options": ["Odisha", "West Bengal", "Andhra Pradesh", "Kerala"],
                "correct": 1,
                "explanation": "The Sundarbans is located in West Bengal and Bangladesh."
            },
            {
                "text": "Which soil is most suitable for cotton cultivation?",
                "options": ["Alluvial", "Black", "Red", "Laterite"],
                "correct": 1,
                "explanation": "Black soil (regur) is most suitable for cotton cultivation."
            }
        ]
    },
    "NEET": {
        "Physics": [
            {
                "text": "The SI unit of electric field intensity is:",
                "options": ["N/C", "C/N", "J/C", "V/m"],
                "correct": 0,
                "explanation": "Electric field intensity is measured in Newton per Coulomb (N/C) or Volt per meter (V/m)."
            },
            {
                "text": "The dimension of Planck's constant is:",
                "options": ["[ML²T⁻¹]", "[ML²T⁻²]", "[MLT⁻¹]", "[ML²T⁻³]"],
                "correct": 0,
                "explanation": "Planck's constant has dimension [ML²T⁻¹] (energy × time)."
            },
            {
                "text": "For a simple pendulum, the time period is independent of:",
                "options": ["Length", "Mass", "Gravity", "Amplitude (small)"],
                "correct": 1,
                "explanation": "Time period of simple pendulum is independent of mass of the bob."
            },
            {
                "text": "The refractive index of water is 4/3. The speed of light in water is:",
                "options": ["2.25 × 10⁸ m/s", "3 × 10⁸ m/s", "4 × 10⁸ m/s", "1.5 × 10⁸ m/s"],
                "correct": 0,
                "explanation": "Speed = c/n = (3×10⁸)/(4/3) = 2.25×10⁸ m/s"
            },
            {
                "text": "A body is thrown vertically upward. At the highest point:",
                "options": ["v=0, a=0", "v=0, a=g", "v≠0, a=0", "v≠0, a=g"],
                "correct": 1,
                "explanation": "At highest point, velocity is zero but acceleration is g (downward)."
            }
        ],
        "Chemistry": [
            {
                "text": "The pH of pure water at 25°C is:",
                "options": ["6", "7", "8", "7.4"],
                "correct": 1,
                "explanation": "Pure water has a pH of 7 at 25°C, indicating neutrality."
            },
            {
                "text": "Which of the following is a Lewis base?",
                "options": ["NH₃", "BF₃", "AlCl₃", "FeCl₃"],
                "correct": 0,
                "explanation": "NH₃ (ammonia) is a Lewis base as it can donate electron pairs."
            },
            {
                "text": "The IUPAC name of CH₃-CH(CH₃)-CH₂-CH₃ is:",
                "options": ["2-Methylbutane", "3-Methylbutane", "Isopentane", "n-Pentane"],
                "correct": 0,
                "explanation": "The compound is 2-Methylbutane (also called isopentane)."
            },
            {
                "text": "Oxidation state of Cr in K₂Cr₂O₇ is:",
                "options": ["+3", "+4", "+6", "+7"],
                "correct": 2,
                "explanation": "In K₂Cr₂O₇, chromium has oxidation state of +6."
            },
            {
                "text": "Which gas is evolved when sodium reacts with water?",
                "options": ["O₂", "H₂", "N₂", "Cl₂"],
                "correct": 1,
                "explanation": "Hydrogen gas is evolved when sodium reacts with water: 2Na + 2H₂O → 2NaOH + H₂"
            }
        ],
        "Biology": [
            {
                "text": "The powerhouse of the cell is:",
                "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi Body"],
                "correct": 1,
                "explanation": "Mitochondria are called the powerhouse as they produce ATP."
            },
            {
                "text": "DNA replication occurs in which phase?",
                "options": ["G1 phase", "S phase", "G2 phase", "M phase"],
                "correct": 1,
                "explanation": "DNA replication occurs during the S (synthesis) phase of the cell cycle."
            },
            {
                "text": "The functional unit of kidney is:",
                "options": ["Neuron", "Nephron", "Alveoli", "Villi"],
                "correct": 1,
                "explanation": "Nephron is the basic functional and structural unit of the kidney."
            },
            {
                "text": "Which blood group is called universal donor?",
                "options": ["A", "B", "AB", "O"],
                "correct": 3,
                "explanation": "Blood group O negative is the universal donor."
            },
            {
                "text": "Photosynthesis occurs in which part of the cell?",
                "options": ["Mitochondria", "Chloroplast", "Nucleus", "Ribosome"],
                "correct": 1,
                "explanation": "Photosynthesis occurs in chloroplasts containing chlorophyll."
            }
        ]
    },
    "JEE": {
        "Mathematics": [
            {
                "text": "The derivative of sin(x²) is:",
                "options": ["cos(x²)", "2x cos(x²)", "-sin(x²)", "2x sin(x²)"],
                "correct": 1,
                "explanation": "Using chain rule: d/dx[sin(x²)] = cos(x²) · 2x"
            },
            {
                "text": "If A and B are square matrices of same order, then (AB)ᵀ equals:",
                "options": ["AᵀBᵀ", "BᵀAᵀ", "ABᵀ", "AᵀB"],
                "correct": 1,
                "explanation": "Transpose of product is the product of transposes in reverse order: (AB)ᵀ = BᵀAᵀ"
            },
            {
                "text": "The sum of first n natural numbers is:",
                "options": ["n(n+1)", "n(n+1)/2", "n²", "n(n-1)/2"],
                "correct": 1,
                "explanation": "Sum = 1+2+3+...+n = n(n+1)/2"
            },
            {
                "text": "The value of ∫₀^π sin(x)dx is:",
                "options": ["0", "1", "2", "π"],
                "correct": 2,
                "explanation": "∫₀^π sin(x)dx = [-cos(x)]₀^π = -(-1-1) = 2"
            },
            {
                "text": "The distance between points (x₁,y₁) and (x₂,y₂) is:",
                "options": ["√[(x₂-x₁)²+(y₂-y₁)²]", "(x₂-x₁)²+(y₂-y₁)²", "|x₂-x₁|+|y₂-y₁|", "√(x₂²+y₂²)"],
                "correct": 0,
                "explanation": "Distance formula: d = √[(x₂-x₁)²+(y₂-y₁)²]"
            }
        ],
        "Physics": [
            {
                "text": "Newton's second law states that F equals:",
                "options": ["ma", "mv", "mv²", "m/a"],
                "correct": 0,
                "explanation": "Newton's second law: Force = mass × acceleration (F=ma)"
            },
            {
                "text": "The SI unit of work is:",
                "options": ["Watt", "Joule", "Newton", "Pascal"],
                "correct": 1,
                "explanation": "Work is measured in Joules (J) where 1 J = 1 N·m"
            },
            {
                "text": "Kepler's third law relates period to:",
                "options": ["Mass", "Velocity", "Radius³", "Radius²"],
                "correct": 2,
                "explanation": "Kepler's third law: T² ∝ r³"
            },
            {
                "text": "The capacitance of a parallel plate capacitor is:",
                "options": ["ε₀A/d", "ε₀d/A", "A/ε₀d", "ε₀Ad"],
                "correct": 0,
                "explanation": "Capacitance C = ε₀A/d where A is area and d is separation"
            },
            {
                "text": "Young's modulus has the same unit as:",
                "options": ["Force", "Stress", "Strain", "Energy"],
                "correct": 1,
                "explanation": "Young's modulus = Stress/Strain, so it has units of stress (Pa)"
            }
        ],
        "Chemistry": [
            {
                "text": "The electronic configuration of Fe²⁺ is:",
                "options": ["[Ar]3d⁶", "[Ar]3d⁴4s²", "[Ar]3d⁵4s¹", "[Ar]3d⁸"],
                "correct": 0,
                "explanation": "Fe (26): [Ar]3d⁶4s², Fe²⁺ loses 2 electrons from 4s: [Ar]3d⁶"
            },
            {
                "text": "Which is the strongest acid?",
                "options": ["HCl", "HF", "HBr", "HI"],
                "correct": 3,
                "explanation": "HI is the strongest acid among hydrogen halides."
            },
            {
                "text": "The hybridization of carbon in CH₄ is:",
                "options": ["sp", "sp²", "sp³", "sp³d"],
                "correct": 2,
                "explanation": "In methane (CH₄), carbon undergoes sp³ hybridization."
            },
            {
                "text": "Which reaction is endothermic?",
                "options": ["Combustion", "Respiration", "Photosynthesis", "Neutralization"],
                "correct": 2,
                "explanation": "Photosynthesis is endothermic as it requires energy (sunlight)."
            },
            {
                "text": "The shape of NH₃ molecule is:",
                "options": ["Linear", "Trigonal planar", "Tetrahedral", "Trigonal pyramidal"],
                "correct": 3,
                "explanation": "NH₃ has trigonal pyramidal shape due to lone pair on nitrogen."
            }
        ]
    },
    "CAT": {
        "Quantitative": [
            {
                "text": "If the sum of three consecutive integers is 48, what is the largest integer?",
                "options": ["15", "16", "17", "18"],
                "correct": 2,
                "explanation": "Let integers be n, n+1, n+2. Then 3n+3=48, n=15. Largest is 17."
            },
            {
                "text": "A train 100m long passes a pole in 5 seconds. What is its speed in km/hr?",
                "options": ["20", "36", "50", "72"],
                "correct": 3,
                "explanation": "Speed = 100m/5s = 20 m/s = 20 × 18/5 = 72 km/hr"
            },
            {
                "text": "The average of 5 numbers is 20. If one number is excluded, average becomes 15. The excluded number is:",
                "options": ["35", "40", "45", "50"],
                "correct": 1,
                "explanation": "Sum of 5 = 100, Sum of 4 = 60. Excluded = 100-60 = 40"
            },
            {
                "text": "If 20% of a number is 40, what is 50% of that number?",
                "options": ["80", "100", "120", "140"],
                "correct": 1,
                "explanation": "20% = 40, so 100% = 200. Therefore 50% = 100"
            },
            {
                "text": "The ratio of ages of A and B is 3:4. After 5 years, ratio is 4:5. Present age of A is:",
                "options": ["15", "18", "20", "24"],
                "correct": 0,
                "explanation": "Let ages be 3x and 4x. Then (3x+5)/(4x+5) = 4/5. Solving: x=5, A=15"
            }
        ],
        "Verbal": [
            {
                "text": "Choose the antonym of 'Verbose':",
                "options": ["Talkative", "Concise", "Eloquent", "Loquacious"],
                "correct": 1,
                "explanation": "Verbose means wordy; Concise is the opposite meaning brief."
            },
            {
                "text": "Fill in the blank: The committee decided to _____ the meeting due to lack of quorum.",
                "options": ["adjourn", "abridge", "accelerate", "accomplish"],
                "correct": 0,
                "explanation": "Adjourn means to suspend or postpone a meeting."
            },
            {
                "text": "Choose the synonym of 'Pragmatic':",
                "options": ["Idealistic", "Practical", "Theoretical", "Abstract"],
                "correct": 1,
                "explanation": "Pragmatic means practical, dealing with things realistically."
            },
            {
                "text": "Identify the error: 'Neither of the students have submitted their assignments.'",
                "options": ["Neither", "have", "their", "No error"],
                "correct": 1,
                "explanation": "'Neither' is singular, so it should be 'has' not 'have'."
            },
            {
                "text": "Choose the correct idiom: To 'beat around the bush' means:",
                "options": ["To be direct", "To avoid main topic", "To hit someone", "To clear bushes"],
                "correct": 1,
                "explanation": "Beat around the bush means to avoid talking about the main point."
            }
        ],
        "Logical": [
            {
                "text": "If A>B, B>C, and C>D, which is true?",
                "options": ["A<D", "A=D", "A>D", "Cannot determine"],
                "correct": 2,
                "explanation": "By transitive property: A>B>C>D, therefore A>D"
            },
            {
                "text": "In a code, PUNE is written as SVQH. How is DELHI written?",
                "options": ["GHOKL", "GHOLM", "GHPML", "GHOLM"],
                "correct": 0,
                "explanation": "Each letter is shifted +3: D→G, E→H, L→O, H→K, I→L"
            },
            {
                "text": "Complete the series: 2, 6, 12, 20, 30, ?",
                "options": ["40", "42", "44", "46"],
                "correct": 1,
                "explanation": "Differences: 4,6,8,10,12. Next term = 30+12 = 42"
            },
            {
                "text": "If all roses are flowers and some flowers are red, then:",
                "options": ["All roses are red", "Some roses are red", "No roses are red", "Cannot conclude"],
                "correct": 3,
                "explanation": "We cannot conclude about roses being red from given statements."
            },
            {
                "text": "A is B's brother. C is B's mother. D is C's father. What is A to D?",
                "options": ["Grandson", "Son", "Nephew", "Brother"],
                "correct": 0,
                "explanation": "A is son of C (B's mother), so A is grandson of D."
            }
        ]
    }
}


async def create_users(db: AsyncSession):
    """Create test users with varying stats."""
    print("\nCreating users...")
    
    # Realistic users with specific exam focus and performance
    users_data = [
        # Rahul - UPSC aspirant, 75% avg, weak in Polity
        {"name": "Rahul Kumar", "email": "rahul@test.com", "stars": 95, "avg": 75, "exam": "UPSC", "weak_subject": "Polity"},
        # Top performers
        {"name": "Sneha Patel", "email": "sneha@test.com", "stars": 142, "avg": 88, "exam": "NEET", "weak_subject": None},
        {"name": "Vivek Sharma", "email": "vivek@test.com", "stars": 128, "avg": 82, "exam": "JEE", "weak_subject": None},
        # Mid-range performers
        {"name": "Lakshmi Reddy", "email": "lakshmi@test.com", "stars": 108, "avg": 78, "exam": "CAT", "weak_subject": None},
        {"name": "Pechu Singh", "email": "pechu@test.com", "stars": 87, "avg": 70, "exam": "UPSC", "weak_subject": None},
        # Lower performers
        {"name": "Shankar Rao", "email": "shankar@test.com", "stars": 72, "avg": 66, "exam": "NEET", "weak_subject": "Chemistry"},
        {"name": "Ramu Naidu", "email": "ramu@test.com", "stars": 58, "avg": 62, "exam": "JEE", "weak_subject": "Physics"},
        # Additional users for variety
        {"name": "Anjali Gupta", "email": "anjali@test.com", "stars": 115, "avg": 80, "exam": "CAT", "weak_subject": None},
        {"name": "Karthik Iyer", "email": "karthik@test.com", "stars": 98, "avg": 74, "exam": "UPSC", "weak_subject": "Geography"},
        {"name": "Divya Menon", "email": "divya@test.com", "stars": 82, "avg": 68, "exam": "NEET", "weak_subject": "Biology"},
    ]
    
    created_users = []
    for i, udata in enumerate(users_data):
        user = User(
            email=udata["email"],
            name=udata["name"],
            hashed_password=get_password_hash("test123"),
            total_stars=udata["stars"],
            total_sessions=0,
            total_tests=0
        )
        db.add(user)
        created_users.append(user)
    
    await db.commit()
    print(f"Created {len(created_users)} users")
    return created_users


async def create_exams_structure(db: AsyncSession):
    """Create comprehensive exam structure."""
    print("\nCreating exam structure...")
    
    # UPSC Exam
    upsc = Exam(
        name="UPSC Civil Services",
        description="Union Public Service Commission - Civil Services Examination",
        category="Government",
        conducting_body="UPSC",
        exam_duration_mins=180,
        total_questions=100
    )
    db.add(upsc)
    await db.flush()
    
    upsc_subjects = {
        "General Studies - Polity": ["Indian Constitution", "Political System", "Governance", "Social Justice", "International Relations"],
        "General Studies - History": ["Ancient India", "Medieval India", "Modern India", "Freedom Struggle", "World History"],
        "General Studies - Geography": ["Physical Geography", "Indian Geography", "World Geography", "Environment", "Disasters"],
        "General Studies - Economy": ["Indian Economy", "Economic Development", "Budget", "Banking", "Trade"],
    }
    
    # NEET Exam
    neet = Exam(
        name="NEET UG",
        description="National Eligibility cum Entrance Test - Undergraduate",
        category="Medical",
        conducting_body="NTA",
        exam_duration_mins=180,
        total_questions=180
    )
    db.add(neet)
    await db.flush()
    
    neet_subjects = {
        "Physics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Modern Physics"],
        "Chemistry": ["Physical Chemistry", "Organic Chemistry", "Inorganic Chemistry", "Environmental Chemistry"],
        "Biology": ["Cell Biology", "Genetics", "Ecology", "Human Physiology", "Plant Physiology"],
    }
    
    # JEE Main Exam
    jee = Exam(
        name="JEE Main",
        description="Joint Entrance Examination - Main for Engineering",
        category="Engineering",
        conducting_body="NTA",
        exam_duration_mins=180,
        total_questions=90
    )
    db.add(jee)
    await db.flush()
    
    jee_subjects = {
        "Mathematics": ["Algebra", "Calculus", "Coordinate Geometry", "Trigonometry", "Vectors & 3D"],
        "Physics": ["Mechanics", "Electrodynamics", "Thermodynamics", "Waves & Optics", "Modern Physics"],
        "Chemistry": ["Physical Chemistry", "Organic Chemistry", "Inorganic Chemistry"],
    }
    
    # CAT Exam
    cat = Exam(
        name="CAT",
        description="Common Admission Test for MBA",
        category="Management",
        conducting_body="IIMs",
        exam_duration_mins=120,
        total_questions=66
    )
    db.add(cat)
    await db.flush()
    
    cat_subjects = {
        "Quantitative Aptitude": ["Arithmetic", "Algebra", "Geometry", "Number System", "Modern Math"],
        "Verbal Ability": ["Reading Comprehension", "Para Jumbles", "Grammar", "Vocabulary", "Critical Reasoning"],
        "Logical Reasoning": ["Puzzles", "Arrangements", "Blood Relations", "Coding-Decoding", "Syllogisms"],
        "Data Interpretation": ["Tables", "Graphs", "Charts", "Caselets", "Data Sufficiency"],
    }
    
    exam_subject_map = {
        upsc: upsc_subjects,
        neet: neet_subjects,
        jee: jee_subjects,
        cat: cat_subjects
    }
    
    all_topics = []
    
    for exam, subjects_dict in exam_subject_map.items():
        for subject_name, topic_list in subjects_dict.items():
            subject = Subject(
                exam_id=exam.id,
                name=subject_name,
                description=f"{subject_name} for {exam.name}"
            )
            db.add(subject)
            await db.flush()
            
            for topic_name in topic_list:
                topic = Topic(
                    subject_id=subject.id,
                    name=topic_name,
                    description=f"Study {topic_name} for {subject_name}"
                )
                db.add(topic)
                all_topics.append((exam.name, subject_name, topic))
    
    await db.commit()
    print(f"Created 4 exams with {len(all_topics)} topics")
    return all_topics


async def create_questions(db: AsyncSession, topics_data):
    """Create real questions for each topic."""
    print("\nCreating questions...")
    
    question_count = 0
    
    for exam_name, subject_name, topic in topics_data:
        # Map to question sets
        question_set = []
        
        if "UPSC" in exam_name:
            if "Polity" in subject_name:
                question_set = REAL_QUESTIONS["UPSC"]["Polity"]
            elif "History" in subject_name:
                question_set = REAL_QUESTIONS["UPSC"]["History"]
            elif "Geography" in subject_name:
                question_set = REAL_QUESTIONS["UPSC"]["Geography"]
        
        elif "NEET" in exam_name:
            if "Physics" in subject_name:
                question_set = REAL_QUESTIONS["NEET"]["Physics"]
            elif "Chemistry" in subject_name:
                question_set = REAL_QUESTIONS["NEET"]["Chemistry"]
            elif "Biology" in subject_name:
                question_set = REAL_QUESTIONS["NEET"]["Biology"]
        
        elif "JEE" in exam_name:
            if "Mathematics" in subject_name:
                question_set = REAL_QUESTIONS["JEE"]["Mathematics"]
            elif "Physics" in subject_name:
                question_set = REAL_QUESTIONS["JEE"]["Physics"]
            elif "Chemistry" in subject_name:
                question_set = REAL_QUESTIONS["JEE"]["Chemistry"]
        
        elif "CAT" in exam_name:
            if "Quantitative" in subject_name:
                question_set = REAL_QUESTIONS["CAT"]["Quantitative"]
            elif "Verbal" in subject_name:
                question_set = REAL_QUESTIONS["CAT"]["Verbal"]
            elif "Logical" in subject_name or "Data" in subject_name:
                question_set = REAL_QUESTIONS["CAT"]["Logical"]
        
        # Create questions for this topic
        for q_data in question_set:
            # Convert options list to dict format and get correct letter
            options_dict = {
                "A": q_data["options"][0],
                "B": q_data["options"][1],
                "C": q_data["options"][2],
                "D": q_data["options"][3],
            }
            correct_letter = ["A", "B", "C", "D"][q_data["correct"]]
            
            question = Question(
                topic_id=topic.id,
                question_text=q_data["text"],
                options=options_dict,
                correct_answer=correct_letter,
                explanation=q_data["explanation"],
                difficulty="medium",
                source="PREVIOUS",
                year=random.choice([2022, 2023, 2024])
            )
            db.add(question)
            question_count += 1
        
        # Add some generic questions if set is empty
        if not question_set:
            for i in range(3):
                options_dict = {
                    "A": "Option A",
                    "B": "Option B",
                    "C": "Option C",
                    "D": "Option D",
                }
                question = Question(
                    topic_id=topic.id,
                    question_text=f"Sample question {i+1} for {topic.name}?",
                    options=options_dict,
                    correct_answer="A",
                    explanation=f"This is a sample question for {topic.name}.",
                    difficulty="medium",
                    source="AI"
                )
                db.add(question)
                question_count += 1
    
    await db.commit()
    print(f"Created {question_count} questions")


async def create_study_sessions(db: AsyncSession, users, topics_data):
    """Create study sessions for users."""
    print("\nCreating study sessions...")
    
    session_count = 0
    now = datetime.utcnow()
    
    for user in users[:5]:  # First 5 users
        for _ in range(random.randint(8, 15)):
            topic = random.choice(topics_data)[2]
            days_ago = random.randint(1, 30)
            duration = random.choice([15, 30, 45, 60])
            
            session = StudySession(
                user_id=user.id,
                topic_id=topic.id,
                duration_mins=duration,
                actual_duration_mins=duration + random.randint(-5, 10),
                started_at=now - timedelta(days=days_ago, hours=random.randint(0, 12)),
                ended_at=now - timedelta(days=days_ago, hours=random.randint(0, 12)) + timedelta(minutes=duration),
                completed=True,
                notes=f"Studied {topic.name}"
            )
            db.add(session)
            session_count += 1
    
    await db.commit()
    print(f"Created {session_count} study sessions")


async def create_mock_tests(db: AsyncSession, users, topics_data):
    """Create mock tests with results."""
    print("\nCreating mock tests...")
    
    test_count = 0
    now = datetime.utcnow()
    
    for user in users:
        # Create varying number of tests based on user rank
        test_range = (15, 25) if user.total_stars > 100 else (5, 15)
        
        for _ in range(random.randint(*test_range)):
            topic = random.choice(topics_data)[2]
            days_ago = random.randint(1, 45)
            
            # Score varies based on user's star count (proxy for skill)
            base_score = min(95, 60 + (user.total_stars / 2))
            score = max(0, min(100, base_score + random.randint(-15, 15)))
            
            # Get questions for this topic
            questions_result = await db.execute(
                select(Question).where(Question.topic_id == topic.id).limit(10)
            )
            questions = list(questions_result.scalars().all())
            
            if questions:
                total_qs = len(questions)
                correct = int((score / 100) * total_qs)
                
                mock_test = MockTest(
                    user_id=user.id,
                    topic_id=topic.id,
                    total_questions=total_qs,
                    correct_answers=correct,
                    score_percentage=score,
                    star_earned=score >= 85,
                    question_ids=[q.id for q in questions],
                    time_limit_seconds=total_qs * 90,  # 90 seconds per question
                    time_taken_seconds=random.randint(total_qs * 40, total_qs * 120),
                    status="completed",
                    started_at=now - timedelta(days=days_ago, hours=random.randint(0, 12)),
                    completed_at=now - timedelta(days=days_ago, hours=random.randint(0, 12)) + timedelta(minutes=total_qs * 2)
                )
                db.add(mock_test)
                test_count += 1
    
    await db.commit()
    print(f"Created {test_count} mock tests")


async def main():
    """Main seeding function."""
    print("COMPREHENSIVE DATA SEEDING")
    print("=" * 50)
    
    # Initialize DB
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Clear existing data
        print("\nClearing existing data...")
        await db.execute(delete(MockTest))
        await db.execute(delete(StudySession))
        await db.execute(delete(Question))
        await db.execute(delete(Topic))
        await db.execute(delete(Subject))
        await db.execute(delete(Exam))
        # Clear all users (we'll create new test ones)
        await db.execute(delete(User))
        await db.commit()
        print("Cleared old data")
        
        # Create all data
        users = await create_users(db)
        topics_data = await create_exams_structure(db)
        await create_questions(db, topics_data)
        await create_study_sessions(db, users, topics_data)
        await create_mock_tests(db, users, topics_data)
    
    print("\n" + "=" * 50)
    print("SEEDING COMPLETE!")
    print("\nSummary:")
    print("   - 10 test users created")
    print("   - 4 exams (UPSC, NEET, JEE, CAT)")
    print("   - 50+ topics across all exams")
    print("   - 100+ real questions")
    print("   - 50+ study sessions")
    print("   - 100+ mock tests with results")
    print("\nReady to test the complete app!")


if __name__ == "__main__":
    asyncio.run(main())
