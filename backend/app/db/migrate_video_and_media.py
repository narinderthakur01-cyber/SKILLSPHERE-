import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.models import (
    MediaAsset, RecordingConsent, InterviewRecording, InterviewTranscript,
    InterviewScorecard, VideoAssessment, VideoAssessmentQuestion,
    CandidateVideoAssignment, CandidateVideoResponse, MediaAuditLog
)

def run_migration():
    print(f"Connecting to database via engine: {engine.url.render_as_string(hide_password=True)}")
    dialect_name = engine.dialect.name
    print(f"Dialect detected: {dialect_name}")

    with engine.begin() as conn:
        # 1. Add new columns to interviews table
        interview_cols = [
            ("room_id", "VARCHAR(100)"),
            ("room_status", "VARCHAR(50) DEFAULT 'SCHEDULED'"),
            ("room_started_at", "TIMESTAMP"),
            ("room_ended_at", "TIMESTAMP"),
            ("round_number", "INTEGER DEFAULT 1"),
            ("round_title", "VARCHAR(100) DEFAULT 'Technical Interview'"),
            ("recording_enabled", "BOOLEAN DEFAULT FALSE"),
            ("recording_status", "VARCHAR(50) DEFAULT 'OFF'"),
            ("is_admitted", "BOOLEAN DEFAULT TRUE"),
            ("candidate_joined_at", "TIMESTAMP"),
            ("recruiter_joined_at", "TIMESTAMP"),
        ]

        for col_name, col_type in interview_cols:
            try:
                conn.execute(text(f"ALTER TABLE interviews ADD COLUMN {col_name} {col_type};"))
                print(f"  + Added column interviews.{col_name}")
            except Exception as e:
                # Column likely already exists
                print(f"  . Column interviews.{col_name} already present or skipped: {e}")

        # Add index on room_id
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_interviews_room_id ON interviews (room_id);"))
            print("  + Created index ix_interviews_room_id")
        except Exception as e:
            print(f"  . Index ix_interviews_room_id skipped: {e}")

    # 2. Create newly declared tables via metadata
    print("Creating new tables via metadata.create_all...")
    Base.metadata.create_all(bind=engine)
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
