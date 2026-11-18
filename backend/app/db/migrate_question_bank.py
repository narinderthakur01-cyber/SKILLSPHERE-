import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import text
from app.core.database import engine, Base
import app.models.models  # ensure models are registered

def run_migration():
    print("🚀 Running Question Bank schema migrations...")
    # 1. Create newly declared tables
    Base.metadata.create_all(bind=engine)

    # 2. Add columns if not exists (for PostgreSQL)
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Assessments columns
        conn.execute(text("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS randomize_questions BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS randomize_options BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS auto_selection_config JSON DEFAULT '{}'::json;"))
        conn.execute(text("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;"))

        # Assessment Questions columns
        conn.execute(text("ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS bank_question_id VARCHAR(36) REFERENCES question_bank_items(id) ON DELETE SET NULL;"))
        conn.execute(text("ALTER TABLE assessment_questions ADD COLUMN IF NOT EXISTS explanation TEXT;"))

        # Assessment Attempts columns
        conn.execute(text("ALTER TABLE assessment_attempts ADD COLUMN IF NOT EXISTS question_order JSON DEFAULT '[]'::json;"))
        conn.execute(text("ALTER TABLE assessment_attempts ADD COLUMN IF NOT EXISTS option_orders JSON DEFAULT '{}'::json;"))

    print("✅ Question Bank migrations completed successfully!")

if __name__ == "__main__":
    run_migration()
