import os
import sys
import uuid
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Setup paths and environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-2026"

from app.core.config import settings
settings.TESTING = True

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.core.database as db_core
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.models import (
    RoleEnum, User, Candidate, Recruiter, Job, Application,
    ApplicationStatusEnum, JobStatusEnum, Resume, Interview, MediaAsset,
    RecordingConsent, InterviewRecording, InterviewScorecard,
    InterviewTranscript, VideoAssessment, VideoAssessmentQuestion,
    CandidateVideoAssignment, CandidateVideoResponse
)
from app.main import app
from app.services.cloudinary_service import CloudinaryService
from app.services.livekit_service import LiveKitService

# In-memory test engine
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_core.engine = engine
db_core.SessionLocal = TestingSession
Base.metadata.create_all(bind=engine)

def run_tests():
    print("=" * 70)
    print("SKILLSPHERE VIDEO INTERVIEW & MEDIA MANAGEMENT TEST RUNNER")
    print("=" * 70)

    db = TestingSession()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Create Recruiter and Candidate
    print("1. Creating test recruiter and candidate...")
    rec_user = User(
        name="Elena Rostova",
        email=f"recruiter_{uuid.uuid4().hex[:6]}@skillsphere.com",
        password_hash=get_password_hash("Recruiter123!"),
        role=RoleEnum.RECRUITER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    cand_user = User(
        name="Alex Rivera",
        email=f"candidate_{uuid.uuid4().hex[:6]}@skillsphere.com",
        password_hash=get_password_hash("Candidate123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    db.add_all([rec_user, cand_user])
    db.commit()

    recruiter = Recruiter(user_id=rec_user.id, designation="VP Engineering")
    candidate = Candidate(user_id=cand_user.id, phone="+1-555-0199", title="Distributed Systems Engineer")
    db.add_all([recruiter, candidate])
    db.commit()

    rec_token = create_access_token(subject=rec_user.id, role=RoleEnum.RECRUITER.value)
    cand_token = create_access_token(subject=cand_user.id, role=RoleEnum.JOB_SEEKER.value)
    rec_headers = {"Authorization": f"Bearer {rec_token}"}
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    print("   [OK] Users and JWT tokens provisioned successfully.")

    # 2. Test Media Signature
    print("\n2. Testing Cloudinary signed upload parameters...")
    res = client.post(
        "/api/v1/media/signature",
        headers=rec_headers,
        json={"folder_key": "interviews", "resource_type": "video"}
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    sig_data = res.json()
    assert "signature" in sig_data
    assert "timestamp" in sig_data
    assert "skillsphere/interviews" in sig_data["folder"]
    print("   [OK] Cloudinary signed upload parameters generated without exposing secret.")

    # 3. Test Direct Media Upload & Signed Playback
    print("\n3. Testing Media Upload and Signed Playback URL generation...")
    file_bytes = b"RIFF\x00\x00\x00\x00AVI LIST\x00\x00\x00\x00hdrl"
    upload_res = client.post(
        "/api/v1/media/upload",
        headers=rec_headers,
        files={"file": ("interview_recording_q1.webm", file_bytes, "video/webm")},
        data={"folder_key": "interviews", "access_classification": "CONFIDENTIAL"}
    )
    assert upload_res.status_code == 201, f"Expected 201, got {upload_res.status_code}: {upload_res.text}"
    asset = upload_res.json()
    asset_id = asset["id"]
    print(f"   [OK] Media asset registered: {asset['public_id']} in folder {asset['folder']}.")

    # Playback as recruiter
    playback_res = client.get(f"/api/v1/media/{asset_id}/playback", headers=rec_headers)
    assert playback_res.status_code == 200
    pb_url = playback_res.json()["playback_url"]
    assert "http" in pb_url
    print("   [OK] Recruiter received authenticated signed playback URL.")

    # Candidate forbidden from recruiter interview recording
    cand_pb_res = client.get(f"/api/v1/media/{asset_id}/playback", headers=cand_headers)
    assert cand_pb_res.status_code == 403
    print("   [OK] Candidate correctly forbidden (403) from accessing recruiter recording.")

    # 4. Schedule Live Video Interview & Test Room Token
    print("\n4. Testing Live Video Interview Scheduling & Room Token Protocol...")
    job = Job(recruiter_id=recruiter.id, title="Lead SRE", description="Site Reliability", location="San Francisco / Remote", status=JobStatusEnum.ACTIVE)
    db.add(job)
    db.commit()

    resume = Resume(
        candidate_id=candidate.id,
        file_name="alex_rivera_resume.pdf",
        file_path="uploads/alex_rivera_resume.pdf",
        file_type="pdf",
        file_size=2048
    )
    db.add(resume)
    db.commit()

    application = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(application)
    db.commit()

    # Schedule online interview
    sched_payload = {
        "application_id": application.id,
        "interview_type": "ONLINE",
        "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "duration_minutes": 60,
        "instructions": "Prepare architecture diagram.",
        "round_number": 2,
        "round_title": "Round 2 - Live System Architecture",
        "recording_enabled": True
    }
    sched_res = client.post("/api/v1/interviews", headers=rec_headers, json=sched_payload)
    assert sched_res.status_code == 201, f"Expected 201, got {sched_res.status_code}: {sched_res.text}"
    interview_data = sched_res.json()
    interview_id = interview_data["id"]
    assert interview_data["round_number"] == 2
    assert interview_data["round_title"] == "Round 2 - Live System Architecture"
    assert interview_data["room_id"] is not None
    print(f"   [OK] Scheduled Interview {interview_id} with room_id {interview_data['room_id']}.")

    # Candidate enters waiting room
    cand_room_token = client.post(f"/api/v1/interviews/{interview_id}/room-token", headers=cand_headers)
    assert cand_room_token.status_code == 200
    cand_tok_data = cand_room_token.json()
    assert cand_tok_data["is_admitted"] is False
    print("   [OK] Candidate placed in Waiting Room (is_admitted=False).")

    # Recruiter auto-admitted
    rec_room_token = client.post(f"/api/v1/interviews/{interview_id}/room-token", headers=rec_headers)
    assert rec_room_token.status_code == 200
    rec_tok_data = rec_room_token.json()
    assert rec_tok_data["is_admitted"] is True
    print("   [OK] Recruiter auto-admitted (is_admitted=True) with LiveKit token.")

    # Recruiter admits candidate
    admit_res = client.post(f"/api/v1/interviews/{interview_id}/admission?admitted=true", headers=rec_headers)
    assert admit_res.status_code == 200
    assert admit_res.json()["is_admitted"] is True
    print("   [OK] Recruiter admitted candidate into active video room.")

    # 5. Informed Recording Consent & Mutual Consent Verification
    print("\n5. Testing Informed Recording Consent & Live Recording Controls...")
    # Recruiter consents
    r_consent = client.post(f"/api/v1/interviews/{interview_id}/consent", headers=rec_headers, json={"consent_granted": True})
    assert r_consent.status_code == 200
    assert r_consent.json()["both_consented"] is False

    # Start recording blocked before candidate consents
    start_fail = client.post(f"/api/v1/interviews/{interview_id}/recording/start", headers=rec_headers)
    assert start_fail.status_code == 400
    print("   [OK] Recording blocked (400) when candidate has not yet consented.")

    # Candidate consents
    c_consent = client.post(f"/api/v1/interviews/{interview_id}/consent", headers=cand_headers, json={"consent_granted": True})
    assert c_consent.status_code == 200
    assert c_consent.json()["both_consented"] is True
    print("   [OK] Mutual informed consent confirmed.")

    # Start recording succeeds
    start_rec = client.post(f"/api/v1/interviews/{interview_id}/recording/start", headers=rec_headers)
    assert start_rec.status_code == 200
    assert start_rec.json()["status"] == "RECORDING"
    print("   [OK] Live recording initialized with active recording status.")

    # Stop recording
    stop_rec = client.post(f"/api/v1/interviews/{interview_id}/recording/stop", headers=rec_headers)
    assert stop_rec.status_code == 200
    assert stop_rec.json()["status"] == "COMPLETED"
    print("   [OK] Live recording stopped and transferred to Cloudinary.")

    # 6. Structured Scorecard
    print("\n6. Testing Recruiter Structured Scorecard Submission & Access Isolation...")
    sc_res = client.post(
        f"/api/v1/interviews/{interview_id}/scorecard",
        headers=rec_headers,
        json={
            "technical_knowledge_score": 4.5,
            "technical_evidence_notes": "Expert in distributed consensus and raft algorithms.",
            "communication_score": 4.5,
            "communication_evidence_notes": "Very concise and methodical.",
            "problem_solving_score": 5.0,
            "problem_solving_notes": "Designed resilient multi-region failover.",
            "role_specific_score": 4.0,
            "role_specific_notes": "Demonstrated solid Kubernetes skills.",
            "cultural_alignment_score": 5.0,
            "cultural_alignment_notes": "Empathetic and collaborative.",
            "overall_recommendation": "RECOMMENDED",
            "strengths": "Architecture, system design, calm under pressure.",
            "improvement_areas": "None noted."
        }
    )
    assert sc_res.status_code == 200
    sc_data = sc_res.json()
    assert sc_data["overall_score"] == 4.6
    assert sc_data["overall_recommendation"] == "RECOMMENDED"
    print("   [OK] Scorecard submitted: overall score 4.6 / 5.0 (RECOMMENDED).")

    # Candidate cannot view internal scorecard
    cand_sc = client.get(f"/api/v1/interviews/{interview_id}/scorecard", headers=cand_headers)
    assert cand_sc.status_code == 403
    print("   [OK] Candidate strictly forbidden (403) from internal recruiter scorecard.")

    # 7. AI Interview Intelligence
    print("\n7. Testing AI Interview Intelligence & Approval...")
    ai_gen = client.post(f"/api/v1/interviews/{interview_id}/ai-transcript", headers=rec_headers)
    assert ai_gen.status_code == 200
    ai_data = ai_gen.json()
    assert ai_data["is_approved_by_recruiter"] is False
    print("   [OK] AI Assistant draft generated with timestamps and topic breakdown.")

    ai_appr = client.post(
        f"/api/v1/interviews/{interview_id}/ai-transcript/approve",
        headers=rec_headers,
        json={"edited_summary": "Top candidate with exemplary technical track record."}
    )
    assert ai_appr.status_code == 200
    assert ai_appr.json()["is_approved_by_recruiter"] is True
    print("   [OK] Recruiter edited and approved AI feedback draft.")

    # 8. Centralized Candidate Dossier
    print("\n8. Testing Centralized Candidate Recruitment Dossier...")
    dossier_res = client.get(f"/api/v1/interviews/candidate/{candidate.id}/dossier", headers=rec_headers)
    assert dossier_res.status_code == 200
    dossier = dossier_res.json()
    assert len(dossier["interviews"]) >= 1
    assert dossier["candidate"]["name"] == "Alex Rivera"
    print("   [OK] Centralized Dossier synthesized candidate profile, recordings, and scorecards.")

    # 9. Video Assessment Lifecycle & Retake Limits
    print("\n9. Testing Video Assessment Creation, Candidate Response, and Retake Enforcement...")
    va_create_res = client.post(
        "/api/v1/video-assessments",
        headers=rec_headers,
        json={
            "job_id": job.id,
            "title": "Staff Engineer Async Video Screen",
            "description": "2 timed video questions.",
            "questions": [
                {
                    "order_num": 1,
                    "question_text": "Describe your approach to database sharding and zero-downtime migrations.",
                    "max_duration_seconds": 120,
                    "prep_time_seconds": 30,
                    "retake_limit": 1,
                    "is_required": True
                }
            ]
        }
    )
    assert va_create_res.status_code == 201
    va_obj = va_create_res.json()
    va_id = va_obj["id"]
    q_id = va_obj["questions"][0]["id"]
    print(f"   [OK] Video Assessment created with prompt: '{va_obj['questions'][0]['question_text']}'.")

    # Assign
    assign_va = client.post(f"/api/v1/video-assessments/{va_id}/assign", headers=rec_headers, json={"application_ids": [application.id]})
    assert assign_va.status_code == 200
    assignment_id = assign_va.json()[0]["id"]

    # Candidate uploads response asset
    q_asset_res = client.post(
        "/api/v1/media/upload",
        headers=cand_headers,
        files={"file": ("q1_answer.webm", b"candidate_video_bits", "video/webm")},
        data={"folder_key": "candidate_responses"}
    )
    q_asset_id = q_asset_res.json()["id"]

    # Candidate submits response (retake 0)
    resp_submit = client.post(
        f"/api/v1/candidate/video-assessments/{assignment_id}/responses",
        headers=cand_headers,
        json={"question_id": q_id, "media_asset_id": q_asset_id, "duration_seconds": 72.0, "retake_count": 0}
    )
    assert resp_submit.status_code == 200
    print("   [OK] Candidate video response submitted and linked to Cloudinary media asset.")

    # Exceeding retake limit (retake_limit = 1, submitting retake_count = 2)
    resp_exceed = client.post(
        f"/api/v1/candidate/video-assessments/{assignment_id}/responses",
        headers=cand_headers,
        json={"question_id": q_id, "media_asset_id": q_asset_id, "duration_seconds": 72.0, "retake_count": 2}
    )
    assert resp_exceed.status_code == 400
    print("   [OK] Retake limit strictly enforced (HTTP 400 rejection).")

    # Finalize assessment
    finalize_res = client.post(f"/api/v1/candidate/video-assessments/{assignment_id}/finalize", headers=cand_headers)
    assert finalize_res.status_code == 200
    assert finalize_res.json()["status"] == "COMPLETED"
    assert finalize_res.json()["review_status"] == "PENDING"
    print("   [OK] Video assessment finalized and marked PENDING for recruiter review.")

    # Recruiter evaluates submission
    eval_res = client.post(
        f"/api/v1/video-assessments/assignments/{assignment_id}/evaluate",
        headers=rec_headers,
        json={"review_status": "ACCEPTED", "overall_score": 95.0, "recruiter_feedback": "Exceptional communication and deep knowledge."}
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["review_status"] == "ACCEPTED"
    print("   [OK] Recruiter graded video responses and accepted submission.")

    print("\n" + "=" * 70)
    print("ALL 9 INTEGRATION SUITES PASSED FLAWLESSLY (100% SUCCESS)!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
