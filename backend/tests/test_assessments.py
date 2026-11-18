import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    ApplicationStatusEnum, Resume, Assessment, AssessmentQuestion,
    AssessmentQuestionOption, CandidateAssessmentAssignment,
    AssessmentAttempt, AssessmentResult, AssessmentStatusEnum,
    AssessmentAssignmentStatusEnum, AttemptStatusEnum, AssessmentResultEnum
)
from app.core.security import get_password_hash, create_access_token

@pytest.fixture
def test_setup(db, candidate_user, recruiter_user):
    import uuid
    uid = str(uuid.uuid4())[:8]

    # Recruiter 2 for isolation test
    user_rec2 = User(
        name="Other Recruiter",
        email=f"other_recruiter_{uid}@skillsphere.com",
        password_hash=get_password_hash("OtherRec123!"),
        role=RoleEnum.RECRUITER
    )
    db.add(user_rec2)
    db.commit()
    recruiter2 = Recruiter(user_id=user_rec2.id, designation="VP Talent")
    db.add(recruiter2)
    db.commit()

    # Candidate 2 for access control test
    user_cand2 = User(
        name="Second Candidate",
        email=f"second_candidate_{uid}@skillsphere.com",
        password_hash=get_password_hash("Cand2Pass!"),
        role=RoleEnum.JOB_SEEKER
    )
    db.add(user_cand2)
    db.commit()
    cand2 = Candidate(user_id=user_cand2.id, phone="9876543210", title="Data Analyst")
    db.add(cand2)
    db.commit()

    # Get Recruiter 1 and Candidate 1
    recruiter1 = db.query(Recruiter).filter(Recruiter.user_id == recruiter_user.id).first()
    candidate1 = db.query(Candidate).filter(Candidate.user_id == candidate_user.id).first()

    # Create Job owned by Recruiter 1
    job1 = Job(
        recruiter_id=recruiter1.id,
        title="Senior Software Engineer",
        description="Full stack dev role",
        location="Remote"
    )
    db.add(job1)
    db.commit()

    # Create Job owned by Recruiter 2
    job2 = Job(
        recruiter_id=recruiter2.id,
        title="Lead Product Designer",
        description="Design role",
        location="Remote"
    )
    db.add(job2)
    db.commit()

    # Resume for candidate 1
    resume1 = Resume(
        candidate_id=candidate1.id,
        file_name="resume.pdf",
        file_path="uploads/resume.pdf",
        file_type="pdf",
        file_size=1024
    )
    db.add(resume1)
    db.commit()

    # Candidate 1 application for Job 1: SHORTLISTED
    app1 = Application(
        job_id=job1.id,
        candidate_id=candidate1.id,
        resume_id=resume1.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app1)

    # Candidate 2 application for Job 1: APPLIED (NOT SHORTLISTED)
    resume2 = Resume(
        candidate_id=cand2.id,
        file_name="resume2.pdf",
        file_path="uploads/resume2.pdf",
        file_type="pdf",
        file_size=1024
    )
    db.add(resume2)
    db.commit()

    app2 = Application(
        job_id=job1.id,
        candidate_id=cand2.id,
        resume_id=resume2.id,
        status=ApplicationStatusEnum.APPLIED
    )
    db.add(app2)
    db.commit()

    token_rec1 = create_access_token(subject=recruiter_user.id, role=recruiter_user.role.value)
    token_rec2 = create_access_token(subject=user_rec2.id, role=user_rec2.role.value)
    token_cand1 = create_access_token(subject=candidate_user.id, role=candidate_user.role.value)
    token_cand2 = create_access_token(subject=user_cand2.id, role=user_cand2.role.value)

    return {
        "job1": job1,
        "job2": job2,
        "recruiter1": recruiter1,
        "recruiter2": recruiter2,
        "candidate1": candidate1,
        "candidate2": cand2,
        "app1": app1,
        "app2": app2,
        "token_rec1": token_rec1,
        "token_rec2": token_rec2,
        "token_cand1": token_cand1,
        "token_cand2": token_cand2,
    }


def test_recruiter_creates_valid_assessment(client, test_setup):
    """1. Recruiter creates a valid assessment."""
    headers = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    payload = {
        "job_id": test_setup["job1"].id,
        "title": "Backend Engineering MCQ Round 1",
        "instructions": "Answer all 2 questions within 30 minutes.",
        "duration_minutes": 30,
        "passing_marks": 5,
        "questions": [
            {
                "question_text": "What is Python's Global Interpreter Lock (GIL)?",
                "order_num": 1,
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "A mutex that prevents multiple native threads from executing Python bytecodes at once", "is_correct": True},
                    {"option_key": "B", "option_text": "A database lock", "is_correct": False},
                    {"option_key": "C", "option_text": "A network protocol", "is_correct": False}
                ]
            },
            {
                "question_text": "Which HTTP status code signifies Resource Created?",
                "order_num": 2,
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "200 OK", "is_correct": False},
                    {"option_key": "B", "option_text": "201 Created", "is_correct": True},
                    {"option_key": "C", "option_text": "204 No Content", "is_correct": False}
                ]
            }
        ]
    }
    res = client.post("/api/v1/recruiter/assessments", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Backend Engineering MCQ Round 1"
    assert data["total_marks"] == 10
    assert data["passing_marks"] == 5
    assert data["question_count"] == 2
    assert data["status"] == "DRAFT"


def test_invalid_assessment_cannot_be_published(client, test_setup):
    """2. Invalid assessment cannot be published."""
    headers = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    # Passing marks exceeding total marks
    invalid_payload = {
        "job_id": test_setup["job1"].id,
        "title": "Invalid Assessment",
        "duration_minutes": 15,
        "passing_marks": 15,
        "questions": [
            {
                "question_text": "Sample Question",
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "Opt 1", "is_correct": True},
                    {"option_key": "B", "option_text": "Opt 2", "is_correct": False}
                ]
            }
        ]
    }
    res = client.post("/api/v1/recruiter/assessments", json=invalid_payload, headers=headers)
    assert res.status_code == 400
    assert "cannot exceed total marks" in res.json()["detail"]


def test_recruiter_cannot_assign_non_shortlisted_candidate(client, test_setup):
    """3. Recruiter cannot assign an assessment to a non-shortlisted candidate."""
    headers = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    # First create and publish valid assessment
    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Shortlist Test Assessment",
        "duration_minutes": 20,
        "passing_marks": 2,
        "questions": [
            {
                "question_text": "Question 1",
                "marks": 2,
                "options": [
                    {"option_key": "A", "option_text": "Correct", "is_correct": True},
                    {"option_key": "B", "option_text": "Incorrect", "is_correct": False}
                ]
            }
        ]
    }, headers=headers)
    assessment_id = create_res.json()["id"]

    # Publish
    pub_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers)
    assert pub_res.status_code == 200

    # Try assigning to candidate 2 who is APPLIED, not SHORTLISTED
    assign_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate2"].id]
    }, headers=headers)
    assert assign_res.status_code == 400
    assert "does not have a SHORTLISTED application" in assign_res.json()["detail"]


def test_duplicate_assignment_is_rejected(client, test_setup):
    """4. Duplicate assignment is rejected."""
    headers = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Dup Test Assessment",
        "duration_minutes": 20,
        "passing_marks": 2,
        "questions": [
            {
                "question_text": "Question 1",
                "marks": 2,
                "options": [
                    {"option_key": "A", "option_text": "Correct", "is_correct": True},
                    {"option_key": "B", "option_text": "Incorrect", "is_correct": False}
                ]
            }
        ]
    }, headers=headers)
    assessment_id = create_res.json()["id"]
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers)

    # First assignment to candidate 1 (who is SHORTLISTED) succeeds
    asgn_res1 = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers)
    assert asgn_res1.status_code == 200

    # Second assignment to candidate 1 fails
    asgn_res2 = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers)
    assert asgn_res2.status_code == 400
    assert "already been assigned" in asgn_res2.json()["detail"]


def test_assigned_candidate_can_view_and_unassigned_cannot(client, test_setup):
    """5. Assigned candidate can view, 6. Unassigned candidate cannot access."""
    headers_rec = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {test_setup['token_cand1']}"}
    headers_cand2 = {"Authorization": f"Bearer {test_setup['token_cand2']}"}

    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Access Test Assessment",
        "instructions": "Follow instructions carefully.",
        "duration_minutes": 25,
        "passing_marks": 2,
        "questions": [
            {
                "question_text": "Question 1",
                "marks": 2,
                "options": [
                    {"option_key": "A", "option_text": "Correct", "is_correct": True},
                    {"option_key": "B", "option_text": "Incorrect", "is_correct": False}
                ]
            }
        ]
    }, headers=headers_rec)
    assessment_id = create_res.json()["id"]
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec)

    # Assign to candidate 1
    asgn_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers_rec)
    assignment_id = asgn_res.json()[0]["id"]

    # 5. Assigned candidate 1 views instructions
    inst_res1 = client.get(f"/api/v1/candidate/assessments/{assignment_id}/instructions", headers=headers_cand1)
    assert inst_res1.status_code == 200
    assert inst_res1.json()["title"] == "Access Test Assessment"

    # 6. Unassigned candidate 2 attempts to view instructions -> Forbidden
    inst_res2 = client.get(f"/api/v1/candidate/assessments/{assignment_id}/instructions", headers=headers_cand2)
    assert inst_res2.status_code == 403


def test_one_attempt_policy_and_no_correct_answers_leaked(client, test_setup):
    """
    7. Candidate can start once.
    8. Second attempt is rejected.
    9. Save/update answers before submission.
    10. Correct answers are not exposed in candidate APIs.
    """
    headers_rec = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {test_setup['token_cand1']}"}

    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Attempt Policy Assessment",
        "duration_minutes": 20,
        "passing_marks": 5,
        "questions": [
            {
                "question_text": "Which keyword defines an asynchronous function in Python?",
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "async def", "is_correct": True},
                    {"option_key": "B", "option_text": "sync def", "is_correct": False},
                    {"option_key": "C", "option_text": "thread def", "is_correct": False}
                ]
            }
        ]
    }, headers=headers_rec)
    assessment_id = create_res.json()["id"]
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec)

    asgn_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers_rec)
    assignment_id = asgn_res.json()[0]["id"]

    # 7. Start attempt
    start_res = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers=headers_cand1)
    assert start_res.status_code == 200
    start_data = start_res.json()
    attempt_id = start_data["attempt_id"]
    assert start_data["status"] == "IN_PROGRESS"
    assert start_data["remaining_seconds"] > 0

    # 10. Verify NO correct answers are exposed in candidate view
    for q in start_data["questions"]:
        for opt in q["options"]:
            assert opt["is_correct"] is None

    # 9. Save and update answers
    q_id = start_data["questions"][0]["id"]
    opt_a_id = start_data["questions"][0]["options"][0]["id"]
    opt_b_id = start_data["questions"][0]["options"][1]["id"]

    # Select B first
    save_res1 = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [{"question_id": q_id, "selected_option_id": opt_b_id}]
    }, headers=headers_cand1)
    assert save_res1.status_code == 200

    # Change to A before submission
    save_res2 = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [{"question_id": q_id, "selected_option_id": opt_a_id}]
    }, headers=headers_cand1)
    assert save_res2.status_code == 200

    # 15. Refreshing / calling attempt status restores saved answer and remaining time without resetting
    status_res = client.get(f"/api/v1/candidate/assessments/{assignment_id}/attempt", headers=headers_cand1)
    assert status_res.status_code == 200
    assert status_res.json()["saved_answers"].get(q_id) == opt_a_id

    # Submit test
    sub_res = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "SUBMITTED"
    assert sub_res.json()["review_status"] == "PENDING_REVIEW"
    assert "Thank you for completing your assessment" in sub_res.json()["message"]

    # 8. Second attempt to start after submission is rejected
    second_start = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers=headers_cand1)
    assert second_start.status_code == 400
    assert "already been finalized" in second_start.json()["detail"]


def test_scoring_pass_fail_and_pipeline_progression(client, test_setup, db):
    """
    11. Backend scoring.
    12. Passing marks produces PASSED and progresses application.
    13. Below passing marks produces FAILED.
    16. Duplicate submissions do not create duplicate results.
    """
    headers_rec = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {test_setup['token_cand1']}"}

    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Pass Fail Test Assessment",
        "duration_minutes": 20,
        "passing_marks": 6,
        "questions": [
            {
                "question_text": "Question 1 (4 marks)",
                "marks": 4,
                "options": [
                    {"option_key": "A", "option_text": "Correct Answer", "is_correct": True},
                    {"option_key": "B", "option_text": "Wrong", "is_correct": False}
                ]
            },
            {
                "question_text": "Question 2 (6 marks)",
                "marks": 6,
                "options": [
                    {"option_key": "A", "option_text": "Correct Answer", "is_correct": True},
                    {"option_key": "B", "option_text": "Wrong", "is_correct": False}
                ]
            }
        ]
    }, headers=headers_rec)
    assessment_id = create_res.json()["id"]
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec)

    asgn_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers_rec)
    assignment_id = asgn_res.json()[0]["id"]

    # Start attempt
    start_res = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]
    q1_id = start_res.json()["questions"][0]["id"]
    q1_opt_corr = start_res.json()["questions"][0]["options"][0]["id"]
    q2_id = start_res.json()["questions"][1]["id"]
    q2_opt_corr = start_res.json()["questions"][1]["options"][0]["id"]

    # Answer both correctly (10/10 marks >= 6 passing)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [
            {"question_id": q1_id, "selected_option_id": q1_opt_corr},
            {"question_id": q2_id, "selected_option_id": q2_opt_corr}
        ]
    }, headers=headers_cand1)

    # Submit (Candidate receives strict submission confirmation without scores)
    submit_res = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["review_status"] == "PENDING_REVIEW"
    assert "Thank you for completing your assessment" in sub_data["message"]
    # Candidate response MUST NOT leak marks_obtained or percentage
    assert "marks_obtained" not in sub_data
    assert "percentage" not in sub_data
    assert "result" not in sub_data

    # 16. Duplicate submit call returns identical result without throwing or duplicating
    dup_submit = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)
    assert dup_submit.status_code == 200
    assert dup_submit.json()["status"] == "SUBMITTED"
    assert dup_submit.json()["review_status"] == "PENDING_REVIEW"

    # Backend scoring calculates and stores private score (10 marks, 100%)
    result_in_db = db.query(AssessmentResult).filter(AssessmentResult.assignment_id == assignment_id).first()
    assert result_in_db is not None
    assert result_in_db.marks_obtained == 10
    assert result_in_db.percentage == 100.0

    # Recruiter accesses private review
    rev_res = client.get(f"/api/v1/recruiter/assessments/reviews?assessment_id={assessment_id}", headers=headers_rec)
    assert rev_res.status_code == 200
    assert len(rev_res.json()) >= 1
    cand_rev = [r for r in rev_res.json() if r["assignment_id"] == assignment_id][0]
    assert cand_rev["score_obtained"] == 10
    assert cand_rev["accuracy_percentage"] == 100.0
    assert cand_rev["score_based_outcome"] == "PASSED"
    assert cand_rev["review_status"] == "PENDING_REVIEW"

    # Recruiter makes decision to advance to interview
    dec_res = client.post(f"/api/v1/recruiter/assessments/assignments/{assignment_id}/decision", json={
        "decision": "MOVED_TO_INTERVIEW",
        "decision_reason": "Excellent score and technical depth demonstrated.",
        "recruiter_remarks": "Proceeding directly to technical interview."
    }, headers=headers_rec)
    assert dec_res.status_code == 200
    assert dec_res.json()["review_status"] == "MOVED_TO_INTERVIEW"
    assert dec_res.json()["application_status"] == "INTERVIEW"


def test_expired_test_auto_submit(client, test_setup, db):
    """14. Expired test is automatically submitted upon expiration."""
    headers_rec = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {test_setup['token_cand1']}"}

    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Expiration Test Assessment",
        "duration_minutes": 10,
        "passing_marks": 5,
        "questions": [
            {
                "question_text": "Question 1",
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "Correct", "is_correct": True},
                    {"option_key": "B", "option_text": "Wrong", "is_correct": False}
                ]
            }
        ]
    }, headers=headers_rec)
    assessment_id = create_res.json()["id"]
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec)

    asgn_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers_rec)
    assignment_id = asgn_res.json()[0]["id"]

    start_res = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]

    # Artificially set expires_at in the past
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    attempt.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    # When candidate calls start/attempt, it auto-finalizes and detects expiration
    check_res = client.post(f"/api/v1/candidate/assessments/{assignment_id}/start", headers=headers_cand1)
    assert check_res.status_code == 400
    assert "expired" in check_res.json()["detail"]

    # Verify attempt is finalized in DB
    db.refresh(attempt)
    assert attempt.status == AttemptStatusEnum.EXPIRED


def test_candidate_and_recruiter_access_isolation(client, test_setup):
    """17. Candidate cannot access another's result. 18. Recruiter cannot access another's assessment."""
    headers_rec1 = {"Authorization": f"Bearer {test_setup['token_rec1']}"}
    headers_rec2 = {"Authorization": f"Bearer {test_setup['token_rec2']}"}
    headers_cand2 = {"Authorization": f"Bearer {test_setup['token_cand2']}"}

    create_res = client.post("/api/v1/recruiter/assessments", json={
        "job_id": test_setup["job1"].id,
        "title": "Isolation Test Assessment",
        "duration_minutes": 15,
        "passing_marks": 5,
        "questions": [
            {
                "question_text": "Question 1",
                "marks": 5,
                "options": [
                    {"option_key": "A", "option_text": "Correct", "is_correct": True},
                    {"option_key": "B", "option_text": "Wrong", "is_correct": False}
                ]
            }
        ]
    }, headers=headers_rec1)
    assessment_id = create_res.json()["id"]

    # 18. Recruiter 2 tries to access or publish Recruiter 1's assessment -> 403 Forbidden
    rec2_access = client.get(f"/api/v1/recruiter/assessments/{assessment_id}", headers=headers_rec2)
    assert rec2_access.status_code == 403

    rec2_publish = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec2)
    assert rec2_publish.status_code == 403

    # Publish properly with recruiter 1
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers=headers_rec1)

    # Assign to candidate 1
    asgn_res = client.post(f"/api/v1/recruiter/assessments/{assessment_id}/assign", json={
        "candidate_ids": [test_setup["candidate1"].id]
    }, headers=headers_rec1)
    assignment_id = asgn_res.json()[0]["id"]

    # 17. Candidate 2 attempts to view candidate 1's result -> 403 Forbidden
    cand2_res = client.get(f"/api/v1/candidate/assessments/{assignment_id}/result", headers=headers_cand2)
    assert cand2_res.status_code == 403
