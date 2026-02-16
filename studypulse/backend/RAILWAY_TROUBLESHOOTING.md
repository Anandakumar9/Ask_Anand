# Railway Deployment Troubleshooting Guide

This guide helps you diagnose and fix common Railway deployment issues for StudyPulse Backend.

---

## Section 1: Quick Verification Checklist

### 1.1 Verify DATABASE_URL is Set Correctly

**Railway Dashboard:**
1. Open your Railway project
2. Click on your backend service
3. Go to **Variables** tab
4. Look for `DATABASE_URL`
5. Verify it starts with `postgresql://` (Railway format)
6. Should look like: `postgresql://user:password@host.railway.internal:5432/railway`

**Using Railway CLI:**
```bash
# View all environment variables
railway variables

# Check DATABASE_URL specifically
railway run printenv DATABASE_URL
```

**Expected Output:**
```
postgresql://postgres:randompassword@containers-us-west-xxx.railway.app:5432/railway
```

**Important Notes:**
- Railway provides `postgresql://` but your app converts it to `postgresql+asyncpg://` automatically
- The conversion happens in `app/core/config.py` during startup
- Check deployment logs for this message: `✅ [CONFIG DEBUG] Converting postgresql:// to postgresql+asyncpg://`

### 1.2 Check Which Dockerfile Railway is Using

**Method 1: Railway Dashboard**
1. Go to your service in Railway
2. Click **Settings** tab
3. Look for **Build** section
4. Check if it shows:
   - `DOCKERFILE` (using your Dockerfile)
   - `NIXPACKS` (using railway.toml or auto-detection)

**Method 2: Check railway.toml**
```bash
cat railway.toml
```

**Current Configuration:**
Your project uses **NIXPACKS** with this configuration:
```toml
[build]
builder = "NIXPACKS"

[build.nixpacksPlan.phases.install]
cmds = ["pip install -r requirements-railway.txt"]

[deploy]
startCommand = "find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; find . -type f -name '*.pyc' -delete 2>/dev/null || true; python -B -c 'print(\"Cache cleared\")'; uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

**Alternative: Using Dockerfile**
If you want to use the Dockerfile instead:
1. Delete or rename `railway.toml` to `railway.toml.backup`
2. Railway will automatically detect and use `Dockerfile`
3. Redeploy

### 1.3 Verify Latest Code is Deployed

**Check Deployment Marker in Logs:**
```bash
railway logs --tail 100
```

Look for this marker in the startup logs:
```
================================================================================
🚂 RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED
================================================================================
✅ Code Version: 2026-02-16-15:35-UTC
✅ PostgreSQL Support: ENABLED
✅ Using getattr() for DB pool settings
================================================================================
```

**If you don't see this marker:**
- Railway might be using cached Python bytecode
- Need to force cache clearing (see Section 3)

**Check Git Commit:**
```bash
# See what commit you pushed
git log -1 --oneline

# Check if Railway deployed that commit
railway status
```

**Railway Deployment Page:**
1. Go to **Deployments** tab in Railway dashboard
2. Click the latest deployment
3. Check the **Source** section - should show your latest Git commit hash
4. Compare with `git log -1` output

### 1.4 Force a Clean Rebuild

**Method 1: Via Railway Dashboard**
1. Go to your service
2. Click **Settings** tab
3. Scroll to **Danger Zone**
4. Click **Remove All Variables** (optional - back them up first!)
5. Click **Restart Deployment**

**Method 2: Via Railway CLI**
```bash
# Trigger new deployment from latest commit
railway up --detach

# Or force redeploy without code changes
railway redeploy
```

**Method 3: Empty Commit + Push**
```bash
# Create empty commit to force rebuild
git commit --allow-empty -m "chore: Force Railway rebuild"
git push origin master

# Railway will auto-deploy on push
```

**Method 4: Clear Build Cache (Nuclear Option)**
```bash
# This clears ALL build cache
railway run --service=your-service-name -- rm -rf /root/.cache

# Then redeploy
railway redeploy
```

---

## Section 2: Common PostgreSQL Connection Errors

### 2.1 AttributeError: 'Settings' object has no attribute 'DB_POOL_SIZE'

**Error Message:**
```
AttributeError: 'Settings' object has no attribute 'DB_POOL_SIZE'
```

**Cause:**
Railway is using cached Python bytecode (`.pyc` files) from an older version of `config.py` that didn't have the `DB_POOL_SIZE` attribute.

**Solution:**

**Step 1: Verify config.py has the attributes**
```bash
grep "DB_POOL_SIZE" studypulse/backend/app/core/config.py
```

Should show:
```python
DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
```

**Step 2: Ensure cache clearing is working**
Your `railway.toml` already includes cache clearing in the start command. Verify it's running:

```bash
railway logs | grep "Cache cleared"
```

**Step 3: Use getattr() as fallback (Already Fixed)**
Your `database.py` uses `getattr()` to safely access these attributes:
```python
"pool_size": getattr(settings, 'DB_POOL_SIZE', 5),
"max_overflow": getattr(settings, 'DB_MAX_OVERFLOW', 10),
"pool_timeout": getattr(settings, 'DB_POOL_TIMEOUT', 30),
```

This prevents crashes even if the attribute is missing.

**Step 4: Force rebuild**
```bash
# Push empty commit to force rebuild
git commit --allow-empty -m "fix: Force Railway cache clear for DB_POOL_SIZE"
git push origin master
```

### 2.2 Could not parse SQLAlchemy URL

**Error Message:**
```
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from string 'postgresql://...'
```

**Cause:**
One of these issues:
1. DATABASE_URL is malformed
2. Password contains special characters that need URL encoding
3. Missing the `+asyncpg` dialect

**Solution:**

**Step 1: Check DATABASE_URL format**
```bash
railway run printenv DATABASE_URL
```

**Valid formats:**
```
postgresql://user:password@host:5432/database   ← Railway provides this
postgresql+asyncpg://user:password@host:5432/db  ← Your app converts to this
```

**Invalid formats:**
```
postgres://...              ← Old PostgreSQL scheme
postgresql:///database      ← Missing host
postgresql://host/database  ← Missing user
```

**Step 2: Check for password special characters**

If password contains these: `@ ! # $ % ^ & * ( ) + = { } [ ] | : ; " ' < > , . ? /`

Railway should handle encoding automatically, but verify:
```bash
railway run python3 -c "from urllib.parse import urlparse; import os; url=os.environ['DATABASE_URL']; print('Valid' if urlparse(url).hostname else 'Invalid')"
```

**Step 3: Verify auto-conversion is working**

Check startup logs for:
```
🔍 [CONFIG DEBUG] DATABASE_URL received: 'postgresql://...'
✅ [CONFIG DEBUG] Converting postgresql:// to postgresql+asyncpg://
✓ Database URL scheme: postgresql+asyncpg
✓ Database host: containers-us-west-xxx.railway.app
```

If you don't see these logs, the config.py conversion isn't running.

**Step 4: Manual fix (if needed)**

Add this environment variable in Railway:
```bash
# In Railway Variables tab
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/railway
```

### 2.3 Connection Timeout Errors

**Error Message:**
```
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
```

**Cause:**
1. Database service is down or unreachable
2. Connection pool exhausted (too many concurrent requests)
3. Network issues between Railway containers

**Solution:**

**Step 1: Verify PostgreSQL service is running**
```bash
# Check all services
railway status

# Check PostgreSQL specifically
railway logs --service postgres
```

**Step 2: Test connection**
```bash
# Use Railway's internal DNS
railway run python3 -c "import asyncpg, asyncio; asyncio.run(asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql://', 'postgresql://')))"
```

**Step 3: Increase connection pool (if needed)**

Add these to Railway Variables:
```bash
DB_POOL_SIZE=10           # Default: 5
DB_MAX_OVERFLOW=20        # Default: 10
DB_POOL_TIMEOUT=60        # Default: 30 seconds
```

**Step 4: Enable connection pre-ping**

This is already enabled in `database.py`:
```python
"pool_pre_ping": True,  # Verify connections before using
"pool_recycle": 3600,   # Recycle connections after 1 hour
```

**Step 5: Check Railway service communication**

Ensure services are in the same project:
1. Go to Railway dashboard
2. Verify both backend and postgres are in the same project
3. Check if postgres has a **private network** enabled

---

## Section 3: Cache Issues

### 3.1 Why Python Bytecode Caching Causes Stale Code

**The Problem:**

Python automatically creates `.pyc` files (bytecode) when importing modules:
```
app/
├── core/
│   ├── __pycache__/
│   │   ├── config.cpython-311.pyc     ← Cached version
│   │   └── database.cpython-311.pyc   ← May be outdated!
│   ├── config.py                       ← New code
│   └── database.py                     ← New code
```

**When it happens:**
1. Railway builds your app (creates `.pyc` files)
2. You push new code
3. Railway reuses cached `.pyc` files (faster builds)
4. Your new Python code is ignored!

**Symptoms:**
- AttributeError for newly added fields
- Old code behavior despite pushing changes
- Database connection errors after config changes
- Deployment marker doesn't update

### 3.2 How to Verify Cache is Being Cleared

**Method 1: Check Startup Logs**

```bash
railway logs --tail 50 | grep -i "cache"
```

Look for:
```
✅ Python cache cleared
Cache cleared
find: '/app/__pycache__': removed
```

**Method 2: Check for __pycache__ folders**

```bash
railway run find /app -type d -name __pycache__
```

Should return empty or "No such file or directory"

**Method 3: Check deployment timestamp**

Your code has a deployment marker in `database.py`:
```python
# RAILWAY DEPLOYMENT MARKER: 2026-02-16-15:35-UTC
print("✅ Code Version: 2026-02-16-15:35-UTC")
```

Check if this appears in logs:
```bash
railway logs | grep "Code Version"
```

**Method 4: Test a known change**

Add a unique print statement to `app/main.py`:
```python
print("🔍 DEPLOYMENT TEST: 2026-02-16-22:00-UTC")
```

Push and check logs for this exact message.

### 3.3 How to Manually Force Cache Clearing

**Method 1: Python -B flag (Already Active)**

Your `railway.toml` uses `python -B`:
```bash
python -B -c 'print("Cache cleared")'
```

The `-B` flag prevents Python from writing `.pyc` files.

**Method 2: Find and Delete**

Your startup command already does this:
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true
```

**Method 3: PYTHONDONTWRITEBYTECODE Environment Variable**

Add to Railway Variables:
```bash
PYTHONDONTWRITEBYTECODE=1
```

This prevents Python from creating `.pyc` files at all.

**Method 4: Dockerfile Cache Clearing**

If using Dockerfile instead of Nixpacks, add to CMD:
```dockerfile
CMD find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
    find /app -type f -name '*.pyc' -delete 2>/dev/null || true; \
    echo "✅ Python cache cleared"; \
    exec gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker
```

**Method 5: Clear Railway Build Cache**

```bash
# Nuclear option: delete all cached layers
railway variables set RAILWAY_CACHE_BUST=$(date +%s)

# Then redeploy
railway redeploy
```

**Method 6: Restart with Fresh Container**

```bash
# Stop all running instances
railway down

# Start fresh
railway up --detach
```

---

## Section 4: Railway CLI Commands

### 4.1 How to View Logs

**Real-time logs (live tail):**
```bash
railway logs --tail
```

**Last 100 lines:**
```bash
railway logs --tail 100
```

**Filter by keyword:**
```bash
railway logs | grep "ERROR"
railway logs | grep "DATABASE"
railway logs | grep "postgresql"
```

**Specific service:**
```bash
railway logs --service studypulse-backend
```

**Time-based:**
```bash
# Logs from last 1 hour
railway logs --since 1h

# Logs from last 30 minutes
railway logs --since 30m
```

**Export logs to file:**
```bash
railway logs --tail 1000 > deployment_logs.txt
```

### 4.2 How to Check Environment Variables

**List all variables:**
```bash
railway variables
```

**Check specific variable:**
```bash
railway run printenv DATABASE_URL
railway run printenv SECRET_KEY
railway run printenv ENVIRONMENT
```

**Verify variable is set:**
```bash
railway run bash -c 'echo "DATABASE_URL=${DATABASE_URL:0:30}..."'
```

**Check all environment in running container:**
```bash
railway run printenv | sort
```

**Export variables to .env file (for local testing):**
```bash
railway variables > .env.railway
```

### 4.3 How to Trigger Manual Deploys

**Deploy from current directory:**
```bash
railway up
```

**Deploy specific directory:**
```bash
railway up --path studypulse/backend
```

**Deploy and detach (don't wait):**
```bash
railway up --detach
```

**Redeploy without code changes:**
```bash
railway redeploy
```

**Deploy specific service:**
```bash
railway up --service studypulse-backend
```

**Deploy from specific Git branch:**
```bash
git checkout feature-branch
git push origin feature-branch
railway up
```

### 4.4 How to Check Build Status

**Check current deployment status:**
```bash
railway status
```

Output:
```
Service: studypulse-backend
Environment: production
Status: RUNNING
Deployment: #42 (Active)
URL: https://studypulse-backend-production.railway.app
```

**Check all deployments:**
```bash
railway deployments
```

**Check specific deployment:**
```bash
railway deployment logs <deployment-id>
```

**Watch deployment progress:**
```bash
railway up && railway logs --tail
```

**Check build time:**
```bash
railway status | grep "Build Time"
```

---

## Section 5: Testing the Deployment

### 5.1 Step-by-Step Testing Instructions

**Step 1: Deploy the Backend**

```bash
# Ensure you're in the backend directory
cd studypulse/backend

# Commit any pending changes
git add .
git commit -m "test: Verify Railway deployment"
git push origin master

# Railway auto-deploys on push, or trigger manually:
railway up --detach
```

**Step 2: Wait for Deployment**

```bash
# Watch logs in real-time
railway logs --tail
```

Wait for the build to complete (usually 2-3 minutes).

**Step 3: Check Service URL**

```bash
railway status
```

Note the URL (e.g., `https://studypulse-backend-production.railway.app`)

**Step 4: Test Health Endpoint**

```bash
# Test if server responds
curl https://your-backend-url.railway.app/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "StudyPulse API",
#   "version": "v1"
# }
```

**Step 5: Test API Root**

```bash
curl https://your-backend-url.railway.app/api/v1/

# Expected response:
# {
#   "message": "StudyPulse API is running",
#   "version": "v1",
#   "documentation": "/docs"
# }
```

**Step 6: Check PostgreSQL Connection**

```bash
# Test database connection via API
curl https://your-backend-url.railway.app/api/v1/health/db

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "type": "postgresql"
# }
```

**Step 7: View API Documentation**

Open in browser:
```
https://your-backend-url.railway.app/docs
```

You should see the FastAPI interactive documentation.

### 5.2 Expected Log Output for Successful Deployment

**During Build:**
```
==> Building application
==> Installing Python dependencies
Collecting fastapi
Collecting sqlalchemy
...
==> Build completed successfully

==> Starting deployment
```

**During Startup:**
```
================================================================================
🚂 RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED
================================================================================
✅ Code Version: 2026-02-16-15:35-UTC
✅ PostgreSQL Support: ENABLED
✅ Using getattr() for DB pool settings
================================================================================

🔍 [CONFIG DEBUG] DATABASE_URL received: 'postgresql://postgres:...'
✅ [CONFIG DEBUG] Converting postgresql:// to postgresql+asyncpg://
✓ Database URL scheme: postgresql+asyncpg
✓ Database host: containers-us-west-xxx.railway.app

✓ Database engine created successfully (type: PostgreSQL)
Using PostgreSQL with connection pool (size=5, max_overflow=10)

INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**After First Request:**
```
INFO:     10.0.0.1:12345 - "GET /health HTTP/1.1" 200 OK
```

**What to Look For:**
- ✅ "RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED"
- ✅ "Converting postgresql:// to postgresql+asyncpg://"
- ✅ "Database engine created successfully"
- ✅ "Using PostgreSQL with connection pool"
- ✅ "Application startup complete"
- ✅ "Uvicorn running on..."

**Red Flags (Errors to Address):**
- ❌ "AttributeError: 'Settings' object has no attribute"
- ❌ "Could not parse SQLAlchemy URL"
- ❌ "Connection refused"
- ❌ "TimeoutError"
- ❌ "ModuleNotFoundError"

### 5.3 How to Verify PostgreSQL Connection Works

**Method 1: Via Health Endpoint**

Create a health check in `app/main.py` (if not exists):
```python
@app.get("/health/db")
async def health_db():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

Test it:
```bash
curl https://your-backend-url.railway.app/health/db
```

**Method 2: Railway Shell**

```bash
# Open shell in running container
railway run bash

# Test connection
python3 << 'EOF'
import asyncio
import asyncpg
import os

async def test():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://'))
        result = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL Connected!")
        print(f"Version: {result}")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test())
EOF
```

**Method 3: Check Logs for Database Queries**

```bash
railway logs | grep -i "select\|insert\|update\|delete"
```

Should show SQL queries if the connection is active.

**Method 4: Railway PostgreSQL Plugin Logs**

```bash
# View PostgreSQL service logs
railway logs --service postgres

# Check for connections
railway logs --service postgres | grep "connection"
```

**Method 5: Test Creating a Table**

```bash
railway run python3 << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def test():
    engine = create_async_engine(os.environ['DATABASE_URL'].replace('postgresql://', 'postgresql+asyncpg://'))
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await conn.execute(text("INSERT INTO test_connection (message) VALUES ('Railway connection test')"))
        result = await conn.execute(text("SELECT * FROM test_connection"))
        rows = result.fetchall()
        print(f"✅ Table created and data inserted successfully!")
        print(f"Rows: {len(rows)}")
    await engine.dispose()

asyncio.run(test())
EOF
```

---

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| Stale code deployed | `git commit --allow-empty -m "chore: Force rebuild" && git push` |
| AttributeError for DB_POOL_SIZE | Already fixed with `getattr()` in database.py |
| DATABASE_URL not found | Add in Railway Variables: `DATABASE_URL=${{Postgres.DATABASE_URL}}` |
| Connection timeout | Increase pool size: `DB_POOL_SIZE=10` `DB_MAX_OVERFLOW=20` |
| Cache not clearing | Add Railway variable: `PYTHONDONTWRITEBYTECODE=1` |
| Build fails | Check `railway logs` and verify `requirements-railway.txt` is valid |
| Wrong Dockerfile used | Delete `railway.toml` to force Dockerfile build |
| Secret key error | Generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |

---

## Getting Help

**Railway Status:**
https://status.railway.app

**Railway Documentation:**
https://docs.railway.app

**Railway Community Discord:**
https://discord.gg/railway

**View Railway Service Metrics:**
```bash
railway metrics
```

**Check Railway Service Health:**
```bash
railway status --service studypulse-backend --verbose
```

---

## Related Documentation

- [RAILWAY_ENV_SETUP.md](./RAILWAY_ENV_SETUP.md) - Environment variables setup
- [Dockerfile](./Dockerfile) - Docker build configuration
- [railway.toml](./railway.toml) - Railway deployment configuration
- [requirements-railway.txt](./requirements-railway.txt) - Production dependencies

---

**Last Updated:** 2026-02-16
**Tested Railway Version:** Latest
**Python Version:** 3.11+
**Database:** PostgreSQL 15+
