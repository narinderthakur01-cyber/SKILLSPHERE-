from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Message, Application, Candidate, Recruiter
from app.schemas.schemas import MessageCreate, MessageResponse, ConversationResponse
from app.services.activity_service import create_notification

router = APIRouter(prefix="/messages", tags=["Messaging"])

def serialize_message(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        application_id=msg.application_id,
        content=msg.content,
        is_read=msg.is_read,
        created_at=msg.created_at,
        sender_name=msg.sender.name if msg.sender else None,
        receiver_name=msg.receiver.name if msg.receiver else None
    )

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve list of distinct communication partners with latest message and unread count."""
    # Find all messages where user is sender or receiver
    all_msgs = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(desc(Message.created_at)).all()

    partners = {}
    for m in all_msgs:
        partner_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if partner_id not in partners:
            partner_user = db.query(User).filter(User.id == partner_id).first()
            if partner_user:
                unread = db.query(Message).filter(
                    Message.sender_id == partner_id,
                    Message.receiver_id == current_user.id,
                    Message.is_read == False
                ).count()
                partners[partner_id] = ConversationResponse(
                    partner_id=partner_id,
                    partner_name=partner_user.name,
                    partner_role=partner_user.role.value,
                    partner_email=partner_user.email,
                    last_message=m.content,
                    last_message_time=m.created_at,
                    unread_count=unread
                )

    return list(partners.values())

@router.get("/thread/{partner_id}", response_model=List[MessageResponse])
def get_message_thread(
    partner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full chronological message history with a partner, and mark received messages as read."""
    partner = db.query(User).filter(User.id == partner_id).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Fetch messages between both users
    thread = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == partner_id),
            and_(Message.sender_id == partner_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Mark incoming unread messages as read
    unread_incoming = [m for m in thread if m.receiver_id == current_user.id and not m.is_read]
    if unread_incoming:
        for m in unread_incoming:
            m.is_read = True
        db.commit()

    return [serialize_message(m) for m in thread]

@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a direct message from recruiter to candidate or candidate to recruiter."""
    receiver = db.query(User).filter(User.id == msg_in.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found."
        )

    if current_user.id == receiver.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send a message to yourself."
        )

    message = Message(
        sender_id=current_user.id,
        receiver_id=msg_in.receiver_id,
        application_id=msg_in.application_id,
        content=msg_in.content,
        is_read=False
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Notify receiver
    create_notification(
        db=db,
        user_id=receiver.id,
        title=f"New Message from {current_user.name}",
        message=msg_in.content[:120] + ("..." if len(msg_in.content) > 120 else ""),
        notification_type="MESSAGE",
        link=f"/dashboard?tab=messages&partner={current_user.id}" if receiver.role.value == "JOB_SEEKER" else f"/recruiter?tab=messages&partner={current_user.id}"
    )

    return serialize_message(message)
