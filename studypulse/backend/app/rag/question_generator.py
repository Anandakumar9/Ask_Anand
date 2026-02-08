"""Async question generator — calls Ollama with exam-specific prompts.

Fully async via httpx, never blocks the event loop.
Includes retry logic and strict validation of generated questions.
"""
import logging
import time

from app.core.ollama import ollama_client
from app.rag.prompt_templates import get_exam_prompt

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates exam-specific MCQ questions using Ollama LLM."""

    async def generate(
        self,
        exam_name: str,
        subject_name: str,
        topic_name: str,
        count: int = 5,
        context_questions: list[dict] | None = None,
        excluded_summaries: list[str] | None = None,
        max_retries: int = 2,
    ) -> list[dict]:
        """Generate MCQ questions via Ollama.

        Returns list of validated question dicts.
        """
        if not await ollama_client.is_available():
            logger.warning("Ollama unavailable — skipping AI generation")
            return []

        system, user = get_exam_prompt(
            exam_name=exam_name,
            subject_name=subject_name,
            topic_name=topic_name,
            question_count=count,
            context_questions=context_questions,
            excluded_summaries=excluded_summaries,
        )

        for attempt in range(max_retries + 1):
            t0 = time.time()
            logger.info(
                f"Generating {count} Qs: {exam_name}/{topic_name} "
                f"(attempt {attempt + 1}/{max_retries + 1})"
            )

            result = await ollama_client.generate_json(
                prompt=user,
                system=system,
                temperature=0.4 + (attempt * 0.1),
            )
            elapsed = time.time() - t0

            if result and isinstance(result, list):
                valid = self._validate(result)
                if valid:
                    logger.info(
                        f"Generated {len(valid)}/{count} valid Qs in {elapsed:.1f}s"
                    )
                    return valid[:count]

            logger.warning(
                f"Attempt {attempt + 1} produced no valid Qs ({elapsed:.1f}s)"
            )

        return []

    # ── Validation ────────────────────────────────────────────

    @staticmethod
    def _validate(raw: list) -> list[dict]:
        """Validate and normalise generated questions."""
        valid = []
        for q in raw:
            if not isinstance(q, dict):
                continue

            text = (q.get("question_text") or "").strip()
            if not text:
                continue

            opts = q.get("options", {})
            if isinstance(opts, list) and len(opts) == 4:
                opts = {chr(65 + i): str(v) for i, v in enumerate(opts)}
            if not isinstance(opts, dict):
                continue

            # Re-key if missing A-D but has 4 items
            if not all(k in opts for k in "ABCD"):
                if len(opts) == 4:
                    opts = {chr(65 + i): v for i, (_, v) in enumerate(sorted(opts.items()))}
                else:
                    continue

            ans = (q.get("correct_answer") or "").strip().upper()
            if ans not in opts:
                continue

            valid.append(
                {
                    "question_text": text,
                    "options": opts,
                    "correct_answer": ans,
                    "explanation": (q.get("explanation") or "").strip()
                    or "No explanation provided.",
                    "difficulty": (q.get("difficulty") or "medium").lower(),
                    "bloom_level": (q.get("bloom_level") or "understand").lower(),
                    "source": "AI",
                }
            )
        return valid
