@echo off
echo ========================================
echo StudyPulse - Quick Status Check
echo ========================================
echo.

echo Checking Backend Server (Port 8001)...
curl -s http://localhost:8001 > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Backend is RUNNING on http://localhost:8001
) else (
    echo [WAIT] Backend is still starting...
)

echo.
echo Checking Mobile App (Port 8082)...
curl -s http://localhost:8082 > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Mobile App is RUNNING on http://localhost:8082
) else (
    echo [WAIT] Mobile App is still compiling (takes 2-3 minutes)
)

echo.
echo ========================================
echo To use the app:
echo ========================================
echo.
echo 1. Wait for both servers to show [OK]
echo 2. Open in browser: http://localhost:8082
echo 3. Start testing the user flow!
echo.
echo Run this script again to check status.
echo.
pause
