from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Notification, AuditLog

def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "SYSTEM",
    link: Optional[str] = None
) -> Notification:
    """Persist an in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def create_audit_log(
    db: Session,
    actor_id: Optional[str],
    action_type: str,
    target_resource: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Persist an immutable audit log entry for platform governance."""
    audit = AuditLog(
        actor_id=actor_id,
        action_type=action_type,
        target_resource=target_resource,
        target_id=target_id,
        details=details or {},
        ip_address=ip_address
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
