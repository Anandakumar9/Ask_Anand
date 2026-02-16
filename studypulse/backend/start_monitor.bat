@echo off
REM Continuous Railway Deployment Monitor - Windows Batch Script
REM This script runs the Python monitor in a loop until PostgreSQL connection succeeds

echo.
echo ================================================================================
echo    CONTINUOUS RAILWAY DEPLOYMENT MONITOR
echo ================================================================================
echo.
echo This will monitor your Railway deployment every 5 minutes until PostgreSQL works.
echo Press Ctrl+C to stop at any time.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Railway CLI not found!
    echo Please install it: npm i -g @railway/cli
    echo Then login: railway login
    echo.
    pause
    exit /b 1
)

REM Navigate to backend directory
cd /d "%~dp0"

echo Starting continuous monitoring...
echo.

REM Run the Python monitor
python continuous_railway_monitor.py 5

echo.
echo Monitoring stopped.
pause
