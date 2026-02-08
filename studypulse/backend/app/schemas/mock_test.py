"""Pydantic schemas for mock test operations."""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class QuestionDisplay(BaseModel):
    """Schema for displaying a question (without correct answer)."""
    id: int
    question_text: str
    options: Dict[str, str]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    source: str  # "PREVIOUS" or "AI"
    difficulty: str
    
    class Config:
        from_attributes = True


class QuestionWithAnswer(QuestionDisplay):
    """Schema for question with correct answer (for results)."""
    correct_answer: str
    explanation: Optional[str] = None
    year: Optional[int] = None


class StudySessionCreate(BaseModel):
    """Schema for creating a study session."""
    topic_id: int
    duration_mins: int


class StudySessionResponse(BaseModel):
    """Schema for study session response."""
    id: int
    user_id: int
    topic_id: int
    duration_mins: int
    actual_duration_mins: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    completed: bool = False
    
    class Config:
        from_attributes = True


class MockTestCreate(BaseModel):
    """Schema for starting a mock test."""
    topic_id: int
    session_id: Optional[int] = None  # Optional link to study session
    question_count: int = 10  # Number of questions
    time_limit_seconds: int = 600  # 10 minutes default
    previous_year_ratio: float = 0.5  # 50% previous year questions


class MockTestResponse(BaseModel):
    """Schema for mock test response (with questions)."""
    test_id: int
    questions: List[QuestionDisplay]
    total_questions: int
    time_limit_seconds: int
    started_at: datetime
    
    class Config:
        from_attributes = True


class AnswerItem(BaseModel):
    """Single answer in a submission."""
    question_id: int
    answer: Optional[str] = None  # "A", "B", "C", "D", or None
    time_spent_seconds: int = 0


class SubmitAnswers(BaseModel):
    """Schema for submitting mock test answers."""
    responses: List[AnswerItem]
    total_time_seconds: int


class QuestionResult(BaseModel):
    """Result for a single question."""
    id: int  # Added for rating purposes
    question_id: int
    question_text: str
    options: Dict[str, str]
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    source: str  # "PREVIOUS" or "AI" - helps identify AI questions for rating


class TestResult(BaseModel):
    """Schema for mock test results."""
    test_id: int
    total_questions: int
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    score_percentage: float
    star_earned: bool
    time_taken_seconds: int
    passed: bool  # Score >= 70%
    feedback_message: str
    questions: List[QuestionResult]  # Renamed from question_results for consistency
    
    # Performance metrics
    accuracy: float
    speed_rating: str  # "fast", "good", "slow"
    
    class Config:
        from_attributes = True


class RateQuestionRequest(BaseModel):
    """Schema for rating an AI-generated question."""
    question_id: int
    rating: int  # 1-5
    feedback: Optional[str] = None
