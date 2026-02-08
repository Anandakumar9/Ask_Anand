# 🚨 Troubleshooting Guide

## Mobile App Shows "Can't Reach Localhost"

### Causes & Solutions

#### 1. Backend Not Running
**Check**: Look for "Backend API - Port 8000" window
**Fix**:
```powershell
cd studypulse\backend
..\..\..\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

#### 2. CORS Issue
**Symptoms**: Backend runs but mobile app can't connect
**Fix**: Already configured in `backend/app/main.py` - CORS allows all origins

#### 3. Flutter Not Starting
**Check**: Look for "Mobile App - Port 8080" window
**Fix**:
```powershell
cd studypulse\mobile
flutter clean
flutter pub get
flutter run -d chrome --web-port=8080
```

#### 4. Virtual Environment Issues
**Check**: Does `..\.venv\Scripts\python.exe` exist?
**Fix**:
```powershell
cd Ask_Anand
python -m venv .venv
.venv\Scripts\pip install -r studypulse\backend\requirements.txt
```

---

## RAG Pipeline Integration

### What is RAG Pipeline?
Advanced AI feature using:
- **Qdrant**: Vector database for semantic search
- **Neo4j**: Knowledge graph for relationships
- **Redis**: Caching layer
- **Custom API**: Question generation pipeline

### Where is it?
Located at: `C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline`

### How to Use It

#### Option 1: Manual Start
```powershell
# 1. Start Docker Desktop

# 2. Start Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 3. Start RAG Pipeline API
cd C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline
uvicorn app.api.main:app --reload --port 8001
```

#### Option 2: Integrated Start
RAG Pipeline is integrated in the backend at `backend/app/core/rag_client.py`

**Configuration**:
```python
# backend/app/core/config.py
RAG_API_URL = "http://localhost:8001"  # RAG Pipeline endpoint
RAG_ENABLED = True                      # Enable RAG features
```

**How It Works**:
1. User starts study session → Backend calls RAG to prepare questions
2. User starts mock test → If RAG has questions ready, use them
3. Fallback → If RAG unavailable, use Ollama directly (already working!)

### Current Status

✅ **Working NOW**: 
- Backend uses Ollama Phi4 for question generation
- Questions generated on-demand during mock tests
- Fully functional without RAG Pipeline

⚠️ **RAG Pipeline (Optional)**:
- Requires Docker + Qdrant + separate API
- Provides advanced features like:
  - Pre-generated questions during study
  - Semantic search across question database
  - Knowledge graph relationships
  - Better question quality/diversity

### Testing RAG Integration

```powershell
# 1. Check if RAG is available
curl http://localhost:8001/health

# 2. Check backend RAG status
curl http://localhost:8000/health
# Look for: "rag_pipeline": "enabled" or "disabled"

# 3. Start study session (triggers RAG)
curl -X POST http://localhost:8000/api/v1/study/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic_id": 1, "duration_mins": 15}'
```

---

## Common Errors

### "ModuleNotFoundError: No module named 'supabase'"
```powershell
cd Ask_Anand
.venv\Scripts\pip install supabase
```

### "Ollama connection refused"
```powershell
# Start Ollama in a terminal
ollama serve

# Or check if running
curl http://localhost:11434/api/tags
```

### "Port 8000 already in use"
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill it
taskkill /F /PID <PID_NUMBER>
```

### "Flutter: Chrome not found"
```powershell
# Make sure Chrome is installed
# Or use a different browser:
flutter run -d edge
```

---

## How to Enable RAG Pipeline

### Step 1: Install Docker
1. Download Docker Desktop for Windows
2. Install and start it
3. Wait for "Docker Desktop is running"

### Step 2: Start Dependencies
```powershell
# Terminal 1: Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 2: Neo4j (Optional)
docker run -p 7474:7474 -p 7687:7687 neo4j

# Terminal 3: Redis (Optional)  
docker run -p 6379:6379 redis
```

### Step 3: Configure Backend
```python
# backend/app/core/config.py
RAG_ENABLED = True
RAG_API_URL = "http://localhost:8001"
```

### Step 4: Start RAG Pipeline
```powershell
cd C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline
uvicorn app.api.main:app --reload --port 8001
```

### Step 5: Verify
```powershell
# Check RAG health
curl http://localhost:8001/health

# Check backend sees RAG
curl http://localhost:8000/health
# Should show RAG as enabled
```

---

## Quick Diagnosis

Run this to check everything:
```powershell
# Backend
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags

# RAG Pipeline (if enabled)
curl http://localhost:8001/health

# Qdrant (if RAG enabled)
curl http://localhost:6333
```

Expected output:
- Backend: `{"status": "healthy", "database": "connected", "ollama": "available"}`
- Ollama: List of models including `phi4:3.8b`
- RAG: `{"status": "healthy"}`
- Qdrant: `{"title": "qdrant", "version": "..."}`

---

## Current System Architecture

```
User (Browser at localhost:8080)
    ↓
Flutter Mobile App
    ↓ HTTP API calls
Backend API (localhost:8000)
    ↓
    ├─→ Supabase (Database) ✅ Working
    ├─→ Ollama Phi4 (AI) ✅ Working  
    └─→ RAG Pipeline (localhost:8001) ⚠️ Optional
         ↓
         ├─→ Qdrant (Vector DB)
         ├─→ Neo4j (Knowledge Graph)
         └─→ Redis (Cache)
```

---

## Success Checklist

When `START.bat` runs successfully, you should see:

1. ✅ **Backend Window** (Yellow)
   - "Uvicorn running on http://0.0.0.0:8000"
   - "✅ Supabase connected successfully"
   - "🤖 Using Ollama: phi4:3.8b"

2. ✅ **Mobile Window** (Pink)
   - "Flutter assets will be downloaded from http://localhost:8080"
   - Chrome browser opens automatically
   - Welcome screen appears

3. ✅ **App Works**
   - Can register/login
   - Can see dashboard
   - Can start study sessions
   - Can take mock tests

---

**If you see all 3 ✅, your app is working perfectly!**

RAG Pipeline is a bonus feature, not required for core functionality.
