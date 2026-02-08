# 📚 StudyPulse

**AI-Powered Exam Preparation Platform**

StudyPulse helps students master exam topics through focused study sessions and intelligent mock tests powered by AI.

---

## 🚀 Quick Start

**Just double-click: `START.bat`**

That's it! Your app will open in Chrome in 60 seconds.

For detailed information, see [QUICK_START.md](QUICK_START.md) and [STATUS.md](STATUS.md)

---

## ✨ Features

- ⏱️ **Study Timer**: 5-120 minute focused sessions
- 📝 **Smart Mock Tests**: 50% previous year + 50% AI-generated questions
- ⭐ **Star Rewards**: Earn stars for 85%+ scores
- 📊 **Analytics**: Track progress and performance
- 🤖 **AI-Powered**: Uses Ollama Phi4 for question generation
- ☁️ **Cloud Database**: Supabase PostgreSQL backend

---

## 🏗️ Architecture

```
studypulse/
├── START.bat           ← One-click startup
├── backend/            ← FastAPI + Supabase + Ollama
│   └── app/
│       ├── main.py
│       ├── api/        (auth, dashboard, exams, study, mock_test)
│       ├── core/       (config, supabase, ollama)
│       └── schemas/
├── mobile/             ← Flutter (Android/iOS/Web)
│   └── lib/
│       ├── main.dart
│       ├── screens/
│       └── api/
└── frontend/           ← Next.js (optional)
```

---

## 💻 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.13)
- **Database**: Supabase (PostgreSQL)
- **AI**: Ollama Phi4 3.8B (local LLM)
- **Optional**: RAG Pipeline with Qdrant

### Mobile
- **Framework**: Flutter 3.0+
- **State**: Provider
- **HTTP**: Dio
- **Platforms**: Android, iOS, Web

### Frontend (Optional)
- **Framework**: Next.js 14
- **Styling**: Tailwind CSS
- **State**: Zustand

---

## 🎯 How It Works

1. **Study**: Select topic → Set timer → Study material
2. **Test**: AI generates mixed questions (previous + new)
3. **Score**: Submit answers → Get instant results
4. **Earn**: Score ≥85% → Earn a ⭐
5. **Track**: View progress on dashboard

---

## 🔧 Manual Setup

Only needed if `START.bat` doesn't work:

### Backend
```bash
cd backend
..\..\..\.venv\Scripts\activate  # Virtual env already set up
uvicorn app.main:app --reload --port 8000
```

### Mobile (Web)
```bash
cd mobile
flutter run -d chrome --web-port=8080
```

### Mobile (Android/iOS)
```bash
cd mobile
flutter run
# Select your device when prompted
```

---

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Step-by-step guide
- **[STATUS.md](STATUS.md)** - System overview and configuration
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Development guide

---

## 🔑 API Access

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Dashboard**: http://localhost:8000/api/v1/dashboard

### Example Request
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

---

## 🎓 Supported Exams

- UPSC (Civil Services)
- JEE (Engineering)
- NEET (Medical)
- SSC (Staff Selection)
- Banking Exams
- State PSCs
- And more...

---

## 📊 Current Status

✅ **Backend**: Fully functional with Supabase + Ollama  
✅ **Mobile**: Working on Web (Chrome), Android, iOS  
✅ **AI**: Phi4 3.8B model for question generation  
✅ **Database**: Supabase PostgreSQL with schema  
⚠️ **RAG Pipeline**: Optional advanced feature (requires Docker)  

---

## 🤝 Contributing

This is a production-ready exam preparation platform. For modifications:

1. Backend: Python/FastAPI knowledge required
2. Mobile: Flutter/Dart experience needed
3. AI: Understanding of LLMs helpful

See [copilot-instructions.md](.github/copilot-instructions.md) for architecture details.

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Supabase** - Cloud PostgreSQL database
- **Ollama** - Local LLM runtime
- **Phi4** - Microsoft's language model
- **FastAPI** - Modern Python web framework
- **Flutter** - Cross-platform mobile framework

---

**Built with ❤️ for students preparing for competitive exams**

---

**Quick Links**:
