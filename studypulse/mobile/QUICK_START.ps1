# Quick Start - Recommended Approach
# Use web-server mode (most reliable) and manually open browser

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  StudyPulse Mobile - Quick Start" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$mobilePath = "c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\mobile"
cd $mobilePath

# Check for existing Flutter processes
Write-Host "[1/3] Checking for existing Flutter processes..." -ForegroundColor Cyan
$flutterProcesses = Get-Process -Name "dart", "flutter" -ErrorAction SilentlyContinue
if ($flutterProcesses) {
    Write-Host "  [INFO] Stopping existing Flutter processes..." -ForegroundColor Yellow
    Stop-Process -Name "dart", "flutter" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  [OK] Cleaned up" -ForegroundColor Green
} else {
    Write-Host "  [OK] No existing processes" -ForegroundColor Green
}
Write-Host ""

Write-Host "[2/3] Starting Flutter in web-server mode..." -ForegroundColor Cyan
Write-Host "  [INFO] This mode is most reliable and doesn't require Chrome debug mode" -ForegroundColor Gray
Write-Host ""

# Start Flutter in background and capture output
$flutterCmd = "C:\src\flutter\bin\flutter.bat"
Start-Process -FilePath $flutterCmd -ArgumentList "run", "-d", "web-server", "--web-port=8082", "--web-hostname=0.0.0.0" -WindowStyle Normal

Write-Host "  [INFO] Waiting for app to compile (30-60 seconds)..." -ForegroundColor Yellow
Write-Host "  [INFO] This is a one-time compilation, next runs will be faster" -ForegroundColor Gray
Write-Host ""

# Wait and check if port is listening
$maxWait = 90
$waited = 0
$isReady = $false

while ($waited -lt $maxWait -and -not $isReady) {
    Start-Sleep -Seconds 3
    $waited += 3

    $connection = Get-NetTCPConnection -LocalPort 8082 -ErrorAction SilentlyContinue
    if ($connection) {
        $isReady = $true
        # Give it 3 more seconds to fully initialize
        Start-Sleep -Seconds 3
    } else {
        Write-Host "  [WAIT] Compiling... ($waited seconds elapsed)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($isReady) {
    Write-Host "[3/3] App is ready!" -ForegroundColor Cyan
    Write-Host "  [OK] Server running on http://localhost:8082" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Opening browser..." -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Start-Sleep -Seconds 1

    # Open in default browser
    Start-Process "http://localhost:8082"

    Write-Host ""
    Write-Host "[SUCCESS] StudyPulse is now running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "App URL:      http://localhost:8082" -ForegroundColor White
    Write-Host "Backend API:  http://localhost:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "Hot Reload Controls (in Flutter window):" -ForegroundColor Gray
    Write-Host "  r - Hot reload" -ForegroundColor White
    Write-Host "  R - Hot restart" -ForegroundColor White
    Write-Host "  q - Quit" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[WARNING] App is taking longer than expected" -ForegroundColor Yellow
    Write-Host "  The app may still be compiling in the background" -ForegroundColor Gray
    Write-Host "  Check the Flutter window for progress" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Once you see 'Running on http://localhost:8082'," -ForegroundColor Gray
    Write-Host "  manually open: http://localhost:8082" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit this window (Flutter will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
