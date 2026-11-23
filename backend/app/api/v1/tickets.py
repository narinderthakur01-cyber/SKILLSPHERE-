"""
FastAPI Route Controllers for Support Ticket System (Stage 4).
Includes both User-facing endpoints (/api/v1/tickets) and Admin-only endpoints (/api/v1/admin/tickets).

Security Enforcements:
- IDOR Prevention: Users only access tickets where ticket.user_id == current_user.id
- Role Isolation: Candidates and Recruiters cannot view internal admin notes
- Status Validation: Backend state machine enforces allowed lifecycle transitions
- Admin Authorization: Admin endpoints strictly require RoleEnum.ADMIN
"""

import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.models import User, RoleEnum, TicketStatusEnum, TicketCategoryEnum, TicketPriorityEnum
from app.schemas.ticket_schemas import (
    TicketCreateRequest,
    TicketMessageCreateRequest,
    AdminTicketMessageCreateRequest,
    TicketStatusUpdateRequest,
    TicketPriorityUpdateRequest,
    TicketAssignRequest,
    TicketMessageResponse,
    SupportTicketDetailResponse,
    TicketListResponse,
    TicketMetricsResponse,
    WSAuthTicketResponse,
    AdminAvailabilityUpdateRequest,
    AdminAvailabilityResponse,
    LiveHandoffRequest,
    LiveHandoffResponse
)
from app.services import ticket_service
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])
admin_router = APIRouter(prefix="/admin/tickets", tags=["Admin Support Tickets"])


# ======================================================================
# User Endpoints (/api/v1/tickets)
# Accessible to authenticated Candidates and Recruiters
# ======================================================================

@router.post(
    "",
    response_model=SupportTicketDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket"
)
def create_ticket(
    request: TicketCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new support ticket bound to the caller's identity.
    Derives user_id and user_role securely from the validated JWT token.
    """
    ticket = ticket_service.create_ticket(db, request, current_user)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=False)


@router.get(
    "",
    response_model=TicketListResponse,
    summary="List tickets owned by the current user"
)
def list_user_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[TicketStatusEnum] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns tickets submitted by the authenticated user.
    Prevents IDOR: non-admins cannot query or enumerate other users' tickets.
    """
    total, tickets = ticket_service.get_user_tickets(
        db, current_user, skip=skip, limit=limit, status_filter=status
    )
    summaries = [ticket_service.serialize_ticket_summary(t) for t in tickets]
    return TicketListResponse(total=total, tickets=summaries)


@router.get(
    "/{ticket_id}",
    response_model=SupportTicketDetailResponse,
    summary="Get details of a specific ticket"
)
def get_user_ticket(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves full details and public conversation history for a ticket.
    Returns 404 for tickets not owned by the caller to avoid exposing their existence.
    Internal admin notes are completely excluded.
    """
    is_admin = (current_user.role.value == "ADMIN" if hasattr(current_user.role, "value") else str(current_user.role) == "ADMIN")
    ticket = ticket_service.get_ticket_for_user(db, ticket_id, current_user)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=is_admin)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a reply to an existing ticket"
)
def reply_to_ticket(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: TicketMessageCreateRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adds a user response to a ticket.
    Automatically moves WAITING_USER status back to IN_PROGRESS.
    """
    msg = ticket_service.add_user_message(db, ticket_id, request, current_user)
    return TicketMessageResponse(
        id=msg.id,
        ticket_id=msg.ticket_id,
        sender_id=msg.sender_id,
        sender_role=msg.sender_role.value if hasattr(msg.sender_role, "value") else str(msg.sender_role),
        sender_name=current_user.name,
        message=msg.message,
        is_internal=msg.is_internal,
        created_at=msg.created_at
    )


@router.post(
    "/{ticket_id}/ws-auth-ticket",
    response_model=WSAuthTicketResponse,
    summary="Issue short-lived single-use WebSocket connection ticket"
)
def issue_ws_auth_ticket(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Issue a 60-second single-use token for authenticating a WebSocket connection.
    Prevents passing long-lived JWTs in WebSocket connection URLs.
    """
    ws_ticket = ticket_service.create_ws_auth_ticket(db, ticket_id, current_user, expiry_seconds=60)
    ws_url = f"/api/v1/tickets/{ticket_id}/ws?ticket={ws_ticket.ticket_token}"
    return WSAuthTicketResponse(
        ticket_token=ws_ticket.ticket_token,
        expires_at=ws_ticket.expires_at,
        ticket_id=ticket_id,
        ws_url=ws_url
    )


@router.post(
    "/{ticket_id}/live-request",
    response_model=LiveHandoffResponse,
    summary="Request real-time human agent handoff"
)
async def request_live_agent(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: Optional[LiveHandoffRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Escalate a support ticket to real-time live human chat.
    Calculates queue position and available agent count.
    """
    reason = request.reason if request else None
    ticket, queue_pos, avail_count = ticket_service.request_live_handoff(db, ticket_id, current_user, reason)

    # Broadcast notice to room if connected
    await ws_manager.broadcast_event(
        ticket_id=ticket_id,
        event_type="live_requested",
        data={
            "ticket_id": ticket_id,
            "queue_position": queue_pos,
            "available_admins": avail_count,
            "reason": reason
        },
        is_internal=False
    )

    msg = f"Live agent handoff requested. Queue position: #{queue_pos}." if avail_count > 0 else "Live agent handoff requested. All administrators are currently offline; your request is queued."
    return LiveHandoffResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        is_live_chat=ticket.is_live_chat,
        queue_position=queue_pos,
        available_admins_count=avail_count,
        message=msg
    )


@router.post(
    "/{ticket_id}/live-end",
    response_model=SupportTicketDetailResponse,
    summary="Conclude active real-time live chat session"
)
async def end_live_agent(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: Optional[LiveHandoffRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    End active real-time live chat session.
    """
    reason = request.reason if request else None
    ticket = ticket_service.end_live_handoff(db, ticket_id, current_user, reason)

    # Broadcast session conclusion to room
    await ws_manager.broadcast_event(
        ticket_id=ticket_id,
        event_type="live_ended",
        data={
            "ticket_id": ticket_id,
            "ended_by": current_user.name,
            "reason": reason
        },
        is_internal=False
    )

    is_admin = (current_user.role == RoleEnum.ADMIN)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=is_admin)


@router.websocket("/{ticket_id}/ws")
async def ticket_websocket_endpoint(
    websocket: WebSocket,
    ticket_id: str,
    ticket: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time live chat.
    Validates single-use connection ticket during handshake.
    Handles application-level JSON ping/pong and bi-directional message dispatch.
    CRITICAL: Internal notes (is_internal=True) are NEVER broadcast to non-admins.
    """
    if not ticket:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication ticket")
        return

    # Validate and atomically consume single-use connection ticket
    user = ticket_service.validate_and_consume_ws_ticket(db, ticket, ticket_id)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired authentication ticket")
        return

    conn_id = secrets.token_hex(8)
    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    await ws_manager.connect(ticket_id, conn_id, websocket, user.id, user_role_str, user.name)

    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                continue

            msg_type = data.get("type")
            if msg_type == "ping":
                # Browser application-level ping/pong keepalive
                await ws_manager.send_personal_message(
                    websocket,
                    "pong",
                    {"timestamp": datetime.now(timezone.utc).isoformat()}
                )
            elif msg_type == "message":
                content = str(data.get("message", "")).strip()
                if not content:
                    continue
                is_internal = bool(data.get("is_internal", False)) and (user.role == RoleEnum.ADMIN)

                # Persist message in database
                if user.role == RoleEnum.ADMIN:
                    msg_obj = ticket_service.add_admin_message(
                        db, ticket_id,
                        AdminTicketMessageCreateRequest(message=content, is_internal=is_internal),
                        user
                    )
                else:
                    msg_obj = ticket_service.add_user_message(
                        db, ticket_id,
                        TicketMessageCreateRequest(message=content),
                        user
                    )

                # Broadcast to room (ws_manager filters out is_internal from non-admins)
                await ws_manager.broadcast_event(
                    ticket_id=ticket_id,
                    event_type="new_message",
                    data={
                        "id": msg_obj.id,
                        "ticket_id": msg_obj.ticket_id,
                        "sender_id": msg_obj.sender_id,
                        "sender_role": msg_obj.sender_role.value if hasattr(msg_obj.sender_role, "value") else str(msg_obj.sender_role),
                        "sender_name": user.name,
                        "message": msg_obj.message,
                        "is_internal": msg_obj.is_internal,
                        "created_at": msg_obj.created_at.isoformat()
                    },
                    is_internal=msg_obj.is_internal
                )
            elif msg_type == "typing":
                await ws_manager.broadcast_event(
                    ticket_id=ticket_id,
                    event_type="typing",
                    data={
                        "user_id": user.id,
                        "user_name": user.name,
                        "is_typing": bool(data.get("is_typing", False))
                    },
                    is_internal=False
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(ticket_id, conn_id)
        await ws_manager.broadcast_event(
            ticket_id=ticket_id,
            event_type="user_left",
            data={
                "user_id": user.id,
                "user_name": user.name,
                "room_occupancy": ws_manager.get_room_occupancy(ticket_id)
            },
            is_internal=False
        )
    except Exception:
        ws_manager.disconnect(ticket_id, conn_id)



# ======================================================================
# Admin-Only Endpoints (/api/v1/admin/tickets)
# Accessible ONLY to authenticated administrators
# ======================================================================

@admin_router.get(
    "/metrics",
    response_model=TicketMetricsResponse,
    summary="Get aggregated support ticket KPI metrics (Admin only)"
)
def get_admin_ticket_metrics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: telemetry counts for KPI dashboard spotlight cards.
    """
    return ticket_service.get_ticket_metrics_admin(db)


@admin_router.get(
    "",
    response_model=TicketListResponse,
    summary="List all platform tickets (Admin only)"
)
def list_all_tickets_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[TicketStatusEnum] = Query(None),
    category: Optional[TicketCategoryEnum] = Query(None),
    priority: Optional[TicketPriorityEnum] = Query(None),
    assigned_admin_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: query and filter all support tickets across the platform.
    """
    status_filter = status if isinstance(status, (TicketStatusEnum, str)) and not hasattr(status, "default") else None
    category_filter = category if isinstance(category, (TicketCategoryEnum, str)) and not hasattr(category, "default") else None
    priority_filter = priority if isinstance(priority, (TicketPriorityEnum, str)) and not hasattr(priority, "default") else None
    assigned_id = assigned_admin_id if isinstance(assigned_admin_id, str) and not hasattr(assigned_admin_id, "default") else None
    search_term = search if isinstance(search, str) and not hasattr(search, "default") else None
    skip_val = skip if isinstance(skip, int) and not hasattr(skip, "default") else 0
    limit_val = limit if isinstance(limit, int) and not hasattr(limit, "default") else 50

    total, tickets = ticket_service.get_all_tickets_admin(
        db,
        skip=skip_val,
        limit=limit_val,
        status_filter=status_filter,
        category_filter=category_filter,
        priority_filter=priority_filter,
        assigned_admin_id=assigned_id,
        search=search_term
    )
    summaries = [ticket_service.serialize_ticket_summary(t) for t in tickets]
    return TicketListResponse(total=total, tickets=summaries)


@admin_router.get(
    "/{ticket_id}",
    response_model=SupportTicketDetailResponse,
    summary="View complete ticket details including internal notes (Admin only)"
)
def get_ticket_detail_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: view complete ticket conversation, including private internal notes and audit history.
    """
    ticket = ticket_service.get_ticket_admin(db, ticket_id)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=True)


@admin_router.put(
    "/{ticket_id}/status",
    response_model=SupportTicketDetailResponse,
    summary="Update ticket lifecycle status (Admin only)"
)
def update_ticket_status_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: TicketStatusUpdateRequest = ...,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: change ticket lifecycle state.
    Enforces server-side transition state machine rules.
    """
    ticket = ticket_service.update_ticket_status_admin(db, ticket_id, request, admin_user)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=True)


@admin_router.put(
    "/{ticket_id}/priority",
    response_model=SupportTicketDetailResponse,
    summary="Update ticket priority urgency (Admin only)"
)
def update_ticket_priority_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: TicketPriorityUpdateRequest = ...,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: adjust ticket priority urgency.
    """
    ticket = ticket_service.update_ticket_priority_admin(db, ticket_id, request.priority, admin_user)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=True)


@admin_router.put(
    "/{ticket_id}/assign",
    response_model=SupportTicketDetailResponse,
    summary="Assign ticket to an administrator (Admin only)"
)
def assign_ticket_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: TicketAssignRequest = ...,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: assign or reassign a support ticket to an active administrator.
    """
    ticket = ticket_service.assign_ticket_admin(db, ticket_id, request, admin_user)
    return ticket_service.serialize_ticket_detail(ticket, is_admin=True)


@admin_router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post public reply or private internal note (Admin only)"
)
def reply_as_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    request: AdminTicketMessageCreateRequest = ...,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin-only: post a public reply to the ticket creator or an internal private note.
    Internal notes are completely hidden from regular user views.
    """
    msg = ticket_service.add_admin_message(db, ticket_id, request, admin_user)
    return TicketMessageResponse(
        id=msg.id,
        ticket_id=msg.ticket_id,
        sender_id=msg.sender_id,
        sender_role=msg.sender_role.value if hasattr(msg.sender_role, "value") else str(msg.sender_role),
        sender_name=admin_user.name,
        message=msg.message,
        is_internal=msg.is_internal,
        created_at=msg.created_at
    )


# ======================================================================
# Admin Live Chat Presence & Handoff Endpoints
# ======================================================================

@admin_router.get(
    "/availability",
    response_model=AdminAvailabilityResponse,
    summary="Get current administrator availability & capacity"
)
def get_admin_availability(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Query real-time availability status, heartbeat presence, and active live chats.
    """
    avail = ticket_service.get_or_create_admin_availability(db, admin_user.id)
    active_chats = ticket_service.get_admin_active_chats_count(db, admin_user.id)
    now = datetime.now(timezone.utc)
    is_presence = False
    if avail.last_heartbeat_at:
        hb = avail.last_heartbeat_at
        if hb.tzinfo is None:
            hb = hb.replace(tzinfo=timezone.utc)
        is_presence = (now - hb) <= timedelta(seconds=60)
    return AdminAvailabilityResponse(
        admin_id=avail.admin_id,
        is_available=avail.is_available,
        max_active_chats=avail.max_active_chats,
        active_chats_count=active_chats,
        last_heartbeat_at=avail.last_heartbeat_at,
        is_active_presence=is_presence
    )


@admin_router.put(
    "/availability",
    response_model=AdminAvailabilityResponse,
    summary="Update administrator live availability & capacity limit"
)
def update_admin_availability(
    request: AdminAvailabilityUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Update administrator online/offline status and maximum concurrent live chat capacity.
    """
    avail = ticket_service.update_admin_availability(
        db, admin_user.id,
        is_available=request.is_available,
        max_active_chats=request.max_active_chats or 3
    )
    active_chats = ticket_service.get_admin_active_chats_count(db, admin_user.id)
    now = datetime.now(timezone.utc)
    is_presence = False
    if avail.last_heartbeat_at:
        hb = avail.last_heartbeat_at
        if hb.tzinfo is None:
            hb = hb.replace(tzinfo=timezone.utc)
        is_presence = (now - hb) <= timedelta(seconds=60)
    return AdminAvailabilityResponse(
        admin_id=avail.admin_id,
        is_available=avail.is_available,
        max_active_chats=avail.max_active_chats,
        active_chats_count=active_chats,
        last_heartbeat_at=avail.last_heartbeat_at,
        is_active_presence=is_presence
    )


@admin_router.post(
    "/availability/heartbeat",
    response_model=AdminAvailabilityResponse,
    summary="Record administrator browser presence heartbeat"
)
def record_admin_heartbeat(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Record periodic browser presence heartbeat (called every 30s by active admin dashboard).
    """
    avail = ticket_service.record_admin_heartbeat(db, admin_user.id)
    active_chats = ticket_service.get_admin_active_chats_count(db, admin_user.id)
    return AdminAvailabilityResponse(
        admin_id=avail.admin_id,
        is_available=avail.is_available,
        max_active_chats=avail.max_active_chats,
        active_chats_count=active_chats,
        last_heartbeat_at=avail.last_heartbeat_at,
        is_active_presence=True
    )


@admin_router.post(
    "/{ticket_id}/accept-handoff",
    response_model=SupportTicketDetailResponse,
    summary="Accept live handoff request with capacity enforcement (Admin only)"
)
async def accept_handoff_admin(
    ticket_id: str = Path(..., min_length=1, max_length=36),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    """
    Admin accepts an incoming live handoff ticket.
    Enforces maximum active chat capacity. Broadcasts join notification over WebSocket.
    """
    ticket = ticket_service.accept_live_handoff(db, ticket_id, admin_user)

    # Broadcast event to room
    await ws_manager.broadcast_event(
        ticket_id=ticket_id,
        event_type="live_accepted",
        data={
            "ticket_id": ticket_id,
            "admin_id": admin_user.id,
            "admin_name": admin_user.name
        },
        is_internal=False
    )

    return ticket_service.serialize_ticket_detail(ticket, is_admin=True)

