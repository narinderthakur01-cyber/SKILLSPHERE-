"""
Pydantic validation schemas for Support Ticket System (Stage 4).
Includes request/response models for ticket creation, lifecycle updates,
internal note handling, and role-gated detail responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.models import (
    RoleEnum,
    TicketStatusEnum,
    TicketPriorityEnum,
    TicketCategoryEnum
)


# ======================================================================
# Request Schemas
# ======================================================================

class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200, description="Brief title of the technical issue")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed problem description")
    category: TicketCategoryEnum = Field(default=TicketCategoryEnum.GENERAL, description="Problem category")
    priority: TicketPriorityEnum = Field(default=TicketPriorityEnum.MEDIUM, description="Initial urgency priority")


class TicketMessageCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000, description="User reply content")


class AdminTicketMessageCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000, description="Reply or internal note text")
    is_internal: bool = Field(default=False, description="Whether this message is an internal note visible only to admins")


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatusEnum = Field(..., description="Target lifecycle state")
    notes: Optional[str] = Field(None, max_length=500, description="Optional explanation for status transition")


class TicketPriorityUpdateRequest(BaseModel):
    priority: TicketPriorityEnum = Field(..., description="Target urgency priority")


class TicketAssignRequest(BaseModel):
    assigned_admin_id: Optional[str] = Field(None, max_length=36, description="User ID of admin to assign (or null to unassign)")


# ======================================================================
# Response Schemas
# ======================================================================

class TicketMetricsResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    waiting_user: int
    resolved: int
    closed: int
    urgent: int
    high: int
    urgent_or_high: int

class TicketMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    sender_id: str
    sender_role: str
    sender_name: Optional[str] = None
    message: str
    is_internal: bool
    created_at: datetime


class TicketAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class SupportTicketSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_number: str
    user_id: str
    user_role: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    subject: str
    category: str
    priority: str
    status: str
    assigned_admin_id: Optional[str] = None
    assigned_admin_name: Optional[str] = None
    is_live_chat: bool = False
    live_chat_requested_at: Optional[datetime] = None
    live_chat_ended_at: Optional[datetime] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class SupportTicketDetailResponse(SupportTicketSummaryResponse):
    description: str
    messages: List[TicketMessageResponse] = []
    audit_logs: Optional[List[TicketAuditLogResponse]] = None


class TicketListResponse(BaseModel):
    total: int
    tickets: List[SupportTicketSummaryResponse]


# ======================================================================
# Stage 7 Live Agent & WebSocket Schemas
# ======================================================================

class WSAuthTicketResponse(BaseModel):
    ticket_token: str
    expires_at: datetime
    ticket_id: str
    ws_url: str


class AdminAvailabilityUpdateRequest(BaseModel):
    is_available: bool
    max_active_chats: Optional[int] = Field(default=3, ge=1, le=10)


class AdminAvailabilityResponse(BaseModel):
    admin_id: str
    is_available: bool
    max_active_chats: int
    active_chats_count: int
    last_heartbeat_at: Optional[datetime] = None
    is_active_presence: bool = False


class LiveHandoffRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class LiveHandoffResponse(BaseModel):
    ticket_id: str
    status: str
    is_live_chat: bool
    queue_position: int
    available_admins_count: int
    message: str

