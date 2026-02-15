# Open StudyPulse Mobile App in Browser
# Quick launcher to open the Flutter web app in your default browser

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Opening StudyPulse Mobile App" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$appUrl = "http://localhost:8082"

Write-Host "[1/2] Checking if app is running..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$appUrl" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  [OK] App is running on $appUrl" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] App is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please start the mobile app first:" -ForegroundColor Yellow
    Write-Host "    cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile" -ForegroundColor White
    Write-Host "    .\START_MOBILE.ps1" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/2] Opening in browser..." -ForegroundColor Cyan
Start-Process $appUrl
Write-Host "  [OK] Browser should open shortly" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  If browser didn't open, manually visit:" -ForegroundColor Yellow
Write-Host "  $appUrl" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 2
