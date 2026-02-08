# =============================================================================
# StudyPulse Production Startup - Complete System with RAG Integration
# Author: Senior DevOps Engineer
# Date: February 7, 2026
# =============================================================================

param(
    [switch]$SkipTests = $false,
    [switch]$ProductionMode = $false
)

$ErrorActionPreference = "Continue"

Write-Host @"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         StudyPulse Production System - RAG Integrated         ║
║                                                               ║
║  Backend (FastAPI) + Ollama Phi4 + Qdrant + Mobile Web       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Configuration
$ROOT_DIR = "C:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse"
$BACKEND_DIR = "$ROOT_DIR\backend"
$MOBILE_DIR = "$ROOT_DIR\mobile"
$VENV_PATH = "C:\Users\anand\OneDrive\Desktop\Ask_Anand\.venv"

# Service ports
$BACKEND_PORT = 8000
$MOBILE_PORT = 8080
$OLLAMA_PORT = 11434
$QDRANT_PORT = 6333
$REDIS_PORT = 6379

# =============================================================================
# 1. SYSTEM CHECKS
# =============================================================================

Write-Host "`n[1/7] 🔍 System Health Checks" -ForegroundColor Yellow

# Check Python
Write-Host "   • Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host " ❌ Python not found!" -ForegroundColor Red
    exit 1
}

# Check Flutter
Write-Host "   • Checking Flutter..." -NoNewline
try {
    $flutterVersion = flutter --version 2>&1 | Select-String "Flutter" | Select-Object -First 1
    Write-Host " ✅" -ForegroundColor Green
} catch {
    Write-Host " ⚠️  Flutter not found (mobile app won't start)" -ForegroundColor Yellow
}

# Check Docker
Write-Host "   • Checking Docker..." -NoNewline
try {
    docker ps > $null 2>&1
    Write-Host " ✅ Docker running" -ForegroundColor Green
} catch {
    Write-Host " ❌ Docker not running!" -ForegroundColor Red
    Write-Host "      Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# =============================================================================
# 2. DEPENDENCIES INSTALLATION
# =============================================================================

Write-Host "`n[2/7] 📦 Installing Dependencies" -ForegroundColor Yellow

# Activate virtual environment
Write-Host "   • Activating virtual environment..." -NoNewline
if (Test-Path "$VENV_PATH\Scripts\Activate.ps1") {
    & "$VENV_PATH\Scripts\Activate.ps1"
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ❌ Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Install backend dependencies
Write-Host "   • Installing backend dependencies..." -NoNewline
Set-Location $BACKEND_DIR
pip install -r requirements.txt --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Some packages failed (may still work)" -ForegroundColor Yellow
}

# =============================================================================
# 3. START INFRASTRUCTURE SERVICES
# =============================================================================

Write-Host "`n[3/7] 🚀 Starting Infrastructure Services" -ForegroundColor Yellow

# Start Qdrant Vector Database
Write-Host "   • Starting Qdrant (Vector DB)..." -NoNewline
$qdrantRunning = docker ps --filter "name=studypulse-qdrant" --format "{{.Names}}"
if ($qdrantRunning) {
    Write-Host " ✅ Already running" -ForegroundColor Green
} else {
    docker run -d `
        --name studypulse-qdrant `
        -p ${QDRANT_PORT}:6333 `
        -p 6334:6334 `
        -v qdrant_storage:/qdrant/storage `
        qdrant/qdrant:v1.16.3 > $null 2>&1
    
    Start-Sleep -Seconds 3
    
    try {
        Invoke-WebRequest -Uri "http://localhost:$QDRANT_PORT" -UseBasicParsing -TimeoutSec 2 > $null
        Write-Host " ✅ Started on port $QDRANT_PORT" -ForegroundColor Green
    } catch {
        Write-Host " ❌ Failed to start" -ForegroundColor Red
    }
}

# Start Redis Cache
Write-Host "   • Starting Redis (Cache)..." -NoNewline
$redisRunning = docker ps --filter "name=studypulse-redis" --format "{{.Names}}"
if ($redisRunning) {
    Write-Host " ✅ Already running" -ForegroundColor Green
} else {
    docker run -d `
        --name studypulse-redis `
        -p ${REDIS_PORT}:6379 `
        redis:7-alpine `
        redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru > $null 2>&1
    
    Write-Host " ✅ Started on port $REDIS_PORT" -ForegroundColor Green
}

# Check Ollama
Write-Host "   • Checking Ollama (AI Model)..." -NoNewline
try {
    Invoke-WebRequest -Uri "http://localhost:$OLLAMA_PORT" -UseBasicParsing -TimeoutSec 2 > $null
    Write-Host " ✅ Running on port $OLLAMA_PORT" -ForegroundColor Green
} catch {
    Write-Host " ❌ Not running!" -ForegroundColor Red
    Write-Host "      Please start: ollama serve" -ForegroundColor Red
    exit 1
}

# =============================================================================
# 4. RAG INTEGRATION TEST
# =============================================================================

if (-not $SkipTests) {
    Write-Host "`n[4/7] 🧪 Testing RAG Integration" -ForegroundColor Yellow
    
    Set-Location $BACKEND_DIR
    
    Write-Host "   • Testing Vector Store..." -NoNewline
    $testScript = @"
import sys
sys.path.insert(0, '.')
try:
    from app.rag.vector_store import VectorStore
    vs = VectorStore(host='localhost', port=6333)
    stats = vs.get_collection_stats()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
    
    $result = $testScript | python 2>&1
    if ($result -match "OK") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌ $result" -ForegroundColor Red
    }
    
    Write-Host "   • Testing Semantic Kernel..." -NoNewline
    $testScript = @"
import sys
sys.path.insert(0, '.')
try:
    from app.rag.semantic_kernel_service import SemanticKernelService
    sk = SemanticKernelService()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
    
    $result = $testScript | python 2>&1
    if ($result -match "OK") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  $result" -ForegroundColor Yellow
    }
}

# =============================================================================
# 5. START BACKEND API
# =============================================================================

Write-Host "`n[5/7] 🌐 Starting Backend API" -ForegroundColor Yellow

Set-Location $BACKEND_DIR

Write-Host "   • Launching FastAPI server..." -NoNewline

# Kill existing backend process
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$BACKEND_DIR'; & '$VENV_PATH\Scripts\Activate.ps1'; uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload"

Start-Sleep -Seconds 5

try {
    $response = Invoke-RestMethod -Uri "http://localhost:$BACKEND_PORT/health" -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host " ✅ Running on http://localhost:$BACKEND_PORT" -ForegroundColor Green
        Write-Host "      API Docs: http://localhost:${BACKEND_PORT}/docs" -ForegroundColor Cyan
    }
} catch {
    Write-Host " ❌ Failed to start" -ForegroundColor Red
    Write-Host "      Check the backend window for errors" -ForegroundColor Red
}

# =============================================================================
# 6. START MOBILE APP
# =============================================================================

Write-Host "`n[6/7] 📱 Starting Mobile Web App" -ForegroundColor Yellow

Set-Location $MOBILE_DIR

Write-Host "   • Launching Flutter web..." -NoNewline

# Start Flutter in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$MOBILE_DIR'; flutter run -d chrome --web-port=$MOBILE_PORT"

Write-Host " ✅ Starting..." -ForegroundColor Green
Write-Host "      Compiling... (this takes ~30 seconds)" -ForegroundColor Cyan

# =============================================================================
# 7. FINAL HEALTH CHECKS
# =============================================================================

Write-Host "`n[7/7] ✅ Final Health Checks" -ForegroundColor Yellow

Start-Sleep -Seconds 25  # Wait for Flutter compilation

$services = @(
    @{Name="Backend API"; URL="http://localhost:$BACKEND_PORT/health"; Expected="healthy"},
    @{Name="Qdrant Vector DB"; URL="http://localhost:$QDRANT_PORT"; Expected=""},
    @{Name="Ollama AI"; URL="http://localhost:$OLLAMA_PORT"; Expected=""},
    @{Name="Mobile Web"; URL="http://localhost:$MOBILE_PORT"; Expected=""}
)

$allHealthy = $true

foreach ($service in $services) {
    Write-Host "   • $($service.Name)..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $service.URL -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Write-Host " ✅ Healthy" -ForegroundColor Green
        } else {
            Write-Host " ⚠️  Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " ❌ Unreachable" -ForegroundColor Red
        $allHealthy = $false
    }
}

# =============================================================================
# SUMMARY
# =============================================================================

Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                    SYSTEM READY! 🚀                           ║
╚═══════════════════════════════════════════════════════════════╝

📍 Service URLs:
   • Backend API:    http://localhost:$BACKEND_PORT
   • API Docs:       http://localhost:${BACKEND_PORT}/docs
   • Mobile Web:     http://localhost:$MOBILE_PORT
   • Qdrant Admin:   http://localhost:${QDRANT_PORT}/dashboard

🎯 Key Features Enabled:
   ✅ AI Question Generation (Ollama Phi4)
   ✅ Semantic Search (Qdrant Vector DB)
   ✅ Versioned Prompts (Semantic Kernel)
   ✅ Guest Mode (No Login Required)
   ✅ Redis Caching

📚 Next Steps:
   1. Open Mobile App: http://localhost:$MOBILE_PORT
   2. Browse exams and start studying
   3. Take mock tests (AI + Previous Year questions)
   4. Review RAG_IMPLEMENTATION_SUMMARY.md for details

📊 Monitoring:
   • Backend logs: Check backend PowerShell window
   • Mobile logs: Check mobile PowerShell window
   • Stop all: Ctrl+C in each window

🔧 Troubleshooting:
   • If services fail, check TROUBLESHOOTING.md
   • Re-run this script to restart all services
   • Use -SkipTests flag to skip RAG tests

"@ -ForegroundColor Cyan

if (-not $allHealthy) {
    Write-Host "⚠️  Some services are not healthy. Check the logs above." -ForegroundColor Yellow
}

Write-Host "Press Ctrl+C to stop monitoring..." -ForegroundColor Gray

# Keep monitoring
while ($true) {
    Start-Sleep -Seconds 30
    
    # Quick health check
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:$BACKEND_PORT/health" -TimeoutSec 2
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Backend: ✅ $($backendHealth.status)" -ForegroundColor Green
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Backend: ❌ Down" -ForegroundColor Red
    }
}
