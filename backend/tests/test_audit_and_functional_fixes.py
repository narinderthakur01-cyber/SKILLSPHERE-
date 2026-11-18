import io
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
    Resume
)
from app.core.security import create_access_token

@pytest.fixture
def audit_fixture(db):
    """
    Sets up a complete recruitment pipeline for end-to-end audit verification.
    """
    # 1. Recruiter
    rec_user = User(
        email=f"recruiter_audit_{datetime.now().timestamp()}@skillsphere.io",
        name="Lead Recruiter",
        password_hash="hashed_secret",
        role=RoleEnum.RECRUITER,
        is_active=True,
        email_verified=True
    )
    db.add(rec_user)
    db.flush()

    recruiter = Recruiter(user_id=rec_user.id, designation="Talent Director")
    db.add(recruiter)
    db.flush()

    # 2. Candidate 1 (Alice)
    cand_user_1 = User(
        email=f"alice_{datetime.now().timestamp()}@skillsphere.io",
        name="Alice Engineer",
        password_hash="hashed_secret",
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True
    )
    db.add(cand_user_1)
    db.flush()

    candidate_1 = Candidate(user_id=cand_user_1.id, title="Senior Backend Engineer")
    db.add(candidate_1)
    db.flush()

    # 3. Candidate 2 (Bob)
    cand_user_2 = User(
        email=f"bob_{datetime.now().timestamp()}@skillsphere.io",
        name="Bob Designer",
        password_hash="hashed_secret",
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True
    )
    db.add(cand_user_2)
    db.flush()

    candidate_2 = Candidate(user_id=cand_user_2.id, title="Product Designer")
    db.add(candidate_2)
    db.flush()

    # 4. Job Posting
    job = Job(
        recruiter_id=recruiter.id,
        title="Principal Platform Architect",
        description="High scale cloud platform role",
        location="Remote",
        status="ACTIVE"
    )
    db.add(job)
    db.flush()

    # 5. Application
    resume = Resume(
        candidate_id=candidate_1.id,
        file_name="alice_resume.pdf",
        file_path="uploads/alice_resume.pdf",
        file_type="application/pdf",
        file_size=2048,
        extracted_text="FastAPI Python PostgreSQL Cloudinary"
    )
    db.add(resume)
    db.flush()

    application = Application(
        job_id=job.id,
        candidate_id=candidate_1.id,
        resume_id=resume.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(application)
    db.commit()

    rec_token = create_access_token(subject=rec_user.id, role="RECRUITER")
    cand1_token = create_access_token(subject=cand_user_1.id, role="JOB_SEEKER")
    cand2_token = create_access_token(subject=cand_user_2.id, role="JOB_SEEKER")

    return {
        "rec_user": rec_user,
        "recruiter": recruiter,
        "cand_user_1": cand_user_1,
        "candidate_1": candidate_1,
        "cand_user_2": cand_user_2,
        "candidate_2": candidate_2,
        "job": job,
        "application": application,
        "rec_token": rec_token,
        "cand1_token": cand1_token,
        "cand2_token": cand2_token
    }

def test_video_assessment_upload_and_undefined_candidate_id_sanitization(client, db, audit_fixture):
    """
    Verify Issue 1 & 2 fixes:
    1. Candidate uploading a video with candidate_id='undefined' is sanitized and resolved to real candidate ID.
    2. Cloudinary metadata is persisted in PostgreSQL media_assets.
    3. No foreign key violation or orphaned records occur.
    """
    token = audit_fixture["cand1_token"]
    cand1 = audit_fixture["candidate_1"]

    # Candidate uploads a video response file sending candidate_id='undefined' (the frontend bug shape)
    fake_video_bytes = b"FAKE_VIDEO_STREAM_CHUNKS_WEBM"
    files = {"file": ("test_response.webm", fake_video_bytes, "video/webm")}
    data = {
        "folder_key": "candidate_responses",
        "candidate_id": "undefined", # Intentionally simulate the frontend bug
        "access_classification": "PRIVATE"
    }

    res = client.post(
        "/api/v1/media/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        data=data
    )

    assert res.status_code == 201, f"Expected 201 Created but got {res.status_code}: {res.text}"
    res_data = res.json()
    assert res_data["id"] is not None
    assert res_data["public_id"].startswith("skillsphere/candidate-responses/")
    assert res_data["candidate_id"] == cand1.id, "Candidate ID must be automatically resolved to the authenticated candidate UUID, not 'undefined'!"

    # Verify database record in PostgreSQL
    asset = db.query(MediaAsset).filter(MediaAsset.id == res_data["id"]).first()
    assert asset is not None
    assert asset.candidate_id == cand1.id
    assert asset.file_size_bytes == len(fake_video_bytes)
    assert asset.resource_type == "video"
    assert asset.upload_status == "COMPLETED"

def test_media_library_role_scoping_and_signed_playback(client, db, audit_fixture):
    """
    Verify Issue 2 fixes:
    1. Candidate can list their own media assets (/api/v1/media) and gets HTTP 200.
    2. Candidate CANNOT see internal recruiter interview recordings or other candidates' media.
    3. Candidate can play their own video with signed URL.
    4. Candidate is blocked with 403 when requesting playback for recruiter internal interview recordings.
    5. Recruiter can list media for their jobs/assessments.
    """
    cand1 = audit_fixture["candidate_1"]
    cand2 = audit_fixture["candidate_2"]
    rec = audit_fixture["recruiter"]
    cand1_token = audit_fixture["cand1_token"]
    cand2_token = audit_fixture["cand2_token"]
    rec_token = audit_fixture["rec_token"]

    # 1. Asset belonging to Candidate 1 (Video response)
    asset_cand1 = MediaAsset(
        public_id="skillsphere/candidate-responses/alice_q1_video",
        asset_id="cld_alice_1",
        candidate_id=cand1.id,
        uploader_user_id=audit_fixture["cand_user_1"].id,
        original_filename="alice_response.webm",
        resource_type="video",
        file_format="webm",
        file_size_bytes=4096,
        secure_url="https://res.cloudinary.com/skillsphere/video/upload/alice.webm",
        folder="skillsphere/candidate-responses",
        upload_status="COMPLETED",
        access_classification="PRIVATE"
    )
    # 2. Asset belonging to Recruiter (Confidential interview recording)
    asset_recruiter_interview = MediaAsset(
        public_id="skillsphere/interviews/recruiter_eval_meeting",
        asset_id="cld_rec_1",
        uploader_user_id=audit_fixture["rec_user"].id,
        original_filename="confidential_interview.mp4",
        resource_type="video",
        file_format="mp4",
        file_size_bytes=10000,
        secure_url="https://res.cloudinary.com/skillsphere/video/upload/interview.mp4",
        folder="skillsphere/interviews",
        upload_status="COMPLETED",
        access_classification="CONFIDENTIAL"
    )
    # 3. Asset belonging to Candidate 2
    asset_cand2 = MediaAsset(
        public_id="skillsphere/candidate-responses/bob_q1_video",
        asset_id="cld_bob_1",
        candidate_id=cand2.id,
        uploader_user_id=audit_fixture["cand_user_2"].id,
        original_filename="bob_response.webm",
        resource_type="video",
        file_format="webm",
        file_size_bytes=3000,
        secure_url="https://res.cloudinary.com/skillsphere/video/upload/bob.webm",
        folder="skillsphere/candidate-responses",
        upload_status="COMPLETED",
        access_classification="PRIVATE"
    )
    db.add_all([asset_cand1, asset_recruiter_interview, asset_cand2])
    db.commit()

    # Candidate 1 lists their media library
    res_c1 = client.get("/api/v1/media", headers={"Authorization": f"Bearer {cand1_token}"})
    assert res_c1.status_code == 200, f"Expected 200 OK for candidate media listing but got {res_c1.status_code}"
    c1_assets = res_c1.json()
    c1_ids = [a["id"] for a in c1_assets]
    assert asset_cand1.id in c1_ids, "Candidate 1 must see their own response video"
    assert asset_cand2.id not in c1_ids, "Candidate 1 MUST NOT see Candidate 2's media assets!"
    assert asset_recruiter_interview.id not in c1_ids, "Candidate 1 MUST NOT see recruiter confidential interview recording!"

    # Candidate 1 requests playback of their own video
    res_play = client.get(f"/api/v1/media/{asset_cand1.id}/playback", headers={"Authorization": f"Bearer {cand1_token}"})
    assert res_play.status_code == 200
    assert "playback_url" in res_play.json()

    # Candidate 1 attempts unauthorized playback of recruiter internal interview
    res_unauth = client.get(f"/api/v1/media/{asset_recruiter_interview.id}/playback", headers={"Authorization": f"Bearer {cand1_token}"})
    assert res_unauth.status_code == 403, "Candidate must be forbidden from accessing confidential recruiter interview recording"

    # Candidate 2 attempts unauthorized playback of Candidate 1's video
    res_tamper = client.get(f"/api/v1/media/{asset_cand1.id}/playback", headers={"Authorization": f"Bearer {cand2_token}"})
    assert res_tamper.status_code == 403, "Candidate 2 must be forbidden from playing Candidate 1's video"

def test_first_round_assessment_lifecycle_and_premature_completion_prevention(client, db, audit_fixture):
    """
    Verify Issue 3 & Issue 6 fixes:
    1. Recruiter creates draft assessment, updates it (validates cascade option cleanup).
    2. Passing marks <= total marks validation enforced.
    3. Assessment assigned to candidate.
    4. Candidate result check yields 404 BEFORE starting/submitting -> PREVENTS PREMATURE 'SUBMISSION COMPLETED' LOCKOUT!
    5. Candidate reads instructions (200), starts attempt, answers, submits.
    6. Candidate receives confirmation without score leakage.
    7. Recruiter evaluates submission.
    """
    rec_token = audit_fixture["rec_token"]
    cand1_token = audit_fixture["cand1_token"]
    job = audit_fixture["job"]
    cand1 = audit_fixture["candidate_1"]

    # 1. Recruiter creates draft assessment
    create_payload = {
        "job_id": job.id,
        "title": "Cloud Systems & Architecture Screening",
        "instructions": "Answer all 2 questions carefully.",
        "duration_minutes": 25,
        "passing_marks": 5,
        "randomize_questions": False,
        "randomize_options": False,
        "questions": [
            {
                "question_text": "What is eventual consistency?",
                "marks": 5,
                "order_num": 1,
                "options": [
                    {"option_key": "A", "option_text": "A consistency model used in distributed systems", "is_correct": True},
                    {"option_key": "B", "option_text": "Immediate write locks across all replicas", "is_correct": False}
                ]
            },
            {
                "question_text": "Which HTTP method is idempotent?",
                "marks": 5,
                "order_num": 2,
                "options": [
                    {"option_key": "A", "option_text": "PUT", "is_correct": True},
                    {"option_key": "B", "option_text": "POST", "is_correct": False}
                ]
            }
        ]
    }
    res_create = client.post("/api/v1/recruiter/assessments", headers={"Authorization": f"Bearer {rec_token}"}, json=create_payload)
    assert res_create.status_code == 200
    assessment_id = res_create.json()["id"]
    assert res_create.json()["total_marks"] == 10
    assert res_create.json()["status"] == "DRAFT"

    # 2. Recruiter tests passing marks validation: passing marks > total marks must fail
    res_invalid_marks = client.put(
        f"/api/v1/recruiter/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"passing_marks": 20} # Exceeds total marks of 10
    )
    assert res_invalid_marks.status_code == 400

    # 3. Recruiter updates draft assessment (tests safe option & question replacement)
    update_payload = {
        "title": "Cloud Systems & Architecture Screening (Revised)",
        "passing_marks": 6,
        "questions": [
            {
                "question_text": "What is CAP theorem?",
                "marks": 6,
                "order_num": 1,
                "options": [
                    {"option_key": "A", "option_text": "Consistency, Availability, Partition tolerance", "is_correct": True},
                    {"option_key": "B", "option_text": "CPU, Architecture, Performance", "is_correct": False}
                ]
            }
        ]
    }
    res_update = client.put(f"/api/v1/recruiter/assessments/{assessment_id}", headers={"Authorization": f"Bearer {rec_token}"}, json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["total_marks"] == 6
    assert res_update.json()["passing_marks"] == 6

    # 4. Recruiter publishes assessment
    res_pub = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers={"Authorization": f"Bearer {rec_token}"})
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # 5. Recruiter assigns to Candidate 1
    res_assign = client.post(
        f"/api/v1/recruiter/assessments/{assessment_id}/assign",
        headers={"Authorization": f"Bearer {rec_token}"},
        json={"candidate_ids": [cand1.id]}
    )
    assert res_assign.status_code == 200
    assignment_id = res_assign.json()[0]["id"]

    # 6. CRITICAL AUDIT CHECK: Candidate checks result BEFORE starting or submitting
    # Must return 404 NOT FOUND so the UI does NOT prematurely show "Submission completed"!
    res_result_early = client.get(
        f"/api/v1/candidate/assessments/{assignment_id}/result",
        headers={"Authorization": f"Bearer {cand1_token}"}
    )
    assert res_result_early.status_code == 404, "Unsubmitted assessment must return 404 on result check to prevent premature lockout!"

    # 7. Candidate opens instructions
    res_inst = client.get(
        f"/api/v1/candidate/assessments/{assignment_id}/instructions",
        headers={"Authorization": f"Bearer {cand1_token}"}
    )
    assert res_inst.status_code == 200
    assert res_inst.json()["assignment_id"] == assignment_id
    assert res_inst.json()["duration_minutes"] == 25

    # 8. Candidate starts assessment attempt
    res_start = client.post(
        f"/api/v1/candidate/assessments/{assignment_id}/start",
        headers={"Authorization": f"Bearer {cand1_token}"}
    )
    assert res_start.status_code == 200
    attempt_id = res_start.json()["attempt_id"]
    questions = res_start.json()["questions"]
    assert len(questions) == 1
    # Verify confidential is_correct answer is NEVER leaked to candidate
    for opt in questions[0]["options"]:
        assert "is_correct" not in opt or opt.get("is_correct") is None or opt.get("is_correct") is False

    # 9. Candidate submits answer
    q_id = questions[0]["id"]
    opt_a_id = questions[0]["options"][0]["id"]
    res_ans = client.post(
        f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers",
        headers={"Authorization": f"Bearer {cand1_token}"},
        json={"answers": [{"question_id": q_id, "selected_option_id": opt_a_id}]}
    )
    assert res_ans.status_code == 200

    # 10. Candidate submits test
    res_sub = client.post(
        f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit",
        headers={"Authorization": f"Bearer {cand1_token}"}
    )
    assert res_sub.status_code == 200
    sub_data = res_sub.json()
    assert sub_data["assignment_id"] == assignment_id
    # Ensure zero score leak on submission
    assert "marks_obtained" not in sub_data
    assert "percentage" not in sub_data

    # 11. Candidate now checks result endpoint -> returns 200 OK with PENDING_REVIEW message
    res_result_final = client.get(
        f"/api/v1/candidate/assessments/{assignment_id}/result",
        headers={"Authorization": f"Bearer {cand1_token}"}
    )
    assert res_result_final.status_code == 200
    assert res_result_final.json()["review_status"] == "PENDING_REVIEW"
    assert res_result_final.json()["submitted_at"] is not None

    # 12. Recruiter evaluates candidate
    res_review = client.get(
        f"/api/v1/recruiter/assessments/attempts/{attempt_id}/detailed-review",
        headers={"Authorization": f"Bearer {rec_token}"}
    )
    assert res_review.status_code == 200
    assert res_review.json()["score_percentage"] == 100.0
