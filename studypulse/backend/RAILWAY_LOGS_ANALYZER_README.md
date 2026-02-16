# Railway Logs Analyzer

A comprehensive Python script for analyzing Railway deployment logs, specifically designed to diagnose PostgreSQL connection issues and track deployment status.

## Features

- **Pattern Detection**: Automatically identifies and categorizes:
  - AttributeErrors (common database connection issues)
  - DATABASE_URL messages and environment variables
  - Railway deployment markers (🚂 RAILWAY DEPLOYMENT CHECK)
  - Successful database connections
  - Python cache clearing confirmations
  - General errors and exceptions

- **Statistics & Metrics**:
  - Error count vs successful connection count
  - Error rate percentage
  - Connection attempt tracking
  - Line-by-line analysis with timestamps

- **Color-Coded Output**: Easy-to-read terminal output with:
  - Red for errors
  - Green for successes
  - Yellow for warnings
  - Blue for informational messages

- **Smart Recommendations**: Provides actionable suggestions based on detected patterns

## Installation

### Prerequisites

1. **Python 3.6+** (already installed)

2. **Railway CLI** (if you want to fetch logs directly):
   ```bash
   npm i -g @railway/cli
   ```

## Usage

### Method 1: Pipe logs directly from Railway CLI

```bash
# Analyze current logs
railway logs --service backend | python analyze_railway_logs.py

# Follow live logs (updates in real-time)
railway logs --service backend --follow | python analyze_railway_logs.py
```

### Method 2: Save logs to file first, then analyze

```bash
# Save logs to file
railway logs --service backend > railway_logs.txt

# Analyze the saved logs
python analyze_railway_logs.py railway_logs.txt
```

### Method 3: Analyze logs with specific time range

```bash
# Get logs from last hour
railway logs --service backend --hours 1 | python analyze_railway_logs.py

# Get logs from specific deployment
railway logs --service backend --deployment <deployment-id> | python analyze_railway_logs.py
```

## Command Line Options

```bash
# Basic usage
python analyze_railway_logs.py <logfile>

# Show Railway CLI help
python analyze_railway_logs.py --help-railway

# Disable colored output (for piping to files)
python analyze_railway_logs.py --no-color railway_logs.txt > analysis.txt

# Show help
python analyze_railway_logs.py --help
```

## Railway CLI Setup

### First-time setup:

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login to Railway
railway login

# 3. Link to your project (run in your project directory)
railway link

# 4. Verify connection
railway status
```

### Useful Railway CLI commands:

```bash
# Get logs for specific service
railway logs --service backend

# Follow logs (live updates)
railway logs --service backend --follow

# Get logs from last N hours
railway logs --service backend --hours 24

# Get logs for specific deployment
railway logs --service backend --deployment <deployment-id>

# List all services
railway status

# Check environment variables
railway variables

# Deploy current directory
railway up
```

## Output Example

```
================================================================================
  RAILWAY LOGS ANALYSIS REPORT
================================================================================

Total log lines analyzed: 1,234

================================================================================
  SUMMARY STATISTICS
================================================================================
  ❌ AttributeErrors Found................................... 5
  ⚪ DATABASE_URL Messages................................... 12
  ✅ Deployment Markers...................................... 3
  ✅ Database Success Messages............................... 8
  ✅ Cache Cleared Messages.................................. 3
  ⚠️  Other Errors........................................... 2
  ⚪ Connection Attempts..................................... 15

ERROR RATE:
  Errors: 38.5% (5 errors)
  Success: 61.5% (8 successes)
```

## Common Issues and Solutions

### Issue: "No DATABASE_URL messages found"
**Solution**: Check Railway dashboard → Variables → Verify DATABASE_URL is set

### Issue: "AttributeErrors detected"
**Possible causes**:
- Database connection not properly initialized
- DATABASE_URL environment variable missing or malformed
- Code trying to access database attributes before connection is established

**Solution**:
1. Verify DATABASE_URL in Railway dashboard
2. Check database.py initialization code
3. Ensure PostgreSQL service is running in Railway

### Issue: "No successful database connections"
**Possible causes**:
- PostgreSQL service not running
- Connection string is incorrect
- Network issues between Railway services

**Solution**:
1. Check Railway dashboard → Services → PostgreSQL status
2. Verify DATABASE_URL format: `postgresql://user:password@host:port/dbname`
3. Check service networking configuration

## Interpreting Results

### Healthy System Signs:
- ✅ Deployment markers present
- ✅ Database success messages > AttributeErrors
- ✅ Low error rate (<20%)
- ✅ Cache cleared messages present

### Warning Signs:
- ⚠️ No DATABASE_URL messages (environment variable may be missing)
- ⚠️ AttributeErrors present (code issue)
- ⚠️ Error rate >50%
- ⚠️ No successful database connections

### Critical Issues:
- ❌ 100% error rate
- ❌ No deployment markers (code not deploying)
- ❌ Multiple AttributeErrors with no successes

## Advanced Usage

### Save analysis to file:

```bash
railway logs --service backend | python analyze_railway_logs.py --no-color > analysis.txt
```

### Analyze logs from multiple services:

```bash
# Backend logs
railway logs --service backend > backend_logs.txt
python analyze_railway_logs.py backend_logs.txt > backend_analysis.txt

# Frontend logs (if needed)
railway logs --service frontend > frontend_logs.txt
python analyze_railway_logs.py frontend_logs.txt > frontend_analysis.txt
```

### Filter logs before analysis:

```bash
# Only analyze last 100 lines
railway logs --service backend | tail -100 | python analyze_railway_logs.py

# Only analyze logs containing "database"
railway logs --service backend | grep -i database | python analyze_railway_logs.py
```

## Troubleshooting

### Script doesn't run:
```bash
# Make it executable
chmod +x analyze_railway_logs.py

# Or run with python directly
python analyze_railway_logs.py
```

### Railway CLI not found:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Verify installation
railway --version
```

### No logs appearing:
```bash
# Check if you're logged in
railway login

# Check if project is linked
railway status

# Try linking again
railway link
```

## File Location

Script location: `studypulse/backend/analyze_railway_logs.py`

## Support

For Railway-specific issues: https://docs.railway.app/
For script issues: Check the script's inline documentation or comments

## License

Part of the StudyPulse project.
