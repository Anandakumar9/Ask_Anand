# Railway Logs Analyzer - Quick Start Guide

## Quick Usage

### Option 1: Direct Analysis (Recommended)
```bash
railway logs --service backend | python analyze_railway_logs.py
```

### Option 2: Save and Analyze Later
```bash
# Save logs
railway logs --service backend > logs.txt

# Analyze
python analyze_railway_logs.py logs.txt
```

### Option 3: Live Monitoring
```bash
railway logs --service backend --follow | python analyze_railway_logs.py
```

## First-Time Setup

### 1. Install Railway CLI
```bash
npm i -g @railway/cli
```

### 2. Login and Link
```bash
railway login
cd your-project-directory
railway link
```

### 3. Test It
```bash
railway logs --service backend | python analyze_railway_logs.py
```

## What It Analyzes

The script looks for:
- ❌ **AttributeErrors** - Critical database access issues
- 🗄️ **DATABASE_URL messages** - Connection string issues
- 🚂 **Deployment markers** - Confirms code is deploying
- ✅ **Database success** - Successful connections
- ✅ **Cache cleared** - Build cache status
- ⚠️ **Other errors** - General application failures

## Example Output

```
================================================================================
  RAILWAY LOGS ANALYSIS REPORT
================================================================================

Total log lines analyzed: 22

SUMMARY STATISTICS
  ❌ AttributeErrors Found............................. 1
  ✅ DATABASE_URL Messages............................. 4
  ✅ Deployment Markers................................ 2
  ✅ Database Success Messages......................... 3
  ✅ Cache Cleared Messages............................ 2

ERROR RATE:
  Errors: 40.0% (2 errors)
  Success: 60.0% (3 successes)

RECOMMENDATIONS
  [recommendations based on findings...]
```

## Common Scenarios

### Scenario 1: No DATABASE_URL Found
**Problem:** Script shows "No DATABASE_URL messages found"
**Solution:**
1. Go to Railway dashboard
2. Click on your backend service
3. Go to Variables tab
4. Check if DATABASE_URL is set
5. If missing, add it or link PostgreSQL service

### Scenario 2: AttributeErrors Detected
**Problem:** Script shows multiple AttributeErrors
**Possible causes:**
- Database connection not initialized
- Accessing database before connection established
- SQLAlchemy session issues

**Debug steps:**
1. Check `studypulse/backend/app/database.py`
2. Verify `get_db()` dependency
3. Check if database is initialized in main.py
4. Review the specific line causing AttributeError

### Scenario 3: 100% Error Rate
**Problem:** No successful database connections
**Diagnosis:**
1. PostgreSQL service not running
2. Wrong DATABASE_URL format
3. Network issues between services

**Solution:**
```bash
# Check services status
railway status

# Check variables
railway variables

# Check PostgreSQL service specifically
railway logs --service postgres
```

### Scenario 4: Mixed Results
**Problem:** Some successes, some failures
**Analysis:** This usually means:
- Database connects initially
- Specific code paths have issues
- Race conditions or timing issues

**Action:** Look at the exact line numbers and code paths in the errors

## Advanced Usage

### Get Logs from Specific Time Range
```bash
# Last hour
railway logs --service backend --hours 1 | python analyze_railway_logs.py

# Last 24 hours
railway logs --service backend --hours 24 | python analyze_railway_logs.py
```

### Analyze Specific Deployment
```bash
# Get deployment ID
railway status

# Analyze that deployment
railway logs --service backend --deployment <id> | python analyze_railway_logs.py
```

### Save Analysis Report
```bash
railway logs --service backend | python analyze_railway_logs.py --no-color > analysis_report.txt
```

### Filter Before Analysis
```bash
# Only errors
railway logs --service backend | grep -i error | python analyze_railway_logs.py

# Only database-related
railway logs --service backend | grep -i database | python analyze_railway_logs.py

# Last 100 lines
railway logs --service backend | tail -100 | python analyze_railway_logs.py
```

## Help Commands

```bash
# Script help
python analyze_railway_logs.py --help

# Railway CLI instructions
python analyze_railway_logs.py --help-railway

# Railway CLI help
railway logs --help
```

## Troubleshooting the Script

### Issue: Colors not showing
**Solution:** Your terminal may not support ANSI colors
```bash
python analyze_railway_logs.py --no-color logs.txt
```

### Issue: Emojis showing as boxes
**Solution:** Already handled automatically on Windows. If issues persist:
```bash
# Windows: Set console to UTF-8
chcp 65001
python analyze_railway_logs.py logs.txt
```

### Issue: "No input provided"
**Solution:** You need to either pipe logs or provide a file:
```bash
# Wrong
python analyze_railway_logs.py

# Correct
railway logs --service backend | python analyze_railway_logs.py
# or
python analyze_railway_logs.py logs.txt
```

## Integration with Your Workflow

### Daily Health Check
```bash
#!/bin/bash
# save as: check_railway_health.sh

railway logs --service backend --hours 24 | python analyze_railway_logs.py > daily_report.txt
cat daily_report.txt
```

### Pre-Deployment Check
```bash
# Before deploying, check current status
railway logs --service backend --hours 1 | python analyze_railway_logs.py
```

### Post-Deployment Verification
```bash
# After deploying, monitor for issues
railway logs --service backend --follow | python analyze_railway_logs.py
```

## Understanding the Recommendations

The script provides intelligent recommendations based on what it finds:

- **✅ Green recommendations** = System is healthy
- **⚠️ Yellow recommendations** = Warnings, investigate
- **❌ Red recommendations** = Critical issues, fix immediately

### Healthy System Signs
- Deployment markers present
- More successes than errors
- DATABASE_URL messages found
- Error rate < 20%

### Warning Signs
- Error rate between 20-50%
- Some AttributeErrors present
- Mixed success/failure pattern

### Critical Issues
- Error rate > 50%
- No successful database connections
- No deployment markers
- Missing DATABASE_URL

## Need More Help?

1. Check the full README: `RAILWAY_LOGS_ANALYZER_README.md`
2. Railway documentation: https://docs.railway.app/
3. View sample analysis: Run script on `sample_railway_logs.txt`

## File Locations

- Script: `studypulse/backend/analyze_railway_logs.py`
- Sample logs: `studypulse/backend/sample_railway_logs.txt`
- Full README: `studypulse/backend/RAILWAY_LOGS_ANALYZER_README.md`
- This guide: `studypulse/backend/RAILWAY_LOGS_QUICK_START.md`
