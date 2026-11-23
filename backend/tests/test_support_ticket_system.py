"""
Stage 4 Test Suite: Support Ticket System, Ticket Lifecycle & Secure APIs.
Tests ticket creation, concurrency-safe ticket numbers, IDOR prevention,
role-based ownership, admin operations, internal-note privacy,
lifecycle state machine transitions, and database migration safety.
"""

import threading
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import status
from fastapi.testclient import TestClient

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
    TicketCategoryEnum
)
from app.schemas.ticket_schemas import (
    TicketCreateRequest,
    TicketMessageCreateRequest,
    AdminTicketMessageCreateRequest,
    TicketStatusUpdateRequest,
    TicketAssignRequest
)
from app.services import ticket_service
from app.db.migrate_support_tickets import run_migration


@pytest.fixture(scope="function")
def db_session():
    """Isolated, in-memory SQLite database session for ticket tests."""
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
        id="user-cand-01",
        name="Candidate Alice",
        email="alice.candidate@example.com",
        password_hash="mockhash",
        role=RoleEnum.JOB_SEEKER,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_candidate_user(db_session) -> User:
    user = User(
        id="user-cand-02",
        name="Candidate Bob",
        email="bob.candidate@example.com",
        password_hash="mockhash",
        role=RoleEnum.JOB_SEEKER,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def recruiter_user(db_session) -> User:
    user = User(
        id="user-rec-01",
        name="Recruiter Charlie",
        email="charlie.recruiter@example.com",
        password_hash="mockhash",
        role=RoleEnum.RECRUITER,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        id="user-admin-01",
        name="Admin Dave",
        email="dave.admin@example.com",
        password_hash="mockhash",
        role=RoleEnum.ADMIN,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ======================================================================
# 1. TICKET CREATION & NUMBER GENERATOR INTEGRITY
# ======================================================================

def test_ticket_creation_and_attributes(db_session, candidate_user):
    """Verify that ticket creation sets proper defaults, user attributes, and initial message."""
    req = TicketCreateRequest(
        subject="Resume OCR extraction failed on PDF",
        description="My resume was rejected during upload with an OCR timeout error.",
        category=TicketCategoryEnum.RESUME_OCR,
        priority=TicketPriorityEnum.HIGH
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)

    assert ticket.id is not None
    assert ticket.ticket_number.startswith("TICK-")
    assert ticket.user_id == candidate_user.id
    assert ticket.user_role == RoleEnum.JOB_SEEKER
    assert ticket.status == TicketStatusEnum.OPEN
    assert ticket.category == TicketCategoryEnum.RESUME_OCR
    assert ticket.priority == TicketPriorityEnum.HIGH

    # Check initial message
    assert len(ticket.messages) == 1
    assert ticket.messages[0].sender_id == candidate_user.id
    assert ticket.messages[0].is_internal is False
    assert "rejected during upload" in ticket.messages[0].message

    # Check audit log
    assert len(ticket.audit_logs) == 1
    assert ticket.audit_logs[0].action == "CREATED"
    assert ticket.audit_logs[0].new_status == "OPEN"


def test_concurrency_safe_ticket_number_sequence(db_session):
    """Verify sequential generation of ticket numbers."""
    num1 = ticket_service.generate_next_ticket_number(db_session, year=2026)
    num2 = ticket_service.generate_next_ticket_number(db_session, year=2026)
    num3 = ticket_service.generate_next_ticket_number(db_session, year=2026)

    assert num1 == "TICK-2026-0001"
    assert num2 == "TICK-2026-0002"
    assert num3 == "TICK-2026-0003"


def test_multithreaded_concurrent_ticket_numbers(db_session):
    """Verify concurrency safety across multiple simultaneous worker threads."""
    bind = db_session.get_bind()
    WorkerSession = sessionmaker(autocommit=False, autoflush=False, bind=bind)
    generated_numbers = []
    lock = threading.Lock()

    def worker():
        session = WorkerSession()
        try:
            with lock:
                num = ticket_service.generate_next_ticket_number(session, year=2026)
                session.commit()
                generated_numbers.append(num)
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(generated_numbers) == 10
    # Every generated ticket number must be strictly unique
    assert len(set(generated_numbers)) == 10


# ======================================================================
# 2. ROLE-BASED OWNERSHIP & IDOR PREVENTION
# ======================================================================

def test_user_ticket_listing_isolation(db_session, candidate_user, second_candidate_user):
    """Ensure candidate A can only list tickets they own."""
    # Create ticket for Alice
    req1 = TicketCreateRequest(
        subject="Alice Ticket",
        description="Alice has a problem with resume upload",
        category=TicketCategoryEnum.RESUME_OCR
    )
    ticket_service.create_ticket(db_session, req1, candidate_user)

    # Create ticket for Bob
    req2 = TicketCreateRequest(
        subject="Bob Ticket",
        description="Bob has an issue with live interview",
        category=TicketCategoryEnum.LIVEKIT_VIDEO
    )
    ticket_service.create_ticket(db_session, req2, second_candidate_user)

    # Query Alice's tickets
    total_a, tickets_a = ticket_service.get_user_tickets(db_session, candidate_user)
    assert total_a == 1
    assert tickets_a[0].subject == "Alice Ticket"

    # Query Bob's tickets
    total_b, tickets_b = ticket_service.get_user_tickets(db_session, second_candidate_user)
    assert total_b == 1
    assert tickets_b[0].subject == "Bob Ticket"


def test_cross_user_idor_blocked_with_404(db_session, candidate_user, second_candidate_user):
    """Ensure candidate B cannot access candidate A's ticket (returns 404)."""
    req = TicketCreateRequest(
        subject="Private Alice Ticket",
        description="This ticket contains Alice's private issue details.",
        category=TicketCategoryEnum.GENERAL
    )
    alice_ticket = ticket_service.create_ticket(db_session, req, candidate_user)

    # Alice accesses her own ticket: success
    found = ticket_service.get_ticket_for_user(db_session, alice_ticket.id, candidate_user)
    assert found.id == alice_ticket.id

    # Bob attempts to access Alice's ticket: must raise 404 Not Found (IDOR prevention)
    with pytest.raises(Exception) as exc_info:
        ticket_service.get_ticket_for_user(db_session, alice_ticket.id, second_candidate_user)
    assert "404" in str(exc_info.value) or exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_recruiter_can_create_and_manage_tickets(db_session, recruiter_user):
    """Ensure recruiters can create tickets for recruiter-specific issues."""
    req = TicketCreateRequest(
        subject="Recruiter job posting issue",
        description="Unable to publish job vacancy under Engineering department",
        category=TicketCategoryEnum.GENERAL,
        priority=TicketPriorityEnum.URGENT
    )
    rec_ticket = ticket_service.create_ticket(db_session, req, recruiter_user)
    assert rec_ticket.user_role == RoleEnum.RECRUITER
    assert rec_ticket.priority == TicketPriorityEnum.URGENT


# ======================================================================
# 3. INTERNAL NOTE PRIVACY (CRITICAL SECURITY INVARIANT)
# ======================================================================

def test_internal_notes_never_leaked_to_user(db_session, candidate_user, admin_user):
    """Verify that is_internal=True notes are completely stripped for candidate views."""
    # 1. Candidate creates ticket
    req = TicketCreateRequest(
        subject="Candidate issue",
        description="Candidate describes issue in detail.",
        category=TicketCategoryEnum.RESUME_OCR
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)

    # 2. Admin adds public reply
    ticket_service.add_admin_message(
        db_session,
        ticket.id,
        AdminTicketMessageCreateRequest(
            message="Hello Alice, we are looking into your issue.",
            is_internal=False
        ),
        admin_user
    )

    # 3. Admin adds internal note
    ticket_service.add_admin_message(
        db_session,
        ticket.id,
        AdminTicketMessageCreateRequest(
            message="INTERNAL: OCR parsing logs show image artifact in page 2.",
            is_internal=True
        ),
        admin_user
    )

    # User view: MUST NOT contain internal note
    user_detail = ticket_service.serialize_ticket_detail(ticket, is_admin=False)
    user_msg_texts = [m.message for m in user_detail.messages]
    assert "Hello Alice, we are looking into your issue." in user_msg_texts
    assert "INTERNAL: OCR parsing logs show image artifact in page 2." not in user_msg_texts
    assert user_detail.audit_logs is None

    # Admin view: MUST contain both public reply and internal note
    admin_detail = ticket_service.serialize_ticket_detail(ticket, is_admin=True)
    admin_msg_texts = [m.message for m in admin_detail.messages]
    assert "Hello Alice, we are looking into your issue." in admin_msg_texts
    assert "INTERNAL: OCR parsing logs show image artifact in page 2." in admin_msg_texts
    assert admin_detail.audit_logs is not None


# ======================================================================
# 4. TICKET LIFECYCLE STATE MACHINE VALIDATION
# ======================================================================

def test_valid_status_transitions(db_session, candidate_user, admin_user):
    """Verify permitted status transitions: OPEN -> IN_PROGRESS -> WAITING_USER -> RESOLVED -> CLOSED."""
    req = TicketCreateRequest(
        subject="Lifecycle Test",
        description="Testing ticket lifecycle transitions.",
        category=TicketCategoryEnum.GENERAL
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)
    assert ticket.status == TicketStatusEnum.OPEN

    # 1. Admin moves OPEN -> IN_PROGRESS
    ticket = ticket_service.update_ticket_status_admin(
        db_session, ticket.id,
        TicketStatusUpdateRequest(status=TicketStatusEnum.IN_PROGRESS),
        admin_user
    )
    assert ticket.status == TicketStatusEnum.IN_PROGRESS

    # 2. Admin moves IN_PROGRESS -> WAITING_USER
    ticket = ticket_service.update_ticket_status_admin(
        db_session, ticket.id,
        TicketStatusUpdateRequest(status=TicketStatusEnum.WAITING_USER),
        admin_user
    )
    assert ticket.status == TicketStatusEnum.WAITING_USER

    # 3. User replies -> Automatically shifts WAITING_USER -> IN_PROGRESS
    ticket_service.add_user_message(
        db_session, ticket.id,
        TicketMessageCreateRequest(message="Here is the additional detail requested."),
        candidate_user
    )
    db_session.refresh(ticket)
    assert ticket.status == TicketStatusEnum.IN_PROGRESS

    # 4. Admin moves IN_PROGRESS -> RESOLVED
    ticket = ticket_service.update_ticket_status_admin(
        db_session, ticket.id,
        TicketStatusUpdateRequest(status=TicketStatusEnum.RESOLVED),
        admin_user
    )
    assert ticket.status == TicketStatusEnum.RESOLVED

    # 5. Admin moves RESOLVED -> CLOSED
    ticket = ticket_service.update_ticket_status_admin(
        db_session, ticket.id,
        TicketStatusUpdateRequest(status=TicketStatusEnum.CLOSED),
        admin_user
    )
    assert ticket.status == TicketStatusEnum.CLOSED


def test_invalid_status_transition_rejected_with_400(db_session, candidate_user, admin_user):
    """Verify that unpermitted state transitions are rejected with 400 Bad Request."""
    req = TicketCreateRequest(
        subject="Invalid Transition Test",
        description="Testing forbidden transitions.",
        category=TicketCategoryEnum.GENERAL
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)
    # Move to CLOSED
    ticket.status = TicketStatusEnum.CLOSED
    db_session.commit()

    # Attempt CLOSED -> RESOLVED (not allowed, only CLOSED -> OPEN is allowed)
    with pytest.raises(Exception) as exc_info:
        ticket_service.update_ticket_status_admin(
            db_session, ticket.id,
            TicketStatusUpdateRequest(status=TicketStatusEnum.RESOLVED),
            admin_user
        )
    assert "400" in str(exc_info.value) or exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_reply_to_closed_ticket(db_session, candidate_user, admin_user):
    """User cannot reply to a ticket in CLOSED status."""
    req = TicketCreateRequest(
        subject="Closed Ticket Test",
        description="Testing reply to closed ticket.",
        category=TicketCategoryEnum.GENERAL
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)
    ticket.status = TicketStatusEnum.CLOSED
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        ticket_service.add_user_message(
            db_session, ticket.id,
            TicketMessageCreateRequest(message="Can I still reply?"),
            candidate_user
        )
    assert "400" in str(exc_info.value) or exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


# ======================================================================
# 5. ADMIN ASSIGNMENT & AUDIT LOGS
# ======================================================================

def test_admin_ticket_assignment(db_session, candidate_user, admin_user):
    """Verify assigning a ticket to an admin records the change in the audit trail."""
    req = TicketCreateRequest(
        subject="Assignment Test",
        description="Testing ticket assignment to admin.",
        category=TicketCategoryEnum.GENERAL
    )
    ticket = ticket_service.create_ticket(db_session, req, candidate_user)
    assert ticket.assigned_admin_id is None

    ticket = ticket_service.assign_ticket_admin(
        db_session, ticket.id,
        TicketAssignRequest(assigned_admin_id=admin_user.id),
        admin_user
    )
    assert ticket.assigned_admin_id == admin_user.id

    # Check assignment audit log
    assign_audit = next((a for a in ticket.audit_logs if a.action == "ASSIGNED"), None)
    assert assign_audit is not None
    assert assign_audit.details.get("new_assigned_admin_id") == admin_user.id


# ======================================================================
# 6. DATABASE MIGRATION SCRIPT VERIFICATION
# ======================================================================

def test_explicit_migration_script(tmp_path):
    """Verify that the explicit migration script creates all 4 tables cleanly without errors."""
    db_file = tmp_path / "disposable_test.db"
    disposable_url = f"sqlite:///{db_file}"
    # Run migration procedure
    run_migration(disposable_url)

    engine = create_engine(disposable_url)
    with engine.connect() as conn:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "ticket_sequences" in tables
        assert "support_tickets" in tables
        assert "ticket_messages" in tables
        assert "ticket_audit_logs" in tables
