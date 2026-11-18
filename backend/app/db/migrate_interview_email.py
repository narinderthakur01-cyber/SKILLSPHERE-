import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import text
from app.core.database import engine, Base
import app.models.models

def run_migration():
    print("🚀 Running Interview Email tracking schema migration...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Safely add columns to interviews table if not present
        columns_to_add = [
            ("email_status", "VARCHAR(50) DEFAULT 'PENDING' NOT NULL"),
            ("brevo_message_id", "VARCHAR(255)"),
            ("email_sent_at", "TIMESTAMP"),
            ("email_error_message", "TEXT")
        ]

        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE interviews ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"  Added/verified column '{col_name}' on 'interviews'")
            except Exception as e:
                print(f"  Column '{col_name}' notice: {e}")

    print("✅ Interview email schema migration completed successfully!")

if __name__ == "__main__":
    run_migration()
