import sys
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import User, PasswordResetToken
from app.core.security import get_password_hash
from app.services.email_service import get_mock_deliveries, clear_mock_deliveries

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("SKILLSPHERE — PASSWORD RECOVERY BACKEND TEST SUITE")
    print("=" * 60)

    db = SessionLocal()
    clear_mock_deliveries()

    test_email = "test_pwd_recovery@example.com"
    initial_password = "InitialPassword123!"
    new_password = "BrandNewSecurePassword2026!"

    try:
        # Step 0: Ensure clean test user
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        test_user = User(
            name="Password Test Candidate",
            email=test_email,
            password_hash=get_password_hash(initial_password),
            role="JOB_SEEKER",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"PASS: Created test user {test_email}")

        # Test 1: Request password reset for unregistered email (Anti-enumeration check)
        resp = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent_random_user_999@example.com"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert "password reset link has been dispatched" in resp.json()["message"]
        print("PASS [1/11]: Unregistered email returns generic success response (Anti-enumeration enforced)")

        # Test 2: Request password reset for valid registered email
        resp = client.post("/api/v1/auth/forgot-password", json={"email": test_email})
        assert resp.status_code == 200
        assert "password reset link has been dispatched" in resp.json()["message"]
        
        # Verify token in database and mock email delivery
        deliveries = get_mock_deliveries()
        assert len(deliveries) >= 1, "Expected mock delivery to be recorded"
        latest_delivery = deliveries[-1]
        assert latest_delivery["to_email"] == test_email
        plain_token = latest_delivery["reset_token"]
        assert len(plain_token) >= 20

        token_hash = hashlib.sha256(plain_token.encode("utf-8")).hexdigest()
        db_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
        assert db_token is not None, "Token hash not found in database"
        assert db_token.is_used is False, "Token should be unused initially"
        print("PASS [2/11]: Valid email reset token generated, hashed in DB, and email queued")

        # Test 3: Password confirmation mismatch
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": plain_token,
            "new_password": new_password,
            "confirm_password": "MismatchedPassword123!"
        })
        assert resp.status_code == 400
        assert "do not match" in resp.json()["detail"]
        print("PASS [3/11]: Password confirmation mismatch rejected with 400")

        # Test 4: Short password (< 8 chars)
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": plain_token,
            "new_password": "short",
            "confirm_password": "short"
        })
        assert resp.status_code == 400
        assert "at least 8 characters" in resp.json()["detail"]
        print("PASS [4/11]: Short password (<8 chars) rejected with 400")

        # Test 5: Bogus / Invalid token
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": "completely_invalid_token_xyz_12345",
            "new_password": new_password,
            "confirm_password": new_password
        })
        assert resp.status_code == 400
        assert "Invalid or already used" in resp.json()["detail"]
        print("PASS [5/11]: Invalid token rejected with 400")

        # Test 6: Expired token
        expired_token_str = "expired_test_token_string_12345678"
        expired_hash = hashlib.sha256(expired_token_str.encode("utf-8")).hexdigest()
        expired_rec = PasswordResetToken(
            user_id=test_user.id,
            token_hash=expired_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            is_used=False
        )
        db.add(expired_rec)
        db.commit()

        resp = client.post("/api/v1/auth/reset-password", json={
            "token": expired_token_str,
            "new_password": new_password,
            "confirm_password": new_password
        })
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()
        print("PASS [6/11]: Expired token rejected with 400")

        # Test 7: Successful password reset with valid token
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": plain_token,
            "new_password": new_password,
            "confirm_password": new_password
        })
        assert resp.status_code == 200
        assert "successfully reset" in resp.json()["message"]
        print("PASS [7/11]: Valid token successfully resets password")

        # Test 8: Single-use check — token reuse must be rejected
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": plain_token,
            "new_password": "YetAnotherPassword123!",
            "confirm_password": "YetAnotherPassword123!"
        })
        assert resp.status_code == 400
        assert "Invalid or already used" in resp.json()["detail"]
        print("PASS [8/11]: Token single-use enforced; second attempt rejected")

        # Test 9: Verify old password fails
        resp = client.post("/api/v1/auth/login", json={"email": test_email, "password": initial_password})
        assert resp.status_code == 401
        print("PASS [9/11]: Old password successfully invalidated")

        # Test 10: Verify new password succeeds
        resp = client.post("/api/v1/auth/login", json={"email": test_email, "password": new_password})
        assert resp.status_code == 200
        token_data = resp.json()
        assert "access_token" in token_data
        print("PASS [10/11]: Authentication with new password succeeds with JWT token")

        # Test 11: Rate limiting check (send multiple requests rapidly)
        spam_email = f"spam_test_{uuid.uuid4().hex[:6]}@example.com"
        # 5 should succeed (with generic msg)
        for i in range(5):
            r = client.post("/api/v1/auth/forgot-password", json={"email": spam_email})
            assert r.status_code == 200
        # 6th should trigger 429
        r = client.post("/api/v1/auth/forgot-password", json={"email": spam_email})
        assert r.status_code == 429, f"Expected 429 Too Many Requests, got {r.status_code}"
        print("PASS [11/11]: Rate limiting strictly enforces 429 after 5 requests in window")

        print("=" * 60)
        print("ALL 11/11 PASSWORD RECOVERY BACKEND TESTS PASSED!")
        print("=" * 60)

    finally:
        # Cleanup test user
        cleanup_user = db.query(User).filter(User.email == test_email).first()
        if cleanup_user:
            db.delete(cleanup_user)
            db.commit()
        db.close()

if __name__ == "__main__":
    run_tests()
