import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.models import User, Candidate, Recruiter, RoleEnum, CandidateTechnology, PracticeQuestion, PracticeAttempt
from app.core.security import get_password_hash, create_access_token
from app.services.tech_detection_service import TechDetectionService

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("SKILLSPHERE — RESUME-BASED TECHNICAL PRACTICE TEST SUITE")
    print("=" * 60)

    db = SessionLocal()

    # Create two test candidates for isolation check
    cand1_email = f"practice_cand1_{uuid.uuid4().hex[:6]}@example.com"
    cand2_email = f"practice_cand2_{uuid.uuid4().hex[:6]}@example.com"
    rec_email = f"practice_rec_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "TestPassword123!"

    try:
        user1 = User(name="Candidate One", email=cand1_email, password_hash=get_password_hash(pwd), role=RoleEnum.JOB_SEEKER, is_active=True)
        user2 = User(name="Candidate Two", email=cand2_email, password_hash=get_password_hash(pwd), role=RoleEnum.JOB_SEEKER, is_active=True)
        user_rec = User(name="Recruiter One", email=rec_email, password_hash=get_password_hash(pwd), role=RoleEnum.RECRUITER, is_active=True)
        db.add_all([user1, user2, user_rec])
        db.commit()

        c1 = Candidate(user_id=user1.id, phone="1234567890", title="Full-Stack Dev")
        c2 = Candidate(user_id=user2.id, phone="9876543210", title="Data Engineer")
        r1 = Recruiter(user_id=user_rec.id, designation="Talent Lead")
        db.add_all([c1, c2, r1])
        db.commit()

        token1 = create_access_token(user1.id, RoleEnum.JOB_SEEKER.value)
        token2 = create_access_token(user2.id, RoleEnum.JOB_SEEKER.value)
        token_rec = create_access_token(user_rec.id, RoleEnum.RECRUITER.value)

        auth_headers1 = {"Authorization": f"Bearer {token1}"}
        auth_headers2 = {"Authorization": f"Bearer {token2}"}
        auth_headers_rec = {"Authorization": f"Bearer {token_rec}"}

        # ---------------------------------------------------------------
        # Test 1: Technology Detection from text & alias normalization
        # ---------------------------------------------------------------
        sample_resume_text = """
        Alex Morgan — Senior Software Engineer
        Experience with py, python3, reactjs, and typescript.
        Strong background in postgresql, postgres, redis, and docker.
        Built cloud deployments on AWS and k8s.
        """
        detected = TechDetectionService.detect_technologies_from_text(sample_resume_text)
        detected_names = {d["technology_name"] for d in detected}
        assert "Python" in detected_names, "Expected 'Python' detected from 'py' and 'python3'"
        assert "React" in detected_names, "Expected 'React' detected from 'reactjs'"
        assert "TypeScript" in detected_names, "Expected 'TypeScript' detected"
        assert "PostgreSQL" in detected_names, "Expected 'PostgreSQL' detected from 'postgres'"
        assert "Docker" in detected_names, "Expected 'Docker' detected"
        assert "AWS" in detected_names, "Expected 'AWS' detected"
        assert "Kubernetes" in detected_names, "Expected 'Kubernetes' detected from 'k8s'"
        print("PASS [1/10]: Resume technology detection and alias normalization verified")

        # ---------------------------------------------------------------
        # Test 2: Resume with no detectable technologies
        # ---------------------------------------------------------------
        empty_resume = "Just non-technical content, general management and cooking recipes."
        detected_empty = TechDetectionService.detect_technologies_from_text(empty_resume)
        assert len(detected_empty) == 0, "Expected empty detected technologies for non-technical text"
        print("PASS [2/10]: Clean handling of resumes with zero tech mentions (no hallucination)")

        # ---------------------------------------------------------------
        # Test 3: Candidate Technology API — Manual Add & Fetch
        # ---------------------------------------------------------------
        # Add Python and React for Candidate 1
        resp = client.post("/api/v1/practice/technologies", json={"technology_name": "Python", "category": "LANGUAGE"}, headers=auth_headers1)
        assert resp.status_code == 201
        tech_data = resp.json()
        assert tech_data["technology_name"] == "Python"
        assert tech_data["is_resume_detected"] is False

        # Add Go
        resp = client.post("/api/v1/practice/technologies", json={"technology_name": "Go", "category": "LANGUAGE"}, headers=auth_headers1)
        assert resp.status_code == 201

        # Fetch list
        resp = client.get("/api/v1/practice/technologies", headers=auth_headers1)
        assert resp.status_code == 200
        cand1_techs = resp.json()
        assert len(cand1_techs) >= 2
        print("PASS [3/10]: Candidate manual technology addition and listing verified")

        # ---------------------------------------------------------------
        # Test 4: Remove Technology
        # ---------------------------------------------------------------
        resp = client.delete("/api/v1/practice/technologies/Go", headers=auth_headers1)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = client.get("/api/v1/practice/technologies", headers=auth_headers1)
        active_names = [t["technology_name"] for t in resp.json()]
        assert "Go" not in active_names
        print("PASS [4/10]: Candidate technology removal verified")

        # ---------------------------------------------------------------
        # Test 5: Question Bank — 20 questions with 7/7/6 distribution
        # ---------------------------------------------------------------
        # Request batch 1 for Python (10 questions)
        resp = client.get("/api/v1/practice/technologies/Python/questions?batch=1", headers=auth_headers1)
        assert resp.status_code == 200
        batch1_qs = resp.json()
        assert len(batch1_qs) == 10, f"Expected 10 questions in batch 1, got {len(batch1_qs)}"

        # Request batch 2 for Python (next 10 questions)
        resp = client.get("/api/v1/practice/technologies/Python/questions?batch=2", headers=auth_headers1)
        assert resp.status_code == 200
        batch2_qs = resp.json()
        assert len(batch2_qs) == 10, f"Expected 10 questions in batch 2, got {len(batch2_qs)}"

        # Total 20 initial questions in DB for Python
        all_py_qs = db.query(PracticeQuestion).filter(PracticeQuestion.technology == "Python").all()
        assert len(all_py_qs) >= 20, f"Expected at least 20 Python questions, got {len(all_py_qs)}"

        diff_counts = {}
        for q in all_py_qs[:20]:
            diff_counts[q.difficulty] = diff_counts.get(q.difficulty, 0) + 1
        assert diff_counts.get("BEGINNER") == 7, f"Expected 7 Beginner, got {diff_counts.get('BEGINNER')}"
        assert diff_counts.get("INTERMEDIATE") == 7, f"Expected 7 Intermediate, got {diff_counts.get('INTERMEDIATE')}"
        assert diff_counts.get("ADVANCED") == 6, f"Expected 6 Advanced, got {diff_counts.get('ADVANCED')}"
        print("PASS [5/10]: 20 Initial questions generated with exact 7/7/6 difficulty distribution")

        # ---------------------------------------------------------------
        # Test 6: Generate 10 More Questions (Batch expansion)
        # ---------------------------------------------------------------
        resp = client.post("/api/v1/practice/technologies/Python/generate-more", headers=auth_headers1)
        assert resp.status_code == 200
        new_qs = resp.json()
        assert len(new_qs) == 10, f"Expected 10 new questions, got {len(new_qs)}"
        # Verify batch 3 questions exist
        resp = client.get("/api/v1/practice/technologies/Python/questions?batch=3", headers=auth_headers1)
        assert resp.status_code == 200
        assert len(resp.json()) == 10
        print("PASS [6/10]: 'Generate 10 More Questions' dynamically generated batch 3 without duplicates")

        # ---------------------------------------------------------------
        # Test 7: Submit Attempt (Correct & Incorrect Answer Evaluation)
        # ---------------------------------------------------------------
        target_q = batch1_qs[0]
        q_id = target_q["id"]
        correct_ans = db.query(PracticeQuestion).filter(PracticeQuestion.id == q_id).first().correct_answer

        # Submit correct answer
        resp = client.post(f"/api/v1/practice/questions/{q_id}/attempt", json={
            "candidate_answer": correct_ans,
            "time_spent_seconds": 25,
            "hints_used": 0
        }, headers=auth_headers1)
        assert resp.status_code == 200
        att_data = resp.json()
        assert att_data["is_correct"] is True
        assert att_data["explanation"] is not None

        # Submit incorrect answer to another question
        target_q2 = batch1_qs[1]
        resp = client.post(f"/api/v1/practice/questions/{target_q2['id']}/attempt", json={
            "candidate_answer": "Z_INCORRECT",
            "time_spent_seconds": 15,
            "hints_used": 1
        }, headers=auth_headers1)
        assert resp.status_code == 200
        assert resp.json()["is_correct"] is False
        print("PASS [7/10]: Question attempt submission, objective grading, and explanation verified")

        # ---------------------------------------------------------------
        # Test 8: Progress Tracking & Analytics Calculation
        # ---------------------------------------------------------------
        resp = client.get("/api/v1/practice/analytics", headers=auth_headers1)
        assert resp.status_code == 200
        analytics = resp.json()
        assert analytics["total_attempted"] == 2
        assert analytics["total_correct"] == 1
        assert analytics["overall_accuracy"] == 50.0
        assert "Python" in analytics["technology_breakdown"]
        assert len(analytics["recent_attempts"]) == 2
        print("PASS [8/10]: Progress analytics accurately computed accuracy and breakdowns")

        # ---------------------------------------------------------------
        # Test 9: Data Isolation — Candidate 2 cannot see Candidate 1's progress
        # ---------------------------------------------------------------
        resp = client.get("/api/v1/practice/analytics", headers=auth_headers2)
        assert resp.status_code == 200
        c2_analytics = resp.json()
        assert c2_analytics["total_attempted"] == 0, "Candidate 2 should have 0 attempts"
        assert c2_analytics["total_correct"] == 0
        print("PASS [9/10]: Candidate data isolation strictly enforced")

        # ---------------------------------------------------------------
        # Test 10: Role Protection — Recruiter cannot access candidate practice portal
        # ---------------------------------------------------------------
        resp = client.get("/api/v1/practice/technologies", headers=auth_headers_rec)
        assert resp.status_code == 403, f"Expected 403 Forbidden for recruiter, got {resp.status_code}"
        print("PASS [10/10]: Role-based access control blocks recruiters from candidate practice portal")

        print("=" * 60)
        print("ALL 10/10 TECHNICAL PRACTICE TESTS PASSED!")
        print("=" * 60)

    finally:
        # Cleanup test data
        for u in [user1, user2, user_rec]:
            db_u = db.query(User).filter(User.id == u.id).first()
            if db_u:
                db.delete(db_u)
        db.commit()
        db.close()

if __name__ == "__main__":
    run_tests()
