RAILWAY DEPLOYMENT CHECKLIST
==============================

Our git repository has the CORRECT code with getattr() calls.
Railway is deploying OLD CACHED code from previous builds.

WHAT TO CHECK IN RAILWAY DASHBOARD:

1. ROOT DIRECTORY CONFIGURATION
   - Go to your Railway service settings
   - Look for "Root Directory" or "Working Directory" setting
   - It MUST be set to: studypulse/backend
   - If it's empty or set to "/" or ".", Railway will look in wrong place

2. CONNECTED BRANCH
   - Verify Railway is watching the "master" branch
   - Should auto-deploy on push to master

3. RECENT DEPLOYMENTS
   - Check if Railway detected commits:
     * 3ef6dce - "Add getattr verification"  (just pushed)
     * bcade6f - "Force Railway rebuild trigger" (just pushed)
     * 0af55af - "Force Railway cache bust" (has correct code)
   - If Railway doesn't show these commits, there's a GitHub connection issue

4. MANUAL REDEPLOY
   - Click the "..." menu on your service
   - Select "Redeploy"
   - This forces Railway to pull latest code from GitHub

5. BUILD LOGS TO WATCH FOR:
   When Railway rebuilds, you should see:
   ```
   === RAILWAY REBUILD <timestamp> ===
   === VERIFYING DATABASE.PY HAS GETATTR ===
   39:        "pool_size": getattr(settings, 'DB_POOL_SIZE', 5),
   40:        "max_overflow": getattr(settings, 'DB_MAX_OVERFLOW', 10),
   ```

   If you see "ERROR: getattr not found!" then Railway pulled wrong code.

6. EXPECTED SUCCESS MARKERS:
   ```
   [RAILWAY] DEPLOYMENT CHECK v2 - CACHE BUSTED
   [OK] Code Version: 2026-02-16T17:30:00Z
   [OK] Fixed AttributeError for DB_POOL_SIZE
   ```

MOST LIKELY ISSUE:
Railway's "Root Directory" setting is not pointing to "studypulse/backend".
This would cause Railway to look for app/ in the wrong place.

NEXT STEPS:
1. Check Root Directory setting (most critical!)
2. Click "Redeploy" to force fresh build
3. Share build logs if issue persists
