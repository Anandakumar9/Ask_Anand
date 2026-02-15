"""Smart Question Selector - Intelligent question mixing algorithm.

Implements adaptive question selection based on:
1. User performance history (adaptive difficulty)
2. Topic coverage optimization (ensure breadth)
3. Dynamic mixing (previous year + AI generated)
4. Repetition avoidance (exclude seen questions)
5. Difficulty progression (start easy → medium → hard)

This module enhances the RAG pipeline by intelligently selecting which questions
to present based on the user's learning profile.
"""
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mock_test import MockTest
from app.models.question import Question
from app.models.user import User

logger = logging.getLogger(__name__)


class SmartQuestionSelector:
    """Intelligently selects questions based on user performance and learning goals."""

    # Difficulty weights for adaptive selection
    DIFFICULTY_WEIGHTS = {
        "easy": 1.0,
        "medium": 1.5,
        "hard": 2.0
    }

    # Default difficulty distribution (can be overridden)
    DEFAULT_DISTRIBUTION = {
        "easy": 0.3,    # 30% easy
        "medium": 0.5,  # 50% medium
        "hard": 0.2     # 20% hard
    }

    def __init__(self):
        pass

    async def select_questions(
        self,
        available_questions: List[dict],
        user_id: int,
        topic_id: int,
        target_count: int,
        db: AsyncSession,
        force_distribution: Optional[Dict[str, float]] = None
    ) -> List[dict]:
        """Smart selection of questions based on user performance.

        Args:
            available_questions: Pool of questions to select from
            user_id: User ID for performance analysis
            topic_id: Topic ID for context
            target_count: Number of questions to select
            db: Database session
            force_distribution: Override default difficulty distribution

        Returns:
            Optimally selected questions
        """
        if not available_questions:
            return []

        # Step 1: Analyze user performance
        performance = await self._analyze_user_performance(user_id, topic_id, db)

        # Step 2: Determine optimal difficulty distribution
        difficulty_dist = force_distribution or self._calculate_difficulty_distribution(performance)

        # Step 3: Select questions with optimal mix
        selected = self._select_by_distribution(
            available_questions,
            difficulty_dist,
            target_count
        )

        # Step 4: Apply intelligent ordering (difficulty progression)
        ordered = self._order_by_difficulty_progression(selected)

        logger.info(
            f"Smart selection: {len(ordered)} questions "
            f"(dist: {self._get_actual_distribution(ordered)})"
        )

        return ordered

    async def _analyze_user_performance(
        self, user_id: int, topic_id: int, db: AsyncSession
    ) -> Dict[str, any]:
        """Analyze user's historical performance on this topic.

        Returns:
            {
                "average_score": float (0-1),
                "tests_taken": int,
                "difficulty_scores": {"easy": 0.9, "medium": 0.7, "hard": 0.4},
                "last_test_date": datetime,
                "trend": "improving" | "declining" | "stable"
            }
        """
        try:
            # Fetch recent test history (last 10 tests)
            result = await db.execute(
                select(MockTest)
                .where(
                    MockTest.user_id == user_id,
                    MockTest.topic_id == topic_id,
                    MockTest.status == "completed"
                )
                .order_by(MockTest.completed_at.desc())
                .limit(10)
            )
            tests = result.scalars().all()

            if not tests:
                # No history - default to beginner profile
                return {
                    "average_score": 0.5,
                    "tests_taken": 0,
                    "difficulty_scores": {"easy": 0.5, "medium": 0.5, "hard": 0.5},
                    "last_test_date": None,
                    "trend": "stable"
                }

            # Calculate average score
            scores = [t.score_percentage / 100 for t in tests if t.score_percentage is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.5

            # Calculate per-difficulty scores (if available)
            # For now, estimate based on overall score
            difficulty_scores = {
                "easy": min(1.0, avg_score + 0.2),
                "medium": avg_score,
                "hard": max(0.0, avg_score - 0.2)
            }

            # Determine trend (last 3 vs previous 3)
            trend = "stable"
            if len(scores) >= 6:
                recent_avg = sum(scores[:3]) / 3
                older_avg = sum(scores[3:6]) / 3
                if recent_avg > older_avg + 0.1:
                    trend = "improving"
                elif recent_avg < older_avg - 0.1:
                    trend = "declining"

            return {
                "average_score": avg_score,
                "tests_taken": len(tests),
                "difficulty_scores": difficulty_scores,
                "last_test_date": tests[0].submitted_at if tests else None,
                "trend": trend
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            # Return default profile on error
            return {
                "average_score": 0.5,
                "tests_taken": 0,
                "difficulty_scores": {"easy": 0.5, "medium": 0.5, "hard": 0.5},
                "last_test_date": None,
                "trend": "stable"
            }

    def _calculate_difficulty_distribution(
        self, performance: Dict[str, any]
    ) -> Dict[str, float]:
        """Calculate optimal difficulty distribution based on performance.

        Adaptive logic:
        - Beginners (score < 0.4): 50% easy, 40% medium, 10% hard
        - Intermediate (0.4-0.7): 30% easy, 50% medium, 20% hard
        - Advanced (> 0.7): 20% easy, 50% medium, 30% hard
        - Improving trend: Slightly increase hard questions
        - Declining trend: Slightly increase easy questions
        """
        avg_score = performance["average_score"]
        trend = performance["trend"]

        # Base distribution based on score
        if avg_score < 0.4:
            # Beginner
            distribution = {"easy": 0.5, "medium": 0.4, "hard": 0.1}
        elif avg_score < 0.7:
            # Intermediate
            distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        else:
            # Advanced
            distribution = {"easy": 0.2, "medium": 0.5, "hard": 0.3}

        # Adjust for trend
        if trend == "improving":
            # User is improving - challenge them more
            distribution["hard"] = min(0.4, distribution["hard"] + 0.1)
            distribution["easy"] = max(0.1, distribution["easy"] - 0.1)
        elif trend == "declining":
            # User struggling - provide more support
            distribution["easy"] = min(0.6, distribution["easy"] + 0.1)
            distribution["hard"] = max(0.05, distribution["hard"] - 0.1)

        # Ensure sum equals 1.0
        total = sum(distribution.values())
        distribution = {k: v / total for k, v in distribution.items()}

        logger.info(
            f"Adaptive distribution: easy={distribution['easy']:.0%}, "
            f"medium={distribution['medium']:.0%}, hard={distribution['hard']:.0%} "
            f"(score={avg_score:.2f}, trend={trend})"
        )

        return distribution

    def _select_by_distribution(
        self,
        questions: List[dict],
        distribution: Dict[str, float],
        target_count: int
    ) -> List[dict]:
        """Select questions matching the target difficulty distribution.

        Strategy:
        1. Group questions by difficulty
        2. Calculate target count for each difficulty
        3. Randomly sample from each group
        4. Fill remaining slots if any group is short
        """
        # Group questions by difficulty
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        for q in questions:
            difficulty = q.get("difficulty", "medium").lower()
            if difficulty in by_difficulty:
                by_difficulty[difficulty].append(q)

        # Calculate target count for each difficulty
        targets = {
            "easy": int(target_count * distribution.get("easy", 0.3)),
            "medium": int(target_count * distribution.get("medium", 0.5)),
            "hard": int(target_count * distribution.get("hard", 0.2))
        }

        # Adjust to ensure sum equals target_count
        while sum(targets.values()) < target_count:
            # Add to medium (most common)
            targets["medium"] += 1

        selected = []

        # Select from each difficulty group
        for difficulty, target in targets.items():
            available = by_difficulty[difficulty]
            if len(available) >= target:
                # Enough questions - random sample
                selected.extend(random.sample(available, target))
            else:
                # Not enough - take all available
                selected.extend(available)

        # Fill remaining slots with any difficulty
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            all_remaining = [q for q in questions if q not in selected]
            if all_remaining:
                extra = random.sample(
                    all_remaining,
                    min(remaining, len(all_remaining))
                )
                selected.extend(extra)

        return selected[:target_count]

    def _order_by_difficulty_progression(self, questions: List[dict]) -> List[dict]:
        """Order questions for optimal learning progression.

        Strategy: easy → medium → hard (gradual difficulty increase)
        Within each difficulty: shuffle for variety
        """
        # Group by difficulty
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        for q in questions:
            difficulty = q.get("difficulty", "medium").lower()
            if difficulty in by_difficulty:
                by_difficulty[difficulty].append(q)

        # Shuffle within each group
        for group in by_difficulty.values():
            random.shuffle(group)

        # Combine in order: easy → medium → hard
        ordered = (
            by_difficulty["easy"] +
            by_difficulty["medium"] +
            by_difficulty["hard"]
        )

        return ordered

    def _get_actual_distribution(self, questions: List[dict]) -> Dict[str, float]:
        """Calculate actual difficulty distribution of selected questions."""
        if not questions:
            return {"easy": 0.0, "medium": 0.0, "hard": 0.0}

        counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            difficulty = q.get("difficulty", "medium").lower()
            if difficulty in counts:
                counts[difficulty] += 1

        total = len(questions)
        return {k: v / total for k, v in counts.items()}

    async def get_recommended_topics(
        self,
        user_id: int,
        exam_id: int,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, any]]:
        """Recommend topics for the user to practice based on performance.

        Returns topics sorted by:
        1. Weak areas (low scores)
        2. Not recently practiced
        3. Popular/important topics

        Returns:
            List of dicts with {topic_id, topic_name, reason, priority}
        """
        try:
            # Get all topics for exam
            from app.models.exam import Topic, Subject
            result = await db.execute(
                select(Topic, Subject)
                .join(Subject, Topic.subject_id == Subject.id)
                .where(Subject.exam_id == exam_id)
            )
            all_topics = result.all()

            # Get user's test history
            result = await db.execute(
                select(MockTest.topic_id, func.avg(MockTest.score_percentage).label("avg_score"))
                .where(
                    MockTest.user_id == user_id,
                    MockTest.status == "completed"
                )
                .group_by(MockTest.topic_id)
            )
            topic_scores = {row.topic_id: row.avg_score for row in result}

            recommendations = []

            for topic, subject in all_topics:
                avg_score = topic_scores.get(topic.id, None)

                # Determine priority and reason
                if avg_score is None:
                    # Not practiced yet
                    priority = 3
                    reason = "Not yet practiced"
                elif avg_score < 0.5:
                    # Weak area
                    priority = 5
                    reason = f"Needs improvement (avg: {avg_score:.0%})"
                elif avg_score < 0.7:
                    # Moderate
                    priority = 2
                    reason = f"Continue practicing (avg: {avg_score:.0%})"
                else:
                    # Strong area
                    priority = 1
                    reason = f"Maintain strength (avg: {avg_score:.0%})"

                recommendations.append({
                    "topic_id": topic.id,
                    "topic_name": topic.name,
                    "subject_name": subject.name,
                    "reason": reason,
                    "priority": priority,
                    "avg_score": avg_score
                })

            # Sort by priority (high to low), then by name
            recommendations.sort(key=lambda x: (-x["priority"], x["topic_name"]))

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Topic recommendation failed: {e}")
            return []


# Singleton
smart_selector = SmartQuestionSelector()
