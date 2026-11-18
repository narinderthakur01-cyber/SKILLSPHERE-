import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    Job, Application, JobStatusEnum, ApplicationStatusEnum,
    Resume, Interview, InterviewQuestion, InterviewResponse,
    InterviewEvaluation, MediaAsset
)
from app.services.cloudinary_service import CloudinaryService

@pytest.fixture
def ai_hub_setup(db, recruiter_user, candidate_user):
    recruiter = recruiter_user.recruiter_profile
    candidate = candidate_user.candidate_profile

    job = Job(
        recruiter_id=recruiter.id,
        title="Senior Distributed Systems Engineer",
        description="Build high-throughput event-driven microservices",
        location="Remote",
        status=JobStatusEnum.ACTIVE
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    resume = Resume(
        candidate_id=candidate.id,
        file_name="distributed_systems_resume.pdf",
        file_path="uploads/distributed_systems_resume.pdf",
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

    return {
        "recruiter": recruiter,
        "candidate": candidate,
        "job": job,
        "application": app_record
    }


def test_ai_question_generation(client, recruiter_token, ai_hub_setup):
    """Verify recruiter can generate tailored questions based on job details and difficulty."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    res = client.post(
        "/api/v1/interviews/ai-questions/generate",
        json={
            "job_id": ai_hub_setup["job"].id,
            "job_title": "Senior Distributed Systems Engineer",
            "difficulty": "SENIOR",
            "question_count": 5,
            "categories": ["TECHNICAL", "PROBLEM_SOLVING", "BEHAVIORAL"]
        },
        headers=headers
    )
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) == 5
    assert all("question_text" in q for q in questions)
    assert all("question_type" in q for q in questions)
    assert all("expected_concepts" in q for q in questions)


def test_four_interview_modes_scheduling_and_configuration(client, recruiter_token, candidate_token, ai_hub_setup):
    """Test scheduling and configuration across 4 interview workflows: Human, AI_LIVE, HYBRID, CONFIGURED."""
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # 1. Option A: Human Live Interview
    res_a = client.post(
        "/api/v1/interviews",
        json={
            "application_id": ai_hub_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "HUMAN",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "duration_minutes": 45,
            "round_title": "Round 1 - Human Technical Screen"
        },
        headers=r_headers
    )
    assert res_a.status_code == 201
    int_a = res_a.json()
    assert int_a["interview_mode"] == "HUMAN"

    # 2. Option B: AI Live Interview
    res_b = client.post(
        "/api/v1/interviews",
        json={
            "application_id": ai_hub_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "AI_LIVE",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "duration_minutes": 30,
            "round_title": "Round 1 - AI Conversational Screen",
            "ai_config_json": {
                "difficulty": "INTERMEDIATE",
                "voice": "nova",
                "question_count": 2
            }
        },
        headers=r_headers
    )
    assert res_b.status_code == 201
    int_b = res_b.json()
    assert int_b["interview_mode"] == "AI_LIVE"

    # Configure questions for int_b
    q_res = client.post(
        f"/api/v1/interviews/{int_b['id']}/configure-ai",
        json={
            "interview_mode": "AI_LIVE",
            "duration_minutes": 30,
            "difficulty": "INTERMEDIATE",
            "voice": "nova",
            "questions": [
                {
                    "question_text": "Explain the difference between optimistic and pessimistic locking in relational databases.",
                    "question_type": "TECHNICAL",
                    "source": "AI_GENERATED",
                    "sequence_number": 1,
                    "expected_concepts": ["concurrency", "row locking", "version timestamp", "deadlock"],
                    "max_duration_seconds": 180
                },
                {
                    "question_text": "Describe how you would design an idempotency key mechanism for payment processing APIs.",
                    "question_type": "PROBLEM_SOLVING",
                    "source": "AI_GENERATED",
                    "sequence_number": 2,
                    "expected_concepts": ["unique constraint", "Redis key expiration", "atomic transaction"],
                    "max_duration_seconds": 210
                }
            ]
        },
        headers=r_headers
    )
    assert q_res.status_code == 200
    configured = q_res.json()
    assert configured["interview_mode"] == "AI_LIVE"

    # 3. Retrieve Questions
    get_q = client.get(f"/api/v1/interviews/{int_b['id']}/questions", headers=r_headers)
    assert get_q.status_code == 200
    q_list = get_q.json()
    assert len(q_list) == 2
    assert q_list[0]["sequence_number"] == 1
    assert "optimistic and pessimistic locking" in q_list[0]["question_text"]

    # 4. Check AI state
    state_res = client.get(f"/api/v1/interviews/{int_b['id']}/ai-state", headers=r_headers)
    assert state_res.status_code == 200
    state = state_res.json()
    assert state["current_question_index"] == 0
    assert state["total_questions"] == 2
    assert state["current_question"]["id"] == q_list[0]["id"]

    # Advance AI to next question
    adv_res = client.post(f"/api/v1/interviews/{int_b['id']}/ai-state/advance", headers=r_headers)
    assert adv_res.status_code == 200
    adv_state = adv_res.json()
    assert adv_state["current_question_index"] == 1
    assert adv_state["current_question"]["id"] == q_list[1]["id"]


def test_hybrid_interview_and_recruiter_takeover(client, recruiter_token, ai_hub_setup):
    """Test Hybrid interview mode with live recruiter takeover and handover."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    # Schedule Option C: HYBRID
    res = client.post(
        "/api/v1/interviews",
        json={
            "application_id": ai_hub_setup["application"].id,
            "interview_type": "ONLINE",
            "interview_mode": "HYBRID",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "duration_minutes": 45,
            "round_title": "Round 1 - Hybrid AI & Recruiter Interview"
        },
        headers=headers
    )
    assert res.status_code == 201
    interview = res.json()
    assert interview["interview_mode"] == "HYBRID"
    assert interview["ai_takeover_status"] == "AI_ACTIVE"

    # Recruiter takes over conversation
    takeover_res = client.post(
        f"/api/v1/interviews/{interview['id']}/hybrid/takeover",
        json={"takeover": True},
        headers=headers
    )
    assert takeover_res.status_code == 200
    assert takeover_res.json()["ai_takeover_status"] == "RECRUITER_ACTIVE"

    # Recruiter hands back control to AI
    handback_res = client.post(
        f"/api/v1/interviews/{interview['id']}/hybrid/takeover",
        json={"takeover": False},
        headers=headers
    )
    assert handback_res.status_code == 200
    assert handback_res.json()["ai_takeover_status"] == "AI_ACTIVE"


def test_ai_interview_responses_and_structured_evaluation(db, client, recruiter_token, candidate_token, ai_hub_setup):
    """Test submitting question-level responses, generating structured evaluations, and confidentiality."""
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}
    c_headers = {"Authorization": f"Bearer {candidate_token}"}

    # Create interview with question
    int_rec = Interview(
        application_id=ai_hub_setup["application"].id,
        recruiter_id=ai_hub_setup["recruiter"].id,
        candidate_id=ai_hub_setup["candidate"].id,
        interview_type="ONLINE",
        interview_mode="AI_LIVE",
        scheduled_time=datetime.now(timezone.utc),
        duration_minutes=30,
        status="IN_PROGRESS"
    )
    db.add(int_rec)
    db.commit()
    db.refresh(int_rec)

    q_rec = InterviewQuestion(
        interview_id=int_rec.id,
        question_text="How do you handle schema migrations with zero downtime in PostgreSQL?",
        question_type="TECHNICAL",
        sequence_number=1,
        expected_concepts=["expand and contract", "concurrent index creation"],
        max_duration_seconds=180
    )
    db.add(q_rec)
    db.commit()
    db.refresh(q_rec)

    # 1. Ingest question response
    resp_res = client.post(
        f"/api/v1/interviews/{int_rec.id}/ai-responses",
        json=[
            {
                "question_id": q_rec.id,
                "transcript": "I utilize the expand-and-contract pattern. New columns are added nullable, double-writing occurs, and old columns are phased out.",
                "response_duration": 85.5,
                "score": 4.5,
                "strengths": "Detailed understanding of expand and contract pattern.",
                "weaknesses": "Could detail lock timeouts."
            }
        ],
        headers=r_headers
    )
    assert resp_res.status_code == 200
    saved_resp = resp_res.json()
    assert len(saved_resp) == 1
    assert saved_resp[0]["score"] == 4.5

    # 2. Generate structured evaluation
    eval_res = client.post(f"/api/v1/interviews/{int_rec.id}/evaluation/generate", headers=r_headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["overall_score"] >= 4.0
    assert "technical_depth" in eval_data["competency_scores"]
    assert eval_data["review_status"] == "PENDING_REVIEW"

    # 3. Recruiter overrides / approves evaluation
    override_res = client.put(
        f"/api/v1/interviews/{int_rec.id}/evaluation",
        json={
            "overall_score": 4.8,
            "review_status": "ACCEPTED",
            "recruiter_notes": "Outstanding response on expand-contract pattern. Clear hire signal."
        },
        headers=r_headers
    )
    assert override_res.status_code == 200
    updated_eval = override_res.json()
    assert updated_eval["overall_score"] == 4.8
    assert updated_eval["review_status"] == "ACCEPTED"
    assert "Clear hire signal" in updated_eval["recruiter_notes"]

    # 4. Confidentiality check: candidate CANNOT view confidential evaluation (403 Forbidden)
    cand_eval_res = client.get(f"/api/v1/interviews/{int_rec.id}/evaluation", headers=c_headers)
    assert cand_eval_res.status_code == 403


def test_cloudinary_ai_interview_recording_archival(db, client, recruiter_token, ai_hub_setup):
    """Test archiving AI interview recording into Cloudinary folder 'skillsphere/ai-interviews/'."""
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    int_rec = Interview(
        application_id=ai_hub_setup["application"].id,
        recruiter_id=ai_hub_setup["recruiter"].id,
        candidate_id=ai_hub_setup["candidate"].id,
        interview_type="ONLINE",
        interview_mode="AI_LIVE",
        scheduled_time=datetime.now(timezone.utc),
        duration_minutes=30,
        status="IN_PROGRESS"
    )
    db.add(int_rec)
    db.commit()
    db.refresh(int_rec)

    res = client.post(f"/api/v1/interviews/{int_rec.id}/archive-recording", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["folder"] == "skillsphere/ai-interviews"
    assert "skillsphere/ai-interviews" in data["public_id"]
    assert data["media_asset_id"] is not None

    # Verify MediaAsset exists in DB
    asset = db.query(MediaAsset).filter(MediaAsset.id == data["media_asset_id"]).first()
    assert asset is not None
    assert asset.folder == "skillsphere/ai-interviews"
    assert asset.interview_id == int_rec.id
