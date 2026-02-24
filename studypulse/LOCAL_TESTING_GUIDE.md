# Local Testing Guide for Question Ingestion System

This guide walks you through testing the complete question ingestion system locally before deploying to Railway (backend) and Vercel (frontend).

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (or use Docker)
- Git

## Step 1: Start Local PostgreSQL Database

### Option A: Using Docker (Recommended)
```bash
# Start PostgreSQL container
docker run --name studypulse-db \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=studypulse \
    -p 5432:5432 \
    -d postgres:15

# Verify container is running
docker ps
```

### Option B: Using Local PostgreSQL
```bash
# Create database
createdb studypulse

# Or using psql
psql -U postgres
CREATE DATABASE studypulse;
\q
```

## Step 2: Configure Backend Environment

```bash
# Navigate to backend directory
cd studypulse/backend

# Create .env file
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/studypulse

# Security
SECRET_KEY=your-secret-key-for-testing-only-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/ML (optional for testing)
OLLAMA_BASE_URL=http://localhost:11434
OPENROUTER_API_KEY=your-openrouter-key

# Environment
ENVIRONMENT=development
DEBUG=true
EOF

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Run Database Migration

```bash
# Make sure you're in the backend directory with venv activated
cd studypulse/backend

# Initialize Alembic (if not already done)
alembic init alembic

# Run migrations
alembic upgrade head

# Verify tables were created
psql -U postgres -d studypulse -c "\dt"
```

## Step 4: Seed Test Data

```bash
# Run the demo data seeder
python seed_demo_data.py

# Or manually create a test topic
python -c "
import asyncio
from app.core.database import async_session_maker
from app.models.exam import Exam, Subject, Topic

async def seed():
    async with async_session_maker() as db:
        exam = Exam(name='NEET PG', description='Medical Entrance', is_active=True)
        db.add(exam)
        await db.flush()
        
        subject = Subject(exam_id=exam.id, name='Pediatrics', description='Child Health', is_active=True)
        db.add(subject)
        await db.flush()
        
        topic = Topic(subject_id=subject.id, name='Fluid and Electrolytes', description='Test topic', is_active=True)
        db.add(topic)
        await db.commit()
        print(f'Created topic with ID: {topic.id}')

asyncio.run(seed())
"
```

## Step 5: Start Backend Server

```bash
# Terminal 1: Start backend
cd studypulse/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verify backend is running
curl http://localhost:8000/api/v1/health
```

## Step 6: Test HTML Parser

```bash
# Terminal 2: Test parser
cd studypulse/backend

# Test with your HTML file
python scripts/html_question_parser.py \
    --input "C:/Users/anand/Downloads/Telegram Desktop/Prep_RR_Qb_Gynaecology___Obstetrics.html" \
    --output "data/questions_import.json" \
    --default-topic 1 \
    --report

# Check the output
cat data/questions_import.json | head -50
cat data/questions_import.report.json
```

## Step 7: Test API Import

```bash
# Import questions via API
curl -X POST "http://localhost:8000/api/v1/questions/import/bulk" \
    -H "Content-Type: application/json" \
    -d @data/questions_import.json

# Check import stats
curl "http://localhost:8000/api/v1/questions/import/stats/1"

# Get questions
curl "http://localhost:8000/api/v1/questions/topic/1?skip=0&limit=5" | jq
```

## Step 8: Start Frontend

```bash
# Terminal 3: Start frontend
cd studypulse/frontend

# Install dependencies
npm install

# Create .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

# Start development server
npm run dev

# Open browser
# http://localhost:3000
```

## Step 9: Test Frontend Components

Create a test page to verify the QuestionCard component:

```bash
# Create test page
cat > studypulse/frontend/src/app/test-questions/page.tsx << 'EOF'
'use client';

import { useState, useEffect } from 'react';
import QuestionCard from '@/components/QuestionCard';

export default function TestQuestionsPage() {
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [showResult, setShowResult] = useState(false);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/questions/topic/1?skip=0&limit=10')
            .then(res => res.json())
            .then(data => {
                setQuestions(data);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-8">Loading...</div>;
    if (!questions.length) return <div className="p-8">No questions found</div>;

    const question = questions[currentIndex];

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-3xl mx-auto">
                <QuestionCard
                    question={question}
                    questionNumber={currentIndex + 1}
                    totalQuestions={questions.length}
                    selectedAnswer={selectedAnswer}
                    showResult={showResult}
                    onAnswerSelect={(answer) => {
                        setSelectedAnswer(answer);
                        setShowResult(true);
                    }}
                />
                
                <div className="mt-4 flex gap-4">
                    <button
                        onClick={() => {
                            setCurrentIndex(i => Math.max(0, i - 1));
                            setSelectedAnswer(null);
                            setShowResult(false);
                        }}
                        disabled={currentIndex === 0}
                        className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                    >
                        Previous
                    </button>
                    <button
                        onClick={() => {
                            setCurrentIndex(i => Math.min(questions.length - 1, i + 1));
                            setSelectedAnswer(null);
                            setShowResult(false);
                        }}
                        disabled={currentIndex === questions.length - 1}
                        className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>
    );
}
EOF

# Open browser to test
# http://localhost:3000/test-questions
```

## Step 10: Run Automated Tests

```bash
# Terminal 4: Run tests
cd studypulse/backend
source venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E test for question ingestion
python tests/test_question_ingestion.py
```

## Step 11: Verify Database Content

```bash
# Connect to database
psql -U postgres -d studypulse

# Check questions with images
SELECT id, question_text, question_images, explanation_images 
FROM questions 
WHERE question_images != '[]'::jsonb 
LIMIT 5;

# Check options format
SELECT id, options FROM questions LIMIT 2;

# Count questions by source
SELECT source, COUNT(*) FROM questions GROUP BY source;
```

## Complete Testing Checklist

### Backend Tests
- [ ] Database migration runs successfully
- [ ] Demo data seeds correctly
- [ ] Health endpoint returns 200
- [ ] HTML parser extracts questions
- [ ] Bulk import API works
- [ ] Questions stored with images
- [ ] Options stored in correct format

### Frontend Tests
- [ ] Frontend starts without errors
- [ ] Questions load from API
- [ ] QuestionCard displays question text
- [ ] Question images display
- [ ] Option images display
- [ ] Explanation images display
- [ ] Answer selection works
- [ ] Result shows correctly

### Integration Tests
- [ ] End-to-end flow works
- [ ] Image URLs are accessible
- [ ] Audio/video links work

## Troubleshooting

### Backend won't start
```bash
# Check database connection
psql -U postgres -d studypulse -c "SELECT 1"

# Check environment variables
cat .env

# Check logs
tail -f logs/app.log
```

### Migration fails
```bash
# Reset database
dropdb studypulse
createdb studypulse
alembic upgrade head
```

### Import fails
```bash
# Check topic exists
curl "http://localhost:8000/api/v1/topics"

# Check JSON format
cat data/questions_import.json | jq '.questions[0]'
```

### Frontend can't connect to backend
```bash
# Check CORS settings in backend
# In app/main.py, ensure:
# app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"])

# Check API URL in frontend
cat studypulse/frontend/.env.local
```

## Quick Test Script

Save this as `test_local.sh` (Linux/Mac) or `test_local.bat` (Windows):

```bash
#!/bin/bash
# test_local.sh

echo "🧪 Testing Question Ingestion System Locally"

# 1. Check database
echo "1️⃣ Checking database connection..."
psql -U postgres -d studypulse -c "SELECT 1" || { echo "❌ Database not connected"; exit 1; }
echo "✅ Database connected"

# 2. Check backend
echo "2️⃣ Checking backend health..."
curl -s http://localhost:8000/api/v1/health | jq . || { echo "❌ Backend not running"; exit 1; }
echo "✅ Backend running"

# 3. Check frontend
echo "3️⃣ Checking frontend..."
curl -s http://localhost:3000 > /dev/null || { echo "❌ Frontend not running"; exit 1; }
echo "✅ Frontend running"

# 4. Test import
echo "4️⃣ Testing question import..."
curl -X POST "http://localhost:8000/api/v1/questions/import/bulk" \
    -H "Content-Type: application/json" \
    -d '{"questions": [{"topic_id": 1, "question_text": "Test question?", "options": {"A": "A", "B": "B", "C": "C", "D": "D"}, "correct_answer": "A"}]}' \
    | jq .
echo "✅ Import working"

echo "🎉 All tests passed!"
```

## Next Steps After Local Testing

Once all tests pass locally:

1. **Commit changes**
   ```bash
   git add .
   git commit -m "Add question ingestion with image support"
   git push origin main
   ```

2. **Deploy backend to Railway**
   ```bash
   railway login
   railway up
   ```

3. **Deploy frontend to Vercel**
   ```bash
   vercel --prod
   ```

4. **Run production migration**
   ```bash
   railway run alembic upgrade head
   ```

5. **Import questions to production**
   ```bash
   curl -X POST "https://your-railway-app.up.railway.app/api/v1/questions/import/bulk" \
       -H "Content-Type: application/json" \
       -d @data/questions_import.json
   ```
