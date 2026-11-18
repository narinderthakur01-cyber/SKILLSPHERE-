import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.models.models import (
    Job, Resume, Application, ApplicationStatusEnum,
    ProcessingStatusEnum, JobStatusEnum, Recruiter, Candidate, User, RoleEnum,
    Interview, Notification, AuditLog
)
from app.services.email_service import get_mock_deliveries, clear_mock_deliveries, EmailService

@pytest.fixture(autouse=True)
def clean_mock_emails():
    clear_mock_deliveries()
    yield
    clear_mock_deliveries()

def test_schedule_interview_dispatches_email_and_tracks_status(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    """
    PART A: Scheduling an interview triggers:
    1. Transactional email dispatch via Brevo EmailService.
    2. Tracking of email_status ('ACCEPTED_BY_BREVO') and brevo_message_id on Interview model.
    3. Creation of candidate in-app notification and audit trail.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Full Stack Architect",
        description="Lead engineering role for SkillSphere platform.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="architect_resume.pdf",
        file_path="/dummy/architect_resume.pdf",
        file_type="application/pdf",
        file_size=4096,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    clear_mock_deliveries()

    sched_time = datetime.now(timezone.utc) + timedelta(days=2)
    payload = {
        "application_id": app_record.id,
        "interview_type": "ONLINE",
        "scheduled_time": sched_time.isoformat(),
        "duration_minutes": 60,
        "meeting_link": "https://meet.google.com/xyz-uvw-rst",
        "instructions": "Please prepare a 10-minute presentation on system design."
    }

    resp = client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=payload
    )

    assert resp.status_code == 201
    data = resp.json()
    interview_id = data["id"]
    assert data["status"] == "SCHEDULED"
    assert data["email_status"] == "ACCEPTED_BY_BREVO"
    assert data["brevo_message_id"] is not None

    # Check mock email dispatch
    deliveries = get_mock_deliveries()
    inv_emails = [d for d in deliveries if d.get("email_type") == "INTERVIEW_INVITATION"]
    assert len(inv_emails) == 1
    email = inv_emails[0]
    assert email["to_email"] == candidate_user.email
    assert "Interview Invitation — Full Stack Architect | SkillSphere" in email["subject"]
    assert email["metadata"]["job_title"] == "Full Stack Architect"

    # Check candidate in-app notification
    notifs = db.query(Notification).filter(
        Notification.user_id == candidate_user.id,
        Notification.notification_type == "INTERVIEW_SCHEDULED"
    ).all()
    assert len(notifs) >= 1
    assert "Interview Scheduled" in notifs[-1].title

    # Check database state directly
    inv_db = db.query(Interview).filter(Interview.id == interview_id).first()
    assert inv_db.email_status == "ACCEPTED_BY_BREVO"
    assert inv_db.brevo_message_id is not None
    assert inv_db.email_sent_at is not None

def test_update_interview_details_sends_update_email(
    client, db, candidate_user, recruiter_user, recruiter_token
):
    """
    PART A: Rescheduling an interview triggers an update email.
    If details are unchanged, idempotency prevents duplicate emails.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Cloud Systems Engineer",
        description="Kubernetes & AWS infrastructure.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="cloud_resume.pdf",
        file_path="/dummy/cloud_resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.INTERVIEW
    )
    db.add(app_record)
    db.commit()

    orig_time = datetime.now(timezone.utc) + timedelta(days=3)
    interview = Interview(
        application_id=app_record.id,
        recruiter_id=recruiter_profile.id,
        candidate_id=candidate_profile.id,
        interview_type="ONLINE",
        scheduled_time=orig_time,
        duration_minutes=45,
        meeting_link="https://meet.google.com/old-link-123",
        status="SCHEDULED",
        email_status="ACCEPTED_BY_BREVO"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    clear_mock_deliveries()

    # 1. Update with new time and new link
    new_time = orig_time + timedelta(hours=4)
    update_resp = client.put(
        f"/api/v1/interviews/{interview.id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={
            "scheduled_time": new_time.isoformat(),
            "meeting_link": "https://meet.google.com/new-link-456"
        }
    )
    assert update_resp.status_code == 200

    deliveries = get_mock_deliveries()
    update_emails = [d for d in deliveries if d.get("email_type") == "INTERVIEW_RESCHEDULED"]
    assert len(update_emails) == 1
    assert "Interview Rescheduled — Cloud Systems Engineer" in update_emails[0]["subject"]

    # 2. Second update with identical data (idempotency check: no duplicate email)
    clear_mock_deliveries()
    noop_resp = client.put(
        f"/api/v1/interviews/{interview.id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={
            "scheduled_time": new_time.isoformat(),
            "meeting_link": "https://meet.google.com/new-link-456"
        }
    )
    assert noop_resp.status_code == 200
    deliveries_after_noop = get_mock_deliveries()
    assert len(deliveries_after_noop) == 0

def test_cancel_interview_sends_cancellation_email(
    client, db, candidate_user, recruiter_user, recruiter_token
):
    """
    PART A: Cancelling an interview sends an official cancellation email.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="AI Research Scientist",
        description="NLP and LLM research.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="ai_resume.pdf",
        file_path="/dummy/ai_resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.INTERVIEW
    )
    db.add(app_record)
    db.commit()

    interview = Interview(
        application_id=app_record.id,
        recruiter_id=recruiter_profile.id,
        candidate_id=candidate_profile.id,
        interview_type="ONLINE",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
        duration_minutes=60,
        meeting_link="https://meet.google.com/ai-meet-789",
        status="SCHEDULED",
        email_status="ACCEPTED_BY_BREVO"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    clear_mock_deliveries()

    cancel_resp = client.put(
        f"/api/v1/interviews/{interview.id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={
            "status": "CANCELLED",
            "instructions": "Position on temporary hold."
        }
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    deliveries = get_mock_deliveries()
    cancel_emails = [d for d in deliveries if d.get("email_type") == "INTERVIEW_CANCELLED"]
    assert len(cancel_emails) == 1
    assert "Interview Cancelled — AI Research Scientist" in cancel_emails[0]["subject"]

def test_resend_interview_email_endpoint(
    client, db, candidate_user, recruiter_user, recruiter_token
):
    """
    PART A: POST /api/v1/interviews/{id}/resend-email safely dispatches invitation email again.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Mobile Developer",
        description="React Native & Android.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="mobile_resume.pdf",
        file_path="/dummy/mobile_resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.INTERVIEW
    )
    db.add(app_record)
    db.commit()

    interview = Interview(
        application_id=app_record.id,
        recruiter_id=recruiter_profile.id,
        candidate_id=candidate_profile.id,
        interview_type="ONLINE",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=2),
        duration_minutes=30,
        meeting_link="https://meet.google.com/mobile-interview",
        status="SCHEDULED",
        email_status="PENDING"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    clear_mock_deliveries()

    resend_resp = client.post(
        f"/api/v1/interviews/{interview.id}/resend-email",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert resend_resp.status_code == 200
    res_data = resend_resp.json()
    assert res_data["email_status"] == "ACCEPTED_BY_BREVO"
    assert res_data["brevo_message_id"] is not None

    deliveries = get_mock_deliveries()
    assert len(deliveries) == 1
    assert deliveries[0]["email_type"] == "INTERVIEW_INVITATION"

def test_interview_email_failure_handling(
    client, db, candidate_user, recruiter_user, recruiter_token
):
    """
    PART A: If Brevo API fails or returns error, interview is still saved,
    and email_status is accurately tracked as FAILED with error detail.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Security Engineer",
        description="Infosec & Pen testing.",
        location="Bengaluru",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()

    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="sec_resume.pdf",
        file_path="/dummy/sec_resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED
    )
    db.add(resume)
    db.commit()

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app_record)
    db.commit()

    # Simulate Brevo API returning error response
    simulated_failure = {
        "status": "error",
        "delivered": False,
        "detail": "Brevo HTTP 401: Unauthorized API key",
        "email_type": "INTERVIEW_INVITATION"
    }

    with patch.object(EmailService, "send_interview_invitation_email", return_value=simulated_failure):
        sched_time = datetime.now(timezone.utc) + timedelta(days=2)
        resp = client.post(
            "/api/v1/interviews",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "application_id": app_record.id,
                "interview_type": "ONLINE",
                "scheduled_time": sched_time.isoformat(),
                "duration_minutes": 45,
                "meeting_link": "https://meet.google.com/sec-interview"
            }
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["email_status"] == "FAILED"
        assert "Unauthorized" in data["email_error_message"]
