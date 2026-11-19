import os
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import User, RoleEnum
from app.core.security import create_access_token, get_password_hash
from app.core.database import get_db, SessionLocal
from app.core.deps import get_current_user
from app.chatbot.history import SQLiteHistoryStore, SessionOwnershipError

@pytest.fixture
def test_users(db: Session):
    """Create two test users: candidate and recruiter."""
    cand_id = str(uuid.uuid4())
    rec_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user_a = User(
        id=cand_id,
        name="Candidate Alice",
        email=f"alice_{cand_id[:8]}@example.com",
        password_hash=get_password_hash("Secret123!"),
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True,
        email_verified_at=now
    )
    user_b = User(
        id=rec_id,
        name="Recruiter Bob",
        email=f"bob_{rec_id[:8]}@example.com",
        password_hash=get_password_hash("Secret123!"),
        role=RoleEnum.RECRUITER,
        is_active=True,
        email_verified=True,
        email_verified_at=now
    )
    db.add_all([user_a, user_b])
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)

    token_a = create_access_token({"sub": user_a.id, "role": user_a.role.value})
    token_b = create_access_token({"sub": user_b.id, "role": user_b.role.value})

    return {
        "user_a": user_a,
        "token_a": token_a,
        "user_b": user_b,
        "token_b": token_b
    }

# 1. Unaffected Existing Health and Root Endpoints
def test_existing_root_and_health_unaffected(client):
    """Verify standard / and /health endpoints remain exactly as before."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["status"] == "operational"
    assert data_root["project"] == "SkillSphere"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}

# 2. Chatbot Diagnostic Health Endpoint
def test_chatbot_health_endpoint(client):
    """Verify /api/v1/chat/health reports healthy engine and storage metrics."""
    res = client.get("/api/v1/chat/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["engine"] == "rule_based_deterministic"
    assert data["total_faqs"] >= 25
    assert data["storage_backend"] in ["sqlite", "postgres"]

# 3. FAQ Retrieval
def test_get_faqs_role_filtering(client):
    """Verify /api/v1/chat/faqs filters candidate vs recruiter FAQs correctly."""
    res_cand = client.get("/api/v1/chat/faqs?role=JOB_SEEKER")
    assert res_cand.status_code == 200
    cand_data = res_cand.json()
    assert cand_data["total"] >= 15
    assert all("JOB_SEEKER" in f["roles"] for f in cand_data["faqs"])

    res_rec = client.get("/api/v1/chat/faqs?role=RECRUITER")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["total"] >= 15
    assert all("RECRUITER" in f["roles"] for f in rec_data["faqs"])

# 4. Authentication Enforcement
def test_send_message_unauthenticated(client):
    """Verify unauthenticated message requests return HTTP 401."""
    res = client.post("/api/v1/chat/message", json={"message": "How do I upload my resume?"})
    assert res.status_code == 401

# 5. Full Chat Lifecycle with Context & History
def test_chat_lifecycle_context_and_history(client, test_users):
    """
    Test authenticated message sending, session creation, contextual follow-up,
    chronological history retrieval, and session deletion.
    """
    token_a = test_users["token_a"]
    headers = {"Authorization": f"Bearer {token_a}"}

    # Step 1: Send initial query
    res1 = client.post(
        "/api/v1/chat/message",
        headers=headers,
        json={"message": "How do I upload my resume?"}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["matched_intent"] == "candidate_resume_upload"
    session_id = data1["session_id"]
    assert session_id is not None
    assert len(data1["quick_replies"]) >= 2

    # Step 2: Send follow-up without specifying context_topic (should restore from session)
    res2 = client.post(
        "/api/v1/chat/message",
        headers=headers,
        json={
            "message": "tell me more",
            "session_id": session_id
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["matched_intent"] == "candidate_resume_upload"
    assert data2["confidence_score"] >= 0.90

    # Step 3: Retrieve history
    res_hist = client.get(f"/api/v1/chat/history/{session_id}", headers=headers)
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["session_id"] == session_id
    assert hist_data["total_messages"] >= 4  # 2 user messages + 2 assistant messages
    # Verify chronological order
    created_ats = [m["created_at"] for m in hist_data["messages"]]
    assert created_ats == sorted(created_ats)

# 6. Cross-User History Protection
def test_cross_user_history_isolation(client, test_users):
    """Verify User B cannot read or delete User A's session history (HTTP 403)."""
    token_a = test_users["token_a"]
    token_b = test_users["token_b"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a session
    res_a = client.post(
        "/api/v1/chat/message",
        headers=headers_a,
        json={"message": "How do I search for jobs?"}
    )
    assert res_a.status_code == 200
    session_id_a = res_a.json()["session_id"]

    # User B attempts to access User A's history -> HTTP 403 Forbidden
    res_b_read = client.get(f"/api/v1/chat/history/{session_id_a}", headers=headers_b)
    assert res_b_read.status_code == 403
    assert "Forbidden" in res_b_read.json()["detail"]

    # User B attempts to delete User A's history -> HTTP 403 Forbidden
    res_b_del = client.delete(f"/api/v1/chat/history/{session_id_a}", headers=headers_b)
    assert res_b_del.status_code == 403

    # User A successfully deletes their own session
    res_a_del = client.delete(f"/api/v1/chat/history/{session_id_a}", headers=headers_a)
    assert res_a_del.status_code == 200
    assert res_a_del.json()["deleted"] is True

    # User A reading deleted session -> HTTP 404 Not Found
    res_a_after = client.get(f"/api/v1/chat/history/{session_id_a}", headers=headers_a)
    assert res_a_after.status_code == 404

# 7. Invalid Inputs
def test_chat_invalid_empty_input(client, test_users):
    """Verify empty/blank message yields HTTP 400 Bad Request."""
    token_a = test_users["token_a"]
    headers = {"Authorization": f"Bearer {token_a}"}
    res = client.post("/api/v1/chat/message", headers=headers, json={"message": "   "})
    assert res.status_code == 400

# 8. SQLite Storage Store Direct Unit Tests
def test_sqlite_store_direct_isolation(tmp_path):
    """Verify SQLiteHistoryStore direct operations, rollback, and ownership checks."""
    test_db = str(tmp_path / "test_cb.db")
    store = SQLiteHistoryStore(db_path=test_db)
    assert store.is_healthy() is True

    # Create session
    s = store.get_or_create_session(None, "user_1", "JOB_SEEKER", "Test Session")
    sid = s["id"]
    assert sid is not None

    # Add message
    msg = store.add_message(sid, "user_1", "user", "Hello world")
    assert msg["content"] == "Hello world"

    # Cross-user access check
    with pytest.raises(SessionOwnershipError):
        store.get_session(sid, "user_2")

    with pytest.raises(SessionOwnershipError):
        store.get_session_messages(sid, "user_2")

    with pytest.raises(SessionOwnershipError):
        store.delete_session(sid, "user_2")

    # Legitimate retrieval
    msgs = store.get_session_messages(sid, "user_1")
    assert len(msgs) == 1

    # Legitimate deletion
    assert store.delete_session(sid, "user_1") is True
    assert store.get_session(sid, "user_1") is None
