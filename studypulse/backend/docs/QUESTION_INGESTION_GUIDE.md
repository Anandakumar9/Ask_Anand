# NEET PG Question Ingestion System - Complete Integration Guide

## Overview

This document provides a comprehensive guide for ingesting NEET PG medical exam questions into the StudyPulse database, including support for images attached to questions, options, and explanations.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Question Ingestion Pipeline                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐   │
│  │  HTML File   │───▶│  HTML Parser     │───▶│  JSON Transform         │   │
│  │  (Source)    │    │  (Python Script) │    │  (QuestionImport format)│   │
│  └──────────────┘    └──────────────────┘    └─────────────────────────┘   │
│                                                         │                   │
│                                                         ▼                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Bulk Import API                                  │  │
│  │  POST /api/v1/questions/import/bulk                                   │  │
│  │  - Validates questions                                                │  │
│  │  - Stores in PostgreSQL                                               │  │
│  │  - Indexes in Qdrant Vector Store                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Database Schema                                  │  │
│  │  questions table:                                                     │  │
│  │  - question_text, options (JSON), correct_answer                      │  │
│  │  - question_images[], explanation_images[]                            │  │
│  │  - audio_url, video_url                                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Frontend Display                                 │  │
│  │  QuestionCard component:                                              │  │
│  │  - Renders question with images                                       │  │
│  │  - Displays option images                                             │  │
│  │  - Shows explanation with images                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Questions Table (Enhanced with Image Support)

```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,  -- {"A": "text"} or {"A": {"text": "...", "image": "url"}}
    correct_answer VARCHAR(1) NOT NULL,
    explanation TEXT,
    source VARCHAR(20) DEFAULT 'PREVIOUS',
    year INTEGER,
    difficulty VARCHAR(20) DEFAULT 'medium',
    
    -- Image support fields
    question_images JSONB DEFAULT '[]',    -- ["url1", "url2", ...]
    explanation_images JSONB DEFAULT '[]', -- ["url1", "url2", ...]
    audio_url VARCHAR(500),
    video_url VARCHAR(500),
    
    -- Metadata
    avg_rating FLOAT DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    metadata_json JSONB DEFAULT '{}',
    is_validated BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for JSON queries
CREATE INDEX ix_questions_question_images ON questions USING GIN (question_images);
CREATE INDEX ix_questions_explanation_images ON questions USING GIN (explanation_images);
```

### Options JSON Format

The `options` column supports two formats:

**Text-only options:**
```json
{
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
}
```

**Options with images (for medical exams):**
```json
{
    "A": {"text": "Option A text", "image": "https://example.com/image-a.jpg"},
    "B": {"text": "Option B text", "image": null},
    "C": {"text": "Option C text", "image": "https://example.com/image-c.jpg"},
    "D": {"text": "Option D text", "image": null}
}
```

## Step-by-Step Ingestion Workflow

### Step 1: Prepare the HTML File

The HTML file should contain questions embedded as JSON in JavaScript:

```html
<script>
    questions = [
        {
            "text": "Question text here...",
            "options": [
                {"label": "A", "text": "Option A", "correct": false},
                {"label": "B", "text": "Option B", "correct": true},
                {"label": "C", "text": "Option C", "correct": false},
                {"label": "D", "text": "Option D", "correct": false}
            ],
            "correct_answer": "B. Option B",
            "question_images": ["https://example.com/q-image.jpg"],
            "explanation_images": ["https://example.com/e-image.jpg"],
            "explanation": "<p>Explanation HTML...</p>",
            "audio": "https://example.com/audio.mp3",
            "video": ""
        }
    ];
</script>
```

### Step 2: Run the HTML Parser

```bash
# Navigate to backend directory
cd studypulse/backend

# Run the parser with topic mapping
python scripts/html_question_parser.py \
    --input "path/to/questions.html" \
    --output "data/questions_import.json" \
    --topic-map '{"Adnexal Mass and Gyne Cancers": 1, "Antepartum Hemorrhage": 2}' \
    --default-topic 1 \
    --report
```

**Output:**
- `questions_import.json` - Questions in bulk import format
- `questions_import.report.json` - Topic mapping report

### Step 3: Review the Generated JSON

```json
{
    "questions": [
        {
            "topic_id": 1,
            "question_text": "Question text...",
            "options": {
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            },
            "correct_answer": "B",
            "explanation": "Explanation text...",
            "source": "WEB",
            "difficulty": "medium",
            "question_images": ["https://..."],
            "explanation_images": ["https://..."]
        }
    ],
    "metadata": {
        "generated_at": "2024-01-15T10:00:00",
        "total_questions": 100,
        "source": "HTML_IMPORT",
        "has_image_support": true
    }
}
```

### Step 4: Import via Bulk API

```bash
# Start the backend server
cd studypulse/backend
uvicorn app.main:app --reload

# Import questions via API
curl -X POST "http://localhost:8000/api/v1/questions/import/bulk" \
    -H "Content-Type: application/json" \
    -d @data/questions_import.json
```

**Response:**
```json
{
    "success": true,
    "imported_count": 100,
    "failed_count": 0,
    "errors": [],
    "question_ids": [1, 2, 3, ...]
}
```

### Step 5: Verify Import

```bash
# Check import stats
curl "http://localhost:8000/api/v1/questions/import/stats/1"

# Get questions for a topic
curl "http://localhost:8000/api/v1/questions/topic/1?skip=0&limit=10"
```

## API Endpoints

### Import Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/questions/import/single` | POST | Import a single question |
| `/api/v1/questions/import/bulk` | POST | Import multiple questions |
| `/api/v1/questions/import/csv` | POST | Import from CSV data |
| `/api/v1/questions/import/stats/{topic_id}` | GET | Get import statistics |

### Single Question Import

```bash
POST /api/v1/questions/import/single
Content-Type: application/json

{
    "topic_id": 1,
    "question_text": "Which of the following is the most common histological type of cervical cancer?",
    "options": {
        "A": "Adenocarcinoma",
        "B": "Squamous cell carcinoma",
        "C": "Small cell carcinoma",
        "D": "Clear cell carcinoma"
    },
    "correct_answer": "B",
    "explanation": "Squamous cell carcinoma is the most common histological type...",
    "source": "MANUAL",
    "difficulty": "medium",
    "question_images": [],
    "explanation_images": ["https://example.com/histology.jpg"]
}
```

### Bulk Import with Images

```bash
POST /api/v1/questions/import/bulk
Content-Type: application/json

{
    "questions": [
        {
            "topic_id": 1,
            "question_text": "Identify the condition shown in the image:",
            "options": {
                "A": {"text": "Cervical dysplasia", "image": null},
                "B": {"text": "Cervical carcinoma", "image": "https://example.com/option-b.jpg"},
                "C": {"text": "Cervical polyp", "image": null},
                "D": {"text": "Normal cervix", "image": null}
            },
            "correct_answer": "B",
            "explanation": "The image shows...",
            "source": "WEB",
            "difficulty": "hard",
            "question_images": ["https://example.com/question-image.jpg"],
            "explanation_images": ["https://example.com/explanation-image.jpg"]
        }
    ]
}
```

## Frontend Integration

### Using the QuestionCard Component

```tsx
import QuestionCard from '@/components/QuestionCard';

function StudyPage() {
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
    const [showResult, setShowResult] = useState(false);

    const question = questions[currentQuestion];

    return (
        <QuestionCard
            question={question}
            questionNumber={currentQuestion + 1}
            totalQuestions={questions.length}
            selectedAnswer={selectedAnswer}
            showResult={showResult}
            onAnswerSelect={(answer) => {
                setSelectedAnswer(answer);
                setShowResult(true);
            }}
        />
    );
}
```

### QuestionCard Features

1. **Question Images**: Displays images attached to the question
2. **Option Images**: Shows images for each option (if available)
3. **Explanation Images**: Displays images in the explanation section
4. **Audio/Video Links**: Provides links to audio/video explanations
5. **Image Modal**: Click any image to view full-size
6. **Difficulty Badge**: Color-coded difficulty indicator
7. **Source Badge**: Shows question source (MANUAL, WEB, AI, etc.)

## Running the Migration

### Apply Database Migration

```bash
# Navigate to backend directory
cd studypulse/backend

# Run Alembic migration
alembic upgrade head

# Or run the migration directly
python -c "
from alembic.config import Config
from alembic import command
config = Config('alembic.ini')
command.upgrade(config, 'head')
"
```

### Verify Migration

```sql
-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'questions' 
AND column_name IN ('question_images', 'explanation_images', 'audio_url', 'video_url');

-- Expected output:
-- question_images | jsonb
-- explanation_images | jsonb
-- audio_url | character varying
-- video_url | character varying
```

## Testing the Pipeline

### Unit Tests

```bash
# Run parser tests
python -m pytest tests/unit/test_html_parser.py -v

# Run import tests
python -m pytest tests/unit/test_question_import.py -v
```

### Integration Tests

```bash
# Run API tests
python -m pytest tests/integration/test_questions_api.py -v

# Run end-to-end test
python -m pytest tests/e2e/test_question_ingestion.py -v
```

### Manual Testing

```bash
# 1. Parse sample HTML
python scripts/html_question_parser.py \
    --input "tests/fixtures/sample_questions.html" \
    --output "tests/output/test_import.json" \
    --report

# 2. Import via API
curl -X POST "http://localhost:8000/api/v1/questions/import/bulk" \
    -H "Content-Type: application/json" \
    -d @tests/output/test_import.json

# 3. Verify in database
psql -d studypulse -c "SELECT id, question_text, question_images FROM questions LIMIT 5;"
```

## Troubleshooting

### Common Issues

1. **"Topic ID not found" error**
   - Ensure topics exist in the database
   - Use correct topic_id mapping in the parser

2. **"Options must have exactly 4 keys" error**
   - Verify all questions have 4 options (A, B, C, D)
   - Check for missing or empty options

3. **Image URLs not saving**
   - Ensure migration has been applied
   - Check column defaults are set correctly

4. **Frontend not displaying images**
   - Verify CORS settings for image URLs
   - Check image URLs are accessible

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/html_question_parser.py --input "questions.html" --output "out.json"
```

## File Structure

```
studypulse/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       └── add_image_support_to_questions.py  # Migration
│   ├── app/
│   │   ├── models/
│   │   │   └── question.py                        # Enhanced model
│   │   ├── schemas/
│   │   │   └── question_import.py                 # Enhanced schema
│   │   ├── services/
│   │   │   └── question_importer.py               # Import service
│   │   └── api/
│   │       └── questions.py                       # API endpoints
│   ├── scripts/
│   │   └── html_question_parser.py                # Parser script
│   └── docs/
│       └── QUESTION_INGESTION_GUIDE.md            # This file
└── frontend/
    └── src/
        └── components/
            └── QuestionCard.tsx                   # Display component
```

## Summary

This integration provides:

1. **HTML Parser**: Extracts questions from HTML files with embedded JSON
2. **Enhanced Schema**: Supports images for questions, options, and explanations
3. **Database Migration**: Adds image support columns to the questions table
4. **Bulk Import API**: Handles both text-only and image-enhanced questions
5. **Frontend Component**: Displays questions with images in a user-friendly interface

The system is backward compatible - existing text-only questions continue to work while new questions can include images for medical entrance exams.
