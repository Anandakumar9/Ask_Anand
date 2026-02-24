# StudyPulse - Quick Start Guide

## 🚀 Status: Servers are Starting!

I've started all three servers for you:

1. ✅ **Backend Server** - Starting on port 8001
2. ✅ **Frontend (Next.js)** - Starting on port 3000
3. ✅ **Mobile App (Flutter)** - Compiling for port 8082

---

## ⏱️ Expected Startup Times

- **Backend**: ~20-30 seconds
- **Frontend**: ~5-10 seconds
- **Mobile App**: **2-3 minutes** (first time compilation)

---

## 🔍 Issues I Found & Fixed

### Issue 1: Frontend Blank Screen
**Root Cause**: The login page was returning `null` while waiting for state hydration from localStorage, causing a blank screen.

**What I Found**:
- Line 53 in `login/page.tsx`: `if (!mounted || !hasHydrated) return null;`
- This made the page completely blank while React was hydrating the Zustand store

**Fix Applied**: Changed to show a loading spinner instead of `null`

### Issue 2: Flutter Build Directory Locked
**Root Cause**: Previous Flutter process left build directory locked

**Fix Applied**:
- Killed all Dart/Flutter processes
- Force-removed build directory
- Started fresh compilation

---

## 📍 How to Access the Apps

### Option 1: Next.js Frontend (Recommended for Testing)
**URL**: http://localhost:3000

**Why use this?**
- Loads faster (5-10 seconds)
- Better error messages in console
- Easier to debug

**Test Steps**:
1. Wait ~10 seconds
2. Open: http://localhost:3000
3. You should see the login page with:
   - Email field (pre-filled: test@studypulse.com)
   - Password field (pre-filled: password123)
   - Login button
   - API status indicator at bottom

### Option 2: Flutter Mobile App (Web Version)
**URL**: http://localhost:8082

**Why use this?**
- Tests the actual mobile app code
- Same app that runs on Android/iOS

**Test Steps**:
1. Wait ~2-3 minutes for compilation
2. Open: http://localhost:8082
3. Should see the StudyPulse mobile app

### Option 3: Production (Vercel Frontend)
**URL**: https://studypulse-eta.vercel.app

This is the live production frontend connecting to Railway backend.

---

## ✅ How to Test the Complete User Flow

Once the frontend/mobile app loads (choose one):

### Step 1: Login
- **Option A**: Use pre-filled credentials and click "Login"
  - Email: test@studypulse.com
  - Password: password123

- **Option B**: Create new account (if Register button available)

- **Option C**: Guest Login (if available)

### Step 2: Navigate the App
Once logged in, you should see the dashboard with:
- Your stats (stars, streak, average score)
- Popular subjects
- Recent activity
- Bottom navigation bar

### Step 3: Start Study Session
1. Click on "Study" tab in bottom nav
2. Select a topic (e.g., "Banking Sector")
3. Set duration to **5 minutes**
4. Start the session
5. Timer counts down

### Step 4: Take Mock Test
1. From dashboard, click "Take Mock Test"
2. Select a topic
3. Answer 5-10 questions
4. Submit test

### Step 5: View Results
- See your score
- See explanations
- Stars earned

### Step 6: Rate Questions
- Rate 2-3 questions with 1-5 stars
- Add feedback if you want

### Step 7: Check Dashboard
- Go back to home/dashboard
- Verify stats updated:
  - Stars increased
  - Tests count increased
  - Study time shows +5 minutes

---

## 🐛 If You See Blank Screen

### Check 1: Open Browser Console
1. Press **F12**
2. Go to **Console** tab
3. Look for **red errors**

**Common Errors**:

#### "Failed to fetch" or "Network error"
**Solution**: Backend not ready yet, wait 30 more seconds

#### "CORS policy blocked"
**Solution**: This shouldn't happen with localhost, but if it does:
```powershell
cd studypulse/backend
# Check CORS_ORIGINS includes localhost:3000 and localhost:8082
```

#### "Cannot read property of null"
**Solution**: Page is still hydrating, wait a moment and refresh

### Check 2: Verify Servers are Running

Run this to check:
```powershell
# Check backend
curl http://localhost:8001

# Check frontend
curl http://localhost:3000

# Check mobile app
curl http://localhost:8082
```

All should return HTML/JSON, not errors.

### Check 3: Look at Server Windows

You should have **3 PowerShell windows** open:
1. Backend server - showing FastAPI logs
2. Frontend server - showing Next.js dev server
3. Mobile app - showing Flutter compilation

Look for any error messages in these windows.

---

## 📊 Expected Behavior (When Working)

### Frontend (http://localhost:3000)

**Login Page**:
```
+---------------------------+
|      StudyPulse          |
|                          |
| Email: [test@studypulse] |
| Password: [***********]  |
|                          |
| [      Login     ]       |
|                          |
| API: Connected (green)   |
+---------------------------+
```

**After Login**:
```
+---------------------------+
| Good Day, Test! 👋       |
| 📍 Andhra Pradesh        |
| [Search box]             |
+---------------------------+
| Continue studying or     |
| Get Started              |
+---------------------------+
| ⭐ 0    🔥 0    📈 0%   |
| Stars   Streak  Avg     |
+---------------------------+
| Popular Subjects         |
| [Geography] [History]    |
| [Polity]    [Economy]    |
+---------------------------+
```

### Browser Console (F12 → Console)
```
No red errors
Maybe some warnings (orange) - that's OK
API calls should show in Network tab
```

### Network Tab (F12 → Network)
```
GET  http://localhost:8001/api/v1/dashboard  200 OK
GET  http://localhost:8001/api/v1/exams/     200 OK
POST http://localhost:8001/api/v1/auth/login 200 OK
```

---

## 🎯 Testing Checklist

Use this to verify everything works:

```
□ Backend responds at http://localhost:8001
□ Frontend loads at http://localhost:3000
□ Login page displays (not blank)
□ Can see email and password fields
□ API status shows "Connected" (green dot)
□ Can click Login button
□ After login, redirects to dashboard
□ Dashboard shows stats and subjects
□ Can navigate using bottom nav bar
□ No red errors in browser console
□ Network tab shows successful API calls
```

---

## 🔧 Quick Commands

### Check Server Status
```powershell
# Windows
netstat -ano | findstr ":8001"  # Backend
netstat -ano | findstr ":3000"  # Frontend
netstat -ano | findstr ":8082"  # Mobile

# Test with curl
curl http://localhost:8001
curl http://localhost:3000
curl http://localhost:8082
```

### Restart Servers (if needed)
```powershell
# Stop all (close PowerShell windows or Ctrl+C)

# Restart backend
cd studypulse/backend
python -m uvicorn app.main:app --reload --port 8001

# Restart frontend
cd studypulse/frontend
npm run dev

# Restart mobile app
cd studypulse/mobile
flutter run -d web-server --web-port=8082
```

---

## 📁 Files & Tools Created

1. **diagnostic.html** - Comprehensive testing tool
2. **start_all.bat** - One-click server startup
3. **check_status.bat** - Quick status checker
4. **test_deployment.py** - Deployment verification
5. **test_e2e_complete_flow.py** - Full user flow test
6. **HOW_TO_RUN_MOBILE_APP.md** - Detailed mobile guide
7. **DEPLOYMENT_FIX_REPORT.md** - Deployment status
8. **FRONTEND_BLANK_SCREEN_FIX.md** - Debugging guide

---

## ✨ What's Next

**In ~20-30 seconds**:
1. Backend will be ready at http://localhost:8001
2. Frontend will be ready at http://localhost:3000

**In ~2-3 minutes**:
3. Mobile app will be ready at http://localhost:8082

**Then you can**:
- Test the complete user flow
- See the app working locally
- Verify all features (login, study, tests, results)

---

## 🆘 Still Having Issues?

**Run the diagnostic tool**:
```
Open: c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\diagnostic.html
```

This will:
- Test all API endpoints
- Show you exactly what's failing
- Give specific error messages

**Or check server logs**:
Look at the PowerShell windows for error messages.

**Or share the error**:
1. Press F12 in browser
2. Copy the red error from Console tab
3. Tell me what it says

---

## 🎉 Success Indicators

You'll know it's working when:

✅ Can see login page (not blank)
✅ API status shows "Connected"
✅ Can login and see dashboard
✅ No red errors in console
✅ Can navigate between pages
✅ Stats and data load correctly

---

**The servers are starting now. Give them 30 seconds - 3 minutes depending on which one you want to test!**

**I recommend starting with the Next.js frontend (http://localhost:3000) as it's fastest to load and easiest to debug.**
