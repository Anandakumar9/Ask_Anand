"""Pydantic schemas for question import operations."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class QuestionImport(BaseModel):
    """Schema for importing a single question."""

    topic_id: int = Field(..., description="ID of the topic this question belongs to")
    question_text: str = Field(..., min_length=10, description="The question text")
    options: Dict[str, str] = Field(..., description="Options as {A: text, B: text, C: text, D: text}")
    correct_answer: str = Field(..., pattern="^[A-D]$", description="Correct answer (A, B, C, or D)")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    source: str = Field(default="MANUAL", description="Source of the question (MANUAL, PREVIOUS, WEB, PDF)")
    year: Optional[int] = Field(None, ge=1950, le=2030, description="Year of exam (for previous year questions)")
    difficulty: str = Field(default="medium", description="Difficulty level")

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure options has exactly 4 keys: A, B, C, D."""
        required_keys = {"A", "B", "C", "D"}
        if set(v.keys()) != required_keys:
            raise ValueError("Options must have exactly 4 keys: A, B, C, D")
        for key, value in v.items():
            if not value or len(value.strip()) < 1:
                raise ValueError(f"Option {key} cannot be empty")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Ensure difficulty is one of: easy, medium, hard."""
        valid = {"easy", "medium", "hard"}
        if v.lower() not in valid:
            raise ValueError(f"Difficulty must be one of: {', '.join(valid)}")
        return v.lower()


class BulkQuestionImport(BaseModel):
    """Schema for bulk import of questions."""

    questions: List[QuestionImport] = Field(..., min_length=1, description="List of questions to import")

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: List[QuestionImport]) -> List[QuestionImport]:
        """Ensure no duplicate questions."""
        seen = set()
        for q in v:
            # Simple dedup by first 100 chars of question text
            key = q.question_text.strip().lower()[:100]
            if key in seen:
                raise ValueError(f"Duplicate question found: {q.question_text[:50]}...")
            seen.add(key)
        return v


class CSVImportRequest(BaseModel):
    """Schema for CSV import request."""

    topic_id: int = Field(..., description="Default topic ID for all questions in CSV")
    source: str = Field(default="CSV", description="Source identifier")
    csv_data: str = Field(..., description="CSV data as string")
    skip_header: bool = Field(default=True, description="Whether to skip first row as header")


class ImportResponse(BaseModel):
    """Response schema for import operations."""

    success: bool
    imported_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    question_ids: List[int] = Field(default_factory=list, description="IDs of successfully imported questions")


class QuestionPreview(BaseModel):
    """Preview of an imported question (for validation before bulk import)."""

    id: int
    question_text: str
    options: Dict[str, str]
    correct_answer: str
    source: str
    difficulty: str
    topic_id: int
