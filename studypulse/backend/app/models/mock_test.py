"""StudySession, MockTest, and QuestionResponse models."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StudySession(Base):
    """Tracks user study sessions."""
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    duration_mins = Column(Integer, nullable=False)  # Planned duration
    actual_duration_mins = Column(Integer, nullable=True)  # Actual time spent
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)  # Optional user notes
    
    # Relationships
    user = relationship("User", back_populates="study_sessions")
    mock_test = relationship("MockTest", back_populates="study_session", uselist=False)
    
    def __repr__(self):
        return f"<StudySession(id={self.id}, user_id={self.user_id}, topic_id={self.topic_id})>"


class MockTest(Base):
    """Tracks mock test attempts."""
    __tablename__ = "mock_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    star_earned = Column(Boolean, default=False)
    time_limit_seconds = Column(Integer)  # Allowed time
    time_taken_seconds = Column(Integer, nullable=True)  # Actual time taken
    question_ids = Column(JSON)  # List of question IDs used in this test
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mock_tests")
    study_session = relationship("StudySession", back_populates="mock_test")
    responses = relationship("QuestionResponse", back_populates="mock_test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MockTest(id={self.id}, score={self.score_percentage}%, star={self.star_earned})>"


class QuestionResponse(Base):
    """Tracks individual question responses in a mock test."""
    __tablename__ = "question_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    mock_test_id = Column(Integer, ForeignKey("mock_tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String(1), nullable=True)  # "A", "B", "C", "D", or null (unanswered)
    is_correct = Column(Boolean, nullable=True)
    is_marked_for_review = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    mock_test = relationship("MockTest", back_populates="responses")
    
    def __repr__(self):
        return f"<QuestionResponse(question_id={self.question_id}, answer='{self.user_answer}', correct={self.is_correct})>"
