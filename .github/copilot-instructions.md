# StudyPulse - AI Coding Agent Instructions

## Project Overview
StudyPulse is an AI-powered exam preparation platform with three main components:
- **Backend** (FastAPI + Python): REST API with RAG pipeline for question generation
- **Frontend** (Next.js + TypeScript): Web application
- **Mobile** (Flutter + Dart): Cross-platform Android/iOS app

**Core Concept:** Students study for configurable duration (5-120 mins), then take AI-generated + previous year question mock tests. Score ≥85% earns a star.

---

## Architecture

### Backend (`studypulse/backend/`)
- **Framework:** FastAPI (async Python)
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **AI/RAG:** OpenAI GPT-4 for question generation
- **Key Pattern:** Domain-driven structure (api, models, schemas, services, rag)

**Critical Files:**
- `app/api/mock_test.py` - Mock test endpoints, RAG integration, question mixing
- `app/rag/question_generator.py` - AI question generation with GPT-4
- `app/models/` - SQLAlchemy models (User, Exam, Subject, Topic, Question, MockTest)
- `app/schemas/` - Pydantic schemas for request/response validation

**Running Backend:**
```powershell
cd studypulse/backend
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

### Frontend (`studypulse/frontend/`)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **State:** Zustand
- **Pattern:** Server components + client components with 'use client'

### Mobile (`studypulse/mobile/`)
- **Framework:** Flutter 3.0+
- **State:** Provider
- **HTTP:** Dio client
- **Pattern:** Screens + API service + global store

**Running Mobile:**
```powershell
cd studypulse/mobile
flutter pub get
flutter run  # Select device when prompted
```

**Platform-specific API URLs:**
- Android Emulator: `http://10.0.2.2:8000/api/v1`
- iOS Simulator: `http://localhost:8000/api/v1`

---

## Key Workflows

### 1. RAG Question Generation Flow
When mock test starts:
1. `POST /api/v1/mock-test/start` in `app/api/mock_test.py`
2. Fetches previous year questions from database
3. If insufficient AI questions, calls `QuestionGenerator.generate_questions()`
4. GPT-4 generates questions matching previous year pattern
5. Mixes 50% previous + 50% AI questions (configurable)
6. Returns shuffled question set to client

**Key Code:** `studypulse/backend/app/api/mock_test.py` lines 50-120

### 2. Study Session Flow
```
Mobile/Web → Start Timer (5-120 mins) → Complete Session → Start Test → RAG generates questions → Submit Answers → Get Results (score, star if ≥85%)
```

### 3. Authentication
- JWT-based auth (OAuth2 password flow)
- Token stored in secure storage (mobile) or cookies (web)
- Guest mode available in mobile app

---

## Development Conventions

### Backend
- **Async everywhere:** Use `async def` for all route handlers
- **Dependency injection:** Use FastAPI's `Depends()` for DB, auth
- **Error handling:** Raise `HTTPException` with appropriate status codes
- **Database:** Always use `async with` context managers
- **Naming:** Snake_case for Python (PEP 8)

**Example:**
```python
@router.post("/start", response_model=MockTestResponse)
async def start_mock_test(
    test_data: MockTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Implementation
```

### Frontend (Next.js)
- **File-based routing:** App router in `src/app/`
- **Server vs Client:** Use `'use client'` only when needed (forms, hooks, interactivity)
- **API calls:** Use `src/services/api.ts` service layer
- **Styling:** Tailwind utility classes, avoid custom CSS
- **Naming:** CamelCase for components, kebab-case for files

### Mobile (Flutter)
- **Screens in `lib/screens/`:** Each screen is a StatefulWidget
- **API calls via Dio:** All in `lib/api/api_service.dart`
- **State:** Provider for global (auth, user), local setState for UI
- **Navigation:** MaterialPageRoute, Navigator.push/pop
- **Naming:** snake_case for files, PascalCase for classes

---

## Critical Integration Points

### Backend ↔ Mobile API Contract
All endpoints prefixed with `/api/v1/`:
- `POST /auth/login` - Returns `{access_token, user}`
- `GET /dashboard/` - Returns stats, continue_topic, recent_activity
- `GET /exams/` - Returns exams with nested subjects/topics
- `POST /study/sessions` - Body: `{topic_id, duration_mins}`
- `POST /mock-test/start` - Body: `{topic_id, session_id?, question_count?, previous_year_ratio?}`
- `POST /mock-test/{test_id}/submit` - Body: `{responses: [{question_id, answer}], total_time_seconds}`

**API Service:** `studypulse/mobile/lib/api/api_service.dart`

### Database Schema
- **User** → **MockTest** (one-to-many)
- **Exam** → **Subject** → **Topic** (hierarchical)
- **Topic** → **Question** (one-to-many)
- **MockTest** → stores `question_ids` as JSON array

---

## Common Tasks

### Adding a New API Endpoint
1. Define Pydantic schema in `app/schemas/`
2. Add route in appropriate `app/api/*.py` file
3. Use existing patterns for auth, DB, error handling
4. Update mobile `api_service.dart` to call new endpoint
5. Test with `curl` or Postman before frontend integration

### Adding New Screen to Mobile
1. Create `lib/screens/my_screen.dart`
2. Import in navigation file (e.g., `home_screen.dart`)
3. Add API method in `api_service.dart` if needed
4. Use Provider if state needs to be global
5. Follow Material Design 3 patterns

### Modifying RAG Question Generation
1. Edit `app/rag/question_generator.py`
2. Update prompt in `generate_questions()` method
3. Ensure output format matches `QuestionDisplay` schema
4. Test with real topics that have sample questions

---

## Testing & Debugging

### Backend
```powershell
# Run tests
cd studypulse/backend
pytest tests/

# Check specific endpoint
curl http://localhost:8000/api/v1/health

# View logs
# FastAPI prints to console with uvicorn --reload
```

### Mobile
```powershell
# Check for issues
flutter doctor -v

# Clean build
flutter clean && flutter pub get

# Run with logs
flutter run --verbose

# Hot reload: Press 'r' in terminal
# Hot restart: Press 'R'
```

---

## Environment Setup

### Backend Requirements
- Python 3.10+
- PostgreSQL running
- OpenAI API key in `.env`:
  ```
  OPENAI_API_KEY=sk-...
  DATABASE_URL=postgresql+asyncpg://user:pass@localhost/studypulse
  ```

### Mobile Requirements
- Flutter SDK 3.0+
- Android Studio (for Android)
- Xcode (for iOS, macOS only)
- Backend running on `localhost:8000`

---

## Important Notes

1. **Star Threshold:** Currently 85% in backend (`app/api/mock_test.py` line ~350). To change to 70%, modify the comparison.

2. **Timer Durations:** Defined in `mobile/lib/screens/study_screen.dart` line 17. Default: [5, 10, 15, 20, 30, 45, 60, 90, 120] minutes.

3. **Guest Mode:** Mobile app allows login without credentials. Auto-creates guest user for testing.

4. **Question Generation:** Requires OpenAI API key. Without it, only previous year questions are used.

5. **Database Seeding:** Use `backend/scripts/seed_data.py` to populate initial exam data.

---

## Quick Reference

**Backend:** FastAPI + PostgreSQL + OpenAI GPT-4  
**Frontend:** Next.js 14 + Tailwind CSS  
**Mobile:** Flutter + Dio + Provider  
**DB:** PostgreSQL (relational) + potential ChromaDB (vectors)  
**Auth:** JWT tokens  
**API Pattern:** RESTful  
**Deployment:** Railway (BE), Vercel (FE), App Stores (Mobile)

---

## File Navigation

### Most Important Files
- `backend/app/api/mock_test.py` - Mock test logic & RAG
- `backend/app/rag/question_generator.py` - AI question generation
- `mobile/lib/main.dart` - Mobile app entry point
- `mobile/lib/api/api_service.dart` - All API calls
- `mobile/lib/screens/home_screen.dart` - Main dashboard
- `frontend/src/app/page.tsx` - Web home page

### Documentation
- `studypulse/README.md` - Main project overview
- `studypulse/mobile/README.md` - Mobile setup guide
- `studypulse/mobile/QUICK_START.md` - Quick start for beginners
- `PRD.md` - Product requirements document
- `IMPLEMENTATION_PLAN.md` - Technical implementation plan

---

## Common Patterns

### Error Handling (Backend)
```python
if not resource:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
```

### API Call (Mobile)
```dart
Future<Response> getData() async {
  return _dio.get('/endpoint');
}
```

### Navigation (Mobile)
```dart
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => NextScreen()),
);
```

---

**Last Updated:** February 6, 2026  
**Version:** 1.0 - Production Ready

