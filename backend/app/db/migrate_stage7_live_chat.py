"""
Explicit, reviewable database migration script for Live Agent Handoff & Real-Time Chat (Stage 7).
This script creates:
- admin_availability (tracks admin availability, capacity, heartbeats)
- websocket_auth_tickets (short-lived single-use authentication tokens)
And adds live chat columns to support_tickets if not already present:
- is_live_chat (Boolean)
- live_chat_requested_at (DateTime)
- live_chat_ended_at (DateTime)

SAFETY NOTICE:
- Do NOT run automatically during application startup.
- Reviewable and executable on demand with target database URI.
"""

import sys
import os
import argparse
from sqlalchemy import create_engine, text, inspect

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import Base
from app.models.models import (
    AdminAvailability,
    WebSocketAuthTicket,
    SupportTicket
)


def run_migration(db_url: str):
    print(f"🚀 Running Stage 7 Live Chat migration on target: {db_url[:20]}...")
    target_engine = create_engine(db_url)

    # 1. Create tables defined in models (admin_availability, websocket_auth_tickets)
    Base.metadata.create_all(
        bind=target_engine,
        tables=[
            AdminAvailability.__table__,
            WebSocketAuthTicket.__table__
        ]
    )

    # 2. Add columns to support_tickets if missing (e.g. for existing databases)
    inspector = inspect(target_engine)
    existing_columns = [col["name"] for col in inspector.get_columns("support_tickets")]

    with target_engine.connect() as conn:
        trans = conn.begin()
        try:
            if "is_live_chat" not in existing_columns:
                print("Adding column is_live_chat to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN is_live_chat BOOLEAN NOT NULL DEFAULT FALSE;"))
            if "live_chat_requested_at" not in existing_columns:
                print("Adding column live_chat_requested_at to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN live_chat_requested_at TIMESTAMP NULL;"))
            if "live_chat_ended_at" not in existing_columns:
                print("Adding column live_chat_ended_at to support_tickets...")
                conn.execute(text("ALTER TABLE support_tickets ADD COLUMN live_chat_ended_at TIMESTAMP NULL;"))
            trans.commit()
        except Exception as e:
            trans.rollback()
            print(f"Column addition note/warning: {e}")

    # 3. Add extra indexes for performance if PostgreSQL
    is_pg = "postgresql" in target_engine.name.lower()
    if is_pg:
        with target_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_is_live ON support_tickets(is_live_chat);",
                "CREATE INDEX IF NOT EXISTS idx_admin_avail_status ON admin_availability(is_available);",
                "CREATE INDEX IF NOT EXISTS idx_ws_tickets_token ON websocket_auth_tickets(ticket_token);",
                "CREATE INDEX IF NOT EXISTS idx_ws_tickets_user_ticket ON websocket_auth_tickets(user_id, ticket_id);"
            ]
            for idx_stmt in indexes:
                try:
                    conn.execute(text(idx_stmt))
                except Exception as e:
                    print(f"Index creation note: {e}")

    print("✅ Stage 7 Live Chat schema migration successfully applied!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stage 7 Live Chat Database Migration")
    parser.add_argument("--db-url", type=str, default=None, help="Target database connection URL")
    args = parser.parse_args()

    from app.core.config import settings
    url = args.db_url or settings.DATABASE_URL
    run_migration(url)
