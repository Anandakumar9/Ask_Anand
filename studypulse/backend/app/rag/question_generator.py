"""Async question generator — PARALLEL batched generation for speed.

Key design decisions:
  - Generates questions in batches of 3 (not all at once)
  - phi4-mini reliably produces 1-3 questions per call
  - Asking for 7-10 at once causes timeouts and malformed JSON
  - Uses Ollama format="json" for clean output (set in ollama.py)
  - PARALLEL: Runs multiple batches concurrently using asyncio.gather()
"""
import asyncio
import logging
import time

from app.core.config import settings
from app.core.ollama import ollama_client
from app.rag.prompt_templates import get_batch_prompt, get_system_prompt
from app.rag.quality_validator import validate_questions_batch

logger = logging.getLogger(__name__)

# Load from settings (configurable via environment variables)
# How many questions to request per LLM call
# phi4-mini:3.8b reliably handles 3; increase for larger models
BATCH_SIZE = settings.QUESTION_BATCH_SIZE

# How many batches to run in parallel (multi-agent deployment)
# Increase for faster generation (requires more CPU/RAM)
PARALLEL_BATCHES = settings.PARALLEL_QUESTION_AGENTS


class QuestionGenerator:
    """Generates exam-specific MCQ questions using Ollama LLM in batches."""

    def __init__(self):
        """Initialize generator with metrics tracking."""
        self.total_generated = 0
        self.total_valid = 0
        self.total_invalid = 0
        self.generation_time = 0.0

    async def generate(
        self,
        exam_name: str,
        subject_name: str,
        topic_name: str,
        count: int = 5,
        context_questions: list[dict] | None = None,
        excluded_summaries: list[str] | None = None,
        max_retries: int = 3,
    ) -> list[dict]:
        """Generate MCQ questions via Ollama using PARALLEL batches.

        OPTIMIZED for speed: Runs multiple batches concurrently instead of sequentially.
        This reduces generation time from 132s to < 10s for 10 questions.
        """
        if not await ollama_client.is_available():
            logger.warning("Ollama unavailable — skipping AI generation")
            return []

        t0 = time.time()
        system = get_system_prompt(exam_name, subject_name)

        # Add existing DB question texts to dedup set
        seen_texts: set[str] = set()
        if excluded_summaries:
            for s in excluded_summaries:
                seen_texts.add(s.strip().lower()[:80])

        # PARALLEL GENERATION: Run multiple batches concurrently
        logger.info(
            f"🚀 Starting PARALLEL generation: {count} questions using {PARALLEL_BATCHES} concurrent agents"
        )

        all_valid = await self._generate_parallel(
            exam_name=exam_name,
            subject_name=subject_name,
            topic_name=topic_name,
            count=count,
            system=system,
            context_questions=context_questions,
            seen_texts=seen_texts,
        )

        elapsed = time.time() - t0
        self.generation_time += elapsed

        success_rate = (self.total_valid / self.total_generated * 100) if self.total_generated > 0 else 0

        # Warn if we didn't reach target count
        if len(all_valid) < count:
            logger.warning(
                f"⚠️  Only generated {len(all_valid)}/{count} questions. "
                f"Target not reached!"
            )

        logger.info(
            f"✅ PARALLEL generation complete: {len(all_valid)}/{count} Qs in {elapsed:.1f}s "
            f"(~{elapsed/max(1, len(all_valid)):.1f}s per question) | Quality: {success_rate:.1f}% pass rate"
        )
        return all_valid[:count]

    async def _generate_parallel(
        self,
        exam_name: str,
        subject_name: str,
        topic_name: str,
        count: int,
        system: str,
        context_questions: list[dict] | None,
        seen_texts: set[str],
    ) -> list[dict]:
        """Generate questions using parallel batch execution.

        Runs PARALLEL_BATCHES concurrent LLM calls to dramatically reduce latency.
        """
        all_valid: list[dict] = []

        # Calculate how many parallel rounds we need
        questions_per_batch = BATCH_SIZE
        batches_needed = (count + questions_per_batch - 1) // questions_per_batch

        # Run batches in parallel rounds
        round_num = 0
        while len(all_valid) < count and round_num < 3:  # Max 3 rounds
            round_num += 1
            remaining = count - len(all_valid)

            # How many parallel batches to run this round
            parallel_count = min(PARALLEL_BATCHES, (remaining + questions_per_batch - 1) // questions_per_batch)

            logger.info(
                f"🔄 Round {round_num}: Running {parallel_count} parallel batches "
                f"(have {len(all_valid)}/{count} questions)"
            )

            # Create tasks for parallel execution
            tasks = []
            for i in range(parallel_count):
                batch_num = (round_num - 1) * PARALLEL_BATCHES + i + 1
                task = self._generate_single_batch(
                    exam_name=exam_name,
                    subject_name=subject_name,
                    topic_name=topic_name,
                    system=system,
                    batch_num=batch_num,
                    already_generated=[q["question_text"][:60] for q in all_valid],
                    context_questions=context_questions,
                )
                tasks.append(task)

            # Execute all batches in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results from all parallel batches
            for batch_idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch failed with error: {result}")
                    continue

                if not result:
                    continue

                # Dedup and add valid questions
                for q in result:
                    if len(all_valid) >= count:
                        break

                    key = q["question_text"].strip().lower()[:80]
                    if key not in seen_texts:
                        seen_texts.add(key)
                        all_valid.append(q)

                logger.debug(
                    f"  Batch {batch_idx + 1}/{parallel_count}: "
                    f"added {len(result)} questions, total: {len(all_valid)}/{count}"
                )

        return all_valid

    async def _generate_single_batch(
        self,
        exam_name: str,
        subject_name: str,
        topic_name: str,
        system: str,
        batch_num: int,
        already_generated: list[str],
        context_questions: list[dict] | None,
    ) -> list[dict]:
        """Generate a single batch of questions (used for parallel execution)."""
        chunk_size = BATCH_SIZE

        prompt = get_batch_prompt(
            exam_name=exam_name,
            subject_name=subject_name,
            topic_name=topic_name,
            count=chunk_size,
            already_generated=already_generated,
            context_questions=context_questions,
        )

        logger.debug(
            f"  Agent {batch_num}: Requesting {chunk_size} questions..."
        )

        result = await ollama_client.generate_json(
            prompt=prompt,
            system=system,
            temperature=0.4 + (batch_num * 0.05),
        )

        if not result:
            logger.warning(f"  Agent {batch_num}: No valid output")
            return []

        # Handle both flat and nested list structures from Ollama
        if isinstance(result, dict):
            if "questions" in result:
                items = result["questions"]
            elif "data" in result:
                items = result["data"]
            elif "items" in result:
                items = result["items"]
            else:
                items = [result]
        elif isinstance(result, list):
            items = result
        else:
            items = [result]

        # Flatten nested structures
        items = self._flatten_recursive(items)

        # Basic structural validation
        valid = self._validate(items)

        # Quality validation
        if valid:
            quality_valid, quality_invalid, errors = validate_questions_batch(valid, strict=True)

            if quality_invalid:
                logger.debug(
                    f"  Agent {batch_num}: {len(quality_invalid)}/{len(valid)} questions failed quality check"
                )

            # Update metrics
            self.total_generated += len(items)
            self.total_valid += len(quality_valid)
            self.total_invalid += len(quality_invalid)

            logger.debug(
                f"  Agent {batch_num}: ✅ Generated {len(quality_valid)} quality questions"
            )

            return quality_valid

        return []

    @staticmethod
    def _flatten_recursive(lst):
        """Recursively flatten nested lists until we get list of dicts."""
        if not isinstance(lst, list):
            return [lst] if isinstance(lst, dict) else []

        flattened = []
        for item in lst:
            if isinstance(item, dict):
                flattened.append(item)
            elif isinstance(item, list):
                flattened.extend(QuestionGenerator._flatten_recursive(item))
        return flattened

    def get_metrics(self) -> dict:
        """Get generation performance metrics."""
        return {
            "total_generated": self.total_generated,
            "total_valid": self.total_valid,
            "total_invalid": self.total_invalid,
            "success_rate": (self.total_valid / self.total_generated * 100) if self.total_generated > 0 else 0,
            "total_time": self.generation_time,
            "avg_time_per_question": (self.generation_time / self.total_valid) if self.total_valid > 0 else 0,
        }

    # ── Validation ────────────────────────────────────────────

    @staticmethod
    def _validate(raw: list) -> list[dict]:
        """Validate and normalise generated questions."""
        valid = []
        for q in raw:
            if not isinstance(q, dict):
                continue

            # Helper to unwrap list-wrapped values from Ollama
            def unwrap(val):
                """Unwrap single-item lists that Ollama sometimes returns."""
                if isinstance(val, list) and len(val) == 1:
                    return val[0]
                return val

            # Get question text, unwrapping if needed
            text_raw = q.get("question_text") or q.get("question") or ""
            text_raw = unwrap(text_raw)
            text = text_raw.strip() if isinstance(text_raw, str) else ""
            if not text or len(text) < 10:
                continue

            # Get options, unwrapping if needed
            opts = unwrap(q.get("options", {}))
            if isinstance(opts, list) and len(opts) == 4:
                opts = {chr(65 + i): str(v) for i, v in enumerate(opts)}
            if not isinstance(opts, dict):
                continue

            # Re-key if missing A-D but has 4 items
            if not all(k in opts for k in "ABCD"):
                if len(opts) == 4:
                    keys = sorted(opts.keys())
                    opts = {chr(65 + i): opts[k] for i, k in enumerate(keys)}
                else:
                    continue

            # Get answer, unwrapping if needed
            ans_raw = q.get("correct_answer") or q.get("answer") or ""
            ans_raw = unwrap(ans_raw)
            ans = ans_raw.strip().upper() if isinstance(ans_raw, str) else ""
            # Handle "A)" or "A." format
            if len(ans) > 1:
                ans = ans[0]
            if ans not in opts:
                continue

            # Get explanation, unwrapping if needed
            expl_raw = q.get("explanation") or ""
            expl_raw = unwrap(expl_raw)
            explanation = (expl_raw.strip() if isinstance(expl_raw, str) else "") or "No explanation provided."

            # Get difficulty, unwrapping if needed
            diff_raw = q.get("difficulty") or "medium"
            diff_raw = unwrap(diff_raw)
            difficulty = diff_raw.lower() if isinstance(diff_raw, str) else "medium"

            # Get bloom level, unwrapping if needed
            bloom_raw = q.get("bloom_level") or "understand"
            bloom_raw = unwrap(bloom_raw)
            bloom_level = bloom_raw.lower() if isinstance(bloom_raw, str) else "understand"

            valid.append(
                {
                    "question_text": text,
                    "options": opts,
                    "correct_answer": ans,
                    "explanation": explanation,
                    "difficulty": difficulty,
                    "bloom_level": bloom_level,
                    "source": "AI",
                }
            )
        return valid
