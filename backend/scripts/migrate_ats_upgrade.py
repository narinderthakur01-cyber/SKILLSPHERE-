import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.models import *

def migrate():
    print("🚀 Starting safe additive ATS database migration...")
    with engine.connect() as conn:
        # 1. Add SCREENING to applicationstatusenum
        try:
            conn.execute(text("ALTER TYPE applicationstatusenum ADD VALUE IF NOT EXISTS 'SCREENING' AFTER 'APPLIED';"))
            conn.commit()
            print("  ✓ Added 'SCREENING' to applicationstatusenum")
        except Exception as e:
            print("  - Enum alter note:", e)

        # 2. Add safe additive columns
        cols = [
            ("applications", "recruiter_notes", "TEXT"),
            ("resumes", "confidence_score", "FLOAT DEFAULT 100.0"),
            ("resumes", "missing_fields", "JSON DEFAULT '[]'::json"),
            ("jobs", "department", "VARCHAR(100)")
        ]
        for table, col, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};"))
                conn.commit()
                print(f"  ✓ Added column {col} to {table}")
            except Exception as e:
                print(f"  - Column alter {table}.{col}:", e)

    # 3. Create all newly declared tables
    Base.metadata.create_all(bind=engine)
    print("  ✓ Created all new tables successfully.")

    # 4. Verify tables
    from sqlalchemy import inspect
    insp = inspect(engine)
    print("  ✓ All active tables in PostgreSQL:", insp.get_table_names())
    print("🎉 Migration completed successfully!")

if __name__ == "__main__":
    migrate()
