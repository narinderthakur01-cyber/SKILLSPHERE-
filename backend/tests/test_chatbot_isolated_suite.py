import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.models import User, RoleEnum
from app.chatbot.matcher import IntentMatcher
from app.chatbot.service import ChatbotService
from app.chatbot.history import SQLiteHistoryStore, SessionOwnershipError
from app.api.v1.chat import (
    send_chat_message,
    get_faqs,
    get_chat_history,
    delete_chat_history,
    get_chatbot_health
)
from app.schemas.chatbot_schemas import ChatMessageRequest

# ----------------------------------------------------------------------
# 1. Test Matcher & Knowledge Base
# ----------------------------------------------------------------------

def test_kb_structure_and_categories():
    svc = ChatbotService()
    assert len(svc.faqs) >= 30
    categories = {f["category"] for f in svc.faqs}
    assert categories == {"candidate", "recruiter", "general"}
    # Verify every FAQ has required keys
    for f in svc.faqs:
        assert "id" in f
        assert "intent" in f
        assert "roles" in f
        assert "sample_questions" in f
        assert "keywords" in f
        assert "response" in f
        assert "quick_replies" in f

def test_matcher_exact_and_fuzzy():
    svc = ChatbotService()
    # Exact match
    faq, score, mtype = svc.matcher.match("How do I upload my resume?", role="JOB_SEEKER")
    assert faq is not None
    assert faq["intent"] == "candidate_resume_upload"
    assert score == 1.0

    # Case-insensitive with extra spaces
    faq, score, _ = svc.matcher.match("   HOW DO I POST A NEW JOB?   ", role="RECRUITER")
    assert faq is not None
    assert faq["intent"] == "recruiter_create_job"
    assert score >= 0.70

def test_matcher_role_isolation():
    svc = ChatbotService()
    # Candidate asking recruiter question
    faq, score, _ = svc.matcher.match("How do I create a job posting?", role="JOB_SEEKER")
    if faq:
        assert faq["intent"] != "recruiter_create_job"

    # Recruiter asking candidate question
    faq, score, _ = svc.matcher.match("Where do I upload my CV?", role="RECRUITER")
    if faq:
        assert faq["intent"] != "candidate_resume_upload"

def test_matcher_follow_up_context():
    svc = ChatbotService()
    # Generic follow up
    faq, score, mtype = svc.matcher.match("tell me more", role="JOB_SEEKER", context_topic="candidate_resume_upload")
    assert faq["intent"] == "candidate_resume_upload"
    assert score >= 0.90
    assert mtype == "context_followup"

    # Context shortcut
    faq, score, mtype = svc.matcher.match("what formats are supported?", role="JOB_SEEKER", context_topic="candidate_resume_upload")
    assert faq["intent"] in ["candidate_resume_formats", "candidate_resume_upload"]
    assert score >= 0.60

def test_matcher_fallback():
    svc = ChatbotService()
    faq, score, mtype = svc.matcher.match("xyzabc nonexistent gibberish query 12345", role="JOB_SEEKER")
    assert faq is None
    assert mtype == "fallback"
    assert score < 0.50

# ----------------------------------------------------------------------
# 2. Test SQLite History Store (Isolated)
# ----------------------------------------------------------------------

@pytest.fixture
def temp_store(tmp_path):
    db_file = str(tmp_path / "test_history.db")
    return SQLiteHistoryStore(db_path=db_file)

def test_store_session_lifecycle(temp_store):
    user_id = str(uuid.uuid4())
    # Create session
    sess = temp_store.get_or_create_session(None, user_id, "JOB_SEEKER", "Initial Title")
    sid = sess["id"]
    assert sid is not None
    assert sess["user_id"] == user_id
    assert sess["title"] == "Initial Title"

    # Insert messages
    m1 = temp_store.add_message(sid, user_id, "user", "Question 1")
    m2 = temp_store.add_message(sid, user_id, "assistant", "Answer 1", intent="intent_1", confidence=0.95)

    assert m1["id"] != m2["id"]
    assert m1["sender"] == "user"
    assert m2["sender"] == "assistant"

    # Retrieve messages in chronological order
    msgs = temp_store.get_session_messages(sid, user_id)
    assert len(msgs) == 2
    assert msgs[0]["content"] == "Question 1"
    assert msgs[1]["content"] == "Answer 1"
    assert msgs[0]["created_at"] <= msgs[1]["created_at"]

    # Context update
    temp_store.update_session_topic(sid, user_id, "intent_1")
    updated_sess = temp_store.get_session(sid, user_id)
    assert updated_sess["last_topic"] == "intent_1"

    # Delete session
    deleted = temp_store.delete_session(sid, user_id)
    assert deleted is True
    assert temp_store.get_session(sid, user_id) is None
    assert len(temp_store.get_session_messages(sid, user_id)) == 0

def test_store_cross_user_isolation(temp_store):
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())

    sess_a = temp_store.get_or_create_session(None, user_a, "JOB_SEEKER", "Alice Session")
    sid_a = sess_a["id"]
    temp_store.add_message(sid_a, user_a, "user", "Private message of Alice")

    # User B attempts to read User A session -> SessionOwnershipError
    with pytest.raises(SessionOwnershipError):
        temp_store.get_session(sid_a, user_b)

    # User B attempts to read User A messages -> SessionOwnershipError
    with pytest.raises(SessionOwnershipError):
        temp_store.get_session_messages(sid_a, user_b)

    # User B attempts to delete User A session -> SessionOwnershipError
    with pytest.raises(SessionOwnershipError):
        temp_store.delete_session(sid_a, user_b)

    # User B attempts to update User A session topic -> SessionOwnershipError
    with pytest.raises(SessionOwnershipError):
        temp_store.update_session_topic(sid_a, user_b, "hijacked_topic")

# ----------------------------------------------------------------------
# 3. Test API Route Controllers (Direct Handler Verification)
# ----------------------------------------------------------------------

@pytest.fixture
def mock_users():
    user_cand = User(
        id=str(uuid.uuid4()),
        name="Candidate Jane",
        email="jane@example.com",
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True
    )
    user_rec = User(
        id=str(uuid.uuid4()),
        name="Recruiter John",
        email="john@example.com",
        role=RoleEnum.RECRUITER,
        is_active=True,
        email_verified=True
    )
    user_attacker = User(
        id=str(uuid.uuid4()),
        name="Attacker Mal",
        email="mal@example.com",
        role=RoleEnum.JOB_SEEKER,
        is_active=True,
        email_verified=True
    )
    return {
        "candidate": user_cand,
        "recruiter": user_rec,
        "attacker": user_attacker
    }

def test_route_send_message_and_context(mock_users):
    user = mock_users["candidate"]
    # 1. Initial message
    req1 = ChatMessageRequest(message="How do I upload my resume?")
    res1 = send_chat_message(payload=req1, current_user=user)
    assert res1.matched_intent == "candidate_resume_upload"
    assert res1.confidence_score == 1.0
    sid = res1.session_id
    assert sid is not None

    # 2. Contextual follow up in same session without client context hint
    req2 = ChatMessageRequest(message="tell me more", session_id=sid)
    res2 = send_chat_message(payload=req2, current_user=user)
    assert res2.matched_intent == "candidate_resume_upload"
    assert res2.confidence_score >= 0.90

    # 3. Retrieve history
    hist = get_chat_history(session_id=sid, current_user=user)
    assert hist.session_id == sid
    assert hist.total_messages >= 4
    assert hist.messages[0].sender == "user"
    assert hist.messages[1].sender == "assistant"

def test_route_cross_user_forbidden(mock_users):
    user_a = mock_users["candidate"]
    attacker = mock_users["attacker"]

    # User A creates a session
    req = ChatMessageRequest(message="How do I search for jobs?")
    res = send_chat_message(payload=req, current_user=user_a)
    sid = res.session_id

    # Attacker tries to read User A's session -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        get_chat_history(session_id=sid, current_user=attacker)
    assert exc_info.value.status_code == 403

    # Attacker tries to delete User A's session -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        delete_chat_history(session_id=sid, current_user=attacker)
    assert exc_info.value.status_code == 403

def test_route_empty_message_bad_request(mock_users):
    user = mock_users["candidate"]
    req = ChatMessageRequest(message="   ")
    with pytest.raises(HTTPException) as exc_info:
        send_chat_message(payload=req, current_user=user)
    assert exc_info.value.status_code == 400

def test_route_nonexistent_session_not_found(mock_users):
    user = mock_users["candidate"]
    fake_id = str(uuid.uuid4())
    with pytest.raises(HTTPException) as exc_info:
        get_chat_history(session_id=fake_id, current_user=user)
    assert exc_info.value.status_code == 404

def test_route_delete_session_success(mock_users):
    user = mock_users["candidate"]
    req = ChatMessageRequest(message="Temporary question to delete")
    res = send_chat_message(payload=req, current_user=user)
    sid = res.session_id

    del_res = delete_chat_history(session_id=sid, current_user=user)
    assert del_res.deleted is True

    # After deletion, reading yields 404
    with pytest.raises(HTTPException) as exc_info:
        get_chat_history(session_id=sid, current_user=user)
    assert exc_info.value.status_code == 404

def test_route_faqs_and_health():
    # FAQ listing
    faqs_cand = get_faqs(role="JOB_SEEKER")
    assert faqs_cand.total >= 15

    faqs_rec = get_faqs(role="RECRUITER")
    assert faqs_rec.total >= 15

    # Health diagnostic
    health = get_chatbot_health()
    assert health.status in ["healthy", "degraded"]
    assert health.engine == "rule_based_deterministic"
    assert health.total_faqs >= 30
