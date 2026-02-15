@echo off
REM Quick start script for running StudyPulse backend tests on Windows

echo ========================================
echo StudyPulse Backend Test Runner
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "tests" (
    echo ERROR: Must run from studypulse\backend directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

echo [2/3] Running tests...
echo.

REM Run tests based on command line argument
if "%1"=="unit" (
    echo Running UNIT tests only...
    pytest tests/unit -v
) else if "%1"=="integration" (
    echo Running INTEGRATION tests only...
    pytest tests/integration -v
) else if "%1"=="e2e" (
    echo Running E2E tests only...
    pytest tests/e2e -v -m e2e
) else if "%1"=="coverage" (
    echo Running tests with COVERAGE report...
    pytest --cov=app --cov-report=html --cov-report=term-missing
) else if "%1"=="fast" (
    echo Running FAST tests only (skipping slow tests)...
    pytest -m "not slow and not load" -v
) else (
    echo Running ALL tests...
    pytest tests/ -v
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo TESTS FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo ALL TESTS PASSED!
echo ========================================

if "%1"=="coverage" (
    echo.
    echo Coverage report available at: htmlcov\index.html
    echo Opening coverage report...
    start htmlcov\index.html
)

echo.
echo [3/3] Done!
echo.
echo Usage:
echo   TEST_START.bat           - Run all tests
echo   TEST_START.bat unit      - Run unit tests only
echo   TEST_START.bat integration - Run integration tests only
echo   TEST_START.bat e2e       - Run E2E tests only
echo   TEST_START.bat coverage  - Run with coverage report
echo   TEST_START.bat fast      - Skip slow tests
echo.

pause
