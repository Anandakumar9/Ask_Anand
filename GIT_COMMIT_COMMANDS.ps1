# PowerShell script to commit and push changes
# Run this from: C:\Users\anand\OneDrive\Desktop\Ask_Anand

Write-Host "Staging studypulse directory..." -ForegroundColor Cyan
git add studypulse/

Write-Host "`nChecking staged files..." -ForegroundColor Cyan
git status --short

Write-Host "`nCommitting changes..." -ForegroundColor Cyan
git commit -m "feat: add OpenRouter RAG integration and security hardening

- Integrate OpenRouter client with multi-LLM fallback (DeepSeek, Qwen, Llama, GPT-4o-mini)
- Wire question generator and PDF parser to use OpenRouter/Ollama based on config
- Harden backend security (remove DB URL leaks, enable security headers/rate limiting)
- Fix test fixtures to match current models
- Add RAG setup guide documentation"

Write-Host "`nPushing to GitHub..." -ForegroundColor Cyan
git push origin master

Write-Host "`n✅ Done! Check GitHub to verify." -ForegroundColor Green
