# Shannon Security Testing Script
# Automates security testing for StudyPulse backend

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$OutputFile = "",
    [switch]$Verbose = $false
)

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "`n=== Shannon Security Testing ===" "Cyan"
Write-ColorOutput "Target: $BackendUrl`n" "Yellow"

# Check if Docker is running
Write-ColorOutput "[1/6] Checking Docker..." "Cyan"
try {
    docker ps | Out-Null
    Write-ColorOutput "✓ Docker is running" "Green"
} catch {
    Write-ColorOutput "✗ Docker is not running. Please start Docker Desktop." "Red"
    Write-ColorOutput "Run: Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" "Yellow"
    exit 1
}

# Check if backend is accessible
Write-ColorOutput "`n[2/6] Checking backend accessibility..." "Cyan"
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -TimeoutSec 5 -ErrorAction Stop
    Write-ColorOutput "✓ Backend is accessible" "Green"
} catch {
    Write-ColorOutput "✗ Backend is not accessible at $BackendUrl" "Red"
    Write-ColorOutput "Make sure backend is running: cd studypulse/backend && uvicorn app.main:app --reload" "Yellow"
    exit 1
}

# Check if Shannon image exists
Write-ColorOutput "`n[3/6] Checking Shannon Docker image..." "Cyan"
$hasImage = docker images | Select-String "shannon"
if ($hasImage) {
    Write-ColorOutput "✓ Shannon image found" "Green"
} else {
    Write-ColorOutput "✗ Shannon image not found." "Red"
    Write-ColorOutput "Build it with:" "Yellow"
    Write-ColorOutput "  cd `$env:USERPROFILE\tools\shannon" "Yellow"
    Write-ColorOutput "  docker build -t shannon ." "Yellow"
    exit 1
}

# Check for API key
Write-ColorOutput "`n[4/6] Checking for ANTHROPIC_API_KEY..." "Cyan"
if ([string]::IsNullOrEmpty($env:ANTHROPIC_API_KEY)) {
    Write-ColorOutput "✗ ANTHROPIC_API_KEY not set in environment" "Red"
    Write-ColorOutput "Set it with:" "Yellow"
    Write-ColorOutput "  `$env:ANTHROPIC_API_KEY='your-api-key-here'" "Yellow"
    exit 1
}
Write-ColorOutput "✓ API key found" "Green"

# Prepare output file
if ([string]::IsNullOrEmpty($OutputFile)) {
    $date = Get-Date -Format "yyyy-MM-dd-HHmm"
    $OutputFile = "security/reports/shannon-$date.md"
}

# Create security directory if it doesn't exist
$securityDir = Split-Path -Parent $OutputFile
if (-not (Test-Path $securityDir)) {
    New-Item -ItemType Directory -Force -Path $securityDir | Out-Null
}

Write-ColorOutput "`n[5/6] Running Shannon security tests..." "Cyan"
Write-ColorOutput "This may take 5-15 minutes depending on API size..." "Yellow"
Write-ColorOutput "Output will be saved to: $OutputFile`n" "Yellow"

# Convert Windows path to WSL path for Docker volume mount
$currentPath = Get-Location
$dockerPath = $currentPath -replace '\\', '/' -replace 'C:', '/c'

# Run Shannon
try {
    $dockerArgs = @(
        "run", "-it", "--rm",
        "-e", "ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY",
        "-v", "${currentPath}:/workspace",
        "shannon",
        "--url", "http://host.docker.internal:8000",
        "--output", "/workspace/$OutputFile"
    )

    if ($Verbose) {
        $dockerArgs += "--verbose"
    }

    & docker @dockerArgs

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "`n✓ Shannon completed successfully!" "Green"
    } else {
        Write-ColorOutput "`n✗ Shannon exited with errors" "Red"
        exit 1
    }
} catch {
    Write-ColorOutput "`n✗ Error running Shannon: $_" "Red"
    exit 1
}

# Parse and display summary
Write-ColorOutput "`n[6/6] Security Test Summary:" "Cyan"
if (Test-Path $OutputFile) {
    $reportContent = Get-Content $OutputFile -Raw

    # Try to extract severity counts
    if ($reportContent -match "Critical.*?(\d+)") {
        $critical = $Matches[1]
        if ([int]$critical -gt 0) {
            Write-ColorOutput "  CRITICAL: $critical" "Red"
        }
    }
    if ($reportContent -match "High.*?(\d+)") {
        $high = $Matches[1]
        if ([int]$high -gt 0) {
            Write-ColorOutput "  HIGH: $high" "Yellow"
        }
    }
    if ($reportContent -match "Medium.*?(\d+)") {
        $medium = $Matches[1]
        if ([int]$medium -gt 0) {
            Write-ColorOutput "  MEDIUM: $medium" "Cyan"
        }
    }

    Write-ColorOutput "`nReport saved to: $OutputFile" "Green"
    Write-ColorOutput "`nNext steps:" "Cyan"
    Write-ColorOutput "  1. Review the report: code $OutputFile" "White"
    Write-ColorOutput "  2. Fix CRITICAL and HIGH issues immediately" "White"
    Write-ColorOutput "  3. Track fixes in security/fixes/" "White"
    Write-ColorOutput "  4. Re-run Shannon to verify fixes`n" "White"
} else {
    Write-ColorOutput "✗ Report file not found at $OutputFile" "Red"
}
