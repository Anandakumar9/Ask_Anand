# Shannon Security Testing - Quick Start

## Prerequisites Check

Before running Shannon, ensure you have:

- [ ] Docker Desktop installed and running
- [ ] StudyPulse backend running on http://localhost:8000
- [ ] Anthropic API key with available credits
- [ ] Shannon cloned and built

## Step-by-Step First Run

### 1. Install Docker Desktop (if not already)

**Windows:**
```powershell
# Download and install from https://www.docker.com/products/docker-desktop
# Or use winget
winget install Docker.DockerDesktop

# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait 30 seconds for Docker to start
Start-Sleep -Seconds 30

# Verify
docker --version
docker ps
```

### 2. Clone and Build Shannon

```powershell
# Create tools directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\tools"
Set-Location "$env:USERPROFILE\tools"

# Clone Shannon repository
git clone https://github.com/KeygraphHQ/shannon.git
Set-Location shannon

# Create .env file
@'
ANTHROPIC_API_KEY=sk-ant-your-key-here
CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
'@ | Out-File ".env" -Encoding UTF8

# Build Docker image (takes 10-15 minutes)
docker build -t shannon .

# Verify build
docker images | Select-String "shannon"
```

### 3. Set Environment Variable

```powershell
# Set for current session
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Set permanently (optional)
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-your-key-here', 'User')
```

### 4. Start StudyPulse Backend

```powershell
# Open new terminal window
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend

# Start backend
uvicorn app.main:app --reload

# Verify it's running (in another terminal)
curl http://localhost:8000/health
```

### 5. Run Shannon Security Test

```powershell
# Go to backend directory
cd c:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend

# Run the automated script
.\scripts\run-shannon-security-test.ps1

# Or run Shannon directly
docker run -it --rm `
  -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY `
  -v "${PWD}:/workspace" `
  shannon `
  --url http://host.docker.internal:8000 `
  --output /workspace/security/reports/first-scan.md
```

### 6. Review the Report

```powershell
# Open the report in VS Code
code security/reports/first-scan.md

# Or view in terminal
Get-Content security/reports/first-scan.md
```

## Expected Output

```
=== Shannon Security Testing ===
Target: http://localhost:8000

[1/6] Checking Docker...
✓ Docker is running

[2/6] Checking backend accessibility...
✓ Backend is accessible

[3/6] Checking Shannon Docker image...
✓ Shannon image found

[4/6] Checking for ANTHROPIC_API_KEY...
✓ API key found

[5/6] Running Shannon security tests...
This may take 5-15 minutes depending on API size...
Output will be saved to: security/reports/shannon-2026-02-10-1530.md

[Scanning endpoints...]
[Testing authentication...]
[Checking for SQL injection...]
[Testing XSS vulnerabilities...]
[Analyzing CORS configuration...]

✓ Shannon completed successfully!

[6/6] Security Test Summary:
  CRITICAL: 0
  HIGH: 2
  MEDIUM: 3

Report saved to: security/reports/shannon-2026-02-10-1530.md

Next steps:
  1. Review the report: code security/reports/shannon-2026-02-10-1530.md
  2. Fix CRITICAL and HIGH issues immediately
  3. Track fixes in security/fixes/
  4. Re-run Shannon to verify fixes
```

## Troubleshooting

### Error: "Docker is not running"

**Fix:**
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Sleep -Seconds 30
docker ps
```

### Error: "Backend is not accessible"

**Fix:**
```powershell
# Check if backend is running
curl http://localhost:8000/health

# If not, start it
cd studypulse/backend
uvicorn app.main:app --reload
```

### Error: "Shannon image not found"

**Fix:**
```powershell
cd $env:USERPROFILE\tools\shannon
docker build -t shannon .
```

### Error: "ANTHROPIC_API_KEY not set"

**Fix:**
```powershell
$env:ANTHROPIC_API_KEY="your-actual-api-key"
```

### Error: "Connection refused to http://host.docker.internal:8000"

**Fix:**
```powershell
# Use localhost instead
docker run -it --rm `
  --network host `
  -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY `
  shannon `
  --url http://localhost:8000
```

## Next Steps After First Run

1. **Review findings** in the generated report
2. **Fix CRITICAL and HIGH issues** immediately
3. **Document fixes** in `security/fixes/`
4. **Re-run Shannon** to verify fixes
5. **Set up monthly automation** with `monthly-security-audit.ps1`
6. **Add to CI/CD** via GitHub Actions

## Ongoing Usage

### Weekly Quick Scan

```powershell
cd studypulse/backend
.\scripts\run-shannon-security-test.ps1
```

### Monthly Full Audit

```powershell
cd studypulse/backend
.\scripts\monthly-security-audit.ps1
```

### Pre-Release Scan

```powershell
cd studypulse/backend
.\scripts\run-shannon-security-test.ps1 -OutputFile "security/reports/pre-release-v1.0.md"
```

---

**Estimated Time for First Run:** 30-45 minutes
- Docker setup: 10 mins
- Shannon build: 15 mins
- First scan: 10 mins
- Report review: 10 mins

**Estimated Time for Subsequent Runs:** 5-10 minutes per scan

---

**Last Updated:** February 10, 2026
