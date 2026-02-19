# RAG Pipeline Setup Guide - OpenRouter + PageIndex

## Overview

Your RAG pipeline now supports **cost-optimized question generation** using OpenRouter API with automatic multi-LLM fallback, plus lightweight vector search via PageIndex.

---

## 🎯 What Changed

### 1. **OpenRouter Integration** (Cost-Optimized LLM)

**Before:** Used Ollama (requires local GPU/server, not ideal for Railway)

**Now:** Uses OpenRouter API with automatic fallback chain:
- **Primary:** DeepSeek R1 (FREE tier) → DeepSeek Chat ($0.14/$0.28 per 1M tokens)
- **Fallback 1:** Qwen 2.5 ($0.55/$0.55 per 1M tokens)
- **Fallback 2:** Llama 3.1 ($0.59/$0.79 per 1M tokens)
- **Fallback 3:** GPT-4o-mini ($0.15/$0.60 per 1M tokens)

**Cost per user per test (10 questions):**
- ~$0.0001 - $0.0005 (extremely cheap!)
- DeepSeek R1 free tier: **$0.00** (if available)

### 2. **PageIndex Vector Store** (Lightweight, Embedded)

**Current setup:** PageIndex (embedded HNSW, no separate server)

**Benefits:**
- ✅ No separate Qdrant server needed
- ✅ Low memory (~20-50 MB vs 200-500 MB for Qdrant)
- ✅ Fast initialization (~0.5s vs ~3s)
- ✅ Perfect for <100k vectors (you have ~4,700 questions)

**Scaling limits:**
- **Current capacity:** 100k vectors (easily expandable to 1M+)
- **When to switch to Qdrant:**
  - You exceed 100k-500k vectors
  - Need multi-replica deployments
  - Need advanced filtering/aggregation
  - Need distributed search across multiple servers

**For now:** PageIndex is **perfect** for your use case. You can switch to Qdrant later if you scale beyond 100k questions.

---

## 🚀 Setup Instructions

### Step 1: Get OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up (free account works)
3. Get your API key from dashboard
4. Add credits (optional, DeepSeek R1 has free tier)

### Step 2: Configure Environment Variables

Add to your Railway environment variables (or `.env` locally):

```bash
# LLM Provider (choose one)
LLM_PROVIDER=openrouter  # or "ollama" for local

# OpenRouter API Key (required if LLM_PROVIDER=openrouter)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# RAG Settings (already configured)
RAG_ENABLED=true
USE_PAGEINDEX=true  # Use PageIndex (lightweight) instead of Qdrant
```

### Step 3: Deploy

Your code is already updated! Just:
1. Set `OPENROUTER_API_KEY` in Railway
2. Set `LLM_PROVIDER=openrouter`
3. Redeploy

The system will automatically:
- Use OpenRouter for question generation
- Fall back to Ollama if OpenRouter unavailable
- Track costs per model
- Use PageIndex for vector search

---

## 📊 Cost Tracking

Cost metrics are available via `/health` endpoint:

```json
{
  "llm_metrics": {
    "provider": "openrouter",
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

**Estimated costs:**
- **10 questions/test:** ~$0.0001 - $0.0005
- **1,000 tests/month:** ~$0.10 - $0.50
- **10,000 tests/month:** ~$1 - $5

**DeepSeek R1 free tier:** If available, costs **$0.00**!

---

## 🔄 Backward Compatibility

**Ollama still works!** If you prefer local generation:

```bash
LLM_PROVIDER=ollama
# Don't set OPENROUTER_API_KEY
```

The system will use Ollama if:
- `LLM_PROVIDER=ollama`, OR
- `LLM_PROVIDER=openrouter` but OpenRouter unavailable (automatic fallback)

---

## 📈 When to Switch from PageIndex to Qdrant

**Stick with PageIndex if:**
- ✅ You have <100k questions (you have ~4,700)
- ✅ Single-server deployment (Railway)
- ✅ Want simplicity (no separate vector DB server)

**Switch to Qdrant if:**
- ⚠️ You exceed 100k-500k vectors
- ⚠️ Need multi-replica deployments
- ⚠️ Need advanced filtering/aggregation
- ⚠️ Need distributed search

**How to switch:**
1. Set `USE_PAGEINDEX=false` in config
2. Deploy Qdrant (Railway, Docker, or Qdrant Cloud)
3. Set `QDRANT_HOST`, `QDRANT_PORT` environment variables
4. Redeploy backend

**For now:** PageIndex is perfect! No need to change.

---

## 🐛 Troubleshooting

### OpenRouter not working?

1. **Check API key:** Ensure `OPENROUTER_API_KEY` is set correctly
2. **Check credits:** OpenRouter dashboard → ensure you have credits (or using free tier)
3. **Check logs:** Railway logs will show which model succeeded/failed
4. **Fallback:** System automatically falls back to Ollama if OpenRouter fails

### PageIndex not initializing?

1. **Check disk space:** PageIndex saves to `./data/pageindex/`
2. **Check permissions:** Ensure write access to storage path
3. **Check logs:** Look for "PageIndex init failed" messages

---

## ✅ Summary

**What you get:**
- ✅ Cost-optimized question generation (~$0.0001-0.0005 per test)
- ✅ Automatic multi-LLM fallback (DeepSeek → Qwen → Llama → GPT-4o-mini)
- ✅ Lightweight vector search (PageIndex, no separate server)
- ✅ Backward compatible (Ollama still works)
- ✅ Cost tracking built-in

**Next steps:**
1. Get OpenRouter API key
2. Set `OPENROUTER_API_KEY` and `LLM_PROVIDER=openrouter` in Railway
3. Redeploy
4. Monitor costs via `/health` endpoint

**You're all set!** 🎉
