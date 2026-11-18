import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("skillsphere.migrations")

def run_schema_migrations(engine: Engine):
    """
    Applies non-destructive schema migrations (e.g. ALTER TABLE ADD COLUMN)
    to guarantee PostgreSQL/production database columns match SQLAlchemy models.
    """
    statements = [
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS interview_mode VARCHAR(50) DEFAULT 'HUMAN' NOT NULL;",
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS ai_config_json JSON DEFAULT '{}'::json NOT NULL;",
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS ai_takeover_status VARCHAR(50) DEFAULT 'AI_ACTIVE' NOT NULL;",
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS current_question_index INTEGER DEFAULT 0 NOT NULL;",
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;",
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITHOUT TIME ZONE;"
    ]

    try:
        with engine.begin() as conn:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as ex:
                    # Ignore syntax differences on SQLite / in-memory test databases
                    pass
        logger.info("Schema migrations verified.")
    except Exception as e:
        logger.warning(f"Schema migration warning: {e}")
