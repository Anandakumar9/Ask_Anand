# Railway PostgreSQL Deployment - Automated Monitoring & Testing

This directory contains automated tools to monitor and verify your Railway deployment until PostgreSQL connection is fully working.

## 🎯 What Was Fixed

**Root Cause:** Railway was using the wrong Dockerfile that didn't clear Python cache, causing old bytecode to load instead of your updated code with `getattr()` fixes.

**Solution Applied:**
1. ✅ Switched to Railway-optimized Dockerfile with cache clearing
2. ✅ Dockerfile now clears `__pycache__` and `.pyc` files on startup
3. ✅ Uses `requirements-railway.txt` (minimal dependencies)
4. ✅ Dynamic `$PORT` configuration for Railway
5. ✅ Code already has `getattr()` for DB pool settings (backward compatible)

## 📁 Monitoring Tools Created

### 1. **continuous_railway_monitor.py**
Automatically checks Railway deployment every 5 minutes until PostgreSQL works.

**Features:**
- Fetches Railway logs via CLI
- Checks for: cache clearing, deployment markers, database connection
- Detects errors: AttributeError, SQLAlchemy URL parsing, connection issues
- Color-coded output with progress indicators
- Runs in a loop until all checks pass

**Usage:**
```bash
# Check every 5 minutes (default)
python continuous_railway_monitor.py

# Check every 1 minute (faster feedback)
python continuous_railway_monitor.py 1

# Check every 10 minutes
python continuous_railway_monitor.py 10
```

### 2. **start_monitor.bat** (Windows)
One-click script to start monitoring.

**Usage:**
```cmd
start_monitor.bat
```

### 3. **test_railway_deployment.py**
One-time test script for your Railway URL.

**Usage:**
```bash
pip install requests colorama
python test_railway_deployment.py https://your-app.railway.app
```

### 4. **analyze_railway_logs.py**
Analyzes Railway logs for PostgreSQL errors.

**Usage:**
```bash
# Analyze live logs
railway logs --service backend | python analyze_railway _logs.py

# Analyze saved logs
python analyze_railway_logs.py railway_logs.txt
```

### 5. **RAILWAY_TROUBLESHOOTING.md**
Comprehensive troubleshooting guide with solutions for common issues.

## 🚀 Quick Start

### Step 1: Install Railway CLI
```bash
npm i -g @railway/cli
railway login
```

### Step 2: Start Continuous Monitoring
```bash
# Windows
start_monitor.bat

# Mac/Linux
python continuous_railway_monitor.py
```

### Step 3: Watch the Output
The monitor will check every 5 minutes and show:
- ✅ Cache cleared
- ✅ Deployment marker present
- ✅ Database connection successful

**When all 3 checks pass, monitoring stops automatically!**

## 📊 What the Monitor Checks

### Positive Indicators ✅
1. **Cache Cleared**: `✅ Python cache cleared` appears in logs
2. **Deployment Marker**: `🚂 RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED` appears
3. **Database Connected**: `✓ Database engine created successfully` appears

### Error Detection ⚠️
1. **AttributeError**: `'Settings' object has no attribute 'DB_POOL_SIZE'`
2. **SQLAlchemy Error**: `Could not parse SQLAlchemy URL`
3. **Connection Errors**: General database connection issues

## 🔧 What to Do If Monitoring Detects Errors

### AttributeError Still Appears
Railway is still using cached bytecode. Solutions:
1. **Force rebuild in Railway dashboard**: Settings → Clear Build Cache → Redeploy
2. **Add environment variable**: `PYTHONDONTWRITEBYTECODE=1`
3. **Verify Dockerfile**: Check that cache clearing commands are present in CMD

### DATABASE_URL Not Found
1. Go to Railway dashboard → Variables
2. Add `DATABASE_URL` with internal PostgreSQL URL:
   ```
   postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway
   ```
3. Redeploy

### Database Connection Timeout
1. Verify PostgreSQL service is running in Railway
2. Check if backend service is linked to PostgreSQL service
3. Test connection in Railway shell: `railway run psql`

## 📝 Expected Timeline

- **0-2 min**: Railway detects new commit and starts build
- **2-5 min**: Docker build completes, container starts
- **5-6 min**: Application starts, database connection initialized
- **6+ min**: First monitoring check should show success

## 🎉 Success Criteria

Monitoring will automatically stop when it sees:
```
✅ Cache Cleared: PASS
✅ Deployment Marker: PRESENT
✅ Database Connection: SUCCESS

🎉 ALL CHECKS PASSED! PostgreSQL is working!
```

## 🔍 Manual Verification (Alternative)

If you prefer not to use automated monitoring:

1. **Go to Railway dashboard** → Your backend service → Logs
2. **Look for these messages**:
   ```
   ✅ Python cache cleared
   🚂 RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED
   ✓ Database engine created successfully
   ```
3. **Test the deployment**:
   ```bash
   curl https://your-app.railway.app/health
   ```

## 📚 Related Documentation

- `RAILWAY_TROUBLESHOOTING.md` - Detailed troubleshooting guide
- `RAILWAY_LOGS_ANALYZER_README.md` - Log analysis tool documentation
- `RAILWAY_LOGS_QUICK_START.md` - Quick reference for common scenarios

## 🆘 Still Having Issues?

1. Run the log analyzer:
   ```bash
   railway logs --service backend | python analyze_railway_logs.py
   ```

2. Check the troubleshooting guide:
   - Read `RAILWAY_TROUBLESHOOTING.md`
   - Look for your specific error message

3. Verify environment variables:
   ```bash
   railway variables --service backend
   ```

4. Force clean rebuild:
   ```bash
   railway up --service backend --detach
   ```

## 💡 Tips

- **First deployment**: Wait 5-6 minutes before first check
- **Redeployments**: Usually faster, 2-3 minutes
- **Log retention**: Railway keeps logs for 7 days
- **Build cache**: Can take 10GB+, clear periodically

---

**Last Updated:** 2026-02-16
**Commit:** fix: Switch to Railway-optimized Dockerfile with cache clearing (36697cf)
