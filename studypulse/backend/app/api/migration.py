"""
Migration API Endpoint

This endpoint runs database migrations when called.
Add this to main.py to enable it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["migration"])


@router.post("/api/v1/migration/run")
async def run_migration_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Run database migration to add missing columns.
    Call this endpoint from Railway's backend service.
    """
    migrations_applied = []
    
    # Add question_images column
    try:
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'questions' AND column_name = 'question_images'
        """))
        if not result.scalar():
            await db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN question_images JSONB DEFAULT '[]'::jsonb
            """))
            migrations_applied.append("added question_images column")
    except Exception as e:
        migrations_applied.append(f"question_images: {str(e)[:50]}")
    
    # Add explanation_images column
    try:
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'questions' AND column_name = 'explanation_images'
        """))
        if not result.scalar():
            await db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN explanation_images JSONB DEFAULT '[]'::jsonb
            """))
            migrations_applied.append("added explanation_images column")
    except Exception as e:
        migrations_applied.append(f"explanation_images: {str(e)[:50]}")
    
    # Add audio_url column
    try:
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'questions' AND column_name = 'audio_url'
        """))
        if not result.scalar():
            await db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN audio_url VARCHAR(500)
            """))
            migrations_applied.append("added audio_url column")
    except Exception as e:
        migrations_applied.append(f"audio_url: {str(e)[:50]}")
    
    # Add video_url column
    try:
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'questions' AND column_name = 'video_url'
        """))
        if not result.scalar():
            await db.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN video_url VARCHAR(500)
            """))
            migrations_applied.append("added video_url column")
    except Exception as e:
        migrations_applied.append(f"video_url: {str(e)[:50]}")
    
    await db.commit()
    
    return {
        "status": "completed",
        "migrations_applied": migrations_applied,
        "message": f"Applied {len([m for m in migrations_applied if 'added' in m])} migrations"
    }
