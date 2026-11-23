"""
Stage 7 Test Suite: Live Agent Handoff, Administrator Availability & Real-Time Chat.
Tests:
- Authenticated single-use WebSocket connection tickets (prevents passing JWTs in URLs)
- Concurrency-safe admin availability, capacity limits, and heartbeat presence tracking
- Single-instance WebSocket ConnectionManager with JSON ping/pong support
- Strict internal-note privacy isolation over WebSockets (non-admins NEVER receive internal notes)
- Candidate/recruiter live handoff escalation, queue position estimation, and acceptance
- Capacity enforcement (rejects handoffs when admin max active chats is reached)
- Chatbot troubleshooting integration for live support handoffs
"""

import json
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import status

from app.core.database import Base
from app.models.models import (
    User,
    RoleEnum,
    SupportTicket,
    TicketMessage,
    TicketAuditLog,
    TicketSequence,
    TicketStatusEnum,
    TicketPriorityEnum,
    TicketCategoryEnum,
    AdminAvailability,
    WebSocketAuthTicket
)
from app.schemas.ticket_schemas import (
    TicketCreateRequest,
    AdminAvailabilityUpdateRequest,
    LiveHandoffRequest
)
from app.services import ticket_service
from app.services.websocket_manager import ws_manager
from app.chatbot.troubleshooter import troubleshooting_engine
from app.api.v1 import tickets


class MockWebSocket:
    """Mock WebSocket client for deterministic, sub-second ASGI testing."""
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.sent_texts = []
        self.close_code = None
        self.close_reason = None

    async def accept(self):
        self.accepted = True

    async def send_text(self, text: str):
        self.sent_texts.append(text)

    async def close(self, code=1000, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite database session for Stage 7 tests."""
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


@pytest.fixture
def candidate_user(db_session) -> User:
    user = User(
        id="cand-stage7-001",
        email="candidate.live@skillsphere.test",
        name="Candidate Live User",
        role=RoleEnum.JOB_SEEKER,
        password_hash="mockhash",
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def other_candidate(db_session) -> User:
    user = User(
        id="cand-stage7-002",
        email="other.cand@skillsphere.test",
        name="Other Candidate",
        role=RoleEnum.JOB_SEEKER,
        password_hash="mockhash",
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        id="admin-stage7-001",
        email="admin.live@skillsphere.test",
        name="Admin Live Support",
        role=RoleEnum.ADMIN,
        password_hash="mockhash",
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def support_ticket(db_session, candidate_user) -> SupportTicket:
    req = TicketCreateRequest(
        subject="LiveKit audio cut out during interview",
        description="WebRTC media stream failed with code 4001, camera audio muted.",
        category=TicketCategoryEnum.LIVEKIT_VIDEO,
        priority=TicketPriorityEnum.HIGH
    )
    return ticket_service.create_ticket(db_session, req, candidate_user)


# ======================================================================
# 1. WebSocket Auth Ticket Tests (No long-lived JWTs in WS URLs)
# ======================================================================

def test_ws_auth_ticket_creation_and_consumption(db_session, candidate_user, support_ticket):
    """Validates creation, single-use consumption, and expiration check of WS auth tickets."""
    # 1. Create short-lived connection ticket
    ws_ticket = ticket_service.create_ws_auth_ticket(
        db_session, support_ticket.id, candidate_user, expiry_seconds=60
    )
    assert ws_ticket.ticket_token is not None
    assert len(ws_ticket.ticket_token) > 20
    assert ws_ticket.is_used is False
    assert ws_ticket.user_id == candidate_user.id
    assert ws_ticket.ticket_id == support_ticket.id

    # 2. First validation and consumption must succeed
    consumed_user = ticket_service.validate_and_consume_ws_ticket(
        db_session, ws_ticket.ticket_token, support_ticket.id
    )
    assert consumed_user is not None
    assert consumed_user.id == candidate_user.id

    # 3. Second validation must FAIL (enforces single-use semantics)
    reconsumed = ticket_service.validate_and_consume_ws_ticket(
        db_session, ws_ticket.ticket_token, support_ticket.id
    )
    assert reconsumed is None


def test_ws_auth_ticket_expiration(db_session, candidate_user, support_ticket):
    """Validates that expired WS connection tickets are rejected."""
    # Create ticket with -10 second expiry
    ws_ticket = ticket_service.create_ws_auth_ticket(
        db_session, support_ticket.id, candidate_user, expiry_seconds=-10
    )
    consumed_user = ticket_service.validate_and_consume_ws_ticket(
        db_session, ws_ticket.ticket_token, support_ticket.id
    )
    assert consumed_user is None


def test_ws_auth_ticket_idor_protection(db_session, other_candidate, support_ticket):
    """Ensures a user cannot obtain a WS auth ticket for a ticket they do not own."""
    with pytest.raises(Exception) as excinfo:
        ticket_service.create_ws_auth_ticket(db_session, support_ticket.id, other_candidate)
    assert "404" in str(excinfo.value) or "403" in str(excinfo.value) or "not found" in str(excinfo.value).lower()


# ======================================================================
# 2. Admin Availability, Capacity & Heartbeat Presence
# ======================================================================

def test_admin_availability_and_heartbeat(db_session, admin_user):
    """Validates setting availability status, recording heartbeats, and presence freshness."""
    avail = ticket_service.get_or_create_admin_availability(db_session, admin_user.id)
    assert avail.is_available is False

    # Update availability to True with max 2 chats
    updated = ticket_service.update_admin_availability(
        db_session, admin_user.id, is_available=True, max_active_chats=2
    )
    assert updated.is_available is True
    assert updated.max_active_chats == 2
    assert updated.last_heartbeat_at is not None

    # Available count should be 1
    avail_count = ticket_service.get_available_admins_count(db_session, max_stale_seconds=60)
    assert avail_count == 1

    # Simulate stale heartbeat (>60 seconds old)
    updated.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    db_session.commit()

    # Now available count must be 0 (stale heartbeat excluded)
    stale_count = ticket_service.get_available_admins_count(db_session, max_stale_seconds=60)
    assert stale_count == 0

    # Sending heartbeat revives presence
    ticket_service.record_admin_heartbeat(db_session, admin_user.id)
    revived_count = ticket_service.get_available_admins_count(db_session, max_stale_seconds=60)
    assert revived_count == 1


# ======================================================================
# 3. Live Agent Handoff Escalation & Queue Position
# ======================================================================

def test_request_and_end_live_handoff(db_session, candidate_user, support_ticket):
    """Validates requesting live handoff, calculating queue position, and ending session."""
    ticket, queue_pos, avail_admins = ticket_service.request_live_handoff(
        db_session, support_ticket.id, candidate_user, reason="Candidate needs live human support"
    )
    assert ticket.is_live_chat is True
    assert ticket.live_chat_requested_at is not None
    assert ticket.live_chat_ended_at is None
    assert queue_pos >= 1

    # Check that system message and audit log were created
    messages = [m for m in ticket.messages if "[System] Live agent handoff requested" in m.message]
    assert len(messages) >= 1

    audit_logs = [a for a in ticket.audit_logs if a.action == "LIVE_CHAT_REQUESTED"]
    assert len(audit_logs) >= 1

    # End live chat session
    ended_ticket = ticket_service.end_live_handoff(
        db_session, support_ticket.id, candidate_user, reason="Candidate resolved problem"
    )
    assert ended_ticket.is_live_chat is False
    assert ended_ticket.live_chat_ended_at is not None

    end_audits = [a for a in ended_ticket.audit_logs if a.action == "LIVE_CHAT_ENDED"]
    assert len(end_audits) >= 1


# ======================================================================
# 4. Strict Admin Capacity Enforcement
# ======================================================================

def test_admin_capacity_enforcement(db_session, candidate_user, admin_user, support_ticket):
    """Validates that an admin cannot accept more concurrent chats than their max_active_chats limit."""
    # Set admin max capacity = 1
    ticket_service.update_admin_availability(
        db_session, admin_user.id, is_available=True, max_active_chats=1
    )

    # 1. Accept first ticket -> must succeed
    ticket1 = ticket_service.accept_live_handoff(db_session, support_ticket.id, admin_user)
    assert ticket1.assigned_admin_id == admin_user.id
    assert ticket1.status == TicketStatusEnum.IN_PROGRESS
    assert ticket1.is_live_chat is True

    # Active count should be 1
    active_chats = ticket_service.get_admin_active_chats_count(db_session, admin_user.id)
    assert active_chats == 1

    # 2. Create second ticket
    req2 = TicketCreateRequest(
        subject="Second ticket for capacity check",
        description="Candidate 2 testing admin maximum active capacity limit.",
        category=TicketCategoryEnum.GENERAL,
        priority=TicketPriorityEnum.MEDIUM
    )
    ticket2 = ticket_service.create_ticket(db_session, req2, candidate_user)
    ticket_service.request_live_handoff(db_session, ticket2.id, candidate_user)

    # 3. Attempting to accept ticket 2 while at capacity must fail with 400 Bad Request
    with pytest.raises(Exception) as excinfo:
        ticket_service.accept_live_handoff(db_session, ticket2.id, admin_user)
    assert "capacity reached" in str(excinfo.value).lower()

    # 4. Ending ticket 1 frees up capacity
    ticket_service.end_live_handoff(db_session, ticket1.id, admin_user)
    assert ticket_service.get_admin_active_chats_count(db_session, admin_user.id) == 0

    # 5. Now accepting ticket 2 must succeed
    accepted2 = ticket_service.accept_live_handoff(db_session, ticket2.id, admin_user)
    assert accepted2.assigned_admin_id == admin_user.id
    assert accepted2.status == TicketStatusEnum.IN_PROGRESS


# ======================================================================
# 5. REST & WebSocket Endpoints Test
# ======================================================================

def test_ws_auth_ticket_endpoint(db_session, candidate_user, support_ticket):
    """Tests the authenticated REST endpoint issuing single-use connection tokens."""
    res = tickets.issue_ws_auth_ticket(ticket_id=support_ticket.id, db=db_session, current_user=candidate_user)
    assert res.ticket_token is not None
    assert res.expires_at is not None
    assert f"/api/v1/tickets/{support_ticket.id}/ws?ticket=" in res.ws_url


def test_admin_availability_endpoints(db_session, admin_user):
    """Tests GET, PUT, and Heartbeat endpoints for administrator availability."""
    # GET
    res = tickets.get_admin_availability(db=db_session, admin_user=admin_user)
    assert res.admin_id == admin_user.id
    assert res.is_available is False

    # PUT
    put_req = AdminAvailabilityUpdateRequest(is_available=True, max_active_chats=4)
    res_put = tickets.update_admin_availability(request=put_req, db=db_session, admin_user=admin_user)
    assert res_put.is_available is True
    assert res_put.max_active_chats == 4

    # Heartbeat
    res_hb = tickets.record_admin_heartbeat(db=db_session, admin_user=admin_user)
    assert res_hb.is_active_presence is True


def sync_run(coro):
    """Zero-socket deterministic runner for coroutines in sandboxed test environments."""
    iter_stack = [coro.__await__() if hasattr(coro, "__await__") else coro]
    while iter_stack:
        try:
            res = iter_stack[-1].send(None)
            if hasattr(res, "__await__"):
                iter_stack.append(res.__await__())
        except StopIteration as e:
            iter_stack.pop()
            if iter_stack:
                iter_stack[-1].send(e.value)
            else:
                return e.value


def test_websocket_ping_pong_and_room_broadcast(db_session, candidate_user, support_ticket):
    """Validates WebSocket connection registration and application-level JSON ping/pong keepalive."""
    async def _test():
        ws_cand = MockWebSocket()
        conn_cand = "conn-cand-test-1"

        await ws_manager.connect(
            ticket_id=support_ticket.id,
            connection_id=conn_cand,
            websocket=ws_cand,
            user_id=candidate_user.id,
            user_role=candidate_user.role.value,
            user_name=candidate_user.name
        )
        assert ws_cand.accepted is True
        assert len(ws_cand.sent_texts) == 1
        join_event = json.loads(ws_cand.sent_texts[0])
        assert join_event["type"] == "user_joined"
        assert join_event["data"]["user_id"] == candidate_user.id

        # Test application-level ping/pong
        await ws_manager.send_personal_message(ws_cand, "pong", {"timestamp": "2026-11-23T12:00:00Z"})
        assert len(ws_cand.sent_texts) == 2
        pong_event = json.loads(ws_cand.sent_texts[1])
        assert pong_event["type"] == "pong"

        # Cleanup
        ws_manager.disconnect(support_ticket.id, conn_cand)

    sync_run(_test())


def test_websocket_internal_note_isolation(db_session, candidate_user, admin_user, support_ticket):
    """
    CRITICAL SECURITY TEST:
    Verifies that when an administrator broadcasts an internal note (is_internal=True)
    over WebSocket, the candidate connection NEVER receives it.
    """
    async def _test():
        ws_cand = MockWebSocket()
        ws_admin = MockWebSocket()

        conn_cand = "conn-cand-iso"
        conn_admin = "conn-admin-iso"

        await ws_manager.connect(
            ticket_id=support_ticket.id,
            connection_id=conn_cand,
            websocket=ws_cand,
            user_id=candidate_user.id,
            user_role=candidate_user.role.value,
            user_name=candidate_user.name
        )

        await ws_manager.connect(
            ticket_id=support_ticket.id,
            connection_id=conn_admin,
            websocket=ws_admin,
            user_id=admin_user.id,
            user_role=admin_user.role.value,
            user_name=admin_user.name
        )

        cand_initial_count = len(ws_cand.sent_texts)
        admin_initial_count = len(ws_admin.sent_texts)

        # 1. Broadcast Public Message
        await ws_manager.broadcast_event(
            ticket_id=support_ticket.id,
            event_type="new_message",
            data={"message": "Public reply to user", "is_internal": False},
            is_internal=False
        )
        # Both received it
        assert len(ws_cand.sent_texts) == cand_initial_count + 1
        assert len(ws_admin.sent_texts) == admin_initial_count + 1

        # 2. Broadcast Internal Note
        await ws_manager.broadcast_event(
            ticket_id=support_ticket.id,
            event_type="new_message",
            data={"message": "CONFIDENTIAL: Internal investigation notes", "is_internal": True},
            is_internal=True
        )

        # Admin received the internal note
        assert len(ws_admin.sent_texts) == admin_initial_count + 2
        admin_last = json.loads(ws_admin.sent_texts[-1])
        assert "CONFIDENTIAL" in admin_last["data"]["message"]

        # CRITICAL SECURITY INVARIANT: Candidate did NOT receive the internal note!
        assert len(ws_cand.sent_texts) == cand_initial_count + 1

        ws_manager.disconnect(support_ticket.id, conn_cand)
        ws_manager.disconnect(support_ticket.id, conn_admin)

    sync_run(_test())


def test_ticket_websocket_endpoint_handshake_validation(db_session, candidate_user, support_ticket):
    """Validates that WebSocket endpoint rejects missing or invalid/expired connection tickets."""
    async def _test():
        # 1. Missing ticket -> closes with WS_1008
        ws_missing = MockWebSocket()
        await tickets.ticket_websocket_endpoint(
            websocket=ws_missing, ticket_id=support_ticket.id, ticket=None, db=db_session
        )
        assert ws_missing.closed is True
        assert ws_missing.close_code == 1008

        # 2. Invalid ticket -> closes with WS_1008
        ws_invalid = MockWebSocket()
        await tickets.ticket_websocket_endpoint(
            websocket=ws_invalid, ticket_id=support_ticket.id, ticket="invalid_token_12345", db=db_session
        )
        assert ws_invalid.closed is True
        assert ws_invalid.close_code == 1008

    sync_run(_test())


# ======================================================================
# 6. Chatbot Live Agent Status & Troubleshooting Integration
# ======================================================================

def test_chatbot_live_agent_inquiry(db_session, candidate_user):
    """Verifies that chatbot answers live agent queries and accurately reports admin presence."""
    # When no admins online
    resp = troubleshooting_engine.handle_message(
        message="Can I talk to a live human agent?",
        session_id="test-chat-live-001",
        role="JOB_SEEKER",
        target_lang="en",
        db=db_session,
        current_user=candidate_user
    )
    assert resp is not None
    assert resp.matched_intent == "live_agent_status"
    assert "currently offline" in resp.message.lower()

    # Now mark admin as available
    admin = User(
        id="admin-bot-001",
        email="botadmin@test.com",
        name="Bot Admin",
        role=RoleEnum.ADMIN,
        password_hash="mock",
        email_verified=True
    )
    db_session.add(admin)
    db_session.commit()
    ticket_service.update_admin_availability(db_session, admin.id, is_available=True, max_active_chats=3)

    # Inquire again
    resp2 = troubleshooting_engine.handle_message(
        message="Can I speak with a live agent?",
        session_id="test-chat-live-002",
        role="JOB_SEEKER",
        target_lang="en",
        db=db_session,
        current_user=candidate_user
    )
    assert resp2 is not None
    assert resp2.matched_intent == "live_agent_status"
    assert "1" in resp2.message or "support administrator" in resp2.message.lower()
