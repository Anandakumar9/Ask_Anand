"""Service for importing questions from various sources (CSV, manual entry, etc.)."""
import csv
import io
import logging
from typing import List, Dict, Optional, Union, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.exam import Topic
from app.schemas.question_import import QuestionImport, ImportResponse

logger = logging.getLogger(__name__)


class QuestionImporter:
    """Handles question import operations from various sources.
    
    Supports:
    - Text-only questions
    - Questions with images (question_images, explanation_images)
    - Questions with option images (stored in options JSON)
    - Audio/video explanations
    """

    def _normalize_options(self, options: Dict[str, Union[str, Dict, Any]]) -> Dict[str, Any]:
        """Normalize options to a consistent format.
        
        Handles both:
        - Simple text: {"A": "text", "B": "text", ...}
        - With images: {"A": {"text": "text", "image": "url"}, ...}
        
        Returns a consistent dict format for database storage.
        """
        normalized = {}
        for key, value in options.items():
            if isinstance(value, str):
                # Simple text option
                normalized[key] = value
            elif isinstance(value, dict):
                # Option with potential image
                normalized[key] = {
                    "text": value.get("text", ""),
                    "image": value.get("image") if value.get("image") else None
                }
            elif hasattr(value, 'text'):
                # OptionData object
                normalized[key] = {
                    "text": value.text,
                    "image": value.image if hasattr(value, 'image') else None
                }
            else:
                normalized[key] = str(value)
        
        return normalized

    async def import_single(
        self, question: QuestionImport, db: AsyncSession
    ) -> tuple[bool, Optional[int], str]:
        """Import a single question with image support.

        Returns: (success: bool, question_id: Optional[int], error: str)
        """
        try:
            # Verify topic exists
            topic = await db.scalar(select(Topic).where(Topic.id == question.topic_id))
            if not topic:
                return False, None, f"Topic ID {question.topic_id} not found"

            # Normalize options to handle both text and image-enhanced formats
            normalized_options = self._normalize_options(question.options)

            # Create question with image support
            db_question = Question(
                topic_id=question.topic_id,
                question_text=question.question_text.strip(),
                options=normalized_options,
                correct_answer=question.correct_answer.upper(),
                explanation=question.explanation.strip() if question.explanation else None,
                source=question.source,
                year=question.year,
                difficulty=question.difficulty,
                # Image support fields
                question_images=question.question_images or [],
                explanation_images=question.explanation_images or [],
                audio_url=question.audio_url,
                video_url=question.video_url,
                # Validation
                is_validated=False,  # Manually imported questions need validation
                is_active=True,
            )

            db.add(db_question)
            await db.flush()
            await db.commit()
            await db.refresh(db_question)

            logger.info(f"Imported question ID {db_question.id} for topic {question.topic_id}")
            return True, db_question.id, ""

        except Exception as e:
            await db.rollback()
            error_msg = f"Failed to import question: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    async def import_bulk(
        self, questions: List[QuestionImport], db: AsyncSession
    ) -> ImportResponse:
        """Import multiple questions in a single transaction.

        Returns: ImportResponse with success stats
        """
        imported_ids: List[int] = []
        errors: List[str] = []
        failed_count = 0

        for idx, question in enumerate(questions, start=1):
            success, question_id, error = await self.import_single(question, db)

            if success and question_id:
                imported_ids.append(question_id)
            else:
                failed_count += 1
                errors.append(f"Row {idx}: {error}")

        return ImportResponse(
            success=failed_count == 0,
            imported_count=len(imported_ids),
            failed_count=failed_count,
            errors=errors,
            question_ids=imported_ids,
        )

    async def import_from_csv(
        self,
        csv_data: str,
        topic_id: int,
        source: str,
        skip_header: bool,
        db: AsyncSession,
    ) -> ImportResponse:
        """Import questions from CSV data.

        Expected CSV format:
        question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, difficulty, year

        Example row:
        "What is the capital of India?", "Mumbai", "Delhi", "Kolkata", "Chennai", "B", "Delhi is the capital.", "easy", 2023
        """
        try:
            # Parse CSV
            reader = csv.reader(io.StringIO(csv_data.strip()))
            if skip_header:
                next(reader)  # Skip header row

            questions: List[QuestionImport] = []
            errors: List[str] = []

            for row_num, row in enumerate(reader, start=1 if not skip_header else 2):
                try:
                    if len(row) < 6:  # Minimum: question + 4 options + answer
                        errors.append(f"Row {row_num}: Insufficient columns (need at least 6)")
                        continue

                    # Parse row
                    question_text = row[0].strip()
                    option_a = row[1].strip()
                    option_b = row[2].strip()
                    option_c = row[3].strip()
                    option_d = row[4].strip()
                    correct_answer = row[5].strip().upper()

                    # Optional fields
                    explanation = row[6].strip() if len(row) > 6 else None
                    difficulty = row[7].strip().lower() if len(row) > 7 else "medium"
                    year = int(row[8].strip()) if len(row) > 8 and row[8].strip() else None

                    # Validate correct_answer
                    if correct_answer not in ["A", "B", "C", "D"]:
                        errors.append(
                            f"Row {row_num}: Invalid correct_answer '{correct_answer}' (must be A, B, C, or D)"
                        )
                        continue

                    # Create question object
                    question = QuestionImport(
                        topic_id=topic_id,
                        question_text=question_text,
                        options={"A": option_a, "B": option_b, "C": option_c, "D": option_d},
                        correct_answer=correct_answer,
                        explanation=explanation,
                        source=source,
                        year=year,
                        difficulty=difficulty,
                    )
                    questions.append(question)

                except ValueError as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")

            # Import valid questions
            if questions:
                result = await self.import_bulk(questions, db)
                result.errors = errors + result.errors  # Combine parsing + import errors
                result.failed_count += len(errors)
                return result
            else:
                return ImportResponse(
                    success=False,
                    imported_count=0,
                    failed_count=len(errors),
                    errors=errors,
                    question_ids=[],
                )

        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            return ImportResponse(
                success=False,
                imported_count=0,
                failed_count=1,
                errors=[f"CSV parsing failed: {str(e)}"],
                question_ids=[],
            )

    async def validate_topic_exists(self, topic_id: int, db: AsyncSession) -> bool:
        """Check if a topic exists."""
        topic = await db.scalar(select(Topic).where(Topic.id == topic_id))
        return topic is not None

    async def get_import_stats(self, topic_id: int, db: AsyncSession) -> Dict[str, int]:
        """Get import statistics for a topic."""
        from sqlalchemy import func, Integer

        result = await db.execute(
            select(
                func.count(Question.id).label("total"),
                func.sum(func.cast(Question.source == "MANUAL", Integer)).label("manual"),
                func.sum(func.cast(Question.source == "CSV", Integer)).label("csv"),
                func.sum(func.cast(Question.source == "PDF", Integer)).label("pdf"),
                func.sum(func.cast(Question.source == "WEB", Integer)).label("web"),
                func.sum(func.cast(Question.source == "PREVIOUS", Integer)).label("previous"),
                func.sum(func.cast(Question.source == "AI", Integer)).label("ai"),
            ).where(Question.topic_id == topic_id)
        )
        row = result.first()
        return {
            "total": row.total or 0,
            "manual": row.manual or 0,
            "csv": row.csv or 0,
            "pdf": row.pdf or 0,
            "web": row.web or 0,
            "previous": row.previous or 0,
            "ai": row.ai or 0,
        }


# Singleton
importer = QuestionImporter()
