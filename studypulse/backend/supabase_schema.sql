-- StudyPulse Supabase Database Schema
-- Run these SQL queries in Supabase SQL Editor to create the tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) DEFAULT 'student',
    target_exam_id BIGINT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Exams table
CREATE TABLE IF NOT EXISTS exams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id BIGSERIAL PRIMARY KEY,
    exam_id BIGINT REFERENCES exams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT REFERENCES subjects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answer VARCHAR(10) NOT NULL,
    explanation TEXT,
    source VARCHAR(50) DEFAULT 'PREVIOUS',
    difficulty VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT true,
    is_validated BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Study sessions table
CREATE TABLE IF NOT EXISTS study_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    topic_id BIGINT REFERENCES topics(id),
    duration_mins INTEGER NOT NULL,
    actual_duration_mins INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active'
);

-- Mock tests table
CREATE TABLE IF NOT EXISTS mock_tests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    topic_id BIGINT REFERENCES topics(id),
    session_id BIGINT REFERENCES study_sessions(id),
    total_questions INTEGER NOT NULL,
    time_limit_seconds INTEGER DEFAULT 600,
    question_ids JSONB NOT NULL,
    score_percentage DECIMAL(5,2),
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    time_taken_seconds INTEGER,
    star_earned BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Question responses table
CREATE TABLE IF NOT EXISTS question_responses (
    id BIGSERIAL PRIMARY KEY,
    mock_test_id BIGINT REFERENCES mock_tests(id) ON DELETE CASCADE,
    question_id BIGINT REFERENCES questions(id),
    selected_answer VARCHAR(10),
    is_correct BOOLEAN,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Question ratings table (for AI-generated questions)
CREATE TABLE IF NOT EXISTS question_ratings (
    id BIGSERIAL PRIMARY KEY,
    question_id BIGINT REFERENCES questions(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subjects_exam_id ON subjects(exam_id);
CREATE INDEX idx_topics_subject_id ON topics(subject_id);
CREATE INDEX idx_questions_topic_id ON questions(topic_id);
CREATE INDEX idx_questions_source ON questions(source);
CREATE INDEX idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX idx_mock_tests_user_id ON mock_tests(user_id);
CREATE INDEX idx_mock_tests_topic_id ON mock_tests(topic_id);
CREATE INDEX idx_question_responses_mock_test_id ON question_responses(mock_test_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
-- Sample exams
INSERT INTO exams (name, description) VALUES
('UPSC', 'Union Public Service Commission'),
('SSC CGL', 'Staff Selection Commission Combined Graduate Level'),
('JEE Main', 'Joint Entrance Examination for Engineering'),
('NEET', 'National Eligibility cum Entrance Test'),
('Banking PO', 'Bank Probationary Officer Exam')
ON CONFLICT DO NOTHING;

-- Sample user (password: password123, hashed with bcrypt)
INSERT INTO users (email, name, hashed_password, role) VALUES
('test@studypulse.com', 'Test User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyI2nOPKMpSu', 'student')
ON CONFLICT (email) DO NOTHING;

-- Row Level Security (RLS) Policies
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mock_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_ratings ENABLE ROW LEVEL SECURITY;

-- Users can read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

-- Users can update their own data
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Users can read their own study sessions
CREATE POLICY "Users can read own sessions" ON study_sessions
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Users can insert their own study sessions
CREATE POLICY "Users can insert own sessions" ON study_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Users can read their own mock tests
CREATE POLICY "Users can read own tests" ON mock_tests
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Users can insert their own mock tests
CREATE POLICY "Users can insert own tests" ON mock_tests
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Public read access for exams, subjects, topics, questions
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can read exams" ON exams FOR SELECT USING (true);
CREATE POLICY "Public can read subjects" ON subjects FOR SELECT USING (true);
CREATE POLICY "Public can read topics" ON topics FOR SELECT USING (true);
CREATE POLICY "Public can read questions" ON questions FOR SELECT USING (true);

-- Grant permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO anon, authenticated;
