import os
import io
import pytest
from pathlib import Path
import pymupdf as fitz
import docx
import pandas as pd
from datetime import datetime, timezone

from app.models.models import (
    User, RoleEnum, Recruiter, Job, Assessment, AssessmentQuestion,
    QuestionBankItem, QuestionBankOption, QuestionDifficultyEnum,
    QuestionImportBatch, QuestionStatusEnum
)
from app.db.seed_question_bank import seed_question_bank
from app.services.question_extractor_service import QuestionExtractorService

@pytest.fixture
def upload_test_setup(db, recruiter_user, candidate_user):
    # Seed base question bank
    seed_question_bank(db)

    rec = db.query(Recruiter).filter(Recruiter.user_id == recruiter_user.id).first()
    job = db.query(Job).filter(Job.recruiter_id == rec.id, Job.title == "Lead Systems Architect").first()
    if not job:
        job = Job(
            recruiter_id=rec.id,
            title="Lead Systems Architect",
            description="Systems Architecture & Cloud Infrastructure",
            location="Remote"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    return {"recruiter": rec, "job": job}

# -----------------------------------------------------------------------------
# 1. SCENARIOS 1 & 2: AVAILABILITY TELEMETRY & INSUFFICIENT QUESTION SHORTAGE
# -----------------------------------------------------------------------------
def test_insufficient_questions_telemetry(client, db, upload_test_setup, recruiter_token):
    # Check availability for specialized technology with 0 questions in bank
    res = client.get(
        "/api/v1/question-bank/availability?technology=RustEmbedded99",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_available"] == 0
    assert data["beginner_count"] == 0

    # Auto-generate requesting 20 questions when 0 are available -> returns HTTP 400 shortage
    job = upload_test_setup["job"]
    gen_res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json={
            "job_id": job.id,
            "title": "Rust Embedded Test",
            "technology": "RustEmbedded99",
            "total_questions": 20,
            "duration_minutes": 30,
            "passing_marks": 10
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert gen_res.status_code == 400
    detail = gen_res.json()["detail"]
    assert "Requested 20 questions" in detail
    assert "only 0" in detail

# -----------------------------------------------------------------------------
# 2. SCENARIO 3: RECRUITER UPLOADS VALID DIGITAL PDF WITH MCQS
# -----------------------------------------------------------------------------
def test_upload_extract_valid_pdf(client, db, upload_test_setup, recruiter_token, tmp_path):
    pdf_path = tmp_path / "valid_mcqs.pdf"
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text(
        fitz.Point(50, 72),
        "1. What is the time complexity of searching in a balanced AVL tree?\n"
        "A) O(1)\n"
        "B) O(log n)\n"
        "C) O(n)\n"
        "D) O(n log n)\n"
        "Answer: B\n"
        "Explanation: AVL tree height is guaranteed logarithmic.\n"
        "Difficulty: INTERMEDIATE\n"
        "Marks: 2\n\n"
        "2. Which data structure operates on a First-In-First-Out (FIFO) basis?\n"
        "A) Stack\n"
        "B) Tree\n"
        "C) Queue\n"
        "D) Graph\n"
        "Answer: C\n"
        "Explanation: Queues process elements in FIFO sequence.\n"
        "Difficulty: BEGINNER\n"
        "Marks: 1\n"
    )

    page2 = doc.new_page()
    page2.insert_text(
        fitz.Point(50, 72),
        "3. In Python, what is the default behavior of dict.get(key) when key is missing?\n"
        "A) Raises KeyError\n"
        "B) Returns None\n"
        "C) Returns False\n"
        "D) Inserts the key with value None\n"
        "Answer: B\n"
        "Explanation: dict.get returns default (None) without raising KeyError.\n"
        "Difficulty: BEGINNER\n"
        "Marks: 1\n"
    )

    doc.save(str(pdf_path))
    doc.close()

    with open(pdf_path, "rb") as f:
        res = client.post(
            "/api/v1/question-bank/upload-extract",
            files={"file": ("valid_mcqs.pdf", f, "application/pdf")},
            data={"technology": "Computer Science", "topic": "Algorithms"},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "valid_mcqs.pdf"
    assert data["total_extracted"] == 3
    assert data["valid_count"] == 3
    assert data["missing_answer_count"] == 0

    # Verify extracted structure and options
    q1 = data["questions"][0]
    assert "AVL tree" in q1["question_text"]
    assert len(q1["options"]) == 4
    assert q1["correct_option"] == "B"
    assert q1["has_correct_answer"] is True
    assert q1["validation_status"] == "VALID"
    assert q1["source_page"] == 1

    q3 = data["questions"][2]
    assert "dict.get" in q3["question_text"]
    assert q3["correct_option"] == "B"
    assert q3["source_page"] == 2

# -----------------------------------------------------------------------------
# 3. SCENARIO 5: RECRUITER UPLOADS DOCX AND EXCEL (XLSX) FILES
# -----------------------------------------------------------------------------
def test_upload_extract_docx(client, db, upload_test_setup, recruiter_token, tmp_path):
    docx_path = tmp_path / "questions.docx"
    doc = docx.Document()
    doc.add_heading("Technical Assessment Questions", 0)

    doc.add_paragraph(
        "1. What is an idempotent HTTP method?\n"
        "A) POST\n"
        "B) GET\n"
        "C) PATCH\n"
        "D) CONNECT\n"
        "Answer: B\n"
        "Difficulty: INTERMEDIATE\n"
        "Explanation: Multiple identical GET requests have the same side effect as a single request."
    )
    doc.add_paragraph(
        "2. Which keyword in Python creates an anonymous function?\n"
        "A) def\n"
        "B) lambda\n"
        "C) anon\n"
        "D) func\n"
        "Answer: B\n"
        "Difficulty: BEGINNER\n"
    )
    doc.save(str(docx_path))

    with open(docx_path, "rb") as f:
        res = client.post(
            "/api/v1/question-bank/upload-extract",
            files={"file": ("questions.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"technology": "Python", "topic": "Functions"},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["total_extracted"] == 2
    assert data["valid_count"] == 2
    assert any("idempotent" in q["question_text"] for q in data["questions"])
    assert any("anonymous function" in q["question_text"] for q in data["questions"])

def test_upload_extract_xlsx(client, db, upload_test_setup, recruiter_token, tmp_path):
    xlsx_path = tmp_path / "questions.xlsx"
    df = pd.DataFrame([
        {
            "technology": "SQL",
            "topic": "Joins",
            "question_text": "Which join returns all rows when there is a match in either left or right table?",
            "option_a": "INNER JOIN",
            "option_b": "LEFT JOIN",
            "option_c": "FULL OUTER JOIN",
            "option_d": "CROSS JOIN",
            "correct_option": "C",
            "explanation": "FULL OUTER JOIN combines the results of both LEFT and RIGHT outer joins.",
            "difficulty": "INTERMEDIATE",
            "marks": 2
        },
        {
            "technology": "SQL",
            "topic": "Indexes",
            "question_text": "What is the primary benefit of creating a B-Tree index on a column?",
            "option_a": "Reduces storage space",
            "option_b": "Speeds up SELECT range queries and lookups",
            "option_c": "Enforces primary key constraint",
            "option_d": "Encrypts sensitive data",
            "correct_option": "B",
            "explanation": "B-Tree indexes provide O(log n) search times.",
            "difficulty": "BEGINNER",
            "marks": 1
        }
    ])
    df.to_excel(str(xlsx_path), index=False)

    with open(xlsx_path, "rb") as f:
        res = client.post(
            "/api/v1/question-bank/upload-extract",
            files={"file": ("questions.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"technology": "SQL"},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["total_extracted"] == 2
    assert data["valid_count"] == 2
    assert data["questions"][0]["correct_option"] == "C"
    assert data["questions"][1]["correct_option"] == "B"

# -----------------------------------------------------------------------------
# 4. SCENARIO 6: EXTRACTED QUESTIONS WITH MISSING ANSWER KEYS
# -----------------------------------------------------------------------------
def test_upload_extract_missing_answer_keys(client, db, upload_test_setup, recruiter_token, tmp_path):
    txt_path = tmp_path / "questions_no_key.txt"
    content = (
        "1. What is the default port for PostgreSQL?\n"
        "A) 3306\n"
        "B) 5432\n"
        "C) 27017\n"
        "D) 6379\n\n"
        "2. What is the time complexity of pushing an element onto a stack?\n"
        "A) O(1)\n"
        "B) O(n)\n"
        "C) O(log n)\n"
        "D) O(n^2)\n"
    )
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(txt_path, "rb") as f:
        res = client.post(
            "/api/v1/question-bank/upload-extract",
            files={"file": ("questions_no_key.txt", f, "text/plain")},
            data={"technology": "PostgreSQL"},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["total_extracted"] == 2
    assert data["missing_answer_count"] == 2
    for q in data["questions"]:
        assert q["validation_status"] == "MISSING_ANSWER"
        assert q["has_correct_answer"] is False
        assert q["correct_option"] is None

# -----------------------------------------------------------------------------
# 5. SCENARIO 7: DUPLICATE DETECTION (IN-FILE & AGAINST BANK)
# -----------------------------------------------------------------------------
def test_upload_extract_duplicate_detection(client, db, upload_test_setup, recruiter_token, tmp_path):
    txt_path = tmp_path / "questions_dup.txt"
    # Question 1 is an existing seeded question: "What is the primary difference between a list and a tuple in Python?"
    existing_q = db.query(QuestionBankItem).filter(QuestionBankItem.technology == "Python").first()

    content = f"""
    1. {existing_q.question_text}
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: A

    2. A brand new unique question about GraphQL resolvers?
    A) First choice
    B) Second choice
    C) Third choice
    D) Fourth choice
    Answer: B

    3. A brand new unique question about GraphQL resolvers?
    A) First choice
    B) Second choice
    C) Third choice
    D) Fourth choice
    Answer: B
    """
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(txt_path, "rb") as f:
        res = client.post(
            "/api/v1/question-bank/upload-extract",
            files={"file": ("questions_dup.txt", f, "text/plain")},
            data={"technology": "Python"},
            headers={"Authorization": f"Bearer {recruiter_token}"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["total_extracted"] == 3
    assert data["duplicate_count"] >= 2

    # Q1 is duplicate against database
    assert data["questions"][0]["validation_status"] == "EXACT_DUPLICATE"
    assert data["questions"][0]["similar_to_id"] == existing_q.id

    # Q2 is unique
    assert data["questions"][1]["validation_status"] == "VALID"

    # Q3 is in-file duplicate of Q2
    assert data["questions"][2]["validation_status"] == "EXACT_DUPLICATE"

# -----------------------------------------------------------------------------
# 6. SCENARIO 8, 9, 10, 11: RECRUITER EDITS & BATCH IMPORTS APPROVED QUESTIONS
# -----------------------------------------------------------------------------
def test_batch_import_approved_questions_and_availability_growth(client, db, upload_test_setup, recruiter_token):
    # Check baseline availability for newly created technology
    tech_name = "CloudDevOps2026"
    avail_before = client.get(
        f"/api/v1/question-bank/availability?technology={tech_name}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    ).json()
    assert avail_before["total_available"] == 0

    # Recruiter submits 5 approved questions via batch-import
    payload = {
        "filename": "cloud_exam.pdf",
        "file_type": "PDF",
        "file_size": 10240,
        "technology": tech_name,
        "topic": "Containers",
        "questions": [
            {
                "question_text": f"Explain containerization principle #{i} in microservices architecture?",
                "options": [
                    {"option_key": "A", "option_text": "Option A text", "is_correct": (i % 2 == 0)},
                    {"option_key": "B", "option_text": "Option B text", "is_correct": (i % 2 != 0)},
                    {"option_key": "C", "option_text": "Option C text", "is_correct": False},
                    {"option_key": "D", "option_text": "Option D text", "is_correct": False}
                ],
                "difficulty": "INTERMEDIATE" if i < 3 else "ADVANCED",
                "marks": 2,
                "explanation": f"Detailed architectural explanation for #{i}",
                "technology": tech_name,
                "topic": "Containers",
                "source_file": "cloud_exam.pdf",
                "source_page": i + 1,
                "is_approved": True
            } for i in range(1, 6)
        ]
    }

    import_res = client.post(
        "/api/v1/question-bank/batch-import",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert import_res.status_code == 200
    import_data = import_res.json()
    assert import_data["imported_count"] == 5
    assert len(import_data["imported_question_ids"]) == 5

    # Verify database state & QuestionImportBatch tracking
    batch_record = db.query(QuestionImportBatch).filter(QuestionImportBatch.id == import_data["import_batch_id"]).first()
    assert batch_record is not None
    assert batch_record.filename == "cloud_exam.pdf"
    assert batch_record.total_approved == 5

    # Check that questions are present in bank with recruiter ownership
    recruiter = upload_test_setup["recruiter"]
    saved_questions = db.query(QuestionBankItem).filter(
        QuestionBankItem.technology == tech_name,
        QuestionBankItem.created_by_user_id == recruiter.user_id
    ).all()
    assert len(saved_questions) == 5
    assert all(q.source_file == "cloud_exam.pdf" for q in saved_questions)
    assert all(q.import_batch_id == batch_record.id for q in saved_questions)

    # Invariant: Availability refreshed and grew from 0 to 5
    avail_after = client.get(
        f"/api/v1/question-bank/availability?technology={tech_name}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    ).json()
    assert avail_after["total_available"] == 5
    assert avail_after["intermediate_count"] == 2
    assert avail_after["advanced_count"] == 3

# -----------------------------------------------------------------------------
# 7. SCENARIO 12 & 13: AUTO-GENERATE ASSESSMENTS POST-IMPORT
# -----------------------------------------------------------------------------
def test_auto_generate_after_import_sufficiency(client, db, upload_test_setup, recruiter_token):
    job = upload_test_setup["job"]
    tech_name = "CloudDevOps2026"

    # Requesting 10 questions fails because only 5 exist
    fail_res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json={
            "job_id": job.id,
            "title": "Cloud Scale Test",
            "technology": tech_name,
            "total_questions": 10,
            "duration_minutes": 30,
            "passing_marks": 5
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert fail_res.status_code == 400
    assert "Requested 10 questions" in fail_res.json()["detail"]

    # Requesting 5 questions succeeds cleanly
    success_res = client.post(
        "/api/v1/question-bank/auto-generate-assessment",
        json={
            "job_id": job.id,
            "title": "Cloud Scale Test (5Q)",
            "technology": tech_name,
            "total_questions": 5,
            "duration_minutes": 25,
            "passing_marks": 5
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert success_res.status_code in [200, 201]
    created = success_res.json()
    assert created["question_count"] == 5

# -----------------------------------------------------------------------------
# 8. SCENARIO 14: CANDIDATE CANNOT ACCESS ANSWER KEYS
# -----------------------------------------------------------------------------
def test_candidate_cannot_access_answer_keys(client, db, upload_test_setup, candidate_token):
    # Candidate browses jobs or takes an assessment
    # Candidate should not have access to question bank management endpoints
    fail_browse = client.get(
        "/api/v1/question-bank/questions",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    # Question bank management is restricted to recruiters and admins
    assert fail_browse.status_code in [401, 403]
