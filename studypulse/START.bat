@echo off
cls
title StudyPulse - Starting...
color 0B

echo.
echo ============================================================
echo                    StudyPulse
echo          AI-Powered Exam Preparation Platform
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "%~dp0..\.venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found at: %~dp0..\.venv
    echo.
    pause
    exit /b 1
)

echo ✓ Virtual environment found
echo.

REM Check Ollama
curl http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Ollama is not running - AI features will be limited
    echo   To start: Open terminal and run "ollama serve"
    echo.
) else (
    echo ✓ Ollama is running
    echo.
)

echo.
echo ============================================================
echo Step 1/2: Starting Backend API
echo ============================================================
echo.

REM Start backend with proper virtual environment
start "Backend API" cmd /k "cd /d %~dp0 && title Backend API - Port 8000 && color 0E && echo ============================================ && echo    Backend API && echo    http://localhost:8000 && echo ============================================ && echo. && echo Activating virtual environment... && call ..\.venv\Scripts\activate.bat && echo. && cd backend && echo Starting server... && echo. && python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0"

echo Waiting for backend (15 seconds)...
timeout /t 15 /nobreak >nul

REM Test backend
curl http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Backend is ready
) else (
    echo ⚠ Backend starting... check Backend window
)

echo.
echo ============================================================
echo Step 2/2: Starting Mobile App
echo ============================================================
echo.

cd /d "%~dp0mobile"

start "Mobile App" cmd /k "cd /d %~dp0mobile && title Mobile App - Port 8080 && color 0D && echo ============================================ && echo    Mobile App && echo    http://localhost:8080 && echo ============================================ && echo. && flutter run -d chrome --web-port=8080 --web-hostname=localhost"

cls
echo.
echo ============================================================
echo              StudyPulse Started!
echo ============================================================
echo.
echo Services:
echo   ✓ Backend: http://localhost:8000
echo   ✓ Mobile:  http://localhost:8080 (opens in Chrome)
echo.
echo Windows:
echo   • Backend API (Yellow)
echo   • Mobile App (Pink)
echo.
echo Your app will open in Chrome in 30-60 seconds
echo.
echo Docs: http://localhost:8000/docs
echo.
echo To stop: Close all windows or CTRL+C
echo.
echo ============================================================
pause
