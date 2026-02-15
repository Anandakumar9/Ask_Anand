"""Question quality validator for AI-generated questions.

Ensures all generated questions meet institutional standards:
- Structural validation (4 options, correct answer, explanation)
- Content quality (no ambiguity, plausible distractors)
- Language quality (professional, error-free)
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class QuestionValidator:
    """Validates AI-generated questions for quality and correctness."""

    def __init__(self):
        self.validation_errors = []

    def validate(self, question: dict, strict: bool = True) -> tuple[bool, list[str]]:
        """Validate a single question.

        Args:
            question: Question dict with question_text, options, correct_answer, explanation
            strict: If True, fail on any error. If False, warn but pass minor issues.

        Returns:
            (is_valid, error_list)
        """
        self.validation_errors = []

        # 1. Structural validation
        if not self._validate_structure(question):
            return False, self.validation_errors

        # 2. Options validation
        if not self._validate_options(question):
            return False, self.validation_errors

        # 3. Correct answer validation
        if not self._validate_correct_answer(question):
            return False, self.validation_errors

        # 4. Explanation validation
        if not self._validate_explanation(question):
            if strict:
                return False, self.validation_errors
            # Non-strict: allow missing/short explanations

        # 5. Content quality validation
        if not self._validate_content_quality(question):
            if strict:
                return False, self.validation_errors

        # 6. Language quality
        if not self._validate_language_quality(question):
            if strict:
                return False, self.validation_errors

        return len(self.validation_errors) == 0, self.validation_errors

    def _validate_structure(self, q: dict) -> bool:
        """Check required fields exist."""
        required_fields = ['question_text', 'options', 'correct_answer']

        for field in required_fields:
            if field not in q:
                self.validation_errors.append(f"Missing required field: {field}")
                return False

            if not q[field]:
                self.validation_errors.append(f"Empty field: {field}")
                return False

        return True

    def _validate_options(self, q: dict) -> bool:
        """Validate options structure and content."""
        options = q.get('options', {})

        # Must have exactly 4 options
        if not isinstance(options, dict):
            self.validation_errors.append("Options must be a dictionary")
            return False

        expected_keys = ['A', 'B', 'C', 'D']
        if set(options.keys()) != set(expected_keys):
            self.validation_errors.append(
                f"Options must have exactly A, B, C, D. Got: {list(options.keys())}"
            )
            return False

        # Each option must be non-empty string
        for key, value in options.items():
            if not value or not isinstance(value, str):
                self.validation_errors.append(f"Option {key} is empty or invalid")
                return False

            if len(value.strip()) < 2:
                self.validation_errors.append(f"Option {key} too short: '{value}'")
                return False

        # Options should be distinct (no duplicates)
        option_values = [v.strip().lower() for v in options.values()]
        if len(option_values) != len(set(option_values)):
            self.validation_errors.append("Duplicate options found")
            return False

        # Options should not be trivially wrong (e.g., "None of the above")
        trivial_patterns = [
            r'none of the above',
            r'all of the above',
            r'both .* and .*',
            r'cannot be determined',
        ]
        for key, value in options.items():
            value_lower = value.lower()
            for pattern in trivial_patterns:
                if re.search(pattern, value_lower):
                    # This is OK if it's the correct answer, questionable otherwise
                    if key == q.get('correct_answer'):
                        continue
                    self.validation_errors.append(
                        f"Option {key} uses trivial pattern: '{value[:50]}'"
                    )

        return True

    def _validate_correct_answer(self, q: dict) -> bool:
        """Validate correct answer is one of the options."""
        correct = q.get('correct_answer', '').strip().upper()

        if correct not in ['A', 'B', 'C', 'D']:
            self.validation_errors.append(
                f"Correct answer must be A, B, C, or D. Got: '{correct}'"
            )
            return False

        # Correct answer must exist in options
        if correct not in q.get('options', {}):
            self.validation_errors.append(
                f"Correct answer '{correct}' not found in options"
            )
            return False

        return True

    def _validate_explanation(self, q: dict) -> bool:
        """Validate explanation quality."""
        explanation = q.get('explanation', '').strip()

        if not explanation:
            self.validation_errors.append("Missing explanation")
            return False

        if len(explanation) < 20:
            self.validation_errors.append(
                f"Explanation too short ({len(explanation)} chars): '{explanation}'"
            )
            return False

        # Explanation should reference the correct answer
        correct = q.get('correct_answer', '')
        if correct and correct not in explanation:
            # This is a warning, not necessarily an error
            logger.debug(
                f"Explanation doesn't mention correct answer '{correct}': {explanation[:50]}"
            )

        return True

    def _validate_content_quality(self, q: dict) -> bool:
        """Check for common quality issues."""
        question_text = q.get('question_text', '').strip()

        # Question should be substantial
        if len(question_text) < 15:
            self.validation_errors.append(
                f"Question too short ({len(question_text)} chars)"
            )
            return False

        # Question should end with punctuation
        if not question_text[-1] in ['.', '?', ':', ')']:
            self.validation_errors.append(
                "Question should end with proper punctuation"
            )

        # Check for incomplete sentences (common AI error)
        incomplete_patterns = [
            r'\.\.\.$',  # Trailing ellipsis
            r'\([^)]*$',  # Unclosed parenthesis
            r'\[[^\]]*$',  # Unclosed bracket
        ]
        for pattern in incomplete_patterns:
            if re.search(pattern, question_text):
                self.validation_errors.append(
                    "Question appears incomplete or has formatting errors"
                )
                return False

        # Check difficulty is valid
        difficulty = q.get('difficulty', '').lower()
        if difficulty and difficulty not in ['easy', 'medium', 'hard']:
            self.validation_errors.append(
                f"Invalid difficulty: '{difficulty}'. Must be easy/medium/hard"
            )

        return True

    def _validate_language_quality(self, q: dict) -> bool:
        """Basic language quality checks."""
        text = q.get('question_text', '')

        # Check for common AI artifacts
        ai_artifacts = [
            'as an ai',
            'i cannot',
            'i apologize',
            'here is',
            'here are',
            'the question is',
        ]

        text_lower = text.lower()
        for artifact in ai_artifacts:
            if artifact in text_lower:
                self.validation_errors.append(
                    f"Question contains AI artifact: '{artifact}'"
                )
                return False

        # Check for excessive capitalization (SHOUTING)
        if text.isupper() and len(text) > 20:
            self.validation_errors.append("Excessive capitalization in question")

        # Check for multiple question marks (???)
        if '??' in text:
            self.validation_errors.append("Multiple question marks found")

        return True


def validate_question(question: dict, strict: bool = True) -> tuple[bool, list[str]]:
    """Convenience function to validate a single question.

    Args:
        question: Question dict
        strict: Strict validation mode

    Returns:
        (is_valid, error_list)
    """
    validator = QuestionValidator()
    return validator.validate(question, strict=strict)


def validate_questions_batch(
    questions: list[dict], strict: bool = True
) -> tuple[list[dict], list[dict], list[str]]:
    """Validate a batch of questions.

    Args:
        questions: List of question dicts
        strict: Strict validation mode

    Returns:
        (valid_questions, invalid_questions, overall_errors)
    """
    validator = QuestionValidator()
    valid = []
    invalid = []
    overall_errors = []

    for i, q in enumerate(questions):
        is_valid, errors = validator.validate(q, strict=strict)
        if is_valid:
            valid.append(q)
        else:
            invalid.append(q)
            overall_errors.append(f"Question {i+1}: {', '.join(errors)}")
            logger.warning(f"Question {i+1} failed validation: {errors}")

    logger.info(
        f"Batch validation: {len(valid)}/{len(questions)} questions passed"
    )

    return valid, invalid, overall_errors
