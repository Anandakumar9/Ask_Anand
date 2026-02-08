# Question Rating & Leaderboard Feature Implementation

## 🎉 New Features Implemented

This document summarizes all the new features added to StudyPulse to improve question quality through user ratings and increase engagement through competitive leaderboards.

---

## 📊 1. AI Question Rating System (1-10 Scale)

### Backend Implementation

#### **New API Endpoints** (`backend/app/api/question_rating.py`)

**POST /api/v1/questions/rate** - Rate an AI-generated question
```python
{
    "question_id": 123,
    "rating": 8,  # 1-10 scale
    "feedback_text": "Great question! Very relevant to exam pattern."
}
```

Response:
```json
{
    "question_id": 123,
    "your_rating": 8,
    "avg_rating": 7.8,
    "rating_count": 25,
    "message": "🌟 Thanks! Your feedback helps us generate better questions."
}
```

**GET /api/v1/questions/quality-stats/{prompt_version}** - Get quality statistics for semantic kernel
```json
{
    "prompt_version": "v2.1",
    "total_questions": 500,
    "avg_rating": 7.8,
    "ratings_distribution": {
        "1": 5, "2": 10, "3": 20, "4": 30, "5": 50,
        "6": 70, "7": 100, "8": 120, "9": 70, "10": 25
    },
    "low_quality_count": 65,
    "high_quality_count": 215,
    "quality_percentage": 43.0,
    "sample_feedback": [
        "Question too easy for JEE level",
        "Excellent question on Newton's laws"
    ]
}
```

**GET /api/v1/questions/compare-prompts?version_a=v2.0&version_b=v2.1** - A/B test prompt versions
```json
{
    "version_a": {...quality_stats...},
    "version_b": {...quality_stats...},
    "winner": "v2.1",
    "improvement_percentage": 12.5
}
```

**GET /api/v1/questions/low-quality-questions** - Get questions needing review
```json
[
    {
        "question_id": 456,
        "question_text": "What is the capital of...",
        "avg_rating": 3.2,
        "rating_count": 15,
        "prompt_version": "v2.0",
        "feedback_samples": ["Too easy", "Irrelevant"]
    }
]
```

#### **Updated Database Model** (`backend/app/models/question.py`)

**QuestionRating Model:**
```python
- rating: Integer (1-10 scale, was 1-5)
- feedback_text: Text (optional user feedback)
- prompt_version: String (tracks which prompt generated the question)
- created_at: DateTime
```

**Question Model Additions:**
```python
- avg_rating: Float (average rating from all users)
- rating_count: Integer (total number of ratings)
- metadata_json: JSONB (stores prompt_version, generation_time, etc.)
```

#### **Pydantic Schemas** (`backend/app/schemas/question_rating.py`)
- `RateQuestionRequest` - Input validation (1-10 rating)
- `QuestionRatingResponse` - Return rating stats
- `QuestionQualityStats` - Analytics for prompt optimization
- `PromptComparisonResponse` - A/B testing results

---

### Mobile Implementation

#### **Question Rating Widget** (`mobile/lib/widgets/question_rating_widget.dart`)

**Features:**
- ⭐ 1-10 star rating selector (tap stars to rate)
- 📝 Optional text feedback (200 char limit)
- 🎨 Color-coded ratings:
  - Red (1-4): Poor Quality
  - Orange (5-6): Needs Improvement
  - Light Green (7-8): Good
  - Green (9-10): Excellent
- ✅ Success confirmation after submission
- 🚫 Only shown for AI-generated questions

**Integration in Results Screen:**
```dart
// Shows rating widget for each AI question
QuestionRatingWidget(
  questionId: question['id'],
  questionText: question['question_text'],
  isAIGenerated: true,
)
```

---

## 🏆 2. Competitive Leaderboard

### Backend Implementation

#### **API Endpoints** (`backend/app/api/leaderboard.py`)

**GET /api/v1/leaderboard/topic/{topic_id}** - Get topic leaderboard
```json
{
    "entries": [
        {
            "rank": 1,
            "display_name": "TopStudent_123",
            "avg_score": 92.5,
            "total_stars": 15,
            "tests_completed": 20,
            "is_current_user": false,
            "medal": "🥇"
        },
        // ... up to 100 entries
    ],
    "total_participants": 500,
    "user_rank": 25,
    "user_entry": {...your_stats...}
}
```

**GET /api/v1/leaderboard/my-rank/{topic_id}** - Get user's ranking
```json
{
    "rank": 25,
    "avg_score": 78.5,
    "total_stars": 8,
    "tests_completed": 12,
    "percentile": 95.0,
    "rank_display": "#25 (Top 5%)"
}
```

**POST /api/v1/leaderboard/update-display-name** - Update public username
```json
{
    "display_name": "CoolStudent_99"
}
```

**POST /api/v1/leaderboard/toggle-visibility** - Show/hide on leaderboard
```json
{
    "is_public": false  // Hide from leaderboard
}
```

#### **Database Enhancements**

**New Columns in Users Table:**
```sql
ALTER TABLE users ADD COLUMN display_name VARCHAR(50) DEFAULT 'Guest_' || id;
ALTER TABLE users ADD COLUMN is_public BOOLEAN DEFAULT TRUE;
```

**Leaderboard View:**
```sql
CREATE VIEW leaderboard_by_topic AS
SELECT 
    topic_id,
    user_id,
    display_name,
    AVG(score_percentage) as avg_score,
    SUM(CASE WHEN star_earned THEN 1 ELSE 0 END) as total_stars,
    COUNT(*) as tests_taken,
    RANK() OVER (PARTITION BY topic_id ORDER BY AVG(score_percentage) DESC) as rank
FROM mock_tests
GROUP BY topic_id, user_id, display_name;
```

**16 Performance Indexes Created:**
- Questions: topic_id, source, (topic_id, source), difficulty
- Mock tests: user_id, topic_id, status, star_earned, created_at
- Study sessions: user_id, topic_id, started_at
- Topics/Subjects: subject_id, exam_id
- Responses: test_id, question_id

---

### Mobile Implementation

#### **Leaderboard Screen** (`mobile/lib/screens/leaderboard_screen.dart`)

**Features:**
- 🥇🥈🥉 Medal emojis for top 3
- 📊 Your Rank Card (highlighted)
  - Rank with medal
  - Average score percentage
  - Percentile (Top X%)
- 📋 Top 100 performers list
- 🔄 Pull-to-refresh
- 👤 "You" badge on your entry
- 🏆 Trophy icon header

**Navigation:**
- Added to Dashboard tab (`home_screen.dart`)
- Shows as card after stats section
- Only visible if user has an active study topic

---

## 🌟 3. Rate Us Dialog

### Implementation (`mobile/lib/widgets/rate_us_dialog.dart`)

**Smart Triggers:**
- Shows after 3rd completed test
- Never shows if already rated
- Respects 7-day dismissal cooldown
- Auto-increments test counter

**Features:**
- ⭐ 5-star visualization
- 🤖 Play Store button (Android)
- 🍎 App Store button (iOS)
- 🕐 "Maybe Later" option
- 🔒 Tracks dismissals in SharedPreferences

**Integration:**
```dart
// Auto-triggered in results_screen.dart
await RateUsDialog.incrementTestsCompleted();
RateUsDialog.showIfEligible(context);
```

**Store URLs:**
```dart
// Update these before publishing
static const playStoreUrl = 'https://play.google.com/store/apps/details?id=com.studypulse.app';
static const appStoreUrl = 'https://apps.apple.com/app/studypulse/id1234567890';
```

---

## 🔧 Updated Files

### Backend
1. ✅ `backend/app/models/question.py` - Updated QuestionRating model (1-10 scale)
2. ✅ `backend/app/api/question_rating.py` - NEW: Rating endpoints
3. ✅ `backend/app/schemas/question_rating.py` - NEW: Rating schemas
4. ✅ `backend/app/api/leaderboard.py` - NEW: Leaderboard endpoints
5. ✅ `backend/app/schemas/leaderboard.py` - NEW: Leaderboard schemas
6. ✅ `backend/app/api/__init__.py` - Export question_rating_router
7. ✅ `backend/app/main.py` - Include rating router
8. ✅ `backend/app/api/mock_test.py` - Updated TestResult schema (added id, source to QuestionResult)
9. ✅ `backend/app/schemas/mock_test.py` - Updated QuestionResult with id field
10. ✅ `backend/scripts/migrate_database.py` - Adds rating columns, leaderboard views

### Mobile
1. ✅ `mobile/lib/screens/leaderboard_screen.dart` - NEW: Leaderboard UI
2. ✅ `mobile/lib/widgets/rate_us_dialog.dart` - NEW: Rate us dialog
3. ✅ `mobile/lib/widgets/question_rating_widget.dart` - NEW: Rating widget
4. ✅ `mobile/lib/screens/results_screen.dart` - Added rating UI + rate us trigger
5. ✅ `mobile/lib/screens/home_screen.dart` - Added leaderboard link
6. ✅ `mobile/lib/api/api_service.dart` - Added rating + leaderboard methods
7. ✅ `mobile/pubspec.yaml` - Added url_launcher dependency

---

## 🚀 How to Use

### 1. Run Database Migration
```powershell
cd studypulse/backend
python scripts/migrate_database.py
```

This creates:
- Rating columns in questions table
- Display name + visibility columns in users table
- Leaderboard database view
- 16 performance indexes

### 2. Install Mobile Dependencies
```powershell
cd studypulse/mobile
flutter pub get
```

### 3. Start the System
Use the one-command startup:
```powershell
cd studypulse
.\LAUNCH_STUDYPULSE.ps1
```

Or manually:
```powershell
# Start Redis
docker run -d -p 6379:6379 --name studypulse-redis redis:7-alpine

# Start Qdrant
docker run -d -p 6333:6333 --name studypulse-qdrant qdrant/qdrant:v1.7.3

# Start backend
cd backend
uvicorn app.main:app --reload

# Start mobile
cd ../mobile
flutter run -d chrome
```

---

## 📊 Semantic Kernel Integration

### Using Ratings to Improve Question Generation

1. **Fetch Quality Stats:**
```python
GET /api/v1/questions/quality-stats/v2.1
```

2. **Analyze Low-Quality Questions:**
```python
GET /api/v1/questions/low-quality-questions?max_avg_rating=4.0
```

3. **Compare Prompt Versions:**
```python
GET /api/v1/questions/compare-prompts?version_a=v2.0&version_b=v2.1
```

4. **Update Prompt Based on Feedback:**
```python
# In question_generator.py
if avg_rating < 5.0:
    # Add more constraints
    prompt += "\nFocus on exam-level difficulty"
    prompt += "\nEnsure questions match previous year patterns"
elif avg_rating > 8.0:
    # Keep this prompt style
    metadata['prompt_version'] = 'v2.1_high_quality'
```

### A/B Testing Workflow

1. Generate questions with prompt v2.0
2. Generate questions with prompt v2.1
3. Collect 100+ ratings for each
4. Compare using `/compare-prompts` endpoint
5. Winner becomes the default prompt
6. Iterate with v2.2 testing

---

## 🎯 Key Metrics to Track

### Question Quality
- Average rating per prompt version
- % of questions rated ≥8 (high quality)
- % of questions rated ≤4 (low quality)
- Rating count per question (engagement)
- Feedback sentiment analysis

### Leaderboard Engagement
- Daily active competitors
- Average ranking changes per week
- % of users opting out (visibility = false)
- Top performers retention rate

### Rate Us Dialog
- Conversion rate (shown → rated)
- Dismissal rate
- Average tests before first show (should be ~3)
- Days between dismissals

---

## 🔐 Privacy & Security

**Question Ratings:**
- Anonymous to other users (only your own visible)
- Can update rating anytime
- Feedback text is not moderated (max 500 chars)

**Leaderboard:**
- Display names are public (not real names)
- Default: Visible (`is_public = true`)
- Users can toggle visibility anytime
- Guest users: `Guest_<user_id>`

**Rate Us Dialog:**
- Stored locally (SharedPreferences)
- No server tracking
- Can be reset by clearing app data

---

## 🐛 Known Limitations

1. **Rating System:**
   - Can only rate AI questions (not previous year)
   - Rating is per user (can change anytime)
   - No bulk rating (must rate each question individually)

2. **Leaderboard:**
   - Top 100 only (performance optimization)
   - Rank calculated on-demand (not real-time cached)
   - Ties broken by tests_completed, then user_id

3. **Rate Us Dialog:**
   - Shows based on local counter (not synced with server)
   - If user clears app data, counter resets
   - No in-app review API (uses external links)

---

## 🎨 UI/UX Enhancements

### Colors
- **Rating Stars:** 1-4 (red), 5-6 (orange), 7-8 (light green), 9-10 (green)
- **Leaderboard:** Deep purple theme (matches "competitive" vibe)
- **Medals:** 🥇 Gold, 🥈 Silver, 🥉 Bronze
- **Rate Us:** Amber stars ⭐

### Animations
- Confetti for earning stars (existing)
- Smooth star selection (instant color change)
- Card elevation on leaderboard entry highlight

### Accessibility
- Large touch targets (stars are 28px)
- Clear labels and icons
- Error messages with retry options
- Loading states (CircularProgressIndicator)

---

## 📝 Future Enhancements

1. **Advanced Analytics:**
   - Question difficulty correlation with ratings
   - Time-to-answer vs rating analysis
   - User expertise level (beginner/intermediate/advanced) affects rating weight

2. **Gamification:**
   - Achievements for rating X questions
   - Leaderboard badges (🔥 Hot streak, 🎯 Perfect score, etc.)
   - Weekly challenges

3. **Social Features:**
   - Share leaderboard rank on social media
   - Friend challenges
   - Study groups with group leaderboards

4. **AI Improvements:**
   - Auto-disable low-rated questions (avg < 3.0)
   - Automatic prompt tuning based on ratings
   - Question difficulty prediction model

---

## ✅ Testing Checklist

### Backend
- [ ] POST /api/v1/questions/rate with valid rating (1-10)
- [ ] POST /api/v1/questions/rate with invalid rating (0, 11)
- [ ] GET /api/v1/questions/quality-stats/v1.0
- [ ] GET /api/v1/questions/compare-prompts
- [ ] GET /api/v1/leaderboard/topic/1
- [ ] GET /api/v1/leaderboard/my-rank/1
- [ ] POST /api/v1/leaderboard/update-display-name
- [ ] POST /api/v1/leaderboard/toggle-visibility

### Mobile
- [ ] Complete test with AI questions → See rating widgets
- [ ] Rate question 1-10 → Verify success message
- [ ] Submit optional feedback → Check backend
- [ ] View leaderboard → See top 100 + your rank
- [ ] Pull-to-refresh leaderboard
- [ ] Complete 3rd test → Rate us dialog appears
- [ ] Dismiss rate us → Doesn't show for 7 days
- [ ] Rate app → Never shows again
- [ ] Navigate from dashboard to leaderboard

---

## 🎓 Documentation

**For Developers:**
- API documentation: `/docs` (FastAPI Swagger)
- Database schema: `backend/supabase_schema.sql`
- Architecture: `ARCHITECTURE_DIAGRAMS.md`
- Migration guide: `backend/scripts/migrate_database.py`

**For Users:**
- How to use leaderboard: In-app (coming soon)
- How to rate questions: In-app tooltip
- Privacy policy: (to be created)

---

**Version:** 1.0.0  
**Last Updated:** February 6, 2026  
**Authors:** GitHub Copilot + Team StudyPulse

