"""Pydantic schemas for question import operations."""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl


class OptionData(BaseModel):
    """Enhanced option with optional image support for medical exams.
    
    Allows attaching images to individual options, which is critical for:
    - Clinical images (X-rays, CT scans, MRI)
    - Histopathology slides
    - Diagram-based questions
    - ECG strips
    """
    text: str = Field(..., min_length=1, description="Option text")
    image: Optional[str] = Field(None, description="Optional image URL for the option")


class QuestionImport(BaseModel):
    """Schema for importing a single question.

    Supports both text-only and image-enhanced questions.
    Options can be either:
    - Simple text: {"A": "text", "B": "text", ...}
    - With images: {"A": {"text": "text", "image": "url"}, ...}
    """

    topic_id: int = Field(..., description="ID of the topic this question belongs to")
    question_text: str = Field(..., min_length=10, description="The question text")
    options: Dict[str, Union[str, OptionData]] = Field(
        ..., 
        description="Options as {A: text/OptionData, B: text/OptionData, C: text/OptionData, D: text/OptionData}"
    )
    correct_answer: str = Field(..., pattern="^[A-D]$", description="Correct answer (A, B, C, or D)")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    source: str = Field(default="MANUAL", description="Source of the question (MANUAL, PREVIOUS, WEB, PDF)")
    year: Optional[int] = Field(None, ge=1950, le=2030, description="Year of exam (for previous year questions)")
    difficulty: str = Field(default="medium", description="Difficulty level")
    
    # Image support fields
    question_images: Optional[List[str]] = Field(
        default_factory=list, 
        description="List of image URLs attached to the question"
    )
    explanation_images: Optional[List[str]] = Field(
        default_factory=list, 
        description="List of image URLs for the explanation"
    )
    audio_url: Optional[str] = Field(None, description="Audio explanation URL")
    video_url: Optional[str] = Field(None, description="Video explanation URL")

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Dict[str, Union[str, OptionData]]) -> Dict[str, Union[str, OptionData]]:
        """Ensure options has exactly 4 keys: A, B, C, D."""
        required_keys = {"A", "B", "C", "D"}
        if set(v.keys()) != required_keys:
            raise ValueError("Options must have exactly 4 keys: A, B, C, D")
        
        for key, value in v.items():
            if isinstance(value, str):
                if not value or len(value.strip()) < 1:
                    raise ValueError(f"Option {key} cannot be empty")
            elif isinstance(value, dict):
                if not value.get("text") or len(value.get("text", "").strip()) < 1:
                    raise ValueError(f"Option {key} text cannot be empty")
            elif isinstance(value, OptionData):
                if not value.text or len(value.text.strip()) < 1:
                    raise ValueError(f"Option {key} text cannot be empty")
            else:
                raise ValueError(f"Option {key} must be a string or OptionData object")
        
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Ensure difficulty is one of: easy, medium, hard."""
        valid = {"easy", "medium", "hard"}
        if v.lower() not in valid:
            raise ValueError(f"Difficulty must be one of: {', '.join(valid)}")
        return v.lower()

    @field_validator("question_images", "explanation_images")
    @classmethod
    def validate_image_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image URLs are properly formatted."""
        if v is None:
            return []
        for url in v:
            if not isinstance(url, str) or not url.startswith(('http://', 'https://', '//')):
                raise ValueError(f"Invalid image URL: {url}")
        return v


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
    options: Dict[str, Union[str, OptionData]]
    correct_answer: str
    source: str
    difficulty: str
    topic_id: int
    question_images: Optional[List[str]] = []
    explanation_images: Optional[List[str]] = []


class ExtendedQuestionData(BaseModel):
    """Extended data for questions including images and media."""
    
    question_id: int
    question_images: List[str] = Field(default_factory=list)
    explanation_images: List[str] = Field(default_factory=list)
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    source_topic: Optional[str] = None
    original_metadata: Dict[str, Any] = Field(default_factory=dict)
