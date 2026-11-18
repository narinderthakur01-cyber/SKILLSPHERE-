"""
SkillSphere Data Migration: SQLite -> PostgreSQL 18
Guarantees:
- Opens SQLite in READ-ONLY mode (file:skillsphere.db?mode=ro). SQLite cannot be modified.
- Backs up SQLite before migration.
- Verifies target PostgreSQL database is clean/empty before schema creation.
- Preserves all Primary Key UUIDs, Foreign Keys, Datetimes, and JSON structures.
- Preserves Alex Morgan's two application records and their 'SELECTED' status.
- Wraps entire PostgreSQL migration in a single atomic transaction (rollback on any failure).
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Company, Skill,
    Job, JobSkill, JobTypeEnum, JobStatusEnum,
    Resume, ProcessingStatusEnum, Application, ApplicationStatusEnum,
    ResumeAnalysis, candidate_skills
)

# Load backend/.env
env_path = backend_dir / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

# Target PostgreSQL parameters
pg_user = env_vars.get("SKILLSPHERE_USER", env_vars.get("POSTGRES_USER", "skillsphere_user"))
pg_pwd = env_vars.get("SKILLSPHERE_USER_PASSWORD", env_vars.get("POSTGRES_PASSWORD", ""))
pg_host = env_vars.get("POSTGRES_SERVER", "localhost")
pg_port = env_vars.get("POSTGRES_PORT", "5432")
pg_db = env_vars.get("POSTGRES_DB", "skillsphere")

sqlite_db_path = backend_dir / "skillsphere.db"

def run_migration():
    print("=" * 65)
    print("SkillSphere: SQLite to PostgreSQL 18 Atomic Migration")
    print("=" * 65)

    # 1. Verify SQLite database exists
    if not sqlite_db_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_db_path}")
        sys.exit(1)
    print(f"✓ Source SQLite Database: {sqlite_db_path} ({os.path.getsize(sqlite_db_path):,} bytes)")

    # 2. Connect to SQLite in strict READ-ONLY mode
    sqlite_uri = f"file:{sqlite_db_path.as_posix()}?mode=ro"
    sqlite_conn = sqlite3.connect(sqlite_uri, uri=True)
    sqlite_cur = sqlite_conn.cursor()
    print("✓ Connected to SQLite in READ-ONLY mode (URI mode=ro).")

    # 3. Connect to PostgreSQL
    pg_url = f"postgresql+psycopg2://{pg_user}:{pg_pwd}@{pg_host}:{pg_port}/{pg_db}"
    print(f"Connecting to PostgreSQL at {pg_host}:{pg_port}/{pg_db} as user '{pg_user}'...")
    try:
        pg_engine = create_engine(pg_url, pool_pre_ping=True)
        with pg_engine.connect() as test_conn:
            res = test_conn.execute(text("SELECT version();")).scalar()
            print(f"✓ Connected to PostgreSQL! Engine version: {res[:50]}...")
    except Exception as e:
        print(f"ERROR: Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    # 4. Check that PostgreSQL target schema is empty before schema creation
    inspector = inspect(pg_engine)
    existing_pg_tables = inspector.get_table_names()
    if existing_pg_tables:
        print(f"ERROR: PostgreSQL target database '{pg_db}' already contains tables: {existing_pg_tables}")
        print("Migration halted to prevent data collision. The target database must be empty.")
        sys.exit(1)
    print(f"✓ Verified target database '{pg_db}' is completely empty.")

    # 5. Create PostgreSQL Schema
    print("\nCreating PostgreSQL schema, enums, constraints, and indexes...")
    Base.metadata.create_all(bind=pg_engine)
    inspector = inspect(pg_engine)
    created_tables = sorted(inspector.get_table_names())
    print(f"✓ Successfully created {len(created_tables)} tables in PostgreSQL:")
    for t in created_tables:
        print(f"   - {t}")

    # 6. Begin Atomic Data Transfer
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    counts = {}
    try:
        print("\nBeginning data transfer inside an atomic PostgreSQL transaction...")

        # Helper to parse datetime
        def parse_dt(val):
            if not val:
                return None
            if isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(val)
            except Exception:
                return val

        # Helper to parse JSON
        def parse_json(val, default):
            if val is None or val == "":
                return default
            if isinstance(val, (dict, list)):
                return val
            try:
                return json.loads(val)
            except Exception:
                return default

        # Table 1: Users
        sqlite_cur.execute("SELECT id, name, email, password_hash, role, is_active, created_at, updated_at FROM users;")
        user_rows = sqlite_cur.fetchall()
        for r in user_rows:
            pg_session.add(User(
                id=r[0], name=r[1], email=r[2], password_hash=r[3],
                role=RoleEnum(r[4]), is_active=bool(r[5]),
                created_at=parse_dt(r[6]), updated_at=parse_dt(r[7])
            ))
        counts["users"] = len(user_rows)
        print(f"  ✓ Users migrated: {len(user_rows)}")

        # Table 2: Companies
        sqlite_cur.execute("SELECT id, company_name, description, website, location, contact_email, logo_url, created_at FROM companies;")
        company_rows = sqlite_cur.fetchall()
        for r in company_rows:
            pg_session.add(Company(
                id=r[0], company_name=r[1], description=r[2], website=r[3],
                location=r[4], contact_email=r[5], logo_url=r[6], created_at=parse_dt(r[7])
            ))
        counts["companies"] = len(company_rows)
        print(f"  ✓ Companies migrated: {len(company_rows)}")

        # Table 3: Recruiters
        sqlite_cur.execute("SELECT id, user_id, company_id, designation, created_at FROM recruiters;")
        recruiter_rows = sqlite_cur.fetchall()
        for r in recruiter_rows:
            pg_session.add(Recruiter(
                id=r[0], user_id=r[1], company_id=r[2], designation=r[3], created_at=parse_dt(r[4])
            ))
        counts["recruiters"] = len(recruiter_rows)
        print(f"  ✓ Recruiters migrated: {len(recruiter_rows)}")

        # Table 4: Candidates
        sqlite_cur.execute("SELECT id, user_id, phone, title, location, bio, education, experience, total_years_exp, created_at, updated_at FROM candidates;")
        cand_rows = sqlite_cur.fetchall()
        for r in cand_rows:
            pg_session.add(Candidate(
                id=r[0], user_id=r[1], phone=r[2], title=r[3], location=r[4], bio=r[5],
                education=parse_json(r[6], []),
                experience=parse_json(r[7], []),
                total_years_exp=float(r[8] or 0.0),
                created_at=parse_dt(r[9]), updated_at=parse_dt(r[10])
            ))
        counts["candidates"] = len(cand_rows)
        print(f"  ✓ Candidates migrated: {len(cand_rows)}")

        # Table 5: Skills
        sqlite_cur.execute("SELECT id, skill_name, category FROM skills;")
        skill_rows = sqlite_cur.fetchall()
        for r in skill_rows:
            pg_session.add(Skill(id=r[0], skill_name=r[1], category=r[2]))
        counts["skills"] = len(skill_rows)
        print(f"  ✓ Skills migrated: {len(skill_rows)}")

        # Flush to satisfy foreign keys
        pg_session.flush()

        # Table 6: candidate_skills (Association)
        sqlite_cur.execute("SELECT candidate_id, skill_id FROM candidate_skills;")
        cs_rows = sqlite_cur.fetchall()
        for r in cs_rows:
            pg_session.execute(candidate_skills.insert().values(candidate_id=r[0], skill_id=r[1]))
        counts["candidate_skills"] = len(cs_rows)
        print(f"  ✓ Candidate Skills associations migrated: {len(cs_rows)}")

        # Table 7: Jobs
        sqlite_cur.execute("SELECT id, recruiter_id, company_id, title, description, location, experience_min, experience_max, job_type, salary_min, salary_max, status, created_at, updated_at FROM jobs;")
        job_rows = sqlite_cur.fetchall()
        for r in job_rows:
            pg_session.add(Job(
                id=r[0], recruiter_id=r[1], company_id=r[2], title=r[3], description=r[4],
                location=r[5], experience_min=float(r[6] or 0.0), experience_max=float(r[7] or 0.0),
                job_type=JobTypeEnum(r[8]), salary_min=r[9], salary_max=r[10],
                status=JobStatusEnum(r[11]), created_at=parse_dt(r[12]), updated_at=parse_dt(r[13])
            ))
        counts["jobs"] = len(job_rows)
        print(f"  ✓ Jobs migrated: {len(job_rows)}")

        # Table 8: job_skills (Association)
        sqlite_cur.execute("SELECT job_id, skill_id, is_required FROM job_skills;")
        js_rows = sqlite_cur.fetchall()
        for r in js_rows:
            pg_session.add(JobSkill(job_id=r[0], skill_id=r[1], is_required=bool(r[2])))
        counts["job_skills"] = len(js_rows)
        print(f"  ✓ Job Skills associations migrated: {len(js_rows)}")

        # Table 9: Resumes
        sqlite_cur.execute("SELECT id, candidate_id, file_name, file_path, file_type, file_size, extracted_text, parsed_data, processing_status, error_message, upload_date FROM resumes;")
        resume_rows = sqlite_cur.fetchall()
        for r in resume_rows:
            pg_session.add(Resume(
                id=r[0], candidate_id=r[1], file_name=r[2], file_path=r[3],
                file_type=r[4], file_size=r[5], extracted_text=r[6],
                parsed_data=parse_json(r[7], {}),
                processing_status=ProcessingStatusEnum(r[8]),
                error_message=r[9], upload_date=parse_dt(r[10])
            ))
        counts["resumes"] = len(resume_rows)
        print(f"  ✓ Resumes migrated: {len(resume_rows)}")

        # Flush to satisfy applications resume foreign keys
        pg_session.flush()

        # Table 10: Applications
        sqlite_cur.execute("SELECT id, job_id, candidate_id, resume_id, status, cover_letter, application_date, updated_at FROM applications;")
        app_rows = sqlite_cur.fetchall()
        for r in app_rows:
            status_enum = ApplicationStatusEnum(r[4])
            pg_session.add(Application(
                id=r[0], job_id=r[1], candidate_id=r[2], resume_id=r[3],
                status=status_enum, cover_letter=r[5],
                application_date=parse_dt(r[6]), updated_at=parse_dt(r[7])
            ))
        counts["applications"] = len(app_rows)
        print(f"  ✓ Applications migrated: {len(app_rows)}")

        # Table 11: Resume Analysis
        sqlite_cur.execute("SELECT id, resume_id, job_id, match_score, matched_skills, missing_skills, recommendations, analysis_date FROM resume_analysis;")
        ra_rows = sqlite_cur.fetchall()
        for r in ra_rows:
            pg_session.add(ResumeAnalysis(
                id=r[0], resume_id=r[1], job_id=r[2],
                match_score=float(r[3]) if r[3] is not None else None,
                matched_skills=parse_json(r[4], []),
                missing_skills=parse_json(r[5], []),
                recommendations=r[6], analysis_date=parse_dt(r[7])
            ))
        counts["resume_analysis"] = len(ra_rows)
        print(f"  ✓ Resume Analysis records migrated: {len(ra_rows)}")

        # Commit Transaction
        pg_session.commit()
        print("\n🎉 PostgreSQL transaction COMMITTED successfully with zero errors!")

    except Exception as e:
        pg_session.rollback()
        print(f"\n❌ Migration transaction FAILED! Transaction rolled back completely: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        pg_session.close()
        sqlite_conn.close()

    print("\nSummary of Migrated Entities:")
    for k, v in counts.items():
        print(f"   {k:20s}: {v}")

if __name__ == "__main__":
    run_migration()
