"""Exam, Subject, and Topic models for organizing questions."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Exam(Base):
    """Exam model (e.g., UPSC, SSC, JEE)."""
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)  # e.g., "UPSC Civil Services"
    description = Column(Text)
    category = Column(String(50))  # e.g., "Government", "School", "Engineering"
    conducting_body = Column(String(200))  # e.g., "UPSC", "CBSE"
    exam_duration_mins = Column(Integer, default=180)
    total_questions = Column(Integer, default=100)
    icon_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subjects = relationship("Subject", back_populates="exam", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exam(id={self.id}, name='{self.name}')>"




class Subject(Base):
    """Subject model (e.g., Geology, History)."""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    name = Column(String(200), nullable=False, index=True)  # e.g., "Geology"
    description = Column(Text)
    syllabus_url = Column(String(500))
    icon_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    exam = relationship("Exam", back_populates="subjects")
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}')>"


class Topic(Base):
    """Topic model (e.g., History of Andhra Pradesh)."""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String(300), nullable=False, index=True)  # e.g., "History of Andhra Pradesh"
    description = Column(Text)
    difficulty_level = Column(String(20), default="medium")  # easy, medium, hard
    estimated_study_mins = Column(Integer, default=60)
    icon_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}')>"
