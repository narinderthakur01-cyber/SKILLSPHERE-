import pytest
from app.models.models import (
    User, RoleEnum, Recruiter, Job, Assessment, AssessmentQuestion,
    QuestionBankItem, QuestionDifficultyEnum
)
from app.db.seed_question_bank import seed_question_bank

@pytest.fixture
def enhanced_setup(db, recruiter_user):
    # Seed full question bank (211 items across 13 technologies)
    seed_question_bank(db)

    rec = db.query(Recruiter).filter(Recruiter.user_id == recruiter_user.id).first()
    job = db.query(Job).filter(Job.recruiter_id == rec.id, Job.title == "Full Stack Python Lead").first()
    if not job:
        job = Job(
            recruiter_id=rec.id,
            title="Full Stack Python Lead",
            description="Lead full stack engineer with Python & React expertise",
            location="Remote"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    return {"recruiter": rec, "job": job}

# -----------------------------------------------------------------------------
# 1. AVAILABILITY ENDPOINT
# -----------------------------------------------------------------------------
def test_question_bank_availability_all(client, db, enhanced_setup, recruiter_token):
    res = client.get(
        "/api/v1/question-bank/availability",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_available"] >= 190
    assert data["beginner_count"] > 0
    assert data["intermediate_count"] > 0
    assert data["advanced_count"] > 0
    assert data["technology"] is None
    assert data["topic"] is None

def test_question_bank_availability_by_technology(client, db, enhanced_setup, recruiter_token):
    res = client.get(
        "/api/v1/question-bank/availability?technology=Python",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["technology"] == "Python"
    assert data["total_available"] >= 30
    assert data["beginner_count"] >= 8
    assert data["intermediate_count"] >= 13
    assert data["advanced_count"] >= 9
    assert (data["beginner_count"] + data["intermediate_count"] + data["advanced_count"]) == data["total_available"]

def test_question_bank_availability_nonexistent(client, db, enhanced_setup, recruiter_token):
    res = client.get(
        "/api/v1/question-bank/availability?technology=Cobol999",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_available"] == 0
    assert data["beginner_count"] == 0
    assert data["intermediate_count"] == 0
    assert data["advanced_count"] == 0

# -----------------------------------------------------------------------------
# 2. AUTO-GENERATE CONFIGURABLE QUESTION COUNTS (5, 10, 15, 20)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("requested_count", [5, 10, 15, 20])
def test_auto_generate_exact_question_counts(client, db, enhanced_setup, recruiter_token, requested_count):
    job = enhanced_setup["job"]
    payload = {
        "job_id": job.id,
        "title": f"Python Assessment ({requested_count} Questions)",
        "instructions": "Answer all questions carefully.",
        "duration_minutes": requested_count * 2,
        "passing_marks": max(1, requested_count // 2),
        "technology": "Python",
        "total_questions": requested_count,
        "randomize_questions": True,
        "randomize_options": True
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code in [200, 201]
    assessment = res.json()
    assert assessment["question_count"] == requested_count

    # Verify questions in database
    db_assessment = db.query(Assessment).filter(Assessment.id == assessment["id"]).first()
    assert len(db_assessment.questions) == requested_count
    for q in db_assessment.questions:
        assert len(q.options) == 4
        # Exactly one option is correct
        correct_opts = [opt for opt in q.options if opt.is_correct]
        assert len(correct_opts) == 1

# -----------------------------------------------------------------------------
# 3. INSUFFICIENT QUESTION COUNT ERROR HANDLING (SHORTAGE DETAIL)
# -----------------------------------------------------------------------------
def test_auto_generate_shortage_error_handling(client, db, enhanced_setup, recruiter_token):
    job = enhanced_setup["job"]
    # Python has 30 questions in the bank. Requesting 50 must fail cleanly with HTTP 400.
    payload = {
        "job_id": job.id,
        "title": "Python Massive Test",
        "duration_minutes": 60,
        "passing_marks": 25,
        "technology": "Python",
        "total_questions": 50,
        "randomize_questions": True
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "Requested 50 questions" in detail
    assert "questions are available" in detail

# -----------------------------------------------------------------------------
# 4. DIFFICULTY DISTRIBUTION CALCULATION (40/40/20)
# -----------------------------------------------------------------------------
def test_auto_generate_difficulty_distribution(client, db, enhanced_setup, recruiter_token):
    job = enhanced_setup["job"]
    payload = {
        "job_id": job.id,
        "title": "Python 10Q Balanced Assessment",
        "duration_minutes": 20,
        "passing_marks": 5,
        "technology": "Python",
        "total_questions": 10,
        "difficulty_distribution": {
            "beginner_pct": 40,
            "intermediate_pct": 40,
            "advanced_pct": 20
        },
        "randomize_questions": False
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code in [200, 201]
    assessment_id = res.json()["id"]

    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    assert len(db_assessment.questions) == 10

    # Cross-reference with QuestionBankItem to verify distribution
    bank_items = {q.question_text: q.difficulty for q in db.query(QuestionBankItem).filter(QuestionBankItem.technology == "Python").all()}
    difficulties = [bank_items.get(q.question_text) for q in db_assessment.questions if q.question_text in bank_items]
    
    beg_count = sum(1 for d in difficulties if d == QuestionDifficultyEnum.BEGINNER)
    int_count = sum(1 for d in difficulties if d == QuestionDifficultyEnum.INTERMEDIATE)
    adv_count = sum(1 for d in difficulties if d == QuestionDifficultyEnum.ADVANCED)

    assert beg_count == 4
    assert int_count == 4
    assert adv_count == 2

# -----------------------------------------------------------------------------
# 5. UNIFORM MARKS ASSIGNMENT (marks_per_question)
# -----------------------------------------------------------------------------
def test_auto_generate_uniform_marks(client, db, enhanced_setup, recruiter_token):
    job = enhanced_setup["job"]
    # 10 questions with uniform marks = 2 -> total_marks = 20
    payload = {
        "job_id": job.id,
        "title": "Python Uniform Marks Test (2 Marks Each)",
        "duration_minutes": 30,
        "passing_marks": 12,
        "technology": "Python",
        "total_questions": 10,
        "marks_per_question": 2
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code in [200, 201]
    assessment_data = res.json()
    assert assessment_data["total_marks"] == 20

    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_data["id"]).first()
    assert db_assessment.total_marks == 20
    for q in db_assessment.questions:
        assert q.marks == 2

def test_auto_generate_uniform_marks_5_each(client, db, enhanced_setup, recruiter_token):
    job = enhanced_setup["job"]
    # 5 questions with uniform marks = 5 -> total_marks = 25
    payload = {
        "job_id": job.id,
        "title": "Python High Stakes Test (5 Marks Each)",
        "duration_minutes": 25,
        "passing_marks": 15,
        "technology": "Python",
        "total_questions": 5,
        "marks_per_question": 5
    }
    res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code in [200, 201]
    assessment_data = res.json()
    assert assessment_data["total_marks"] == 25

    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_data["id"]).first()
    assert db_assessment.total_marks == 25
    for q in db_assessment.questions:
        assert q.marks == 5

# -----------------------------------------------------------------------------
# 6. SAMPLING ENDPOINT WITH MARKS & SHORTAGE VALIDATION
# -----------------------------------------------------------------------------
def test_sample_endpoint_success_and_shortage(client, db, enhanced_setup, recruiter_token):
    # Valid sample of 5 questions with marks_per_question=3
    sample_res = client.post(
        "/api/v1/question-bank/sample",
        json={
            "technology": "Python",
            "count": 5,
            "marks_per_question": 3
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert sample_res.status_code == 200
    data = sample_res.json()
    assert data["count"] == 5
    assert len(data["questions"]) == 5
    for q in data["questions"]:
        assert q["marks"] == 3

    # Shortage sample request (100 questions) -> returns HTTP 400
    shortage_res = client.post(
        "/api/v1/question-bank/sample",
        json={
            "technology": "Python",
            "count": 100
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert shortage_res.status_code == 400
    detail = shortage_res.json()["detail"]
    assert "Requested 100 questions" in detail
    assert "questions are available" in detail
