"""Leaderboard API - simplified and working with demo data."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_leaderboard(
    exam_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get global leaderboard - ranked by stars (primary) and avg score (secondary)."""
    try:
        from sqlalchemy import func, case
        from app.models.mock_test import MockTest

        # Build query to get users with their stats
        # Calculate average score and test count from mock_tests
        avg_score = func.avg(
            case((MockTest.status == "completed", MockTest.score_percentage), else_=None)
        ).label("avg_score")

        test_count = func.count(
            case((MockTest.status == "completed", MockTest.id), else_=None)
        ).label("test_count")

        # Query users with aggregated stats
        query = (
            select(
                User,
                func.coalesce(avg_score, 0.0).label("avg_score"),
                test_count
            )
            .outerjoin(MockTest, User.id == MockTest.user_id)
            .group_by(User.id)
            .order_by(
                desc(User.total_stars),  # Primary: most stars
                desc(func.coalesce(avg_score, 0.0))  # Secondary: highest avg score
            )
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        leaderboard = []
        for rank, (user, avg_score_val, test_count_val) in enumerate(rows, start=1):
            name = user.name if user.name else f"User{user.id}"
            username = name.split()[0] if " " in name else name

            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "username": username,
                "avatar_url": user.avatar_url or "",
                "accuracy": round(avg_score_val or 0.0, 1),
                "stars": user.total_stars if user.total_stars else 0,
                "test_count": test_count_val or 0,
            })

        # If no users, return empty leaderboard with clear message
        if not leaderboard:
            return {
                "exam_id": exam_id,
                "leaderboard": [],
                "your_rank": None,
                "message": "No users on leaderboard yet. Be the first!",
                "is_empty": True
            }

        # Find current user
        your_rank = None
        for item in leaderboard:
            if item["user_id"] == current_user.id:
                your_rank = item["rank"]
                break

        return {
            "exam_id": exam_id,
            "leaderboard": leaderboard,
            "your_rank": your_rank if your_rank else len(leaderboard) + 1,
            "total_users": len(leaderboard),
        }
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return {
            "exam_id": exam_id,
            "leaderboard": [],
            "your_rank": None,
            "total_users": 0,
        }


@router.get("/exams")
async def get_exam_leaderboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of exams with leaderboards."""
    # Demo data for testing
    return {
        "exams": [
            {"id": 1, "name": "UPSC Civil Services", "total_users": 1234},
            {"id": 2, "name": "SSC CGL", "total_users": 5678},
            {"id": 3, "name": "Banking (IBPS)", "total_users": 3456},
        ]
    }
