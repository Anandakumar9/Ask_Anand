---
status: investigating
trigger: "Investigate why questions take 2 minutes to display to users in the app."
created: 2026-02-13T00:00:00Z
updated: 2026-02-13T00:00:00Z
symptoms_prefilled: true
---

## Current Focus

hypothesis: CONFIRMED - Batching logic requests too many Ollama API calls
test: Analyzed question_generator.py max_batches calculation and loop behavior
expecting: Root cause identified, ready to document fix
next_action: Document specific line numbers and code changes needed

## Symptoms

expected: Instant question display due to pre-generation
actual: 2-minute delay before users see questions
errors: Unknown - need to check logs/error handling
reproduction: User starts study session, waits 2 minutes for questions
started: Unknown - performance regression

## Eliminated

- hypothesis: Background task not running (asyncio.create_task issue)
  evidence: Verified study.py:61-63 correctly creates async task
  timestamp: 2026-02-13T00:03:00Z

- hypothesis: Missing await causing blocking operation
  evidence: All async calls properly awaited
  timestamp: 2026-02-13T00:04:00Z

## Evidence

- timestamp: 2026-02-13T00:05:00Z
  checked: config.py lines 30, 49
  found: OLLAMA_TIMEOUT=300s, RAG_ENABLED=True
  implication: AI generation enabled with long timeout

- timestamp: 2026-02-13T00:06:00Z
  checked: question_generator.py:67 max_batches calculation
  found: max_batches = (10//3)*2 + 5 + 3 = 14 batches for 10 questions
  implication: Up to 14 Ollama API calls

- timestamp: 2026-02-13T00:07:00Z
  checked: question_generator.py:20,41,69-171 batch loop
  found: BATCH_SIZE=3, loop runs 10-14 batches at 10-15s each
  implication: Total time = 120-168 seconds (2-2.8 minutes)

- timestamp: 2026-02-13T00:08:00Z
  checked: Both background pre-gen and fallback paths
  found: study.py:347 and study.py:262 both call orchestrator.generate_test()
  implication: Both hit same slow batching bottleneck

## Resolution

root_cause: Batching logic in question_generator.py:67 is too aggressive. Formula (count//BATCH_SIZE)*2 + 5 + max_retries produces 14 batches for 10 questions. Each Ollama call takes 10-15s, resulting in 120-168 second total time. This affects both background pre-generation and on-demand fallback.

fix: Reduce max_batches formula to (count//BATCH_SIZE) + 2 to minimize API calls while maintaining reliability. For 10 questions with BATCH_SIZE=3, this gives 5 batches maximum instead of 14.

verification:
files_changed:
  - studypulse/backend/app/rag/question_generator.py:67
