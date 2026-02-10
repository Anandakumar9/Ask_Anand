# Shannon Security Testing Setup Guide

## Overview
Shannon is an AI-powered penetration testing tool that automatically discovers and tests security vulnerabilities in web applications. It uses Claude AI to intelligently probe APIs, test authentication, and identify security flaws.

---

## Prerequisites

### 1. Docker Desktop
Shannon runs in a Docker container with pre-installed security testing tools.

**Installation:**
- Windows/Mac: Download from https://www.docker.com/products/docker-desktop
- Verify installation:
  ```powershell
  docker --version
  docker ps
  ```

### 2. Anthropic API Key
Shannon uses Claude AI for intelligent testing.

- Get your API key from: https://console.anthropic.com
- Make sure you have credits/billing enabled

---

## Installation Steps

### Step 1: Clone Shannon Repository

```powershell
# Create tools directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\tools"
Set-Location "$env:USERPROFILE\tools"

# Clone Shannon
git clone https://github.com/KeygraphHQ/shannon.git
Set-Location shannon
```

### Step 2: Configure Shannon

Create `.env` file in the Shannon directory:

```powershell
# Create .env file
$shannonEnv = @'
ANTHROPIC_API_KEY=your-anthropic-api-key-here
CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000
'@

$shannonEnv | Out-File ".env" -Encoding UTF8
```

**Replace `your-anthropic-api-key-here` with your actual Anthropic API key.**

### Step 3: Build Shannon Docker Image

```powershell
# Build the Docker image (takes 10-15 minutes)
docker build -t shannon .

# Verify the build
docker images | Select-String "shannon"
```

---

## Running Security Tests

### Basic Usage

```powershell
# Make sure StudyPulse backend is running on http://localhost:8000

# Run Shannon against local backend
docker run -it --rm `
  -e ANTHROPIC_API_KEY=your-anthropic-api-key `
  -v "${PWD}:/workspace" `
  shannon `
  --url http://host.docker.internal:8000 `
  --output /workspace/security-report.md
```

### What Shannon Tests

Shannon automatically tests for:
- **SQL Injection** - Database query manipulation
- **Cross-Site Scripting (XSS)** - Script injection
- **Authentication Bypass** - Unauthorized access
- **CORS Misconfiguration** - Cross-origin issues
- **API Endpoint Discovery** - Unmapped/hidden endpoints
- **Input Validation** - Parameter fuzzing
- **Rate Limiting** - DDoS vulnerability
- **JWT Token Security** - Token manipulation
- **File Upload Vulnerabilities** - Malicious file uploads
- **Information Disclosure** - Sensitive data leaks

---

## Automated Testing Script

I've created a PowerShell script for automated security testing.

### Location
`studypulse/backend/scripts/run-shannon-security-test.ps1`

### Usage

```powershell
cd studypulse/backend

# Run security test
.\scripts\run-shannon-security-test.ps1

# Run with custom URL
.\scripts\run-shannon-security-test.ps1 -BackendUrl "http://localhost:8000"

# Run with specific output file
.\scripts\run-shannon-security-test.ps1 -OutputFile "security-audit-2026-02.md"
```

The script will:
1. Check if Docker is running
2. Check if backend is accessible
3. Check if Shannon image exists
4. Run comprehensive security tests
5. Generate detailed security report
6. Output severity summary

---

## Understanding Shannon Reports

### Report Structure

```markdown
# Shannon Security Report - StudyPulse
**Date:** 2026-02-10
**Target:** http://localhost:8000

## Executive Summary
- **Total Findings:** 12
- **Critical:** 1
- **High:** 3
- **Medium:** 5
- **Low:** 3

## Findings

### 1. SQL Injection in Mock Test Endpoint [CRITICAL]
**Endpoint:** POST /api/v1/mock-test/submit
**Finding:** User input not sanitized...
**Exploit:** `{"answer": "'; DROP TABLE users; --"}`
**Recommendation:** Use parameterized queries...

### 2. Missing Rate Limiting [HIGH]
...
```

### Severity Levels

| Severity | Action Required | Timeline |
|----------|----------------|----------|
| **CRITICAL** | Fix immediately | < 24 hours |
| **HIGH** | Fix before next deploy | < 1 week |
| **MEDIUM** | Fix in next sprint | < 1 month |
| **LOW** | Consider for future | Backlog |

---

## Security Testing Workflow

### 1. Before Every Major Release

```powershell
# Week before release
cd studypulse/backend
.\scripts\run-shannon-security-test.ps1

# Review report
code security/shannon-report-*.md

# Fix HIGH and CRITICAL issues
# Re-run Shannon to verify fixes
```

### 2. Monthly Security Audits

Create a scheduled task or reminder:

```powershell
# First Monday of each month
cd studypulse/backend
.\scripts\monthly-security-audit.ps1
```

### 3. After Major Code Changes

Run Shannon after:
- New authentication features
- Database schema changes
- New API endpoints
- Third-party integrations
- File upload features

---

## Common Vulnerabilities & Fixes

### 1. SQL Injection

**Finding:**
```python
# VULNERABLE
query = f"SELECT * FROM users WHERE id = {user_id}"
```

**Fix:**
```python
# SECURE
query = select(User).where(User.id == user_id)  # SQLAlchemy
```

### 2. XSS (Cross-Site Scripting)

**Finding:**
```javascript
// VULNERABLE
element.innerHTML = userInput;
```

**Fix:**
```javascript
// SECURE
element.textContent = userInput;
// or use DOMPurify library
```

### 3. Authentication Bypass

**Finding:**
```python
# VULNERABLE
if user_id:  # Doesn't verify token
    return user
```

**Fix:**
```python
# SECURE
current_user = Depends(get_current_user)  # Verify JWT
```

### 4. CORS Misconfiguration

**Finding:**
```python
# VULNERABLE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Too permissive
)
```

**Fix:**
```python
# SECURE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.studypulse.com",
        "http://localhost:3000"  # Only for dev
    ],
)
```

---

## Integration with CI/CD

### GitHub Actions Workflow

I've created a workflow that runs Shannon on every PR to main/master:

**File:** `.github/workflows/shannon-security.yml`

```yaml
name: Shannon Security Testing

on:
  pull_request:
    branches: [main, master]
  schedule:
    - cron: '0 0 1 * *'  # Monthly on 1st

jobs:
  security-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Start Backend
        run: |
          cd studypulse/backend
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10

      - name: Run Shannon
        run: |
          docker run -it --rm \
            -e ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }} \
            shannon \
            --url http://localhost:8000 \
            --output security-report.md

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: shannon-security-report
          path: security-report.md
```

**Required Secrets:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key

---

## Security Reports Management

### Directory Structure

```
studypulse/backend/security/
├── reports/
│   ├── 2026-02-01-audit.md
│   ├── 2026-02-10-pre-release.md
│   └── archive/
├── fixes/
│   ├── sql-injection-fix.md
│   └── cors-fix.md
└── README.md
```

### Report Retention

- Keep last 12 monthly reports
- Archive older reports
- Track remediation status


---

## Troubleshooting

### Shannon Container Won't Start

**Error:** `Cannot connect to Docker daemon`

**Solution:**
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait for Docker to start
Start-Sleep -Seconds 30

# Verify
docker ps
```

### Shannon Can't Reach Backend

**Error:** `Connection refused to http://host.docker.internal:8000`

**Solution:**
```powershell
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Test from Docker
docker run --rm curlimages/curl curl http://host.docker.internal:8000/health

# 3. If fails, use host network mode
docker run --net=host shannon --url http://localhost:8000
```

### Shannon Reports False Positives

**Solution:**
- Review the finding context
- Test manually to verify
- Add to Shannon ignore list if confirmed false positive
- Document in `security/false-positives.md`

### Out of API Credits

**Error:** `Anthropic API rate limit exceeded`

**Solution:**
- Check usage: https://console.anthropic.com/usage
- Add credits or wait for reset
- Use `--max-requests` flag to limit API calls

---

## Best Practices

### 1. Test in Staging First
Never run Shannon against production without testing in staging first.

### 2. Review Before Automated Fixes
Shannon can suggest fixes, but always review before applying.

### 3. Document Remediation
Track what was fixed, when, and how.

### 4. Regular Cadence
- **Weekly:** Quick scan during development
- **Monthly:** Full comprehensive audit
- **Pre-Deploy:** Always before production releases

### 5. Team Training
Ensure team understands:
- How to read Shannon reports
- Severity levels and timelines
- Common vulnerability patterns
- Where to get help

---

## Resources

### Shannon
- **GitHub:** https://github.com/KeygraphHQ/shannon
- **Benchmarks:** https://github.com/KeygraphHQ/shannon/tree/main/xben-benchmark-results
- **Documentation:** Check repository README

### Security Learning
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **PortSwigger Web Security:** https://portswigger.net/web-security
- **HackTheBox:** https://www.hackthebox.com/ (practice pentesting)

### FastAPI Security
- **Official Docs:** https://fastapi.tiangolo.com/tutorial/security/
- **Security Best Practices:** https://fastapi.tiangolo.com/advanced/security/

---

## Next Steps

1. ✅ **Install Docker Desktop**
2. ✅ **Clone Shannon repository**
3. ✅ **Build Shannon image**
4. ⏳ **Run first security test**
5. ⏳ **Review and fix findings**
6. ⏳ **Set up monthly automation**
7. ⏳ **Integrate with CI/CD**

---

**Last Updated:** February 10, 2026
**Version:** 1.0
**Status:** Ready for Testing 🔒
