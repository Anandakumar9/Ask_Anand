"""Pydantic schemas for question rating."""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class RateQuestionRequest(BaseModel):
    """Request to rate an AI-generated question."""
    question_id: int = Field(..., description="ID of the question to rate")
    rating: int = Field(..., ge=1, le=10, description="Rating from 1-10 (10 = excellent)")
    feedback_text: Optional[str] = Field(None, max_length=500, description="Optional feedback")
    
    @validator('rating')
    def validate_rating(cls, v):
        """Ensure rating is between 1 and 10."""
        if not 1 <= v <= 10:
            raise ValueError("Rating must be between 1 and 10")
        return v


class QuestionRatingResponse(BaseModel):
    """Response after rating a question."""
    question_id: int
    your_rating: int
    avg_rating: float = Field(..., description="Average rating from all users")
    rating_count: int = Field(..., description="Total number of ratings")
    message: str
    
    model_config = {"from_attributes": True}


class QuestionQualityStats(BaseModel):
    """Statistics about question quality for prompt optimization."""
    prompt_version: str
    total_questions: int
    avg_rating: float
    ratings_distribution: dict[int, int] = Field(
        ..., 
        description="Distribution of ratings: {1: count, 2: count, ..., 10: count}"
    )
    low_quality_count: int = Field(..., description="Questions rated ≤4")
    high_quality_count: int = Field(..., description="Questions rated ≥8")
    sample_feedback: list[str] = Field(default=[], description="Sample feedback comments")
    
    @property
    def quality_percentage(self) -> float:
        """Percentage of high-quality questions."""
        if self.total_questions == 0:
            return 0.0
        return (self.high_quality_count / self.total_questions) * 100


class PromptComparisonResponse(BaseModel):
    """Compare quality metrics between prompt versions."""
    version_a: QuestionQualityStats
    version_b: QuestionQualityStats
    winner: Optional[str] = Field(None, description="Which version performs better")
    improvement_percentage: Optional[float] = Field(
        None, 
        description="How much better the winner is"
    )
