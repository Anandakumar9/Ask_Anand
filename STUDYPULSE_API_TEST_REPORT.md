# StudyPulse Backend API Test Report

## Test Configuration

**Localhost URL**: `http://localhost:8001`
**Production URL**: `https://askanand-simba.up.railway.app`
**Test Date**: 2026-02-18

## Endpoint Specifications

### 1. GET / - Health Check (Root)
**Path**: `/`
**Method**: GET
**Authentication**: Not required
**Expected Status**: 200 OK

**Expected Response**:
```json
{
  "message": "Welcome to StudyPulse API",
  "version": "1.0",
  "docs": "/docs",
  "health": "/health"
}
```

**Purpose**: Basic health check to verify the API is running.

---

### 2. GET /api/v1/exams/ - List Exams
**Path**: `/api/v1/exams/`
**Method**: GET
**Authentication**: Not required
**Expected Status**: 200 OK

**Query Parameters**:
- `category` (optional): Filter by exam category (e.g., "Government", "Engineering")
- `search` (optional): Search exams by name

**Expected Response**:
```json
[
  {
    "id": 1,
    "name": "UPSC Civil Services",
    "category": "Government",
    "icon_url": "https://...",
    "subject_count": 5
  }
]
```

**Purpose**: Lists all available exams in the system with their subject counts.

---

### 3. POST /api/v1/auth/guest - Guest Authentication
**Path**: `/api/v1/auth/guest`
**Method**: POST
**Authentication**: Not required
**Expected Status**: 200 OK

**Request Body**: Empty `{}`

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "guest@studypulse.com",
    "name": "Guest User",
    "total_stars": 0,
    "is_active": true
  }
}
```

**Purpose**: Provides instant authentication for guest users without registration. Creates a guest user automatically if it doesn't exist.

**Implementation Notes**:
- Guest email: `guest@studypulse.com`
- Password: `guest-no-login-required` (hashed, not exposed)
- Returns JWT token valid for API access

---

### 4. POST /api/v1/auth/login - Regular Login
**Path**: `/api/v1/auth/login`
**Method**: POST
**Authentication**: Not required
**Expected Status**: 200 OK for success, 401 for invalid credentials

**Content-Type**: `application/x-www-form-urlencoded`

**Request Body** (form-encoded):
```
username=test@studypulse.com&password=password123
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "email": "test@studypulse.com",
    "name": "Test User",
    "total_stars": 0,
    "is_active": true
  }
}
```

**Error Response** (401):
```json
{
  "detail": "Incorrect email or password"
}
```

**Purpose**: Authenticates registered users using OAuth2 password flow.

**Important**:
- Test user must exist in database first
- Uses form-encoded data (NOT JSON)
- Username field contains the email address

---

### 5. GET /api/v1/dashboard - Dashboard Data
**Path**: `/api/v1/dashboard`
**Method**: GET
**Authentication**: Required (Bearer token)
**Expected Status**: 200 OK, 401 if no token

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "greeting": "Good Morning",
  "user_name": "Test",
  "stats": {
    "sessions": 5,
    "tests": 3,
    "stars": 2,
    "study_streak": 1
  },
  "performance_goal": {
    "target": 100.0,
    "current": 75.5,
    "percentage": 75
  },
  "recent_activity": [
    {
      "type": "test",
      "topic_name": "Physics",
      "subject_name": "Science",
      "score": 85.0,
      "percentage": 85.0,
      "star_earned": true,
      "timestamp": "2026-02-18T10:30:00"
    }
  ],
  "continue_topic": {
    "topic_id": 1,
    "topic_name": "Physics",
    "subject_name": "Science",
    "progress": 60,
    "session_completed": true
  }
}
```

**Purpose**: Provides personalized dashboard with user stats, performance metrics, recent activity, and suggested topics.

**Features**:
- Time-based greeting (Good Morning/Afternoon/Evening/Night)
- Study streak calculation
- Performance goal tracking (target: 100%)
- Recent activity feed (last 10 items)
- Continue studying suggestion

---

### 6. POST /api/v1/mock-test/start - Create Mock Test
**Path**: `/api/v1/mock-test/start`
**Method**: POST
**Authentication**: Required (Bearer token)
**Expected Status**: 200 OK, 404 if topic not found

**Request Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "topic_id": 1,
  "question_count": 5,
  "previous_year_ratio": 0.7,
  "time_limit_seconds": 300
}
```

**Expected Response** (Success):
```json
{
  "test_id": 42,
  "questions": [
    {
      "id": 101,
      "question_text": "What is the capital of France?",
      "options": {
        "A": "Paris",
        "B": "London",
        "C": "Berlin",
        "D": "Rome"
      },
      "source": "PREVIOUS"
    }
  ],
  "time_limit_seconds": 300,
  "total_questions": 5,
  "metadata": {
    "cached": false,
    "generation_time_ms": 450,
    "previous_year_count": 3,
    "ai_generated_count": 2
  }
}
```

**Error Response** (404 - No Questions):
```json
{
  "detail": "No questions available for topic 'Physics' or similar topics. Please try a different topic or add questions to the database."
}
```

**Purpose**: Starts a mock test with intelligent question generation using the RAG pipeline.

**Features**:
- Cache-first approach (returns pre-generated questions in milliseconds)
- Intelligent question mix (70% previous year, 30% AI-generated by default)
- Fallback to similar topics if insufficient questions
- Real-time generation time tracking

**Parameters**:
- `topic_id`: ID of the topic to test on (required)
- `question_count`: Number of questions (default: 10, range: 1-50)
- `previous_year_ratio`: Ratio of previous year questions (0.0-1.0)
- `time_limit_seconds`: Time limit for the test (default: 600)

---

## Summary of API Routes

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/` | GET | No | Health check |
| `/health` | GET | No | Detailed health status |
| `/api/v1/exams/` | GET | No | List all exams |
| `/api/v1/auth/guest` | POST | No | Guest login |
| `/api/v1/auth/login` | POST | No | User login |
| `/api/v1/auth/register` | POST | No | User registration |
| `/api/v1/dashboard` | GET | Yes | User dashboard |
| `/api/v1/mock-test/start` | POST | Yes | Start mock test |
| `/api/v1/mock-test/{test_id}/submit` | POST | Yes | Submit test answers |
| `/api/v1/mock-test/{test_id}/results` | GET | Yes | Get test results |
| `/api/v1/mock-test/history/all` | GET | Yes | Get test history |

---

## How to Run the Test Script

1. **Install dependencies**:
   ```bash
   pip install requests
   ```

2. **Run the test script**:
   ```bash
   python test_all_endpoints.py
   ```

3. **Expected Output**:
   - Detailed test results for each endpoint
   - Status codes and response times
   - Response body previews (first 200 chars)
   - Summary table comparing localhost vs Railway

---

## Testing Checklist

### Localhost Testing (http://localhost:8001)
- [ ] Backend server is running
- [ ] Port 8001 is accessible
- [ ] Database is initialized
- [ ] Redis cache is available (optional)
- [ ] Ollama is running (optional, for AI generation)

### Railway Testing (https://askanand-simba.up.railway.app)
- [ ] Railway deployment is active
- [ ] Environment variables are configured
- [ ] Database is provisioned
- [ ] Public URL is accessible
- [ ] CORS is configured for allowed origins

---

## Common Issues and Solutions

### Issue 1: Connection Error on Localhost
**Error**: `Connection Error: Cannot connect to server`

**Solution**:
```bash
cd studypulse/backend
python -m uvicorn app.main:app --reload --port 8001
```

### Issue 2: 401 Unauthorized on Dashboard
**Error**: `401 Unauthorized`

**Solution**:
- Ensure you're passing the Bearer token in the Authorization header
- Token format: `Authorization: Bearer <token>`
- Token obtained from `/api/v1/auth/guest` or `/api/v1/auth/login`

### Issue 3: 404 on Mock Test Creation
**Error**: `No questions available for topic`

**Solution**:
- Database needs to be populated with questions
- Run the question importer scripts
- Or test with a different topic that has questions

### Issue 4: Test User Not Found
**Error**: `Incorrect email or password`

**Solution**:
- Create test user via `/api/v1/auth/register`
- Or use guest authentication instead
- Check database for existing users

---

## API Documentation Links

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- **OpenAPI JSON**: `http://localhost:8001/openapi.json`

---

## Authentication Flow

### Guest User Flow:
1. POST `/api/v1/auth/guest` → Get token
2. Use token for all authenticated endpoints

### Registered User Flow:
1. POST `/api/v1/auth/register` → Create account
2. POST `/api/v1/auth/login` → Get token
3. Use token for all authenticated endpoints

### Token Usage:
```bash
# Example curl command
curl -X GET "http://localhost:8001/api/v1/dashboard" \
  -H "Authorization: Bearer <your_token_here>"
```

---

## Performance Benchmarks (Expected)

| Endpoint | Expected Response Time | Notes |
|----------|------------------------|-------|
| GET / | < 50ms | Simple JSON response |
| GET /api/v1/exams/ | < 200ms | Database query |
| POST /api/v1/auth/guest | < 300ms | DB query + hash check |
| POST /api/v1/auth/login | < 300ms | DB query + hash verification |
| GET /api/v1/dashboard | < 500ms | Multiple DB queries + aggregations |
| POST /api/v1/mock-test/start (cached) | < 100ms | Redis cache hit |
| POST /api/v1/mock-test/start (uncached) | 2-5s | RAG pipeline + AI generation |

---

## Database Requirements

### Minimum Data for Testing:

1. **Users Table**:
   - Guest user (auto-created)
   - Test user (optional)

2. **Exams Table**:
   - At least 1 exam

3. **Subjects Table**:
   - At least 1 subject linked to exam

4. **Topics Table**:
   - At least 1 topic linked to subject

5. **Questions Table**:
   - At least 5-10 questions per topic for mock tests

### Database Initialization:
```bash
cd studypulse/backend
python -m app.core.database  # Initialize tables
python check_db.py  # Verify data
```

---

## Environment Variables (Railway)

Required variables for production deployment:

```env
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key-here
OLLAMA_BASE_URL=http://ollama:11434
REDIS_URL=redis://...
CORS_ORIGINS=https://your-frontend.com,http://localhost:3000
RAG_ENABLED=true
STAR_THRESHOLD_PERCENTAGE=70
```

---

## Next Steps

1. **Run the test script** to get actual results
2. **Check the summary table** for pass/fail status
3. **Review error messages** for any failed endpoints
4. **Verify database** has required data
5. **Test Railway production** separately
6. **Monitor logs** for any warnings or errors

---

## Contact & Support

For issues or questions about the API:
- Check logs: `studypulse/backend/logs/`
- Review FastAPI docs: `http://localhost:8001/docs`
- Check database: `python check_db.py`
