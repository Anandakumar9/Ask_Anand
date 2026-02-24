-- Production Database Migration Script
-- Run this SQL directly on the production PostgreSQL database
-- This adds the missing image support columns to the questions table

-- Add question_images column (JSON array of image URLs)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'question_images') THEN
        ALTER TABLE questions ADD COLUMN question_images JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

-- Add explanation_images column (JSON array of image URLs)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'explanation_images') THEN
        ALTER TABLE questions ADD COLUMN explanation_images JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

-- Add audio_url column
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'audio_url') THEN
        ALTER TABLE questions ADD COLUMN audio_url VARCHAR(500);
    END IF;
END $$;

-- Add video_url column
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'video_url') THEN
        ALTER TABLE questions ADD COLUMN video_url VARCHAR(500);
    END IF;
END $$;

-- Update metadata_json default to empty dict if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'metadata_json') THEN
        ALTER TABLE questions ALTER COLUMN metadata_json SET DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Create indexes for faster JSON queries (optional but recommended)
CREATE INDEX IF NOT EXISTS ix_questions_question_images ON questions USING gin (question_images);
CREATE INDEX IF NOT EXISTS ix_questions_explanation_images ON questions USING gin (explanation_images);

-- Verify the migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'questions' 
AND column_name IN ('question_images', 'explanation_images', 'audio_url', 'video_url');
