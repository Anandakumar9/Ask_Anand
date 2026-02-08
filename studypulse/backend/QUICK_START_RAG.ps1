# StudyPulse RAG Integration - Quick Start (Windows)

Write-Host "🚀 StudyPulse RAG Integration - Quick Start" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Install new dependencies
Write-Host "📦 Step 1: Installing new dependencies..." -ForegroundColor Cyan
Set-Location "C:\Users\anand\OneDrive\Desktop\Ask_Anand\studypulse\backend"

# Activate virtual environment
$venvPath = "C:\Users\anand\OneDrive\Desktop\Ask_Anand\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "   Activating virtual environment..." -ForegroundColor Yellow
    & $venvPath
}

Write-Host "   Installing RAG dependencies..." -ForegroundColor Yellow
pip install qdrant-client sentence-transformers semantic-kernel tiktoken --quiet

# Step 2: Check Qdrant
Write-Host ""
Write-Host "🔧 Step 2: Checking Qdrant vector database..." -ForegroundColor Cyan
try {
    $qdrantStatus = Invoke-WebRequest -Uri "http://localhost:6333" -UseBasicParsing -TimeoutSec 2
    Write-Host "   ✅ Qdrant is running" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Qdrant not running. Starting container..." -ForegroundColor Yellow
    docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage --name studypulse-qdrant qdrant/qdrant:v1.16.3
    Start-Sleep -Seconds 5
}

# Step 3: Check Ollama
Write-Host ""
Write-Host "🤖 Step 3: Checking Ollama..." -ForegroundColor Cyan
try {
    $ollamaStatus = Invoke-WebRequest -Uri "http://localhost:11434" -UseBasicParsing -TimeoutSec 2
    Write-Host "   ✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Ollama not running. Please start: ollama serve" -ForegroundColor Red
    exit 1
}

# Step 4: Test RAG Components
Write-Host ""
Write-Host "🧪 Step 4: Testing RAG components..." -ForegroundColor Cyan

$testScript = @"
import asyncio
import sys
sys.path.insert(0, '.')

async def test_rag():
    try:
        from app.rag.vector_store import VectorStore
        print('\n✅ VectorStore imported successfully')
        
        vector_store = VectorStore(host='localhost', port=6333)
        stats = vector_store.get_collection_stats()
        print(f'   Collection stats: {stats}')
        
        from app.rag.semantic_kernel_service import SemanticKernelService
        print('\n✅ SemanticKernelService imported successfully')
        
        sk_service = SemanticKernelService()
        
        sample_questions = [{
            'question_text': 'What is the capital of India?',
            'options': {'A': 'Mumbai', 'B': 'Delhi', 'C': 'Kolkata', 'D': 'Chennai'},
            'correct_answer': 'B'
        }]
        
        print('\n🔄 Generating test questions...')
        questions = await sk_service.generate_question(
            topic_name='Indian Geography',
            subject_name='General Studies',
            exam_name='UPSC',
            sample_questions=sample_questions,
            count=2,
            prompt_version='v2_enhanced'
        )
        
        print(f'\n✅ Generated {len(questions)} questions:')
        for i, q in enumerate(questions, 1):
            print(f'\n   Q{i}: {q.get(\"question_text\", \"\")}')
            print(f'   Answer: {q.get(\"correct_answer\")}')
        
        print('\n✅ All RAG components working!')
        return True
        
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_rag())
sys.exit(0 if result else 1)
"@

$testScript | python

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✅ RAG Integration Setup Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📚 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Review PRODUCTION_ARCHITECTURE.md for deployment plan" -ForegroundColor White
    Write-Host "   2. Start backend: uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "   3. Access API docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Key Features Now Available:" -ForegroundColor Cyan
    Write-Host "   ✅ Vector-based semantic search" -ForegroundColor Green
    Write-Host "   ✅ Versioned prompt engineering" -ForegroundColor Green
    Write-Host "   ✅ A/B testing for prompts" -ForegroundColor Green
    Write-Host "   ✅ Production-ready RAG pipeline" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Setup incomplete. Check errors above." -ForegroundColor Red
    exit 1
}
