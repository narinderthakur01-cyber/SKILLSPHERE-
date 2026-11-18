import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    Job, Resume, Application, ApplicationStatusEnum,
    ProcessingStatusEnum, JobStatusEnum, Recruiter, Candidate, User, RoleEnum,
    Assessment, AssessmentStatusEnum, AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAssignmentStatusEnum,
    AssessmentAttempt, AttemptStatusEnum, ProctoringSession, ProctoringEvent,
    ProctoringSessionStatusEnum, ProctoringEventTypeEnum, AuditLog
)

@pytest.fixture
def active_assessment_setup(db, candidate_user, recruiter_user):
    """Creates a complete job, published assessment, assignment, and in-progress attempt."""
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter_profile.id,
        title="Full Stack Software Engineer",
        description="FastAPI + React production systems.",
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

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate_profile.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    assessment = Assessment(
        job_id=job.id,
        recruiter_id=recruiter_profile.id,
        title="Engineering First-Round MCQ Test",
        duration_minutes=30,
        total_marks=10,
        passing_marks=7,
        status=AssessmentStatusEnum.PUBLISHED
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    assignment = CandidateAssessmentAssignment(
        assessment_id=assessment.id,
        candidate_id=candidate_profile.id,
        application_id=app_record.id,
        assigned_by_user_id=recruiter_user.id,
        status=AssessmentAssignmentStatusEnum.STARTED
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    now = datetime.now(timezone.utc)
    attempt = AssessmentAttempt(
        assignment_id=assignment.id,
        candidate_id=candidate_profile.id,
        assessment_id=assessment.id,
        started_at=now,
        expires_at=now + timedelta(minutes=30),
        status=AttemptStatusEnum.IN_PROGRESS
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "job": job,
        "assessment": assessment,
        "assignment": assignment,
        "attempt": attempt,
        "candidate": candidate_profile,
        "recruiter": recruiter_profile
    }

def test_proctoring_session_start_and_idempotency(client, candidate_token, active_assessment_setup):
    """Candidate starts proctoring session; repeating start returns existing session."""
    attempt = active_assessment_setup["attempt"]

    # 1. Start proctoring session
    resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["assessment_attempt_id"] == attempt.id
    assert data["camera_permission_granted"] is True
    assert data["monitoring_status"] == "ACTIVE"
    assert data["total_warning_count"] == 0
    assert data["warning_level"] == "NORMAL"
    session_id = data["id"]

    # 2. Idempotent start returns same session
    resp2 = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    assert resp2.status_code == 200
    assert resp2.json()["id"] == session_id

def test_candidate_records_events_and_increments_counters(client, candidate_token, active_assessment_setup):
    """Recording tab switch and face absence increments specific and total warning counters."""
    attempt = active_assessment_setup["attempt"]

    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    # Record TAB_SWITCH event
    evt_resp1 = client.post(
        f"/api/v1/proctoring/session/{session_id}/event",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "event_type": "TAB_SWITCH",
            "duration_seconds": 3.5,
            "severity": "HIGH",
            "details_json": {"reason": "User navigated away"}
        }
    )
    assert evt_resp1.status_code == 200
    s1 = evt_resp1.json()
    assert s1["tab_switch_count"] == 1
    assert s1["total_warning_count"] == 1
    assert s1["warning_level"] == "WARNING_1"

    # Record FACE_NOT_DETECTED event
    evt_resp2 = client.post(
        f"/api/v1/proctoring/session/{session_id}/event",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "event_type": "FACE_NOT_DETECTED",
            "duration_seconds": 5.2,
            "severity": "MEDIUM",
            "details_json": {"confidence": 0.2}
        }
    )
    assert evt_resp2.status_code == 200
    s2 = evt_resp2.json()
    assert s2["face_not_detected_count"] == 1
    assert s2["tab_switch_count"] == 1
    assert s2["total_warning_count"] == 2
    assert s2["warning_level"] == "WARNING_2"

def test_escalation_to_flagged_status_at_threshold(client, candidate_token, active_assessment_setup):
    """Reaching 3 warnings transitions session monitoring_status to FLAGGED without auto-failing."""
    attempt = active_assessment_setup["attempt"]

    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    # Send 3 distinct events
    for idx, etype in enumerate(["TAB_SWITCH", "FACE_NOT_DETECTED", "MULTIPLE_FACES_DETECTED"]):
        resp = client.post(
            f"/api/v1/proctoring/session/{session_id}/event",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={"event_type": etype, "duration_seconds": 2.0, "severity": "HIGH"}
        )
        assert resp.status_code == 200

    final_session = resp.json()
    assert final_session["total_warning_count"] == 3
    assert final_session["monitoring_status"] == "FLAGGED"
    assert final_session["warning_level"] == "FLAGGED"

def test_candidate_ends_proctoring_session(client, candidate_token, active_assessment_setup):
    """Ending proctoring session sets ended_at and marks status COMPLETED."""
    attempt = active_assessment_setup["attempt"]

    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    end_resp = client.post(
        f"/api/v1/proctoring/session/{session_id}/end",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert end_resp.status_code == 200
    ended_data = end_resp.json()
    assert ended_data["ended_at"] is not None
    assert ended_data["monitoring_status"] == "COMPLETED"

def test_unauthorized_candidate_cannot_access_or_submit_events(
    client, db, candidate_token, active_assessment_setup
):
    """Candidate cannot access or tamper with another candidate's session."""
    attempt = active_assessment_setup["attempt"]

    # Start session as primary candidate
    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    # Create another candidate
    from app.core.security import get_password_hash, create_access_token
    other_user = User(
        name="Other Cand",
        email="other_candidate@skillsphere.com",
        password_hash=get_password_hash("Pass123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    other_profile = Candidate(user_id=other_user.id)
    db.add(other_profile)
    db.commit()
    other_token = create_access_token(subject=other_user.id, role=other_user.role.value)

    # Other candidate attempts to record event on primary candidate's session -> MUST FAIL WITH 403
    forbidden_resp = client.post(
        f"/api/v1/proctoring/session/{session_id}/event",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"event_type": "TAB_SWITCH", "duration_seconds": 1.0}
    )
    assert forbidden_resp.status_code == 403

def test_admin_lists_and_filters_proctoring_sessions(
    client, admin_token, candidate_token, active_assessment_setup
):
    """Admin can list and filter proctoring sessions."""
    attempt = active_assessment_setup["attempt"]

    # Initialize a session
    client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )

    # Admin lists sessions
    list_resp = client.get(
        "/api/v1/admin/proctoring/sessions?filter=ALL",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "candidate_name" in item
    assert "assessment_title" in item
    assert "job_title" in item
    assert "monitoring_status" in item

def test_admin_inspects_session_detail_and_reviews_event(
    client, db, admin_token, candidate_token, active_assessment_setup
):
    """Admin fetches detailed session timeline and reviews an individual event."""
    attempt = active_assessment_setup["attempt"]

    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    # Add an event
    client.post(
        f"/api/v1/proctoring/session/{session_id}/event",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"event_type": "TAB_SWITCH", "duration_seconds": 4.5, "severity": "HIGH"}
    )

    # Admin inspects detail
    detail_resp = client.get(
        f"/api/v1/admin/proctoring/sessions/{session_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["events"]) == 1
    event_id = detail["events"][0]["id"]
    assert detail["events"][0]["reviewed_status"] == "PENDING"

    # Admin marks event as REVIEWED
    review_resp = client.put(
        f"/api/v1/admin/proctoring/events/{event_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reviewed_status": "REVIEWED", "admin_notes": "Legitimate focus loss confirmed."}
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.json()
    assert rev_data["reviewed_status"] == "REVIEWED"
    assert rev_data["admin_notes"] == "Legitimate focus loss confirmed."

def test_admin_resolves_proctoring_session_status(
    client, admin_token, candidate_token, active_assessment_setup
):
    """Admin updates session monitoring status and records audit trail."""
    attempt = active_assessment_setup["attempt"]

    start_resp = client.post(
        "/api/v1/proctoring/session/start",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"attempt_id": attempt.id, "camera_permission_granted": True}
    )
    session_id = start_resp.json()["id"]

    # Admin resolves session to COMPLETED
    res_resp = client.put(
        f"/api/v1/admin/proctoring/sessions/{session_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"monitoring_status": "COMPLETED", "admin_notes": "Candidate cleared after manual check."}
    )
    assert res_resp.status_code == 200
    resolved = res_resp.json()
    assert resolved["monitoring_status"] == "COMPLETED"

def test_non_admin_forbidden_from_admin_proctoring_endpoints(
    client, candidate_token, recruiter_token, active_assessment_setup
):
    """Candidate and recruiter are forbidden from admin proctoring management routes."""
    # Candidate -> 403
    r1 = client.get(
        "/api/v1/admin/proctoring/sessions",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert r1.status_code == 403

    # Recruiter -> 403
    r2 = client.get(
        "/api/v1/admin/proctoring/sessions",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert r2.status_code == 403
