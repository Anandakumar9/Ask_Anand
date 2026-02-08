# 🏗️ StudyPulse Production Architecture - Oracle Cloud Deployment

**Prepared by:** Senior Solutions Architect  
**Date:** February 7, 2026  
**Target:** Oracle Cloud Infrastructure (OCI)

---

## 📊 Executive Summary

### Current State (Local Development)
- ✅ Backend: FastAPI + Supabase (working)
- ✅ Mobile: Flutter Web (working)
- ✅ AI: Ollama Phi4 local (working)
- ✅ Vector DB: Qdrant Docker (working)
- ⚠️ **RAG Pipeline: Separate folder** (needs integration)

### Proposed State (Production on Oracle Cloud)
```
┌─────────────────────────────────────────────────────────────┐
│                   Oracle Cloud Infrastructure                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Load Balancer │──│  API Gateway    │──│  CloudFlare │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────┘ │
│           │                                                   │
│  ┌────────▼──────────────────────────────────────────────┐  │
│  │          Kubernetes Cluster (OKE)                      │  │
│  │                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │  │
│  │  │   Backend    │  │   Ollama     │  │   Qdrant    │ │  │
│  │  │  (FastAPI)   │──│   (Phi4)     │──│ (Vector DB) │ │  │
│  │  │  + RAG       │  │              │  │             │ │  │
│  │  └──────┬───────┘  └──────────────┘  └─────────────┘ │  │
│  │         │                                              │  │
│  │  ┌──────▼───────┐  ┌──────────────┐  ┌─────────────┐ │  │
│  │  │  Semantic    │  │   Prompt     │  │   Redis     │ │  │
│  │  │  Kernel      │──│   Registry   │──│   Cache     │ │  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Supabase DB    │  │  Object Storage │  │  Monitoring │ │
│  │  (PostgreSQL)   │  │  (S3-compatible)│  │  (Grafana)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Architectural Decisions

### ✅ **Decision 1: Merge RAG Pipeline into Backend**
**Rationale:**
- **Cost Optimization:** Single deployment unit = lower Oracle Cloud costs
- **Simplified Networking:** No inter-service latency between FastAPI and RAG
- **Easier Debugging:** Unified logging and tracing
- **Atomic Transactions:** Backend + RAG share same database session

**Implementation:**
```
studypulse/backend/app/
├── api/              # FastAPI endpoints
├── core/             # Config, auth
├── models/           # Database models
├── schemas/          # Pydantic
├── rag/              # ✅ INTEGRATED RAG SERVICE
│   ├── __init__.py
│   ├── question_generator.py  # Already exists
│   ├── vector_store.py        # NEW: Qdrant integration
│   ├── embeddings.py          # NEW: Sentence transformers
│   └── semantic_search.py     # NEW: Semantic question retrieval
└── services/         # Business logic
```

### ✅ **Decision 2: Semantic Kernel for Prompt Engineering**
**Why Semantic Kernel?**
- ✅ **Versioned Prompts:** Track prompt changes in Git
- ✅ **A/B Testing:** Test multiple prompt variants
- ✅ **Observability:** Log prompt performance metrics
- ✅ **LLM Agnostic:** Switch between Ollama, OpenAI, Azure OpenAI
- ✅ **Plugin Architecture:** Easily add new AI capabilities

**Example Integration:**
```python
# backend/app/rag/semantic_kernel_service.py
import semantic_kernel as sk
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion

kernel = sk.Kernel()
kernel.add_service(OllamaChatCompletion(model="phi4"))

# Load prompts from templates
question_generator = kernel.create_function_from_prompt(
    prompt_template_path="prompts/question_generator_v2.txt",
    function_name="generate_question"
)

# Execute with telemetry
result = await question_generator.invoke(
    topic="History of Andhra Pradesh",
    difficulty="medium"
)
```

### ✅ **Decision 3: Oracle Cloud Container Engine for Kubernetes (OKE)**
**Why Kubernetes?**
- ✅ **Auto-scaling:** Scale backend pods based on CPU/memory
- ✅ **Rolling Updates:** Zero-downtime deployments
- ✅ **Self-healing:** Auto-restart failed containers
- ✅ **Cost-effective:** Oracle Cloud offers generous free tier + competitive pricing

**Oracle Cloud Resources:**
- **Compute:** 2x E4.Flex instances (4 OCPU, 16GB RAM) - ~$100/month
- **OKE Cluster:** Free control plane
- **Load Balancer:** $10/month
- **Block Storage:** 500GB SSD - $25/month
- **Bandwidth:** First 10TB free
- **Total Estimated Cost:** **~$135/month** (can optimize to ~$80 with reserved instances)

---

## 🔧 Implementation Roadmap

### **Phase 1: RAG Integration (Week 1)**
**Goal:** Merge RAG pipeline into backend as unified service

#### Step 1.1: Create Unified RAG Module
```bash
# Create new RAG service files
backend/app/rag/
├── vector_store.py       # Qdrant client
├── embeddings.py         # Sentence transformers
├── semantic_search.py    # Question retrieval
└── prompt_templates/     # Versioned prompts
    ├── v1_question_gen.txt
    └── v2_question_gen_enhanced.txt
```

#### Step 1.2: Install Dependencies
```txt
# Add to requirements.txt
semantic-kernel==0.9.0
qdrant-client==1.7.0
sentence-transformers==2.3.1
tiktoken==0.5.2
```

#### Step 1.3: Update Mock Test API
```python
# backend/app/api/mock_test.py
from app.rag.question_generator import QuestionGenerator
from app.rag.vector_store import VectorStore
from app.rag.semantic_search import SemanticQuestionSearch

@router.post("/start")
async def start_mock_test(test_data: MockTestCreate, db: Session):
    # 1. Retrieve previous year questions from DB
    prev_questions = await db.query(Question).filter(...).all()
    
    # 2. Semantic search for similar questions from vector DB
    vector_store = VectorStore()
    similar_questions = await vector_store.search(
        query=test_data.topic_name,
        limit=10
    )
    
    # 3. Generate AI questions using Semantic Kernel
    generator = QuestionGenerator()
    ai_questions = await generator.generate_questions(
        topic_name=test_data.topic_name,
        sample_questions=prev_questions + similar_questions,
        count=5
    )
    
    # 4. Mix and return
    final_questions = mix_questions(prev_questions, ai_questions)
    return {"questions": final_questions}
```

### **Phase 2: Semantic Kernel Integration (Week 2)**
**Goal:** Implement versioned prompt engineering system

#### Step 2.1: Create Prompt Registry
```
backend/app/rag/prompts/
├── question_generator/
│   ├── v1_basic.txt
│   ├── v2_enhanced.txt
│   └── v3_exam_specific.txt
├── answer_explainer/
│   └── v1_detailed.txt
└── performance_analyzer/
    └── v1_student_feedback.txt
```

#### Step 2.2: Implement Semantic Kernel Service
```python
# backend/app/rag/sk_service.py
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

class SemanticKernelService:
    def __init__(self):
        self.kernel = Kernel()
        self.kernel.add_service(
            OllamaChatCompletion(
                model="phi4",
                base_url="http://localhost:11434"
            )
        )
        
    async def generate_question_with_version(
        self,
        topic: str,
        prompt_version: str = "v2"
    ):
        """Generate question using versioned prompt."""
        prompt_path = f"prompts/question_generator/{prompt_version}_enhanced.txt"
        
        # Load and execute prompt
        function = self.kernel.create_function_from_prompt(
            prompt_template_path=prompt_path
        )
        
        result = await function.invoke(
            topic=topic,
            difficulty="medium"
        )
        
        # Log performance metrics
        await self._log_prompt_metrics(
            version=prompt_version,
            latency_ms=result.metadata.latency,
            tokens_used=result.metadata.tokens
        )
        
        return result.value
```

#### Step 2.3: Implement A/B Testing for Prompts
```python
# backend/app/rag/prompt_ab_testing.py
import random
from typing import Dict, List

class PromptABTester:
    def __init__(self):
        self.variants = {
            'control': 'v1_basic.txt',
            'variant_a': 'v2_enhanced.txt',
            'variant_b': 'v3_exam_specific.txt'
        }
        self.metrics = {}
        
    def get_prompt_variant(self, user_id: int) -> str:
        """Assign user to a variant."""
        # Use consistent hashing for user
        bucket = user_id % 100
        
        if bucket < 33:
            return 'control'
        elif bucket < 66:
            return 'variant_a'
        else:
            return 'variant_b'
            
    async def track_performance(
        self,
        variant: str,
        user_score: float,
        user_feedback: int
    ):
        """Track prompt variant performance."""
        if variant not in self.metrics:
            self.metrics[variant] = []
            
        self.metrics[variant].append({
            'score': user_score,
            'feedback': user_feedback,
            'timestamp': datetime.now()
        })
        
    def get_winning_variant(self) -> str:
        """Determine best performing prompt."""
        avg_scores = {}
        for variant, data in self.metrics.items():
            avg_scores[variant] = sum(d['score'] for d in data) / len(data)
        
        return max(avg_scores, key=avg_scores.get)
```

### **Phase 3: Dockerization (Week 3)**
**Goal:** Containerize all services for local testing

#### Step 3.1: Enhanced Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Backend API with integrated RAG
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    container_name: studypulse-api
    environment:
      - DATABASE_URL=${SUPABASE_URL}
      - OLLAMA_BASE_URL=http://ollama:11434
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379
      - SEMANTIC_KERNEL_LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    depends_on:
      - ollama
      - qdrant
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    
  # Ollama Phi4 LLM
  ollama:
    image: ollama/ollama:latest
    container_name: studypulse-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_MAX_LOADED_MODELS=1
    command: serve
    restart: unless-stopped
    
  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.16.3
    container_name: studypulse-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
    
  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: studypulse-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: unless-stopped
    
  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: studypulse-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped
    
  # Grafana Dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: studypulse-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

volumes:
  ollama_models:
  qdrant_storage:
  redis_data:
  prometheus_data:
  grafana_data:
```

#### Step 3.2: Production Dockerfile
```dockerfile
# backend/Dockerfile.production
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### **Phase 4: Oracle Cloud Deployment (Week 4)**
**Goal:** Deploy to OCI with Kubernetes

#### Step 4.1: Kubernetes Manifests
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: studypulse-backend
  namespace: studypulse-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: {REGION}.ocir.io/{TENANCY}/studypulse-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: OLLAMA_BASE_URL
          value: "http://ollama-service:11434"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Step 4.2: Oracle Cloud Setup Script
```bash
# scripts/deploy-oracle-cloud.sh
#!/bin/bash

# 1. Setup OCI CLI
oci setup config

# 2. Create OKE Cluster
oci ce cluster create \
  --name studypulse-cluster \
  --compartment-id $COMPARTMENT_ID \
  --kubernetes-version v1.28.2 \
  --vcn-id $VCN_ID \
  --node-pools '[{
    "name": "pool1",
    "size": 2,
    "shape": "VM.Standard.E4.Flex",
    "memory-in-gbs": 16,
    "ocpus": 4
  }]'

# 3. Get kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_ID \
  --file $HOME/.kube/config

# 4. Deploy application
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/ollama-deployment.yaml
kubectl apply -f k8s/qdrant-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# 5. Setup monitoring
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

echo "✅ Deployment complete!"
echo "Backend URL: $(kubectl get svc backend-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
```

---

## 📊 Cost Optimization Strategies

### **Oracle Cloud Free Tier (Always Free)**
- ✅ 2x AMD E2.1.Micro instances (1 OCPU, 1GB RAM each)
- ✅ 4x Arm Ampere A1 instances (4 OCPU, 24GB RAM total)
- ✅ 200GB block storage
- ✅ 10TB outbound bandwidth/month

### **Recommended Production Setup**
```
Component              | Instance Type    | Cost/Month
---------------------------------------------------------
Backend (3 replicas)   | E4.Flex 2 OCPU  | $60
Ollama LLM            | E4.Flex 4 OCPU  | $120 (can use Always Free ARM)
Qdrant Vector DB      | E4.Flex 2 OCPU  | $60
Redis Cache           | Micro (Free)     | $0
Load Balancer         | Flexible LB      | $10
Block Storage 500GB   | SSD              | $25
---------------------------------------------------------
TOTAL                                    | $275/month

OPTIMIZED (using Always Free ARM):
Backend + Ollama on ARM A1 (Free)        | $0
Qdrant on E4.Flex 2 OCPU                 | $60
Load Balancer                             | $10
Block Storage                             | $25
---------------------------------------------------------
OPTIMIZED TOTAL                          | $95/month 🎉
```

---

## 🧪 Testing Strategy

### **End-to-End Test Flow**
```python
# tests/test_complete_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_student_journey():
    """Test full flow: Register → Study → Test → Results"""
    
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Register user
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!",
            "name": "Test User"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get dashboard
        response = await client.get("/api/v1/dashboard/", headers=headers)
        assert response.status_code == 200
        assert "stats" in response.json()
        
        # 3. Start study session
        response = await client.post("/api/v1/study/sessions", headers=headers, json={
            "topic_id": 1,
            "duration_mins": 10
        })
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        # 4. Complete session (simulate)
        await asyncio.sleep(2)  # Wait 2 seconds for demo
        
        # 5. Start mock test (RAG integration test)
        response = await client.post("/api/v1/mock-test/start", headers=headers, json={
            "topic_id": 1,
            "session_id": session_id,
            "question_count": 10,
            "previous_year_ratio": 0.5
        })
        assert response.status_code == 200
        test_data = response.json()
        
        # Verify RAG generated questions
        assert len(test_data["questions"]) == 10
        ai_questions = [q for q in test_data["questions"] if q["source"] == "AI"]
        assert len(ai_questions) >= 5, "Should have AI-generated questions"
        
        # 6. Submit answers
        responses = [
            {"question_id": q["id"], "answer": q["correct_answer"]}
            for q in test_data["questions"]
        ]
        response = await client.post(
            f"/api/v1/mock-test/{test_data['test_id']}/submit",
            headers=headers,
            json={"responses": responses, "total_time_seconds": 600}
        )
        assert response.status_code == 200
        
        # 7. Verify results
        results = response.json()
        assert results["score"] == 100.0, "All answers correct"
        assert results["earned_star"] == True, "Should earn star for 100%"
        
        print("✅ Complete flow test PASSED!")
```

### **RAG Pipeline Test**
```python
# tests/test_rag_pipeline.py
@pytest.mark.asyncio
async def test_rag_question_generation():
    """Test RAG pipeline generates quality questions"""
    
    from app.rag.question_generator import QuestionGenerator
    from app.rag.vector_store import VectorStore
    
    generator = QuestionGenerator()
    vector_store = VectorStore()
    
    # Sample previous year questions
    sample_questions = [
        {
            "question_text": "What is the capital of Andhra Pradesh?",
            "options": {"A": "Hyderabad", "B": "Amaravati", "C": "Vijayawada", "D": "Visakhapatnam"},
            "correct_answer": "B"
        }
    ]
    
    # Generate AI questions
    ai_questions = await generator.generate_questions(
        topic_name="Geography of Andhra Pradesh",
        subject_name="General Studies",
        exam_name="UPSC",
        sample_questions=sample_questions,
        count=5
    )
    
    # Assertions
    assert len(ai_questions) == 5
    for q in ai_questions:
        assert "question_text" in q
        assert len(q["options"]) == 4
        assert q["correct_answer"] in ["A", "B", "C", "D"]
        assert "explanation" in q
        assert q["source"] == "AI"
    
    print("✅ RAG pipeline test PASSED!")
```

---

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] All tests passing (pytest --cov=app tests/)
- [ ] Docker Compose running successfully locally
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Semantic Kernel prompts versioned in Git
- [ ] Security scan completed (trivy, bandit)

### **Oracle Cloud Setup**
- [ ] OCI account created
- [ ] Compartment created
- [ ] VCN and subnets configured
- [ ] OKE cluster created
- [ ] Container Registry set up
- [ ] Secrets stored in OCI Vault

### **Post-Deployment**
- [ ] Load balancer health checks passing
- [ ] Prometheus metrics collecting
- [ ] Grafana dashboards configured
- [ ] Logs aggregated in OCI Logging
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured

---

## 📈 Performance Targets

| Metric                    | Target      | Current    |
|---------------------------|-------------|------------|
| API Response Time (p95)   | < 200ms     | TBD        |
| Question Generation Time  | < 5s        | ~3s ✅     |
| Concurrent Users          | 1000+       | TBD        |
| Uptime                    | 99.9%       | N/A        |
| AI Question Quality       | >85% user rating | TBD   |
| Cost per 1000 tests       | < $0.50     | TBD        |

---

## 🎯 Next Steps (Priority Order)

1. **Week 1:** Integrate RAG into backend as service module ⭐
2. **Week 2:** Implement Semantic Kernel for prompt versioning ⭐
3. **Week 3:** Test complete flow end-to-end locally
4. **Week 4:** Deploy to Oracle Cloud OKE
5. **Ongoing:** Monitor metrics, optimize prompts, reduce costs

---

**Senior Architect Recommendation:** Start with Phase 1 (RAG integration) this week. This provides immediate value and validates the architecture before cloud deployment. Semantic Kernel integration in Week 2 sets up robust prompt engineering foundation for continuous improvement.
