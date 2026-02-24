@echo off
REM Local Testing Script for Question Ingestion System
REM Run this script to test the complete system locally

echo ============================================================
echo    StudyPulse Question Ingestion - Local Testing
echo ============================================================
echo.

REM Check if we're in the right directory
if not exist "studypulse\backend" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Step 1: Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.11+
    exit /b 1
)
echo       Python found

REM Step 2: Check Node.js
echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js not found. Please install Node.js 18+
    exit /b 1
)
echo       Node.js found

REM Step 3: Setup Backend
echo [3/6] Setting up backend...
cd studypulse\backend

REM Create venv if not exists
if not exist "venv" (
    echo       Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install dependencies
echo       Installing Python dependencies...
pip install -q -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo       Creating .env file...
    (
        echo DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/studypulse
        echo SECRET_KEY=local-testing-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo ENVIRONMENT=development
        echo DEBUG=true
    ) > .env
)

cd ..\..

REM Step 4: Setup Frontend
echo [4/6] Setting up frontend...
cd studypulse\frontend

REM Check node_modules
if not exist "node_modules" (
    echo       Installing Node.js dependencies...
    call npm install
)

REM Check for .env.local
if not exist ".env.local" (
    echo       Creating .env.local...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 > .env.local
)

cd ..\..

echo.
echo ============================================================
echo    Setup Complete! Next Steps:
echo ============================================================
echo.
echo 1. Start PostgreSQL database:
echo    docker run --name studypulse-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=studypulse -p 5432:5432 -d postgres:15
echo.
echo 2. Run database migration:
echo    cd studypulse\backend ^&^& venv\Scripts\activate ^&^& alembic upgrade head
echo.
echo 3. Seed test data:
echo    cd studypulse\backend ^&^& venv\Scripts\activate ^&^& python seed_demo_data.py
echo.
echo 4. Start backend server:
echo    cd studypulse\backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo.
echo 5. Start frontend server (new terminal):
echo    cd studypulse\frontend ^&^& npm run dev
echo.
echo 6. Test question import:
echo    cd studypulse\backend ^&^& venv\Scripts\activate ^&^& python scripts\html_question_parser.py --input "YOUR_HTML_FILE.html" --output data\questions.json --report
echo.
echo 7. Open browser:
echo    http://localhost:3000
echo.
echo ============================================================
echo.

REM Ask if user wants to start servers
set /p START_SERVERS="Do you want to start the backend and frontend servers now? (y/n): "

if /i "%START_SERVERS%"=="y" (
    echo.
    echo Starting servers...
    
    REM Start backend in new window
    start "StudyPulse Backend" cmd /k "cd studypulse\backend && call venv\Scripts\activate && uvicorn app.main:app --reload"
    
    REM Wait a bit for backend to start
    timeout /t 3 /nobreak >nul
    
    REM Start frontend in new window
    start "StudyPulse Frontend" cmd /k "cd studypulse\frontend && npm run dev"
    
    echo.
    echo Servers started in new windows!
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:3000
    echo.
    echo Press any key to open the frontend in your browser...
    pause >nul
    start http://localhost:3000
)

echo.
echo Done!
