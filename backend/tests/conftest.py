import os
import sys
import tempfile
from pathlib import Path

# Ensure backend root is always in sys.path
backend_root = str(Path(__file__).resolve().parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

TEST_DB_FILE = Path(__file__).resolve().parent / "test_skillsphere.db"
if TEST_DB_FILE.exists():
    try:
        TEST_DB_FILE.unlink()
    except Exception:
        pass

# Configure environment BEFORE loading any app modules
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests-2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
settings.TESTING = True
settings.DATABASE_URL = "sqlite:///:memory:"
settings.SECRET_KEY = "test-secret-key-for-unit-tests-2026"

import app.core.database as db_module
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal

from app.core.database import Base, get_db
from app.main import app
from datetime import datetime, timezone
from app.models.models import RoleEnum, User, Candidate, Recruiter
from app.core.security import get_password_hash, create_access_token

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def candidate_user(db):
    user = db.query(User).filter(User.email == "test_candidate@skillsphere.com").first()
    if not user:
        user = User(
            name="Test Candidate",
            email="test_candidate@skillsphere.com",
            password_hash=get_password_hash("Secret123!"),
            role=RoleEnum.JOB_SEEKER,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
    if not candidate:
        candidate = Candidate(user_id=user.id, phone="+1234567890", title="Python Engineer")
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
    return user

@pytest.fixture
def candidate_token(candidate_user):
    return create_access_token(subject=candidate_user.id, role=candidate_user.role.value)

@pytest.fixture
def recruiter_user(db):
    user = db.query(User).filter(User.email == "test_recruiter@skillsphere.com").first()
    if not user:
        user = User(
            name="Test Recruiter",
            email="test_recruiter@skillsphere.com",
            password_hash=get_password_hash("Recruiter123!"),
            role=RoleEnum.RECRUITER,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        recruiter = Recruiter(user_id=user.id, designation="Hiring Manager")
        db.add(recruiter)
        db.commit()
        db.refresh(recruiter)
    return user

@pytest.fixture
def recruiter_token(recruiter_user):
    return create_access_token(subject=recruiter_user.id, role=recruiter_user.role.value)

@pytest.fixture
def admin_user(db):
    user = db.query(User).filter(User.email == "test_admin@skillsphere.com").first()
    if not user:
        user = User(
            name="Test Admin",
            email="test_admin@skillsphere.com",
            password_hash=get_password_hash("Admin123!"),
            role=RoleEnum.ADMIN,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    return create_access_token(subject=admin_user.id, role=admin_user.role.value)
