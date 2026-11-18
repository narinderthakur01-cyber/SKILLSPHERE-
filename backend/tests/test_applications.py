from datetime import datetime, timezone
from app.models.models import (
    Job, Skill, JobSkill, Resume, Application, ApplicationStatusEnum,
    ProcessingStatusEnum, JobStatusEnum, Recruiter, User, RoleEnum
)
from app.core.security import get_password_hash, create_access_token

def test_application_lifecycle_and_duplicate_prevention(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    # 1. Create a Job posted by recruiter
    recruiter_profile = recruiter_user.recruiter_profile
    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Full Stack Engineer",
        description="Build scalable applications using FastAPI and React.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 2. Create a Resume for Candidate
    candidate_profile = candidate_user.candidate_profile
    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="resume.pdf",
        file_path="/dummy/path/resume.pdf",
        file_type="application/pdf",
        file_size=1024,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 3. Candidate applies to the job
    apply_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "resume_id": resume.id,
            "cover_letter": "I am excited to apply for this engineering role."
        }
    )
    assert apply_resp.status_code == 201
    app_data = apply_resp.json()
    assert app_data["status"] == ApplicationStatusEnum.APPLIED.value
    application_id = app_data["id"]

    # 4. DUPLICATE APPLICATION CHECK: Candidate applies again to same job -> MUST FAIL WITH 400
    dup_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "resume_id": resume.id,
            "cover_letter": "Trying to apply again."
        }
    )
    assert dup_resp.status_code == 400
    assert "already submitted an active application" in dup_resp.json()["detail"]

    # 5. Candidate views their applications
    my_apps_resp = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert my_apps_resp.status_code == 200
    apps_list = my_apps_resp.json()
    assert len(apps_list) == 1
    assert apps_list[0]["id"] == application_id

    # 6. Recruiter views applicants for this job
    recruiter_apps_resp = client.get(
        f"/api/v1/recruiter/applicants?job_id={job.id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert recruiter_apps_resp.status_code == 200
    recruiter_apps = recruiter_apps_resp.json()
    assert len(recruiter_apps) == 1
    assert recruiter_apps[0]["id"] == application_id

    # 7. Recruiter advances applicant status to SHORTLISTED
    status_update_resp = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value}
    )
    assert status_update_resp.status_code == 200
    assert status_update_resp.json()["status"] == ApplicationStatusEnum.SHORTLISTED.value

    # 8. Another recruiter attempts to modify status -> MUST FAIL WITH 403 FORBIDDEN
    other_recruiter = User(
        name="Other Recruiter",
        email="other@recruiter.com",
        password_hash=get_password_hash("Pass123!"),
        role=RoleEnum.RECRUITER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    db.add(other_recruiter)
    db.commit()
    db.refresh(other_recruiter)
    other_profile = Recruiter(user_id=other_recruiter.id)
    db.add(other_profile)
    db.commit()
    other_token = create_access_token(subject=other_recruiter.id, role=other_recruiter.role.value)

    unauth_resp = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"status": ApplicationStatusEnum.REJECTED.value}
    )
    assert unauth_resp.status_code == 403
    assert "Forbidden" in unauth_resp.json()["detail"]

    # 9. Candidate withdraws application
    withdraw_resp = client.put(
        f"/api/v1/applications/{application_id}/withdraw",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.json()["status"] == ApplicationStatusEnum.WITHDRAWN.value
