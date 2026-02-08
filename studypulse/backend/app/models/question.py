"""Question and QuestionRating models."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Question(Base):
    """Question model for storing exam questions."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String(1), nullable=False)  # "A", "B", "C", or "D"
    explanation = Column(Text)
    source = Column(String(20), default="PREVIOUS")  # "PREVIOUS" or "AI"
    year = Column(Integer, nullable=True)  # Year of the exam (for previous year questions)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    avg_rating = Column(Float, default=0.0)  # Average rating from users (1-10 scale)
    rating_count = Column(Integer, default=0)  # Total number of ratings
    metadata_json = Column(JSON, default={})  # Stores prompt_version, generation_time, etc.
    is_validated = Column(Boolean, default=False)  # Whether question has been validated
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    topic = relationship("Topic", back_populates="questions")
    ratings = relationship("QuestionRating", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question(id={self.id}, source='{self.source}', topic_id={self.topic_id})>"


class QuestionRating(Base):
    """Stores user ratings for AI-generated questions (1-10 scale)."""
    __tablename__ = "question_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-10 scale for AI question quality
    feedback_text = Column(Text, nullable=True)  # Optional text feedback
    prompt_version = Column(String(50), nullable=True)  # Which prompt generated this question
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("Question", back_populates="ratings")
    
    def __repr__(self):
        return f"<QuestionRating(question_id={self.question_id}, rating={self.rating})>"
