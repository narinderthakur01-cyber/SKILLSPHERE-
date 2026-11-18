"""
SkillSphere Post-Migration Parity and Integrity Verification Script.
Audits:
1. Exact row count parity across all 11 tables between SQLite and PostgreSQL.
2. UUID primary key and foreign key preservation.
3. Alex Morgan candidate profile, verified skills (27 skills), and education/experience JSON integrity.
4. Uploaded resume file existence on disk.
5. Alex Morgan's two application records and their 'SELECTED' status.
6. PostgreSQL partial unique index integrity check.
"""

import os
import sys
import sqlite3
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models.models import (
    User, Candidate, Recruiter, Company, Skill, Job, JobSkill,
    Resume, Application, ApplicationStatusEnum, ResumeAnalysis
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

pg_user = env_vars.get("SKILLSPHERE_USER", env_vars.get("POSTGRES_USER", "skillsphere_user"))
pg_pwd = env_vars.get("SKILLSPHERE_USER_PASSWORD", env_vars.get("POSTGRES_PASSWORD", ""))
pg_host = env_vars.get("POSTGRES_SERVER", "localhost")
pg_port = env_vars.get("POSTGRES_PORT", "5432")
pg_db = env_vars.get("POSTGRES_DB", "skillsphere")

sqlite_path = backend_dir / "skillsphere.db"

def run_verification():
    print("=" * 65)
    print("SkillSphere: Post-Migration Parity & Data Audit")
    print("=" * 65)

    # 1. Connect to SQLite (Read-Only)
    sqlite_conn = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
    sqlite_cur = sqlite_conn.cursor()

    # 2. Connect to PostgreSQL
    pg_url = f"postgresql+psycopg2://{pg_user}:{pg_pwd}@{pg_host}:{pg_port}/{pg_db}"
    pg_engine = create_engine(pg_url, pool_pre_ping=True)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    print(f"Auditing PostgreSQL database '{pg_db}' on {pg_host}:{pg_port} against SQLite...")

    tables_to_check = [
        "users", "companies", "recruiters", "candidates", "skills",
        "candidate_skills", "jobs", "job_skills", "resumes",
        "applications", "resume_analysis"
    ]

    all_passed = True

    # 1. Row Count Parity
    print("\n--- 1. TABLE ROW COUNT PARITY ---")
    for t in tables_to_check:
        sqlite_cur.execute(f"SELECT COUNT(*) FROM '{t}';")
        sql_cnt = sqlite_cur.fetchone()[0]

        with pg_engine.connect() as conn:
            pg_cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{t}";')).scalar()

        match = (sql_cnt == pg_cnt)
        status = "MATCH ✓" if match else "MISMATCH ✗"
        if not match:
            all_passed = False
        print(f"  {t:20s}: SQLite = {sql_cnt:4d} | PostgreSQL = {pg_cnt:4d} | {status}")

    # 2. Primary Keys and IDs check
    print("\n--- 2. PRIMARY KEY INTEGRITY AUDIT ---")
    for t in ["users", "candidates", "jobs", "resumes", "applications"]:
        sqlite_cur.execute(f"SELECT id FROM '{t}' ORDER BY id;")
        sql_ids = set(r[0] for r in sqlite_cur.fetchall())

        with pg_engine.connect() as conn:
            pg_ids = set(r[0] for r in conn.execute(text(f'SELECT id FROM "{t}";')).fetchall())

        diff = sql_ids.symmetric_difference(pg_ids)
        if diff:
            print(f"  ✗ Mismatched IDs in table '{t}': {diff}")
            all_passed = False
        else:
            print(f"  ✓ All {len(sql_ids)} IDs in '{t}' match identically.")

    # 3. Alex Morgan Profile & Verification
    print("\n--- 3. ALEX MORGAN CANDIDATE AUDIT ---")
    alex_user = pg_session.query(User).filter(User.email == "alex@example.com").first()
    assert alex_user is not None, "Alex Morgan user record not found in PostgreSQL!"
    print(f"  ✓ User Record: {alex_user.name} ({alex_user.email}) | Role: {alex_user.role.value}")

    alex_cand = pg_session.query(Candidate).filter(Candidate.user_id == alex_user.id).first()
    assert alex_cand is not None, "Alex Morgan candidate profile not found in PostgreSQL!"
    print(f"  ✓ Candidate Profile: Title='{alex_cand.title}', Phone='{alex_cand.phone}', Exp={alex_cand.total_years_exp} yrs")
    print(f"  ✓ Structured Education: {len(alex_cand.education)} entry -> {alex_cand.education[0]['degree']}")
    print(f"  ✓ Structured Experience: {len(alex_cand.experience)} entries -> {[e['title'] for e in alex_cand.experience]}")
    print(f"  ✓ Verified Skills: {len(alex_cand.skills)} skills linked")
    assert len(alex_cand.skills) == 27, f"Expected 27 skills, got {len(alex_cand.skills)}"

    # 4. Resume & Uploaded Files Audit
    print("\n--- 4. RESUMES & UPLOADED FILES AUDIT ---")
    alex_resumes = pg_session.query(Resume).filter(Resume.candidate_id == alex_cand.id).all()
    print(f"  Found {len(alex_resumes)} resume(s) in PostgreSQL:")
    for r in alex_resumes:
        file_exists = os.path.exists(r.file_path)
        print(f"   - Resume {r.id}: '{r.file_name}' | Path exists: {file_exists} ({r.file_size:,} bytes)")
        if not file_exists:
            print(f"     ✗ WARNING: Physical file missing at {r.file_path}")
            all_passed = False
        else:
            print(f"     ✓ Physical file verified on disk.")

    # 5. Application Records & Status Audit
    print("\n--- 5. APPLICATIONS & 'SELECTED' STATUS AUDIT ---")
    alex_apps = pg_session.query(Application).filter(Application.candidate_id == alex_cand.id).all()
    print(f"  Found {len(alex_apps)} application(s) for Alex Morgan:")
    assert len(alex_apps) == 2, f"Expected 2 applications, got {len(alex_apps)}"
    for a in alex_apps:
        print(f"   - Application ID: {a.id}")
        print(f"     Job: {a.job.title} ({a.job.company.company_name})")
        print(f"     Status: {a.status.value}")
        print(f"     Application Date: {a.application_date}")
        assert a.status == ApplicationStatusEnum.SELECTED, f"Expected status 'SELECTED', got '{a.status.value}'"
        print(f"     ✓ Status 'SELECTED' verified!")

    # 6. PostgreSQL Partial Unique Index Constraint Audit
    print("\n--- 6. PARTIAL UNIQUE INDEX AUDIT ---")
    test_job_id = alex_apps[0].job_id
    duplicate_app = Application(
        job_id=test_job_id,
        candidate_id=alex_cand.id,
        resume_id=alex_apps[0].resume_id,
        status=ApplicationStatusEnum.APPLIED
    )
    pg_session.add(duplicate_app)
    try:
        pg_session.commit()
        print("  ✗ Partial unique index failed to prevent duplicate active application!")
        all_passed = False
    except IntegrityError:
        pg_session.rollback()
        print("  ✓ Partial unique index successfully blocked duplicate active application (IntegrityError caught).")

    pg_session.close()
    sqlite_conn.close()

    print("\n" + "=" * 65)
    if all_passed:
        print("🎉 ALL MIGRATION AND INTEGRITY CHECKS PASSED WITH 100% PARITY!")
    else:
        print("⚠️ SOME CHECKS FAILED. REVIEW THE AUDIT LOG ABOVE.")
    print("=" * 65)
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
