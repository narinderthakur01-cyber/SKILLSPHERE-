from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.chatbot.service import chatbot_service
from app.chatbot.history import get_history_store, SessionOwnershipError
from app.schemas.chatbot_schemas import (
    ChatMessageRequest,
    ChatResponse,
    FAQListResponse,
    ChatbotHealthResponse,
    ChatHistoryResponse,
    ChatHistoryMessage,
    DeleteSessionResponse
)

router = APIRouter(prefix="/chat", tags=["SkillSphere Assistant"])

@router.post("/message", response_model=ChatResponse)
def send_chat_message(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process user query with rule-based intent matching, contextual follow-up,
    role-based FAQ gating, and persistent conversation history.
    """
    clean_msg = payload.message.strip()
    if not clean_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or blank."
        )

    store = get_history_store()
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    # 1. Retrieve or create session strictly bound to authenticated user
    try:
        session = store.get_or_create_session(
            session_id=payload.session_id,
            user_id=current_user.id,
            user_role=user_role_str,
            title=clean_msg[:50]
        )
    except SessionOwnershipError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access or modify this chat session."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize chat session."
        )

    # 2. Context Restoration: if client did not supply context_topic, restore it from session history
    active_context = payload.context_topic or session.get("last_topic")

    # 3. Save incoming user message to history
    try:
        store.add_message(
            session_id=session["id"],
            user_id=current_user.id,
            sender="user",
            content=clean_msg
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record user message in session history."
        )

    # 4. Generate rule-based response
    bot_res = chatbot_service.process_message(
        message=clean_msg,
        role=user_role_str,
        session_id=session["id"],
        context_topic=active_context,
        language_preference=payload.language_preference,
        db=db,
        current_user=current_user
    )

    # 5. Save assistant response to history
    try:
        store.add_message(
            session_id=session["id"],
            user_id=current_user.id,
            sender="assistant",
            content=bot_res.message,
            intent=bot_res.matched_intent,
            confidence=bot_res.confidence_score
        )
    except Exception:
        pass  # Do not block client response if audit write encounters a transient issue

    # 6. Update session last_topic if valid intent matched
    if bot_res.matched_intent and bot_res.matched_intent != "fallback":
        try:
            store.update_session_topic(session["id"], current_user.id, bot_res.matched_intent)
        except Exception:
            pass

    return bot_res


@router.get("/faqs", response_model=FAQListResponse)
def get_faqs(
    role: Optional[str] = Query(None, description="Optional role filter ('JOB_SEEKER' or 'RECRUITER')")
):
    """
    Retrieve list of verified SkillSphere FAQs filtered by role.
    """
    faqs = chatbot_service.get_faqs_for_role(role)
    return FAQListResponse(
        total=len(faqs),
        role=role or "ALL_PUBLIC",
        faqs=faqs
    )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve full conversation history for a specific session in ascending chronological order.
    Enforces strict user ownership: users can only read their own sessions.
    """
    store = get_history_store()
    try:
        session = store.get_session(session_id, current_user.id)
    except SessionOwnershipError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view this chat session."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query session."
        )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )

    raw_messages = store.get_session_messages(session_id, current_user.id)
    typed_messages = [
        ChatHistoryMessage(
            id=m["id"],
            session_id=m["session_id"],
            sender=m["sender"],
            content=m["content"],
            intent=m.get("intent"),
            confidence=m.get("confidence"),
            created_at=m["created_at"]
        )
        for m in raw_messages
    ]

    return ChatHistoryResponse(
        session_id=session["id"],
        user_id=session["user_id"],
        title=session.get("title"),
        last_topic=session.get("last_topic"),
        messages=typed_messages,
        total_messages=len(typed_messages)
    )


@router.delete("/history/{session_id}", response_model=DeleteSessionResponse)
def delete_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete a conversation session and all its associated messages.
    Enforces strict ownership: users can only delete their own sessions.
    """
    store = get_history_store()
    try:
        session = store.get_session(session_id, current_user.id)
    except SessionOwnershipError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to delete this chat session."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify session ownership."
        )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )

    deleted = store.delete_session(session_id, current_user.id)
    return DeleteSessionResponse(
        session_id=session_id,
        message="Chat session and conversation history successfully deleted.",
        deleted=deleted
    )


@router.get("/health", response_model=ChatbotHealthResponse)
def get_chatbot_health():
    """
    Diagnostic health endpoint for SkillSphere Assistant.
    Reports rule engine status, knowledge base counts, and persistence backend health.
    """
    return chatbot_service.get_health()
