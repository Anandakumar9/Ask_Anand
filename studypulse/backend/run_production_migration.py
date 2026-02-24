#!/usr/bin/env python3
"""
Run Migration on Production Database

This script connects to the production database and adds missing columns.

Usage:
    # Set the production database URL
    set PRODUCTION_DATABASE_URL=postgresql://user:pass@host:port/db
    
    # Run the migration
    python scripts/run_production_migration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def run_migration(database_url: str):
    """Run the migration to add missing columns."""
    
    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    print(f"Connecting to production database...")
    engine = create_async_engine(database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n[1/5] Adding question_images column...")
        try:
            await session.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN IF NOT EXISTS question_images JSONB DEFAULT '[]'::jsonb
            """))
            print("  [OK] question_images column added")
        except Exception as e:
            print(f"  [SKIP] question_images: {e}")
        
        print("\n[2/5] Adding explanation_images column...")
        try:
            await session.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN IF NOT EXISTS explanation_images JSONB DEFAULT '[]'::jsonb
            """))
            print("  [OK] explanation_images column added")
        except Exception as e:
            print(f"  [SKIP] explanation_images: {e}")
        
        print("\n[3/5] Adding audio_url column...")
        try:
            await session.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN IF NOT EXISTS audio_url VARCHAR(500)
            """))
            print("  [OK] audio_url column added")
        except Exception as e:
            print(f"  [SKIP] audio_url: {e}")
        
        print("\n[4/5] Adding video_url column...")
        try:
            await session.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN IF NOT EXISTS video_url VARCHAR(500)
            """))
            print("  [OK] video_url column added")
        except Exception as e:
            print(f"  [SKIP] video_url: {e}")
        
        print("\n[5/5] Committing changes...")
        await session.commit()
        print("  [OK] Migration completed!")
        
        # Verify
        print("\n[VERIFY] Checking columns...")
        result = await session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'questions' 
            AND column_name IN ('question_images', 'explanation_images', 'audio_url', 'video_url')
        """))
        columns = result.fetchall()
        print(f"  Found {len(columns)} image support columns:")
        for col in columns:
            print(f"    - {col[0]}: {col[1]}")
    
    await engine.dispose()


def main():
    print("=" * 60)
    print("Production Database Migration")
    print("=" * 60)
    print()
    
    # Get database URL from environment
    database_url = os.getenv("PRODUCTION_DATABASE_URL")
    
    if not database_url:
        print("ERROR: PRODUCTION_DATABASE_URL not set!")
        print()
        print("To get your database URL from Railway:")
        print("1. Go to Railway Dashboard")
        print("2. Click on your PostgreSQL service")
        print("3. Click 'Variables' tab")
        print("4. Copy the DATABASE_URL value")
        print()
        print("Then run:")
        print("  set PRODUCTION_DATABASE_URL=your_database_url")
        print("  python scripts/run_production_migration.py")
        sys.exit(1)
    
    asyncio.run(run_migration(database_url))


if __name__ == "__main__":
    main()
