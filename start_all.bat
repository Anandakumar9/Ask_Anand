@echo off
echo ========================================
echo StudyPulse - Start All Servers
echo ========================================
echo.

echo [1/3] Starting Backend Server...
start "Backend Server" cmd /k "cd /d c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend && python -m uvicorn app.main:app --reload --port 8001 --host 0.0.0.0"

timeout /t 3 /nobreak > nul

echo [2/3] Starting Mobile App (Flutter)...
start "Mobile App" cmd /k "cd /d c:\Users\anand\OneDrive\Desktop\Ask_Anand\ studypulse\mobile && C:\src\flutter\bin\flutter.bat run -d web-server --web-port=8082 --web-hostname=0.0.0.0"

timeout /t 5 /nobreak > nul

echo [3/3] Opening Diagnostic Tool...
start "" "c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\diagnostic.html"

echo.
echo ========================================
echo All servers started!
echo ========================================
echo.
echo Backend will be ready in ~15 seconds
echo Mobile app will be ready in ~2-3 minutes
echo.
echo The diagnostic tool will help you test everything.
echo.
echo After mobile app is ready:
echo   Open: http://localhost:8082
echo.
pause
