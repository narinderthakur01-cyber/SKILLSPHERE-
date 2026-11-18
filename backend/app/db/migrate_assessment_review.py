import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.core.database import engine

def migrate():
    print("[MIGRATION] Applying Recruiter Assessment Review & Decision History schema changes...")
    queries = [
        # Columns on candidate_assessment_assignments
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS review_status VARCHAR(50) DEFAULT 'PENDING_REVIEW' NOT NULL;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS final_decision VARCHAR(50);
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS decision_reason TEXT;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS recruiter_remarks TEXT;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS candidate_message TEXT;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS reviewed_by_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS score_adjustment INTEGER DEFAULT 0 NOT NULL;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS score_adjustment_reason TEXT;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS adjusted_by_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS adjusted_at TIMESTAMP WITH TIME ZONE;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS decision_email_status VARCHAR(50) DEFAULT 'NOT_SENT' NOT NULL;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS decision_email_error TEXT;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS decision_email_sent_at TIMESTAMP WITH TIME ZONE;
        """,
        """
        ALTER TABLE candidate_assessment_assignments
        ADD COLUMN IF NOT EXISTS brevo_message_id VARCHAR(255);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_caa_review_status ON candidate_assessment_assignments(review_status);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_caa_final_decision ON candidate_assessment_assignments(final_decision);
        """,

        # Columns on assessment_results
        """
        ALTER TABLE assessment_results
        ADD COLUMN IF NOT EXISTS original_marks_obtained INTEGER;
        """,
        """
        ALTER TABLE assessment_results
        ADD COLUMN IF NOT EXISTS is_score_adjusted BOOLEAN DEFAULT FALSE NOT NULL;
        """,
        """
        ALTER TABLE assessment_results
        ADD COLUMN IF NOT EXISTS score_adjustment_reason TEXT;
        """,
        """
        ALTER TABLE assessment_results
        ADD COLUMN IF NOT EXISTS adjusted_by_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE assessment_results
        ADD COLUMN IF NOT EXISTS adjusted_at TIMESTAMP WITH TIME ZONE;
        """,

        # Table assessment_decision_history
        """
        CREATE TABLE IF NOT EXISTS assessment_decision_history (
            id VARCHAR(36) PRIMARY KEY,
            application_id VARCHAR(36) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            assessment_id VARCHAR(36) NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
            assignment_id VARCHAR(36) NOT NULL REFERENCES candidate_assessment_assignments(id) ON DELETE CASCADE,
            attempt_id VARCHAR(36) NOT NULL REFERENCES assessment_attempts(id) ON DELETE CASCADE,
            previous_status VARCHAR(50),
            new_status VARCHAR(50) NOT NULL,
            decision VARCHAR(50) NOT NULL,
            recruiter_id VARCHAR(36) REFERENCES recruiters(id) ON DELETE SET NULL,
            recruiter_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
            reason TEXT,
            remarks TEXT,
            candidate_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_adh_application_id ON assessment_decision_history(application_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_adh_assessment_id ON assessment_decision_history(assessment_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_adh_assignment_id ON assessment_decision_history(assignment_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_adh_attempt_id ON assessment_decision_history(attempt_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_adh_recruiter_user_id ON assessment_decision_history(recruiter_user_id);
        """
    ]

    with engine.begin() as conn:
        for q in queries:
            conn.execute(text(q))
    print("[MIGRATION] Assessment Review & Decision History schema migration completed successfully.")

if __name__ == "__main__":
    migrate()
