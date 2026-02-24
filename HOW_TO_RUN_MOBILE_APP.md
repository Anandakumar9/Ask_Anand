# How to Run StudyPulse Mobile App - Complete Guide

## 🎯 Quick Start (Easiest Option)

### Option 1: Run on Web Browser (Recommended for Testing)

This is the **fastest and easiest** way to test the mobile app:

**Step 1: Start the Backend (if not already running)**
```powershell
# Open PowerShell Terminal 1
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend
python -m uvicorn app.main:app --reload --port 8001 --host 0.0.0.0
```

**Step 2: Start the Mobile App**
```powershell
# Open PowerShell Terminal 2 (NEW WINDOW)
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
flutter run -d web-server --web-port=8082 --web-hostname=0.0.0.0
```

**Step 3: Wait for Compilation**
- First run takes 2-3 minutes (Flutter needs to compile)
- You'll see: `Running on http://localhost:8082`
- The PowerShell window will stay open (don't close it)

**Step 4: Open in Browser**
```
Open: http://localhost:8082
```

---

## 🎯 Option 2: Run on Android Emulator

### Prerequisites Check
```powershell
# Check if Android emulator is installed
flutter doctor

# List available emulators
flutter emulators

# List available devices
flutter devices
```

### Start Android Emulator
```powershell
# Option A: Start default emulator
flutter emulators --launch <emulator_name>

# Option B: Start any emulator from Android Studio
# Open Android Studio > Tools > AVD Manager > Click Play button
```

### Run App on Emulator
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile

# Run on connected emulator/device
flutter run
```

The app will automatically detect the emulator and install.

---

## 🎯 Option 3: Run on Physical Android Device

### Enable USB Debugging on Your Phone
1. Go to **Settings** > **About Phone**
2. Tap **Build Number** 7 times (enables Developer Mode)
3. Go back to **Settings** > **Developer Options**
4. Enable **USB Debugging**
5. Connect phone to PC via USB cable
6. Allow USB debugging when prompted on phone

### Run App on Phone
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile

# Check if device is detected
flutter devices

# Run on connected device
flutter run
```

---

## 🧪 Complete User Flow Testing Guide

Once the app is running, follow these steps to test the complete user flow:

### Step 1: Guest Login / Authentication
1. Open the app (http://localhost:8082 or on device)
2. You should see the **Login/Welcome screen**
3. Click **"Continue as Guest"** or **"Guest Login"** button
4. ✅ **Expected**: Logged in successfully, redirected to home/dashboard

---

### Step 2: Explore All Sessions (Navigation Test)

**2.1 Home/Dashboard**
- Check if you can see:
  - Your stats (stars, study time, tests taken)
  - Recent activity
  - Quick action buttons
- ✅ **Expected**: Dashboard loads with all widgets

**2.2 Study Session**
- Tap on **"Study"** or **"Start Study"** tab/button
- ✅ **Expected**: See list of available topics/exams
  - Banking Sector
  - Fiscal Policy
  - Constitution
  - Ancient India
  - Cardiovascular System
  - Upper Limb

**2.3 Rank/Leaderboard**
- Tap on **"Rank"** or **"Leaderboard"** tab
- ✅ **Expected**: See leaderboard with user rankings

**2.4 Profile**
- Tap on **"Profile"** tab
- ✅ **Expected**: See user information, achievements, settings

---

### Step 3: Start Study Session (5 Minutes)

1. Go to **Study** section
2. Select a topic (e.g., **"Banking Sector"** or **"Fiscal Policy"**)
3. Set duration to **5 minutes**
4. Tap **"Start Study Session"**
5. ✅ **Expected**:
   - Timer starts counting down from 5:00
   - Session is active
   - You can see the timer updating

**IMPORTANT**: Let it run for the full 5 minutes! This tests:
- Real-time session tracking
- Data persistence
- Session completion logic

---

### Step 4: End Study Session

**After 5 minutes:**
1. Timer should reach 0:00
2. Either:
   - Click **"End Session"** button, OR
   - Timer expires automatically
3. ✅ **Expected**:
   - Session ends
   - You might see a success message
   - Possibly redirected to questions or results

---

### Step 5: Take Mock Test

1. From home/dashboard, tap **"Take Mock Test"** or **"Start Exam"**
2. Select a topic (same as before: Banking, Fiscal Policy, etc.)
3. Tap **"Start Test"**
4. ✅ **Expected**: Questions appear (5-10 questions)

**Answer the questions:**
- Read each question
- Select an answer (A, B, C, or D)
- Move to next question
- Continue until all questions answered

5. Tap **"Submit Test"** when done
6. ✅ **Expected**: Test submitted successfully

---

### Step 6: View Results

**After submitting the test:**
1. You should automatically see the **Results Screen**
2. ✅ **Check these details**:
   - Your score (e.g., 4/5, 3/5)
   - Percentage (e.g., 80%, 60%)
   - Stars earned (based on performance)
   - List of questions with:
     - Your answer
     - Correct answer
     - ✅ or ❌ indicator
     - **Explanation** for each question

---

### Step 7: Rate AI-Generated Questions

**On the results screen:**
1. Look for **"Rate this question"** or star rating icons
2. Rate 2-3 questions:
   - Tap the stars (1-5 stars)
   - Optionally add feedback/comments
3. ✅ **Expected**:
   - Rating saved
   - Visual confirmation (e.g., "Thank you for rating!")

---

### Step 8: Check Dashboard Analytics

1. Go back to **Dashboard/Home** screen
2. ✅ **Verify these metrics have updated**:
   - **Total Stars Earned**: Should show new stars from the test
   - **Total Tests Taken**: Should increment by 1
   - **Average Score/Accuracy**: Should reflect your test score
   - **Total Study Time**: Should show 5 minutes added
   - **Performance Trends**: Graphs/charts should update
   - **Recent Tests**: Your test should appear in recent activity
   - **Recent Sessions**: Your 5-minute study session should appear

---

## 🎮 Testing Checklist

Use this checklist while testing:

### Authentication
- [ ] App opens successfully
- [ ] Guest login button visible
- [ ] Guest login works (no errors)
- [ ] Redirected to home after login

### Navigation
- [ ] Home/Dashboard tab works
- [ ] Study tab works
- [ ] Rank/Leaderboard tab works
- [ ] Profile tab works
- [ ] All screens load without errors

### Study Session
- [ ] Can see list of topics
- [ ] Can select a topic
- [ ] Can set duration to 5 minutes
- [ ] Study session starts
- [ ] Timer counts down correctly
- [ ] Can end session manually
- [ ] Session data is saved

### Mock Test
- [ ] Can start a mock test
- [ ] Questions load (5-10 questions)
- [ ] Can select answers
- [ ] Can navigate between questions
- [ ] Can submit test
- [ ] No errors during test

### Results
- [ ] Results screen appears
- [ ] Score is displayed correctly
- [ ] Percentage is calculated
- [ ] Stars are shown
- [ ] Correct/incorrect answers marked
- [ ] Explanations are provided
- [ ] Explanations are relevant

### Rating
- [ ] Can see rating options
- [ ] Can rate questions (1-5 stars)
- [ ] Can add feedback (optional)
- [ ] Rating is saved
- [ ] Confirmation message appears

### Dashboard Update
- [ ] Total stars updated
- [ ] Total tests incremented
- [ ] Average score updated
- [ ] Study time updated (+5 minutes)
- [ ] Recent tests shows latest test
- [ ] Recent sessions shows study session
- [ ] Performance trends updated

---

## 🐛 Troubleshooting

### Problem: Flutter command not found
**Solution:**
```powershell
# Add Flutter to PATH or use full path
C:\src\flutter\bin\flutter.bat run -d web-server --web-port=8082
```

### Problem: Port 8082 already in use
**Solution:**
```powershell
# Use a different port
flutter run -d web-server --web-port=8083

# Or kill existing process
netstat -ano | findstr :8082
taskkill /PID <process_id> /F
```

### Problem: Backend not responding
**Solution:**
```powershell
# Make sure backend is running
curl http://localhost:8001

# Restart backend if needed
cd studypulse/backend
python -m uvicorn app.main:app --reload --port 8001
```

### Problem: "No devices found"
**Solution:**
```powershell
# For web browser
flutter run -d chrome

# For web server
flutter run -d web-server

# List all available devices
flutter devices
```

### Problem: App shows blank white screen
**Solution:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Refresh the page (Ctrl + F5)
4. Clear browser cache
5. Make sure backend is running on port 8001

### Problem: API errors / Can't fetch exams
**Solution:**
1. Check backend is running: http://localhost:8001
2. Check API URL in code:
   ```dart
   // Should point to Railway for production or localhost for dev
   _devBaseUrlWeb = 'http://localhost:8001/api/v1'
   ```
3. Check browser console for CORS errors

---

## 🚀 Quick Commands Reference

### Start Everything (3 terminals)

**Terminal 1 - Backend:**
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - Mobile App:**
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
flutter run -d web-server --web-port=8082
```

**Terminal 3 - Open Browser:**
```powershell
start http://localhost:8082
```

### Check Status
```powershell
# Check backend
curl http://localhost:8001

# Check mobile app
curl http://localhost:8082

# Check Flutter devices
flutter devices

# Check Flutter doctor
flutter doctor
```

### Stop Everything
```powershell
# Stop backend - Press Ctrl+C in backend terminal

# Stop mobile app - Press 'q' in Flutter terminal or Ctrl+C

# Or kill all processes
taskkill /IM python.exe /F
taskkill /IM dart.exe /F
```

---

## 🎯 Expected Results

### Successful Test Completion

After completing the full user flow, you should have:

✅ **Successfully logged in** as guest
✅ **Navigated** through all 4 tabs (Home, Study, Rank, Profile)
✅ **Started** a 5-minute study session
✅ **Completed** the 5-minute study session
✅ **Taken** a mock test with 5-10 questions
✅ **Viewed** results with scores and explanations
✅ **Rated** 2-3 questions with feedback
✅ **Verified** dashboard updated with:
   - New stars earned
   - Test count increased
   - Study time increased by 5 minutes
   - Recent activity shows your test and session

### Data That Should Persist

Go back to the backend database and verify:
```powershell
cd studypulse/backend
python check_db.py
```

You should see:
- Your user record
- Study session record (5 minutes)
- Test record with scores
- Question ratings

---

## 📱 Production Testing (Using Railway Backend)

If you want to test with the **production backend** instead of localhost:

**Edit the mobile app config:**
```dart
// File: studypulse/mobile/lib/api/api_service.dart
// Change this line temporarily:
static const String _devBaseUrlWeb = 'https://askanand-simba.up.railway.app/api/v1';
```

Then run the app same as before. This will use the Railway backend instead of local backend.

**Don't forget to change it back to localhost for local development!**

---

## 🎓 Tips for Best Testing Experience

1. **Use Chrome Browser** for web testing (best DevTools)
2. **Open Browser Console** (F12) to see any errors
3. **Take your time** - let the 5-minute study session complete
4. **Try different topics** - test multiple exams
5. **Check network tab** in DevTools to see API calls
6. **Test on real device** if possible for best mobile experience
7. **Clear app data** between tests if needed

---

## ✅ Quick Verification

After starting the app, verify these URLs are working:

**Backend:**
- http://localhost:8001 - Should show welcome message
- http://localhost:8001/docs - Should show API documentation

**Mobile App:**
- http://localhost:8082 - Should show StudyPulse app

**If both are working, you're ready to test!** 🚀

---

## 📞 Need Help?

If you encounter any issues:

1. Check backend logs in Terminal 1
2. Check Flutter logs in Terminal 2
3. Check browser console (F12 > Console tab)
4. Try refreshing the page
5. Restart the app (Ctrl+C and run again)

---

**Happy Testing!** 🎉

Your StudyPulse app is fully functional and ready for comprehensive testing!
