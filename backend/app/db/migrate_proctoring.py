import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import text
from app.core.database import engine, Base
import app.models.models  # Ensure all models are registered

def run_migration():
    print("🚀 Running Proctoring schema migration...")
    # 1. Create newly declared tables
    Base.metadata.create_all(bind=engine)

    # 2. Add extra columns / indexes if needed for PostgreSQL
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Create indexes if they don't already exist
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_sessions_attempt ON proctoring_sessions(assessment_attempt_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_sessions_cand ON proctoring_sessions(candidate_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_sessions_status ON proctoring_sessions(monitoring_status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_events_session ON proctoring_events(proctoring_session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_events_type ON proctoring_events(event_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proctoring_events_review ON proctoring_events(reviewed_status);"))

    print("✅ Proctoring schema migrations completed successfully!")

if __name__ == "__main__":
    run_migration()
