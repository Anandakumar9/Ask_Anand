# 🚀 Complete Deployment Checklist - OpenRouter RAG Integration

## ⚠️ CRITICAL: Your OpenRouter Key Was Exposed

**You pasted your real API key in chat. You MUST:**
1. Go to https://openrouter.ai/keys
2. **Revoke/Delete** the key: `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`
3. **Create a NEW key** and use that instead

---

## 📋 Files That Will Be Committed

### ✅ Backend Changes (RAG + Security)
- `studypulse/backend/app/core/openrouter.py` (NEW - OpenRouter client)
- `studypulse/backend/app/core/config.py` (security logging + LLM_PROVIDER)
- `studypulse/backend/app/core/database.py` (removed debug prints)
- `studypulse/backend/app/main.py` (security middleware + OpenRouter init)
- `studypulse/backend/app/middleware/rate_limiter.py` (Redis storage + Settings)
- `studypulse/backend/app/api/auth.py` (rate limits + password strength)
- `studypulse/backend/app/rag/question_generator.py` (OpenRouter integration)
- `studypulse/backend/app/services/pdf_question_parser.py` (OpenRouter integration)
- `studypulse/backend/tests/conftest.py` (fixed test fixtures)
- `studypulse/backend/RAG_SETUP_GUIDE.md` (NEW - documentation)

### ✅ Frontend/Mobile Changes (if any)
- Various frontend/mobile files (already modified, will be included)

### ❌ NOT Committed (temp files, safe to ignore)
- `RAILWAY_ENV_VARS.txt` (docs only, no secrets)
- `*.bat`, `*.json` temp files
- `.cursor/` directory

---

## 🔧 Step-by-Step: Set Environment Variables via CLI

### Prerequisites

Install CLI tools if you haven't:

```powershell
# Railway CLI
npm install -g @railway/cli

# Vercel CLI
npm install -g vercel

# Supabase CLI
npm install -g supabase
```

---

## 1️⃣ Railway (Backend) - Set OpenRouter Variables

### Option A: Via Railway CLI (Recommended)

```powershell
# Login to Railway
railway login

# Link to your project (if not already linked)
cd C:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend
railway link

# Set environment variables
railway variables set LLM_PROVIDER=openrouter
railway variables set OPENROUTER_API_KEY=sk-or-v1-YOUR_NEW_KEY_HERE

# Verify they're set
railway variables
```

### Option B: Via Railway Dashboard (Easier)

1. Go to https://railway.app/dashboard
2. Click your project → Backend service
3. Click **"Variables"** tab
4. Click **"+ New Variable"** for each:

```
Name: LLM_PROVIDER
Value: openrouter

Name: OPENROUTER_API_KEY  
Value: sk-or-v1-YOUR_NEW_KEY_HERE
```

5. Railway will **auto-redeploy** after you save

---

## 2️⃣ Vercel (Frontend) - No Changes Needed

**Your frontend doesn't need OpenRouter key** (it's backend-only).

**Optional:** If you want to update frontend env vars:

```powershell
cd C:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\frontend

# Login to Vercel
vercel login

# Link project (if not linked)
vercel link

# Set variables (if needed)
vercel env add NEXT_PUBLIC_API_URL production
# Enter your Railway backend URL when prompted

# Redeploy
vercel --prod
```

---

## 3️⃣ Supabase - No Changes Needed

**Supabase doesn't need OpenRouter key** (it's only for backend RAG).

**If you want to verify Supabase connection:**

```powershell
# Login to Supabase
supabase login

# Link project (if needed)
supabase link --project-ref YOUR_PROJECT_REF

# Check connection
supabase status
```

---

## 📝 Git Commit & Push Commands

Run these in PowerShell from your project root:

```powershell
cd C:\Users\anand\OneDrive\Desktop\Ask_Anand

# Stage only studypulse directory (excludes temp files)
git add studypulse/

# Check what will be committed
git status

# Commit with descriptive message
git commit -m "feat: add OpenRouter RAG integration and security hardening

- Integrate OpenRouter client with multi-LLM fallback (DeepSeek, Qwen, Llama, GPT-4o-mini)
- Wire question generator and PDF parser to use OpenRouter/Ollama based on config
- Harden backend security (remove DB URL leaks, enable security headers/rate limiting)
- Fix test fixtures to match current models
- Add RAG setup guide documentation"

# Push to GitHub
git push origin master
```

---

## ✅ Verification Checklist

After deployment, verify everything works:

### 1. Check Railway Logs
```powershell
railway logs
```

**Look for:**
- ✅ `"OpenRouter client initialized"`
- ✅ `"OpenRouter ready (multi-LLM fallback...)"`
- ✅ No errors about missing `OPENROUTER_API_KEY`

### 2. Test Health Endpoint
```powershell
# Replace with your Railway backend URL
curl https://your-backend.railway.app/health
```

**Should show:**
```json
{
  "components": {
    "llm": "healthy",
    ...
  },
  "llm_metrics": {
    "provider": "openrouter",
    "total_cost_usd": 0.0,
    ...
  }
}
```

### 3. Test Question Generation
- Start a study session (5 minutes)
- Wait for timer to end
- Start mock test
- **Questions should generate** (check Railway logs for OpenRouter calls)

---

## 🐛 Troubleshooting

### OpenRouter Not Working?

1. **Check API key is set:**
   ```powershell
   railway variables
   ```
   Should show `OPENROUTER_API_KEY` and `LLM_PROVIDER=openrouter`

2. **Check Railway logs:**
   ```powershell
   railway logs --tail
   ```
   Look for: `"OpenRouter API key not set"` or `"OpenRouter not available"`

3. **Verify key is valid:**
   - Go to https://openrouter.ai/keys
   - Ensure key is active and has credits (or using free tier)

### Fallback to Ollama?

If OpenRouter fails, system **automatically falls back to Ollama** (if configured).

Check logs for: `"OpenRouter unavailable, trying Ollama fallback..."`

---

## 📊 Cost Monitoring

Monitor costs via `/health` endpoint:

```json
{
  "llm_metrics": {
    "total_cost_usd": 0.0012,
    "token_usage": {
      "deepseek/deepseek-r1:free": {
        "input_tokens": 5000,
        "output_tokens": 3000
      }
    }
  }
}
```

**Expected costs:**
- Per test (10 questions): ~$0.0001 - $0.0005
- 1,000 tests/month: ~$0.10 - $0.50
- DeepSeek R1 free tier: **$0.00** (if available)

---

## 🎯 Summary: What's Done vs Pending

### ✅ DONE (My Side)
- [x] Created OpenRouter client with multi-LLM fallback
- [x] Updated question generator to use OpenRouter
- [x] Updated PDF parser to use OpenRouter
- [x] Hardened security (no DB URL leaks, rate limiting, headers)
- [x] Fixed test fixtures
- [x] Added RAG setup guide
- [x] Created this deployment checklist

### ⏳ PENDING (Your Side)
- [ ] **Revoke old OpenRouter key** (CRITICAL - you exposed it)
- [ ] **Create new OpenRouter key**
- [ ] **Set Railway env vars** (`LLM_PROVIDER`, `OPENROUTER_API_KEY`)
- [ ] **Run git commit/push** (commands provided above)
- [ ] **Verify deployment** (check Railway logs, test health endpoint)
- [ ] **Test question generation** (start study session → mock test)

---

## 🚨 Important Notes

1. **Your app is LIVE** - changes won't break it until you:
   - Set `LLM_PROVIDER=openrouter` in Railway
   - If OpenRouter fails, it falls back to Ollama (or DB-only mode)

2. **Backward compatible** - if you don't set OpenRouter vars, system uses Ollama (or skips AI if Ollama unavailable)

3. **No frontend changes needed** - frontend doesn't know about OpenRouter

4. **Database unchanged** - no migrations needed

---

**Ready to deploy? Follow the steps above!** 🚀
