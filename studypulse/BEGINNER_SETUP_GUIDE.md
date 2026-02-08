# 🚀 StudyPulse - Complete Setup Guide for Beginners

**Welcome!** This guide will help you set up StudyPulse from scratch. Don't worry if you're new to coding - just follow these simple steps!

---

## 📱 What You're Building

StudyPulse is an AI-powered exam prep app with:
- **Mobile App** (Android/iOS) - For students to use
- **Backend** (Server) - Handles all the logic
- **AI System** - Generates exam questions automatically
- **Database** (Supabase) - Stores all data in the cloud

---

## ✅ Before You Start

Make sure you have these installed:

### 1. Python (for Backend)
- Download: https://www.python.org/downloads/
- Version: 3.10 or higher
- ✓ Check if installed: Open PowerShell and type `python --version`

### 2. Flutter (for Mobile App)
- Download: https://docs.flutter.dev/get-started/install/windows
- ✓ Check if installed: `flutter --version`

### 3. Ollama (for AI)
- Download: https://ollama.ai/download
- After installing, open Command Prompt and run:
  ```
  ollama pull phi4:3.8b
  ```
- This downloads the AI model (might take 5-10 minutes)

### 4. Supabase Account (Already Set Up ✓)
- Your database is already configured!
- URL: https://eguewniqweyrituwbowt.supabase.co

---

## 🎯 Step-by-Step Setup

### STEP 1: Set Up Database (One-Time Setup)

1. **Right-click** on `studypulse\SETUP_SUPABASE.ps1`
2. Select **"Run with PowerShell"**
3. Follow the instructions in the window:
   - It will open your Supabase dashboard
   - It will copy SQL code to your clipboard
   - Paste it in Supabase SQL Editor
   - Click "Run"
4. Done! Your database is ready ✓

**What this does:** Creates all the tables (users, exams, questions, etc.) in your cloud database.

---

### STEP 2: Start the Backend and AI Systems

**Option A: Using Batch File (Easiest)**

1. Go to the `studypulse` folder
2. **Double-click** `START_ALL.bat`
3. Wait for windows to open (should see 2-3 terminal windows)
4. A browser will open showing API documentation
5. Done! Backend is running ✓

**Option B: Using PowerShell**

1. **Right-click** `studypulse\START_ALL.ps1`
2. Select **"Run with PowerShell"**
3. Same result as Option A

**What's running now:**
- ✓ Backend API: `http://localhost:8000`
- ✓ RAG Pipeline: `http://localhost:8001`
- ✓ Ollama AI: `http://localhost:11434`

**Keep these windows open!** Closing them stops the backend.

---

### STEP 3: Start the Mobile App

1. Connect your Android phone via USB **OR** start an Android emulator
2. Go to the `studypulse` folder
3. **Double-click** `START_MOBILE.bat`
4. When asked to select a device, type the number of your device and press Enter
5. Wait 30-60 seconds for the app to build
6. App will launch on your phone/emulator!

**First Time Login:**
- Email: `test@studypulse.com`
- Password: `password123`

(This is a demo account that will be created automatically)

---

## 🎉 You're Done!

Your app is now running! Here's what you can do:

### Test the App
1. Open the app on your phone
2. Login with test credentials
3. Select an exam (UPSC, NEET, etc.)
4. Choose a subject and topic
5. Start a study timer (try 5 minutes)
6. After timer ends, take the mock test
7. Submit answers and see results!

### Stop Everything
- Close all the terminal windows that opened
- Or press `Ctrl+C` in each window

### Start Again Tomorrow
- Just run `START_ALL.bat` again!
- No need to repeat STEP 1 (database setup)

---

## 📂 File Structure Explained

```
studypulse/
├── START_ALL.bat            ← Double-click to start backend
├── START_MOBILE.bat         ← Double-click to start mobile app
├── SETUP_SUPABASE.ps1       ← Run once to set up database
│
├── backend/                 ← Server code (Python)
│   ├── .env                 ← Your secret keys (already configured)
│   ├── app/                 ← Main application code
│   └── supabase_schema.sql  ← Database structure
│
└── mobile/                  ← Flutter app code
    ├── lib/                 ← App screens and logic
    └── android/             ← Android-specific files
```

---

## 🐛 Common Problems & Solutions

### "Python not found"
- **Fix:** Install Python from python.org
- Make sure to check "Add Python to PATH" during installation

### "Flutter not found"
- **Fix:** Install Flutter SDK
- Add Flutter to your system PATH

### "Ollama not responding"
- **Fix:** 
  1. Open Command Prompt
  2. Run: `ollama serve`
  3. Keep that window open

### "Supabase connection failed"
- **Fix:** 
  1. Check your internet connection
  2. Make sure you ran `SETUP_SUPABASE.ps1`
  3. Check if tables exist in Supabase dashboard

### "Port 8000 already in use"
- **Fix:** 
  1. Close the previous backend instance
  2. Or restart your computer

### Mobile app won't run
- **Fix:**
  1. Make sure backend is running first
  2. Check if USB debugging is enabled on phone
  3. Try: `flutter clean` then `flutter pub get`

---

## 📞 Getting Help

### Check Logs
- Backend logs: Look at the terminal window running `uvicorn`
- Mobile logs: Look at the Flutter terminal output

### Test Each Component

1. **Test Ollama:**
   ```
   curl http://localhost:11434/api/tags
   ```

2. **Test Backend:**
   ```
   curl http://localhost:8000/api/v1/health
   ```

3. **Test RAG Pipeline:**
   ```
   curl http://localhost:8001/api/health
   ```

All should respond without errors.

---

## 🎓 Next Steps

### Add Your Own Exams

1. Open Supabase dashboard: https://app.supabase.com
2. Go to "Table Editor"
3. Add rows to:
   - `exams` table (e.g., "JEE Main", "CAT")
   - `subjects` table (e.g., "Physics", "Math")
   - `topics` table (e.g., "Mechanics", "Algebra")

### Customize the App

- **Change colors:** Edit `mobile/lib/main.dart`
- **Add features:** Ask me what you want to add!
- **Change timer durations:** Edit `mobile/lib/screens/study_screen.dart`

---

## 🔒 Important Security Notes

1. **Never share** your `.env` file
2. **Change** the `SECRET_KEY` in `.env` before going live
3. **Don't commit** `.env` to Git
4. **Use strong passwords** for real users

---

## ✨ What Makes This Special

- ✅ **Free AI**: No OpenAI API costs (using local Ollama)
- ✅ **Cloud Database**: Data backed up automatically
- ✅ **Smart Questions**: AI generates questions based on previous year papers
- ✅ **Offline Capable**: Can work without internet after initial setup
- ✅ **Cross-Platform**: Same app runs on Android & iOS

---

## 📹 Visual Guide

### Video Walkthrough (Coming Soon)
I'll create a video showing:
1. Installing all prerequisites
2. Running the setup scripts
3. Testing the app
4. Adding custom exams

---

## 🎯 Quick Reference Card

| Task | Command/File |
|------|-------------|
| Set up database (once) | Right-click `SETUP_SUPABASE.ps1` → Run |
| Start backend & AI | Double-click `START_ALL.bat` |
| Start mobile app | Double-click `START_MOBILE.bat` |
| Stop everything | Close terminal windows |
| View API docs | Open `http://localhost:8000/docs` |
| Check Supabase data | https://app.supabase.com |

---

**You're all set! 🎉 Enjoy your AI-powered exam prep platform!**

---

*Last Updated: February 6, 2026*  
*Created for: Complete beginners in coding*
