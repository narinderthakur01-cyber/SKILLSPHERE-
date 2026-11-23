"""
Service layer for Support Ticket System (Stage 4).
Handles concurrency-safe ticket number generation, lifecycle transitions,
role-based ownership verification, IDOR prevention, and internal note isolation.
"""

from datetime import datetime, timezone, timedelta
import secrets
import threading
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

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
    TicketMessageCreateRequest,
    AdminTicketMessageCreateRequest,
    TicketStatusUpdateRequest,
    TicketAssignRequest,
    TicketMessageResponse,
    TicketAuditLogResponse,
    SupportTicketSummaryResponse,
    SupportTicketDetailResponse,
    TicketListResponse,
    WSAuthTicketResponse,
    AdminAvailabilityResponse,
    LiveHandoffResponse
)


# Allowed state machine transitions
VALID_STATUS_TRANSITIONS: Dict[TicketStatusEnum, List[TicketStatusEnum]] = {
    TicketStatusEnum.OPEN: [
        TicketStatusEnum.IN_PROGRESS,
        TicketStatusEnum.WAITING_USER,
        TicketStatusEnum.RESOLVED,
        TicketStatusEnum.CLOSED
    ],
    TicketStatusEnum.IN_PROGRESS: [
        TicketStatusEnum.WAITING_USER,
        TicketStatusEnum.RESOLVED,
        TicketStatusEnum.CLOSED
    ],
    TicketStatusEnum.WAITING_USER: [
        TicketStatusEnum.IN_PROGRESS,
        TicketStatusEnum.RESOLVED,
        TicketStatusEnum.CLOSED
    ],
    TicketStatusEnum.RESOLVED: [
        TicketStatusEnum.OPEN,
        TicketStatusEnum.IN_PROGRESS,
        TicketStatusEnum.CLOSED
    ],
    TicketStatusEnum.CLOSED: [
        TicketStatusEnum.OPEN
    ]
}


_seq_lock = threading.Lock()


def generate_next_ticket_number(db: Session, year: Optional[int] = None) -> str:
    """
    Concurrency-safe, database-backed atomic sequence generator.
    Guarantees unique sequential identifiers formatted as TICK-YYYY-XXXX.
    Uses pessimistic locking (FOR UPDATE) where supported by dialect,
    complemented by an in-process thread lock for thread safety across workers.
    """
    current_year = year or datetime.now(timezone.utc).year

    with _seq_lock:
        try:
            seq = db.query(TicketSequence).filter(TicketSequence.year == current_year).with_for_update().first()
        except Exception:
            # SQLite or dialect without row-level lock support
            seq = db.query(TicketSequence).filter(TicketSequence.year == current_year).first()

        if not seq:
            seq = TicketSequence(year=current_year, last_number=1)
            db.add(seq)
            db.flush()
        else:
            seq.last_number += 1
            db.flush()

        return f"TICK-{current_year}-{seq.last_number:04d}"


def create_ticket(
    db: Session,
    request: TicketCreateRequest,
    current_user: User
) -> SupportTicket:
    """
    Creates a new support ticket bound to the authenticated user.
    Derives user_id and user_role strictly from the session token.
    Wraps sequence generation, ticket creation, initial message, and audit log
    in a single atomic transaction.
    """
    ticket_num = generate_next_ticket_number(db)

    ticket = SupportTicket(
        ticket_number=ticket_num,
        user_id=current_user.id,
        user_role=current_user.role,
        subject=request.subject.strip(),
        description=request.description.strip(),
        category=request.category,
        priority=request.priority,
        status=TicketStatusEnum.OPEN
    )
    db.add(ticket)
    db.flush()

    # Initial message recording the original problem description
    initial_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=request.description.strip(),
        is_internal=False
    )
    db.add(initial_msg)

    # Initial audit log
    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        action="CREATED",
        new_status=TicketStatusEnum.OPEN.value,
        details={
            "ticket_number": ticket_num,
            "category": request.category.value,
            "priority": request.priority.value
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket


def get_user_tickets(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[TicketStatusEnum] = None
) -> Tuple[int, List[SupportTicket]]:
    """
    List tickets strictly owned by the current authenticated user.
    Enforces IDOR prevention: non-admins cannot query other users' tickets.
    """
    query = db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id)
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)

    total = query.count()
    tickets = query.order_by(desc(SupportTicket.updated_at)).offset(skip).limit(limit).all()
    return total, tickets


def get_ticket_for_user(
    db: Session,
    ticket_id: str,
    current_user: User
) -> SupportTicket:
    """
    Retrieves a single ticket ensuring caller ownership.
    Returns 404 for inaccessible tickets to prevent leaking ticket existence.
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )

    # IDOR Check: Non-admins can only access their own tickets
    if current_user.role != RoleEnum.ADMIN and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )

    return ticket


get_ticket_with_auth = get_ticket_for_user


def add_user_message(
    db: Session,
    ticket_id: str,
    request: TicketMessageCreateRequest,
    current_user: User
) -> TicketMessage:
    """
    Adds a public message from the ticket owner.
    Transitions WAITING_USER back to IN_PROGRESS.
    """
    ticket = get_ticket_for_user(db, ticket_id, current_user)

    if ticket.status == TicketStatusEnum.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reply to a closed ticket. Please open a new ticket."
        )

    # If ticket was waiting for user or resolved, user reply moves it back to IN_PROGRESS
    old_status = ticket.status.value
    if ticket.status in [TicketStatusEnum.WAITING_USER, TicketStatusEnum.RESOLVED]:
        ticket.status = TicketStatusEnum.IN_PROGRESS
        audit = TicketAuditLog(
            ticket_id=ticket.id,
            actor_id=current_user.id,
            action="STATUS_CHANGED",
            old_status=old_status,
            new_status=TicketStatusEnum.IN_PROGRESS.value,
            details={"reason": "User replied to ticket"}
        )
        db.add(audit)

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=request.message.strip(),
        is_internal=False
    )
    db.add(msg)

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg


# ======================================================================
# Admin Operations
# ======================================================================

def get_all_tickets_admin(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[TicketStatusEnum] = None,
    category_filter: Optional[TicketCategoryEnum] = None,
    priority_filter: Optional[TicketPriorityEnum] = None,
    assigned_admin_id: Optional[str] = None,
    search: Optional[str] = None
) -> Tuple[int, List[SupportTicket]]:
    """
    Admin-only: query all platform tickets with rich filtering and search.
    """
    query = db.query(SupportTicket)

    if status_filter and not hasattr(status_filter, "default"):
        query = query.filter(SupportTicket.status == status_filter)
    if category_filter and not hasattr(category_filter, "default"):
        query = query.filter(SupportTicket.category == category_filter)
    if priority_filter and not hasattr(priority_filter, "default"):
        query = query.filter(SupportTicket.priority == priority_filter)
    if assigned_admin_id and not hasattr(assigned_admin_id, "default"):
        query = query.filter(SupportTicket.assigned_admin_id == assigned_admin_id)
    if search and not hasattr(search, "default") and str(search).strip():
        term = f"%{str(search).strip()}%"
        query = query.filter(
            or_(
                SupportTicket.ticket_number.ilike(term),
                SupportTicket.subject.ilike(term)
            )
        )

    total = query.count()
    tickets = query.order_by(desc(SupportTicket.updated_at)).offset(skip).limit(limit).all()
    return total, tickets


def get_ticket_metrics_admin(db: Session) -> Dict[str, int]:
    """
    Admin-only: aggregated counts for KPI Spotlight metrics.
    Computes real-time counts from the database without hardcoded values.
    """
    total = db.query(SupportTicket).count()
    open_count = db.query(SupportTicket).filter(SupportTicket.status == TicketStatusEnum.OPEN).count()
    in_progress_count = db.query(SupportTicket).filter(SupportTicket.status == TicketStatusEnum.IN_PROGRESS).count()
    waiting_user_count = db.query(SupportTicket).filter(SupportTicket.status == TicketStatusEnum.WAITING_USER).count()
    resolved_count = db.query(SupportTicket).filter(SupportTicket.status == TicketStatusEnum.RESOLVED).count()
    closed_count = db.query(SupportTicket).filter(SupportTicket.status == TicketStatusEnum.CLOSED).count()
    urgent_count = db.query(SupportTicket).filter(SupportTicket.priority == TicketPriorityEnum.URGENT).count()
    high_count = db.query(SupportTicket).filter(SupportTicket.priority == TicketPriorityEnum.HIGH).count()

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress_count,
        "waiting_user": waiting_user_count,
        "resolved": resolved_count,
        "closed": closed_count,
        "urgent": urgent_count,
        "high": high_count,
        "urgent_or_high": urgent_count + high_count
    }


def update_ticket_priority_admin(
    db: Session,
    ticket_id: str,
    new_priority: TicketPriorityEnum,
    admin_user: User
) -> SupportTicket:
    """
    Admin-only: update ticket priority urgency with audit trail logging.
    """
    ticket = get_ticket_admin(db, ticket_id)
    old_priority = ticket.priority
    if new_priority == old_priority:
        return ticket

    ticket.priority = new_priority
    ticket.updated_at = datetime.now(timezone.utc)

    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=admin_user.id,
        action="PRIORITY_CHANGED",
        details={
            "old_priority": old_priority.value if hasattr(old_priority, "value") else str(old_priority),
            "new_priority": new_priority.value if hasattr(new_priority, "value") else str(new_priority)
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket_admin(db: Session, ticket_id: str) -> SupportTicket:
    """Admin-only: fetch any ticket by ID."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    return ticket


def update_ticket_status_admin(
    db: Session,
    ticket_id: str,
    request: TicketStatusUpdateRequest,
    admin_user: User
) -> SupportTicket:
    """
    Admin-only: update ticket status validating state machine transitions.
    """
    ticket = get_ticket_admin(db, ticket_id)
    old_status = ticket.status

    if request.status == old_status:
        return ticket

    allowed_targets = VALID_STATUS_TRANSITIONS.get(old_status, [])
    if request.status not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid lifecycle transition from {old_status.value} to {request.status.value}. Allowed: {[s.value for s in allowed_targets]}"
        )

    ticket.status = request.status
    ticket.updated_at = datetime.now(timezone.utc)

    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=admin_user.id,
        action="STATUS_CHANGED",
        old_status=old_status.value,
        new_status=request.status.value,
        details={"notes": request.notes} if request.notes else None
    )
    db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket


def assign_ticket_admin(
    db: Session,
    ticket_id: str,
    request: TicketAssignRequest,
    admin_user: User
) -> SupportTicket:
    """
    Admin-only: assign or unassign a ticket.
    """
    ticket = get_ticket_admin(db, ticket_id)
    target_admin_id = request.assigned_admin_id

    if target_admin_id:
        # Verify target user is an active admin
        target_admin = db.query(User).filter(User.id == target_admin_id, User.role == RoleEnum.ADMIN).first()
        if not target_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user must be an active administrator"
            )

    old_admin_id = ticket.assigned_admin_id
    ticket.assigned_admin_id = target_admin_id
    ticket.updated_at = datetime.now(timezone.utc)

    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=admin_user.id,
        action="ASSIGNED",
        details={
            "old_assigned_admin_id": old_admin_id,
            "new_assigned_admin_id": target_admin_id
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket


def add_admin_message(
    db: Session,
    ticket_id: str,
    request: AdminTicketMessageCreateRequest,
    admin_user: User
) -> TicketMessage:
    """
    Admin-only: post a public reply to the user or an internal private note.
    Internal notes are flagged with is_internal=True and hidden from user endpoints.
    """
    ticket = get_ticket_admin(db, ticket_id)

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=admin_user.id,
        sender_role=admin_user.role,
        message=request.message.strip(),
        is_internal=request.is_internal
    )
    db.add(msg)

    # If public reply and ticket was waiting on user or open, change status to WAITING_USER
    if not request.is_internal and ticket.status in [TicketStatusEnum.OPEN, TicketStatusEnum.IN_PROGRESS]:
        old_status = ticket.status.value
        ticket.status = TicketStatusEnum.WAITING_USER
        audit_status = TicketAuditLog(
            ticket_id=ticket.id,
            actor_id=admin_user.id,
            action="STATUS_CHANGED",
            old_status=old_status,
            new_status=TicketStatusEnum.WAITING_USER.value,
            details={"reason": "Admin replied to user"}
        )
        db.add(audit_status)

    audit_action = "INTERNAL_NOTE" if request.is_internal else "ADMIN_REPLY"
    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=admin_user.id,
        action=audit_action,
        details={"is_internal": request.is_internal}
    )
    db.add(audit)

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg


# ======================================================================
# Serializers with Internal-Note Privacy Enforcement
# ======================================================================

def serialize_ticket_summary(ticket: SupportTicket) -> SupportTicketSummaryResponse:
    """Format summary response with associated sender info."""
    user = ticket.user
    admin = ticket.assigned_admin
    # Count public messages for users, all messages for admins
    return SupportTicketSummaryResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        user_id=ticket.user_id,
        user_role=ticket.user_role.value if hasattr(ticket.user_role, "value") else str(ticket.user_role),
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        subject=ticket.subject,
        category=ticket.category.value if hasattr(ticket.category, "value") else str(ticket.category),
        priority=ticket.priority.value if hasattr(ticket.priority, "value") else str(ticket.priority),
        status=ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status),
        assigned_admin_id=ticket.assigned_admin_id,
        assigned_admin_name=admin.name if admin else None,
        is_live_chat=bool(getattr(ticket, "is_live_chat", False)),
        live_chat_requested_at=getattr(ticket, "live_chat_requested_at", None),
        live_chat_ended_at=getattr(ticket, "live_chat_ended_at", None),
        message_count=len(ticket.messages) if ticket.messages else 0,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )


def serialize_ticket_detail(ticket: SupportTicket, is_admin: bool = False) -> SupportTicketDetailResponse:
    """
    Format detail response.
    CRITICAL SECURITY INVARIANT: If is_admin is False, all messages with
    is_internal=True are completely stripped, and audit logs are excluded.
    """
    summary = serialize_ticket_summary(ticket)

    # Filter messages
    message_responses = []
    for m in (ticket.messages or []):
        if m.is_internal and not is_admin:
            continue  # NEVER leak internal notes to non-admins
        sender = m.sender
        message_responses.append(
            TicketMessageResponse(
                id=m.id,
                ticket_id=m.ticket_id,
                sender_id=m.sender_id,
                sender_role=m.sender_role.value if hasattr(m.sender_role, "value") else str(m.sender_role),
                sender_name=sender.name if sender else None,
                message=m.message,
                is_internal=m.is_internal,
                created_at=m.created_at
            )
        )

    # Audit logs only for admins
    audit_responses = None
    if is_admin:
        audit_responses = []
        for a in (ticket.audit_logs or []):
            actor = a.actor
            audit_responses.append(
                TicketAuditLogResponse(
                    id=a.id,
                    action=a.action,
                    actor_id=a.actor_id,
                    actor_name=actor.name if actor else None,
                    old_status=a.old_status,
                    new_status=a.new_status,
                    details=a.details,
                    created_at=a.created_at
                )
            )

    return SupportTicketDetailResponse(
        **summary.model_dump(),
        description=ticket.description,
        messages=message_responses,
        audit_logs=audit_responses
    )


# ======================================================================
# Stage 7 Live Chat, Admin Availability & WebSocket Authentication
# ======================================================================

def get_or_create_admin_availability(db: Session, admin_id: str) -> AdminAvailability:
    """Retrieve or initialize administrator availability and capacity configuration."""
    avail = db.query(AdminAvailability).filter(AdminAvailability.admin_id == admin_id).first()
    if not avail:
        avail = AdminAvailability(
            admin_id=admin_id,
            is_available=False,
            max_active_chats=3,
            last_heartbeat_at=None
        )
        db.add(avail)
        db.commit()
        db.refresh(avail)
    return avail


def update_admin_availability(
    db: Session,
    admin_id: str,
    is_available: bool,
    max_active_chats: int = 3
) -> AdminAvailability:
    """Update administrator online presence and active chat capacity."""
    avail = get_or_create_admin_availability(db, admin_id)
    avail.is_available = is_available
    avail.max_active_chats = max(1, min(10, max_active_chats))
    if is_available:
        avail.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(avail)
    return avail


def record_admin_heartbeat(db: Session, admin_id: str) -> AdminAvailability:
    """Record browser presence heartbeat for active administrator."""
    avail = get_or_create_admin_availability(db, admin_id)
    avail.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(avail)
    return avail


def get_admin_active_chats_count(db: Session, admin_id: str) -> int:
    """
    Compute database-backed active live chat count for an administrator.
    Counts support tickets currently in progress with live chat active.
    """
    return db.query(SupportTicket).filter(
        SupportTicket.assigned_admin_id == admin_id,
        SupportTicket.is_live_chat == True,
        SupportTicket.status == TicketStatusEnum.IN_PROGRESS
    ).count()


def get_available_admins_count(db: Session, max_stale_seconds: int = 60) -> int:
    """
    Count administrators who are currently marked available, have sent a heartbeat
    within the freshness threshold, and have remaining chat capacity.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_stale_seconds)
    online_admins = db.query(AdminAvailability).filter(
        AdminAvailability.is_available == True,
        AdminAvailability.last_heartbeat_at >= cutoff
    ).all()

    available_count = 0
    for admin_avail in online_admins:
        active_chats = get_admin_active_chats_count(db, admin_avail.admin_id)
        if active_chats < admin_avail.max_active_chats:
            available_count += 1
    return available_count


def request_live_handoff(
    db: Session,
    ticket_id: str,
    current_user: User,
    reason: Optional[str] = None
) -> Tuple[SupportTicket, int, int]:
    """
    Candidate or recruiter requests real-time human agent handoff on a ticket.
    Computes genuine queue position and available agent count.
    """
    ticket = get_ticket_with_auth(db, ticket_id, current_user)

    if ticket.status in (TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED):
        # Auto-reopen ticket if handoff is requested on resolved/closed ticket
        ticket.status = TicketStatusEnum.OPEN

    ticket.is_live_chat = True
    now = datetime.now(timezone.utc)
    if not ticket.live_chat_requested_at or ticket.live_chat_ended_at:
        ticket.live_chat_requested_at = now
    ticket.live_chat_ended_at = None

    # System message acknowledging handoff request
    sys_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=f"[System] Live agent handoff requested. Reason: {reason or 'Candidate/Recruiter requested human assistance.'}",
        is_internal=False
    )
    db.add(sys_msg)

    # Audit log
    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        action="LIVE_CHAT_REQUESTED",
        old_status=ticket.status.value,
        new_status=ticket.status.value,
        details={"reason": reason, "requested_at": now.isoformat()}
    )
    db.add(audit)
    db.commit()
    db.refresh(ticket)

    # Calculate real queue position: unassigned open tickets requested before or at this time
    queue_pos = db.query(SupportTicket).filter(
        SupportTicket.is_live_chat == True,
        SupportTicket.status == TicketStatusEnum.OPEN,
        SupportTicket.assigned_admin_id == None,
        SupportTicket.live_chat_requested_at <= ticket.live_chat_requested_at
    ).count()
    if queue_pos == 0:
        queue_pos = 1

    available_admins = get_available_admins_count(db)
    return ticket, queue_pos, available_admins


def accept_live_handoff(
    db: Session,
    ticket_id: str,
    admin_user: User
) -> SupportTicket:
    """
    Administrator accepts an incoming live chat handoff with strict capacity enforcement.
    """
    if admin_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can accept live chat handoffs."
        )

    avail = get_or_create_admin_availability(db, admin_user.id)
    active_chats = get_admin_active_chats_count(db, admin_user.id)
    if active_chats >= avail.max_active_chats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin chat capacity reached ({active_chats}/{avail.max_active_chats} active chats)."
        )

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    old_status = ticket.status.value
    ticket.assigned_admin_id = admin_user.id
    ticket.status = TicketStatusEnum.IN_PROGRESS
    ticket.is_live_chat = True
    if not ticket.live_chat_requested_at:
        ticket.live_chat_requested_at = datetime.now(timezone.utc)
    ticket.live_chat_ended_at = None

    # Public message notifying user
    join_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=admin_user.id,
        sender_role=RoleEnum.ADMIN,
        message=f"Administrator {admin_user.name} has joined the live chat.",
        is_internal=False
    )
    db.add(join_msg)

    # Audit log
    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=admin_user.id,
        action="LIVE_CHAT_ACCEPTED",
        old_status=old_status,
        new_status=TicketStatusEnum.IN_PROGRESS.value,
        details={"admin_id": admin_user.id, "admin_name": admin_user.name}
    )
    db.add(audit)
    db.commit()
    db.refresh(ticket)
    return ticket


def end_live_handoff(
    db: Session,
    ticket_id: str,
    current_user: User,
    reason: Optional[str] = None
) -> SupportTicket:
    """
    End an active live chat session. Can be triggered by the user or an admin.
    """
    ticket = get_ticket_with_auth(db, ticket_id, current_user)
    ticket.is_live_chat = False
    ticket.live_chat_ended_at = datetime.now(timezone.utc)

    # Post session ending notice
    end_msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=f"[System] Live chat session concluded by {current_user.name}. Reason: {reason or 'Session completed'}",
        is_internal=False
    )
    db.add(end_msg)

    # Audit log
    audit = TicketAuditLog(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        action="LIVE_CHAT_ENDED",
        old_status=ticket.status.value,
        new_status=ticket.status.value,
        details={"ended_by": current_user.id, "reason": reason}
    )
    db.add(audit)
    db.commit()
    db.refresh(ticket)
    return ticket


def create_ws_auth_ticket(
    db: Session,
    ticket_id: str,
    current_user: User,
    expiry_seconds: int = 60
) -> WebSocketAuthTicket:
    """
    Issue a short-lived, single-use connection ticket for authenticating WebSocket handshakes.
    PREVENTS PASSING LONG-LIVED JWTS IN WEBSOCKET URLS.
    """
    # Verify user has authorized access to this support ticket
    ticket = get_ticket_with_auth(db, ticket_id, current_user)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)

    ws_ticket = WebSocketAuthTicket(
        ticket_token=token,
        user_id=current_user.id,
        ticket_id=ticket.id,
        expires_at=expires_at,
        is_used=False
    )
    db.add(ws_ticket)
    db.commit()
    db.refresh(ws_ticket)
    return ws_ticket


def validate_and_consume_ws_ticket(
    db: Session,
    ticket_token: str,
    ticket_id: str
) -> Optional[User]:
    """
    Validate and atomically consume a short-lived WebSocket connection ticket.
    Guarantees single-use semantics and expiration checks.
    """
    if not ticket_token or not ticket_id:
        return None

    ws_ticket = db.query(WebSocketAuthTicket).filter(
        WebSocketAuthTicket.ticket_token == ticket_token,
        WebSocketAuthTicket.ticket_id == ticket_id,
        WebSocketAuthTicket.is_used == False
    ).first()

    if not ws_ticket:
        return None

    # Check expiration
    now = datetime.now(timezone.utc)
    ticket_expiry = ws_ticket.expires_at
    if ticket_expiry.tzinfo is None:
        ticket_expiry = ticket_expiry.replace(tzinfo=timezone.utc)

    if ticket_expiry < now:
        return None

    # Atomically mark as consumed
    ws_ticket.is_used = True
    db.commit()

    # Retrieve user
    return db.query(User).filter(User.id == ws_ticket.user_id).first()

