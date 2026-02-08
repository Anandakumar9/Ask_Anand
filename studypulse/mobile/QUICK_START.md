# 🚀 Quick Start Guide - StudyPulse Mobile App

## For Android Users (Windows/Mac/Linux)

### Prerequisites
- Flutter SDK installed
- Android Studio or Android device

### Steps:

1. **Open Terminal/PowerShell** in project directory:
   ```powershell
   cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
   ```

2. **Install dependencies:**
   ```powershell
   flutter pub get
   ```

3. **Start Backend Server** (in another terminal):
   ```powershell
   cd ..\backend
   uvicorn app.main:app --reload
   ```

4. **Run the app:**
   ```powershell
   # Check connected devices
   flutter devices
   
   # Run on first available device
   flutter run
   ```

5. **Login** (or tap "Continue as Guest"):
   - Email: `test@studypulse.com`
   - Password: `password123`

---

## For iOS Users (macOS Only)

### Prerequisites
- Flutter SDK installed
- Xcode installed
- iOS Simulator or iPhone

### Steps:

1. **Open Terminal** in project directory:
   ```bash
   cd ~/path/to/studypulse/mobile
   ```

2. **Install dependencies:**
   ```bash
   flutter pub get
   cd ios
   pod install
   cd ..
   ```

3. **Start Backend Server** (in another terminal):
   ```bash
   cd ../backend
   uvicorn app.main:app --reload
   ```

4. **Run the app:**
   ```bash
   # Open iOS Simulator
   open -a Simulator
   
   # Run app
   flutter run
   ```

5. **Login** (or tap "Continue as Guest")

---

## Using FlutterFlow (Alternative)

If you want to use FlutterFlow for visual development:

1. **Export to FlutterFlow:**
   - Go to [flutterflow.io](https://flutterflow.io)
   - Create new project
   - Import existing Flutter code
   - Or manually recreate screens using FlutterFlow's visual builder

2. **API Integration in FlutterFlow:**
   - Use "API Calls" feature
   - Add base URL: `http://localhost:8000/api/v1`
   - Configure each endpoint from `lib/api/api_service.dart`

---

## Using Expo (React Native Alternative)

**Note:** The current app is built with Flutter, not Expo/React Native.

To use Expo, you would need to:
1. Rebuild the entire app using React Native
2. Create new project: `npx create-expo-app studypulse-mobile`
3. Convert Flutter code to React Native components

**Recommendation:** Stick with Flutter as it's already fully implemented.

---

## App Features Overview

### 1. Welcome Screen
- Displays inspirational quote
- Auto-navigates to login after 3 seconds

### 2. Study Session Flow
- Home → Study Tab
- Select: Exam → Subject → Topic
- Choose Timer: 5, 10, 15, 20, 30, 45, 60, 90, or 120 minutes
- Start studying
- RAG pipeline generates questions in background

### 3. Mock Test
- Combination of:
  - Previous year questions
  - AI-generated questions (from RAG)
- 4 options per question
- Timed test

### 4. Results
- Score percentage
- ⭐ Star earned if score ≥ 85%
- 🎉 Confetti animation for stars
- Suggestions to study again if < 85%

### 5. Progress Tracking
- Results Tab: View all tests topic-wise
- Profile Tab: Manage account and view statistics
- Dashboard: Overall stats and recent activity

---

## Troubleshooting

### "Cannot connect to backend"
```powershell
# 1. Check if backend is running
curl http://localhost:8000/health

# 2. Start backend
cd ..\backend
uvicorn app.main:app --reload
```

### "Build failed" or "Dependency errors"
```powershell
flutter clean
flutter pub get
flutter pub upgrade
flutter run
```

### "Android emulator not found"
1. Open Android Studio
2. Tools → AVD Manager
3. Create new device (e.g., Pixel 5, Android 11+)
4. Start emulator
5. Run `flutter run`

### "iOS pod install failed" (macOS)
```bash
cd ios
pod deintegrate
pod install --repo-update
cd ..
flutter run
```

---

## Testing Guest Mode

If you don't have backend running, the app will automatically log you in as **Guest User** with limited features. This is perfect for UI testing.

---

## Next Steps

After successfully running:

1. ✅ Test the complete flow from welcome to results
2. ✅ Try different timer durations (5-120 mins)
3. ✅ Take mock tests and earn stars
4. ✅ View topic-wise results history
5. ✅ Customize your profile

---

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Review backend setup in [../backend/RUN_BACKEND.md](../backend/RUN_BACKEND.md)
- Flutter issues: `flutter doctor -v`
- Backend issues: Check FastAPI logs

---

**Happy Learning! 📚✨**
