"""Exam-specific prompt templates for question generation.

Designed for batched generation with small models (phi4-mini):
  - Short, focused prompts that fit in context window
  - Separate system prompt (cached by Ollama) from batch prompt
  - Dedup instructions reference already-generated questions
  - Enhanced quality criteria for institutional standards

Bloom's Taxonomy levels control cognitive complexity:
  Remember → Understand → Apply → Analyze → Evaluate → Create
"""

# ── Exam profiles ─────────────────────────────────────────────

EXAM_PROFILES: dict[str, dict] = {
    "UPSC Civil Services": {
        "style": "analytical, statement-based, multi-dimensional",
        "focus": "conceptual understanding, governance, policy, current affairs integration",
        "standards": "NCERT-based, analytical depth, multiple correct interpretations avoided",
        "difficulty_mix": "30% easy, 50% medium, 20% hard",
    },
    "NEET PG": {
        "style": "clinical vignettes, case-based, diagnostic reasoning",
        "focus": "recent medical advances, clinical application, evidence-based practice",
        "standards": "Harrison's/Bailey's aligned, DNB guidelines, AIIMS pattern",
        "difficulty_mix": "20% easy, 50% medium, 30% hard",
    },
    "NEET UG": {
        "style": "biology-focused, NCERT-aligned, assertion-reason",
        "focus": "NCERT strict alignment, conceptual clarity, clinical correlation",
        "standards": "NCERT Class 11-12, no ambiguity, single correct answer",
        "difficulty_mix": "40% easy, 40% medium, 20% hard",
    },
    "SSC CGL": {
        "style": "factual, speed-oriented, direct questions",
        "focus": "recall, basic application, 30-60 sec per question, static GK",
        "standards": "previous year pattern, factual accuracy, no tricks",
        "difficulty_mix": "50% easy, 40% medium, 10% hard",
    },
    "JEE Main": {
        "style": "problem-solving, numerical, multi-step calculations",
        "focus": "deep concept application, physics/chemistry/math integration",
        "standards": "JEE Main syllabus, NTA guidelines, numerical accuracy critical",
        "difficulty_mix": "25% easy, 50% medium, 25% hard",
    },
    "IBPS PO": {
        "style": "banking/finance context, data interpretation, logical reasoning",
        "focus": "quantitative aptitude, banking awareness, current economic trends",
        "standards": "IBPS official pattern, RBI guidelines awareness",
        "difficulty_mix": "40% easy, 45% medium, 15% hard",
    },
    "CAT": {
        "style": "logical reasoning, critical thinking, inference-based",
        "focus": "data sufficiency, verbal ability, lateral thinking",
        "standards": "IIM pattern, no calculation tricks, reasoning clarity",
        "difficulty_mix": "20% easy, 50% medium, 30% hard",
    },
    "CBSE Class 12": {
        "style": "NCERT-aligned board pattern, case-study integration",
        "focus": "fundamentals, application-based, board marking scheme",
        "standards": "NCERT strict, CBSE board pattern, competency-based",
        "difficulty_mix": "50% easy, 35% medium, 15% hard",
    },
    "CBSE Class 10": {
        "style": "foundation-level, clear language, simple application",
        "focus": "fundamental concepts, direct application, no tricks",
        "standards": "NCERT Class 10, age-appropriate, single interpretation",
        "difficulty_mix": "60% easy, 30% medium, 10% hard",
    },
    "GATE": {
        "style": "engineering fundamentals, numerical problem-solving",
        "focus": "core concepts, multi-step reasoning, engineering application",
        "standards": "GATE syllabus, IIT/IISc standards, precise numerical answers",
        "difficulty_mix": "25% easy, 50% medium, 25% hard",
    },
}

_DEFAULT_PROFILE: dict = {
    "style": "standard competitive exam format",
    "focus": "conceptual clarity, practical application",
    "standards": "clear question, unambiguous options, single correct answer",
    "difficulty_mix": "40% easy, 40% medium, 20% hard",
}


def _get_profile(exam_name: str) -> dict:
    """Get exam profile; falls back to default."""
    if exam_name in EXAM_PROFILES:
        return EXAM_PROFILES[exam_name]
    for key, profile in EXAM_PROFILES.items():
        if exam_name.lower() in key.lower() or key.lower() in exam_name.lower():
            return profile
    return _DEFAULT_PROFILE


# ── Prompt builders ───────────────────────────────────────────


def get_system_prompt(exam_name: str, subject_name: str) -> str:
    """System prompt — cached by Ollama across batches.

    Enhanced with institutional quality standards.
    """
    p = _get_profile(exam_name)
    return (
        f"You are an expert {exam_name} question paper setter "
        f"specializing in {subject_name}.\n\n"
        f"EXAM PROFILE:\n"
        f"- Style: {p['style']}\n"
        f"- Focus: {p['focus']}\n"
        f"- Standards: {p['standards']}\n"
        f"- Difficulty Mix: {p['difficulty_mix']}\n\n"
        f"QUALITY REQUIREMENTS:\n"
        f"1. Each question must be UNAMBIGUOUS with EXACTLY ONE correct answer\n"
        f"2. Options must be DISTINCT and PLAUSIBLE (no obvious wrong answers)\n"
        f"3. Explanations must be CLEAR, CONCISE, and EDUCATIONAL\n"
        f"4. Language must be PROFESSIONAL and ERROR-FREE\n"
        f"5. Follow institutional standards strictly (NCERT/Harrison's/etc.)\n\n"
        f"OUTPUT FORMAT:\n"
        f"Always respond with ONLY a valid JSON array of question objects.\n"
        f"No explanation, no markdown, no text outside the JSON."
    )


def get_batch_prompt(
    exam_name: str,
    subject_name: str,
    topic_name: str,
    count: int,
    already_generated: list[str] | None = None,
    context_questions: list[dict] | None = None,
) -> str:
    """Build a concise batch prompt for N questions.

    Kept short to avoid overwhelming small models.
    Enhanced with quality checks.
    """
    # Dedup block
    dedup = ""
    if already_generated:
        dedup = "\n⚠️  DO NOT repeat these already-generated questions:\n"
        for q in already_generated[:10]:  # Show max 10 to preserve context
            dedup += f"  - {q[:100]}...\n"

    # Reference questions (style guide)
    ctx = ""
    if context_questions:
        ctx = "\n📚 Match this question style:\n"
        for q in context_questions[:2]:
            ctx += f"  Example: {q.get('question_text', '')[:100]}...\n"

    return (
        f"Generate exactly {count} high-quality MCQ questions for {exam_name}.\n\n"
        f"📋 TOPIC: {subject_name} > {topic_name}\n"
        f"{ctx}{dedup}\n"
        f"✅ REQUIREMENTS:\n"
        f"- Each question covers a DIFFERENT concept within {topic_name}\n"
        f"- Mix difficulties appropriately (refer to exam profile)\n"
        f"- All 4 options must be plausible but only ONE correct\n"
        f"- Explanation must teach WHY the answer is correct\n"
        f"- Use precise, professional language\n"
        f"- Follow institutional standards strictly\n\n"
        f"📝 JSON FORMAT (return ONLY this):\n"
        f'[{{\n'
        f'  "question_text": "Clear, unambiguous question here",\n'
        f'  "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},\n'
        f'  "correct_answer": "B",\n'
        f'  "explanation": "Why B is correct and others are wrong",\n'
        f'  "difficulty": "medium"\n'
        f'}}]'
    )


# ── Legacy compat (used by old code paths) ───────────────────


def get_exam_prompt(
    exam_name: str,
    subject_name: str,
    topic_name: str,
    question_count: int,
    context_questions: list[dict] | None = None,
    excluded_summaries: list[str] | None = None,
) -> tuple[str, str]:
    """Legacy compatibility wrapper. Returns (system, user) tuple."""
    system = get_system_prompt(exam_name, subject_name)
    user = get_batch_prompt(
        exam_name=exam_name,
        subject_name=subject_name,
        topic_name=topic_name,
        count=question_count,
        already_generated=excluded_summaries,
        context_questions=context_questions,
    )
    return system, user
