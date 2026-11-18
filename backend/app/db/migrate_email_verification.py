import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import text
from app.core.database import engine, Base
import app.models.models  # ensure models are registered

def run_migration():
    print("🚀 Running Email Verification schema migrations and backfill...")
    
    # 1. Create newly declared tables (such as email_verification_tokens)
    Base.metadata.create_all(bind=engine)

    # 2. Add columns if not exists (for PostgreSQL)
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        is_sqlite = engine.url.drivername.startswith("sqlite")
        
        if not is_sqlite:
            # PostgreSQL column additions
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_token_hash ON email_verification_tokens(token_hash);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_user_id ON email_verification_tokens(user_id);"))
            
            # Safe backfill: Existing users before this migration are marked as verified so they are never locked out
            result = conn.execute(text("""
                UPDATE users 
                SET email_verified = TRUE, 
                    email_verified_at = COALESCE(created_at, NOW()) 
                WHERE email_verified IS NULL OR email_verified = FALSE;
            """))
            print(f"ℹ️ Safe backfill: updated existing users to verified (rows affected: {result.rowcount})")
        else:
            # SQLite fallback (e.g. unit tests or local SQLite)
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0;"))
            except Exception:
                pass
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME;"))
            except Exception:
                pass
            try:
                conn.execute(text("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL OR email_verified = 0;"))
            except Exception:
                pass

    print("✅ Email Verification migration and existing user backfill completed successfully!")

if __name__ == "__main__":
    run_migration()
