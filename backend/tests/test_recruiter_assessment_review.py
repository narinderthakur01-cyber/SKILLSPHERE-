import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    ApplicationStatusEnum, Resume, Assessment, AssessmentQuestion,
    AssessmentQuestionOption, CandidateAssessmentAssignment,
    AssessmentAttempt, AssessmentResult, AssessmentStatusEnum,
    AssessmentAssignmentStatusEnum, AttemptStatusEnum,
    AssessmentDecisionHistory, ProctoringSession, ProctoringEvent
)
from app.core.security import get_password_hash, create_access_token

@pytest.fixture
def review_setup(db, candidate_user, recruiter_user):
    import uuid
    uid = str(uuid.uuid4())[:8]

    # Recruiter 2 (Unauthorized Recruiter)
    user_rec2 = User(
        name="Other Recruiter",
        email=f"rec2_{uid}@skillsphere.com",
        password_hash=get_password_hash("RecPass123!"),
        role=RoleEnum.RECRUITER,
        email_verified=True
    )
    db.add(user_rec2)
    db.commit()
    recruiter2 = Recruiter(user_id=user_rec2.id, designation="Hiring Manager")
    db.add(recruiter2)
    db.commit()

    # Recruiter 1 & Candidate 1 from fixtures
    recruiter1 = db.query(Recruiter).filter(Recruiter.user_id == recruiter_user.id).first()
    candidate1 = db.query(Candidate).filter(Candidate.user_id == candidate_user.id).first()

    # Candidate 2
    user_cand2 = User(
        name="Bob Smith",
        email=f"bob_{uid}@example.com",
        password_hash=get_password_hash("CandPass123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=True
    )
    db.add(user_cand2)
    db.commit()
    candidate2 = Candidate(user_id=user_cand2.id, phone="9112233445", title="Backend Dev")
    db.add(candidate2)
    db.commit()

    # Job owned by Recruiter 1
    job1 = Job(
        recruiter_id=recruiter1.id,
        title="Full Stack Software Engineer",
        description="Core engineering role",
        location="San Francisco / Remote"
    )
    db.add(job1)
    db.commit()

    # Resumes
    resume1 = Resume(
        candidate_id=candidate1.id,
        file_name="candidate1_resume.pdf",
        file_path="uploads/candidate1_resume.pdf",
        file_type="pdf",
        file_size=1024
    )
    resume2 = Resume(
        candidate_id=candidate2.id,
        file_name="candidate2_resume.pdf",
        file_path="uploads/candidate2_resume.pdf",
        file_type="pdf",
        file_size=1024
    )
    db.add_all([resume1, resume2])
    db.commit()

    # Application for Candidate 1
    app1 = Application(
        job_id=job1.id,
        candidate_id=candidate1.id,
        resume_id=resume1.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app1)

    # Application for Candidate 2
    app2 = Application(
        job_id=job1.id,
        candidate_id=candidate2.id,
        resume_id=resume2.id,
        status=ApplicationStatusEnum.SHORTLISTED
    )
    db.add(app2)
    db.commit()

    # Assessment with 2 Questions (Total 10 marks, passing 6 marks)
    assessment1 = Assessment(
        job_id=job1.id,
        recruiter_id=recruiter1.id,
        title="Full Stack Technical Assessment",
        instructions="Answer all questions carefully.",
        duration_minutes=30,
        passing_marks=6,
        status=AssessmentStatusEnum.PUBLISHED
    )
    db.add(assessment1)
    db.commit()

    q1 = AssessmentQuestion(
        assessment_id=assessment1.id,
        question_text="What is the time complexity of binary search?",
        marks=5,
        order_num=1,
        explanation="Binary search halves the search space at every step, yielding O(log n)."
    )
    db.add(q1)
    db.commit()

    q1_opt_a = AssessmentQuestionOption(question_id=q1.id, option_key="A", option_text="O(log n)", is_correct=True)
    q1_opt_b = AssessmentQuestionOption(question_id=q1.id, option_key="B", option_text="O(n)", is_correct=False)
    db.add_all([q1_opt_a, q1_opt_b])

    q2 = AssessmentQuestion(
        assessment_id=assessment1.id,
        question_text="Which HTTP status code signifies Not Found?",
        marks=5,
        order_num=2,
        explanation="404 indicates resource not found."
    )
    db.add(q2)
    db.commit()

    q2_opt_a = AssessmentQuestionOption(question_id=q2.id, option_key="A", option_text="404", is_correct=True)
    q2_opt_b = AssessmentQuestionOption(question_id=q2.id, option_key="B", option_text="500", is_correct=False)
    db.add_all([q2_opt_a, q2_opt_b])
    db.commit()

    # Assignments
    asgn1 = CandidateAssessmentAssignment(
        assessment_id=assessment1.id,
        candidate_id=candidate1.id,
        application_id=app1.id,
        status=AssessmentAssignmentStatusEnum.ASSIGNED
    )
    asgn2 = CandidateAssessmentAssignment(
        assessment_id=assessment1.id,
        candidate_id=candidate2.id,
        application_id=app2.id,
        status=AssessmentAssignmentStatusEnum.ASSIGNED
    )
    db.add_all([asgn1, asgn2])
    db.commit()

    token_rec1 = create_access_token(recruiter_user.id, role=RoleEnum.RECRUITER.value)
    token_rec2 = create_access_token(user_rec2.id, role=RoleEnum.RECRUITER.value)
    token_cand1 = create_access_token(candidate_user.id, role=RoleEnum.JOB_SEEKER.value)
    token_cand2 = create_access_token(user_cand2.id, role=RoleEnum.JOB_SEEKER.value)

    return {
        "recruiter1": recruiter1,
        "recruiter2": recruiter2,
        "candidate1": candidate1,
        "candidate2": candidate2,
        "job1": job1,
        "assessment1": assessment1,
        "q1": q1,
        "q1_opt_a": q1_opt_a,
        "q1_opt_b": q1_opt_b,
        "q2": q2,
        "q2_opt_a": q2_opt_a,
        "q2_opt_b": q2_opt_b,
        "asgn1": asgn1,
        "asgn2": asgn2,
        "app1": app1,
        "app2": app2,
        "token_rec1": token_rec1,
        "token_rec2": token_rec2,
        "token_cand1": token_cand1,
        "token_cand2": token_cand2,
    }


def test_candidate_submission_privacy_and_idempotency(client, review_setup, db):
    """
    Candidate completes assessment:
    1. Score is computed and saved privately in backend.
    2. Response to candidate is CandidateSubmissionConfirmationResponse:
       - Contains status="SUBMITTED", review_status="PENDING_REVIEW".
       - Standard confirmation message is present.
       - Zero disclosure of marks_obtained, percentage, passing_marks, or pass/fail result.
    3. Application status is NOT automatically changed to INTERVIEW.
    4. Subsequent calls to submit are idempotent (return identical confirmation).
    5. Candidate assessment result endpoint returns CandidateAssessmentStatusResponse with zero scores.
    6. Candidate dashboard endpoint masks scores.
    """
    headers_cand = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    asgn_id = review_setup["asgn1"].id

    # 1. Start attempt
    start_res = client.post(f"/api/v1/candidate/assessments/{asgn_id}/start", headers=headers_cand)
    assert start_res.status_code == 200
    attempt_id = start_res.json()["attempt_id"]

    # 2. Save answers (both correct = 10/10)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [
            {"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id},
            {"question_id": review_setup["q2"].id, "selected_option_id": review_setup["q2_opt_a"].id}
        ]
    }, headers=headers_cand)

    # 3. Submit attempt
    sub_res = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand)
    assert sub_res.status_code == 200
    sub_json = sub_res.json()

    # Verify confirmation fields
    assert sub_json["status"] == "SUBMITTED"
    assert sub_json["review_status"] == "PENDING_REVIEW"
    assert "Thank you for completing your assessment" in sub_json["message"]
    assert "Your responses have been successfully submitted and your assessment is now under review" in sub_json["message"]

    # STRICT PRIVACY: Verify zero score or pass/fail disclosure
    assert "marks_obtained" not in sub_json
    assert "percentage" not in sub_json
    assert "passing_marks" not in sub_json
    assert "result" not in sub_json
    assert "is_passed" not in sub_json

    # 4. Verify Application status was NOT automatically changed
    app = db.query(Application).filter(Application.id == review_setup["app1"].id).first()
    assert app.status == ApplicationStatusEnum.SHORTLISTED

    # 5. Idempotent submission: repeat submit returns identical 200 confirmation
    dup_res = client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand)
    assert dup_res.status_code == 200
    dup_json = dup_res.json()
    assert dup_json["status"] == "SUBMITTED"
    assert dup_json["review_status"] == "PENDING_REVIEW"
    assert "marks_obtained" not in dup_json

    # 6. Verify result in DB is privately stored
    res_db = db.query(AssessmentResult).filter(AssessmentResult.assignment_id == asgn_id).first()
    assert res_db is not None
    assert res_db.marks_obtained == 10.0
    assert res_db.percentage == 100.0

    # 7. Candidate accesses /result endpoint: returns CandidateAssessmentStatusResponse
    cand_result_res = client.get(f"/api/v1/candidate/assessments/{asgn_id}/result", headers=headers_cand)
    assert cand_result_res.status_code == 200
    status_json = cand_result_res.json()
    assert status_json["review_status"] == "PENDING_REVIEW"
    assert "Under Review" in status_json["status_headline"]
    assert "Thank you for completing your assessment" in status_json["status_message"]
    assert "marks_obtained" not in status_json
    assert "percentage" not in status_json

    # 8. Candidate accesses /candidate/assessments: list endpoint masks scores
    list_res = client.get("/api/v1/candidate/assessments", headers=headers_cand)
    assert list_res.status_code == 200
    cand_asgn = [a for a in list_res.json() if a["id"] == asgn_id][0]
    assert cand_asgn["marks_obtained"] is None
    assert cand_asgn["percentage"] is None
    assert cand_asgn["result"] is None
    assert cand_asgn["review_status"] == "PENDING_REVIEW"


def test_recruiter_reviews_list_and_filters(client, review_setup, db):
    """
    Recruiter accesses private reviews list:
    - Candidate names, private scores, accuracy, benchmarks, telemetry.
    - Search and status filters work as expected.
    """
    headers_rec1 = {"Authorization": f"Bearer {review_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {review_setup['token_cand1']}"}

    # Complete test for candidate 1
    start_res = client.post(f"/api/v1/candidate/assessments/{review_setup['asgn1'].id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [{"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id}]
    }, headers=headers_cand1)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)

    # Recruiter queries reviews
    res = client.get("/api/v1/recruiter/assessments/reviews", headers=headers_rec1)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1

    item = [d for d in data if d["assignment_id"] == review_setup["asgn1"].id][0]
    assert item["candidate_name"] == review_setup["candidate1"].user.name
    assert item["score_obtained"] == 5.0
    assert item["total_marks"] == 10.0
    assert item["accuracy_percentage"] == 50.0
    assert item["review_status"] == "PENDING_REVIEW"
    assert item["score_based_outcome"] == "FAILED"  # passing marks is 6

    # Filter by review_status
    filter_res = client.get("/api/v1/recruiter/assessments/reviews?review_status=PENDING_REVIEW", headers=headers_rec1)
    assert filter_res.status_code == 200
    assert any(d["assignment_id"] == review_setup["asgn1"].id for d in filter_res.json())

    # Search filter
    search_res = client.get(f"/api/v1/recruiter/assessments/reviews?search={review_setup['candidate1'].user.email[:5]}", headers=headers_rec1)
    assert search_res.status_code == 200
    assert any(d["assignment_id"] == review_setup["asgn1"].id for d in search_res.json())


def test_recruiter_detailed_review_answers_and_telemetry(client, review_setup, db):
    """
    Recruiter detailed review returns:
    - Candidate answers with question snapshots, candidate choices, correct choices, explanations.
    - Proctoring event timeline.
    - Decision audit history.
    """
    headers_rec1 = {"Authorization": f"Bearer {review_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    asgn_id = review_setup["asgn1"].id

    start_res = client.post(f"/api/v1/candidate/assessments/{asgn_id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]

    # Record a proctoring event
    proc_sess = ProctoringSession(
        assessment_attempt_id=attempt_id,
        candidate_id=review_setup["candidate1"].id,
        assessment_id=review_setup["assessment1"].id,
        monitoring_status="ACTIVE"
    )
    db.add(proc_sess)
    db.commit()

    proc_evt = ProctoringEvent(
        proctoring_session_id=proc_sess.id,
        event_type="TAB_SWITCH",
        duration_seconds=3.5,
        severity="MEDIUM",
        details_json={"note": "Switched to browser window"}
    )
    db.add(proc_evt)
    db.commit()

    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [
            {"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id},
            {"question_id": review_setup["q2"].id, "selected_option_id": review_setup["q2_opt_b"].id} # incorrect
        ]
    }, headers=headers_cand1)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)

    # Detailed review
    res = client.get(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/detailed-review", headers=headers_rec1)
    assert res.status_code == 200
    det = res.json()

    assert det["assignment_id"] == asgn_id
    assert det["marks_obtained"] == 5.0
    assert det["total_marks"] == 10.0
    assert len(det["answers"]) == 2

    # Check answers
    ans1 = [a for a in det["answers"] if a["question_id"] == review_setup["q1"].id][0]
    assert ans1["status"] == "CORRECT"
    assert ans1["marks_awarded"] == 5.0
    assert ans1["correct_answer"] == "A"
    assert ans1["candidate_selected_option"] == "A"

    ans2 = [a for a in det["answers"] if a["question_id"] == review_setup["q2"].id][0]
    assert ans2["status"] == "INCORRECT"
    assert ans2["marks_awarded"] == 0.0
    assert ans2["correct_answer"] == "A"
    assert ans2["candidate_selected_option"] == "B"

    # Check proctoring timeline
    assert len(det["proctoring_timeline"]) >= 1
    assert det["proctoring_timeline"][0]["event_type"] == "TAB_SWITCH"
    assert det["proctoring_timeline"][0]["severity"] == "MEDIUM"


def test_manual_score_adjustment_and_audit(client, review_setup, db):
    """
    Recruiter adjusts score:
    - Reason is mandatory (fails with 400 if reason < 3 chars).
    - Preserves original score.
    - Updates marks_obtained and percentage.
    - Logs to AssessmentDecisionHistory.
    """
    headers_rec1 = {"Authorization": f"Bearer {review_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    asgn_id = review_setup["asgn1"].id

    start_res = client.post(f"/api/v1/candidate/assessments/{asgn_id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [{"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id}]
    }, headers=headers_cand1)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)

    # 1. Missing reason fails
    fail_res = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/adjust-score", json={
        "adjusted_score": 8.0,
        "reason": "  "
    }, headers=headers_rec1)
    assert fail_res.status_code == 400

    # 2. Valid adjustment
    adj_res = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/adjust-score", json={
        "adjusted_score": 8.5,
        "reason": "Partial credit granted for question 2 due to alternative correct interpretation."
    }, headers=headers_rec1)
    assert adj_res.status_code == 200
    adj_data = adj_res.json()
    assert adj_data["is_score_adjusted"] is True
    assert adj_data["original_score"] == 5.0
    assert adj_data["marks_obtained"] == 8.5
    assert adj_data["percentage"] == 85.0
    assert adj_data["score_adjustment_reason"] == "Partial credit granted for question 2 due to alternative correct interpretation."

    # Verify decision history audit log in DB
    history = db.query(AssessmentDecisionHistory).filter(
        AssessmentDecisionHistory.assignment_id == asgn_id,
        AssessmentDecisionHistory.decision == "SCORE_ADJUSTED"
    ).first()
    assert history is not None
    assert history.decision_reason == "Partial credit granted for question 2 due to alternative correct interpretation."


def test_recruiter_decisions_and_application_pipeline_sync(client, review_setup, db):
    """
    Recruiter decisions:
    1. ACCEPTED: sets assignment review_status="ACCEPTED", application.status="SHORTLISTED", logs history.
    2. REJECTED: requires mandatory reason (fails if missing); sets review_status="REJECTED", application.status="REJECTED".
    3. MOVED_TO_INTERVIEW: sets review_status="MOVED_TO_INTERVIEW", application.status="INTERVIEW".
    4. ON_HOLD: sets review_status="ON_HOLD", application.status="UNDER_REVIEW", no email dispatched.
    5. Revision: recruiter revises ON_HOLD -> ACCEPTED, creating chronological audit entries.
    """
    headers_rec1 = {"Authorization": f"Bearer {review_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    asgn_id = review_setup["asgn1"].id

    start_res = client.post(f"/api/v1/candidate/assessments/{asgn_id}/start", headers=headers_cand1)
    attempt_id = start_res.json()["attempt_id"]
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/answers", json={
        "answers": [{"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id}]
    }, headers=headers_cand1)
    client.post(f"/api/v1/candidate/assessments/attempts/{attempt_id}/submit", headers=headers_cand1)

    with patch("app.services.email_service.EmailService.send_assessment_decision_email") as mock_email:
        mock_email.return_value = {"success": True, "message_id": "test-msg-123"}

        # 1. HOLD FOR REVIEW (No email should be dispatched)
        hold_res = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/decision", json={
            "decision": "ON_HOLD",
            "decision_reason": "Benchmarking against remaining cohort candidates.",
            "recruiter_remarks": "Solid performance but let's check remaining applicants."
        }, headers=headers_rec1)
        assert hold_res.status_code == 200
        assert hold_res.json()["review_status"] == "ON_HOLD"
        assert hold_res.json()["email_dispatched"] is False
        mock_email.assert_not_called()

        app = db.query(Application).filter(Application.id == review_setup["app1"].id).first()
        assert app.status == ApplicationStatusEnum.UNDER_REVIEW

        # 2. Rejection without mandatory reason FAILS
        rej_fail = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/decision", json={
            "decision": "REJECTED",
            "decision_reason": ""
        }, headers=headers_rec1)
        assert rej_fail.status_code == 400
        assert "mandatory" in rej_fail.json()["detail"].lower()

        # 3. Decision Revision: Move to Interview
        dec_res = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/decision", json={
            "decision": "MOVED_TO_INTERVIEW",
            "decision_reason": "High problem solving speed and accurate core concepts.",
            "candidate_message": "Congratulations! We invite you to schedule your Round 2 technical interview."
        }, headers=headers_rec1)
        assert dec_res.status_code == 200
        assert dec_res.json()["review_status"] == "MOVED_TO_INTERVIEW"
        assert dec_res.json()["application_status"] == "INTERVIEW"
        assert dec_res.json()["email_dispatched"] is True
        mock_email.assert_called_once()

        db.refresh(app)
        assert app.status == ApplicationStatusEnum.INTERVIEW

        # Verify audit history holds both entries
        history_entries = db.query(AssessmentDecisionHistory).filter(
            AssessmentDecisionHistory.assignment_id == asgn_id
        ).order_by(AssessmentDecisionHistory.decided_at.asc()).all()

        decisions = [h.decision for h in history_entries]
        assert "ON_HOLD" in decisions
        assert "MOVED_TO_INTERVIEW" in decisions


def test_recruiter_cohort_comparison_and_analytics(client, review_setup, db):
    """
    Cohort analytics & comparison:
    - Aggregated metrics (total_assigned, total_submitted, average_score, score_distribution).
    - Ranked leaderboard.
    """
    headers_rec1 = {"Authorization": f"Bearer {review_setup['token_rec1']}"}
    headers_cand1 = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    headers_cand2 = {"Authorization": f"Bearer {review_setup['token_cand2']}"}

    # Candidate 1: scores 10/10
    start1 = client.post(f"/api/v1/candidate/assessments/{review_setup['asgn1'].id}/start", headers=headers_cand1)
    att1_id = start1.json()["attempt_id"]
    client.post(f"/api/v1/candidate/assessments/attempts/{att1_id}/answers", json={
        "answers": [
            {"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id},
            {"question_id": review_setup["q2"].id, "selected_option_id": review_setup["q2_opt_a"].id}
        ]
    }, headers=headers_cand1)
    client.post(f"/api/v1/candidate/assessments/attempts/{att1_id}/submit", headers=headers_cand1)

    # Candidate 2: scores 5/10
    start2 = client.post(f"/api/v1/candidate/assessments/{review_setup['asgn2'].id}/start", headers=headers_cand2)
    att2_id = start2.json()["attempt_id"]
    client.post(f"/api/v1/candidate/assessments/attempts/{att2_id}/answers", json={
        "answers": [
            {"question_id": review_setup["q1"].id, "selected_option_id": review_setup["q1_opt_a"].id}
        ]
    }, headers=headers_cand2)
    client.post(f"/api/v1/candidate/assessments/attempts/{att2_id}/submit", headers=headers_cand2)

    comp_res = client.get(f"/api/v1/recruiter/assessments/{review_setup['assessment1'].id}/comparison", headers=headers_rec1)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()

    assert comp_data["analytics"]["total_assigned"] == 2
    assert comp_data["analytics"]["total_submitted"] == 2
    assert comp_data["analytics"]["average_score"] == 7.5
    assert comp_data["analytics"]["average_percentage"] == 75.0

    # Leaderboard candidate 1 should be rank #1 (10 pts > 5 pts)
    candidates = comp_data["candidates"]
    assert len(candidates) == 2
    assert candidates[0]["candidate_id"] == review_setup["candidate1"].id
    assert candidates[0]["score_obtained"] == 10.0
    assert candidates[1]["candidate_id"] == review_setup["candidate2"].id
    assert candidates[1]["score_obtained"] == 5.0


def test_recruiter_and_candidate_access_isolation(client, review_setup):
    """
    Security & RBAC:
    - Other recruiter (recruiter2) cannot access recruiter1's reviews or decisions -> 403.
    - Candidate cannot access recruiter review or decision endpoints -> 403.
    """
    headers_rec2 = {"Authorization": f"Bearer {review_setup['token_rec2']}"}
    headers_cand = {"Authorization": f"Bearer {review_setup['token_cand1']}"}
    asgn_id = review_setup["asgn1"].id

    # Recruiter 2 tries to access detailed review of recruiter 1's assignment
    rec2_det = client.get(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/detailed-review", headers=headers_rec2)
    assert rec2_det.status_code == 403

    # Recruiter 2 tries to make a decision
    rec2_dec = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/decision", json={
        "decision": "ACCEPTED"
    }, headers=headers_rec2)
    assert rec2_dec.status_code == 403

    # Candidate tries to access recruiter reviews endpoint
    cand_rev = client.get("/api/v1/recruiter/assessments/reviews", headers=headers_cand)
    assert cand_rev.status_code == 403

    # Candidate tries to adjust score
    cand_adj = client.post(f"/api/v1/recruiter/assessments/assignments/{asgn_id}/adjust-score", json={
        "adjusted_score": 10.0,
        "reason": "Self granted score"
    }, headers=headers_cand)
    assert cand_adj.status_code == 403
