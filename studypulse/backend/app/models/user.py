"""User model for authentication and profile."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, select, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func as sql_func
from app.core.database import Base


class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)  # Editable display name
    hashed_password = Column(String(255), nullable=False)
    profile_pic = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)  # User-selectable avatar
    target_exam_id = Column(Integer, nullable=True)
    total_stars = Column(Integer, default=0)
    # total_sessions and total_tests removed - now computed via count queries
    is_active = Column(Boolean, default=True)
    is_first_login = Column(Boolean, default=True)  # Track first-time users
    created_at = Column(DateTime(timezone=True), server_default=sql_func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

    # Relationships
    study_sessions = relationship("StudySession", back_populates="user")
    mock_tests = relationship("MockTest", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

    async def get_total_sessions(self, db) -> int:
        """Computed property: count all study sessions."""
        from app.models.mock_test import StudySession
        result = await db.execute(
            select(sql_func.count(StudySession.id)).where(StudySession.user_id == self.id)
        )
        return result.scalar() or 0

    async def get_total_tests(self, db) -> int:
        """Computed property: count all completed tests."""
        from app.models.mock_test import MockTest
        result = await db.execute(
            select(sql_func.count(MockTest.id)).where(
                MockTest.user_id == self.id,
                MockTest.status == "completed"
            )
        )
        return result.scalar() or 0
