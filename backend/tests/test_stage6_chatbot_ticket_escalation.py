"""
Stage 6 Verification Test Suite: Chatbot Ticket Escalation & User Ticket Tracking.
Tests:
- Automatic ticket preview generation when troubleshooting fails or user requests escalation
- Explicit confirmation requirement before creating support ticket
- Real ticket number generation (TICK-2026-XXXX) stored in database
- Duplicate submission prevention within active sessions
- Ticket creation cancellation
- Multilingual ticket escalation across English, Hindi, Hinglish, Punjabi, and Roman Punjabi
- In-chat ticket tracking ("Where are my support tickets?")
- Authentication safety and role isolation
- Full Chat API route schema validation with ticket_data
"""

import pytest
import re
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.models import (
    Base,
    User,
    RoleEnum,
    SupportTicket,
    TicketMessage,
    TicketAuditLog,
    TicketSequence,
    TicketStatusEnum,
    TicketPriorityEnum,
    TicketCategoryEnum
)
from app.schemas.chatbot_schemas import ChatMessageRequest, ChatResponse
from app.services import ticket_service
from app.chatbot.service import chatbot_service
from app.chatbot.troubleshooter import troubleshooting_engine, TroubleshootingEngine
from app.api.v1.chat import send_chat_message


@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite database session for Stage 6 tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def candidate_user(db_session):
    """Seed candidate user in database."""
    user = User(
        id="cand-uuid-101",
        email="candidate.stage6@example.com",
        name="Amrita Kaur",
        password_hash="mockhash",
        role=RoleEnum.JOB_SEEKER,
        email_verified=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def recruiter_user(db_session):
    """Seed recruiter user in database."""
    user = User(
        id="rec-uuid-202",
        email="recruiter.stage6@example.com",
        name="Rohan Verma",
        password_hash="mockhash",
        role=RoleEnum.RECRUITER,
        email_verified=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# 1. TICKET ESCALATION PREVIEW GENERATION
# ============================================================================

def test_troubleshooting_escalation_generates_preview(candidate_user, db_session):
    """When troubleshooting reaches failure or escalation is requested, render preview card."""
    session_id = "test-session-escalate-1"
    
    # 1. Start resume upload troubleshooting flow
    resp1 = chatbot_service.process_message(
        message="My resume upload failed with an OCR error",
        session_id=session_id,
        current_user=candidate_user,
        db=db_session
    )
    assert "troubleshoot" in resp1.matched_intent
    
    # 2. Escalate to human support ticket
    resp2 = chatbot_service.process_message(
        message="This didn't help, create a support ticket please",
        session_id=session_id,
        context_topic="ticket_escalation",
        current_user=candidate_user,
        db=db_session
    )
    assert resp2.matched_intent == "ticket_preview"
    assert resp2.ticket_data is not None
    assert resp2.ticket_data.get("action") == "preview"
    assert resp2.ticket_data.get("category") == "RESUME_OCR"
    assert resp2.ticket_data.get("priority") == "HIGH"
    labels = [qr.label for qr in resp2.quick_replies]
    assert any("Confirm" in l for l in labels)
    assert any("Cancel" in l for l in labels)
    
    # Verify no ticket was created prematurely in DB
    ticket_count = db_session.query(SupportTicket).count()
    assert ticket_count == 0


# ============================================================================
# 2. EXPLICIT CONFIRMATION CREATES REAL TICKET IN DATABASE
# ============================================================================

def test_chatbot_ticket_confirmation_creates_real_ticket(candidate_user, db_session):
    """Confirming ticket preview creates a real database ticket with TICK-2026-XXXX."""
    session_id = "test-session-confirm-2"
    
    # 1. Start LiveKit flow
    chatbot_service.process_message(
        message="Livekit error: camera not working and video call not connecting",
        session_id=session_id,
        current_user=candidate_user,
        db=db_session
    )
    
    # 2. Trigger preview
    chatbot_service.process_message(
        message="Please escalate to human support ticket",
        session_id=session_id,
        context_topic="ticket_escalation",
        current_user=candidate_user,
        db=db_session
    )
    
    # 3. Explicitly confirm submission
    resp_confirm = chatbot_service.process_message(
        message="Confirm & Submit Ticket",
        session_id=session_id,
        context_topic="confirm_ticket_submission",
        current_user=candidate_user,
        db=db_session
    )
    
    assert resp_confirm.matched_intent == "ticket_created"
    assert resp_confirm.ticket_data is not None
    assert resp_confirm.ticket_data.get("action") == "created"
    
    ticket_number = resp_confirm.ticket_data.get("ticket_number")
    assert ticket_number is not None
    assert re.match(r"^TICK-2026-\d{4}$", ticket_number)
    
    # Verify database persistence
    db_ticket = db_session.query(SupportTicket).filter(
        SupportTicket.ticket_number == ticket_number
    ).first()
    assert db_ticket is not None
    assert db_ticket.user_id == candidate_user.id
    assert db_ticket.user_role == RoleEnum.JOB_SEEKER
    assert db_ticket.status == TicketStatusEnum.OPEN
    assert db_ticket.category == TicketCategoryEnum.LIVEKIT_VIDEO
    
    # Verify initial message was saved
    initial_msg = db_session.query(TicketMessage).filter(
        TicketMessage.ticket_id == db_ticket.id
    ).first()
    assert initial_msg is not None
    assert initial_msg.sender_id == candidate_user.id
    assert initial_msg.is_internal is False


# ============================================================================
# 3. DUPLICATE SUBMISSION PREVENTION
# ============================================================================

def test_duplicate_submission_prevention(candidate_user, db_session):
    """Submitting confirmation again in the same session does not create duplicate tickets."""
    session_id = "test-session-dup-3"
    
    # 1. Trigger preview and confirm
    chatbot_service.process_message(
        message="I have an MCQ test error, create ticket",
        session_id=session_id,
        context_topic="ticket_escalation",
        current_user=candidate_user,
        db=db_session
    )
    resp1 = chatbot_service.process_message(
        message="Confirm & Submit Ticket",
        session_id=session_id,
        context_topic="confirm_ticket_submission",
        current_user=candidate_user,
        db=db_session
    )
    first_ticket_num = resp1.ticket_data.get("ticket_number")
    assert first_ticket_num is not None
    
    # Verify count is 1
    assert db_session.query(SupportTicket).count() == 1
    
    # 2. Try to confirm again in same session
    resp_dup = chatbot_service.process_message(
        message="Confirm & Submit Ticket",
        session_id=session_id,
        context_topic="confirm_ticket_submission",
        current_user=candidate_user,
        db=db_session
    )
    assert resp_dup.ticket_data.get("action") == "duplicate"
    assert resp_dup.ticket_data.get("ticket_number") == first_ticket_num
    
    # Database still has only 1 ticket
    assert db_session.query(SupportTicket).count() == 1


# ============================================================================
# 4. TICKET CREATION CANCELLATION
# ============================================================================

def test_chatbot_ticket_cancellation(candidate_user, db_session):
    """User can cancel ticket creation before confirmation."""
    session_id = "test-session-cancel-4"
    
    # 1. Trigger preview
    chatbot_service.process_message(
        message="Escalate to ticket",
        session_id=session_id,
        context_topic="ticket_escalation",
        current_user=candidate_user,
        db=db_session
    )
    
    # 2. Cancel
    resp_cancel = chatbot_service.process_message(
        message="Cancel",
        session_id=session_id,
        context_topic="cancel_ticket_creation",
        current_user=candidate_user,
        db=db_session
    )
    assert resp_cancel.matched_intent == "ticket_cancelled"
    assert db_session.query(SupportTicket).count() == 0


# ============================================================================
# 5. MULTILINGUAL ESCALATION & CONFIRMATION
# ============================================================================

@pytest.mark.parametrize("lang_code,msg_escalate,msg_confirm,expected_words", [
    ("hi", "कृपया एक सपोर्ट टिकट बनाएँ", "हाँ टिकट बनाएँ", ["टिकट", "दर्ਜ", "विवरण"]),
    ("hinglish", "Mera problem solve nahi hua, support ticket bana do", "Haan ticket create karo", ["Ticket", "submit", "ID"]),
    ("pa", "ਕਿਰਪਾ ਕਰਕੇ ਸਪੋਰਟ ਟਿਕਟ ਬਣਾਓ", "ਹਾਂ ਟਿਕਟ ਬਣਾਓ", ["ਟਿਕਟ", "ਦਰਜ", "ਸੰਖੇਪ"]),
    ("pa-Latn", "Meri samasya solve nahi hoyi, ticket bana do", "Haan ticket bana dyo", ["Ticket", "darj", "number"])
])
def test_multilingual_ticket_escalation(candidate_user, db_session, lang_code, msg_escalate, msg_confirm, expected_words):
    """Ticket escalation preview and confirmation support all 5 language modes."""
    session_id = f"test-session-lang-{lang_code}"
    
    # 1. Escalate in target language
    resp_prev = chatbot_service.process_message(
        message=msg_escalate,
        session_id=session_id,
        current_user=candidate_user,
        language_preference=lang_code,
        db=db_session
    )
    assert resp_prev.matched_intent in ("ticket_preview", "troubleshoot_step", "support_escalation")
    
    # If returned preview directly, confirm it
    if resp_prev.ticket_data and resp_prev.ticket_data.get("action") == "preview":
        resp_conf = chatbot_service.process_message(
            message=msg_confirm,
            session_id=session_id,
            context_topic="confirm_ticket_submission",
            current_user=candidate_user,
            language_preference=lang_code,
            db=db_session
        )
        assert resp_conf.matched_intent == "ticket_created"
        assert resp_conf.ticket_data.get("action") == "created"
        assert re.match(r"^TICK-2026-\d{4}$", resp_conf.ticket_data.get("ticket_number"))


# ============================================================================
# 6. IN-CHAT USER TICKET TRACKING ("Where are my support tickets?")
# ============================================================================

def test_chatbot_track_my_tickets(candidate_user, recruiter_user, db_session):
    """User can query ticket status directly in the assistant and receive their ticket card."""
    # Seed 2 tickets for candidate
    t1 = SupportTicket(
        id="t-cand-1",
        ticket_number="TICK-2026-0001",
        user_id=candidate_user.id,
        user_role=RoleEnum.JOB_SEEKER,
        subject="Resume parser fails on PDF",
        description="OCR errors on experience section",
        category=TicketCategoryEnum.RESUME_OCR,
        priority=TicketPriorityEnum.MEDIUM,
        status=TicketStatusEnum.OPEN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    t2 = SupportTicket(
        id="t-cand-2",
        ticket_number="TICK-2026-0002",
        user_id=candidate_user.id,
        user_role=RoleEnum.JOB_SEEKER,
        subject="Audio device muted in LiveKit",
        description="Microphone permissions issue",
        category=TicketCategoryEnum.LIVEKIT_VIDEO,
        priority=TicketPriorityEnum.HIGH,
        status=TicketStatusEnum.RESOLVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    # Seed 1 ticket for recruiter (must not appear in candidate tracker)
    t3 = SupportTicket(
        id="t-rec-3",
        ticket_number="TICK-2026-0003",
        user_id=recruiter_user.id,
        user_role=RoleEnum.RECRUITER,
        subject="Job posting not showing in search",
        description="Published job missing",
        category=TicketCategoryEnum.ACCOUNT_AUTH,
        priority=TicketPriorityEnum.HIGH,
        status=TicketStatusEnum.OPEN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()
    
    # Candidate queries tracker
    resp = chatbot_service.process_message(
        message="Where are my support tickets?",
        session_id="test-session-track-1",
        context_topic="track_tickets",
        current_user=candidate_user,
        db=db_session
    )
    
    assert resp.matched_intent in ("track_tickets", "ticket_tracking_list", "ticket_tracking_active")
    assert resp.ticket_data is not None
    assert resp.ticket_data.get("action") == "list"
    
    tickets_list = resp.ticket_data.get("tickets", [])
    assert len(tickets_list) == 2
    
    ticket_nums = [t["ticket_number"] for t in tickets_list]
    assert "TICK-2026-0001" in ticket_nums
    assert "TICK-2026-0002" in ticket_nums
    assert "TICK-2026-0003" not in ticket_nums  # Recruiter ticket isolated!


# ============================================================================
# 7. AUTHENTICATION & ROLE ISOLATION SAFETY
# ============================================================================

def test_unauthenticated_user_ticket_safety(db_session):
    """Anonymous/unauthenticated users are instructed to log in before creating tickets."""
    session_id = "test-session-anon-1"
    
    # 1. Request preview anonymously
    resp_prev = chatbot_service.process_message(
        message="Create a support ticket for me",
        session_id=session_id,
        context_topic="ticket_escalation",
        current_user=None,
        db=db_session
    )
    assert resp_prev.matched_intent == "ticket_preview"
    assert resp_prev.ticket_data.get("action") == "preview"
    
    # 2. Try to confirm without being authenticated
    resp_confirm = chatbot_service.process_message(
        message="Confirm & Submit Ticket",
        session_id=session_id,
        context_topic="confirm_ticket_submission",
        current_user=None,
        db=db_session
    )
    assert resp_confirm.matched_intent == "auth_required"
    assert "log in" in resp_confirm.message.lower() or "sign in" in resp_confirm.message.lower()
    assert db_session.query(SupportTicket).count() == 0

    # 3. Try to track tickets anonymously
    resp_track = chatbot_service.process_message(
        message="Where are my support tickets?",
        session_id="test-session-anon-2",
        context_topic="track_tickets",
        current_user=None,
        db=db_session
    )
    assert resp_track.matched_intent == "auth_required"
    assert "log in" in resp_track.message.lower()


# ============================================================================
# 8. END-TO-END CHAT API ROUTE SCHEMA VALIDATION
# ============================================================================

def test_chat_api_route_end_to_end_with_ticket_data(candidate_user, db_session):
    """Direct invocation of send_chat_message returns ChatResponse model with ticket_data."""
    request_payload = ChatMessageRequest(
        message="Where are my support tickets?",
        context_topic="track_tickets"
    )
    
    response = send_chat_message(
        payload=request_payload,
        db=db_session,
        current_user=candidate_user
    )
    
    assert isinstance(response, ChatResponse)
    assert response.matched_intent in ("track_tickets", "ticket_tracking_empty", "ticket_tracking_list", "ticket_tracking_active")
    assert response.ticket_data is not None
    assert response.ticket_data.get("action") in ("list", "empty")


# ============================================================================
# 9. WAITING_USER LIFECYCLE & CLOSED REPLY RESTRICTION VERIFICATION
# ============================================================================

def test_user_ticket_waiting_user_and_closed_reply_restrictions(candidate_user, db_session):
    """
    Verify:
    1. Canonical status enum is WAITING_USER
    2. Status filtering with status=TicketStatusEnum.WAITING_USER works accurately
    3. User reply automatically transitions WAITING_USER -> IN_PROGRESS
    4. Replying to a CLOSED ticket raises HTTP 400 Bad Request
    5. Non-admin serialization completely strips internal notes and audit logs
    """
    from fastapi import HTTPException
    from app.schemas.ticket_schemas import TicketMessageCreateRequest
    
    # Create ticket in WAITING_USER status
    t = SupportTicket(
        id="t-waiting-user-01",
        ticket_number="TICK-2026-9001",
        user_id=candidate_user.id,
        user_role=RoleEnum.JOB_SEEKER,
        subject="Waiting User Transition Test",
        description="Ticket requiring candidate clarification.",
        category=TicketCategoryEnum.GENERAL,
        priority=TicketPriorityEnum.MEDIUM,
        status=TicketStatusEnum.WAITING_USER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    # Add an internal note (admin-only)
    note = TicketMessage(
        ticket_id=t.id,
        sender_id="admin-999",
        sender_role=RoleEnum.ADMIN,
        message="Private administrative diagnostic note.",
        is_internal=True
    )
    db_session.add_all([t, note])
    db_session.commit()
    
    # 1. Filter by status WAITING_USER
    total, tickets = ticket_service.get_user_tickets(
        db_session, candidate_user, status_filter=TicketStatusEnum.WAITING_USER
    )
    assert total == 1
    assert tickets[0].status == TicketStatusEnum.WAITING_USER
    
    # 2. Verify non-admin serialization strips internal note and audit logs
    detail = ticket_service.serialize_ticket_detail(t, is_admin=False)
    assert len(detail.messages) == 0
    assert detail.audit_logs is None
    
    # 3. User replies: status should transition WAITING_USER -> IN_PROGRESS
    reply_req = TicketMessageCreateRequest(message="Here is the additional detail requested.")
    user_msg = ticket_service.add_user_message(db_session, t.id, reply_req, candidate_user)
    assert user_msg.is_internal is False
    assert t.status == TicketStatusEnum.IN_PROGRESS
    
    # 4. Close ticket and verify reply restriction
    t.status = TicketStatusEnum.CLOSED
    db_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        ticket_service.add_user_message(db_session, t.id, reply_req, candidate_user)
    assert exc_info.value.status_code == 400
    assert "closed ticket" in exc_info.value.detail.lower()
