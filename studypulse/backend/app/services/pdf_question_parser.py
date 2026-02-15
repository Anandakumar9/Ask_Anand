"""PDF-to-Question parser using Ollama AI.

Converts extracted PDF text into structured MCQ questions.
Uses intelligent chunking and Ollama's JSON mode for reliable parsing.
"""
import logging
from typing import List, Dict, Optional

from app.core.ollama import ollama_client
from app.schemas.question_import import QuestionImport

logger = logging.getLogger(__name__)


class PDFQuestionParser:
    """Parses PDF text into structured questions using Ollama LLM."""

    # Maximum characters per chunk (prevents context overflow)
    CHUNK_SIZE = 4000

    # Question generation prompt template
    SYSTEM_PROMPT = """You are an expert question generator for competitive exams.
Your task is to create high-quality multiple choice questions (MCQs) from educational text.

RULES:
1. Each question must have exactly 4 options (A, B, C, D)
2. Only ONE option is correct
3. Options should be plausible but clearly distinguishable
4. Include a brief explanation (1-2 sentences)
5. Questions should test understanding, not just memorization
6. Avoid negative phrasing ("Which is NOT...")
7. Keep questions clear and concise

Respond with ONLY valid JSON in this exact format:
[
  {
    "question_text": "Full question text here?",
    "option_a": "First option",
    "option_b": "Second option",
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "B",
    "explanation": "Brief explanation why B is correct",
    "difficulty": "medium"
  }
]

Difficulty must be one of: easy, medium, hard"""

    async def parse_text_to_questions(
        self,
        text: str,
        topic_id: int,
        source: str,
        target_count: int = 10,
        difficulty: str = "medium",
    ) -> List[QuestionImport]:
        """Parse PDF text into questions.

        Args:
            text: Extracted PDF text
            topic_id: Database topic ID for questions
            source: Source identifier (e.g., "PDF: Economics Chapter 1")
            target_count: Number of questions to generate
            difficulty: Target difficulty (easy/medium/hard)

        Returns:
            List of QuestionImport objects
        """
        # Split text into manageable chunks
        chunks = self._chunk_text(text, self.CHUNK_SIZE)

        if not chunks:
            logger.warning("No text chunks to process")
            return []

        all_questions = []
        questions_per_chunk = max(1, target_count // len(chunks))

        for idx, chunk in enumerate(chunks, start=1):
            logger.info(f"Processing chunk {idx}/{len(chunks)} ({len(chunk)} chars)")

            chunk_questions = await self._generate_questions_from_chunk(
                chunk=chunk,
                topic_id=topic_id,
                source=source,
                count=questions_per_chunk,
                difficulty=difficulty,
            )

            all_questions.extend(chunk_questions)

            # Stop if we have enough questions
            if len(all_questions) >= target_count:
                break

        logger.info(f"Generated {len(all_questions)} questions from {len(chunks)} chunks")
        return all_questions[:target_count]  # Trim to exact count

    async def _generate_questions_from_chunk(
        self,
        chunk: str,
        topic_id: int,
        source: str,
        count: int,
        difficulty: str,
    ) -> List[QuestionImport]:
        """Generate questions from a single text chunk."""
        prompt = f"""Based on this educational text, generate {count} multiple choice questions.

TEXT:
{chunk}

TARGET DIFFICULTY: {difficulty}

Generate exactly {count} questions following the rules. Output ONLY the JSON array."""

        try:
            # Use Ollama JSON mode for structured output
            result = await ollama_client.generate_json(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                temperature=0.7,  # Some creativity, but not too much
            )

            if not result or not isinstance(result, list):
                logger.warning(f"Invalid response from Ollama: {type(result)}")
                return []

            # Convert JSON to QuestionImport objects
            questions = []
            for q_data in result:
                try:
                    question = self._json_to_question_import(
                        q_data, topic_id, source
                    )
                    questions.append(question)
                except Exception as e:
                    logger.warning(f"Skipping invalid question: {e}")
                    continue

            logger.info(f"Parsed {len(questions)}/{count} questions from chunk")
            return questions

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return []

    def _json_to_question_import(
        self, data: Dict, topic_id: int, source: str
    ) -> QuestionImport:
        """Convert raw JSON to QuestionImport schema."""
        # Validate correct_answer
        correct_answer = data.get("correct_answer", "").upper()
        if correct_answer not in ["A", "B", "C", "D"]:
            raise ValueError(f"Invalid correct_answer: {correct_answer}")

        # Validate difficulty
        difficulty = data.get("difficulty", "medium").lower()
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"

        return QuestionImport(
            topic_id=topic_id,
            question_text=data["question_text"].strip(),
            options={
                "A": data["option_a"].strip(),
                "B": data["option_b"].strip(),
                "C": data["option_c"].strip(),
                "D": data["option_d"].strip(),
            },
            correct_answer=correct_answer,
            explanation=data.get("explanation", "").strip() or None,
            source=source,
            year=None,  # PDFs don't have year info
            difficulty=difficulty,
        )

    @staticmethod
    def _chunk_text(text: str, max_chars: int) -> List[str]:
        """Split text into chunks at paragraph boundaries.

        Args:
            text: Full text to chunk
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If adding this paragraph exceeds limit, save current chunk
            if current_size + para_size > max_chars and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    async def validate_questions(self, questions: List[QuestionImport]) -> Dict[str, any]:
        """Validate generated questions and return quality metrics.

        Args:
            questions: List of generated questions

        Returns:
            Dict with validation stats
        """
        stats = {
            "total": len(questions),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

        for idx, q in enumerate(questions, start=1):
            try:
                # Check required fields
                if not q.question_text or len(q.question_text) < 10:
                    stats["errors"].append(f"Q{idx}: Question too short")
                    stats["invalid"] += 1
                    continue

                # Check all options exist
                if len(q.options) != 4:
                    stats["errors"].append(f"Q{idx}: Must have 4 options")
                    stats["invalid"] += 1
                    continue

                # Check no duplicate options
                option_values = list(q.options.values())
                if len(set(option_values)) != 4:
                    stats["errors"].append(f"Q{idx}: Duplicate options")
                    stats["invalid"] += 1
                    continue

                stats["valid"] += 1

            except Exception as e:
                stats["errors"].append(f"Q{idx}: {str(e)}")
                stats["invalid"] += 1

        return stats


# Singleton
pdf_question_parser = PDFQuestionParser()
