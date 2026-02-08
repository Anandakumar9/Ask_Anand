"""Exam-specific prompt templates for question generation.

Each competitive exam has unique question patterns, cognitive requirements,
and formatting conventions. This module provides structured prompts that
guide the LLM to generate exam-authentic MCQ questions.

Bloom's Taxonomy levels are used to control cognitive complexity:
  Remember → Understand → Apply → Analyze → Evaluate → Create
"""

# ── Exam profiles ─────────────────────────────────────────────

EXAM_PROFILES: dict[str, dict] = {
    "UPSC Civil Services": {
        "style": "analytical and conceptual",
        "question_types": [
            "statement-based",
            "assertion-reason",
            "match-the-following",
            "factual",
        ],
        "cognitive_focus": ["Analyze", "Evaluate", "Apply"],
        "difficulty_distribution": {"easy": 0.2, "medium": 0.5, "hard": 0.3},
        "instructions": (
            "- Use 'Consider the following statements...' format\n"
            "- Include 'Which of the above is/are correct?' patterns\n"
            "- Test conceptual understanding, not mere recall\n"
            "- Distractors should reflect common governance/history misconceptions"
        ),
    },
    "SSC CGL": {
        "style": "factual and speed-oriented",
        "question_types": ["direct-factual", "calculation", "analogy", "pattern"],
        "cognitive_focus": ["Remember", "Understand", "Apply"],
        "difficulty_distribution": {"easy": 0.4, "medium": 0.4, "hard": 0.2},
        "instructions": (
            "- Questions answerable in 30-60 seconds\n"
            "- Focus on factual recall and basic application\n"
            "- Clear, unambiguous language"
        ),
    },
    "JEE Main": {
        "style": "problem-solving and numerical",
        "question_types": ["conceptual-MCQ", "numerical", "multi-step"],
        "cognitive_focus": ["Apply", "Analyze", "Evaluate"],
        "difficulty_distribution": {"easy": 0.2, "medium": 0.5, "hard": 0.3},
        "instructions": (
            "- Multi-step calculation problems\n"
            "- Test deep understanding of Physics / Chemistry / Mathematics\n"
            "- Distractors should be values from common calculation errors"
        ),
    },
    "NEET UG": {
        "style": "biology-focused with clinical application",
        "question_types": ["assertion-reason", "diagram-based", "factual", "application"],
        "cognitive_focus": ["Remember", "Understand", "Apply"],
        "difficulty_distribution": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
        "instructions": (
            "- NCERT-aligned Biology content\n"
            "- Include assertion-reason type questions\n"
            "- Test application of biological concepts\n"
            "- Chemistry: focus on organic reactions and mechanisms"
        ),
    },
    "IBPS PO": {
        "style": "banking and quantitative reasoning",
        "question_types": ["data-interpretation", "reasoning", "calculation", "verbal"],
        "cognitive_focus": ["Apply", "Analyze", "Remember"],
        "difficulty_distribution": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
        "instructions": (
            "- Banking/finance context where relevant\n"
            "- Percentages, ratios, profit/loss for quantitative\n"
            "- Logical deduction for reasoning\n"
            "- Grammar, vocabulary, comprehension for English"
        ),
    },
    "CAT": {
        "style": "logical reasoning and verbal ability",
        "question_types": ["RC-passage", "logical-puzzle", "data-sufficiency", "para-jumble"],
        "cognitive_focus": ["Analyze", "Evaluate", "Apply"],
        "difficulty_distribution": {"easy": 0.1, "medium": 0.5, "hard": 0.4},
        "instructions": (
            "- Requires critical thinking\n"
            "- LRDI: complex data sets\n"
            "- Verbal: inference-based, not just comprehension\n"
            "- Quant: tricky, not just calculation-heavy"
        ),
    },
    "CBSE Class 12": {
        "style": "NCERT-aligned board exam pattern",
        "question_types": ["short-answer-MCQ", "application-based", "case-study"],
        "cognitive_focus": ["Remember", "Understand", "Apply"],
        "difficulty_distribution": {"easy": 0.4, "medium": 0.4, "hard": 0.2},
        "instructions": (
            "- Strictly follow NCERT syllabus and textbook content\n"
            "- Include case-study based questions (new CBSE pattern)\n"
            "- Exam-board appropriate difficulty"
        ),
    },
    "CBSE Class 10": {
        "style": "foundation-level board exam pattern",
        "question_types": ["direct-MCQ", "application-based", "assertion-reason"],
        "cognitive_focus": ["Remember", "Understand"],
        "difficulty_distribution": {"easy": 0.5, "medium": 0.4, "hard": 0.1},
        "instructions": (
            "- Simple, clear language for Class 10 students\n"
            "- Follow NCERT content strictly\n"
            "- Focus on fundamental concepts"
        ),
    },
}

_DEFAULT_PROFILE: dict = {
    "style": "standard competitive exam",
    "question_types": ["MCQ", "factual", "application"],
    "cognitive_focus": ["Remember", "Understand", "Apply"],
    "difficulty_distribution": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
    "instructions": "- Clear, well-structured MCQ questions\n- Plausible distractors",
}


# ── Helpers ───────────────────────────────────────────────────


def get_exam_profile(exam_name: str) -> dict:
    """Get exam profile; falls back to default if unknown exam."""
    if exam_name in EXAM_PROFILES:
        return EXAM_PROFILES[exam_name]
    for key, profile in EXAM_PROFILES.items():
        if exam_name.lower() in key.lower() or key.lower() in exam_name.lower():
            return profile
    return _DEFAULT_PROFILE


def get_exam_prompt(
    exam_name: str,
    subject_name: str,
    topic_name: str,
    question_count: int,
    context_questions: list[dict] | None = None,
    excluded_summaries: list[str] | None = None,
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for question generation.

    Includes exam-specific style, cognitive levels, difficulty distribution,
    reference questions for style matching, and an exclusion list for dedup.
    """
    p = get_exam_profile(exam_name)

    # ── System prompt ─────────────────────────────────────────
    system = (
        f"You are an expert {exam_name} question paper setter.\n"
        f"You create high-quality MCQ questions that match the exact pattern, "
        f"difficulty, and style of real {exam_name} exams.\n"
        f"You have deep domain knowledge of {subject_name}.\n"
        f"Respond with ONLY a valid JSON array. No extra text."
    )

    # ── Context block (reference questions) ───────────────────
    ctx = ""
    if context_questions:
        examples = []
        for i, q in enumerate(context_questions[:5], 1):
            opts = q.get("options", {})
            ostr = (
                "\n".join(f"  {k}) {v}" for k, v in opts.items())
                if isinstance(opts, dict)
                else str(opts)
            )
            examples.append(
                f"Example {i}: {q.get('question_text', '')}\n{ostr}\n"
                f"  Answer: {q.get('correct_answer', '')}"
            )
        ctx = "\n\nREFERENCE QUESTIONS (match this style):\n" + "\n\n".join(examples)

    # ── Exclusion block ───────────────────────────────────────
    excl = ""
    if excluded_summaries:
        excl = (
            "\n\nDO NOT REPEAT these questions:\n"
            + "\n".join(f"- {s}" for s in excluded_summaries[:20])
        )

    # ── Difficulty counts ─────────────────────────────────────
    dist = p["difficulty_distribution"]
    easy_n = max(1, round(question_count * dist["easy"]))
    hard_n = max(1, round(question_count * dist["hard"]))
    med_n = question_count - easy_n - hard_n

    # ── User prompt ───────────────────────────────────────────
    user = f"""Generate exactly {question_count} unique MCQ questions for:
- Exam: {exam_name}
- Subject: {subject_name}
- Topic: {topic_name}

STYLE: {p['style']}
QUESTION TYPES: {', '.join(p['question_types'])}
COGNITIVE LEVELS: {', '.join(p['cognitive_focus'])}

DIFFICULTY MIX: {easy_n} easy, {med_n} medium, {hard_n} hard

EXAM RULES:
{p['instructions']}{ctx}{excl}

Return ONLY this JSON array (no markdown, no explanation):
[
  {{
    "question_text": "Full question text",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "explanation": "Why this answer is correct",
    "difficulty": "easy|medium|hard",
    "bloom_level": "remember|understand|apply|analyze|evaluate"
  }}
]

RULES:
1. ONLY output the JSON array
2. Exactly 4 options per question (A, B, C, D)
3. Exactly 1 correct answer
4. Plausible distractors (common misconceptions)
5. Clear educational explanation for each
6. Factually accurate
7. Vary correct-answer position"""

    return system, user
