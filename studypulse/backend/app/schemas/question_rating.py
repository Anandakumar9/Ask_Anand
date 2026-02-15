"""Pydantic schemas for question rating system."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


# Enum classes for rating categories
class QualityScore(IntEnum):
    """Quality rating scale."""
    POOR = 1
    AVERAGE = 2
    GOOD = 3
    EXCELLENT = 4


class ClarityScore(IntEnum):
    """Clarity rating scale."""
    CONFUSING = 1
    CLEAR = 2
    VERY_CLEAR = 3


class DifficultyScore(IntEnum):
    """Difficulty rating scale."""
    TOO_EASY = 1
    JUST_RIGHT = 2
    TOO_HARD = 3


class RelevanceScore(IntEnum):
    """Relevance rating scale."""
    OFF_TOPIC = 1
    SOMEWHAT_RELEVANT = 2
    HIGHLY_RELEVANT = 3


class RateQuestionRequest(BaseModel):
    """Request to rate an AI-generated question with detailed categories."""
    question_id: int = Field(..., description="ID of the question to rate")
    rating: int = Field(..., ge=1, le=5, description="Overall rating from 1-5 stars")

    # Detailed category scores
    quality_score: Optional[int] = Field(None, ge=1, le=4, description="Quality: 1=Poor, 2=Average, 3=Good, 4=Excellent")
    clarity_score: Optional[int] = Field(None, ge=1, le=3, description="Clarity: 1=Confusing, 2=Clear, 3=Very Clear")
    difficulty_score: Optional[int] = Field(None, ge=1, le=3, description="Difficulty: 1=Too Easy, 2=Just Right, 3=Too Hard")
    relevance_score: Optional[int] = Field(None, ge=1, le=3, description="Relevance: 1=Off-topic, 2=Somewhat Relevant, 3=Highly Relevant")

    feedback_text: Optional[str] = Field(None, max_length=500, description="Optional feedback")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Ensure rating is between 1 and 5."""
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class QuestionRatingResponse(BaseModel):
    """Response after rating a question."""
    id: int
    question_id: int
    user_id: int
    rating: int
    quality_score: Optional[int] = None
    clarity_score: Optional[int] = None
    difficulty_score: Optional[int] = None
    relevance_score: Optional[int] = None
    feedback_text: Optional[str] = None
    avg_rating: float = Field(..., description="Average rating from all users")
    rating_count: int = Field(..., description="Total number of ratings")
    message: str

    model_config = {"from_attributes": True}


class QuestionRatingStats(BaseModel):
    """Aggregated rating statistics for a question."""
    question_id: int
    total_ratings: int
    avg_rating: float
    avg_quality_score: Optional[float] = None
    avg_clarity_score: Optional[float] = None
    avg_difficulty_score: Optional[float] = None
    avg_relevance_score: Optional[float] = None

    # Distribution of ratings
    rating_distribution: dict[int, int] = {}  # {1: count, 2: count, ...}

    # Common feedback themes (if enough text feedback exists)
    common_feedback_themes: Optional[List[str]] = None


class LowRatedQuestion(BaseModel):
    """Schema for low-rated questions needing improvement."""
    id: int
    question_text: str
    topic_id: int
    topic_name: Optional[str] = None
    subject_name: Optional[str] = None
    avg_rating: float
    rating_count: int
    avg_quality_score: Optional[float] = None
    avg_clarity_score: Optional[float] = None
    avg_difficulty_score: Optional[float] = None
    avg_relevance_score: Optional[float] = None
    source: str
    created_at: datetime

    # Aggregated feedback insights
    main_issues: List[str] = []  # e.g., ["Poor clarity", "Too difficult"]
    sample_feedback: List[str] = []  # Recent user feedback


class RatingImprovement(BaseModel):
    """Schema for tracking rating improvements over time."""
    question_id: int
    initial_rating: float
    current_rating: float
    improvement_percentage: float
    total_ratings: int
    last_updated: datetime


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
