# StudyPulse - Supabase + Ollama Phi4 + RAG Pipeline Integration Guide

## 🎯 Overview

This guide explains how to set up StudyPulse with:
1. **Supabase** - Cloud PostgreSQL database (replacing local PostgreSQL)
2. **Ollama Phi4** - Local LLM for AI question generation (replacing OpenAI GPT-4)
3. **RAG Pipeline** - Advanced question generation from `Ask_Rag_pipeline`

---

## 📋 Prerequisites

### Required Software

1. **Python 3.10+**
2. **Flutter SDK 3.0+** (for mobile app)
3. **Ollama** - Download from [ollama.ai](https://ollama.ai)
4. **Supabase Account** - Already configured

### Required Services

- ✅ Supabase project (already set up)
- ✅ Ollama installed locally
- ✅ RAG Pipeline (`Ask_Rag_pipeline` folder on desktop)

---

## 🚀 Setup Instructions

### Step 1: Install Ollama and Pull Phi4 Model

```powershell
# Download and install Ollama from https://ollama.ai/download

# After installation, pull the Phi4 model
ollama pull phi4

# Verify it's installed
ollama list

# Test the model
ollama run phi4 "Hello, how are you?"

# Keep Ollama running in background (it runs as a service)
```

### Step 2: Set Up Supabase Database

1. **Go to Supabase Dashboard**: https://app.supabase.com
2. **Open your project**: `eguewniqweyrituwbowt`
3. **Navigate to SQL Editor**
4. **Run the schema**:
   - Copy the contents of `studypulse/backend/supabase_schema.sql`
   - Paste into Supabase SQL Editor
   - Click "Run" to create all tables

5. **Verify tables created**:
   - Go to Table Editor
   - You should see: users, exams, subjects, topics, questions, study_sessions, mock_tests, question_responses

6. **Get API Keys** (already provided):
   ```
   URL: https://eguewniqweyrituwbowt.supabase.co
   Public Key: sb_publishable_OOqHjmN6kddWu8r5WdG9Zg_VZTQax-J
   ```

### Step 3: Configure Backend Environment

Create `.env` file in `studypulse/backend/`:

```env
# Supabase Configuration
SUPABASE_URL=https://eguewniqweyrituwbowt.supabase.co
SUPABASE_KEY=sb_publishable_OOqHjmN6kddWu8r5WdG9Zg_VZTQax-J

# JWT Secret
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi4

# RAG Pipeline
RAG_API_URL=http://localhost:8001
RAG_ENABLED=true

# Redis (for RAG caching)
REDIS_URL=redis://localhost:6379

# Question Generation
QUESTION_COUNT_DEFAULT=10
PREVIOUS_YEAR_RATIO=0.5
AI_GENERATED_RATIO=0.5
STAR_THRESHOLD_PERCENTAGE=85

# App Settings
APP_NAME=StudyPulse
DEBUG=true
```

### Step 4: Install Backend Dependencies

```powershell
cd studypulse\backend

# Install new dependencies
pip install supabase postgrest-py requests

# Or install everything
pip install -r requirements.txt
```

### Step 5: Start RAG Pipeline Service

```powershell
# Open new terminal
cd C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline

# Install dependencies (if not already done)
poetry install

# Start Redis, Qdrant, Neo4j (optional - RAG can work without these)
docker-compose up -d redis

# Start RAG API on port 8001
poetry run uvicorn app.api.main:app --reload --port 8001
```

### Step 6: Start StudyPulse Backend

```powershell
# In studypulse/backend terminal
cd studypulse\backend

# Start backend on port 8000
uvicorn app.main:app --reload

# Backend should now connect to:
# - Supabase (database)
# - Ollama Phi4 (AI generation)
# - RAG Pipeline (advanced question generation)
```

### Step 7: Test the Integration

```powershell
# Test backend health
curl http://localhost:8000/api/v1/health

# Test Ollama connection
curl http://localhost:11434/api/tags

# Test RAG pipeline
curl http://localhost:8001/api/health

# Test backend API docs
# Open browser: http://localhost:8000/docs
```

### Step 8: Run Mobile App

```powershell
cd studypulse\mobile

flutter pub get
flutter run

# Login with:
# Email: test@studypulse.com
# Password: password123
```

---

## 🔄 How It Works Together

### 1. Study Session Flow

```
Mobile App
  ↓ (Start Study Session)
Backend (port 8000)
  ↓ (Create session in Supabase)
  ↓ (Trigger RAG pipeline)
RAG Pipeline (port 8001)
  ↓ (Prepare questions in background)
  ↓ (Use Qdrant for retrieval)
  ↓ (Use Neo4j for context)
  ↓ (Generate with Ollama Phi4)
  ↓ (Store in Redis cache)
Backend
  ↓ (Fetch prepared questions)
  ↓ (Mix with previous year questions from Supabase)
  ↓ (Return to mobile app)
Mobile App
  ↓ (Display test)
```

### 2. Question Generation

**Two Paths:**

**Path A: Quick Generation (Direct)**
```
Backend → Ollama Phi4 → Questions
```

**Path B: Advanced Generation (RAG Pipeline)**
```
Backend → RAG Pipeline → Retrieval (Qdrant) → Context → Ollama Phi4 → Validation → Questions
```

### 3. Data Storage

- **Users, Exams, Topics** → Supabase PostgreSQL
- **Study Sessions, Mock Tests** → Supabase PostgreSQL
- **Vector Embeddings** → Qdrant (in RAG pipeline)
- **Knowledge Graph** → Neo4j (in RAG pipeline)
- **Cache** → Redis

---

## 🧪 Testing Each Component

### Test Supabase Connection

```python
# Run in Python terminal
from app.core.supabase import supabase_client

# Test connection
exams = await supabase_client.get_exams()
print(f"Found {len(exams)} exams")
```

### Test Ollama Phi4

```powershell
# Test via Ollama CLI
ollama run phi4 "Generate a sample UPSC question about Indian history."

# Test via Python
from app.core.ollama import ollama_client

response = ollama_client.generate("What is 2+2?")
print(response)
```

### Test RAG Pipeline

```powershell
# Test session creation
curl -X POST http://localhost:8001/api/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test123",
    "exam": "UPSC",
    "subject": "History",
    "topic": "Ancient India",
    "duration_minutes": 30
  }'
```

---

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      Mobile App (Flutter)                     │
│                     localhost:8000/api/v1                     │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  StudyPulse Backend (FastAPI)                 │
│                     Port 8000                                 │
├──────────────────────────┬────────────────┬───────────────────┤
│   Supabase Client        │   Ollama       │   RAG Client      │
│   (Database)             │   (Phi4 LLM)   │   (Advanced Gen)  │
└──────────┬───────────────┴────────┬───────┴──────┬────────────┘
           │                        │              │
           ▼                        ▼              ▼
┌──────────────────┐   ┌───────────────────┐   ┌──────────────────┐
│   Supabase       │   │   Ollama Server   │   │  RAG Pipeline    │
│   PostgreSQL     │   │   localhost:11434 │   │  Port 8001       │
│   (Cloud)        │   │   (Local)         │   │  (Local)         │
└──────────────────┘   └───────────────────┘   └────────┬─────────┘
                                                         │
                                    ┌────────────────────┼─────────────┐
                                    │                    │             │
                                    ▼                    ▼             ▼
                            ┌──────────┐        ┌─────────┐   ┌──────────┐
                            │  Redis   │        │ Qdrant  │   │  Neo4j   │
                            │  Cache   │        │ Vector  │   │  Graph   │
                            └──────────┘        └─────────┘   └──────────┘
```

---

## 🔧 Configuration Files

### Backend `.env`
```env
SUPABASE_URL=https://eguewniqweyrituwbowt.supabase.co
SUPABASE_KEY=sb_publishable_OOqHjmN6kddWu8r5WdG9Zg_VZTQax-J
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi4
RAG_API_URL=http://localhost:8001
RAG_ENABLED=true
```

### Mobile `lib/api/api_service.dart`
```dart
static const String _devBaseUrlAndroid = 'http://10.0.2.2:8000/api/v1';
static const String _devBaseUrlOther = 'http://localhost:8000/api/v1';
```

---

## 🐛 Troubleshooting

### Issue: Ollama not found

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Or reinstall from https://ollama.ai
```

### Issue: Phi4 model not available

```powershell
# Pull the model
ollama pull phi4

# List available models
ollama list
```

### Issue: Supabase connection error

1. Check URL and API key in `.env`
2. Verify project is active in Supabase dashboard
3. Check if tables exist in Supabase Table Editor
4. Run `supabase_schema.sql` again if tables missing

### Issue: RAG pipeline not responding

```powershell
# Check if running
curl http://localhost:8001/api/health

# If not, start it
cd C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline
poetry run uvicorn app.api.main:app --reload --port 8001
```

### Issue: Redis connection error

```powershell
# Start Redis (if using Docker)
docker run -d -p 6379:6379 redis

# Or install Redis for Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

---

## 📈 Performance Optimization

### 1. Question Generation Speed

- **Fast Mode**: Direct Ollama Phi4 (2-5 seconds per question)
- **Quality Mode**: RAG Pipeline (10-20 seconds, higher quality)

Configure in backend:
```python
RAG_ENABLED=false  # Use only Ollama (faster)
RAG_ENABLED=true   # Use RAG pipeline (better quality)
```

### 2. Caching

- RAG pipeline uses Redis to cache prepared tests
- Reduces regeneration time from 20s to <1s

### 3. Background Processing

- RAG starts preparing questions during study timer
- Questions ready when timer completes

---

## 🎯 Next Steps

1. ✅ **Populate Supabase** with exam data
   - Use Supabase Table Editor to add exams, subjects, topics
   - Or create a seeding script

2. ✅ **Feed RAG Pipeline** with study materials
   - Add PDFs to `Ask_Rag_pipeline/data/`
   - Run ingestion scripts

3. ✅ **Test End-to-End** flow
   - Start study session
   - Verify RAG preparation
   - Take mock test
   - Check results in Supabase

4. ✅ **Monitor Performance**
   - Check Ollama response times
   - Monitor Supabase query performance
   - Verify RAG pipeline status

---

## 📝 Important Notes

1. **Ollama must be running** for AI question generation
2. **RAG pipeline is optional** - backend works without it (uses direct Ollama)
3. **Supabase is always required** for database operations
4. **Redis is required** if RAG pipeline is enabled
5. **Guest mode** works without authentication

---

## 🔐 Security

- Supabase uses Row Level Security (RLS)
- JWT tokens for authentication
- API keys stored in `.env` (not in git)
- Ollama runs locally (no data sent to external services)

---

**Ready to use! Start all services and enjoy your AI-powered exam prep platform! 🚀**
