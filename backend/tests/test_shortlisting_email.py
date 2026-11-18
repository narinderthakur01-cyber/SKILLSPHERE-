import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    Job, Resume, Application, ApplicationStatusEnum,
    ProcessingStatusEnum, JobStatusEnum, Recruiter, Candidate, User, RoleEnum,
    Assessment, AssessmentStatusEnum, AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAssignmentStatusEnum,
    Notification, AuditLog
)
from app.services.email_service import get_mock_deliveries, clear_mock_deliveries, EmailService

@pytest.fixture(autouse=True)
def clean_mock_emails():
    clear_mock_deliveries()
    yield
    clear_mock_deliveries()

def test_shortlisting_status_triggers_email_and_notification(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    """
    FEATURE A: Recruiter updating candidate application to SHORTLISTED
    triggers Brevo email, candidate in-app notification, and audit log.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    # 1. Setup Job & Resume
    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Senior Backend Engineer",
        description="FastAPI & PostgreSQL backend engineering role.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="resume.pdf",
        file_path="/dummy/resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 2. Candidate applies
    apply_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"resume_id": resume.id, "cover_letter": "Excited to join!"}
    )
    assert apply_resp.status_code == 201
    app_id = apply_resp.json()["id"]

    clear_mock_deliveries()

    # 3. Recruiter updates status to SHORTLISTED
    status_resp = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value, "notes": "Strong system design background."}
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == ApplicationStatusEnum.SHORTLISTED.value

    # Verify Brevo Email was triggered
    deliveries = get_mock_deliveries()
    shortlist_emails = [d for d in deliveries if d.get("email_type") == "SHORTLISTED"]
    assert len(shortlist_emails) == 1
    email = shortlist_emails[0]
    assert email["to_email"] == candidate_user.email
    assert "Congratulations! You Have Been Shortlisted" in email["subject"]
    assert email["metadata"]["job_title"] == job.title
    assert email["metadata"]["has_assessment"] is False

    # Verify In-App Notification created for candidate
    notifs = db.query(Notification).filter(
        Notification.user_id == candidate_user.id,
        Notification.notification_type == "SHORTLISTED"
    ).all()
    assert len(notifs) >= 1
    assert "Shortlisted" in notifs[-1].title

    # Verify Audit Log
    logs = db.query(AuditLog).filter(
        AuditLog.target_resource == "Application",
        AuditLog.target_id == app_id,
        AuditLog.action_type == "APPLICATION_SHORTLISTED"
    ).all()
    assert len(logs) >= 1

def test_shortlisting_idempotency_prevents_duplicate_emails(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    """
    FEATURE A: Submitting SHORTLISTED status repeatedly does NOT send duplicate emails.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Data Engineer",
        description="ETL pipelines and Kafka.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="resume.pdf",
        file_path="/dummy/resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    apply_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"resume_id": resume.id}
    )
    app_id = apply_resp.json()["id"]

    clear_mock_deliveries()

    # First update to SHORTLISTED -> Should send 1 email
    resp1 = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value}
    )
    assert resp1.status_code == 200
    deliveries_1 = [d for d in get_mock_deliveries() if d.get("email_type") == "SHORTLISTED"]
    assert len(deliveries_1) == 1

    # Second update to SHORTLISTED (identical status) -> MUST NOT SEND DUPLICATE EMAIL
    resp2 = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value, "notes": "Re-confirming shortlist"}
    )
    assert resp2.status_code == 200
    deliveries_2 = [d for d in get_mock_deliveries() if d.get("email_type") == "SHORTLISTED"]
    assert len(deliveries_2) == 1, "Duplicate email was unexpectedly dispatched on redundant status update!"

def test_shortlisting_email_includes_assessment_info_when_assigned(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    """
    FEATURE A: When Round 1 assessment has already been assigned for candidate/job,
    the shortlisting email conditionally includes the assessment title, duration, and deadline.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Frontend Specialist",
        description="React & TypeScript.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="resume.pdf",
        file_path="/dummy/resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    apply_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"resume_id": resume.id}
    )
    app_id = apply_resp.json()["id"]

    # Create Assessment for Job
    assessment = Assessment(
        job_id=job.id,
        recruiter_id=recruiter_profile.id,
        title="React & State Management Diagnostic",
        duration_minutes=45,
        total_marks=20,
        passing_marks=14,
        status=AssessmentStatusEnum.PUBLISHED
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Assign assessment to candidate
    deadline = datetime.now(timezone.utc) + timedelta(days=3)
    assignment = CandidateAssessmentAssignment(
        assessment_id=assessment.id,
        candidate_id=candidate_profile.id,
        application_id=app_id,
        assigned_by_user_id=recruiter_user.id,
        status=AssessmentAssignmentStatusEnum.ASSIGNED,
        deadline_at=deadline
    )
    db.add(assignment)
    db.commit()

    clear_mock_deliveries()

    # Recruiter updates status to SHORTLISTED
    resp = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value}
    )
    assert resp.status_code == 200

    # Verify email metadata includes assessment details
    deliveries = [d for d in get_mock_deliveries() if d.get("email_type") == "SHORTLISTED"]
    assert len(deliveries) == 1
    email = deliveries[0]
    assert email["metadata"]["has_assessment"] is True
    assert email["metadata"]["job_title"] == "Frontend Specialist"

def test_email_service_failure_does_not_rollback_status_update(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token, monkeypatch
):
    """
    FEATURE A: Database transaction safety: If email dispatch throws an exception,
    the application status update remains committed and is NOT rolled back.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="DevOps Engineer",
        description="Kubernetes & Terraform.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="resume.pdf",
        file_path="/dummy/resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    apply_resp = client.post(
        f"/api/v1/jobs/{job.id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"resume_id": resume.id}
    )
    app_id = apply_resp.json()["id"]

    # Mock EmailService.send_shortlisting_email to simulate an unhandled network error
    def mock_broken_email(*args, **kwargs):
        raise ConnectionError("Simulated upstream network timeout to Brevo SMTP server")

    monkeypatch.setattr(EmailService, "send_shortlisting_email", mock_broken_email)

    # Recruiter updates status to SHORTLISTED
    resp = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": ApplicationStatusEnum.SHORTLISTED.value}
    )
    # Status update still succeeds cleanly with 200!
    assert resp.status_code == 200
    assert resp.json()["status"] == ApplicationStatusEnum.SHORTLISTED.value

    # Verify the database persisted the status change
    db.expire_all()
    app_record = db.query(Application).filter(Application.id == app_id).first()
    assert app_record.status == ApplicationStatusEnum.SHORTLISTED
