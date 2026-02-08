# StudyPulse - AI-Powered Exam Preparation Platform

> Transform your study routine with intelligent mock tests powered by RAG (Retrieval Augmented Generation)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.0+-02569B.svg?style=flat&logo=Flutter&logoColor=white)](https://flutter.dev)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg?style=flat&logo=Next.js&logoColor=white)](https://nextjs.org)

## 🎯 Overview

StudyPulse is a comprehensive exam preparation platform that combines traditional study methods with AI-powered question generation. Study for a configurable duration (5-120 minutes), then take a mock test with questions tailored to your topic. Score ≥85% to earn a star!

### ✨ Key Features

- **📚 Comprehensive Content:** 8 exams, 29 subjects, 94 topics, 4,700+ questions
- **⏱️ Flexible Study Sessions:** Choose from 5 to 120-minute study durations
- **🤖 AI-Powered Questions:** RAG pipeline with Qdrant + Ollama (optional)
- **⚡ Lightning Fast:** Questions load in 70ms with database-only mode
- **📱 Cross-Platform:** Web (Next.js), Mobile (Flutter), Backend (FastAPI)
- **⭐ Gamification:** Earn stars for scoring ≥85% on tests
- **📊 Progress Tracking:** Dashboard with study history and performance analytics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       StudyPulse                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Next.js    │  │   Flutter    │  │   FastAPI    │    │
│  │   Frontend   │  │   Mobile     │  │   Backend    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │            │
│         └──────────────────┴──────────────────┘            │
│                            │                               │
│         ┌──────────────────┴──────────────────┐           │
│         │         REST API (FastAPI)           │           │
│         ├──────────────────────────────────────┤           │
│         │  • Auth (JWT)                        │           │
│         │  • Study Sessions                    │           │
│         │  • Mock Tests                        │           │
│         │  • Question Generation (RAG)         │           │
│         └──────────────────┬──────────────────┘           │
│                            │                               │
│         ┌──────────────────┴──────────────────┐           │
│         │         Data Layer                   │           │
│         ├──────────────────────────────────────┤           │
│         │  • SQLite (4,700 questions)          │           │
│         │  • Redis (caching)                   │           │
│         │  • Qdrant (vector store - optional)  │           │
│         │  • Ollama (LLM - optional)           │           │
│         └──────────────────────────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **Flutter 3.0+** (for mobile)
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/Anandakumar9/Ask_Anand.git
cd Ask_Anand/studypulse
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

# Populate database with 4,700 questions
python scripts/populate_questions.py

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

### 3. Mobile App (Quickest to Test)

```bash
cd mobile
flutter pub get
flutter run -d chrome --web-port=8080
```

App will open at `http://localhost:8080`

### 4. Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 📱 How to Use

1. **Login:** Use guest mode or create an account
2. **Select Topic:** Choose Exam → Subject → Topic
3. **Study:** Select duration (5-120 mins) and start timer
4. **Take Test:** When timer ends, click "Start Mock Test"
5. **Answer Questions:** 10 questions, choose answers, submit
6. **View Results:** Get score, explanations, and earn ⭐ if score ≥ 85%

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (async Python)
- **Database:** SQLite (4,700+ questions)
- **Cache:** Redis
- **Vector Store:** Qdrant (optional, for semantic search)
- **LLM:** Ollama phi4-mini (optional, for AI generation)
- **Auth:** JWT tokens
- **ORM:** SQLAlchemy (async)

### Frontend (Web)
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **State:** Zustand
- **Language:** TypeScript

### Mobile
- **Framework:** Flutter 3.0+
- **Language:** Dart
- **HTTP:** Dio
- **State:** Provider
- **Storage:** flutter_secure_storage

## 📊 Database Schema

```sql
-- 8 Exams
UPSC Civil Services, JEE Main, NEET UG, IBPS PO, CAT, 
CBSE Class 12, SSC CGL, CBSE Class 10

-- 29 Subjects
Geography, History, Physics, Chemistry, Mathematics, 
Biology, Banking, English, etc.

-- 94 Topics
Physical Geography, Ancient India, Laws of Motion, 
Organic Chemistry, Differential Calculus, etc.

-- 4,700+ Questions
Multiple choice questions with explanations
Previous year questions + AI-generated (optional)
```

## 🔧 Configuration

### Backend Environment Variables

Create `.env` file in `backend/`:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./studypulse.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Qdrant (optional)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Ollama (optional)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi4-mini:3.8b-q4_K_M

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# RAG Settings
RAG_ENABLED=false  # Set to true to enable AI generation
PREVIOUS_YEAR_RATIO=1.0  # 1.0 = 100% database questions
DEFAULT_QUESTION_COUNT=10
```

### Mobile API Configuration

Edit `mobile/lib/api/api_service.dart`:

```dart
static const String _devBaseUrlWeb = 'http://localhost:8000/api/v1';
static const String _devBaseUrlAndroid = 'http://10.0.2.2:8000/api/v1';
```

## 🎨 Features in Detail

### Study Flow
1. Select topic and duration
2. Timer counts down (with pause/resume)
3. Session tracked in backend
4. Pre-generation of questions in background
5. Seamless transition to test when timer ends

### Mock Test Flow
1. Questions fetched from database (70ms response time)
2. Mix of previous year questions
3. Multiple choice format
4. Time tracking
5. Instant results with explanations

### RAG Pipeline (Optional)
```
Cache Check → DB Questions → Qdrant Search → AI Generation → Combine → Shuffle
```

- **Cache:** Redis (1-hour TTL)
- **Database:** SQLite previous year questions
- **Semantic Search:** Qdrant vector similarity
- **AI Generation:** Ollama with phi4-mini model
- **Deduplication:** Avoid repeating questions for same user

## 📈 Performance

- **API Response Time:** 70ms (database-only mode)
- **Questions Available:** 4,700+ across all topics
- **Concurrent Users:** Tested with 10+ simultaneous sessions
- **Database Size:** ~5MB (SQLite)
- **Cache Hit Rate:** 80%+ for pre-generated questions

## 🐛 Known Issues & Solutions

### Issue: Questions not loading (timeout)
**Solution:** Ensure backend is running and RAG_ENABLED=false in .env

### Issue: Session ID null error
**Solution:** Fixed in latest commit - session_id field name corrected

### Issue: Flutter hot reload not working
**Solution:** Use `flutter clean` then `flutter run` for full rebuild

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Anandakumar**
- GitHub: [@Anandakumar9](https://github.com/Anandakumar9)

## 🙏 Acknowledgments

- FastAPI for the excellent async framework
- Flutter for cross-platform development
- Qdrant for vector similarity search
- Ollama for local LLM inference
- Next.js for the web framework

## 📚 Documentation

- [Backend API Docs](studypulse/backend/README.md)
- [Mobile Setup Guide](studypulse/mobile/QUICK_START.md)
- [Frontend Guide](studypulse/frontend/README.md)
- [Complete Project Guide](studypulse/COMPLETE_PROJECT_GUIDE.md)

## 🔮 Roadmap

- [ ] Add more exam types (GATE, UPSC CSE Mains, etc.)
- [ ] Implement question rating system
- [ ] Add leaderboard functionality
- [ ] Social features (study groups, challenges)
- [ ] Spaced repetition algorithm
- [ ] Offline mode for mobile
- [ ] Video explanations for questions
- [ ] AI tutor chatbot

---

**⭐ Star this repo if you find it helpful!**

Made with ❤️ for students everywhere
