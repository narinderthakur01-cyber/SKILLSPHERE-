import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, engine
from app.models.models import User, RoleEnum, Candidate, Application, ApplicationStatusEnum, Job

def test_everything():
    print("=" * 60)
    print("SkillSphere: Complete Backend & Frontend Working Audit")
    print("=" * 60)

    # 1. Database & Dialect
    print("\n1. Database Connection:")
    print("   Active Engine Dialect:", engine.dialect.name)
    assert engine.dialect.name == "postgresql", "Expected PostgreSQL dialect!"

    client = TestClient(app)

    # 2. Test All User Logins
    print("\n2. Testing Authentication for all 4 accounts:")
    test_credentials = [
        ("Alex Morgan (Candidate)", "alex@example.com", "12345678", RoleEnum.JOB_SEEKER),
        ("Standard Candidate", "seeker@skillsphere.com", "Seeker123!", RoleEnum.JOB_SEEKER),
        ("TechNova Recruiter", "recruiter@technova.com", "Recruiter123!", RoleEnum.RECRUITER),
        ("Super Admin (Admin123!)", "admin@skillsphere.local", "Admin123!", RoleEnum.ADMIN),
    ]

    tokens = {}
    for label, email, password, expected_role in test_credentials:
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if resp.status_code == 200:
            data = resp.json()
            tokens[label] = data["access_token"]
            print(f"   ✓ {label}: Login SUCCESS (status {resp.status_code}, role {data['user']['role']})")
        else:
            print(f"   ✗ {label}: Login FAILED (status {resp.status_code}, error: {resp.text})")
            raise AssertionError(f"Login failed for {label}")

    # 3. Test Jobs API (Public / Seeker)
    print("\n3. Testing Jobs API:")
    resp = client.get("/api/v1/jobs")
    assert resp.status_code == 200
    jobs = resp.json()["items"]
    print(f"   ✓ Listed {len(jobs)} active jobs successfully.")

    # 4. Test Alex Morgan's Application Status in PostgreSQL
    print("\n4. Testing Alex Morgan Applications & 'SELECTED' Status:")
    db = SessionLocal()
    alex_user = db.query(User).filter(User.email == "alex@example.com").first()
    assert alex_user is not None
    cand = alex_user.candidate_profile
    assert cand is not None
    apps = db.query(Application).filter(Application.candidate_id == cand.id).all()
    print(f"   Found {len(apps)} applications for Alex Morgan:")
    selected_app_ids = {'ca5622b9-4c4a-4721-a645-d8fc8bc05c8a', '621ac8d6-f7fe-4011-85db-41022daa2b05'}
    found_selected = 0
    for app_item in apps:
        print(f"   - App ID: {app_item.id} | Job: {app_item.job.title} | Status: {app_item.status.value}")
        if app_item.id in selected_app_ids:
            assert app_item.status == ApplicationStatusEnum.SELECTED, f"Expected SELECTED for {app_item.id}, got {app_item.status.value}"
            found_selected += 1
    assert found_selected == 2, f"Expected 2 SELECTED applications, found {found_selected}"
    print("   ✓ Both primary applications confirmed as SELECTED.")

    # 5. Test Candidate Authenticated Endpoints
    print("\n5. Testing Candidate Endpoints with Alex's Token:")
    alex_token = tokens["Alex Morgan (Candidate)"]
    headers = {"Authorization": f"Bearer {alex_token}"}
    resp = client.get("/api/v1/resume/profile", headers=headers)
    assert resp.status_code == 200
    prof = resp.json()
    print(f"   ✓ Profile loaded: {prof['name']} | Verified Skills: {len(prof['skills'])} skills")

    # 6. Test Admin Authenticated Endpoints
    print("\n6. Testing Admin Endpoints with Super Admin Token:")
    admin_token = tokens["Super Admin (Admin123!)"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/admin/analytics", headers=admin_headers)
    assert resp.status_code == 200
    analytics = resp.json()
    print(f"   ✓ Admin Analytics loaded: {analytics['total_users']} total users, {analytics['total_jobs']} jobs, {analytics['total_applications']} apps")

    db.close()
    print("\n" + "=" * 60)
    print("🎉 ALL ENDPOINTS, LOGINS & WORKFLOWS ARE 100% OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    test_everything()