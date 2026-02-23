"""Profile API - user stats, streak, proficiency, and updates."""
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func, and_, distinct, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache
from app.models.exam import Subject, Topic
from app.models.mock_test import MockTest
from app.models.mock_test import StudySession
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfileUpdate(BaseModel):
    """Profile update request."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


async def calculate_study_streak(user_id: int, db: AsyncSession) -> int:
    """Calculate consecutive days with study activity (sessions or tests)."""
    try:
        # Get all activity timestamps (study sessions + mock tests)
        session_times = (await db.execute(
            select(StudySession.started_at)
            .where(StudySession.user_id == user_id)
        )).scalars().all()

        test_times = (await db.execute(
            select(MockTest.started_at)
            .where(MockTest.user_id == user_id)
        )).scalars().all()

        # Convert datetime to date objects
        def to_date(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                # Parse ISO format string
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            if isinstance(dt, datetime):
                return dt.date()
            return dt

        # Get unique dates
        all_dates = set()
        for dt in session_times:
            d = to_date(dt)
            if d:
                all_dates.add(d)
        for dt in test_times:
            d = to_date(dt)
            if d:
                all_dates.add(d)

        if not all_dates:
            return 0

        # Sort dates in descending order
        all_dates = sorted(all_dates, reverse=True)

        # Count consecutive days from today backwards
        today = date.today()
        streak = 0

        # Check if there's activity today or yesterday (ongoing streak)
        if all_dates[0] not in (today, today - timedelta(days=1)):
            return 0

        # Count backwards from most recent activity
        current_date = all_dates[0]
        for activity_date in all_dates:
            if activity_date == current_date:
                streak += 1
                current_date = current_date - timedelta(days=1)
            else:
                # Gap found, streak broken
                break

        return streak

    except Exception as e:
        logger.error(f"Streak calculation error: {e}", exc_info=True)
        return 0


@router.get("/stats")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive profile statistics.

    Returns nested structure:
    - basic_info: username, email, display_name, avatar, join date
    - activity_stats: total sessions, total tests, stars, average_score
    - study_streak: consecutive days with activity
    - subject_proficiency: Map of subject_name -> {average_score, test_count}
    - performance_goal: overall accuracy target vs current
    - recent_performance: last 10 completed tests with scores and dates
    - best_performance: highest scoring test ever
    - improvement_trend: comparison of last 5 tests vs previous 5 tests
    """

    # Check cache first
    cached = cache.get_profile_stats(current_user.id)
    if cached:
        return cached

    try:
        # --- Basic Info ---
        basic_info = {
            "id": current_user.id,
            "username": current_user.name,
            "display_name": current_user.display_name or current_user.name.split()[0] if current_user.name else "User",
            "email": current_user.email,
            "avatar_url": current_user.avatar_url,
            "join_date": current_user.created_at.isoformat() if current_user.created_at else None,
        }

        # --- Activity Stats (using computed properties) ---
        total_sessions = await current_user.get_total_sessions(db)
        total_tests = await current_user.get_total_tests(db)

        # --- Study Streak (REAL calculation) ---
        streak = await calculate_study_streak(current_user.id, db)

        # --- Subject Proficiency (REAL data from user's test results) ---
        # Group tests by subject and calculate average score
        subject_stats_query = (
            select(
                Subject.id,
                Subject.name,
                func.avg(MockTest.score_percentage).label("avg_score"),
                func.count(MockTest.id).label("test_count")
            )
            .join(Topic, Topic.subject_id == Subject.id)
            .join(MockTest, MockTest.topic_id == Topic.id)
            .where(
                and_(
                    MockTest.user_id == current_user.id,
                    MockTest.status == "completed"
                )
            )
            .group_by(Subject.id, Subject.name)
            .order_by(func.avg(MockTest.score_percentage).desc())
        )

        subject_results = (await db.execute(subject_stats_query)).all()

        # Convert to Map/Object structure that Flutter expects
        subject_proficiency = {
            row.name: {
                "average_score": round(row.avg_score, 1) if row.avg_score else 0.0,
                "test_count": row.test_count
            }
            for row in subject_results
        }

        # Calculate overall average score for activity stats
        avg_score = (await db.execute(
            select(func.avg(MockTest.score_percentage))
            .where(and_(
                MockTest.user_id == current_user.id,
                MockTest.status == "completed"
            ))
        )).scalar() or 0.0

        activity_stats = {
            "total_sessions": total_sessions,
            "total_tests": total_tests,
            "total_stars": current_user.total_stars or 0,
            "average_score": round(avg_score, 1)
        }

        # Build the profile response structure that Flutter expects
        profile = {
            "basic_info": basic_info,
            "activity_stats": activity_stats,
            "study_streak": streak,
            "subject_proficiency": subject_proficiency,
            "performance_goal": {
                "target": 100.0,
                "current": round(avg_score, 1)
            }
        }

        # --- Recent Performance (Last 10 tests, deduplicated by topic) ---
        recent_tests_query = (
            select(MockTest)
            .where(
                and_(
                    MockTest.user_id == current_user.id,
                    MockTest.status == "completed"
                )
            )
            .order_by(MockTest.completed_at.desc())
            .limit(20)  # Get more to allow for deduplication
        )

        recent_tests = (await db.execute(recent_tests_query)).scalars().all()
        
        # Deduplicate by topic_id - only keep the most recent test per topic
        seen_topics = set()
        deduped_tests = []
        for test in recent_tests:
            if test.topic_id not in seen_topics:
                seen_topics.add(test.topic_id)
                deduped_tests.append(test)
            if len(deduped_tests) >= 4:  # Limit to 4 unique topics
                break

        # Get topic names for the tests - single query to avoid N+1 problem
        topic_ids = [t.topic_id for t in deduped_tests if t.topic_id]
        topics_map = {}
        if topic_ids:
            topics_result = await db.execute(select(Topic).where(Topic.id.in_(topic_ids)))
            topics_map = {t.id: t.name for t in topics_result.scalars().all()}
        
        recent_performance = []
        for test in deduped_tests:
            topic_name = topics_map.get(test.topic_id, "Unknown") if test.topic_id else "Unknown"
            
            recent_performance.append({
                "test_id": test.id,
                "topic_id": test.topic_id,
                "topic_name": topic_name,
                "score": round(test.score_percentage, 1),
                "total_questions": test.total_questions,
                "correct_answers": test.correct_answers,
                "date": test.completed_at.isoformat() if test.completed_at else test.started_at.isoformat(),
                "star_earned": test.star_earned
            })
        
        profile["recent_performance"] = recent_performance

        # --- Best Performance (Highest scoring test) ---
        best_test_query = (
            select(MockTest)
            .where(
                and_(
                    MockTest.user_id == current_user.id,
                    MockTest.status == "completed"
                )
            )
            .order_by(MockTest.score_percentage.desc())
            .limit(1)
        )

        best_test = (await db.execute(best_test_query)).scalar_one_or_none()

        if best_test:
            profile["best_performance"] = {
                "test_id": best_test.id,
                "score": round(best_test.score_percentage, 1),
                "total_questions": best_test.total_questions,
                "correct_answers": best_test.correct_answers,
                "date": best_test.completed_at.isoformat() if best_test.completed_at else best_test.started_at.isoformat(),
                "star_earned": best_test.star_earned
            }
        else:
            profile["best_performance"] = None

        # --- Improvement Trend (Last 5 tests vs Previous 5 tests) ---
        # Get last 10 tests to compare trends
        trend_tests_query = (
            select(MockTest.score_percentage)
            .where(
                and_(
                    MockTest.user_id == current_user.id,
                    MockTest.status == "completed"
                )
            )
            .order_by(MockTest.completed_at.desc())
            .limit(10)
        )

        trend_scores = (await db.execute(trend_tests_query)).scalars().all()

        if len(trend_scores) >= 10:
            # Have enough data for comparison
            last_5_avg = sum(trend_scores[:5]) / 5
            previous_5_avg = sum(trend_scores[5:10]) / 5
            improvement = last_5_avg - previous_5_avg

            profile["improvement_trend"] = {
                "last_5_average": round(last_5_avg, 1),
                "previous_5_average": round(previous_5_avg, 1),
                "improvement": round(improvement, 1),
                "trending": "up" if improvement > 0 else "down" if improvement < 0 else "stable"
            }
        elif len(trend_scores) >= 5:
            # Only have recent 5 tests
            last_5_avg = sum(trend_scores[:5]) / 5
            profile["improvement_trend"] = {
                "last_5_average": round(last_5_avg, 1),
                "previous_5_average": None,
                "improvement": None,
                "trending": "insufficient_data"
            }
        else:
            # Not enough tests for trend analysis
            profile["improvement_trend"] = {
                "last_5_average": None,
                "previous_5_average": None,
                "improvement": None,
                "trending": "insufficient_data"
            }

        # Cache the profile stats for 5 minutes
        await cache.cache_profile_stats(current_user.id, profile)

        return profile

    except Exception as e:
        logger.error(f"Profile stats error: {e}", exc_info=True)
        # Return minimal profile on error with nested structure
        return {
            "basic_info": {
                "id": current_user.id,
                "username": current_user.name or "User",
                "display_name": current_user.name.split()[0] if current_user.name else "User",
                "email": current_user.email,
                "avatar_url": None,
                "join_date": None,
            },
            "activity_stats": {
                "total_sessions": 0,
                "total_tests": 0,
                "total_stars": 0,
                "average_score": 0.0
            },
            "study_streak": 0,
            "subject_proficiency": {},
            "performance_goal": {"target": 100.0, "current": 0.0},
            "recent_performance": [],
            "best_performance": None,
            "improvement_trend": {
                "last_5_average": None,
                "previous_5_average": None,
                "improvement": None,
                "trending": "insufficient_data"
            }
        }


@router.put("/update")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile (display name and avatar)."""

    if profile_data.display_name is not None:
        if len(profile_data.display_name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Display name must be at least 2 characters"
            )
        current_user.display_name = profile_data.display_name.strip()

    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url.strip()

    current_user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(current_user)

    # Invalidate profile cache
    cache.invalidate_profile_stats(current_user.id)

    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "display_name": current_user.display_name,
            "avatar_url": current_user.avatar_url,
        }
    }


@router.post("/first-login-complete")
async def complete_first_login(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark first login as complete (hide welcome screen next time)."""
    current_user.is_first_login = False
    await db.commit()

    return {"success": True, "is_first_login": False}
