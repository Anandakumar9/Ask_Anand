# StudyPulse - Quick Start Guide

## 🚀 One-Click Startup

**Just double-click: `START.bat`**

That's it! The script will:
1. Start the backend API (FastAPI + Supabase + Ollama)
2. Launch the mobile app in your Chrome browser
3. Optionally start RAG Pipeline (if Docker is running)

---

## 📋 What You Need

### Essential (Already Installed)
- ✅ Python 3.13
- ✅ Flutter SDK
- ✅ Supabase account
- ✅ Ollama with Phi4 model

### Optional (for Advanced Features)
- Docker Desktop (for RAG Pipeline with Qdrant vector database)

---

## 🎯 Quick Access

Once started, access:

- **Backend API Docs**: http://localhost:8000/docs
- **Mobile App**: Opens automatically in Chrome (or http://localhost:8080)
- **Health Check**: http://localhost:8000/health

---

## 🔧 Manual Setup (If Needed)

### 1. Backend Only
```powershell
cd studypulse\backend
uvicorn app.main:app --reload --port 8000
```

### 2. Mobile App Only (Web)
```powershell
cd studypulse\mobile
flutter run -d chrome --web-port=8080
```

### 3. Mobile App (Android/iOS)
```powershell
cd studypulse\mobile
flutter run
# Select your device when prompted
```

---

## 🐛 Troubleshooting

### Backend won't start
```powershell
cd studypulse\backend
..\..\.venv\Scripts\pip install -r requirements.txt
```

### Mobile app errors
```powershell
cd studypulse\mobile
flutter clean
flutter pub get
flutter run -d chrome
```

### RAG Pipeline fails
- Make sure Docker Desktop is running
- The app works fine without RAG - it uses Ollama directly

---

## 📁 Project Structure

```
studypulse/
├── START.bat               ← Double-click this!
├── backend/                ← FastAPI + Supabase
│   └── app/
│       ├── main.py
│       ├── core/
│       └── api/
├── mobile/                 ← Flutter app
│   └── lib/
│       ├── main.dart
│       ├── screens/
│       └── api/
└── frontend/               ← Next.js (optional)
```

---

## 🎓 How It Works

1. **Study Session**: Choose topic → Set timer (5-120 mins) → Study
2. **Mock Test**: AI generates questions (50% previous + 50% new)
3. **Score**: Get ≥85% to earn a ⭐
4. **Track**: View progress on dashboard

---

## 🔑 Configuration

All settings in `backend/app/core/config.py`:
- Supabase: Already configured
- Ollama: Uses local Phi4 model at port 11434
- RAG: Optional, uses port 8001

---

## 📞 Support

If something doesn't work:
1. Check that Ollama is running: `ollama list`
2. Test backend: http://localhost:8000/docs
3. Check terminal output for errors

---

**Version**: 1.0  
**Last Updated**: February 7, 2026
