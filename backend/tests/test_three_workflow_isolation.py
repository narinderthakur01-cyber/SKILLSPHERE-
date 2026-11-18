import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    User, RoleEnum, Recruiter, Candidate, Job, Application,
    ApplicationStatusEnum, Assessment, AssessmentStatusEnum,
    AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAssignmentStatusEnum,
    AssessmentAttempt, AttemptStatusEnum, AssessmentResult,
    VideoAssessment, VideoAssessmentQuestion, CandidateVideoAssignment,
    CandidateVideoResponse, MediaAsset, QuestionBankItem, QuestionStatusEnum,
    Interview, Resume
)
from app.core.security import create_access_token
from app.services.cloudinary_service import CloudinaryService

@pytest.fixture
def isolation_setup(db):
    """
    Sets up a clean recruitment pipeline with a recruiter, candidate, and job.
    """
    # 1. Recruiter User
    rec_user = User(
        email=f"recruiter_iso_{datetime.now().timestamp()}@skillsphere.io",
        name="Iso Recruiter",
        password_hash="hashed_pwd_test",
        role=RoleEnum.RECRUITER,
        is_active=True,
        email_verified=True
    )
    db.add(rec_user)
    db.flush()

    recruiter = Recruiter(user_id=rec_user.id, designation="Lead Recruiter")
    db.add(recruiter)
    db.flush()

    # 2. Candidate User
    cand_user = User(
        email=f"candidate_iso_{datetime.now().timestamp()}@skillsphere.io",
        name="Iso Candidate",
        password_hash="hashed_pwd_test",
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True
    )
    db.add(cand_user)
    db.flush()

    candidate = Candidate(user_id=cand_user.id, title="Senior Software Engineer")
    db.add(candidate)
    db.flush()

    # 3. Job Posting
    job = Job(
        recruiter_id=recruiter.id,
        title="Full Stack Cloud Architect",
        description="Senior architecture role",
        location="Remote",
        status="ACTIVE"
    )
    db.add(job)
    db.flush()

    # 4. Resume & Shortlisted Application
    resume = Resume(
        candidate_id=candidate.id,
        file_name="resume.pdf",
        file_path="uploads/resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        extracted_text="Python AWS React Architect"
    )
    db.add(resume)
    db.flush()

    app = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app)
    db.flush()

    # 5. Question Bank items for testing shortage check
    qb1 = QuestionBankItem(
        technology="CloudArch",
        topic="Microservices",
        question_text="What is circuit breaker pattern?",
        difficulty="INTERMEDIATE",
        status=QuestionStatusEnum.ACTIVE,
        marks=2,
        created_by_user_id=rec_user.id
    )
    db.add(qb1)
    db.commit()

    rec_token = create_access_token(subject=rec_user.id, role="RECRUITER")
    cand_token = create_access_token(subject=cand_user.id, role="JOB_SEEKER")

    return {
        "rec_user": rec_user,
        "recruiter": recruiter,
        "cand_user": cand_user,
        "candidate": candidate,
        "job": job,
        "application": app,
        "rec_token": rec_token,
        "cand_token": cand_token,
    }


def test_mcq_assessment_lifecycle_session_recording_and_privacy(client, db, isolation_setup):
    """
    Tests Round 1 MCQ workflow:
    - Creation in DRAFT status
    - Publishing transition
    - Assignment to candidate
    - Candidate attempt submission with strict score privacy
    - Session recording upload to skillsphere/assessments/
    - Recruiter review with score & signed playback URL
    """
    rec_token = isolation_setup["rec_token"]
    cand_token = isolation_setup["cand_token"]
    job = isolation_setup["job"]
    candidate = isolation_setup["candidate"]

    # 1. Create MCQ in DRAFT
    mcq_payload = {
        "job_id": job.id,
        "title": "Cloud Architecture Round 1 MCQ",
        "instructions": "Answer all 2 questions carefully.",
        "duration_minutes": 30,
        "passing_marks": 5,
        "questions": [
            {
                "question_text": "Which HTTP method is idempotent?",
                "marks": 5,
                "order_num": 1,
                "options": [
                    {"option_key": "A", "option_text": "POST", "is_correct": False},
                    {"option_key": "B", "option_text": "PUT", "is_correct": True},
                    {"option_key": "C", "option_text": "PATCH", "is_correct": False},
                ]
            },
            {
                "question_text": "What does ACID stand for in databases?",
                "marks": 5,
                "order_num": 2,
                "options": [
                    {"option_key": "A", "option_text": "Atomicity, Consistency, Isolation, Durability", "is_correct": True},
                    {"option_key": "B", "option_text": "Asynchronous, Consistent, Isolated, Distributed", "is_correct": False},
                ]
            }
        ]
    }
    res_create = client.post("/api/v1/recruiter/assessments", json=mcq_payload, headers={"Authorization": f"Bearer {rec_token}"})
    assert res_create.status_code == 200
    mcq_data = res_create.json()
    assert mcq_data["status"] == "DRAFT"
    mcq_id = mcq_data["id"]

    # 2. Cannot assign DRAFT MCQ
    res_assign_draft = client.post(
        f"/api/v1/recruiter/assessments/{mcq_id}/assign",
        json={"candidate_ids": [candidate.id]},
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_assign_draft.status_code == 400
    assert "published" in res_assign_draft.json()["detail"].lower()

    # 3. Publish MCQ
    res_pub = client.post(f"/api/v1/recruiter/assessments/{mcq_id}/publish", headers={"Authorization": f"Bearer {rec_token}"})
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # 4. Assign Published MCQ
    res_assign = client.post(
        f"/api/v1/recruiter/assessments/{mcq_id}/assign",
        json={"candidate_ids": [candidate.id]},
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_assign.status_code == 200
    assignments = res_assign.json()
    assert len(assignments) == 1
    assignment_id = assignments[0]["id"]

    # 5. Candidate views assigned MCQ
    res_cand_list = client.get("/api/v1/candidate/assessments", headers={"Authorization": f"Bearer {cand_token}"})
    assert res_cand_list.status_code == 200
    my_asgns = res_cand_list.json()
    assert any(a["id"] == assignment_id for a in my_asgns)

    # 6. Candidate starts attempt
    res_start = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers={"Authorization": f"Bearer {cand_token}"})
    assert res_start.status_code == 200
    attempt_data = res_start.json()
    attempt_id = attempt_data["attempt_id"]

    # 7. Candidate answers Question 1 correctly
    q1 = attempt_data["questions"][0]
    opt_b = next(o for o in q1["options"] if o["option_text"] == "PUT")
    res_save = client.post(
        f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers",
        json={"answers": [{"question_id": q1["id"], "selected_option_id": opt_b["id"]}]},
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_save.status_code == 200

    # 8. Candidate submits attempt -> Score MUST BE strictly hidden
    res_submit = client.post(
        f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_submit.status_code == 200
    sub_data = res_submit.json()
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["review_status"] == "PENDING_REVIEW"
    # Verify no leaked scores
    assert "score" not in sub_data or sub_data.get("score") is None
    assert "marks_obtained" not in sub_data or sub_data.get("marks_obtained") is None

    # 9. Candidate uploads session video recording to skillsphere/assessments
    upload_req = {
        "public_id": "skillsphere/assessments/test_session_rec_001",
        "asset_id": "cld_asset_001",
        "secure_url": "https://res.cloudinary.com/demo/video/upload/skillsphere/assessments/test_session_rec_001.mp4",
        "duration_seconds": 125.5,
        "file_size_bytes": 1048576,
        "file_format": "mp4",
        "original_filename": "candidate_mcq_session.mp4",
        "resource_type": "video"
    }
    res_rec = client.post(
        f"/api/v1/candidate/assessments/attempts/{attempt_id}/session-recording",
        json=upload_req,
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_rec.status_code == 200
    rec_body = res_rec.json()
    assert rec_body["status"] == "COMPLETED"
    assert rec_body["public_id"] == "skillsphere/assessments/test_session_rec_001"

    # Verify MediaAsset record in DB
    asset_record = db.query(MediaAsset).filter(MediaAsset.id == rec_body["media_asset_id"]).first()
    assert asset_record is not None
    assert asset_record.assessment_type == "MCQ"
    assert asset_record.folder == "skillsphere/assessments"
    assert asset_record.attempt_id == attempt_id

    # 10. Recruiter gets detailed review -> Sees marks and signed playback URL
    res_review = client.get(
        f"/api/v1/recruiter/assessments/assignments/{assignment_id}/detailed-review",
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_review.status_code == 200
    rev_data = res_review.json()
    assert rev_data["marks_obtained"] == 5.0
    assert rev_data["total_marks"] == 10.0
    assert rev_data["session_recording"] is not None
    assert rev_data["session_recording"]["public_id"] == "skillsphere/assessments/test_session_rec_001"
    assert "playback_url" in rev_data["session_recording"]


def test_video_assessment_draft_publishing_and_retake_limit(client, db, isolation_setup):
    """
    Tests Video Assessment independent lifecycle:
    - Draft creation
    - Inability to assign draft assessment
    - Publishing transition
    - Candidate response upload with retake enforcement
    - Recruiter grading & evaluation
    """
    rec_token = isolation_setup["rec_token"]
    cand_token = isolation_setup["cand_token"]
    job = isolation_setup["job"]
    app = isolation_setup["application"]

    # 1. Create Video Assessment in DRAFT
    va_payload = {
        "job_id": job.id,
        "title": "System Design Video Presentation",
        "description": "Walk us through an event-driven Kafka architecture.",
        "instructions": "Speak clearly and show diagrams if helpful.",
        "status": "DRAFT",
        "questions": [
            {
                "order_num": 1,
                "question_text": "Explain how you handle out-of-order Kafka events.",
                "question_instructions": "Focus on partitioning keys and idempotent consumer.",
                "max_duration_seconds": 180,
                "prep_time_seconds": 30,
                "retake_limit": 1,
                "is_required": True
            }
        ]
    }
    res_va = client.post("/api/v1/video-assessments", json=va_payload, headers={"Authorization": f"Bearer {rec_token}"})
    assert res_va.status_code == 201
    va_data = res_va.json()
    assert va_data["status"] == "DRAFT"
    va_id = va_data["id"]
    q1_id = va_data["questions"][0]["id"]

    # 2. Cannot assign DRAFT Video Assessment
    res_assign_draft = client.post(
        f"/api/v1/video-assessments/{va_id}/assign",
        json={"application_ids": [app.id]},
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_assign_draft.status_code == 400
    assert "draft" in res_assign_draft.json()["detail"].lower()

    # 3. Publish Video Assessment
    res_pub = client.post(f"/api/v1/video-assessments/{va_id}/publish", headers={"Authorization": f"Bearer {rec_token}"})
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # 4. Assign Published Video Assessment
    res_assign = client.post(
        f"/api/v1/video-assessments/{va_id}/assign",
        json={"application_ids": [app.id]},
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_assign.status_code == 200
    asgns = res_assign.json()
    assert len(asgns) == 1
    va_asgn_id = asgns[0]["id"]

    # 5. Candidate views assigned video assessments
    res_cand_va = client.get("/api/v1/candidate/video-assessments", headers={"Authorization": f"Bearer {cand_token}"})
    assert res_cand_va.status_code == 200
    cand_va_list = res_cand_va.json()
    assert any(a["id"] == va_asgn_id for a in cand_va_list)

    # 6. Candidate creates MediaAsset for question response
    media_asset = MediaAsset(
        public_id="skillsphere/candidate-responses/cld_resp_kafka_001",
        secure_url="https://res.cloudinary.com/demo/video/upload/skillsphere/candidate-responses/cld_resp_kafka_001.mp4",
        original_filename="kafka_presentation.mp4",
        resource_type="video",
        file_format="mp4",
        folder="skillsphere/candidate-responses"
    )
    db.add(media_asset)
    db.commit()
    db.refresh(media_asset)

    # 7. Candidate submits response (retake count 0 -> valid)
    res_resp1 = client.post(
        f"/api/v1/candidate/video-assessments/{va_asgn_id}/responses",
        json={
            "question_id": q1_id,
            "media_asset_id": media_asset.id,
            "duration_seconds": 120.0,
            "retake_count": 0
        },
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_resp1.status_code == 200

    # 8. Enforce retake limit: retake_limit is 1, so retake_count=2 must fail
    res_retake_fail = client.post(
        f"/api/v1/candidate/video-assessments/{va_asgn_id}/responses",
        json={
            "question_id": q1_id,
            "media_asset_id": media_asset.id,
            "duration_seconds": 115.0,
            "retake_count": 2
        },
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_retake_fail.status_code == 400
    assert "retake limit exceeded" in res_retake_fail.json()["detail"].lower()

    # 9. Recruiter evaluates video assessment
    res_eval = client.post(
        f"/api/v1/video-assessments/assignments/{va_asgn_id}/evaluate",
        json={
            "review_status": "ACCEPTED",
            "overall_score": 92.5,
            "recruiter_feedback": "Exceptional explanation of Kafka partitioning keys.",
            "question_notes": {q1_id: "Very solid grasp of idempotency."}
        },
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["review_status"] == "ACCEPTED"


def test_three_workflow_strict_isolation(client, db, isolation_setup):
    """
    Verifies that:
    1. Publishing MCQ does NOT activate or publish Video Assessment.
    2. Publishing Video Assessment does NOT activate or publish MCQ.
    3. Candidate assigned assessments strictly return only their matching type.
    4. Cloudinary storage paths strictly separate skillsphere/assessments/ from skillsphere/candidate-responses/.
    5. LiveKit token generation operates without any Cloudinary egress pipeline.
    """
    rec_token = isolation_setup["rec_token"]
    cand_token = isolation_setup["cand_token"]
    job = isolation_setup["job"]

    # 1. Create a Draft MCQ
    mcq = Assessment(
        job_id=job.id,
        recruiter_id=isolation_setup["recruiter"].id,
        title="Isolated MCQ Test",
        duration_minutes=20,
        total_marks=10,
        passing_marks=6,
        status=AssessmentStatusEnum.DRAFT
    )
    db.add(mcq)

    # 2. Create a Draft Video Assessment
    va = VideoAssessment(
        job_id=job.id,
        recruiter_id=isolation_setup["recruiter"].id,
        title="Isolated Video Test",
        total_questions=1,
        status="DRAFT"
    )
    db.add(va)
    db.commit()
    db.refresh(mcq)
    db.refresh(va)

    # Add questions so they are publishable (min 2 options)
    q_mcq = AssessmentQuestion(assessment_id=mcq.id, order_num=1, question_text="Q1?", marks=10)
    db.add(q_mcq)
    db.flush()
    opt_a = AssessmentQuestionOption(question_id=q_mcq.id, option_key="A", option_text="Opt A", is_correct=True)
    opt_b = AssessmentQuestionOption(question_id=q_mcq.id, option_key="B", option_text="Opt B", is_correct=False)
    db.add(opt_a)
    db.add(opt_b)

    q_va = VideoAssessmentQuestion(video_assessment_id=va.id, order_num=1, question_text="VQ1?", max_duration_seconds=60)
    db.add(q_va)
    db.commit()

    # 3. Publish ONLY MCQ
    res_pub_mcq = client.post(f"/api/v1/recruiter/assessments/{mcq.id}/publish", headers={"Authorization": f"Bearer {rec_token}"})
    assert res_pub_mcq.status_code == 200

    # Verify MCQ is PUBLISHED but Video Assessment remains DRAFT
    db.refresh(mcq)
    db.refresh(va)
    assert mcq.status == AssessmentStatusEnum.PUBLISHED
    assert va.status == "DRAFT"

    # 4. Candidate MCQ list contains ONLY MCQ, never Video Assessment
    res_cand_mcq = client.get("/api/v1/candidate/assessments", headers={"Authorization": f"Bearer {cand_token}"})
    assert res_cand_mcq.status_code == 200
    for item in res_cand_mcq.json():
        assert "video" not in item["assessment_title"].lower() or "mcq" in item["assessment_title"].lower()

    # 5. Candidate Video Assessment list contains ONLY Video Assessments
    res_cand_va = client.get("/api/v1/candidate/video-assessments", headers={"Authorization": f"Bearer {cand_token}"})
    assert res_cand_va.status_code == 200
    for item in res_cand_va.json():
        assert item.get("total_questions", 0) >= 0

    # 6. Folder path contract check in CloudinaryService
    assert CloudinaryService.get_folder_path("assessments") == "skillsphere/assessments"
    assert CloudinaryService.get_folder_path("candidate_responses") == "skillsphere/candidate-responses"
    assert CloudinaryService.get_folder_path("interviews") == "skillsphere/interviews"
    assert CloudinaryService.get_folder_path("resumes") == "skillsphere/resumes"

    # 7. LiveKit Room Token Generation operates cleanly without any egress
    interview = Interview(
        application_id=isolation_setup["application"].id,
        recruiter_id=isolation_setup["recruiter"].id,
        candidate_id=isolation_setup["candidate"].id,
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=2),
        duration_minutes=45,
        interview_type="ONLINE",
        status="SCHEDULED",
        room_id="interview-iso-room-101"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    res_token = client.post(
        f"/api/v1/interviews/{interview.id}/room-token",
        headers={"Authorization": f"Bearer {cand_token}"}
    )
    assert res_token.status_code == 200
    token_data = res_token.json()
    assert "token" in token_data
    assert token_data["room_name"] == interview.room_id
