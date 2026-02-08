"""User model for authentication and profile."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    profile_pic = Column(String(500), nullable=True)
    target_exam_id = Column(Integer, nullable=True)
    total_stars = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    study_sessions = relationship("StudySession", back_populates="user")
    mock_tests = relationship("MockTest", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
