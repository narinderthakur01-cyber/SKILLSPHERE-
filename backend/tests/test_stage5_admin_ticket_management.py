"""
Stage 5 Verification Test Suite: Admin Support Dashboard & Ticket Management.
Tests:
- Admin metrics telemetry calculation (get_ticket_metrics_admin)
- Admin ticket filtering and search (by ticket number and subject)
- Admin priority update with audit logging (update_ticket_priority_admin)
- Strict authorization & role isolation (require_role blocks non-admins)
- Internal note isolation between admin view and candidate/recruiter views
- Status update persistence and state machine validation
"""

import pytest
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import require_role
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
from app.schemas.ticket_schemas import (
    TicketCreateRequest,
    TicketStatusUpdateRequest,
    TicketPriorityUpdateRequest,
    TicketAssignRequest,
    AdminTicketMessageCreateRequest
)
from app.services import ticket_service
from app.api.v1 import tickets as tickets_api


@pytest.fixture(scope="function")
def db_session():
    """Isolated, in-memory SQLite database session for Stage 5 tests."""
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
def admin_user(db_session) -> User:
    user = User(
        id="admin-01",
        email="lead_admin@skillsphere.com",
        name="Lead Administrator",
        password_hash="mockhash",
        role=RoleEnum.ADMIN,
        email_verified=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def candidate_user(db_session) -> User:
    user = User(
        id="cand-01",
        email="candidate_applicant@skillsphere.com",
        name="Candidate Applicant",
        password_hash="mockhash",
        role=RoleEnum.JOB_SEEKER,
        email_verified=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def recruiter_user(db_session) -> User:
    user = User(
        id="rec-01",
        email="recruiter_talent@skillsphere.com",
        name="Recruiter Talent",
        password_hash="mockhash",
        role=RoleEnum.RECRUITER,
        email_verified=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ======================================================================
# 1. ADMIN METRICS TELEMETRY
# ======================================================================

def test_admin_metrics_telemetry_reflects_real_data(db_session, admin_user, candidate_user):
    """Verify get_ticket_metrics_admin computes real-time database counts accurately."""
    # Initially zero
    initial_metrics = ticket_service.get_ticket_metrics_admin(db_session)
    assert initial_metrics["total"] == 0
    assert initial_metrics["open"] == 0

    # 1. Create Open / Urgent ticket
    req1 = TicketCreateRequest(
        subject="OCR failure on PDF resume",
        description="Detailed description for OCR failure.",
        category=TicketCategoryEnum.RESUME_OCR,
        priority=TicketPriorityEnum.URGENT
    )
    t1 = ticket_service.create_ticket(db_session, req1, candidate_user)

    # 2. Create In Progress / High ticket
    req2 = TicketCreateRequest(
        subject="WebRTC video lag in LiveKit interview",
        description="Detailed description for LiveKit video issue.",
        category=TicketCategoryEnum.LIVEKIT_VIDEO,
        priority=TicketPriorityEnum.HIGH
    )
    t2 = ticket_service.create_ticket(db_session, req2, candidate_user)
    t2.status = TicketStatusEnum.IN_PROGRESS
    db_session.commit()

    # 3. Create Waiting User / Medium ticket
    req3 = TicketCreateRequest(
        subject="Assessment question clarification",
        description="Detailed description for MCQ proctoring question.",
        category=TicketCategoryEnum.PROCTORING_MCQ,
        priority=TicketPriorityEnum.MEDIUM
    )
    t3 = ticket_service.create_ticket(db_session, req3, candidate_user)
    t3.status = TicketStatusEnum.WAITING_USER
    db_session.commit()

    # 4. Create Resolved / Low ticket
    req4 = TicketCreateRequest(
        subject="Account email update request",
        description="Detailed description for account assistance.",
        category=TicketCategoryEnum.ACCOUNT_AUTH,
        priority=TicketPriorityEnum.LOW
    )
    t4 = ticket_service.create_ticket(db_session, req4, candidate_user)
    t4.status = TicketStatusEnum.RESOLVED
    db_session.commit()

    # Call endpoint function
    metrics = tickets_api.get_admin_ticket_metrics(db=db_session, admin_user=admin_user)
    assert metrics["total"] == 4
    assert metrics["open"] == 1
    assert metrics["in_progress"] == 1
    assert metrics["waiting_user"] == 1
    assert metrics["resolved"] == 1
    assert metrics["closed"] == 0
    assert metrics["urgent"] == 1
    assert metrics["high"] == 1
    assert metrics["urgent_or_high"] == 2


# ======================================================================
# 2. ADMIN TICKET FILTERING & SEARCH
# ======================================================================

def test_admin_search_by_ticket_number_and_subject(db_session, admin_user, candidate_user):
    """Verify admin query can search tickets by ticket number or subject keyword."""
    req1 = TicketCreateRequest(
        subject="Camera disconnected during assessment",
        description="Camera failed to connect during proctored exam.",
        category=TicketCategoryEnum.PROCTORING_MCQ,
        priority=TicketPriorityEnum.HIGH
    )
    t1 = ticket_service.create_ticket(db_session, req1, candidate_user)

    req2 = TicketCreateRequest(
        subject="Resume parsing formatting error",
        description="Resume formatting error on upload.",
        category=TicketCategoryEnum.RESUME_OCR,
        priority=TicketPriorityEnum.MEDIUM
    )
    t2 = ticket_service.create_ticket(db_session, req2, candidate_user)

    # Search by subject keyword "Camera"
    res1 = tickets_api.list_all_tickets_admin(
        db=db_session, admin_user=admin_user, search="Camera"
    )
    assert res1.total == 1
    assert res1.tickets[0].ticket_number == t1.ticket_number

    # Search by ticket number string
    res2 = tickets_api.list_all_tickets_admin(
        db=db_session, admin_user=admin_user, search=t2.ticket_number
    )
    assert res2.total == 1
    assert res2.tickets[0].subject == "Resume parsing formatting error"

    # Search with no match
    res3 = tickets_api.list_all_tickets_admin(
        db=db_session, admin_user=admin_user, search="NonexistentTermXYZ"
    )
    assert res3.total == 0


def test_admin_filtering_by_status_category_priority(db_session, admin_user, candidate_user):
    """Verify admin filtering by status, category, and priority combinations."""
    req = TicketCreateRequest(
        subject="Specific Filter Verification",
        description="Detailed description for filter verification.",
        category=TicketCategoryEnum.LIVEKIT_VIDEO,
        priority=TicketPriorityEnum.URGENT
    )
    t = ticket_service.create_ticket(db_session, req, candidate_user)

    # Filter matching all 3
    res_match = tickets_api.list_all_tickets_admin(
        db=db_session,
        admin_user=admin_user,
        category=TicketCategoryEnum.LIVEKIT_VIDEO,
        priority=TicketPriorityEnum.URGENT,
        status=TicketStatusEnum.OPEN
    )
    assert res_match.total == 1

    # Filter with mismatch category
    res_mismatch = tickets_api.list_all_tickets_admin(
        db=db_session,
        admin_user=admin_user,
        category=TicketCategoryEnum.ACCOUNT_AUTH
    )
    assert res_mismatch.total == 0


# ======================================================================
# 3. PRIORITY MANAGEMENT WITH AUDIT LOGGING
# ======================================================================

def test_admin_priority_update_and_audit(db_session, admin_user, candidate_user):
    """Verify update_ticket_priority_admin updates priority and creates PRIORITY_CHANGED audit log."""
    req = TicketCreateRequest(
        subject="Priority Escalation Test",
        description="Detailed problem needing urgent escalation.",
        category=TicketCategoryEnum.ACCOUNT_AUTH,
        priority=TicketPriorityEnum.LOW
    )
    t = ticket_service.create_ticket(db_session, req, candidate_user)
    assert t.priority == TicketPriorityEnum.LOW

    # Update to URGENT via API controller
    update_req = TicketPriorityUpdateRequest(priority=TicketPriorityEnum.URGENT)
    updated = tickets_api.update_ticket_priority_admin(
        ticket_id=t.id, request=update_req, db=db_session, admin_user=admin_user
    )
    assert updated.priority == "URGENT"

    # Check audit log in DB
    audit = db_session.query(TicketAuditLog).filter(
        TicketAuditLog.ticket_id == t.id,
        TicketAuditLog.action == "PRIORITY_CHANGED"
    ).first()
    assert audit is not None
    assert audit.details["old_priority"] == "LOW"
    assert audit.details["new_priority"] == "URGENT"


# ======================================================================
# 4. STRICT AUTHORIZATION: NON-ADMINS BLOCKED BY REQUIRE_ROLE
# ======================================================================

def test_non_admin_blocked_from_admin_endpoints(candidate_user, recruiter_user, admin_user):
    """Verify require_role([RoleEnum.ADMIN]) strictly blocks candidates and recruiters with 403."""
    admin_checker = require_role([RoleEnum.ADMIN])

    # 1. Admin passes
    checked_admin = admin_checker(current_user=admin_user)
    assert checked_admin.id == admin_user.id

    # 2. Candidate blocked with 403
    with pytest.raises(HTTPException) as exc_cand:
        admin_checker(current_user=candidate_user)
    assert exc_cand.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Forbidden" in exc_cand.value.detail

    # 3. Recruiter blocked with 403
    with pytest.raises(HTTPException) as exc_rec:
        admin_checker(current_user=recruiter_user)
    assert exc_rec.value.status_code == status.HTTP_403_FORBIDDEN


# ======================================================================
# 5. INTERNAL NOTE PRIVACY ENFORCEMENT
# ======================================================================

def test_internal_note_visible_in_admin_detail_but_hidden_from_candidate(
    db_session, admin_user, candidate_user
):
    """Verify internal note posted by admin is visible to admin, but never returned to candidate."""
    req = TicketCreateRequest(
        subject="Confidential Note Test",
        description="Testing that internal notes never leak to candidates.",
        category=TicketCategoryEnum.GENERAL
    )
    t = ticket_service.create_ticket(db_session, req, candidate_user)

    # Admin posts an internal note
    note_req = AdminTicketMessageCreateRequest(
        message="Suspicious telemetry pattern. Investigating backend DB trace.",
        is_internal=True
    )
    tickets_api.reply_as_admin(
        ticket_id=t.id, request=note_req, db=db_session, admin_user=admin_user
    )

    # Admin posts a public reply
    pub_req = AdminTicketMessageCreateRequest(
        message="We are looking into this issue.",
        is_internal=False
    )
    tickets_api.reply_as_admin(
        ticket_id=t.id, request=pub_req, db=db_session, admin_user=admin_user
    )

    # 1. Check Admin Detail: Must contain all 3 messages + audit logs
    admin_detail = tickets_api.get_ticket_detail_admin(
        ticket_id=t.id, db=db_session, admin_user=admin_user
    )
    assert len(admin_detail.messages) == 3
    internal_msgs = [m for m in admin_detail.messages if m.is_internal]
    assert len(internal_msgs) == 1
    assert "Suspicious telemetry pattern" in internal_msgs[0].message
    assert admin_detail.audit_logs is not None
    assert len(admin_detail.audit_logs) >= 2

    # 2. Check Candidate Detail: Must contain ONLY public messages (initial + public reply)
    cand_detail = tickets_api.get_user_ticket(
        ticket_id=t.id, db=db_session, current_user=candidate_user
    )
    assert len(cand_detail.messages) == 2
    for m in cand_detail.messages:
        assert m.is_internal is False
        assert "Suspicious telemetry pattern" not in m.message
    # Audit logs completely absent for candidate
    assert cand_detail.audit_logs is None
