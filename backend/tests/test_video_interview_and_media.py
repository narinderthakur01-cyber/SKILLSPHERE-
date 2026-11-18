import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models.models import (
    Job, Application, ApplicationStatusEnum, JobStatusEnum, Resume,
    Recruiter, Candidate, User, RoleEnum, Interview,
    MediaAsset, RecordingConsent, InterviewRecording,
    InterviewScorecard, InterviewTranscript,
    VideoAssessment, VideoAssessmentQuestion, CandidateVideoAssignment, CandidateVideoResponse
)
from app.services.cloudinary_service import CloudinaryService
from app.services.livekit_service import LiveKitService

@pytest.fixture
def test_setup_data(db, recruiter_user, candidate_user):
    """Sets up a common job, candidate, application, and interview."""
    recruiter = recruiter_user.recruiter_profile
    candidate = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter.id,
        title="Senior Cloud & Video Architect",
        description="Lead media infrastructure and video interview systems.",
        location="Remote",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate.id,
        file_name="architect_resume.pdf",
        file_path="uploads/architect_resume.pdf",
        file_type="pdf",
        file_size=2048
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

    interview = Interview(
        application_id=app_record.id,
        recruiter_id=recruiter.id,
        candidate_id=candidate.id,
        interview_type="ONLINE",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=2),
        duration_minutes=45,
        status="SCHEDULED",
        room_id=f"room_{uuid.uuid4().hex[:12]}",
        room_status="WAITING",
        round_number=1,
        round_title="Round 1 - Technical Screen",
        recording_enabled=True,
        recording_status="NOT_RECORDED",
        is_admitted=False
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return {
        "recruiter": recruiter,
        "candidate": candidate,
        "job": job,
        "application": app_record,
        "interview": interview
    }

# ============================================================================
# 1. MEDIA MANAGEMENT TESTS
# ============================================================================

def test_media_upload_signature_generation(client, recruiter_token, candidate_token):
    """Verify signed upload signature parameter generation for Cloudinary."""
    # Recruiter requesting interview folder signature
    res = client.post(
        "/api/v1/media/signature",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"folder_key": "interviews", "resource_type": "video"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "signature" in data
    assert "timestamp" in data
    assert "api_key" in data
    assert "skillsphere/interviews" in data["folder"]
    assert data["resource_type"] == "video"

    # Candidate forbidden from uploading directly to interview folder
    res_cand = client.post(
        "/api/v1/media/signature",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"folder_key": "interviews", "resource_type": "video"}
    )
    assert res_cand.status_code == 403

def test_media_upload_direct_and_signed_playback(client, recruiter_token, candidate_token, test_setup_data):
    """Direct upload produces MediaAsset, stores in DB, and generates signed playback URL."""
    fake_video_content = b"RIFF....AVI....SkillSphereTestVideoBytes"
    files = {"file": ("test_clip.webm", fake_video_content, "video/webm")}
    data = {
        "folder_key": "interviews",
        "interview_id": test_setup_data["interview"].id,
        "access_classification": "CONFIDENTIAL"
    }

    res = client.post(
        "/api/v1/media/upload",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        files=files,
        data=data
    )
    assert res.status_code == 201
    asset_data = res.json()
    assert asset_data["original_filename"] == "test_clip.webm"
    assert "skillsphere/interviews" in asset_data["folder"]
    assert asset_data["access_classification"] == "CONFIDENTIAL"
    asset_id = asset_data["id"]

    # Request signed playback URL as recruiter
    playback_res = client.get(
        f"/api/v1/media/{asset_id}/playback",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert playback_res.status_code == 200
    pb_data = playback_res.json()
    assert "playback_url" in pb_data
    assert pb_data["expires_in_seconds"] == 3600
    assert "signature=" in pb_data["playback_url"] or "token=" in pb_data["playback_url"] or "res.cloudinary.com" in pb_data["playback_url"]

    # Candidate forbidden from accessing recruiter interview media
    cand_pb_res = client.get(
        f"/api/v1/media/{asset_id}/playback",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_pb_res.status_code == 403

def test_media_deletion(client, recruiter_token, test_setup_data):
    """Recruiter can delete their uploaded media asset."""
    fake_video = b"test bytes"
    res = client.post(
        "/api/v1/media/upload",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        files={"file": ("to_delete.webm", fake_video, "video/webm")},
        data={"folder_key": "interviews"}
    )
    asset_id = res.json()["id"]

    del_res = client.delete(
        f"/api/v1/media/{asset_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

# ============================================================================
# 2. LIVE VIDEO & ROOM TOKEN TESTS
# ============================================================================

def test_room_token_generation_and_waiting_room_admission(
    client, recruiter_token, candidate_token, test_setup_data
):
    """
    Candidate enters waiting room (is_admitted=False) until recruiter admits them (is_admitted=True).
    """
    interview = test_setup_data["interview"]

    # Candidate requests room token
    cand_res = client.post(
        f"/api/v1/interviews/{interview.id}/room-token",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_res.status_code == 200
    cand_data = cand_res.json()
    assert cand_data["role"] == "candidate"
    assert cand_data["is_recruiter"] is False
    assert cand_data["is_admitted"] is False  # Candidate waiting room

    # Recruiter requests room token
    rec_res = client.post(
        f"/api/v1/interviews/{interview.id}/room-token",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["role"] == "recruiter"
    assert rec_data["is_recruiter"] is True
    assert rec_data["is_admitted"] is True  # Recruiter auto-admitted

    # Recruiter admits candidate
    admit_res = client.post(
        f"/api/v1/interviews/{interview.id}/admission?admitted=true",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert admit_res.status_code == 200
    assert admit_res.json()["is_admitted"] is True

    # Candidate now admitted
    cand_res2 = client.post(
        f"/api/v1/interviews/{interview.id}/room-token",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_res2.json()["is_admitted"] is True

def test_room_status_and_lifecycle(client, recruiter_token, test_setup_data):
    """Test start and end room lifecycle."""
    interview = test_setup_data["interview"]

    start_res = client.post(
        f"/api/v1/interviews/{interview.id}/room-start",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"

    status_res = client.get(
        f"/api/v1/interviews/{interview.id}/room-status",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert status_res.status_code == 200
    assert status_res.json()["room_status"] == "IN_PROGRESS"

    end_res = client.post(
        f"/api/v1/interviews/{interview.id}/room-end",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert end_res.status_code == 200
    assert end_res.json()["status"] == "COMPLETED"

# ============================================================================
# 3. RECORDING & INFORMED CONSENT TESTS
# ============================================================================

def test_mutual_consent_enforced_before_recording(
    client, recruiter_token, candidate_token, test_setup_data
):
    """
    Recording is blocked unless BOTH participants grant informed consent.
    """
    interview = test_setup_data["interview"]

    # 1. Recruiter grants consent
    rec_consent = client.post(
        f"/api/v1/interviews/{interview.id}/consent",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"consent_granted": True}
    )
    assert rec_consent.status_code == 200
    assert rec_consent.json()["both_consented"] is False

    # Attempt to start recording when candidate has not yet consented -> 400 Bad Request
    start_fail = client.post(
        f"/api/v1/interviews/{interview.id}/recording/start",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert start_fail.status_code == 400
    assert "explicit consent" in start_fail.json()["detail"].lower()

    # 2. Candidate grants consent
    cand_consent = client.post(
        f"/api/v1/interviews/{interview.id}/consent",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={"consent_granted": True}
    )
    assert cand_consent.status_code == 200
    assert cand_consent.json()["both_consented"] is True

    # 3. Now start recording succeeds
    start_success = client.post(
        f"/api/v1/interviews/{interview.id}/recording/start",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert start_success.status_code == 200
    assert start_success.json()["status"] == "RECORDING"

    # 4. Stop recording transfers to Cloudinary
    stop_res = client.post(
        f"/api/v1/interviews/{interview.id}/recording/stop",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert stop_res.status_code == 200
    rec_obj = stop_res.json()
    assert rec_obj["status"] == "COMPLETED"
    assert rec_obj["media_asset_id"] is not None

    # 5. List recordings as recruiter
    list_rec = client.get(
        f"/api/v1/interviews/{interview.id}/recordings",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert list_rec.status_code == 200
    assert len(list_rec.json()) >= 1

    # Candidate forbidden from accessing recordings
    cand_list_rec = client.get(
        f"/api/v1/interviews/{interview.id}/recordings",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_list_rec.status_code == 403

# ============================================================================
# 4. STRUCTURED SCORECARD TESTS
# ============================================================================

def test_interview_scorecard_flow_and_rbac(
    client, recruiter_token, candidate_token, test_setup_data
):
    """
    Recruiter submits structured scorecard across technical, communication, problem solving,
    role-specific, and cultural alignment. Candidates are strictly forbidden from viewing.
    """
    interview = test_setup_data["interview"]

    scorecard_payload = {
        "technical_knowledge_score": 4.5,
        "technical_evidence_notes": "Strong grasp of distributed caching and microservices.",
        "communication_score": 4.0,
        "communication_evidence_notes": "Articulate explanations with clear diagrams.",
        "problem_solving_score": 5.0,
        "problem_solving_notes": "Quickly diagnosed edge-case concurrency bugs.",
        "role_specific_score": 4.5,
        "role_specific_notes": "Deep FastAPI and PostgreSQL experience.",
        "cultural_alignment_score": 4.0,
        "cultural_alignment_notes": "Collaborative, receptive to feedback.",
        "overall_recommendation": "RECOMMENDED",
        "strengths": "Architecture depth, clean coding standards.",
        "improvement_areas": "Could explore Kafka partitions in more detail.",
        "private_evaluation_notes": "Ideal match for Tech Lead opening."
    }

    # Submit scorecard
    sc_res = client.post(
        f"/api/v1/interviews/{interview.id}/scorecard",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=scorecard_payload
    )
    assert sc_res.status_code == 200
    sc_data = sc_res.json()
    assert sc_data["overall_score"] == 4.4  # (4.5 + 4 + 5 + 4.5 + 4) / 5 = 22 / 5 = 4.4
    assert sc_data["overall_recommendation"] == "RECOMMENDED"

    # Recruiter retrieves scorecard
    get_sc = client.get(
        f"/api/v1/interviews/{interview.id}/scorecard",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert get_sc.status_code == 200
    assert get_sc.json()["overall_recommendation"] == "RECOMMENDED"

    # Candidate forbidden from accessing scorecard
    cand_get_sc = client.get(
        f"/api/v1/interviews/{interview.id}/scorecard",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_get_sc.status_code == 403

# ============================================================================
# 5. AI INTERVIEW INTELLIGENCE TESTS
# ============================================================================

def test_ai_transcript_generation_and_approval(
    client, recruiter_token, test_setup_data
):
    """
    Generates AI transcript, summary, and draft feedback labeled as assistant draft.
    Recruiter reviews and approves.
    """
    interview = test_setup_data["interview"]

    # Generate AI intelligence
    ai_res = client.post(
        f"/api/v1/interviews/{interview.id}/ai-transcript",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "timestamps_json" in ai_data
    assert len(ai_data["technical_topics_json"]) >= 1
    assert ai_data["is_approved_by_recruiter"] is False  # Assistant draft

    # Recruiter approves
    approve_res = client.post(
        f"/api/v1/interviews/{interview.id}/ai-transcript/approve",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={
            "edited_summary": "Candidate demonstrated outstanding competence in cloud distributed systems.",
            "edited_feedback": {"readiness": "Immediate hire ready"}
        }
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["is_approved_by_recruiter"] is True
    assert approve_res.json()["ai_summary"] == "Candidate demonstrated outstanding competence in cloud distributed systems."

# ============================================================================
# 6. CENTRALIZED CANDIDATE DOSSIER TEST
# ============================================================================

def test_candidate_dossier(client, recruiter_token, test_setup_data):
    """Recruiter retrieves candidate dossier with resume, MCQ, video, and interview history."""
    candidate = test_setup_data["candidate"]
    res = client.get(
        f"/api/v1/interviews/candidate/{candidate.id}/dossier",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "candidate" in data
    assert "resumes" in data
    assert "mcq_assessments" in data
    assert "video_assessments" in data
    assert "interviews" in data
    assert len(data["interviews"]) >= 1

# ============================================================================
# 7. VIDEO ASSESSMENTS END-TO-END WORKFLOW
# ============================================================================

def test_video_assessment_creation_assignment_response_and_grading(
    client, recruiter_token, candidate_token, test_setup_data
):
    """
    Full Video Assessment Lifecycle:
    1. Recruiter creates video assessment with question prompts.
    2. Recruiter assigns video assessment to candidate.
    3. Candidate retrieves questions.
    4. Candidate submits video response.
    5. Retake limit enforcement.
    6. Candidate finalizes submission.
    7. Recruiter evaluates and grades responses.
    """
    job = test_setup_data["job"]
    application = test_setup_data["application"]

    # 1. Create Video Assessment
    create_payload = {
        "job_id": job.id,
        "title": "Backend Engineering Video Screen",
        "description": "3-question asynchronous video evaluation.",
        "instructions": "Speak clearly and state your assumptions before answering.",
        "questions": [
            {
                "order_num": 1,
                "question_text": "How do you handle database connection pooling and failover in FastAPI?",
                "question_instructions": "Discuss connection limits and retry policies.",
                "max_duration_seconds": 120,
                "prep_time_seconds": 30,
                "retake_limit": 1,
                "is_required": True
            },
            {
                "order_num": 2,
                "question_text": "Describe your strategy for live video streaming and media asset retention.",
                "question_instructions": "Mention WebRTC, Cloudinary, and storage tiers.",
                "max_duration_seconds": 90,
                "prep_time_seconds": 20,
                "retake_limit": 2,
                "is_required": False
            }
        ]
    }

    va_res = client.post(
        "/api/v1/video-assessments",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=create_payload
    )
    assert va_res.status_code == 201
    va_data = va_res.json()
    assert va_data["total_questions"] == 2
    va_id = va_data["id"]
    q1_id = va_data["questions"][0]["id"]
    q2_id = va_data["questions"][1]["id"]

    # 2. Assign to Candidate
    assign_res = client.post(
        f"/api/v1/video-assessments/{va_id}/assign",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"application_ids": [application.id]}
    )
    assert assign_res.status_code == 200
    assignment_id = assign_res.json()[0]["id"]

    # 3. Candidate views assigned assessments
    my_va_res = client.get(
        "/api/v1/candidate/video-assessments",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert my_va_res.status_code == 200
    assert len(my_va_res.json()) >= 1

    # Candidate views assignment details
    detail_res = client.get(
        f"/api/v1/candidate/video-assessments/{assignment_id}",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert detail_res.status_code == 200
    assert len(detail_res.json()["questions"]) == 2

    # 4. Candidate uploads video asset for response
    upload_res = client.post(
        "/api/v1/media/upload",
        headers={"Authorization": f"Bearer {candidate_token}"},
        files={"file": ("q1_response.webm", b"video-response-content", "video/webm")},
        data={"folder_key": "candidate_responses"}
    )
    media_asset_id = upload_res.json()["id"]

    # Submit response for Q1
    resp_res = client.post(
        f"/api/v1/candidate/video-assessments/{assignment_id}/responses",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "question_id": q1_id,
            "media_asset_id": media_asset_id,
            "duration_seconds": 85.5,
            "retake_count": 0
        }
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["duration_seconds"] == 85.5

    # 5. Retake Limit Enforcement: Q1 retake_limit is 1. Exceeding retake_limit (e.g. 2) should fail
    resp_fail = client.post(
        f"/api/v1/candidate/video-assessments/{assignment_id}/responses",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json={
            "question_id": q1_id,
            "media_asset_id": media_asset_id,
            "duration_seconds": 88.0,
            "retake_count": 2  # Limit is 1
        }
    )
    assert resp_fail.status_code == 400
    assert "retake limit exceeded" in resp_fail.json()["detail"].lower()

    # 6. Finalize assessment
    finalize_res = client.post(
        f"/api/v1/candidate/video-assessments/{assignment_id}/finalize",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert finalize_res.status_code == 200
    assert finalize_res.json()["status"] == "COMPLETED"

    # 7. Recruiter views candidate submission and grades it
    review_res = client.get(
        f"/api/v1/video-assessments/assignments/{assignment_id}/review",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert review_res.status_code == 200
    assert len(review_res.json()["responses"]) >= 1

    # Recruiter evaluates
    eval_res = client.post(
        f"/api/v1/video-assessments/assignments/{assignment_id}/evaluate",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={
            "review_status": "ACCEPTED",
            "overall_score": 92.5,
            "recruiter_feedback": "Excellent technical articulation and architecture mindset."
        }
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["review_status"] == "ACCEPTED"
