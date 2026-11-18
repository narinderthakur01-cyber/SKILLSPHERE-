import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
import psycopg2
from psycopg2.extras import RealDictCursor

def run_migration():
    print(f"Connecting to PostgreSQL at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}...")
    conn = psycopg2.connect(
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Checking and creating new tables for Password Recovery & Technical Practice...")

    # 1. Table: password_reset_tokens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            ip_address VARCHAR(50)
        );
        CREATE INDEX IF NOT EXISTS idx_reset_token_hash ON password_reset_tokens(token_hash);
        CREATE INDEX IF NOT EXISTS idx_reset_token_user_id ON password_reset_tokens(user_id);
    """)
    print("Table password_reset_tokens verified.")

    # 2. Table: candidate_technologies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_technologies (
            id VARCHAR(36) PRIMARY KEY,
            candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
            technology_name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'LANGUAGE',
            is_resume_detected BOOLEAN NOT NULL DEFAULT TRUE,
            proficiency_level VARCHAR(50) NOT NULL DEFAULT 'INTERMEDIATE',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_candidate_technology UNIQUE (candidate_id, technology_name)
        );
        CREATE INDEX IF NOT EXISTS idx_candidate_tech_cand_id ON candidate_technologies(candidate_id);
    """)
    print("Table candidate_technologies verified.")

    # 3. Table: practice_questions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_questions (
            id VARCHAR(36) PRIMARY KEY,
            technology VARCHAR(100) NOT NULL,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'INTERMEDIATE',
            question_type VARCHAR(20) NOT NULL DEFAULT 'MULTIPLE_CHOICE',
            title VARCHAR(255) NOT NULL,
            prompt TEXT NOT NULL,
            options JSONB,
            correct_answer TEXT NOT NULL,
            hint TEXT,
            explanation TEXT,
            code_template TEXT,
            sample_test_cases JSONB,
            is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
            batch_number INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_practice_questions_tech ON practice_questions(technology);
        CREATE INDEX IF NOT EXISTS idx_practice_questions_diff ON practice_questions(difficulty);
    """)
    print("Table practice_questions verified.")

    # 4. Table: practice_attempts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_attempts (
            id VARCHAR(36) PRIMARY KEY,
            candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
            question_id VARCHAR(36) NOT NULL REFERENCES practice_questions(id) ON DELETE CASCADE,
            technology VARCHAR(100) NOT NULL,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'INTERMEDIATE',
            candidate_answer TEXT,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            explanation_viewed BOOLEAN NOT NULL DEFAULT FALSE,
            hints_used INTEGER NOT NULL DEFAULT 0,
            attempt_count INTEGER NOT NULL DEFAULT 1,
            time_spent_seconds INTEGER NOT NULL DEFAULT 0,
            completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_practice_attempts_cand_id ON practice_attempts(candidate_id);
        CREATE INDEX IF NOT EXISTS idx_practice_attempts_tech ON practice_attempts(technology);
    """)
    print("Table practice_attempts verified.")

    cursor.close()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()
