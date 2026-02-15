# StudyPulse Backend Startup Script
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  StudyPulse Backend Server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$backendPath = "c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend"
cd $backendPath

# Stop any existing backend processes on port 8001
Write-Host "[0/4] Checking for existing backend processes..." -ForegroundColor Cyan
$existingProcesses = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($existingProcesses) {
    Write-Host "  [INFO] Stopping $($existingProcesses.Count) existing process(es) on port 8001..." -ForegroundColor Yellow
    foreach ($procId in $existingProcesses) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Stopped process $procId" -ForegroundColor Green
        } catch {
            Write-Host "  [WARNING] Could not stop process $procId" -ForegroundColor Yellow
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  [OK] Port 8001 is free" -ForegroundColor Green
}
Write-Host ""

Write-Host "[1/4] Checking virtual environment..." -ForegroundColor Cyan
$venvPath = "venv"
$pythonExe = "$venvPath\Scripts\python.exe"
$pipExe = "$venvPath\Scripts\pip.exe"

if (-Not (Test-Path $pythonExe)) {
    Write-Host "  [ERROR] Virtual environment not found at: $venvPath" -ForegroundColor Red
    Write-Host "  Please create it with: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  [OK] Virtual environment found" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Checking Python version..." -ForegroundColor Cyan
& $pythonExe --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Python not working!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  [OK] Python ready" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Checking dependencies..." -ForegroundColor Cyan
$requirementsHash = (Get-FileHash -Path "requirements.txt" -Algorithm MD5).Hash
$installedFile = ".installed_hash"

if (Test-Path $installedFile) {
    $installedHash = Get-Content $installedFile
    if ($installedHash -eq $requirementsHash) {
        Write-Host "  [OK] Dependencies up to date" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Installing updated dependencies..." -ForegroundColor Yellow
        & $pipExe install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            $requirementsHash | Out-File -FilePath $installedFile
            Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Failed to install dependencies" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  [INFO] Installing dependencies..." -ForegroundColor Yellow
    & $pipExe install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        $requirementsHash | Out-File -FilePath $installedFile
        Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Failed to install dependencies" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[4/4] Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "  [INFO] Server will run on http://localhost:8001" -ForegroundColor Yellow
Write-Host "  [INFO] API docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "  [NOTE] Using Qdrant for vector search (will fallback gracefully if not available)" -ForegroundColor Gray
Write-Host "  [NOTE] Redis cache not required - will use in-memory fallback" -ForegroundColor Gray
Write-Host "  [NOTE] Initialization may take 10-15 seconds on first run" -ForegroundColor Gray
Write-Host ""

# Set environment variable to reduce Redis timeout
$env:REDIS_CONNECT_TIMEOUT = "2"

# Test imports before starting
Write-Host "  [INFO] Testing backend imports..." -ForegroundColor Yellow
& $pythonExe -c "from app.main import app"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Backend import failed! Check the error above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  [OK] Backend imports successful" -ForegroundColor Green
Write-Host ""

& $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
