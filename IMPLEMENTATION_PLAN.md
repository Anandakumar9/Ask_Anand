# 🛠️ Technical Implementation Plan
## StudyPulse - Step-by-Step Development Guide

---

## 📚 Table of Contents
1. [Prerequisites & Setup](#1-prerequisites--setup)
2. [Project Structure](#2-project-structure)
3. [Phase 1: Backend Development](#3-phase-1-backend-development)
4. [Phase 2: RAG & AI Integration](#4-phase-2-rag--ai-integration)
5. [Phase 3: Frontend Development](#5-phase-3-frontend-development)
6. [Phase 4: Integration & Testing](#6-phase-4-integration--testing)
7. [Deployment Guide](#7-deployment-guide)

---

## 1. Prerequisites & Setup

### 1.1 Tools You Need to Install

| Tool | Purpose | Download Link |
|------|---------|---------------|
| **Node.js (v18+)** | JavaScript runtime | https://nodejs.org |
| **Python (3.10+)** | Backend & AI | https://python.org |
| **VS Code** | Code editor | https://code.visualstudio.com |
| **Git** | Version control | https://git-scm.com |
| **Docker Desktop** | Containerization | https://docker.com |
| **PostgreSQL** | Database | https://postgresql.org |

### 1.2 VS Code Extensions (Recommended)
```
- Python (Microsoft)
- Pylance
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- GitLens
- Thunder Client (API testing)
- Docker
```

### 1.3 Accounts You Need
| Service | Purpose | Link |
|---------|---------|------|
| **OpenAI** | LLM for question generation | https://platform.openai.com |
| **GitHub** | Code repository | https://github.com |
| **Vercel** | Frontend hosting | https://vercel.com |
| **Railway/Render** | Backend hosting | https://railway.app |

---

## 2. Project Structure

### 2.1 Monorepo Structure
```
studypulse/
├── 📁 backend/                 # Python FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 api/            # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── exams.py       # Exam/Subject/Topic endpoints
│   │   │   ├── study.py       # Study session endpoints
│   │   │   ├── mock_test.py   # Mock test endpoints
│   │   │   └── dashboard.py   # Dashboard/Stats endpoints
│   │   ├── 📁 core/           # Core configurations
│   │   │   ├── config.py      # Environment variables
│   │   │   ├── database.py    # Database connection
│   │   │   └── security.py    # JWT, hashing
│   │   ├── 📁 models/         # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── exam.py
│   │   │   ├── question.py
│   │   │   └── mock_test.py
│   │   ├── 📁 schemas/        # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── exam.py
│   │   │   └── mock_test.py
│   │   ├── 📁 services/       # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── question_service.py
│   │   │   └── evaluation_service.py
│   │   ├── 📁 rag/            # RAG Implementation
│   │   │   ├── document_processor.py
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   └── question_generator.py
│   │   └── main.py            # FastAPI app entry
│   ├── 📁 data/               # Question bank data
│   │   ├── 📁 pdfs/           # Previous year papers
│   │   └── 📁 processed/      # Processed JSON
│   ├── 📁 tests/              # Unit tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── 📁 frontend/               # React/Next.js Frontend
│   ├── 📁 src/
│   │   ├── 📁 app/            # Next.js App Router
│   │   │   ├── page.tsx       # Landing page
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── 📁 auth/       # Auth pages
│   │   │   ├── 📁 study/      # Study pages
│   │   │   ├── 📁 test/       # Mock test pages
│   │   │   └── 📁 dashboard/  # Dashboard pages
│   │   ├── 📁 components/     # Reusable components
│   │   │   ├── 📁 ui/         # UI primitives
│   │   │   ├── 📁 forms/      # Form components
│   │   │   └── 📁 layout/     # Layout components
│   │   ├── 📁 hooks/          # Custom React hooks
│   │   ├── 📁 lib/            # Utilities
│   │   ├── 📁 services/       # API client
│   │   └── 📁 styles/         # CSS files
│   ├── package.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── 📁 docs/                   # Documentation
│   ├── PRD.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── API_DOCS.md
│
├── docker-compose.yml         # Local development
├── .gitignore
└── README.md
```

---

## 3. Phase 1: Backend Development

### 3.1 Step 1: Initialize Backend Project

```bash
# Create project directory
mkdir studypulse
cd studypulse
mkdir backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy asyncpg python-jose passlib bcrypt python-multipart pydantic-settings alembic
```

### 3.2 Step 2: Create requirements.txt

```txt
# Backend Dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic-settings==2.1.0
alembic==1.13.1
httpx==0.26.0

# RAG & AI Dependencies
openai==1.10.0
langchain==0.1.4
chromadb==0.4.22
sentence-transformers==2.3.1
pypdf==4.0.1
python-docx==1.1.0

# Utilities
python-dotenv==1.0.0
redis==5.0.1
celery==5.3.6
```

### 3.3 Step 3: Database Configuration

**File: `backend/app/core/config.py`**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "StudyPulse"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/studypulse"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # ChromaDB
    CHROMA_PERSIST_PATH: str = "./data/chroma"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**File: `backend/app/core/database.py`**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 3.4 Step 4: Create Database Models

**File: `backend/app/models/user.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    profile_pic = Column(String, nullable=True)
    target_exam_id = Column(Integer, nullable=True)
    total_stars = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    study_sessions = relationship("StudySession", back_populates="user")
    mock_tests = relationship("MockTest", back_populates="user")
```

**File: `backend/app/models/exam.py`**
```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "UPSC Civil Services"
    description = Column(Text)
    category = Column(String)  # e.g., "Government", "School", "Engineering"
    conducting_body = Column(String)  # e.g., "UPSC", "CBSE"
    exam_duration_mins = Column(Integer)
    total_questions = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    subjects = relationship("Subject", back_populates="exam")

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    name = Column(String, nullable=False)  # e.g., "Geology"
    description = Column(Text)
    syllabus_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    exam = relationship("Exam", back_populates="subjects")
    topics = relationship("Topic", back_populates="subject")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    name = Column(String, nullable=False)  # e.g., "History of Andhra Pradesh"
    description = Column(Text)
    difficulty_level = Column(String, default="medium")  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic")
```

**File: `backend/app/models/question.py`**
```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    question_text = Column(Text, nullable=False)
    options = Column(JSON)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String, nullable=False)  # "A", "B", "C", or "D"
    explanation = Column(Text)
    source = Column(String, default="PREVIOUS")  # "PREVIOUS" or "AI"
    year = Column(Integer, nullable=True)  # For previous year questions
    difficulty = Column(String, default="medium")
    avg_rating = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    is_validated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    topic = relationship("Topic", back_populates="questions")
```

**File: `backend/app/models/mock_test.py`**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    duration_mins = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    completed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="study_sessions")
    mock_test = relationship("MockTest", back_populates="study_session", uselist=False)

class MockTest(Base):
    __tablename__ = "mock_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    total_questions = Column(Integer)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0)
    star_earned = Column(Boolean, default=False)
    time_taken_seconds = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    question_ids = Column(JSON)  # List of question IDs used
    
    user = relationship("User", back_populates="mock_tests")
    study_session = relationship("StudySession", back_populates="mock_test")
    responses = relationship("QuestionResponse", back_populates="mock_test")

class QuestionResponse(Base):
    __tablename__ = "question_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    mock_test_id = Column(Integer, ForeignKey("mock_tests.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_answer = Column(String)  # "A", "B", "C", "D", or null
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    mock_test = relationship("MockTest", back_populates="responses")

class QuestionRating(Base):
    __tablename__ = "question_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.5 Step 5: Create API Endpoints

**File: `backend/app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, exams, study, mock_test, dashboard

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(exams.router, prefix="/api/v1/exams", tags=["Exams"])
app.include_router(study.router, prefix="/api/v1/study", tags=["Study Sessions"])
app.include_router(mock_test.router, prefix="/api/v1/mock-test", tags=["Mock Tests"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"message": "Welcome to StudyPulse API", "version": settings.API_VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**File: `backend/app/api/auth.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)
    user = await auth_service.create_user(user_data)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    auth_service = AuthService(db)
    token = await auth_service.authenticate(credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return token

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    return current_user
```

**File: `backend/app/api/mock_test.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.mock_test import (
    MockTestCreate, MockTestResponse, 
    SubmitAnswers, TestResult,
    QuestionDisplay
)
from app.services.question_service import QuestionService
from app.services.evaluation_service import EvaluationService
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/start", response_model=MockTestResponse)
async def start_mock_test(
    test_data: MockTestCreate,
    current_user = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new mock test for a specific topic.
    Returns test ID and questions.
    """
    question_service = QuestionService(db)
    
    # Get mixed questions (50% previous year, 50% AI)
    questions = await question_service.get_mixed_questions(
        topic_id=test_data.topic_id,
        total_questions=test_data.question_count,
        previous_year_ratio=0.5
    )
    
    # Create mock test record
    mock_test = await question_service.create_mock_test(
        user_id=current_user.id,
        topic_id=test_data.topic_id,
        session_id=test_data.session_id,
        questions=questions
    )
    
    return MockTestResponse(
        test_id=mock_test.id,
        questions=[QuestionDisplay.from_orm(q) for q in questions],
        total_questions=len(questions),
        time_limit_seconds=test_data.time_limit_seconds
    )

@router.post("/{test_id}/submit", response_model=TestResult)
async def submit_mock_test(
    test_id: int,
    answers: SubmitAnswers,
    current_user = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit answers for a mock test and get results.
    Awards star if score >= 85%.
    """
    evaluation_service = EvaluationService(db)
    
    result = await evaluation_service.evaluate_test(
        test_id=test_id,
        user_id=current_user.id,
        answers=answers.responses
    )
    
    return result

@router.post("/{test_id}/rate-question")
async def rate_question(
    test_id: int,
    question_id: int,
    rating: int,
    feedback: str = None,
    current_user = Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate an AI-generated question (1-5 stars)"""
    question_service = QuestionService(db)
    await question_service.rate_question(
        question_id=question_id,
        user_id=current_user.id,
        rating=rating,
        feedback=feedback
    )
    return {"message": "Rating submitted successfully"}
```

---

## 4. Phase 2: RAG & AI Integration

### 4.1 Understanding RAG (For Beginners)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WHAT IS RAG? (Simple Explanation)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  RAG = Retrieval Augmented Generation                                       │
│                                                                              │
│  Think of it like this:                                                      │
│                                                                              │
│  1. 📚 You have a HUGE library of books (previous year question papers)     │
│                                                                              │
│  2. 🔍 When someone asks a question, instead of reading ALL books,          │
│        you FIND the most relevant pages first                                │
│                                                                              │
│  3. 🤖 Then you give those relevant pages to an AI (like ChatGPT)           │
│        and ask it to answer based on those pages                             │
│                                                                              │
│  WHY USE RAG?                                                                │
│  • AI models don't know about YOUR specific question papers                  │
│  • RAG teaches them by showing relevant examples                             │
│  • This makes AI generate questions that MATCH the exam pattern              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Document Processing Pipeline

**File: `backend/app/rag/document_processor.py`**
```python
import os
from typing import List, Dict
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """Process PDF question papers and extract questions"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file"""
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def parse_questions_from_text(self, text: str) -> List[Dict]:
        """
        Parse question text into structured format.
        This is a simplified version - you may need custom parsing
        based on your question paper format.
        """
        questions = []
        # Split by question numbers (Q1, Q2, etc.)
        import re
        pattern = r'Q\.?\s*(\d+)\.?\s*(.*?)(?=Q\.?\s*\d+|$)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for num, content in matches:
            # Try to extract options
            option_pattern = r'\(([A-D])\)\s*(.*?)(?=\([A-D]\)|$)'
            options_matches = re.findall(option_pattern, content, re.DOTALL)
            
            if options_matches:
                question_text = content.split('(A)')[0].strip()
                options = {m[0]: m[1].strip() for m in options_matches}
                
                questions.append({
                    "question_number": int(num),
                    "question_text": question_text,
                    "options": options
                })
        
        return questions
    
    def process_directory(self, directory: str) -> List[Dict]:
        """Process all PDFs in a directory"""
        all_questions = []
        
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                filepath = os.path.join(directory, filename)
                text = self.extract_text_from_pdf(filepath)
                questions = self.parse_questions_from_text(text)
                
                # Add metadata
                for q in questions:
                    q['source_file'] = filename
                    q['source'] = 'PREVIOUS'
                
                all_questions.extend(questions)
        
        return all_questions
```

### 4.3 Embeddings & Vector Storage

**File: `backend/app/rag/embeddings.py`**
```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json

class QuestionEmbeddings:
    """Store and retrieve questions using vector embeddings"""
    
    def __init__(self, persist_path: str = "./data/chroma"):
        # Initialize embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_path
        ))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="questions",
            metadata={"description": "Question bank embeddings"}
        )
    
    def add_questions(self, questions: List[Dict], topic_id: int):
        """Add questions to the vector database"""
        for i, q in enumerate(questions):
            # Create embedding from question text
            text = q['question_text']
            if q.get('options'):
                text += " " + " ".join(q['options'].values())
            
            embedding = self.model.encode(text).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[q['question_text']],
                metadatas=[{
                    "topic_id": str(topic_id),
                    "options": json.dumps(q.get('options', {})),
                    "source": q.get('source', 'PREVIOUS'),
                    "year": str(q.get('year', ''))
                }],
                ids=[f"q_{topic_id}_{i}"]
            )
    
    def search_similar_questions(
        self, 
        query: str, 
        topic_id: int, 
        n_results: int = 10
    ) -> List[Dict]:
        """Find similar questions for a topic"""
        query_embedding = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"topic_id": str(topic_id)}
        )
        
        questions = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            questions.append({
                "question_text": doc,
                "options": json.loads(metadata['options']),
                "source": metadata['source'],
                "year": metadata.get('year')
            })
        
        return questions
```

### 4.4 AI Question Generator

**File: `backend/app/rag/question_generator.py`**
```python
from openai import OpenAI
from typing import List, Dict
import json
from app.core.config import settings

class QuestionGenerator:
    """Generate new questions using AI based on patterns"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_questions(
        self,
        topic_name: str,
        subject_name: str,
        exam_name: str,
        sample_questions: List[Dict],
        count: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate new questions based on sample patterns.
        
        Args:
            topic_name: Name of the topic (e.g., "History of Andhra Pradesh")
            subject_name: Name of the subject (e.g., "Geology")
            exam_name: Name of the exam (e.g., "UPSC")
            sample_questions: Previous year questions as examples
            count: Number of questions to generate
            difficulty: easy, medium, or hard
        """
        
        # Format sample questions for the prompt
        samples = "\n\n".join([
            f"Q: {q['question_text']}\n" +
            "\n".join([f"({k}) {v}" for k, v in q.get('options', {}).items()])
            for q in sample_questions[:5]  # Use top 5 samples
        ])
        
        prompt = f"""You are an expert question paper setter for {exam_name} examination.

CONTEXT:
- Subject: {subject_name}
- Topic: {topic_name}
- Difficulty Level: {difficulty}

SAMPLE QUESTIONS FROM PREVIOUS YEARS:
{samples}

TASK:
Generate exactly {count} NEW multiple-choice questions that:
1. Follow the EXACT pattern and style of the sample questions above
2. Are factually accurate and can be verified
3. Have exactly 4 options (A, B, C, D) with only ONE correct answer
4. Are DIFFERENT from the sample questions (don't repeat)
5. Match the {difficulty} difficulty level
6. Include a brief explanation for why the answer is correct

OUTPUT FORMAT (JSON):
{{
  "questions": [
    {{
      "question_text": "Your question here?",
      "options": {{"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"}},
      "correct_answer": "A",
      "explanation": "Brief explanation of why A is correct",
      "difficulty": "{difficulty}"
    }}
  ]
}}

Generate {count} questions now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert exam question generator. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            questions = result.get("questions", [])
            
            # Mark as AI-generated
            for q in questions:
                q['source'] = 'AI'
                q['is_validated'] = False
            
            return questions
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
```

### 4.5 Question Service (Combining Everything)

**File: `backend/app/services/question_service.py`**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import random
from app.models.question import Question
from app.models.mock_test import MockTest
from app.rag.embeddings import QuestionEmbeddings
from app.rag.question_generator import QuestionGenerator

class QuestionService:
    """Service for managing questions and mock tests"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embeddings = QuestionEmbeddings()
        self.generator = QuestionGenerator()
    
    async def get_mixed_questions(
        self,
        topic_id: int,
        total_questions: int = 10,
        previous_year_ratio: float = 0.5
    ) -> List[Question]:
        """
        Get a mix of previous year and AI-generated questions.
        
        Args:
            topic_id: ID of the topic
            total_questions: Total number of questions needed
            previous_year_ratio: Ratio of previous year questions (0.5 = 50%)
        """
        previous_count = int(total_questions * previous_year_ratio)
        ai_count = total_questions - previous_count
        
        # Get previous year questions
        previous_query = select(Question).where(
            Question.topic_id == topic_id,
            Question.source == "PREVIOUS"
        ).order_by(func.random()).limit(previous_count)
        
        result = await self.db.execute(previous_query)
        previous_questions = list(result.scalars().all())
        
        # Get AI-generated questions (pre-generated & validated)
        ai_query = select(Question).where(
            Question.topic_id == topic_id,
            Question.source == "AI",
            Question.is_validated == True  # Only validated AI questions
        ).order_by(func.random()).limit(ai_count)
        
        result = await self.db.execute(ai_query)
        ai_questions = list(result.scalars().all())
        
        # If not enough AI questions, generate new ones
        if len(ai_questions) < ai_count:
            needed = ai_count - len(ai_questions)
            new_questions = await self._generate_new_questions(
                topic_id, 
                previous_questions, 
                needed
            )
            ai_questions.extend(new_questions)
        
        # Combine and shuffle
        all_questions = previous_questions + ai_questions
        random.shuffle(all_questions)
        
        return all_questions
    
    async def _generate_new_questions(
        self,
        topic_id: int,
        sample_questions: List[Question],
        count: int
    ) -> List[Question]:
        """Generate new AI questions based on samples"""
        # Get topic, subject, exam info
        # (simplified - you'd fetch these from DB)
        
        samples = [
            {
                "question_text": q.question_text,
                "options": q.options
            }
            for q in sample_questions
        ]
        
        generated = self.generator.generate_questions(
            topic_name="Topic Name",  # Fetch from DB
            subject_name="Subject Name",
            exam_name="Exam Name",
            sample_questions=samples,
            count=count
        )
        
        # Save to database
        new_questions = []
        for q in generated:
            question = Question(
                topic_id=topic_id,
                question_text=q['question_text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation'),
                source='AI',
                difficulty=q.get('difficulty', 'medium'),
                is_validated=False  # Needs validation
            )
            self.db.add(question)
            new_questions.append(question)
        
        await self.db.commit()
        return new_questions
    
    async def create_mock_test(
        self,
        user_id: int,
        topic_id: int,
        questions: List[Question],
        session_id: Optional[int] = None
    ) -> MockTest:
        """Create a new mock test record"""
        mock_test = MockTest(
            user_id=user_id,
            topic_id=topic_id,
            session_id=session_id,
            total_questions=len(questions),
            question_ids=[q.id for q in questions]
        )
        self.db.add(mock_test)
        await self.db.commit()
        await self.db.refresh(mock_test)
        return mock_test
```

---

## 5. Phase 3: Frontend Development

### 5.1 Initialize Next.js Project

```bash
# From project root
cd studypulse

# Create Next.js app
npx -y create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

cd frontend

# Install additional dependencies
npm install @tanstack/react-query axios lucide-react framer-motion
npm install @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-progress
npm install react-hook-form zod @hookform/resolvers
npm install zustand
```

### 5.2 Key Frontend Components (Overview)

```
frontend/src/
├── app/
│   ├── page.tsx              # Landing/Home
│   ├── layout.tsx            # Root layout
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── setup/
│   │   └── page.tsx          # Study setup wizard
│   ├── study/
│   │   └── [sessionId]/page.tsx  # Study timer
│   ├── test/
│   │   └── [testId]/page.tsx     # Mock test
│   ├── results/
│   │   └── [testId]/page.tsx     # Test results
│   └── dashboard/
│       └── page.tsx          # User dashboard
├── components/
│   ├── ui/                   # Buttons, inputs, cards
│   ├── setup/                # Setup wizard components
│   ├── timer/                # Study timer components
│   ├── test/                 # Mock test components
│   └── results/              # Results components
├── hooks/
│   ├── useAuth.ts
│   ├── useTimer.ts
│   └── useMockTest.ts
├── services/
│   └── api.ts                # API client
└── store/
    └── useStore.ts           # Zustand store
```

---

## 6. Phase 4: Integration & Testing

### 6.1 Testing Strategy

| Type | Tools | Coverage |
|------|-------|----------|
| **Unit Tests** | pytest (Backend), Jest (Frontend) | Services, Utils |
| **Integration** | pytest + httpx | API Endpoints |
| **E2E** | Playwright | Critical User Flows |

### 6.2 Key Test Scenarios

```
1. User Registration & Login
   ├── Register with valid email
   ├── Login with correct credentials
   └── Handle invalid credentials

2. Study Setup Flow
   ├── Select exam, subject, topic
   ├── Navigate hierarchy correctly
   └── Start study session

3. Study Timer
   ├── Timer countdown works
   ├── Pause/Resume functionality
   └── Complete session triggers test

4. Mock Test
   ├── Questions load correctly
   ├── Answer selection works
   ├── Submit calculates score
   └── Star awarded at 85%+

5. AI Question Generation
   ├── Questions match format
   ├── Correct answers are valid
   └── Rating system works
```

---

## 7. Deployment Guide

### 7.1 Backend Deployment (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Set environment variables
railway variables set DATABASE_URL=<your-postgres-url>
railway variables set OPENAI_API_KEY=<your-key>
railway variables set SECRET_KEY=<random-string>

# Deploy
railway up
```

### 7.2 Frontend Deployment (Vercel)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter your Railway backend URL
```

### 7.3 Database (Supabase - Free Tier)

1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings > Database
4. Use in `DATABASE_URL` environment variable

---

## 📋 Quick Reference Commands

```bash
# Backend Development
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend Development
cd frontend
npm install
npm run dev

# Database Migrations
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run Tests
cd backend && pytest
cd frontend && npm test

# Docker Development
docker-compose up -d
```

---

## 🎯 Next Steps After This Guide

1. ✅ Set up development environment
2. ✅ Initialize backend and frontend projects
3. ✅ Configure database
4. ✅ Implement authentication
5. ✅ Set up RAG pipeline
6. ✅ Build core features
7. ✅ Test with school exam data
8. ✅ Deploy MVP

---

*This implementation plan is designed for beginners. Each section can be expanded with more details as you progress through development.*
