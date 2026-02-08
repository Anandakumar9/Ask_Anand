# StudyPulse Mobile App 📱

**AI-Powered Exam Preparation - Flutter Mobile Application**

A cross-platform mobile application for Android and iOS that helps students prepare for competitive exams through intelligent study sessions, AI-generated mock tests, and personalized performance tracking.

---

## 🎯 Features

### Core Functionality
- **Welcome Screen** with inspirational quotes
- **Study Sessions** with customizable timers (5 mins to 2 hours)
- **Smart Mock Tests** combining previous year questions + AI-generated questions
- **Instant Results** with star rewards for 85%+ scores
- **Topic-wise Performance Tracking**
- **User Profile Management**
- **Progress Analytics Dashboard**

### User Journey
1. **Welcome** → Inspirational quote screen
2. **Login/Guest** → Flexible authentication
3. **Dashboard** → View stats, recent activity, continue studying
4. **Study** → Select Exam → Subject → Topic → Duration → Start Timer
5. **Test** → Answer mock test questions (Previous Year + AI)
6. **Results** → View score, earn stars, get suggestions
7. **History** → Review past performance topic-wise

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Flutter 3.0+ |
| State Management | Provider |
| UI Components | Material Design 3 |
| Icons | Lucide Icons |
| HTTP Client | Dio |
| Secure Storage | flutter_secure_storage |
| Backend API | FastAPI (Python) |

---

## 📋 Prerequisites

### Required Software
1. **Flutter SDK** (3.0.0 or higher)
   ```powershell
   # Check installation
   flutter --version
   flutter doctor
   ```

2. **Android Studio** or **VS Code** with Flutter extensions

3. **For Android Development:**
   - Android SDK
   - Android Emulator or physical device with USB debugging

4. **For iOS Development** (macOS only):
   - Xcode 13+
   - iOS Simulator or physical device
   - CocoaPods

5. **Backend Server**
   - StudyPulse backend running on `localhost:8000` or configured endpoint

---

## 🚀 Installation & Setup

### Step 1: Install Flutter (if not already installed)

**Windows:**
```powershell
# Download Flutter SDK from https://flutter.dev/docs/get-started/install/windows
# Extract to C:\src\flutter
# Add to PATH: C:\src\flutter\bin

# Verify installation
flutter doctor -v
```

**macOS:**
```bash
# Using Homebrew
brew install --cask flutter

# Or download from https://flutter.dev/docs/get-started/install/macos

# Verify installation
flutter doctor -v
```

### Step 2: Clone & Navigate to Project
```powershell
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile
```

### Step 3: Install Dependencies
```powershell
flutter pub get
```

### Step 4: Configure Backend API Endpoint

Edit `lib/api/api_service.dart` if needed:
```dart
static const String _devBaseUrlAndroid = 'http://10.0.2.2:8000/api/v1';  // Android Emulator
static const String _devBaseUrlOther = 'http://localhost:8000/api/v1';    // iOS Simulator/Web
```

### Step 5: Run the App

**On Android Emulator:**
```powershell
# Start emulator
flutter emulators --launch <emulator_id>

# Run app
flutter run
```

**On iOS Simulator** (macOS only):
```bash
# Open simulator
open -a Simulator

# Run app
flutter run
```

**On Physical Device:**
```powershell
# Connect device via USB, enable USB debugging
# Verify device is connected
flutter devices

# Run on connected device
flutter run
```

**On Chrome (Web - for testing):**
```powershell
flutter run -d chrome
```

---

## 📁 Project Structure

```
mobile/
├── lib/
│   ├── main.dart                   # App entry point
│   ├── api/
│   │   └── api_service.dart        # Backend API client (Dio)
│   ├── screens/
│   │   ├── welcome_screen.dart     # Welcome with quotes
│   │   ├── login_screen.dart       # Authentication
│   │   ├── home_screen.dart        # Dashboard with tabs
│   │   ├── study_screen.dart       # Study session setup
│   │   ├── study_timer_screen.dart # Study timer (5-120 mins)
│   │   ├── test_screen.dart        # Mock test interface
│   │   ├── results_screen.dart     # Test results & stars
│   │   ├── results_history_screen.dart # Topic-wise history
│   │   ├── profile_screen.dart     # User profile
│   │   └── setup_screen.dart       # Exam selection
│   └── store/
│       └── app_store.dart          # Global state (auth, user)
├── android/                        # Android-specific files
├── ios/                           # iOS-specific files
├── pubspec.yaml                   # Dependencies
└── README.md                      # This file
```

---

## 🔧 Development Workflow

### Key Dependencies (from pubspec.yaml)
```yaml
dependencies:
  flutter: sdk: flutter
  dio: ^5.3.3                      # HTTP client
  provider: ^6.0.5                 # State management
  flutter_secure_storage: ^9.0.0  # Secure token storage
  google_fonts: ^6.1.0             # Typography
  lucide_icons: ^0.257.0           # Icons
  confetti: ^0.7.0                 # Celebration animation
  percent_indicator: ^4.2.3        # Progress indicators
```

### Running in Development Mode
```powershell
# Hot reload enabled
flutter run

# With specific device
flutter run -d <device_id>

# Release mode (optimized)
flutter run --release
```

### Debugging
```powershell
# Check for issues
flutter doctor

# Clean build artifacts
flutter clean
flutter pub get

# View logs
flutter logs
```

---

## 📱 Testing on Devices

### Android Emulator Setup
```powershell
# List available emulators
flutter emulators

# Launch specific emulator
flutter emulators --launch <emulator_id>

# Create new emulator (via Android Studio)
# Tools → AVD Manager → Create Virtual Device
```

### iOS Simulator Setup (macOS only)
```bash
# List available simulators
xcrun simctl list devices

# Launch specific simulator
open -a Simulator

# Select device from Simulator menu: Hardware → Device
```

### Physical Device Setup

**Android:**
1. Enable Developer Options on device
2. Enable USB Debugging
3. Connect via USB
4. Accept debugging prompt
5. Run `flutter devices` to verify

**iOS:**
1. Connect iPhone/iPad via USB
2. Trust computer on device
3. Open Xcode and add Apple ID (free developer account)
4. Select device in Xcode
5. Run `flutter devices` to verify

---

## 🌐 Backend Integration

### API Endpoints Used
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/dashboard/` - Dashboard stats
- `GET /api/v1/exams/` - List exams, subjects, topics
- `POST /api/v1/study/sessions` - Start study session
- `POST /api/v1/study/sessions/{id}/complete` - Complete session
- `POST /api/v1/mock-test/start` - Generate mock test with RAG
- `POST /api/v1/mock-test/{id}/submit` - Submit answers
- `GET /api/v1/mock-test/{id}/results` - Get test results

### Backend Setup Required
```powershell
# Navigate to backend directory
cd ..\backend

# Start backend server
uvicorn app.main:app --reload

# Server should run on http://localhost:8000
```

---

## 🎨 UI/UX Guidelines

### Color Scheme
- Primary: `#43B02A` (Green)
- Secondary: `#2D8A1E` (Dark Green)
- Background: `#F7F7F7` (Light Gray)
- Text: `#343538` (Dark Gray)
- Accent: `#767676` (Medium Gray)

### Typography
- Font Family: Google Fonts - Inter
- Material Design 3 (useMaterial3: true)

---

## 🐛 Troubleshooting

### Common Issues

**1. Backend Connection Failed**
```powershell
# Check if backend is running
curl http://localhost:8000/health

# For Android emulator, use 10.0.2.2 instead of localhost
# Update lib/api/api_service.dart if needed
```

**2. Build Errors**
```powershell
flutter clean
flutter pub get
flutter pub upgrade
flutter run
```

**3. Gradle/CocoaPods Issues**
```powershell
# Android
cd android
./gradlew clean
cd ..

# iOS (macOS)
cd ios
pod install --repo-update
cd ..
```

**4. Hot Reload Not Working**
```powershell
# Press 'R' in terminal for hot reload
# Press 'Shift+R' for hot restart
# Or stop and re-run flutter run
```

---

## 📦 Building for Production

### Android APK
```powershell
# Build APK
flutter build apk --release

# Build App Bundle (for Play Store)
flutter build appbundle --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### iOS IPA (macOS only)
```bash
# Build for iOS
flutter build ios --release

# Open in Xcode for archive and upload
open ios/Runner.xcworkspace
```

---

## 🔐 Configuration

### Environment Variables
Create `.env` file (not tracked in git):
```env
API_BASE_URL=https://your-production-api.com/api/v1
```

### Signing (for distribution)
- **Android**: Configure `android/app/build.gradle` with signing keys
- **iOS**: Configure signing in Xcode

---

## 📝 App Flow Summary

1. **Welcome Screen** (3 seconds) → Shows random inspirational quote
2. **Login** → Optional (can proceed as guest)
3. **Dashboard** → 
   - View stats (stars, streak, avg score)
   - Continue studying previous topic
   - Recent activity
4. **Study Tab** →
   - Select Exam → Subject → Topic
   - Choose duration (5, 10, 15, 20, 30, 45, 60, 90, 120 minutes)
   - Start timer
5. **Timer Running** →
   - RAG pipeline activates in background
   - Can pause/resume
   - End session starts test
6. **Mock Test** →
   - Mix of Previous Year + AI-generated questions
   - 4 options per question
   - Time tracking
7. **Results** →
   - Score percentage
   - Star earned if ≥85%
   - Confetti animation
   - Suggestions for improvement (<85%)
8. **Results Tab** → View all past tests topic-wise
9. **Profile Tab** → Manage user details and settings

---

## 🤝 Contributing

To add new features:
1. Create screen in `lib/screens/`
2. Add API method in `lib/api/api_service.dart`
3. Update navigation in `lib/screens/home_screen.dart`
4. Test on both Android and iOS

---

## 📄 License

MIT License - Part of the StudyPulse project

---

## 👨‍💻 Developer Notes

### State Management
- Uses **Provider** for global state (authentication, user data)
- `AppStore` in `lib/store/app_store.dart` handles:
  - Token persistence (secure storage)
  - User profile caching
  - Logout functionality

### API Client
- **Dio** HTTP client with interceptors
- Automatic token injection for authenticated requests
- Platform-specific base URLs (Android emulator vs iOS simulator)

### Key Features Implementation
- **Timer**: Uses Dart `Timer.periodic` for countdown
- **RAG Integration**: Backend generates AI questions when test starts
- **Stars**: Awarded for 85%+ scores (backend logic)
- **Confetti**: Uses `confetti` package for celebration
- **Offline**: Secure storage keeps user logged in

---

**Made with ❤️ for students preparing for competitive exams**

For backend setup, see: `../backend/README.md`
