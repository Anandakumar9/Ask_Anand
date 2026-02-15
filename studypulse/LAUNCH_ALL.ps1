# StudyPulse - Launch Both Backend and Mobile App
# This script launches both services in separate PowerShell windows

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  StudyPulse - Full Stack Launcher" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse"

Write-Host "[1/2] Starting Backend Server..." -ForegroundColor Cyan
Write-Host "  [INFO] Opening backend in new window..." -ForegroundColor Yellow

# Launch backend in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", "$projectRoot\backend\START_BACKEND.ps1"

Write-Host "  [OK] Backend started (check new window)" -ForegroundColor Green
Write-Host "  [INFO] Waiting 10 seconds for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "[2/2] Starting Mobile App..." -ForegroundColor Cyan
Write-Host "  [INFO] Opening mobile app in new window..." -ForegroundColor Yellow

# Launch mobile in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", "$projectRoot\mobile\START_MOBILE.ps1"

Write-Host "  [OK] Mobile app started (check new window)" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Both services are now running!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:    http://localhost:8001" -ForegroundColor Yellow
Write-Host "API Docs:       http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host "Mobile App:     http://localhost:8082" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check the new PowerShell windows for service status." -ForegroundColor Gray
Write-Host "You can close this window now." -ForegroundColor Gray
Write-Host ""

# Keep window open briefly
Start-Sleep -Seconds 5
