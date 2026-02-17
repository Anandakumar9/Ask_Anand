# Railway Environment Variables Setup Guide

## Table of Contents
1. [Quick Start Checklist](#quick-start-checklist)
2. [Generate Secure SECRET_KEY](#generate-secure-secret_key)
3. [Required Environment Variables](#required-environment-variables)
4. [Step-by-Step Railway Configuration](#step-by-step-railway-configuration)
5. [Redeploy After Configuration](#redeploy-after-configuration)
6. [Verify Configuration](#verify-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start Checklist

Before you begin, make sure you have:
- [ ] A Railway account (https://railway.app)
- [ ] Your backend deployed to Railway
- [ ] Railway PostgreSQL database service added/provisioned
- [ ] Python 3.11+ installed locally (for generating SECRET_KEY)

---

## Generate Secure SECRET_KEY

### Method 1: Using Python (Recommended)

Open your terminal/command prompt and run:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

This will output something like:
```
YhZ3vX8nQ9pW2mK5rL4tB6jN8cF7dG1aS9xV0wE3qA2zR5yP4oM8nL6kJ7iH9gF0dS1a
```

**Copy this entire string - this is your SECRET_KEY!**

### Method 2: Using Python Interactive Shell

```python
python
>>> import secrets
>>> secrets.token_urlsafe(64)
'YhZ3vX8nQ9pW2mK5rL4tB6jN8cF7dG1aS9xV0wE3qA2zR5yP4oM8nL6kJ7iH9gF0dS1a'
>>> exit()
```

### Method 3: Online Generator (Less Secure)

Visit: https://generate-secret.vercel.app/64
- Click "Generate"
- Copy the generated key

**Important Security Notes:**
- SECRET_KEY must be at least 64 characters for production
- Never commit your SECRET_KEY to Git
- Keep it secure - it's used for JWT token signing
- Generate a new key for each environment (dev, staging, production)

---

## Required Environment Variables

Below are the **essential** environment variables for Railway deployment:

### 1. DATABASE_URL (Automatically Provided by Railway)

**What it is:** PostgreSQL connection string from Railway's database service

**Railway Format:**
```
postgresql://postgres:password@containers-us-west-xxx.railway.app:6543/railway
```

**What your app receives:**
- Railway automatically converts this to the async format: `postgresql+asyncpg://...`
- The app's config.py handles this conversion automatically

**How to get it:**
- Railway provides this automatically when you add a PostgreSQL service
- Variable name: `DATABASE_URL`
- This appears as a reference variable: `${{Postgres.DATABASE_URL}}`

**Screenshot Description:**
```
In Railway Dashboard:
1. Click on your PostgreSQL service (the database icon)
2. Go to "Variables" tab
3. You'll see DATABASE_URL in the list (with a link/chain icon)
4. Click the eye icon to view the full URL
```

### 2. SECRET_KEY (You Must Set This)

**What it is:** Secret key for JWT token signing and encryption

**Example:**
```
SECRET_KEY=YhZ3vX8nQ9pW2mK5rL4tB6jN8cF7dG1aS9xV0wE3qA2zR5yP4oM8nL6kJ7iH9gF0dS1a
```

**Requirements:**
- Minimum 64 characters (enforced in production)
- Use the Python command from Section 2 to generate
- Must be unique for your deployment

### 3. ENVIRONMENT (Production Flag)

**What it is:** Tells the app it's running in production mode

**Value:**
```
ENVIRONMENT=production
```

**What it does:**
- Disables DEBUG mode automatically
- Enforces strict security validation
- Enables production optimizations
- Requires stronger SECRET_KEY length

### 4. CORS_ORIGINS (Frontend URLs)

**What it is:** Comma-separated list of allowed frontend origins (no spaces!)

**Initial Setup (Before Vercel Deploy):**
```
CORS_ORIGINS=https://yourapp.railway.app
```

**After Vercel Deployment:**
```
CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
```

**Important Notes:**
- NO SPACES between URLs
- Must use `https://` (not `http://` in production)
- Include all domains where your frontend will be hosted
- You can update this later when you deploy to Vercel

### 5. DEBUG (Optional - Defaults to False)

**What it is:** Enables verbose logging and error details

**Value for Production:**
```
DEBUG=False
```

**Note:** In production mode (ENVIRONMENT=production), DEBUG is automatically set to False and cannot be True (will throw an error).

---

## Optional Environment Variables

These are not required for basic operation but enhance functionality:

### Redis (For Caching - Railway Add-on)

```
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

**How to get it:**
1. In Railway, click "New" > "Add Database" > "Add Redis"
2. Railway auto-populates this variable

### Ollama AI (For Question Generation)

```
OLLAMA_BASE_URL=http://ollama-service:11434
OLLAMA_MODEL=phi4-mini:3.8b-q4_K_M
RAG_ENABLED=true
```

### Database Connection Pool Settings

```
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

**Note:** These have sensible defaults; only change if you experience connection issues.

---

## Step-by-Step Railway Configuration

### Step 1: Access Your Railway Dashboard

1. Go to https://railway.app/dashboard
2. Click on your project
3. You should see two services:
   - Your backend service (the Python/FastAPI app)
   - PostgreSQL database service

**Screenshot Description:**
```
Railway Dashboard Overview:
- Left panel: List of all your services (Backend, Postgres, etc.)
- Right panel: Deployment history and logs
- Top right: Settings gear icon
```

### Step 2: Navigate to Backend Service Variables

1. Click on your **Backend Service** (NOT the Postgres service)
2. Click on the **"Variables"** tab at the top
3. You'll see a table with columns: Variable, Value, and actions

**Screenshot Description:**
```
Variables Tab View:
- List of all environment variables
- "+ New Variable" button on top right
- Each row shows variable name and masked/visible value
- Edit (pencil) and Delete (trash) icons on the right
```

### Step 3: Add Environment Variables One by One

For each variable below, click **"+ New Variable"**:

#### Variable 1: SECRET_KEY
```
Variable Name: SECRET_KEY
Value: [Paste the 64-character key you generated]
Example: YhZ3vX8nQ9pW2mK5rL4tB6jN8cF7dG1aS9xV0wE3qA2zR5yP4oM8nL6kJ7iH9gF0dS1a
```

Click "Add"

#### Variable 2: ENVIRONMENT
```
Variable Name: ENVIRONMENT
Value: production
```

Click "Add"

#### Variable 3: CORS_ORIGINS
```
Variable Name: CORS_ORIGINS
Value: https://yourapp.railway.app

(Update this later after Vercel deployment with your real domain)
Example after Vercel: https://studypulse.vercel.app,https://studypulse.com
```

Click "Add"

#### Variable 4: DEBUG (Optional but Recommended)
```
Variable Name: DEBUG
Value: False
```

Click "Add"

### Step 4: Reference the DATABASE_URL

Railway automatically provides DATABASE_URL from your PostgreSQL service.

**To verify it's connected:**

1. In the Variables tab, you should see:
   ```
   DATABASE_URL: ${{Postgres.DATABASE_URL}}
   ```

2. This is a **reference variable** (note the `${{...}}` syntax)

3. If you DON'T see this:
   - Click "+ New Variable"
   - Variable Name: `DATABASE_URL`
   - Value: `${{Postgres.DATABASE_URL}}`
   - Click "Add"

**Screenshot Description:**
```
Reference Variable:
DATABASE_URL shows as a special variable with a link icon
Clicking reveals: ${{Postgres.DATABASE_URL}}
This means: "Use the DATABASE_URL from the Postgres service"
```

### Step 5: Review All Variables

Your Variables tab should now show:

```
DATABASE_URL       ${{Postgres.DATABASE_URL}}          (Reference)
SECRET_KEY         YhZ3vX8nQ...                         (Hidden by default)
ENVIRONMENT        production
CORS_ORIGINS       https://yourapp.railway.app
DEBUG              False
```

**Screenshot Description:**
```
Final Variables List:
- 5 variables total
- DATABASE_URL with chain/link icon (reference)
- SECRET_KEY with eye icon to show/hide
- Other variables showing their values
- No red error indicators
```

---

## Redeploy After Configuration

After adding environment variables, Railway needs to redeploy your service.

### Option 1: Automatic Redeploy (Recommended)

Railway automatically triggers a redeploy when you add/change variables:

1. Look for a notification: "Deploying changes..."
2. Watch the deployment progress in the "Deployments" tab
3. Wait for the status to change from "Building" → "Deploying" → "Active"

**Screenshot Description:**
```
Deployments Tab:
- List of deployments with timestamps
- Latest deployment at the top
- Status: Building (orange) → Deploying (blue) → Active (green)
- Click on a deployment to see build logs
```

### Option 2: Manual Redeploy

If automatic redeploy didn't trigger:

1. Click on your Backend service
2. Click the **3-dot menu** (⋮) in the top right
3. Select **"Redeploy"**
4. Confirm the action

**Screenshot Description:**
```
Service Menu (3 dots):
- Redeploy (force new build)
- Restart (keep current build)
- Settings
- Delete
```

### Option 3: Git Push (Alternative)

Make a small change to your code and push to the connected branch:

```bash
git commit --allow-empty -m "Trigger Railway redeploy"
git push origin master
```

Railway will detect the push and start a new deployment.

---

## Verify Configuration

### Step 1: Check Build Logs

1. Click on your Backend service
2. Go to the **"Deployments"** tab
3. Click on the latest deployment (top of the list)
4. Click **"View Logs"** button

**Look for these success indicators:**

```
[DEBUG] DATABASE_URL received: postgresql+asyncpg://postgres:...
[OK] Database URL scheme: postgresql+asyncpg
[OK] Database host: containers-us-west-xxx.railway.app
[OK] Application starting in production mode
[OK] CORS origins configured: ['https://yourapp.vercel.app']
```

**Screenshot Description:**
```
Build Logs View:
- Real-time log stream with timestamps
- Scroll to find the "[DEBUG]" and "[OK]" messages
- Green text = success, Red text = error
- Filter by "Error", "Warning", "Info" at the top
```

### Step 2: Check Runtime Logs

After build completes:

1. Go to the **"Logs"** tab (different from build logs)
2. Look for application startup messages:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
[OK] StudyPulse API is ready to accept connections
```

### Step 3: Test API Health Check

Railway provides a public URL for your service:

1. Click on your Backend service
2. Find the **"Settings"** tab
3. Look for **"Domains"** section
4. Copy your Railway domain (format: `yourapp-production.up.railway.app`)

**Test the health check:**

Open your browser and visit:
```
https://yourapp-production.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

**Screenshot Description:**
```
Settings > Domains:
- Shows your Railway subdomain
- Option to add custom domain
- "Generate Domain" button if none exists
- Copy icon next to the URL
```

### Step 4: Verify Environment Variables in Logs

Check that the app is reading your variables correctly:

**Search logs for:**
```
[DEBUG] ENVIRONMENT: production
[DEBUG] SECRET_KEY length: 86 # Should be 64+
[DEBUG] CORS origins: ['https://yourapp.vercel.app']
[DEBUG] DATABASE_URL type: <class 'str'>
```

---

## Troubleshooting

### Issue 1: "SECRET_KEY must be at least 64 characters"

**Error in logs:**
```
[ERROR] SECRET_KEY must be at least 64 characters long in production!
```

**Solution:**
- Regenerate SECRET_KEY using the Python command (Section 2)
- Make sure you copied the ENTIRE string (no truncation)
- Verify length: `python -c "print(len('your-key'))"`

### Issue 2: "DATABASE_URL not found" or Connection Errors

**Error in logs:**
```
[ERROR] Could not connect to database
asyncpg.exceptions.InvalidCatalogNameError
```

**Solutions:**

1. **Check DATABASE_URL is set:**
   - Go to Backend service > Variables
   - Verify DATABASE_URL exists and shows `${{Postgres.DATABASE_URL}}`

2. **Verify PostgreSQL service is running:**
   - Click on Postgres service
   - Check status is "Active" (green)

3. **Check database service name:**
   - If your Postgres service has a different name, update reference:
   - `${{YourActualPostgresServiceName.DATABASE_URL}}`

4. **Manual URL (Last Resort):**
   - Go to Postgres service > Variables
   - Copy the actual DATABASE_URL value
   - Add it directly to Backend service (not recommended, prefer reference)

### Issue 3: CORS Errors from Frontend

**Error in browser console:**
```
Access to fetch at 'https://api.railway.app' from origin 'https://app.vercel.app'
has been blocked by CORS policy
```

**Solutions:**

1. **Add frontend domain to CORS_ORIGINS:**
   ```
   CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
   ```

2. **Common mistakes:**
   - **WRONG:** `http://` (use `https://` in production)
   - **WRONG:** `https://your-app.vercel.app ` (trailing space)
   - **WRONG:** `https://your-app.vercel.app, https://domain.com` (space after comma)
   - **RIGHT:** `https://your-app.vercel.app,https://domain.com` (no spaces)

3. **Wildcard (NOT recommended for production):**
   ```
   CORS_ORIGINS=*
   ```
   Note: Your app will reject this in production mode for security reasons.

### Issue 4: Railway Not Detecting New Variables

**Symptom:** Added variables but app still uses old values

**Solution:**

1. **Force redeploy:**
   - Service menu (3 dots) > Redeploy

2. **Restart service:**
   - Service menu > Restart

3. **Check variable syntax:**
   - No quotes around values (Railway adds them automatically)
   - No `export` keyword (just `VAR=value`)
   - **WRONG:** `SECRET_KEY="mykey"`
   - **RIGHT:** `SECRET_KEY=mykey`

### Issue 5: "DEBUG=True is not allowed in production"

**Error in logs:**
```
[ERROR] DEBUG=True is not allowed in production environment!
ValueError: Security validation failed
```

**Solution:**

- Set `DEBUG=False` in Railway variables
- OR remove DEBUG variable entirely (defaults to False)
- Never set DEBUG=True when ENVIRONMENT=production

### Issue 6: Build Fails with "Module not found"

**Error in logs:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**

1. **Check root directory setting:**
   - Settings > "Root Directory" should be: `studypulse/backend`

2. **Verify requirements.txt exists:**
   - Railway looks for `requirements.txt` or `requirements-railway.txt`
   - Should be in the root directory specified above

3. **Check Dockerfile location:**
   - If using Dockerfile, it should be in project root OR in Railway settings
   - Settings > "Dockerfile Path"

---

## Next Steps After Railway Setup

1. **Deploy Frontend to Vercel**
   - Your backend is now ready to receive API requests
   - Update CORS_ORIGINS after you get your Vercel URL

2. **Update Frontend API URL**
   - In your frontend `.env`:
     ```
     VITE_API_URL=https://yourapp-production.up.railway.app
     ```

3. **Test the Full Stack**
   - Visit your Vercel frontend
   - Try login/signup
   - Check browser console for API calls

4. **Set Up Custom Domain (Optional)**
   - Railway Settings > Domains > "Custom Domain"
   - Add your domain, update DNS records
   - Update CORS_ORIGINS to include custom domain

5. **Monitor Your App**
   - Railway Dashboard > Metrics (CPU, Memory, Network)
   - Set up alerts for downtime
   - Check logs regularly for errors

---

## Security Best Practices

1. **Never commit .env files** to Git
   - Add to `.gitignore`
   - Use .env.example for templates only

2. **Rotate SECRET_KEY regularly**
   - Generate new key every 90 days
   - Update Railway variable immediately

3. **Use strong database passwords**
   - Railway generates secure passwords by default
   - Don't change unless necessary

4. **Enable Railway's built-in SSL**
   - Railway provides SSL certificates automatically
   - Always use `https://` for production

5. **Review logs weekly**
   - Check for unauthorized access attempts
   - Monitor error rates
   - Look for unusual traffic patterns

---

## Quick Reference Card

Copy this for quick access:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Required Variables:
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=[Generated 64-char key]
ENVIRONMENT=production
CORS_ORIGINS=https://your-app.vercel.app

# Optional Variables:
DEBUG=False
REDIS_URL=${{Redis.REDIS_URL}}
OLLAMA_BASE_URL=http://ollama-service:11434

# Test Health Check:
curl https://your-app.railway.app/health
```

---

## Getting Help

If you're stuck:

1. **Check Railway Logs First**
   - 90% of issues show up in logs
   - Look for [ERROR] or [WARNING] messages

2. **Railway Community**
   - Discord: https://discord.gg/railway
   - Forum: https://help.railway.app

3. **StudyPulse Repository**
   - Check existing issues on GitHub
   - Open a new issue with logs attached

4. **Common Issues Documentation**
   - See `RAILWAY_DEPLOYMENT_CHECKLIST.md` for deployment-specific issues
   - See `PRODUCTION_READY_SUMMARY.md` for architecture details

---

## Congratulations!

You've successfully configured Railway environment variables for production deployment. Your backend is now secure, scalable, and ready to handle real users.

**Next:** Deploy your frontend to Vercel and connect the two services!
