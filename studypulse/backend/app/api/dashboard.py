"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.api.profile import calculate_study_streak  # Import optimized streak calculator
from app.models.user import User
from app.models.mock_test import MockTest
from app.models.mock_test import StudySession
from app.models.exam import Topic, Subject, Exam

router = APIRouter()


def get_greeting() -> str:
    """Get time-based greeting."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 22:
        return "Good Evening"
    else:
        return "Good Night"


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
    topic_name: str
    subject_name: str
    score: Optional[float] = None
    percentage: Optional[float] = None
    star_earned: bool = False
    duration_mins: Optional[int] = None
    timestamp: datetime


class DashboardResponse(BaseModel):
    """Complete dashboard data."""
    greeting: str
    user_name: str
    stats: dict
    performance_goal: dict
    recent_activity: List[RecentActivity]
    continue_topic: Optional[dict] = None


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard data for current user with greeting and stats."""
    user_id = current_user.id
    
    # Get greeting
    greeting = get_greeting()
    user_name = current_user.display_name or current_user.name.split()[0]
    
    # Get stats
    total_sessions = (await db.execute(
        select(func.count(StudySession.id)).where(StudySession.user_id == user_id)
    )).scalar() or 0
    
    total_tests = (await db.execute(
        select(func.count(MockTest.id)).where(
            and_(MockTest.user_id == user_id, MockTest.status == "completed")
        )
    )).scalar() or 0
    
    # Calculate study streak
    streak = await calculate_study_streak(user_id, db)
    
    stats = {
        "sessions": total_sessions,
        "tests": total_tests,
        "stars": current_user.total_stars,
        "study_streak": streak,
    }
    
    # Performance goal (fixed at 100%)
    avg_score = (await db.execute(
        select(func.avg(MockTest.score_percentage)).where(
            and_(MockTest.user_id == user_id, MockTest.status == "completed")
        )
    )).scalar() or 0.0
    
    performance_goal = {
        "target": 100.0,
        "current": round(avg_score, 1),
        "percentage": int((avg_score / 100.0) * 100) if avg_score else 0,
    }
    
    # Get recent activity (last 3 tests with topic, percentage, star)
    recent_activity = await get_recent_activity(user_id, db)
    
    # Get continue topic
    continue_topic = await get_continue_topic(user_id, db)
    
    return DashboardResponse(
        greeting=greeting,
        user_name=user_name,
        stats=stats,
        performance_goal=performance_goal,
        recent_activity=recent_activity,
        continue_topic=continue_topic
    )


# calculate_study_streak is now imported from profile.py (optimized version)


async def get_recent_activity(user_id: int, db: AsyncSession, limit: int = 10) -> List[RecentActivity]:
    """Get recent study sessions and tests - deduplicated by topic.
    
    Only shows the most recent activity per topic to avoid duplicates.
    Prioritizes tests over study sessions for the same topic.
    """
    activities = []
    seen_topics = set()
    
    # Get recent tests first (prioritize tests over study sessions)
    test_query = select(MockTest).where(
        MockTest.user_id == user_id,
        MockTest.status == "completed"
    ).order_by(desc(MockTest.completed_at)).limit(limit * 2)
    
    test_result = await db.execute(test_query)
    tests = test_result.scalars().all()
    
    for test in tests:
        if test.topic_id in seen_topics:
            continue
            
        topic_query = select(Topic, Subject).join(Subject, Topic.subject_id == Subject.id).where(Topic.id == test.topic_id)
        topic_result = await db.execute(topic_query)
        row = topic_result.first()
        topic_name = row[0].name if row else "Unknown"
        subject_name = row[1].name if row else "Unknown"

        activities.append(RecentActivity(
            type="test",
            topic_name=topic_name,
            subject_name=subject_name,
            score=test.score_percentage,
            percentage=test.score_percentage,
            star_earned=test.star_earned,
            timestamp=test.completed_at or test.started_at
        ))
        seen_topics.add(test.topic_id)
        
        if len(activities) >= limit:
            break
    
    # Only get study sessions if we haven't filled the limit
    if len(activities) < limit:
        study_query = select(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.completed == True
        ).order_by(desc(StudySession.ended_at)).limit(limit * 2)
        
        study_result = await db.execute(study_query)
        sessions = study_result.scalars().all()
        
        for session in sessions:
            # Skip if we already have this topic
            if session.topic_id in seen_topics:
                continue
            
            topic_query = select(Topic, Subject).join(Subject, Topic.subject_id == Subject.id).where(Topic.id == session.topic_id)
            topic_result = await db.execute(topic_query)
            row = topic_result.first()
            topic_name = row[0].name if row else "Unknown"
            subject_name = row[1].name if row else "Unknown"

            activities.append(RecentActivity(
                type="study",
                topic_name=topic_name,
                subject_name=subject_name,
                duration_mins=session.actual_duration_mins,
                timestamp=session.ended_at or session.started_at
            ))
            seen_topics.add(session.topic_id)
            
            if len(activities) >= limit:
                break
    
    # Sort by timestamp
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


async def get_continue_topic(user_id: int, db: AsyncSession) -> Optional[dict]:
    """Get the last studied topic for 'Continue Studying' feature.
    
    Only returns a continue topic if there's an INCOMPLETE session.
    Completed sessions should not show 'Resume' - user needs to start fresh.
    """
    # Get most recent INCOMPLETE study session only
    query = select(StudySession).where(
        StudySession.user_id == user_id,
        StudySession.completed == False
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
