import hashlib
from datetime import datetime, timezone, timedelta
import pytest
from app.models.models import RoleEnum, User, EmailVerificationToken
from app.core.security import get_password_hash, create_access_token

def test_registration_sets_unverified_and_generates_token(client, db):
    email = "new_candidate_verify@skillsphere.com"
    response = client.post("/api/v1/auth/register", json={
        "name": "Verify Candidate",
        "email": email,
        "password": "Password123!",
        "role": RoleEnum.JOB_SEEKER.value
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == email
    assert data["user"]["email_verified"] is False
    assert data["user"]["email_verified_at"] is None

    # Verify token row in DB
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.email_verified is False

    tokens = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).all()
    assert len(tokens) == 1
    token_row = tokens[0]
    assert token_row.used_at is None
    assert token_row.token_hash is not None

def test_login_blocked_for_unverified_user(client, db):
    email = "unverified_login_test@skillsphere.com"
    user = User(
        name="Unverified User",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()

    # Attempt login
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert response.status_code == 403
    assert "Email verification required" in response.json()["detail"]

def test_verify_email_success_post(client, db):
    email = "verify_flow_post@skillsphere.com"
    user = User(
        name="Verify Flow",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = "secure_test_token_post_flow_12345678"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )
    db.add(token_obj)
    db.commit()

    # Verify via POST
    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["email_verified"] is True
    assert "successfully verified" in res_data["message"].lower()

    # DB state verified
    db.refresh(user)
    assert user.email_verified is True
    assert user.email_verified_at is not None

    db.refresh(token_obj)
    assert token_obj.used_at is not None

def test_verify_email_success_get(client, db):
    email = "verify_flow_get@skillsphere.com"
    user = User(
        name="Verify Flow GET",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.RECRUITER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = "secure_test_token_get_flow_87654321"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )
    db.add(token_obj)
    db.commit()

    # Verify via GET
    response = client.get(f"/api/v1/auth/verify-email?token={raw_token}")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["email_verified"] is True

    # User can now log in successfully
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email_verified"] is True

def test_verify_email_token_reuse_rejected(client, db):
    email = "reuse_token_test@skillsphere.com"
    user = User(
        name="Reuse Tester",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = "already_used_token_string_999"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db.add(token_obj)
    db.commit()

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 400
    assert "already used" in response.json()["detail"].lower()

def test_verify_email_expired_token_rejected(client, db):
    email = "expired_token_test@skillsphere.com"
    user = User(
        name="Expired Tester",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = "expired_token_string_000"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=10) # 10 minutes ago
    )
    db.add(token_obj)
    db.commit()

    response = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

def test_verify_email_invalid_token_rejected(client):
    response = client.post("/api/v1/auth/verify-email", json={"token": "non_existent_token_12345"})
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

def test_resend_verification_cooldown_enforced(client, db):
    email = "cooldown_test@skillsphere.com"
    user = User(
        name="Cooldown Tester",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Add token created 10 seconds ago
    raw_token = "recent_token_123"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        created_at=datetime.now(timezone.utc) - timedelta(seconds=10)
    )
    db.add(token_obj)
    db.commit()

    response = client.post("/api/v1/auth/resend-verification", json={"email": email})
    assert response.status_code == 429
    assert "wait" in response.json()["detail"].lower()

def test_resend_verification_after_cooldown_success(client, db):
    email = "cooldown_pass_test@skillsphere.com"
    user = User(
        name="Cooldown Pass",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Token created 75 seconds ago
    raw_token = "old_token_123"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_obj = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=28),
        created_at=datetime.now(timezone.utc) - timedelta(seconds=75)
    )
    db.add(token_obj)
    db.commit()

    response = client.post("/api/v1/auth/resend-verification", json={"email": email})
    assert response.status_code == 200
    assert "verification" in response.json()["message"].lower()

    # Old token was marked used/invalidated
    db.refresh(token_obj)
    assert token_obj.used_at is not None

def test_require_verified_user_blocks_unverified_jwt(client, db):
    email = "unverified_jwt_test@skillsphere.com"
    user = User(
        name="Unverified JWT Candidate",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Even if they have a JWT token somehow, protected endpoints block them
    token = create_access_token(subject=user.id, role=user.role.value)
    response = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Email verification required" in response.json()["detail"]

def test_verification_status_endpoint(client, db):
    email = "status_check@skillsphere.com"
    user = User(
        name="Status Check",
        email=email,
        password_hash=get_password_hash("Password123!"),
        role=RoleEnum.JOB_SEEKER,
        email_verified=False
    )
    db.add(user)
    db.commit()

    # Check status when unverified
    res1 = client.get(f"/api/v1/auth/verification-status?email={email}")
    assert res1.status_code == 200
    assert res1.json()["email_verified"] is False

    # Mark verified
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()

    # Check status when verified
    res2 = client.get(f"/api/v1/auth/verification-status?email={email}")
    assert res2.status_code == 200
    assert res2.json()["email_verified"] is True
