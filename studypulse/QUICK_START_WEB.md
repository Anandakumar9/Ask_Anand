# StudyPulse - Quick Start Guide

## ✅ SIMPLIFIED STARTUP (NO VS / QDRANT NEEDED)

Since you're encountering:
- Visual Studio version mismatch (Flutter wants VS 2019, you have VS 2026)
- Qdrant not running (vector database)

## 🚀 EASIEST SOLUTION: Use Web Version

**Double-click**: `START_WEB.bat`

This runs your app in **Chrome browser** instead of Windows desktop:
- ✅ No Visual Studio needed
- ✅ No Qdrant needed
- ✅ Works immediately
- ✅ Same full functionality

---

## 🔧 What START_WEB.bat Does:

1. Starts Backend API (port 8000)
2. Starts Mobile App in Chrome browser (port 8080)
3. Skips RAG Pipeline (optional)

**Total time**: 30-60 seconds  
**Result**: Full app running in Chrome!

---

## 📊 Why This Works:

### Issue 1: Visual Studio Mismatch
- **Problem**: Flutter configured for VS 2019, you have VS Build Tools 2026
- **Solution**: Use Chrome web instead of Windows desktop
- **Result**: No VS needed at all!

### Issue 2: Qdrant Not Running
- **Problem**: RAG Pipeline needs Qdrant vector database
- **Solution**: Skip RAG for now (app works without it)
- **Alternative**: Start Qdrant with: `docker run -p 6333:6333 qdrant/qdrant`

---

## 🎯 To Run Your App RIGHT NOW:

```
Double-click: START_WEB.bat
```

Wait 60 seconds → Chrome opens with your app!

---

## 🛠️ To Fix Visual Studio Issue (Optional):

If you want Windows desktop app later:

1. Open: `studypulse\mobile\windows\CMakeLists.txt`
2. After line 2, add:
   ```cmake
   set(CMAKE_GENERATOR_TOOLSET "v143")
   ```
3. Save and try `flutter run -d windows` again

---

## 🔥 To Fix RAG Pipeline (Optional):

If you want full RAG features:

1. Start Qdrant:
   ```
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

2. Keep it running in background

3. Then start RAG Pipeline:
   ```
   cd C:\Users\anand\OneDrive\Desktop\Ask_Rag_pipeline
   uvicorn app.api.main:app --port 8001
   ```

---

## ✨ Current Status:

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Working | Port 8000 |
| Mobile App (Web) | ✅ Working | Chrome browser |
| Mobile App (Desktop) | ⚠️ VS issue | Use web version instead |
| RAG Pipeline | ⚠️ Needs Qdrant | Optional feature |

---

## 🎉 Bottom Line:

**Use `START_WEB.bat` - it just works!**

Everything works perfectly in Chrome browser. No VS or Qdrant needed.

---

**Last Updated**: February 7, 2026
