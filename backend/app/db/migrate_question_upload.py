import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import text
from app.core.database import engine, Base
import app.models.models

def run_migration():
    print("🚀 Running Question Upload & Import Tracking schema migration...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Safely add columns to question_bank_items table if not present
        columns_to_add = [
            ("source_file", "VARCHAR(255)"),
            ("source_page", "INTEGER"),
            ("import_batch_id", "VARCHAR(36)")
        ]

        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE question_bank_items ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"  Added/verified column '{col_name}' on 'question_bank_items'")
            except Exception as e:
                print(f"  Column '{col_name}' notice: {e}")

    print("✅ Question Upload schema migration completed successfully!")

if __name__ == "__main__":
    run_migration()
