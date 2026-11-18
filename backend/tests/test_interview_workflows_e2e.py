import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    Job, Application, JobStatusEnum, ApplicationStatusEnum,
    Resume, Interview, InterviewQuestion, InterviewResponse,
    InterviewEvaluation, MediaAsset
)

@pytest.fixture
def e2e_interview_setup(db, recruiter_user, candidate_user):
    recruiter = recruiter_user.recruiter_profile
    candidate = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter.id,
        title="Principal Platform Architect",
        description="Lead global cloud platform architecture and reliability.",
        location="Hybrid / San Francisco",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate.id,
        file_name="platform_architect_cv.pdf",
        file_path="uploads/platform_architect_cv.pdf",
        file_type="pdf",
        file_size=4096
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    app_record = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    return {
        "recruiter": recruiter,
        "candidate": candidate,
        "job": job,
        "application": app_record
    }


def test_recruiter_schedule_ai_interview_with_scheduled_at_and_autoseed(client, recruiter_token, e2e_interview_setup):
    """Verify recruiter can schedule AI interview using frontend `scheduled_at` format, with auto-seeded questions."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    scheduled_iso = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    res = client.post(
        "/api/v1/interviews",
        json={
            "application_id": e2e_interview_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "AI_LIVE",
            "scheduled_at": scheduled_iso,  # Frontend field
            "duration_minutes": 30,
            "round_title": "AI Technical Evaluation Round",
            "voice": "alloy",
            "difficulty": "SENIOR",
            "allow_recruiter_takeover": True,
            "recording_enabled": True
        },
        headers=headers
    )
    assert res.status_code == 201
    int_data = res.json()
    assert int_data["interview_mode"] == "AI_LIVE"
    assert int_data["status"] == "SCHEDULED"
    assert int_data["scheduled_time"] is not None

    interview_id = int_data["id"]

    # Verify questions were auto-seeded
    q_res = client.get(f"/api/v1/interviews/{interview_id}/questions", headers=headers)
    assert q_res.status_code == 200
    questions = q_res.json()
    assert len(questions) >= 3, "Expected at least 3 auto-seeded AI interview questions"
    assert all("question_text" in q for q in questions)


def test_room_status_endpoint_returns_mode_takeover_and_question_index(client, recruiter_token, e2e_interview_setup):
    """Verify room status endpoint returns interview_mode, ai_takeover_status, and current_question_index."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    scheduled_iso = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # Schedule a HYBRID interview
    res = client.post(
        "/api/v1/interviews",
        json={
            "application_id": e2e_interview_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "HYBRID",
            "scheduled_time": scheduled_iso,
            "duration_minutes": 45,
            "round_title": "Hybrid Architecture Deep-Dive"
        },
        headers=headers
    )
    assert res.status_code == 201
    interview_id = res.json()["id"]

    # Query room status
    status_res = client.get(f"/api/v1/interviews/{interview_id}/room-status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["interview_mode"] == "HYBRID"
    assert status_data["ai_takeover_status"] == "AI_ACTIVE"
    assert status_data["current_question_index"] == 0

    # Recruiter takeover
    takeover_res = client.post(
        f"/api/v1/interviews/{interview_id}/hybrid/takeover",
        json={"takeover": True},
        headers=headers
    )
    assert takeover_res.status_code == 200
    assert takeover_res.json()["ai_takeover_status"] == "RECRUITER_ACTIVE"

    # Verify room status reflects takeover
    status_res_2 = client.get(f"/api/v1/interviews/{interview_id}/room-status", headers=headers)
    assert status_res_2.status_code == 200
    assert status_res_2.json()["ai_takeover_status"] == "RECRUITER_ACTIVE"


def test_recruiter_cancel_interview_flow(client, recruiter_token, candidate_token, e2e_interview_setup):
    """Verify recruiter can cancel an interview and it transitions to CANCELLED."""
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}
    c_headers = {"Authorization": f"Bearer {candidate_token}"}
    scheduled_iso = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    # Schedule interview
    res = client.post(
        "/api/v1/interviews",
        json={
            "application_id": e2e_interview_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "HUMAN",
            "scheduled_time": scheduled_iso,
            "duration_minutes": 45,
            "round_title": "HR Leadership Discussion"
        },
        headers=r_headers
    )
    assert res.status_code == 201
    interview_id = res.json()["id"]

    # Cancel interview
    cancel_res = client.post(f"/api/v1/interviews/{interview_id}/cancel", headers=r_headers)
    assert cancel_res.status_code == 200
    cancelled_data = cancel_res.json()
    assert cancelled_data["status"] == "CANCELLED"

    # Candidate fetches interviews: cancelled should not be considered active/joinable
    my_ints = client.get("/api/v1/interviews/my", headers=c_headers)
    assert my_ints.status_code == 200
    cand_data = my_ints.json()
    interview_entry = next((i for i in cand_data if i["id"] == interview_id), None)
    assert interview_entry is not None
    assert interview_entry["status"] == "CANCELLED"


def test_recruiter_edit_interview_schedule(client, recruiter_token, e2e_interview_setup):
    """Verify recruiter can edit an existing interview's schedule and duration."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    initial_iso = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # Schedule
    res = client.post(
        "/api/v1/interviews",
        json={
            "application_id": e2e_interview_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "AI_LIVE",
            "scheduled_time": initial_iso,
            "duration_minutes": 30,
            "round_title": "Initial Screen"
        },
        headers=headers
    )
    assert res.status_code == 201
    interview_id = res.json()["id"]

    # Update with new time using scheduled_at
    new_iso = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    put_res = client.put(
        f"/api/v1/interviews/{interview_id}",
        json={
            "scheduled_at": new_iso,
            "duration_minutes": 60,
            "round_title": "Expanded Technical Screen"
        },
        headers=headers
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["duration_minutes"] == 60
    assert updated["round_title"] == "Expanded Technical Screen"
