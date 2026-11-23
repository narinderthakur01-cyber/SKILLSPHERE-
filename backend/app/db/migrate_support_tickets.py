"""
Explicit, reviewable database migration script for Support Ticket System (Stage 4).
This script creates:
- ticket_sequences (atomic counter table)
- support_tickets
- ticket_messages
- ticket_audit_logs
with appropriate indexes and unique constraints.

SAFETY NOTICE:
- Do NOT run automatically during application startup.
- Reviewable and executable on demand with target database URI.
"""

import sys
import os
import argparse
from sqlalchemy import create_engine, text

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import Base
from app.models.models import (
    TicketSequence,
    SupportTicket,
    TicketMessage,
    TicketAuditLog
)


def run_migration(db_url: str):
    print(f"🚀 Running Support Tickets migration on target: {db_url[:20]}...")
    target_engine = create_engine(db_url)

    # 1. Create tables defined in models
    Base.metadata.create_all(
        bind=target_engine,
        tables=[
            TicketSequence.__table__,
            SupportTicket.__table__,
            TicketMessage.__table__,
            TicketAuditLog.__table__
        ]
    )

    # 2. Add extra performance indexes if on PostgreSQL
    is_pg = "postgresql" in target_engine.name.lower()
    if is_pg:
        with target_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_user ON support_tickets(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);",
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_cat ON support_tickets(category);",
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_priority ON support_tickets(priority);",
                "CREATE INDEX IF NOT EXISTS idx_support_tickets_admin ON support_tickets(assigned_admin_id);",
                "CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id);",
                "CREATE INDEX IF NOT EXISTS idx_ticket_messages_internal ON ticket_messages(is_internal);",
                "CREATE INDEX IF NOT EXISTS idx_ticket_audit_ticket ON ticket_audit_logs(ticket_id);"
            ]
            for idx_stmt in indexes:
                try:
                    conn.execute(text(idx_stmt))
                except Exception as e:
                    print(f"Index creation note: {e}")

    print("✅ Support Tickets schema migration successfully applied!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Support Tickets Database Migration")
    parser.add_argument("--db-url", type=str, default=None, help="Target database connection URL")
    args = parser.parse_args()

    from app.core.config import settings
    url = args.db_url or settings.DATABASE_URL
    run_migration(url)
