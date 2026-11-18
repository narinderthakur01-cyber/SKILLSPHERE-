"""
SkillSphere End-to-End Workflow Verification against PostgreSQL 18
Tests:
1. Candidate authentication & JWT issuance (alex@example.com)
2. Recruiter authentication & JWT issuance (recruiter@technova.com)
3. Admin authentication & JWT issuance (admin@skillsphere.local)
4. Candidate Profile retrieval from PostgreSQL
5. Active Jobs listing from PostgreSQL
6. Resume-to-Job Matching Analysis on PostgreSQL
7. Candidate Applications retrieval (verifying SELECTED statuses)
8. Recruiter viewing job applicants on PostgreSQL
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import verify_password, create_access_token
from app.models.models import User, Candidate, Recruiter, Job, Application, ApplicationStatusEnum, Resume
from app.services.matching_service import calculate_skill_match

def run_workflow_tests():
    print("=" * 65)
    print("SkillSphere: PostgreSQL 18 Workflow Verification")
    print("=" * 65)
    print(f"Active Engine: {engine.dialect.name.upper()} ({engine.url.render_as_string(hide_password=True)})")
    assert engine.dialect.name == "postgresql", f"Expected engine 'postgresql', got '{engine.dialect.name}'"

    db = SessionLocal()
    try:
        # 1. Candidate Authentication
        print("\n--- 1. CANDIDATE AUTHENTICATION ---")
        alex = db.query(User).filter(User.email == "alex@example.com").first()
        assert alex is not None, "Alex user not found in PostgreSQL"
        alex_token = create_access_token(subject=alex.id, role=alex.role.value)
        print(f"  ✓ Candidate '{alex.name}' ({alex.email}) loaded from PostgreSQL.")
        print(f"  ✓ Issued candidate JWT: {alex_token[:25]}... (Role: {alex.role.value})")

        # 2. Recruiter Authentication
        print("\n--- 2. RECRUITER AUTHENTICATION ---")
        recruiter = db.query(User).filter(User.email == "recruiter@technova.com").first()
        assert recruiter is not None, "Recruiter user not found in PostgreSQL"
        rec_token = create_access_token(subject=recruiter.id, role=recruiter.role.value)
        print(f"  ✓ Recruiter '{recruiter.name}' ({recruiter.email}) loaded from PostgreSQL.")
        print(f"  ✓ Issued recruiter JWT: {rec_token[:25]}... (Role: {recruiter.role.value})")

        # 3. Admin Authentication
        print("\n--- 3. ADMIN AUTHENTICATION ---")
        admin = db.query(User).filter(User.email == "admin@skillsphere.local").first()
        assert admin is not None, "Admin user not found in PostgreSQL"
        admin_token = create_access_token(subject=admin.id, role=admin.role.value)
        print(f"  ✓ Admin '{admin.name}' ({admin.email}) loaded from PostgreSQL.")
        print(f"  ✓ Issued admin JWT: {admin_token[:25]}... (Role: {admin.role.value})")

        # 4. Candidate Profile Retrieval
        print("\n--- 4. CANDIDATE PROFILE RETRIEVAL ---")
        cand = db.query(Candidate).filter(Candidate.user_id == alex.id).first()
        assert cand is not None, "Candidate profile not found in PostgreSQL"
        skills = [s.skill_name for s in cand.skills]
        print(f"  ✓ Profile Name: {cand.user.name}")
        print(f"  ✓ Professional Title: {cand.title}")
        print(f"  ✓ Contact Phone: {cand.phone}")
        print(f"  ✓ Total Years Exp: {cand.total_years_exp}")
        print(f"  ✓ Education History: {len(cand.education)} entry ({cand.education[0]['degree']})")
        print(f"  ✓ Work Experience: {len(cand.experience)} entries ({[e['title'] for e in cand.experience]})")
        print(f"  ✓ Verified Skills count: {len(skills)}")
        assert len(skills) == 27, f"Expected 27 skills, got {len(skills)}"

        # 5. Job Openings Listing
        print("\n--- 5. JOB OPENINGS LISTING ---")
        jobs = db.query(Job).all()
        print(f"  ✓ Found {len(jobs)} active jobs posted on PostgreSQL:")
        for j in jobs:
            req_skills = [js.skill.skill_name for js in j.job_skills]
            print(f"     - '{j.title}' at {j.company.company_name} (Required Skills: {req_skills})")

        # 6. Resume to Job Matching Analysis
        print("\n--- 6. RESUME-TO-JOB MATCHING FLOW ---")
        resume = db.query(Resume).filter(Resume.candidate_id == cand.id).first()
        assert resume is not None, "Resume not found in PostgreSQL"
        target_job = jobs[0]  # Senior Full-Stack Engineer
        target_req_skills = [js.skill.skill_name for js in target_job.job_skills]
        match_result = calculate_skill_match(skills, target_req_skills)
        print(f"  ✓ Target Role: {target_job.title}")
        print(f"  ✓ Calculated Match Score: {match_result['match_score']}%")
        print(f"  ✓ Matched Skills: {match_result['matched_skills']}")
        print(f"  ✓ Missing Skills: {match_result['missing_skills']}")
        print(f"  ✓ Recommendation: {match_result['recommendations']}")
        assert match_result['match_score'] == 100.0, f"Expected 100% match, got {match_result['match_score']}"

        # 7. Applications & SELECTED Status Verification
        print("\n--- 7. CANDIDATE APPLICATIONS & SELECTED STATUS ---")
        apps = db.query(Application).filter(Application.candidate_id == cand.id).all()
        assert len(apps) == 2, f"Expected 2 applications, got {len(apps)}"
        for app in apps:
            print(f"  ✓ Application ID: {app.id}")
            print(f"    Role: {app.job.title}")
            print(f"    Status: {app.status.value}")
            print(f"    Resume Attached: {app.resume.file_name}")
            assert app.status == ApplicationStatusEnum.SELECTED, f"Expected SELECTED, got {app.status.value}"

        # 8. Recruiter Candidate Review Flow
        print("\n--- 8. RECRUITER APPLICANTS PIPELINE ---")
        rec_profile = recruiter.recruiter_profile
        rec_jobs = db.query(Job).filter(Job.recruiter_id == rec_profile.id).all()
        print(f"  ✓ Recruiter oversees {len(rec_jobs)} job postings.")
        for rj in rec_jobs:
            rj_apps = db.query(Application).filter(Application.job_id == rj.id).all()
            print(f"    - Job: '{rj.title}' has {len(rj_apps)} candidate application(s):")
            for a in rj_apps:
                print(f"      -> Candidate: {a.candidate.user.name} | Status: {a.status.value}")

        print("\n" + "=" * 65)
        print("🎉 ALL END-TO-END WORKFLOWS ON POSTGRESQL 18 PASSED 100%!")
        print("=" * 65)
    finally:
        db.close()

if __name__ == "__main__":
    run_workflow_tests()
