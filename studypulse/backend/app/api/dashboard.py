"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.mock_test import MockTest, StudySession
from app.models.exam import Topic, Subject, Exam

router = APIRouter()


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_stars: int
    average_score: float
    study_streak: int
    total_study_hours: float
    tests_completed: int
    tests_passed: int


class RecentActivity(BaseModel):
    """Single activity item."""
    type: str  # "study" or "test"
    title: str
    score: Optional[float] = None
    star_earned: bool = False
    duration_mins: Optional[int] = None
    timestamp: datetime


class DashboardResponse(BaseModel):
    """Complete dashboard data."""
    stats: DashboardStats
    recent_activity: List[RecentActivity]
    continue_topic: Optional[dict] = None


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard data for current user."""
    user_id = current_user.id
    
    # Get total stars
    total_stars = current_user.total_stars
    
    # Get average score
    avg_query = select(func.avg(MockTest.score_percentage)).where(
        MockTest.user_id == user_id,
        MockTest.status == "completed"
    )
    avg_result = await db.execute(avg_query)
    average_score = avg_result.scalar() or 0
    
    # Get test counts
    tests_query = select(func.count(MockTest.id)).where(
        MockTest.user_id == user_id,
        MockTest.status == "completed"
    )
    tests_result = await db.execute(tests_query)
    tests_completed = tests_result.scalar() or 0
    
    passed_query = select(func.count(MockTest.id)).where(
        MockTest.user_id == user_id,
        MockTest.status == "completed",
        MockTest.score_percentage >= 70
    )
    passed_result = await db.execute(passed_query)
    tests_passed = passed_result.scalar() or 0
    
    # Calculate study streak (consecutive days with activity)
    streak = await calculate_study_streak(user_id, db)
    
    # Get total study hours
    hours_query = select(func.sum(StudySession.actual_duration_mins)).where(
        StudySession.user_id == user_id,
        StudySession.completed == True
    )
    hours_result = await db.execute(hours_query)
    total_mins = hours_result.scalar() or 0
    total_study_hours = round(total_mins / 60, 1)
    
    stats = DashboardStats(
        total_stars=total_stars,
        average_score=round(average_score, 1),
        study_streak=streak,
        total_study_hours=total_study_hours,
        tests_completed=tests_completed,
        tests_passed=tests_passed
    )
    
    # Get recent activity
    recent_activity = await get_recent_activity(user_id, db)
    
    # Get continue topic (last incomplete or most recent)
    continue_topic = await get_continue_topic(user_id, db)
    
    return DashboardResponse(
        stats=stats,
        recent_activity=recent_activity,
        continue_topic=continue_topic
    )


async def calculate_study_streak(user_id: int, db: AsyncSession) -> int:
    """Calculate consecutive days with study activity."""
    today = datetime.utcnow().date()
    streak = 0
    current_date = today
    
    for _ in range(365):  # Check up to a year back
        # Check if there's any activity on this date
        start = datetime.combine(current_date, datetime.min.time())
        end = datetime.combine(current_date, datetime.max.time())
        
        study_query = select(func.count(StudySession.id)).where(
            StudySession.user_id == user_id,
            StudySession.started_at >= start,
            StudySession.started_at <= end
        )
        
        test_query = select(func.count(MockTest.id)).where(
            MockTest.user_id == user_id,
            MockTest.started_at >= start,
            MockTest.started_at <= end
        )
        
        study_result = await db.execute(study_query)
        test_result = await db.execute(test_query)
        
        has_activity = (study_result.scalar() or 0) > 0 or (test_result.scalar() or 0) > 0
        
        if has_activity:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak


async def get_recent_activity(user_id: int, db: AsyncSession, limit: int = 10) -> List[RecentActivity]:
    """Get recent study sessions and tests."""
    activities = []
    
    # Get recent study sessions
    study_query = select(StudySession).where(
        StudySession.user_id == user_id,
        StudySession.completed == True
    ).order_by(desc(StudySession.ended_at)).limit(limit)
    
    study_result = await db.execute(study_query)
    sessions = study_result.scalars().all()
    
    for session in sessions:
        # Get topic name
        topic_query = select(Topic).where(Topic.id == session.topic_id)
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()
        
        activities.append(RecentActivity(
            type="study",
            title=f"Study Session - {topic.name if topic else 'Unknown'}",
            duration_mins=session.actual_duration_mins,
            timestamp=session.ended_at or session.started_at
        ))
    
    # Get recent tests
    test_query = select(MockTest).where(
        MockTest.user_id == user_id,
        MockTest.status == "completed"
    ).order_by(desc(MockTest.completed_at)).limit(limit)
    
    test_result = await db.execute(test_query)
    tests = test_result.scalars().all()
    
    for test in tests:
        # Get topic name
        topic_query = select(Topic).where(Topic.id == test.topic_id)
        topic_result = await db.execute(topic_query)
        topic = topic_result.scalar_one_or_none()
        
        activities.append(RecentActivity(
            type="test",
            title=f"Mock Test - {topic.name if topic else 'Unknown'}",
            score=test.score_percentage,
            star_earned=test.star_earned,
            timestamp=test.completed_at or test.started_at
        ))
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


async def get_continue_topic(user_id: int, db: AsyncSession) -> Optional[dict]:
    """Get the last studied topic for 'Continue Studying' feature."""
    # Get most recent study session
    query = select(StudySession).where(
        StudySession.user_id == user_id
    ).order_by(desc(StudySession.started_at)).limit(1)
    
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        return None
    
    # Get topic details
    topic_query = select(Topic).where(Topic.id == session.topic_id)
    topic_result = await db.execute(topic_query)
    topic = topic_result.scalar_one_or_none()
    
    if not topic:
        return None
    
    # Get subject name
    subject_query = select(Subject).where(Subject.id == topic.subject_id)
    subject_result = await db.execute(subject_query)
    subject = subject_result.scalar_one_or_none()
    
    # Calculate progress (simplified - based on tests taken)
    tests_query = select(func.count(MockTest.id)).where(
        MockTest.user_id == user_id,
        MockTest.topic_id == session.topic_id,
        MockTest.star_earned == True
    )
    tests_result = await db.execute(tests_query)
    stars_on_topic = tests_result.scalar() or 0
    
    # Assume 5 stars = 100% mastery
    progress = min(100, stars_on_topic * 20)
    
    return {
        "topic_id": topic.id,
        "topic_name": topic.name,
        "subject_name": subject.name if subject else "Unknown",
        "progress": progress,
        "session_completed": session.completed
    }


@router.get("/stats/weekly")
async def get_weekly_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly statistics for charts."""
    user_id = current_user.id
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    daily_stats = []
    
    for i in range(7):
        day = today - timedelta(days=6-i)
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        
        # Study minutes
        study_query = select(func.sum(StudySession.actual_duration_mins)).where(
            StudySession.user_id == user_id,
            StudySession.ended_at >= start,
            StudySession.ended_at <= end,
            StudySession.completed == True
        )
        study_result = await db.execute(study_query)
        study_mins = study_result.scalar() or 0
        
        # Tests taken
        tests_query = select(func.count(MockTest.id)).where(
            MockTest.user_id == user_id,
            MockTest.completed_at >= start,
            MockTest.completed_at <= end,
            MockTest.status == "completed"
        )
        tests_result = await db.execute(tests_query)
        tests_count = tests_result.scalar() or 0
        
        # Stars earned
        stars_query = select(func.count(MockTest.id)).where(
            MockTest.user_id == user_id,
            MockTest.completed_at >= start,
            MockTest.completed_at <= end,
            MockTest.star_earned == True
        )
        stars_result = await db.execute(stars_query)
        stars_count = stars_result.scalar() or 0
        
        daily_stats.append({
            "date": day.isoformat(),
            "day_name": day.strftime("%a"),
            "study_minutes": study_mins,
            "tests_completed": tests_count,
            "stars_earned": stars_count
        })
    
    return {"weekly_stats": daily_stats}
