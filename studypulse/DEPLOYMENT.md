# Production Deployment Guide

Complete guide to deploy StudyPulse to production using Railway.app + Supabase.

## Prerequisites

- [ ] GitHub account
- [ ] Railway.app account (sign up at https://railway.app)
- [ ] Supabase account (already configured)
- [ ] Domain name (optional, can use Railway subdomain)

## Architecture

```
┌─────────────────────┐
│   Flutter Mobile    │ ← User Interface (iOS/Android/Web)
│   (Vercel/CDN)      │
└──────────┬──────────┘
           │ HTTPS
           ↓
┌─────────────────────┐
│  Railway Backend    │ ← FastAPI + Uvicorn
│  (Auto-scaling)     │
└──────────┬──────────┘
           │
    ┌──────┴────────┬────────────┐
    ↓               ↓            ↓
┌─────────┐   ┌─────────┐  ┌─────────┐
│Supabase │   │ Redis   │  │ Ollama  │
│PostreSQL│   │ (cache) │  │  (LLM)  │
└─────────┘   └─────────┘  └─────────┘
```

## Step 1: Prepare Backend for Deployment

### 1.1 Install Production Dependencies

Add these to `studypulse/backend/requirements.txt`:

```txt
# Production server
gunicorn==21.2.0
uvicorn[standard]>=0.27.0

# Supabase integration
supabase==2.3.0

# Rate limiting
slowapi==0.1.9

# Monitoring
sentry-sdk[fastapi]==1.40.0

# Production database
psycopg2-binary==2.9.9
asyncpg==0.29.0
```

### 1.2 Create Production Environment File

Create `.env.production.example`:

```bash
# Application
APP_NAME=StudyPulse
DEBUG=False
API_VERSION=v1
ENVIRONMENT=production

# Supabase (from your existing setup)
SUPABASE_URL=https://eguewniqweyrituwbowt.supabase.co
SUPABASE_KEY=<your_supabase_anon_key>
SUPABASE_JWT_SECRET=<your_supabase_jwt_secret>

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# Security
SECRET_KEY=<generate_64_character_random_string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Ollama (Railway service)
OLLAMA_BASE_URL=https://ollama.<railway-domain>.railway.app
OLLAMA_MODEL=phi4-mini:3.8b-q4_K_M

# Redis (Railway addon)
REDIS_URL=redis://<railway-redis-url>

# CORS (your frontend domain)
CORS_ORIGINS=https://<your-domain>.vercel.app,https://<your-domain>.com

# Monitoring
SENTRY_DSN=<your_sentry_dsn>

# Question Generation
QUESTION_COUNT_DEFAULT=10
PREVIOUS_YEAR_RATIO=0.5
STAR_THRESHOLD_PERCENTAGE=85
```

### 1.3 Generate Secure Secrets

Run this Python script to generate secure secrets:

```python
# generate_secrets.py
import secrets
import string

def generate_secret_key(length=64):
    """Generate cryptographically secure secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

print(f"SECRET_KEY={generate_secret_key(64)}")
print(f"JWT_SECRET={generate_secret_key(32)}")
```

```bash
python generate_secrets.py
```

### 1.4 Update Database Configuration

Edit `studypulse/backend/app/core/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

# Production-ready connection pool
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,  # Increase for production
    max_overflow=10,  # Allow burst connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "server_settings": {"application_name": "studypulse"},
        "command_timeout": 60,
    }
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### 1.5 Create Procfile for Railway

Create `studypulse/backend/Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

### 1.6 Update main.py for Production

Edit `studypulse/backend/app/main.py` to add security middleware:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware, RequestSizeLimitMiddleware
from app.middleware.rate_limiter import setup_rate_limiting
from app.core.config import settings
import sentry_sdk

# Initialize Sentry for error tracking (production only)
if not settings.DEBUG and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment="production",
        traces_sample_rate=0.1,  # 10% of transactions
    )

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in prod
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10*1024*1024)  # 10MB

# Rate limiting
setup_rate_limiting(app)

# CORS - restrict to frontend domains only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
from app.api import auth, exams, study, mock_test, dashboard, profile, leaderboard, health
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# ... other routers ...
```

## Step 2: Deploy to Railway

### 2.1 Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select `Ask_Anand` repository
6. Railway will detect the FastAPI app

### 2.2 Configure Railway Service

1. Set root directory: `studypulse/backend`
2. Railway auto-detects Python and uses Procfile
3. Click "Add variables" and paste your `.env.production` values

**Important Environment Variables:**
```
DATABASE_URL=<from Supabase connection string>
SUPABASE_URL=https://eguewniqweyrituwbowt.supabase.co
SUPABASE_KEY=<your key>
SECRET_KEY=<generated secret>
CORS_ORIGINS=<your frontend domains>
DEBUG=False
ENVIRONMENT=production
```

### 2.3 Get Supabase Database URL

1. Go to Supabase Dashboard → Project Settings → Database
2. Copy "Connection string" (URI format)
3. Replace `[YOUR-PASSWORD]` with your database password: `kJyLnlOXfTvV02OQ`
4. Convert to asyncpg format:
   ```
   postgresql+asyncpg://postgres:kJyLnlOXfTvV02OQ@db.eguewniqweyrituwbowt.supabase.co:5432/postgres
   ```

### 2.4 Add Redis (Optional but Recommended)

1. In Railway project, click "New Service"
2. Select "Redis"
3. Copy the `REDIS_URL` environment variable
4. Add to your backend environment variables

### 2.5 Deploy Ollama (Optional - for AI questions)

**Option A: Use Railway Template**
1. Add new service → "Template"
2. Search for "Ollama"
3. Deploy with model: `phi4-mini:3.8b-q4_K_M`
4. Get public URL and set as `OLLAMA_BASE_URL`

**Option B: Skip Ollama** (use DB questions only)
- Set `RAG_ENABLED=false` in environment variables
- App will use only database questions (no AI generation)

### 2.6 Deploy Backend

1. Click "Deploy" in Railway
2. Wait for build to complete (~5 minutes)
3. Railway will provide a public URL: `https://<your-app>.up.railway.app`
4. Test health check: `https://<your-app>.up.railway.app/api/v1/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-15T...",
  "application": "StudyPulse",
  "version": "v1"
}
```

## Step 3: Configure Supabase Auth

### 3.1 Enable Auth Providers

1. Go to Supabase Dashboard → Authentication → Providers
2. Enable Email provider (already enabled)
3. Enable Google OAuth:
   - Go to Google Cloud Console
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs:
     ```
     https://<project-ref>.supabase.co/auth/v1/callback
     ```
   - Copy Client ID and Secret
   - Paste in Supabase Google provider settings

### 3.2 Configure Redirect URLs

In Supabase → Authentication → URL Configuration:
- Site URL: `https://<your-domain>.com`
- Redirect URLs (add):
  - `https://<your-domain>.com/auth/callback`
  - `https://<your-app>.vercel.app/auth/callback`
  - `myapp://auth/callback` (for mobile deep linking)

## Step 4: Deploy Flutter Mobile Web

### 4.1 Update API Base URL

Edit `studypulse/mobile/lib/api/api_service.dart`:

```dart
String get baseUrl {
  const environment = String.fromEnvironment('ENVIRONMENT', defaultValue: 'development');

  if (environment == 'production') {
    return 'https://<your-railway-app>.up.railway.app/api/v1';
  }

  // Development
  if (kIsWeb) {
    return 'http://localhost:8001/api/v1';
  } else {
    return 'http://10.0.2.2:8001/api/v1';  // Android emulator
  }
}
```

### 4.2 Build Flutter Web

```bash
cd studypulse/mobile
flutter build web --release --dart-define=ENVIRONMENT=production
```

### 4.3 Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Create `vercel.json` in `studypulse/mobile/`:
   ```json
   {
     "github": {
       "silent": true
     },
     "buildCommand": "flutter build web --release",
     "outputDirectory": "build/web",
     "routes": [
       { "handle": "filesystem" },
       { "src": "/.*", "dest": "/index.html" }
     ]
   }
   ```

3. Deploy:
   ```bash
   vercel --prod
   ```

4. Vercel will provide URL: `https://<project>.vercel.app`

## Step 5: Database Migration

### 5.1 Create Production Database Tables

Run migrations on Supabase:

```bash
# From studypulse/backend/
python -c "
from app.core.database import engine
from app.models import Base
import asyncio

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✓ Tables created')

asyncio.run(create_tables())
"
```

### 5.2 Seed Initial Data

```bash
python seed_complete_demo.py
```

This creates:
- 6 competitive exams (UPSC, CAT, NEET, etc.)
- 119 topics with 1,809+ questions
- Demo users for testing

## Step 6: Testing Production Deployment

### 6.1 Test Health Endpoints

```bash
# Basic health
curl https://<railway-url>/api/v1/health

# Readiness check
curl https://<railway-url>/api/v1/health/ready

# Metrics
curl https://<railway-url>/api/v1/health/metrics
```

### 6.2 Test Authentication

```bash
# Register
curl -X POST https://<railway-url>/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"SecurePass123!"}'

# Login
curl -X POST https://<railway-url>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
```

### 6.3 Load Test (100 concurrent users)

```bash
cd studypulse/backend/tests/load
locust -f test_concurrent_users.py --host=https://<railway-url>
```

Open http://localhost:8089 and start test with 100 users.

## Step 7: Monitoring Setup

### 7.1 Configure Sentry

1. Sign up at https://sentry.io (free tier: 5,000 events/month)
2. Create new project (Python/FastAPI)
3. Copy DSN
4. Add to Railway environment variables:
   ```
   SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>
   ```

### 7.2 Set Up UptimeRobot

1. Go to https://uptimerobot.com (free tier: 50 monitors)
2. Add "HTTP(s)" monitor:
   - URL: `https://<railway-url>/api/v1/health/ready`
   - Interval: 5 minutes
   - Alert contacts: Your email

## Step 8: Custom Domain (Optional)

### 8.1 Configure Railway Domain

1. In Railway project → Settings → Domains
2. Click "Generate Domain" or "Custom Domain"
3. If custom: Add DNS records at your registrar:
   ```
   CNAME api.<your-domain>.com  <your-app>.up.railway.app
   ```

### 8.2 Update CORS Origins

Add your custom domain to environment variables:
```
CORS_ORIGINS=https://app.<your-domain>.com,https://<project>.vercel.app
```

## Production Checklist

- [ ] Backend deployed to Railway
- [ ] Database migrated to Supabase PostgreSQL
- [ ] Redis cache connected (optional)
- [ ] Environment variables configured
- [ ] SSL/HTTPS working (automatic with Railway)
- [ ] Health checks responding
- [ ] Sentry error tracking configured
- [ ] UptimeRobot monitoring active
- [ ] Flutter web deployed to Vercel
- [ ] Mobile app configured with production API
- [ ] Supabase Auth providers enabled (Email + Google)
- [ ] CORS configured for frontend domains
- [ ] Load tested with 100 concurrent users

## Estimated Monthly Costs

| Service | Tier | Cost |
|---------|------|------|
| Railway (Backend) | Hobby | $5/month (500 hours) |
| Supabase (DB + Auth) |Free | $0 (up to 500MB) |
| Vercel (Frontend) | Hobby | $0 (100GB bandwidth) |
| Sentry (Errors) | Free | $0 (5k events) |
| UptimeRobot (Monitoring) | Free | $0 (50 monitors) |
| **Total** | | **$5/month** |

## Troubleshooting

### Issue: Database connection fails
- Check DATABASE_URL format includes `+asyncpg`
- Verify Supabase password is correct
- Check Supabase connection pooler is enabled

### Issue: CORS errors
- Verify CORS_ORIGINS includes your frontend domain
- Check protocol (http vs HTTPS)
- Ensure no trailing slashes

### Issue: Rate limiting too aggressive
- Adjust limits in `app/middleware/rate_limiter.py`
- Redeploy to Railway

### Issue: Ollama timeouts
- Increase timeout in `app/core/ollama.py`
- Or disable with `RAG_ENABLED=false`

## Next Steps

1. **Performance Monitoring**: Track response times and optimize slow endpoints
2. **A/B Testing**: Test AI questions vs database questions quality
3. **Analytics**: Add user behavior tracking
4. **CI/CD**: Set up GitHub Actions for automated deployments
5. **Scaling**: Add more Railway workers if needed (pay-as-you-go)

## Support

- Railway docs: https://docs.railway.app
- Supabase docs: https://supabase.com/docs
- FastAPI deployment: https://fastapi.tiangolo.com/deployment/

---

**Your app is now production-ready!** 🚀
