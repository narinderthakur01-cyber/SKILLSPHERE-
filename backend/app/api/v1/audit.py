from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_role
from app.models.models import RoleEnum, AuditLog
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit & Governance"], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    action_type: Optional[str] = Query(None),
    target_resource: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve immutable platform audit logs with optional filtering by action type or resource."""
    query = db.query(AuditLog)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if target_resource:
        query = query.filter(AuditLog.target_resource == target_resource)

    logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()

    response = []
    for log in logs:
        actor_name = log.actor.name if log.actor else "System"
        actor_email = log.actor.email if log.actor else None
        response.append(AuditLogResponse(
            id=log.id,
            actor_id=log.actor_id,
            actor_name=actor_name,
            actor_email=actor_email,
            action_type=log.action_type,
            target_resource=log.target_resource,
            target_id=log.target_id,
            details=log.details or {},
            ip_address=log.ip_address,
            created_at=log.created_at
        ))

    return response
