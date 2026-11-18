import pytest
import io
import csv
from datetime import datetime, timezone, timedelta
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    ApplicationStatusEnum, Resume, Assessment, AssessmentQuestion,
    AssessmentQuestionOption, CandidateAssessmentAssignment,
    AssessmentAttempt, AssessmentResult, AssessmentStatusEnum,
    AssessmentAssignmentStatusEnum, AttemptStatusEnum, AssessmentResultEnum,
    QuestionBankItem, QuestionBankOption, QuestionDifficultyEnum, QuestionStatusEnum
)
from app.core.security import get_password_hash, create_access_token
from app.db.seed_question_bank import seed_question_bank

@pytest.fixture
def qb_setup(db, candidate_user, recruiter_user, admin_user):
    # Ensure standard questions are seeded
    seed_question_bank(db)

    # Candidate 2
    user_cand2 = db.query(User).filter(User.email == "cand2_test@skillsphere.com").first()
    if not user_cand2:
        user_cand2 = User(
            name="Candidate Two",
            email="cand2_test@skillsphere.com",
            password_hash=get_password_hash("Cand2Pass!"),
            role=RoleEnum.JOB_SEEKER,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc)
        )
        db.add(user_cand2)
        db.commit()
        db.refresh(user_cand2)

    cand2 = db.query(Candidate).filter(Candidate.user_id == user_cand2.id).first()
    if not cand2:
        cand2 = Candidate(user_id=user_cand2.id, phone="9988776655", title="Frontend Engineer")
        db.add(cand2)
        db.commit()
        db.refresh(cand2)

    cand1 = db.query(Candidate).filter(Candidate.user_id == candidate_user.id).first()
    rec1 = db.query(Recruiter).filter(Recruiter.user_id == recruiter_user.id).first()

    # Job
    job = db.query(Job).filter(Job.recruiter_id == rec1.id, Job.title == "Senior Python Backend Architect").first()
    if not job:
        job = Job(
            recruiter_id=rec1.id,
            title="Senior Python Backend Architect",
            description="Architecture and backend scalability",
            location="Bengaluru, IN"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    # Resume
    res1 = db.query(Resume).filter(Resume.candidate_id == cand1.id).first()
    if not res1:
        res1 = Resume(
            candidate_id=cand1.id,
            file_name="resume1.pdf",
            file_path="uploads/resume1.pdf",
            file_type="pdf",
            file_size=2048
        )
        db.add(res1)
        db.commit()
        db.refresh(res1)

    res2 = db.query(Resume).filter(Resume.candidate_id == cand2.id).first()
    if not res2:
        res2 = Resume(
            candidate_id=cand2.id,
            file_name="resume2.pdf",
            file_path="uploads/resume2.pdf",
            file_type="pdf",
            file_size=2048
        )
        db.add(res2)
        db.commit()
        db.refresh(res2)

    # Applications (Shortlisted)
    app1 = db.query(Application).filter(Application.job_id == job.id, Application.candidate_id == cand1.id).first()
    if not app1:
        app1 = Application(
            job_id=job.id,
            candidate_id=cand1.id,
            resume_id=res1.id,
            status=ApplicationStatusEnum.SHORTLISTED
        )
        db.add(app1)
        db.commit()
        db.refresh(app1)

    app2 = db.query(Application).filter(Application.job_id == job.id, Application.candidate_id == cand2.id).first()
    if not app2:
        app2 = Application(
            job_id=job.id,
            candidate_id=cand2.id,
            resume_id=res2.id,
            status=ApplicationStatusEnum.SHORTLISTED
        )
        db.add(app2)
        db.commit()
        db.refresh(app2)

    cand2_token = create_access_token(subject=user_cand2.id, role=user_cand2.role.value)

    return {
        "job": job,
        "cand1": cand1,
        "cand2": cand2,
        "user_cand1": candidate_user,
        "user_cand2": user_cand2,
        "cand2_token": cand2_token,
        "rec1": rec1,
        "app1": app1,
        "app2": app2
    }

# -----------------------------------------------------------------------------
# 1. QUESTION BANK BROWSING & FILTERING
# -----------------------------------------------------------------------------
def test_browse_and_filter_question_bank(client, qb_setup, recruiter_token):
    # Test browse all
    res = client.get(
        "/api/v1/question-bank/questions",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 20
    assert len(data["items"]) > 0

    # Filter by technology: Python
    res_py = client.get(
        "/api/v1/question-bank/questions?technology=Python",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res_py.status_code == 200
    py_data = res_py.json()
    assert all(it["technology"].lower() == "python" for it in py_data["items"])

    # Filter by difficulty: BEGINNER
    res_diff = client.get(
        "/api/v1/question-bank/questions?difficulty=BEGINNER",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res_diff.status_code == 200
    diff_data = res_diff.json()
    assert all(it["difficulty"] == "BEGINNER" for it in diff_data["items"])

    # Search keyword
    res_search = client.get(
        "/api/v1/question-bank/questions?search=GIL",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert any("gil" in it["question_text"].lower() or "gil" in it["topic"].lower() for it in search_data["items"])

# -----------------------------------------------------------------------------
# 2. RECRUITER CUSTOM QUESTION CREATION
# -----------------------------------------------------------------------------
def test_recruiter_custom_question_creation(client, qb_setup, recruiter_token):
    payload = {
        "technology": "Python",
        "topic": "AsyncIO",
        "subtopic": "Event Loop",
        "difficulty": "ADVANCED",
        "question_text": "What does asyncio.gather() do in Python?",
        "explanation": "Runs awaitable objects in the aws sequence concurrently.",
        "marks": 5,
        "tags": ["asyncio", "concurrency"],
        "options": [
            {"option_key": "A", "option_text": "Runs tasks sequentially", "is_correct": False},
            {"option_key": "B", "option_text": "Runs tasks concurrently and returns aggregate results", "is_correct": True},
            {"option_key": "C", "option_text": "Terminates the event loop", "is_correct": False},
            {"option_key": "D", "option_text": "Creates a thread pool", "is_correct": False}
        ]
    }
    res = client.post(
        "/api/v1/question-bank/questions",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["technology"] == "Python"
    assert data["is_global"] is False  # Recruiter questions are private custom questions
    assert data["created_by_user_id"] == qb_setup["rec1"].user_id

# -----------------------------------------------------------------------------
# 3. SNAPSHOT ISOLATION & USAGE COUNT
# -----------------------------------------------------------------------------
def test_snapshot_isolation(client, db, qb_setup, recruiter_token):
    # Pick a seeded bank question
    bank_q = db.query(QuestionBankItem).filter(QuestionBankItem.technology == "Python").first()
    initial_usage = bank_q.usage_count
    original_text = bank_q.question_text

    # Recruiter creates assessment using this question
    opts = [
        {"option_key": o.option_key, "option_text": o.option_text, "is_correct": o.is_correct}
        for o in bank_q.options
    ]
    assessment_payload = {
        "job_id": qb_setup["job"].id,
        "title": "Python Snapshot Test Assessment",
        "duration_minutes": 20,
        "passing_marks": bank_q.marks,
        "questions": [
            {
                "bank_question_id": bank_q.id,
                "question_text": original_text,
                "marks": bank_q.marks,
                "options": opts
            }
        ]
    }
    create_res = client.post(
        "/api/v1/recruiter/assessments",
        json=assessment_payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert create_res.status_code == 200
    assessment_id = create_res.json()["id"]

    # Usage count in bank should have incremented
    db.refresh(bank_q)
    assert bank_q.usage_count == initial_usage + 1

    # Now edit the assessment question text
    edited_text = "MODIFIED: " + original_text
    update_payload = {
        "questions": [
            {
                "bank_question_id": bank_q.id,
                "question_text": edited_text,
                "marks": bank_q.marks,
                "options": opts
            }
        ]
    }
    up_res = client.put(
        f"/api/v1/recruiter/assessments/{assessment_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert up_res.status_code == 200

    # Verify central bank question text was NOT modified (Snapshot Isolation preserved)
    db.refresh(bank_q)
    assert bank_q.question_text == original_text
    assert bank_q.question_text != edited_text

# -----------------------------------------------------------------------------
# 4. DUPLICATE QUESTION DETECTION
# -----------------------------------------------------------------------------
def test_duplicate_question_detection(client, db, recruiter_token):
    bank_q = db.query(QuestionBankItem).first()
    assert bank_q is not None

    dup_check = client.post(
        "/api/v1/question-bank/check-duplicate",
        json={"question_text": bank_q.question_text.upper()},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert dup_check.status_code == 200
    data = dup_check.json()
    assert data["is_duplicate"] is True
    assert data["similar_question_id"] == bank_q.id

    # Non-duplicate check
    non_dup = client.post(
        "/api/v1/question-bank/check-duplicate",
        json={"question_text": "Completely unique and brand new algorithmic problem xyz 12345?"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert non_dup.status_code == 200
    assert non_dup.json()["is_duplicate"] is False

# -----------------------------------------------------------------------------
# 5. AUTOMATIC ASSESSMENT GENERATION
# -----------------------------------------------------------------------------
def test_automatic_assessment_generation(client, qb_setup, recruiter_token):
    auto_payload = {
        "job_id": qb_setup["job"].id,
        "title": "Auto-Generated Python Core Assessment",
        "instructions": "Answer all questions accurately.",
        "duration_minutes": 25,
        "passing_marks": 10,
        "technology": "Python",
        "question_count": 3,
        "difficulty_distribution": {
            "BEGINNER": 1,
            "INTERMEDIATE": 2
        },
        "randomize_questions": True,
        "randomize_options": True
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=auto_payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Auto-Generated Python Core Assessment"
    assert data["question_count"] == 3
    assert data["randomize_questions"] is True
    assert data["randomize_options"] is True
    assert data["status"] == "DRAFT"

# -----------------------------------------------------------------------------
# 6 & 7. QUESTION & OPTION RANDOMIZATION FOR CANDIDATES
# -----------------------------------------------------------------------------
def test_randomization_for_candidates(client, db, qb_setup, recruiter_token, candidate_token):
    # Create an assessment with 4 questions and publish it
    questions = []
    for i in range(1, 5):
        questions.append({
            "question_text": f"Randomization Question #{i}",
            "marks": 5,
            "options": [
                {"option_key": "A", "option_text": f"Option A for Q{i}", "is_correct": (i % 2 == 0)},
                {"option_key": "B", "option_text": f"Option B for Q{i}", "is_correct": (i % 2 != 0)},
                {"option_key": "C", "option_text": f"Option C for Q{i}", "is_correct": False},
                {"option_key": "D", "option_text": f"Option D for Q{i}", "is_correct": False}
            ]
        })

    create_res = client.post(
        "/api/v1/recruiter/assessments",
        json={
            "job_id": qb_setup["job"].id,
            "title": "Strict Randomization Assessment",
            "duration_minutes": 30,
            "passing_marks": 10,
            "randomize_questions": True,
            "randomize_options": True,
            "questions": questions
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert create_res.status_code == 200
    assessment_id = create_res.json()["id"]

    # Publish
    client.post(f"/api/v1/recruiter/assessments/{assessment_id}/publish", headers={"Authorization": f"Bearer {recruiter_token}"})

    # Assign to candidate 1 and candidate 2
    client.post(
        f"/api/v1/recruiter/assessments/{assessment_id}/assign",
        json={"candidate_ids": [qb_setup["cand1"].id, qb_setup["cand2"].id]},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )

    # Cand1 assignment
    asgn1 = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.assessment_id == assessment_id,
        CandidateAssessmentAssignment.candidate_id == qb_setup["cand1"].id
    ).first()

    # Cand2 assignment
    asgn2 = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.assessment_id == assessment_id,
        CandidateAssessmentAssignment.candidate_id == qb_setup["cand2"].id
    ).first()

    # Cand 1 starts test
    res1 = client.post(
        f"/api/v1/candidate/assessments/{asgn1.id}/start",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert res1.status_code == 200
    cand1_data = res1.json()

    # Cand 2 starts test
    res2 = client.post(
        f"/api/v1/candidate/assessments/{asgn2.id}/start",
        headers={"Authorization": f"Bearer {qb_setup['cand2_token']}"}
    )
    assert res2.status_code == 200
    cand2_data = res2.json()

    # Invariants: No correct answer leaked
    for q in cand1_data["questions"]:
        for opt in q["options"]:
            assert opt["is_correct"] is None

    # Verify attempt recorded orders
    att1 = db.query(AssessmentAttempt).filter(AssessmentAttempt.assignment_id == asgn1.id).first()
    assert att1.question_order is not None
    assert att1.option_orders is not None
    assert len(att1.question_order) == 4

# -----------------------------------------------------------------------------
# 8 & 9. ATTEMPT PERSISTENCE ON RECONNECT & REFRESH
# -----------------------------------------------------------------------------
def test_attempt_persistence_on_refresh(client, db, qb_setup, candidate_token):
    # Find active assignment for candidate 1
    asgn1 = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.candidate_id == qb_setup["cand1"].id,
        CandidateAssessmentAssignment.status == AssessmentAssignmentStatusEnum.STARTED
    ).first()
    assert asgn1 is not None

    # First fetch
    first_view = client.post(
        f"/api/v1/candidate/assessments/{asgn1.id}/start",
        headers={"Authorization": f"Bearer {candidate_token}"}
    ).json()

    first_q_order = [q["id"] for q in first_view["questions"]]
    first_opt_order = [opt["id"] for opt in first_view["questions"][0]["options"]]

    # Save an answer
    chosen_opt_id = first_opt_order[0]
    client.post(
        f"/api/v1/candidate/assessments/attempts/{first_view['attempt_id']}/answers",
        json={"answers": [{"question_id": first_q_order[0], "selected_option_id": chosen_opt_id}]},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    # Second fetch (Simulate candidate browser page reload/reconnect)
    second_view = client.post(
        f"/api/v1/candidate/assessments/{asgn1.id}/start",
        headers={"Authorization": f"Bearer {candidate_token}"}
    ).json()

    second_q_order = [q["id"] for q in second_view["questions"]]
    second_opt_order = [opt["id"] for opt in second_view["questions"][0]["options"]]

    # Invariant: Question and option sequence MUST be strictly identical on refresh
    assert first_q_order == second_q_order
    assert first_opt_order == second_opt_order
    # Invariant: Saved answer preserved
    assert second_view["saved_answers"][first_q_order[0]] == chosen_opt_id

# -----------------------------------------------------------------------------
# 10. BULK CSV IMPORT VALIDATION & COMMIT
# -----------------------------------------------------------------------------
def test_bulk_csv_import_validation_and_commit(client, admin_token, recruiter_token):
    csv_content = """technology,topic,subtopic,difficulty,question_text,explanation,marks,option_a,option_b,option_c,option_d,correct_option,tags
React,Hooks,useEffect,BEGINNER,What is the primary purpose of useEffect hook?,Used for side effects in functional components.,5,State management,Handling side effects,Routing,Rendering JSX,B,react,hooks
,Hooks,useState,BEGINNER,Invalid row missing technology,Explanation,5,State,Props,DOM,CSS,A,react
React,Virtual DOM,,UNKNOWN_DIFF,Invalid difficulty question?,Explanation,5,A,B,C,D,A,react
React,Props,,INTERMEDIATE,What are React props?,Read-only attributes passed to components.,5,Mutable state,Immutable input data,CSS classes,Database queries,B,react,props
"""

    # Preview mode (commit=False)
    preview_res = client.post(
        "/api/v1/question-bank/bulk-import",
        json={"csv_content": csv_content, "commit": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["total_rows"] == 4
    assert preview_data["valid_rows_count"] == 2
    assert preview_data["invalid_rows_count"] == 2
    assert preview_data["can_commit"] is True

    # Check errors reported on invalid rows
    row2 = preview_data["rows"][1]
    assert row2["is_valid"] is False
    assert any("Missing required 'technology'" in e for e in row2["errors"])

    row3 = preview_data["rows"][2]
    assert row3["is_valid"] is False
    assert any("Invalid difficulty" in e for e in row3["errors"])

    # Commit mode (commit=True)
    commit_res = client.post(
        "/api/v1/question-bank/bulk-import",
        json={"csv_content": csv_content, "commit": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert commit_res.status_code == 200

    # Verify questions are now present in bank
    q_search = client.get(
        "/api/v1/question-bank/questions?search=primary purpose of useEffect",
        headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert q_search["total"] >= 1

# -----------------------------------------------------------------------------
# 11. ADMIN VS RECRUITER PERMISSIONS
# -----------------------------------------------------------------------------
def test_admin_vs_recruiter_permissions(client, db, admin_token, recruiter_token):
    # Find a global question
    global_q = db.query(QuestionBankItem).filter(QuestionBankItem.is_global == True).first()
    assert global_q is not None

    # Recruiter attempting to edit global question -> Forbidden 403
    rec_attempt = client.put(
        f"/api/v1/question-bank/questions/{global_q.id}",
        json={"question_text": "Hacked global text"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_attempt.status_code == 403

    # Recruiter duplicating global question to custom bank -> Allowed 200
    dup_res = client.post(
        f"/api/v1/question-bank/questions/{global_q.id}/duplicate",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert dup_data["is_global"] is False

    # Recruiter can edit their duplicated custom question -> Allowed 200
    edit_dup = client.put(
        f"/api/v1/question-bank/questions/{dup_data['id']}",
        json={"question_text": "Recruiter personalized version of question"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert edit_dup.status_code == 200
    assert edit_dup.json()["question_text"] == "Recruiter personalized version of question"

# -----------------------------------------------------------------------------
# 12. ASSESSMENT ANALYTICS CALCULATION
# -----------------------------------------------------------------------------
def test_assessment_analytics_calculation(client, db, qb_setup, recruiter_token, candidate_token):
    # Find the active attempt for cand1 and submit it
    asgn1 = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.candidate_id == qb_setup["cand1"].id,
        CandidateAssessmentAssignment.status == AssessmentAssignmentStatusEnum.STARTED
    ).first()

    if asgn1 and asgn1.attempt:
        client.post(
            f"/api/v1/candidate/assessments/{asgn1.attempt.id}/submit",
            headers={"Authorization": f"Bearer {candidate_token}"}
        )

    # Fetch analytics
    res = client.get(
        f"/api/v1/question-bank/assessments/{asgn1.assessment_id}/analytics",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    analytics = res.json()
    assert "pass_percentage" in analytics
    assert "average_marks" in analytics
    assert "questions_analytics" in analytics
    assert len(analytics["questions_analytics"]) > 0

# -----------------------------------------------------------------------------
# 13. PUBLISHED ASSESSMENT IMMUTABILITY WITH ACTIVE ATTEMPTS
# -----------------------------------------------------------------------------
def test_published_assessment_immutability(client, db, qb_setup, recruiter_token):
    # Find assessment with started attempts
    asgn1 = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.candidate_id == qb_setup["cand1"].id
    ).first()

    assessment_id = asgn1.assessment_id

    # Recruiter attempts to modify assessment questions while attempts exist -> Bad Request 400
    fail_mod = client.put(
        f"/api/v1/recruiter/assessments/{assessment_id}",
        json={"title": "Trying to modify active test", "duration_minutes": 10},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert fail_mod.status_code == 400
    detail = fail_mod.json()["detail"].lower()
    assert "already started" in detail or "draft" in detail

# -----------------------------------------------------------------------------
# 14. REGRESSION: TECHNOLOGIES CONTRACT & NO [object Object]
# -----------------------------------------------------------------------------
def test_technologies_contract_returns_string_arrays(client, qb_setup, recruiter_token):
    res = client.get(
        "/api/v1/question-bank/technologies",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "technologies" in data
    assert isinstance(data["technologies"], list)
    assert len(data["technologies"]) > 0
    # Every technology must be a string, not an object/dict
    assert all(isinstance(t, str) for t in data["technologies"])
    assert "Python" in data["technologies"]

    assert "topics_by_technology" in data
    assert isinstance(data["topics_by_technology"], dict)
    assert "Python" in data["topics_by_technology"]
    assert isinstance(data["topics_by_technology"]["Python"], list)

# -----------------------------------------------------------------------------
# 15. REGRESSION: AUTO-GENERATE WITH PERCENTAGES & TOTAL_QUESTIONS
# -----------------------------------------------------------------------------
def test_auto_generate_with_percentages_and_total_questions(client, qb_setup, recruiter_token):
    job = qb_setup["job"]
    payload = {
        "job_id": job.id,
        "title": "Python Architecture Auto Test (Percentages)",
        "instructions": "Test auto-generation with percentage distribution",
        "duration_minutes": 25,
        "passing_marks": 10,
        "technology": "Python",
        "total_questions": 4,
        "difficulty_distribution": {
            "beginner_pct": 50,
            "intermediate_pct": 50,
            "advanced_pct": 0
        },
        "randomize_questions": True,
        "randomize_options": True
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code in [200, 201]
    created = res.json()
    assert created["title"] == "Python Architecture Auto Test (Percentages)"
    assert created["question_count"] == 4

# -----------------------------------------------------------------------------
# 16. REGRESSION: DUPLICATE CHECK WITH 'text' AND 'question_text'
# -----------------------------------------------------------------------------
def test_duplicate_check_with_text_and_question_text_aliases(client, db, qb_setup, recruiter_token):
    bank_q = db.query(QuestionBankItem).first()
    assert bank_q is not None

    # Call with 'text' alias
    res_text = client.post(
        "/api/v1/question-bank/check-duplicate",
        json={"text": bank_q.question_text},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res_text.status_code == 200
    data_text = res_text.json()
    assert data_text["is_duplicate"] is True

    # Call with 'question_text' field
    res_qtext = client.post(
        "/api/v1/question-bank/check-duplicate",
        json={"question_text": bank_q.question_text},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res_qtext.status_code == 200
    data_qtext = res_qtext.json()
    assert data_qtext["is_duplicate"] is True

