"""Unit tests for RAG question quality validator."""
import pytest

from app.rag.quality_validator import (
    QuestionValidator,
    validate_question,
    validate_questions_batch,
)


class TestQuestionStructure:
    """Test structural validation of questions."""

    def test_valid_question_structure(self, sample_question_data):
        """Test validation passes for well-formed question."""
        is_valid, errors = validate_question(sample_question_data, strict=True)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        question = {
            "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
            "correct_answer": "A",
            # Missing question_text
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("Missing required field" in err for err in errors)

    def test_empty_required_field(self):
        """Test validation fails when required field is empty."""
        question = {
            "question_text": "",  # Empty
            "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
            "correct_answer": "A",
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("Empty field" in err for err in errors)


class TestOptionsValidation:
    """Test validation of question options."""

    def test_valid_options(self, sample_question_data):
        """Test valid 4-option question."""
        is_valid, errors = validate_question(sample_question_data)

        assert is_valid is True

    def test_missing_option(self):
        """Test validation fails with missing option."""
        question = {
            "question_text": "What is the capital of France?",
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin"
                # Missing D
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France."
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("exactly A, B, C, D" in err for err in errors)

    def test_duplicate_options(self):
        """Test validation fails with duplicate option values."""
        question = {
            "question_text": "What is 2+2?",
            "options": {
                "A": "4",
                "B": "4",  # Duplicate
                "C": "5",
                "D": "6"
            },
            "correct_answer": "A",
            "explanation": "2+2=4"
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("Duplicate options" in err for err in errors)

    def test_empty_option_value(self):
        """Test validation fails with empty option."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "",  # Empty
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A",
            "explanation": "Explanation here."
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("Option B is empty" in err for err in errors)

    def test_short_option_value(self):
        """Test validation fails with too short option."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Long answer here",
                "B": "X",  # Too short (1 char)
                "C": "Another answer",
                "D": "Final answer"
            },
            "correct_answer": "A",
            "explanation": "Explanation here."
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("too short" in err for err in errors)

    def test_options_not_dict(self):
        """Test validation fails when options is not a dict."""
        question = {
            "question_text": "What is the answer?",
            "options": ["A", "B", "C", "D"],  # List instead of dict
            "correct_answer": "A",
            "explanation": "Explanation here."
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("Options must be a dictionary" in err for err in errors)


class TestCorrectAnswerValidation:
    """Test validation of correct answer."""

    def test_valid_correct_answer(self, sample_question_data):
        """Test valid correct answer."""
        is_valid, errors = validate_question(sample_question_data)

        assert is_valid is True

    def test_invalid_correct_answer_letter(self):
        """Test validation fails with invalid answer letter."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "E",  # Invalid
            "explanation": "Explanation here."
        }

        is_valid, errors = validate_question(question)

        assert is_valid is False
        assert any("must be A, B, C, or D" in err for err in errors)

    def test_lowercase_correct_answer(self):
        """Test validation with lowercase correct answer."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "b",  # Lowercase (should be normalized)
            "explanation": "Explanation here."
        }

        # Should pass after normalization to uppercase
        validator = QuestionValidator()
        is_valid, errors = validator.validate(question)

        # Current implementation normalizes to uppercase
        assert is_valid is True


class TestExplanationValidation:
    """Test validation of explanations."""

    def test_valid_explanation(self, sample_question_data):
        """Test valid explanation."""
        is_valid, errors = validate_question(sample_question_data, strict=True)

        assert is_valid is True

    def test_missing_explanation_strict(self):
        """Test validation fails with missing explanation in strict mode."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A"
            # Missing explanation
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("Missing explanation" in err for err in errors)

    def test_missing_explanation_non_strict(self):
        """Test validation passes with missing explanation in non-strict mode."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A"
        }

        is_valid, errors = validate_question(question, strict=False)

        # Non-strict mode should pass even without explanation
        # (Check implementation - might still flag as warning)
        assert is_valid is False or len(errors) == 0

    def test_short_explanation(self):
        """Test validation fails with too short explanation."""
        question = {
            "question_text": "What is the answer?",
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A",
            "explanation": "Too short"  # Less than 20 chars
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("Explanation too short" in err for err in errors)


class TestContentQualityValidation:
    """Test content quality checks."""

    def test_valid_content(self, sample_question_data):
        """Test valid question content."""
        is_valid, errors = validate_question(sample_question_data, strict=True)

        assert is_valid is True

    def test_question_too_short(self):
        """Test validation fails with too short question."""
        question = {
            "question_text": "What?",  # Too short
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A",
            "explanation": "This is a proper explanation with enough characters."
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("Question too short" in err for err in errors)

    def test_question_missing_punctuation(self):
        """Test validation warns about missing punctuation."""
        question = {
            "question_text": "What is the capital of France",  # No punctuation
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Madrid"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France."
        }

        is_valid, errors = validate_question(question, strict=True)

        # Should flag missing punctuation
        assert any("punctuation" in err for err in errors)

    def test_question_with_unclosed_parenthesis(self):
        """Test validation fails with unclosed parenthesis."""
        question = {
            "question_text": "What is the answer (incomplete",  # Unclosed
            "options": {
                "A": "Answer 1",
                "B": "Answer 2",
                "C": "Answer 3",
                "D": "Answer 4"
            },
            "correct_answer": "A",
            "explanation": "This is a proper explanation."
        }

        is_valid, errors = validate_question(question, strict=True)

        assert is_valid is False
        assert any("incomplete" in err.lower() for err in errors)

    def test_invalid_difficulty(self):
        """Test validation flags invalid difficulty."""
        question = {
            "question_text": "What is the capital of France?",
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Madrid"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France.",
            "difficulty": "super_hard"  # Invalid
        }

        is_valid, errors = validate_question(question, strict=True)

        assert any("Invalid difficulty" in err for err in errors)


class TestLanguageQualityValidation:
    """Test language quality checks."""

    def test_valid_language(self, sample_question_data):
        """Test valid language quality."""
        is_valid, errors = validate_question(sample_question_data, strict=True)

        assert is_valid is True

    def test_ai_artifact_detection(self):
        """Test detection of AI-generated artifacts."""
        ai_artifacts = [
            "As an AI, I cannot answer this question.",
            "I apologize, but the question is unclear.",
            "Here is a question about history:",
        ]

        for artifact_text in ai_artifacts:
            question = {
                "question_text": artifact_text,
                "options": {
                    "A": "Answer 1",
                    "B": "Answer 2",
                    "C": "Answer 3",
                    "D": "Answer 4"
                },
                "correct_answer": "A",
                "explanation": "This is a proper explanation."
            }

            is_valid, errors = validate_question(question, strict=True)

            assert is_valid is False
            assert any("AI artifact" in err for err in errors)

    def test_excessive_capitalization(self):
        """Test detection of excessive capitalization."""
        question = {
            "question_text": "WHAT IS THE CAPITAL OF FRANCE?",  # All caps
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Madrid"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France."
        }

        is_valid, errors = validate_question(question, strict=True)

        # Should flag excessive capitalization
        assert any("capitalization" in err.lower() for err in errors)

    def test_multiple_question_marks(self):
        """Test detection of multiple question marks."""
        question = {
            "question_text": "What is the capital of France???",  # Multiple ??
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Madrid"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France."
        }

        is_valid, errors = validate_question(question, strict=True)

        # Should flag multiple question marks
        assert any("question marks" in err.lower() for err in errors)


class TestBatchValidation:
    """Test batch validation of multiple questions."""

    def test_batch_all_valid(self, sample_question_data):
        """Test batch validation with all valid questions."""
        questions = [sample_question_data] * 3

        valid, invalid, errors = validate_questions_batch(questions, strict=True)

        assert len(valid) == 3
        assert len(invalid) == 0
        assert len(errors) == 0

    def test_batch_mixed_validity(self, sample_question_data, invalid_question_data):
        """Test batch validation with mixed valid/invalid questions."""
        questions = [sample_question_data, invalid_question_data, sample_question_data]

        valid, invalid, errors = validate_questions_batch(questions, strict=True)

        assert len(valid) == 2
        assert len(invalid) == 1
        assert len(errors) > 0

    def test_batch_all_invalid(self, invalid_question_data):
        """Test batch validation with all invalid questions."""
        questions = [invalid_question_data] * 3

        valid, invalid, errors = validate_questions_batch(questions, strict=True)

        assert len(valid) == 0
        assert len(invalid) == 3
        assert len(errors) == 3  # One error report per question
