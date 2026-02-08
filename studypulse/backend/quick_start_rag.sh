#!/bin/bash
# Quick Start Script for RAG Integration Testing

echo "🚀 StudyPulse RAG Integration - Quick Start"
echo "=========================================="
echo ""

# Step 1: Install new dependencies
echo "📦 Step 1: Installing new dependencies..."
cd backend
pip install qdrant-client sentence-transformers semantic-kernel tiktoken

# Step 2: Start Qdrant (if not running)
echo ""
echo "🔧 Step 2: Checking Qdrant vector database..."
if ! docker ps | grep -q qdrant; then
    echo "Starting Qdrant container..."
    docker run -d -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:v1.16.3
else
    echo "✅ Qdrant already running"
fi

# Step 3: Verify Ollama
echo ""
echo "🤖 Step 3: Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama not running. Please start: ollama serve"
    exit 1
fi

# Step 4: Test RAG components
echo ""
echo "🧪 Step 4: Testing RAG components..."
python3 << 'PYTHON'
import asyncio
from app.rag.vector_store import VectorStore
from app.rag.semantic_kernel_service import SemanticKernelService

async def test_rag():
    print("\n✅ Testing VectorStore...")
    vector_store = VectorStore(host="localhost", port=6333)
    stats = vector_store.get_collection_stats()
    print(f"   Collection stats: {stats}")
    
    print("\n✅ Testing SemanticKernelService...")
    sk_service = SemanticKernelService()
    
    sample_questions = [{
        "question_text": "What is the capital of India?",
        "options": {"A": "Mumbai", "B": "Delhi", "C": "Kolkata", "D": "Chennai"},
        "correct_answer": "B"
    }]
    
    questions = await sk_service.generate_question(
        topic_name="Indian Geography",
        subject_name="General Studies",
        exam_name="UPSC",
        sample_questions=sample_questions,
        count=2,
        prompt_version="v2_enhanced"
    )
    
    print(f"\n✅ Generated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"\n   Q{i}: {q.get('question_text', '')}")
        print(f"   Answer: {q.get('correct_answer')}")
    
    print("\n✅ All RAG components working!")

asyncio.run(test_rag())
PYTHON

echo ""
echo "=========================================="
echo "✅ RAG Integration Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Review PRODUCTION_ARCHITECTURE.md for full deployment plan"
echo "2. Test complete flow: python tests/test_rag_pipeline.py"
echo "3. Start backend: uvicorn app.main:app --reload"
echo ""
