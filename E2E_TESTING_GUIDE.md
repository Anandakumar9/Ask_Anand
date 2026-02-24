# StudyPulse Complete End-to-End Testing Guide

## Overview
This guide provides comprehensive instructions for testing the complete StudyPulse application flow, including Backend API, Mobile App, and RAG Pipeline.

---

## Prerequisites

### 1. Start Backend Server
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend
python -m uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
```

### 2. Start Mobile App
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
flutter run -d web-server --web-port=8082 --web-hostname=0.0.0.0
```

### 3. Verify Servers are Running
- Backend:  [http://localhost:8001/docs](http://localhost:8001/docs)
- Mobile App: [http://localhost:8082](http://localhost:8082)

---

## Automated Test (Recommended)

### Quick Test
Run the automated E2E test script:
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand
python test_e2e_complete_flow.py
```

### With Custom Study Duration
Run with a specific study session duration (e.g., 2 minutes for quick test):
```powershell
python test_e2e_complete_flow.py 2
```

The automated test will:
- ✓ Test guest login
- ✓ Navigate through all sessions
- ✓ Start and monitor study session (with real-time waiting)
- ✓ End study session and verify data persistence
- ✓ Take a mock exam with random answers
- ✓ View results with explanations
- ✓ Rate AI-generated questions
- ✓ Check dashboard analytics (accuracy, performance, stars)

**Expected Duration**: ~5-8 minutes (depending on study session duration)

---

## Manual Testing (Alternative)

If you prefer to test manually, follow these steps:

### Step 1: Guest Login / Authentication
**Objective**: Verify user authentication works

1. Open mobile app: [http://localhost:8082](http://localhost:8082)
2. Click "Continue as Guest" or "Guest Login"
3. **Expected**: You should be logged in and see the home screen

**API Test (Alternative)**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/guest \
  -H "Content-Type: application/json" \
  -d "{}"
```
**Expected**: Response with `access_token` and `user_id`

---

### Step 2: Navigate Through All Sessions
**Objective**: Verify all navigation routes work

1. **Home/Dashboard**: Check the main dashboard displays
   - View your stats (stars, study time, tests taken)
   - See recent activity

2. **Study Session**: Go to "Start Study" or study section
   - Should see list of available topics/exams
   - Should be able to select a topic

3. **Rank/Leaderboard**: Go to leaderboard section
   - Should see ranking of users
   - Should see your rank

4. **Profile**: Go to profile section
   - Should see user information
   - Should see achievements/badges

**Expected**: All screens should load without errors

---

### Step 3: Start Study Session (5 Minutes)
**Objective**: Verify study session can be started and tracked

1. From the Study section, select a topic (e.g., "Banking Sector")
2. Set duration to **5 minutes**
3. Click "Start Study Session"
4. **Monitor the session**:
   - Timer should be counting down
   - Session should be tracked in the backend
5. **DO NOT SKIP** - Let the timer run for the full 5 minutes
   - This tests the complete session lifecycle
   - This ensures data persistence works correctly

**API Test (Alternative)**:
```bash
# Get available exams
curl -X GET http://localhost:8001/api/v1/exams/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Start session (replace EXAM_ID)
curl -X POST http://localhost:8001/api/v1/study/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"exam_id": 1, "duration_seconds": 300}'
```

**Expected**:
- Session starts successfully
- Timer is visible and counting down
- Session status is "active"

---

### Step 4: End Study Session
**Objective**: Verify session ends correctly and data persists

1. After 5 minutes, click "End Session" (or let timer expire)
2. **Expected**:
   - Session should end
   - You might be redirected to a results or question screen
   - Session data should be saved

**API Test (Alternative)**:
```bash
# End session (replace SESSION_ID)
curl -X POST http://localhost:8001/api/v1/study/sessions/SESSION_ID/complete \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
- Session marked as complete
- Study time recorded
- Possible questions generated

---

### Step 5: Take Mock Test
**Objective**: Verify mock test flow and RAG question generation

1. From home or tests section, click "Take Mock Test"
2. Select a topic (e.g., "Banking Sector")
3. Start the test
4. **Answer all questions**:
   - Read each question carefully
   - Select answers (random or thoughtful)
   - Move through all questions
5. Submit the test

**API Test (Alternative)**:
```bash
# Start mock test
curl -X POST http://localhost:8001/api/v1/mock-tests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"exam_id": 1, "question_count": 5}'

# Submit test (replace TEST_ID and add your answers)
curl -X POST http://localhost:8001/api/v1/mock-tests/TEST_ID/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"answers": [{"question_id": 1, "selected_answer": "A"}]}'
```

**Expected**:
- Test starts with questions loaded
- Questions display correctly
- Can submit answers
- Test submits successfully

---

### Step 6: View Results
**Objective**: Verify results display correctly with explanations

1. After submitting test, view the results screen
2. **Check the following**:
   - Your score (e.g., 4/5)
   - Percentage (e.g., 80%)
   - Stars earned (if applicable)
   - Correct/incorrect answers marked
   - **Explanations for each question**
   - Right answer highlighted

**API Test (Alternative)**:
```bash
# Get test results (replace TEST_ID)
curl -X GET http://localhost:8001/api/v1/mock-tests/TEST_ID/results \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
- Detailed results with score
- Correct answers shown
- Explanations provided
- Stars calculated correctly

---

### Step 7: Rate AI-Generated Questions
**Objective**: Verify question rating functionality

1. On the results screen or question review screen
2. Find the rating option (e.g., "Rate this question" or star icons)
3. **Rate 2-3 questions**:
   - Give ratings from 1-5 stars
   - Optionally add feedback/comments
4. Submit ratings

**API Test (Alternative)**:
```bash
# Rate a question (replace QUESTION_ID)
curl -X POST http://localhost:8001/api/v1/questions/QUESTION_ID/rate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"rating": 5, "feedback": "Great question!"}'
```

**Expected**:
- Rating saves successfully
- Feedback is recorded
- UI updates to show rating submitted

---

### Step 8: Check Dashboard Analytics
**Objective**: Verify dashboard shows historical data correctly

1. Go back to the **Dashboard/Home** screen
2. **Verify the following metrics are updated**:
   - **Total stars earned**: Should include stars from the mock test
   - **Total tests taken**: Should increment by 1
   - **Average score/accuracy**: Should reflect your test score
   - **Study time**: Should include the 5-minute session
   - **Performance trends**: Check if graphs/charts update
   - **Recent tests**: Your test should appear in recent activity
   - **Recent sessions**: Your study session should appear

**API Test (Alternative)**:
```bash
# Get dashboard data
curl -X GET http://localhost:8001/api/v1/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected**:
- All metrics updated correctly
- Historical data visible
- Recent activity shows your test and session
- Performance trends reflect your progress

---

## Verification Checklist

### Backend API Tests
- [ ] Background server running on port 8001
- [ ] Guest login endpoint works
- [ ] Can fetch exams list
- [ ] Can start study session
- [ ] Can end study session
- [ ] Can start mock test
- [ ] Can submit mock test
- [ ] Can get test results
- [ ] Can rate questions
- [ ] Can get dashboard data

### Mobile App Tests
- [ ] Mobile app running on port 8082
- [ ] App loads without errors
- [ ] Can navigate to all screens
- [ ] Study timer works correctly
- [ ] Mock test UI works
- [ ] Results screen displays
- [ ] Rating feature works
- [ ] Dashboard updates

### RAG Pipeline Tests
- [ ] Questions are generated
- [ ] Questions have explanations
- [ ] Questions are relevant to topic
- [ ] Quality of AI-generated content is good

### Data Persistence Tests
- [ ] Study session time is saved
- [ ] Test scores are recorded
- [ ] Stars are calculated and saved
- [ ] Dashboard reflects all activities
- [ ] Historical data is accurate

### End-to-End User Flow
- [ ] Complete flow from login to dashboard works
- [ ] No errors or crashes
- [ ] All features are functional
- [ ] Data is consistent across components

---

## Common Issues and Troubleshooting

### Backend Not Starting
**Symptoms**: Can't access http://localhost:8001
**Solutions**:
1. Check if port 8001 is already in use:
   ```powershell
   netstat -ano | findstr :8001
   ```
2. Kill existing process if needed
3. Check if Python virtual environment is activated
4. Install dependencies: `pip install -r requirements.txt`
5. Check database file exists: `studypulse.db`

### Mobile App Not Starting
**Symptoms**: Can't access http://localhost:8082
**Solutions**:
1. Check if Flutter is installed: `flutter doctor`
2. Check if port 8082 is available
3. Run `flutter clean` then `flutter pub get`
4. Check for errors in Flutter console

### API Returns 401/403 Errors
**Symptoms**: Authentication errors
**Solutions**:
1. Check if token is valid
2. Try guest login again
3. Check CORS settings in backend
4. Verify Authorization header is correctly formatted

### Questions Not Generated
**Symptoms**: No questions after study session or mock test
**Solutions**:
1. Check if database has questions: `python check_db.py`
2. Run seed script: `python seed_demo_data.py`
3. Check if RAG pipeline is enabled in `.env`
4. Check Ollama is running (if using AI generation)

### Dashboard Not Updating
**Symptoms**: Stats don't change after tests
**Solutions**:
1. Refresh the page/app
2. Check if data was actually saved (check API directly)
3. Check browser console for errors
4. Verify session token is still valid

---

## Performance Benchmarks

### Expected Response Times
- Guest login: < 500ms
- Fetch exams: < 300ms
- Start session: < 500ms
- End session: < 1s (with question generation)
- Start mock test: < 2s (with question loading)
- Submit test: < 1s
- Get results: < 500ms
- Dashboard: < 800ms

### Expected Behavior
- Study timer should count down smoothly
- No UI freezes or crashes
- All navigation should be instant
- Questions should load without delay

---

## Test Data

### Default Test Users
- Guest users are created automatically
- Each guest session is independent

### Sample Topics/Exams
- Banking Sector
- Fiscal Policy
- Constitution
- Ancient India
- Cardiovascular System
- Upper Limb

---

## Advanced Testing

### Load Testing
Test with multiple concurrent users:
```bash
# Use tools like Apache Bench or Locust
ab -n 100 -c 10 http://localhost:8001/api/v1/exams/
```

### API Documentation
Full API docs available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## Reporting Issues

If you find bugs or issues during testing:

1. **Note the exact steps** to reproduce
2. **Check browser console** for errors (F12 > Console)
3. **Check backend logs** in the terminal
4. **Note the error message** and status code
5. **Document expected vs actual behavior**

---

## Success Criteria

### Test Considered Successful If:
- ✓ All 8 test steps complete without errors
- ✓ Data persists correctly across the flow
- ✓ Dashboard reflects all activities
- ✓ No console errors or warnings
- ✓ App performs smoothly
- ✓ RAG questions are generated correctly

---

## Next Steps After Testing

1. **If all tests pass**: Application is ready for production
2. **If some tests fail**: Review error logs and fix issues
3. **Document any bugs** found
4. **Retest after fixes**
5. **Deploy to production** once all tests pass

---

## Contact & Support

- Check backend logs for detailed error messages
- Check mobile app console for frontend errors
- Review API documentation at `/docs` endpoint

---

**Good luck with testing! 🚀**
