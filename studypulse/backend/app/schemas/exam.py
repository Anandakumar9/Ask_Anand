"""Pydantic schemas for exam, subject, and topic operations."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class TopicResponse(BaseModel):
    """Schema for topic response data."""
    id: int
    subject_id: int
    name: str
    description: Optional[str] = None
    difficulty_level: str = "medium"
    estimated_study_mins: int = 60
    icon_url: Optional[str] = None
    question_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class SubjectResponse(BaseModel):
    """Schema for subject response data."""
    id: int
    exam_id: int
    name: str
    description: Optional[str] = None
    syllabus_url: Optional[str] = None
    icon_url: Optional[str] = None
    topics: List[TopicResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class SubjectBrief(BaseModel):
    """Brief subject info without topics."""
    id: int
    exam_id: int
    name: str
    icon_url: Optional[str] = None
    topic_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ExamResponse(BaseModel):
    """Schema for exam response data."""
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    conducting_body: Optional[str] = None
    exam_duration_mins: int = 180
    total_questions: int = 100
    icon_url: Optional[str] = None
    subjects: List[SubjectBrief] = []
    
    model_config = ConfigDict(from_attributes=True)


class ExamBrief(BaseModel):
    """Brief exam info for listing."""
    id: int
    name: str
    category: Optional[str] = None
    icon_url: Optional[str] = None
    subject_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)
