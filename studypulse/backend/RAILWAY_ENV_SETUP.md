# Railway Environment Variables Setup

## Required Environment Variables

Configure these in Railway Dashboard → Settings → Variables:

### 1. Core Application Settings

```bash
# Environment mode
ENVIRONMENT=production

# API Configuration
APP_NAME=StudyPulse
API_VERSION=v1
DEBUG=false
```

### 2. Security (CRITICAL - App won't start without these)

```bash
# Generate a secure 64+ character secret key
# Run this command locally to generate one:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=<your-64-char-secret-key-here>

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. Database (Required)

```bash
# Railway will provide this automatically if you add a PostgreSQL plugin
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### 4. CORS Configuration (Required for frontend)

```bash
# Set to your frontend URL when deployed
# For now, you can use:
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
```

### 5. LLM Service (Ollama)

**Option A: Use Railway-hosted Ollama (Recommended)**
```bash
# If you deploy Ollama as a separate Railway service
OLLAMA_BASE_URL=https://your-ollama-service.railway.internal
OLLAMA_MODEL=phi4-mini:3.8b-q4_K_M
OLLAMA_TIMEOUT=300
```

**Option B: Use external Ollama/API service**
```bash
OLLAMA_BASE_URL=https://your-external-ollama-url
# Or use OpenRouter as fallback:
OPENROUTER_API_KEY=<your-openrouter-key>
```

### 6. Vector Database (Optional - defaults to embedded)

```bash
# Option 1: Use embedded PageIndex (lighter, no external service needed)
USE_PAGEINDEX=true
PAGEINDEX_STORAGE_PATH=/app/data/pageindex

# Option 2: Use Qdrant (requires separate service)
# QDRANT_HOST=your-qdrant-host
# QDRANT_PORT=6333
```

### 7. Performance Tuning

```bash
# Adjust based on Railway plan resources
QUESTION_BATCH_SIZE=3
PARALLEL_QUESTION_AGENTS=2
```

## Quick Setup Steps

1. Go to Railway Dashboard → Your Project → studypulse-backend
2. Click "Variables" tab
3. Add all required variables above
4. Generate SECRET_KEY:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
5. Add PostgreSQL plugin if not already added:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will auto-set DATABASE_URL variable
6. Click "Deploy" or wait for auto-redeploy

## Check Deployment Logs

After setting variables:
1. Go to "Deployments" tab
2. Click latest deployment
3. Check logs for errors
4. Look for "Application startup complete" message

## Common Startup Errors

- **"SECRET_KEY must be at least 64 characters"** → Generate new key
- **"Wildcard CORS (*) not allowed in production"** → Set specific CORS_ORIGINS
- **Database connection failed** → Check DATABASE_URL is set correctly
- **Port binding failed** → Railway handles this automatically via $PORT

## Minimal Working Configuration

To get started quickly, set these FIRST:

```bash
ENVIRONMENT=production
SECRET_KEY=<64-char-key>
DATABASE_URL=${{Postgres.DATABASE_URL}}
CORS_ORIGINS=http://localhost:3000
USE_PAGEINDEX=true
```

Then add LLM configuration later.
