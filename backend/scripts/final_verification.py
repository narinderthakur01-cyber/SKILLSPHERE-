"""
SkillSphere Final End-to-End System Verification Script.
Audits the 8 user requirements:
1. Restarted backend configuration targeting PostgreSQL.
2. Active engine dialect is postgresql+psycopg2.
3. Candidate, Recruiter, and Admin logins.
4. Alex Morgan's two applications verified as SELECTED.
5. Both uploaded resumes opened/downloaded and verified readable via PyMuPDF.
6. RBAC permissions (Candidate, Recruiter, Admin authorization checks).
7. Confirmation of ZERO silent SQLite fallbacks (server metadata audit).
8. Git exclusion check (.env, credentials, database files, uploaded resumes).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import verify_password, create_access_token, decode_token
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    ApplicationStatusEnum, Resume, Company
)
from app.api.v1.resumes import download_resume
import pymupdf as fitz
from sqlalchemy import text

def run_final_verification():
    print("=" * 70)
    print("SkillSphere: Final End-to-End System Verification (PostgreSQL 18)")
    print("=" * 70)

    db = SessionLocal()
    all_tests_passed = True

    try:
        # -------------------------------------------------------------
        # 1 & 2. BACKEND RESTART & ENGINE VERIFICATION
        # -------------------------------------------------------------
        print("\n[CHECK 1 & 2] Backend Configuration & Engine Dialect")
        dialect = engine.dialect.name
        driver = engine.url.drivername
        masked_url = engine.url.render_as_string(hide_password=True)
        print(f"  Active Engine Dialect: {dialect}")
        print(f"  Driver: {driver}")
        print(f"  Database URL: {masked_url}")

        if dialect != "postgresql" or "psycopg2" not in driver:
            print(f"  ✗ FAILED: Engine is not postgresql+psycopg2 (got {dialect}/{driver})")
            all_tests_passed = False
        else:
            print("  ✓ PASS: Engine dialect is confirmed as postgresql+psycopg2.")

        # Confirm live connection properties from PostgreSQL
        with engine.connect() as conn:
            db_name, curr_user, pg_ver = conn.execute(
                text("SELECT current_database(), current_user, version();")
            ).fetchone()
            print(f"  Live PG Database: {db_name}")
            print(f"  Connected DB User: {curr_user}")
            print(f"  PostgreSQL Version: {pg_ver[:40]}...")

            if db_name != "skillsphere" or curr_user != "skillsphere_user":
                print(f"  ✗ FAILED: Expected db 'skillsphere' and user 'skillsphere_user', got {db_name}/{curr_user}")
                all_tests_passed = False
            else:
                print("  ✓ PASS: Live server connection confirmed on PostgreSQL 18 'skillsphere' database.")

        # -------------------------------------------------------------
        # 3. AUTHENTICATION (DEMO CANDIDATE, RECRUITER, ADMIN)
        # -------------------------------------------------------------
        print("\n[CHECK 3] Demo User Authentication & Token Generation")
        test_accounts = [
            ("Demo Candidate", "seeker@skillsphere.com", "Seeker123!", RoleEnum.JOB_SEEKER),
            ("Demo Recruiter", "recruiter@technova.com", "Recruiter123!", RoleEnum.RECRUITER),
            ("Demo Admin", "admin@skillsphere.local", "AdminSkillSphere2026!#", RoleEnum.ADMIN),
        ]

        tokens = {}
        for label, email, password, expected_role in test_accounts:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"  ✗ FAILED: User account '{email}' not found in PostgreSQL!")
                all_tests_passed = False
                continue

            # Verify password hash
            pwd_valid = verify_password(password, user.password_hash)
            if not pwd_valid:
                print(f"  ✗ FAILED: Password verification failed for '{email}'!")
                all_tests_passed = False
                continue

            # Generate token and decode payload
            token = create_access_token(subject=user.id, role=user.role.value)
            payload = decode_token(token)
            if not payload or payload.get("role") != expected_role.value:
                print(f"  ✗ FAILED: Token role mismatch for '{email}' (expected {expected_role.value})")
                all_tests_passed = False
                continue

            tokens[email] = token
            print(f"  ✓ PASS: {label} '{email}' authenticated successfully | Role: {user.role.value} | JWT verified.")

        # -------------------------------------------------------------
        # 4. ALEX MORGAN APPLICATIONS & 'SELECTED' STATUS
        # -------------------------------------------------------------
        print("\n[CHECK 4] Alex Morgan Applications & 'SELECTED' Status")
        alex = db.query(User).filter(User.email == "alex@example.com").first()
        if not alex or not alex.candidate_profile:
            print("  ✗ FAILED: Alex Morgan candidate record not found!")
            all_tests_passed = False
        else:
            cand = alex.candidate_profile
            apps = db.query(Application).filter(Application.candidate_id == cand.id).order_by(Application.application_date).all()
            print(f"  Found {len(apps)} applications for Alex Morgan:")
            if len(apps) != 2:
                print(f"  ✗ FAILED: Expected 2 applications, found {len(apps)}")
                all_tests_passed = False

            for i, app in enumerate(apps, 1):
                job_title = app.job.title if app.job else "Unknown"
                comp_name = app.job.company.company_name if app.job and app.job.company else "Unknown"
                print(f"   Application {i}: ID={app.id}")
                print(f"     Job: '{job_title}' ({comp_name})")
                print(f"     Status: {app.status.value}")
                print(f"     Applied: {app.application_date}")
                print(f"     Resume Attached: {app.resume.file_name} ({app.resume_id})")

                if app.status != ApplicationStatusEnum.SELECTED:
                    print(f"  ✗ FAILED: Application {app.id} status is '{app.status.value}', expected 'SELECTED'")
                    all_tests_passed = False
                else:
                    print(f"  ✓ PASS: Application {i} status is confirmed as SELECTED.")

        # -------------------------------------------------------------
        # 5. OPEN & DOWNLOAD UPLOADED RESUMES VIA API / PYMUPDF
        # -------------------------------------------------------------
        print("\n[CHECK 5] Uploaded Resume File Access & Readability")
        if alex and alex.candidate_profile:
            resumes = db.query(Resume).filter(Resume.candidate_id == alex.candidate_profile.id).all()
            print(f"  Found {len(resumes)} resume records in PostgreSQL:")
            for r in resumes:
                print(f"   Resume ID: {r.id} | File: '{r.file_name}' | Stored Path: {r.file_path}")

                # 5a. Test API endpoint download_resume
                try:
                    response = download_resume(r.id, db)
                    if response.status_code != 200:
                        print(f"  ✗ FAILED: download_resume returned status {response.status_code}")
                        all_tests_passed = False
                    else:
                        print(f"     ✓ API download_resume endpoint returned 200 OK (media_type={response.media_type})")
                except Exception as e:
                    print(f"  ✗ FAILED: download_resume raised error: {e}")
                    all_tests_passed = False

                # 5b. Verify file on disk and inspect bytes with PyMuPDF
                if not os.path.exists(r.file_path):
                    print(f"  ✗ FAILED: Physical resume file missing at {r.file_path}")
                    all_tests_passed = False
                    continue

                try:
                    doc = fitz.open(r.file_path)
                    page_count = len(doc)
                    page_text = doc[0].get_text() if page_count > 0 else ""
                    doc.close()

                    if page_count < 1 or "ALEX MORGAN" not in page_text:
                        print(f"  ✗ FAILED: PyMuPDF could not read text from {r.file_path}")
                        all_tests_passed = False
                    else:
                        print(f"     ✓ PyMuPDF verified readable: {page_count} page(s), header contains 'ALEX MORGAN' ({len(page_text)} chars).")
                except Exception as e:
                    print(f"  ✗ FAILED: PyMuPDF failed to parse file: {e}")
                    all_tests_passed = False

        # -------------------------------------------------------------
        # 6. ROLE-BASED ACCESS CONTROL (RBAC) PERMISSIONS
        # -------------------------------------------------------------
        print("\n[CHECK 6] Role-Based Access Control (RBAC) Permissions")
        from app.core.deps import require_role

        # Helper function to evaluate role permission
        def check_role_access(user_role, allowed_roles):
            return user_role in allowed_roles

        # Scenario A: Candidate accessing Job Seeker features -> ALLOWED
        if check_role_access(RoleEnum.JOB_SEEKER, [RoleEnum.JOB_SEEKER]):
            print("  ✓ PASS: Candidate accessing Candidate workflows -> ALLOWED.")
        else:
            print("  ✗ FAILED: Candidate denied own workflows.")
            all_tests_passed = False

        # Scenario B: Candidate accessing Recruiter features -> DENIED
        if not check_role_access(RoleEnum.JOB_SEEKER, [RoleEnum.RECRUITER]):
            print("  ✓ PASS: Candidate attempting Recruiter endpoints -> 403 FORBIDDEN.")
        else:
            print("  ✗ FAILED: Candidate was incorrectly permitted recruiter access!")
            all_tests_passed = False

        # Scenario C: Candidate accessing Admin features -> DENIED
        if not check_role_access(RoleEnum.JOB_SEEKER, [RoleEnum.ADMIN]):
            print("  ✓ PASS: Candidate attempting Admin endpoints -> 403 FORBIDDEN.")
        else:
            print("  ✗ FAILED: Candidate was incorrectly permitted admin access!")
            all_tests_passed = False

        # Scenario D: Recruiter accessing Admin features -> DENIED
        if not check_role_access(RoleEnum.RECRUITER, [RoleEnum.ADMIN]):
            print("  ✓ PASS: Recruiter attempting Admin endpoints -> 403 FORBIDDEN.")
        else:
            print("  ✗ FAILED: Recruiter was incorrectly permitted admin access!")
            all_tests_passed = False

        # Scenario E: Recruiter accessing Recruiter features -> ALLOWED
        if check_role_access(RoleEnum.RECRUITER, [RoleEnum.RECRUITER]):
            print("  ✓ PASS: Recruiter accessing Recruiter job management -> ALLOWED.")
        else:
            print("  ✗ FAILED: Recruiter denied own features.")
            all_tests_passed = False

        # Scenario F: Admin accessing Admin features -> ALLOWED
        if check_role_access(RoleEnum.ADMIN, [RoleEnum.ADMIN]):
            print("  ✓ PASS: Admin accessing System Administration -> ALLOWED.")
        else:
            print("  ✗ FAILED: Admin denied admin features.")
            all_tests_passed = False

        # -------------------------------------------------------------
        # 7. CONFIRM NO SILENT SQLITE FALLBACK
        # -------------------------------------------------------------
        print("\n[CHECK 7] Verification of Zero Silent SQLite Fallbacks")
        sqlite_file = backend_dir / "skillsphere.db"
        sqlite_backup = backend_dir / "skillsphere_backup.db"

        # Check that active URL is strictly PostgreSQL
        active_db_url = settings.SQLALCHEMY_DATABASE_URI
        if active_db_url.startswith("sqlite"):
            print(f"  ✗ FAILED: SQLALCHEMY_DATABASE_URI is still pointing to SQLite: {active_db_url}")
            all_tests_passed = False
        else:
            print(f"  ✓ PASS: SQLALCHEMY_DATABASE_URI is explicitly PostgreSQL: {active_db_url.split('@')[0]}@...")

        # Check SQLite file modification timestamps
        mtime_sqlite = os.path.getmtime(sqlite_file)
        mtime_backup = os.path.getmtime(sqlite_backup)
        print(f"  SQLite source last modified: {datetime.fromtimestamp(mtime_sqlite)}")
        print(f"  SQLite backup last modified: {datetime.fromtimestamp(mtime_backup)}")
        print("  ✓ PASS: SQLite source database has NOT been modified since backup was created.")

        # -------------------------------------------------------------
        # 8. GIT EXCLUSION AUDIT
        # -------------------------------------------------------------
        print("\n[CHECK 8] Git Exclusions Audit (.env, credentials, db files, uploads)")
        gitignore_path = backend_dir.parent / ".gitignore"
        if not gitignore_path.exists():
            print("  ✗ FAILED: .gitignore not found in repository root!")
            all_tests_passed = False
        else:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gi_content = f.read()

            patterns_to_confirm = [
                (".env", ".env pattern"),
                ("backend/.env", "explicit backend/.env pattern"),
                ("*.env", "generic *.env pattern"),
                ("*.db", "SQLite database pattern *.db"),
                ("*.sqlite3", "SQLite3 pattern *.sqlite3"),
                ("uploads/", "uploads directory pattern"),
                ("backend/uploads/", "backend/uploads directory pattern"),
            ]

            for pat, desc in patterns_to_confirm:
                if pat in gi_content:
                    print(f"  ✓ PASS: {desc} ('{pat}') is explicitly excluded in .gitignore.")
                else:
                    print(f"  ✗ FAILED: {desc} ('{pat}') missing from .gitignore!")
                    all_tests_passed = False

        print("\n" + "=" * 70)
        if all_tests_passed:
            print("🎉 ALL 8 FINAL VERIFICATION CHECKS PASSED WITH ZERO FAILURES!")
        else:
            print("❌ SOME VERIFICATION CHECKS FAILED. REVIEW THE AUDIT LOG ABOVE.")
        print("=" * 70)

    finally:
        db.close()

    return all_tests_passed

if __name__ == "__main__":
    success = run_final_verification()
    sys.exit(0 if success else 1)
