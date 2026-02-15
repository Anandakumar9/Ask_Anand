"""API endpoints for question management and import operations."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.ollama import ollama_client
from app.models.user import User
from app.schemas.question_import import (
    QuestionImport,
    BulkQuestionImport,
    CSVImportRequest,
    ImportResponse,
    QuestionPreview,
)
from app.services.question_importer import importer
from app.services.pdf_extractor import pdf_extractor
from app.services.pdf_question_parser import pdf_question_parser
from app.services.upsc_web_scraper import upsc_scraper
from app.services.neet_web_scraper import neet_scraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/import/single", response_model=ImportResponse)
async def import_single_question(
    question: QuestionImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a single question manually.

    **Use cases:**
    - Manually add a question from a book
    - Import a question from a PDF by copy-paste
    - Add a practice question

    **Example request:**
    ```json
    {
      "topic_id": 15,
      "question_text": "Which of the following is the primary function of RBI?",
      "options": {
        "A": "Printing currency notes",
        "B": "Regulating commercial banks",
        "C": "Managing forex reserves",
        "D": "All of the above"
      },
      "correct_answer": "D",
      "explanation": "RBI performs all these functions as India's central bank.",
      "source": "MANUAL",
      "year": 2023,
      "difficulty": "medium"
    }
    ```
    """
    # Verify topic exists
    if not await importer.validate_topic_exists(question.topic_id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic ID {question.topic_id} not found",
        )

    success, question_id, error = await importer.import_single(question, db)

    if success:
        return ImportResponse(
            success=True,
            imported_count=1,
            failed_count=0,
            errors=[],
            question_ids=[question_id],
        )
    else:
        return ImportResponse(
            success=False,
            imported_count=0,
            failed_count=1,
            errors=[error],
            question_ids=[],
        )


@router.post("/import/bulk", response_model=ImportResponse)
async def import_bulk_questions(
    data: BulkQuestionImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import multiple questions at once.

    **Use cases:**
    - Batch import from a structured source
    - Programmatic question addition
    - Testing with multiple questions

    **Example request:**
    ```json
    {
      "questions": [
        {
          "topic_id": 15,
          "question_text": "Question 1 text...",
          "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
          "correct_answer": "A",
          "difficulty": "easy"
        },
        {
          "topic_id": 15,
          "question_text": "Question 2 text...",
          "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
          "correct_answer": "B",
          "difficulty": "medium"
        }
      ]
    }
    ```
    """
    # Verify all topics exist
    topic_ids = {q.topic_id for q in data.questions}
    for topic_id in topic_ids:
        if not await importer.validate_topic_exists(topic_id, db):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic ID {topic_id} not found",
            )

    result = await importer.import_bulk(data.questions, db)
    return result


@router.post("/import/csv", response_model=ImportResponse)
async def import_csv_questions(
    data: CSVImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import questions from CSV data.

    **CSV Format:**
    ```
    question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, difficulty, year
    ```

    **Example CSV:**
    ```csv
    question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,difficulty,year
    "What is the capital of India?","Mumbai","Delhi","Kolkata","Chennai","B","Delhi is the capital.","easy",2023
    "Who is the current RBI Governor?","Shaktikanta Das","Urjit Patel","Raghuram Rajan","D Subbarao","A","As of 2024.","medium",2024
    ```

    **Request body:**
    ```json
    {
      "topic_id": 15,
      "source": "CSV",
      "csv_data": "question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,difficulty,year\\n...",
      "skip_header": true
    }
    ```
    """
    # Verify topic exists
    if not await importer.validate_topic_exists(data.topic_id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic ID {data.topic_id} not found",
        )

    result = await importer.import_from_csv(
        csv_data=data.csv_data,
        topic_id=data.topic_id,
        source=data.source,
        skip_header=data.skip_header,
        db=db,
    )
    return result


@router.get("/import/stats/{topic_id}")
async def get_import_stats(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get import statistics for a topic.

    Returns counts by source type: MANUAL, CSV, PDF, WEB, PREVIOUS, AI.
    """
    if not await importer.validate_topic_exists(topic_id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic ID {topic_id} not found",
        )

    stats = await importer.get_import_stats(topic_id, db)
    return stats


@router.post("/import/pdf", response_model=ImportResponse)
async def import_pdf_questions(
    file: UploadFile = File(..., description="PDF file to extract questions from"),
    topic_id: int = Form(..., description="Topic ID to assign questions to"),
    target_count: int = Form(10, description="Number of questions to generate"),
    difficulty: str = Form("medium", description="Target difficulty: easy/medium/hard"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract and import questions from a PDF textbook using AI.

    **How it works:**
    1. Extracts text from uploaded PDF
    2. Uses Ollama AI to parse text into MCQ format
    3. Auto-imports questions to database

    **Use cases:**
    - Bulk import from PDF textbooks
    - Extract questions from UPSC/NEET study materials
    - Quickly populate question bank

    **Requirements:**
    - PDF must be text-based (not scanned images)
    - Ollama must be running locally
    - Topic must exist in database

    **Example request (multipart/form-data):**
    ```
    file: [PDF file]
    topic_id: 15
    target_count: 20
    difficulty: medium
    ```

    **Response:**
    ```json
    {
      "success": true,
      "imported_count": 18,
      "failed_count": 2,
      "errors": ["Q7: Duplicate options"],
      "question_ids": [101, 102, 103, ...],
      "metadata": {
        "pdf_filename": "economics.pdf",
        "pdf_pages": 45,
        "extraction_time_sec": 3.2,
        "parsing_time_sec": 12.5
      }
    }
    ```
    """
    import time

    start_time = time.time()

    # Validate file type (extension and MIME type)
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF (.pdf extension)",
        )

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type must be application/pdf",
        )

    # Verify topic exists
    if not await importer.validate_topic_exists(topic_id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic ID {topic_id} not found",
        )

    # Verify Ollama is available
    if not await ollama_client.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama AI service is not available. Make sure Ollama is running.",
        )

    # Validate parameters
    if target_count < 1 or target_count > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_count must be between 1 and 100",
        )

    if difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="difficulty must be one of: easy, medium, hard",
        )

    try:
        # Step 1: Read PDF file
        pdf_content = await file.read()
        logger.info(f"Uploaded PDF: {file.filename} ({len(pdf_content)} bytes)")

        # Step 2: Extract text from PDF
        extraction_start = time.time()
        extracted_text = pdf_extractor.extract_text(pdf_content, file.filename)
        extraction_time = time.time() - extraction_start

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from PDF. Ensure it's not a scanned image.",
            )

        logger.info(f"Extracted {len(extracted_text)} chars in {extraction_time:.1f}s")

        # Step 3: Parse text into questions using Ollama AI
        parsing_start = time.time()
        source = f"PDF: {file.filename}"
        questions = await pdf_question_parser.parse_text_to_questions(
            text=extracted_text,
            topic_id=topic_id,
            source=source,
            target_count=target_count,
            difficulty=difficulty,
        )
        parsing_time = time.time() - parsing_start

        logger.info(f"Parsed {len(questions)} questions in {parsing_time:.1f}s")

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not generate questions from PDF content. Try a different PDF or adjust target_count.",
            )

        # Step 4: Import questions to database
        result = await importer.import_bulk(questions, db)

        # Add metadata
        pdf_info = pdf_extractor.get_pdf_info(pdf_content)
        total_time = time.time() - start_time

        result_dict = result.model_dump()
        result_dict["metadata"] = {
            "pdf_filename": file.filename,
            "pdf_pages": pdf_info.get("page_count", 0),
            "pdf_size_kb": pdf_info.get("file_size_kb", 0),
            "text_chars_extracted": len(extracted_text),
            "extraction_time_sec": round(extraction_time, 2),
            "parsing_time_sec": round(parsing_time, 2),
            "total_time_sec": round(total_time, 2),
        }

        logger.info(
            f"PDF import complete: {result.imported_count}/{target_count} questions "
            f"in {total_time:.1f}s"
        )

        return result_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF import failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF import failed: {str(e)}",
        )


# Pydantic models for web scraping requests
class WebScrapingRequest(BaseModel):
    """Request model for web scraping."""
    urls: List[HttpUrl]
    topic_id: int
    max_questions_per_url: int = 20
    exam_type: str = "upsc"  # "upsc" or "neet"


@router.post("/import/web-scrape", response_model=ImportResponse)
async def import_from_web_scraping(
    request: WebScrapingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scrape questions from UPSC/NEET websites and import to database.

    **How it works:**
    1. Scrapes specified URLs for MCQ questions
    2. Parses question text, options, answers, explanations
    3. Auto-imports questions to database

    **Supported websites:**
    - UPSC: ClearIAS.com, InsightsOnIndia, Vision IAS
    - NEET: Marrow.in, PrepLadder, Medscape

    **Request body:**
    ```json
    {
      "urls": [
        "https://www.clearias.com/upsc-prelims-questions/",
        "https://www.insightsonindia.com/daily-quiz/"
      ],
      "topic_id": 1,
      "max_questions_per_url": 20,
      "exam_type": "upsc"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "imported_count": 35,
      "failed_count": 5,
      "errors": [...],
      "question_ids": [...],
      "metadata": {
        "urls_scraped": 2,
        "total_time_sec": 15.3
      }
    }
    ```

    **Note:** Web scraping depends on website structure. If a website changes
    its HTML, scraping may fail. Use PDF import as a more reliable alternative.
    """
    import time

    start_time = time.time()

    # Validate topic exists
    if not await importer.validate_topic_exists(request.topic_id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic ID {request.topic_id} not found",
        )

    # Validate exam type
    if request.exam_type.lower() not in ["upsc", "neet"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="exam_type must be 'upsc' or 'neet'",
        )

    # Validate URLs
    if not request.urls or len(request.urls) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide 1-10 URLs to scrape",
        )

    try:
        # Select appropriate scraper
        if request.exam_type.lower() == "upsc":
            scraper = upsc_scraper
            logger.info(f"Using UPSC scraper for {len(request.urls)} URLs")
        else:
            scraper = neet_scraper
            logger.info(f"Using NEET scraper for {len(request.urls)} URLs")

        # Scrape questions from all URLs
        url_strings = [str(url) for url in request.urls]
        questions = await scraper.scrape_multiple_urls(
            urls=url_strings,
            topic_id=request.topic_id,
            max_questions_per_url=request.max_questions_per_url
        )

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No questions could be scraped from the provided URLs. "
                       "Check that URLs contain MCQ questions and are accessible.",
            )

        logger.info(f"Scraped {len(questions)} questions total")

        # Import to database
        result = await importer.import_bulk(questions, db)

        # Add metadata
        total_time = time.time() - start_time
        result_dict = result.model_dump()
        result_dict["metadata"] = {
            "urls_scraped": len(request.urls),
            "exam_type": request.exam_type.upper(),
            "questions_per_url": len(questions) / len(request.urls),
            "total_time_sec": round(total_time, 2),
        }

        await scraper.close()  # Clean up HTTP client

        logger.info(
            f"Web scraping complete: {result.imported_count} questions imported in {total_time:.1f}s"
        )

        return result_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web scraping failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Web scraping failed: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Simple health check for question import service."""
    return {"status": "ok", "service": "question_importer"}
