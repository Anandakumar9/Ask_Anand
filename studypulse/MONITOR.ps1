# StudyPulse Production Monitor & Tester
# Run this to start and monitor all services

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "         StudyPulse - Production Monitor" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"
$basePath = "C:\Users\anand\OneDrive\Desktop\Ask_Anand"
$studypulsePath = "$basePath\studypulse"

# Test functions
function Test-Service {
    param($Name, $Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "√ $Name is running (Status: $($response.StatusCode))" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "× $Name is not responding" -ForegroundColor Red
        return $false
    }
}

# 1. Check Prerequisites
Write-Host "[1/6] Checking Prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Virtual Environment
if (Test-Path "$basePath\.venv\Scripts\python.exe") {
    Write-Host "√ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "× Virtual environment missing!" -ForegroundColor Red
    Write-Host "Run: python -m venv $basePath\.venv" -ForegroundColor Yellow
    exit 1
}

# Ollama
$ollamaRunning = Test-Service "Ollama" "http://localhost:11434/api/tags"
if (-not $ollamaRunning) {
    Write-Host "  Starting Ollama..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

Write-Host ""

# 2. Start Backend
Write-Host "[2/6] Starting Backend API..." -ForegroundColor Yellow

$backendRunning = Test-Service "Backend" "http://localhost:8000/health"
if (-not $backendRunning) {
    Write-Host "  Starting backend..." -ForegroundColor Yellow
    Start-Process cmd -ArgumentList "/k", "cd /d $studypulsePath && title Backend API && color 0E && call $basePath\.venv\Scripts\activate.bat && cd backend && python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0" -WindowStyle Normal
    
    Write-Host "  Waiting 15 seconds for backend to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
    
    $backendRunning = Test-Service "Backend" "http://localhost:8000/health"
}

Write-Host ""

# 3. Start Qdrant for RAG (Optional)
Write-Host "[3/6] Setting up RAG Pipeline..." -ForegroundColor Yellow

docker info >$null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "√ Docker is running" -ForegroundColor Green
    
    # Check if Qdrant container exists
    $qdrantExists = docker ps -a --filter "name=qdrant" --format "{{.Names}}" | Select-String -Pattern "qdrant"
    
    if ($qdrantExists) {
        # Start existing container
        docker start qdrant >$null 2>&1
        Write-Host "  Started existing Qdrant container" -ForegroundColor Gray
    } else {
        # Create new container
        Write-Host "  Creating Qdrant container..." -ForegroundColor Yellow
        docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant >$null 2>&1
    }
    
    Start-Sleep -Seconds 5
    $qdrantRunning = Test-Service "Qdrant" "http://localhost:6333"
} else {
    Write-Host "× Docker not running - RAG features will be limited" -ForegroundColor Yellow
    $qdrantRunning = $false
}

Write-Host ""

# 4. Kill locked Flutter processes
Write-Host "[4/6] Preparing Flutter..." -ForegroundColor Yellow

Get-Process | Where-Object {$_.ProcessName -like "*dart*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "√ Flutter processes cleaned" -ForegroundColor Green
Write-Host ""

# 5. Start Mobile App
Write-Host "[5/6] Starting Mobile App..." -ForegroundColor Yellow

Set-Location "$studypulsePath\mobile"

# Clean build
Remove-Item -Recurse -Force .dart_tool, build -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "  Starting Flutter web app..." -ForegroundColor Gray
Start-Process cmd -ArgumentList "/k", "cd /d $studypulsePath\mobile && title Mobile App && color 0D && flutter run -d chrome --web-port=8080 --web-hostname=localhost" -WindowStyle Normal

Write-Host "  Waiting 20 seconds for Flutter to compile..." -ForegroundColor Gray
Start-Sleep -Seconds 20

$mobileRunning = Test-Service "Mobile App" "http://localhost:8080"

Write-Host ""

# 6. Run Tests
Write-Host "[6/6] Testing API Endpoints..." -ForegroundColor Yellow
Write-Host ""

# Test Health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "√ Health Check: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "× Health Check Failed" -ForegroundColor Red
}

# Test Exams List
try {
    $exams = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/exams/" -Method GET
    Write-Host "√ Exams API: $($exams.Count) exams available" -ForegroundColor Green
} catch {
    Write-Host "× Exams API Failed" -ForegroundColor Red
}

# Test Documentation
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    Write-Host "√ API Docs: Available at http://localhost:8000/docs" -ForegroundColor Green
} catch {
    Write-Host "× API Docs Failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                 Service Status" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend API       : " -NoNewline
if ($backendRunning) { Write-Host "RUNNING  " -ForegroundColor Green -NoNewline } else { Write-Host "STOPPED  " -ForegroundColor Red -NoNewline }
Write-Host "http://localhost:8000"

Write-Host "Mobile App        : " -NoNewline
if ($mobileRunning) { Write-Host "RUNNING  " -ForegroundColor Green -NoNewline } else { Write-Host "STARTING " -ForegroundColor Yellow -NoNewline }
Write-Host "http://localhost:8080"

Write-Host "Ollama AI         : " -NoNewline
if ($ollamaRunning) { Write-Host "RUNNING  " -ForegroundColor Green -NoNewline } else { Write-Host "STOPPED  " -ForegroundColor Red -NoNewline }
Write-Host "http://localhost:11434"

Write-Host "Qdrant (RAG)      : " -NoNewline
if ($qdrantRunning) { Write-Host "RUNNING  " -ForegroundColor Green -NoNewline } else { Write-Host "OPTIONAL " -ForegroundColor Gray -NoNewline }
Write-Host "http://localhost:6333"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($backendRunning -and ($mobileRunning -or $true)) {
    Write-Host "SUCCESS! Your app is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Open Chrome and go to: " -NoNewline
    Write-Host "http://localhost:8080" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "API Documentation: " -NoNewline
    Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    
    # Auto-open browser
    Start-Process "http://localhost:8080"
    Start-Process "http://localhost:8000/docs"
} else {
    Write-Host "ISSUES DETECTED - Check the service windows for errors" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to see live monitoring..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Live monitoring loop
Write-Host "`nLive Monitoring (Press Ctrl+C to stop)..." -ForegroundColor Cyan
Write-Host ""

while ($true) {
    Clear-Host
    Write-Host "StudyPulse - Live Status Monitor" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray
    
    $backendOk = Test-Service "Backend API" "http://localhost:8000/health"
    $mobileOk = Test-Service "Mobile App" "http://localhost:8080"
    $ollamaOk = Test-Service "Ollama AI" "http://localhost:11434/api/tags"
    
    Write-Host ""
    
    # Show active connections
    Write-Host "Active Ports:" -ForegroundColor Yellow
    netstat -ano | Select-String ":8000|:8080|:11434|:6333" | ForEach-Object { 
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 5
}
