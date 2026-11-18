import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc

from app.core.database import get_db
from app.core.deps import get_current_candidate, get_current_user, require_role
from app.models.models import (
    ProctoringSession, ProctoringEvent, ProctoringSessionStatusEnum,
    ProctoringEventTypeEnum, AssessmentAttempt, Candidate, User, RoleEnum,
    Assessment, Job, AssessmentResult
)
from app.schemas.schemas import (
    ProctoringSessionStartRequest, ProctoringSessionResponse,
    ProctoringEventCreate, ProctoringEventResponse,
    ProctoringSessionDetailResponse, AdminEventReviewRequest,
    AdminSessionReviewRequest, AdminProctoringListResponse
)
from app.services.activity_service import create_audit_log

logger = logging.getLogger("skillsphere.proctoring")

router = APIRouter(tags=["Proctoring"])

def _calculate_warning_level(warning_count: int, status_enum: ProctoringSessionStatusEnum) -> str:
    if status_enum == ProctoringSessionStatusEnum.FLAGGED or warning_count >= 3:
        return "FLAGGED"
    elif warning_count == 2:
        return "WARNING_2"
    elif warning_count == 1:
        return "WARNING_1"
    return "NORMAL"

def _serialize_session_response(session: ProctoringSession) -> ProctoringSessionResponse:
    warning_level = _calculate_warning_level(session.total_warning_count, session.monitoring_status)
    return ProctoringSessionResponse(
        id=session.id,
        assessment_attempt_id=session.assessment_attempt_id,
        candidate_id=session.candidate_id,
        assessment_id=session.assessment_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        camera_permission_granted=session.camera_permission_granted,
        monitoring_status=session.monitoring_status.value if hasattr(session.monitoring_status, "value") else str(session.monitoring_status),
        total_warning_count=session.total_warning_count,
        tab_switch_count=session.tab_switch_count,
        face_not_detected_count=session.face_not_detected_count,
        multiple_faces_count=session.multiple_faces_count,
        camera_interruption_count=session.camera_interruption_count,
        warning_level=warning_level,
        created_at=session.created_at
    )

def _serialize_session_detail(session: ProctoringSession, db: Session) -> ProctoringSessionDetailResponse:
    cand = session.candidate
    cand_user = cand.user if cand else None
    assessment = session.assessment
    job = assessment.job if assessment else None

    # Check attempt result if completed
    result_record = db.query(AssessmentResult).filter(
        AssessmentResult.attempt_id == session.assessment_attempt_id
    ).first()

    events_list = [
        ProctoringEventResponse(
            id=e.id,
            proctoring_session_id=e.proctoring_session_id,
            event_type=e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            event_timestamp=e.event_timestamp,
            duration_seconds=e.duration_seconds,
            severity=e.severity,
            details_json=e.details_json or {},
            reviewed_status=e.reviewed_status,
            reviewed_by_admin_id=e.reviewed_by_admin_id,
            reviewed_at=e.reviewed_at,
            admin_notes=e.admin_notes,
            created_at=e.created_at
        )
        for e in sorted(session.events, key=lambda x: x.event_timestamp)
    ]

    warning_level = _calculate_warning_level(session.total_warning_count, session.monitoring_status)

    return ProctoringSessionDetailResponse(
        id=session.id,
        assessment_attempt_id=session.assessment_attempt_id,
        candidate_id=session.candidate_id,
        assessment_id=session.assessment_id,
        candidate_name=cand_user.name if cand_user else "Candidate",
        candidate_email=cand_user.email if cand_user else "",
        assessment_title=assessment.title if assessment else "Assessment",
        job_title=job.title if job else "N/A",
        started_at=session.started_at,
        ended_at=session.ended_at,
        camera_permission_granted=session.camera_permission_granted,
        monitoring_status=session.monitoring_status.value if hasattr(session.monitoring_status, "value") else str(session.monitoring_status),
        total_warning_count=session.total_warning_count,
        tab_switch_count=session.tab_switch_count,
        face_not_detected_count=session.face_not_detected_count,
        multiple_faces_count=session.multiple_faces_count,
        camera_interruption_count=session.camera_interruption_count,
        warning_level=warning_level,
        score=result_record.marks_obtained if result_record else None,
        total_marks=result_record.total_marks if result_record else (assessment.total_marks if assessment else None),
        percentage=result_record.percentage if result_record else None,
        result=result_record.result.value if (result_record and hasattr(result_record.result, "value")) else None,
        events=events_list,
        created_at=session.created_at
    )

# ==============================================================================
# Candidate Endpoints
# ==============================================================================

@router.post("/proctoring/session/start", response_model=ProctoringSessionResponse)
def start_proctoring_session(
    req: ProctoringSessionStartRequest,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Initialize a proctoring telemetry session for an assessment attempt.
    Enforces candidate ownership and single-session mapping.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == req.attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found.")
    if attempt.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Attempt belongs to another candidate.")

    existing_session = db.query(ProctoringSession).filter(
        ProctoringSession.assessment_attempt_id == attempt.id
    ).first()

    if existing_session:
        existing_session.camera_permission_granted = req.camera_permission_granted
        db.commit()
        db.refresh(existing_session)
        return _serialize_session_response(existing_session)

    new_session = ProctoringSession(
        assessment_attempt_id=attempt.id,
        candidate_id=candidate.id,
        assessment_id=attempt.assessment_id,
        started_at=datetime.now(timezone.utc),
        camera_permission_granted=req.camera_permission_granted,
        monitoring_status=ProctoringSessionStatusEnum.ACTIVE,
        total_warning_count=0,
        tab_switch_count=0,
        face_not_detected_count=0,
        multiple_faces_count=0,
        camera_interruption_count=0
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    logger.info(f"[Proctoring] Session {new_session.id} started for candidate {candidate.id}, attempt {attempt.id}")
    return _serialize_session_response(new_session)

@router.post("/proctoring/session/{session_id}/event", response_model=ProctoringSessionResponse)
def record_proctoring_event(
    session_id: str,
    event_in: ProctoringEventCreate,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Record a behavioral proctoring event (tab switch, face absent, multiple faces, camera drop).
    Strict privacy contract: Only numeric durations, timestamps and metadata are saved.
    Increments warning thresholds and flags session when limit is reached.
    """
    session = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring session not found.")
    if session.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Session does not belong to you.")

    # Match event type
    try:
        event_type_enum = ProctoringEventTypeEnum(event_in.event_type.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid event type: {event_in.event_type}")

    now = datetime.now(timezone.utc)
    event_record = ProctoringEvent(
        proctoring_session_id=session.id,
        event_type=event_type_enum,
        event_timestamp=now,
        duration_seconds=max(0.0, float(event_in.duration_seconds)),
        severity=event_in.severity.upper() if event_in.severity else "LOW",
        details_json=event_in.details_json or {},
        reviewed_status="PENDING"
    )
    db.add(event_record)

    # Increment specific counter
    if event_type_enum == ProctoringEventTypeEnum.TAB_SWITCH or event_type_enum == ProctoringEventTypeEnum.WINDOW_BLUR:
        session.tab_switch_count += 1
        session.total_warning_count += 1
    elif event_type_enum == ProctoringEventTypeEnum.FACE_NOT_DETECTED:
        session.face_not_detected_count += 1
        session.total_warning_count += 1
    elif event_type_enum == ProctoringEventTypeEnum.MULTIPLE_FACES_DETECTED:
        session.multiple_faces_count += 1
        session.total_warning_count += 1
    elif event_type_enum == ProctoringEventTypeEnum.CAMERA_INTERRUPTED:
        session.camera_interruption_count += 1
        session.total_warning_count += 1
    elif event_type_enum == ProctoringEventTypeEnum.SUSPICIOUS_ACTIVITY:
        session.total_warning_count += 1

    # Warning threshold escalation (3+ warnings flags for human review, no auto-fail)
    if session.total_warning_count >= 3:
        session.monitoring_status = ProctoringSessionStatusEnum.FLAGGED

    session.updated_at = now
    db.commit()
    db.refresh(session)

    logger.warning(
        f"[Proctoring] Recorded {event_type_enum.value} on session {session.id}. "
        f"Total warnings: {session.total_warning_count}, status: {session.monitoring_status.value}"
    )

    return _serialize_session_response(session)

@router.get("/proctoring/session/my/{attempt_id}", response_model=ProctoringSessionResponse)
def get_candidate_session(
    attempt_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Fetch candidate's active proctoring session telemetry and warning status."""
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt or attempt.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found.")

    session = db.query(ProctoringSession).filter(
        ProctoringSession.assessment_attempt_id == attempt.id
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No proctoring session for this attempt.")

    return _serialize_session_response(session)

@router.post("/proctoring/session/{session_id}/end", response_model=ProctoringSessionResponse)
def end_proctoring_session(
    session_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Finalize proctoring session when candidate finishes or submits test."""
    session = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring session not found.")
    if session.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    now = datetime.now(timezone.utc)
    session.ended_at = now
    if session.monitoring_status != ProctoringSessionStatusEnum.FLAGGED:
        session.monitoring_status = ProctoringSessionStatusEnum.COMPLETED

    session.updated_at = now
    db.commit()
    db.refresh(session)

    logger.info(f"[Proctoring] Session {session.id} ended. Status: {session.monitoring_status.value}")
    return _serialize_session_response(session)

# ==============================================================================
# Admin Endpoints (RBAC: ADMIN role strictly required)
# ==============================================================================

@router.get("/admin/proctoring/sessions", response_model=AdminProctoringListResponse)
def get_admin_proctoring_sessions(
    filter: Optional[str] = Query("ALL", description="ALL, NORMAL, WARNINGS, REQUIRES_REVIEW, COMPLETED"),
    search: Optional[str] = Query(None, description="Search candidate name, email, assessment, job"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    List all proctoring sessions for Admin oversight with filtering, search, and pagination.
    """
    query = db.query(ProctoringSession).join(
        Candidate, ProctoringSession.candidate_id == Candidate.id
    ).join(
        User, Candidate.user_id == User.id
    ).join(
        Assessment, ProctoringSession.assessment_id == Assessment.id
    ).join(
        Job, Assessment.job_id == Job.id
    )

    # Filter logic
    f_upper = (filter or "ALL").upper()
    if f_upper == "NORMAL":
        query = query.filter(ProctoringSession.total_warning_count == 0)
    elif f_upper == "WARNINGS":
        query = query.filter(
            ProctoringSession.total_warning_count > 0,
            ProctoringSession.total_warning_count < 3
        )
    elif f_upper == "REQUIRES_REVIEW":
        query = query.filter(
            or_(
                ProctoringSession.monitoring_status == ProctoringSessionStatusEnum.FLAGGED,
                ProctoringSession.total_warning_count >= 3
            )
        )
    elif f_upper == "COMPLETED":
        query = query.filter(ProctoringSession.monitoring_status == ProctoringSessionStatusEnum.COMPLETED)

    # Search logic
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                Assessment.title.ilike(term),
                Job.title.ilike(term)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    sessions = query.order_by(desc(ProctoringSession.created_at)).offset(offset).limit(page_size).all()

    items = [_serialize_session_detail(s, db) for s in sessions]

    return AdminProctoringListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/admin/proctoring/sessions/{session_id}", response_model=ProctoringSessionDetailResponse)
def get_admin_proctoring_session_detail(
    session_id: str,
    admin_user: User = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Fetch deep session detail including candidate metadata, test score, and full event timeline."""
    session = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring session not found.")

    return _serialize_session_detail(session, db)

@router.put("/admin/proctoring/events/{event_id}/review", response_model=ProctoringEventResponse)
def review_proctoring_event(
    event_id: str,
    review_in: AdminEventReviewRequest,
    admin_user: User = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Mark an individual suspicious event as REVIEWED or DISMISSED with admin notes."""
    event_record = db.query(ProctoringEvent).filter(ProctoringEvent.id == event_id).first()
    if not event_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring event not found.")

    now = datetime.now(timezone.utc)
    event_record.reviewed_status = review_in.reviewed_status
    if review_in.admin_notes is not None:
        event_record.admin_notes = review_in.admin_notes
    event_record.reviewed_by_admin_id = admin_user.id
    event_record.reviewed_at = now

    db.commit()
    db.refresh(event_record)

    create_audit_log(
        db=db,
        actor_id=admin_user.id,
        action_type="PROCTORING_EVENT_REVIEWED",
        target_resource="ProctoringEvent",
        target_id=event_record.id,
        details={
            "session_id": event_record.proctoring_session_id,
            "status": review_in.reviewed_status,
            "notes": review_in.admin_notes
        }
    )

    return ProctoringEventResponse(
        id=event_record.id,
        proctoring_session_id=event_record.proctoring_session_id,
        event_type=event_record.event_type.value if hasattr(event_record.event_type, "value") else str(event_record.event_type),
        event_timestamp=event_record.event_timestamp,
        duration_seconds=event_record.duration_seconds,
        severity=event_record.severity,
        details_json=event_record.details_json or {},
        reviewed_status=event_record.reviewed_status,
        reviewed_by_admin_id=event_record.reviewed_by_admin_id,
        reviewed_at=event_record.reviewed_at,
        admin_notes=event_record.admin_notes,
        created_at=event_record.created_at
    )

@router.put("/admin/proctoring/sessions/{session_id}/review", response_model=ProctoringSessionDetailResponse)
def review_proctoring_session(
    session_id: str,
    review_in: AdminSessionReviewRequest,
    admin_user: User = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update overall proctoring session status (e.g. resolve FLAGGED or clear for recruiter)."""
    session = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proctoring session not found.")

    now = datetime.now(timezone.utc)
    session.monitoring_status = ProctoringSessionStatusEnum(review_in.monitoring_status)
    session.updated_at = now

    db.commit()
    db.refresh(session)

    create_audit_log(
        db=db,
        actor_id=admin_user.id,
        action_type="PROCTORING_SESSION_REVIEWED",
        target_resource="ProctoringSession",
        target_id=session.id,
        details={
            "new_status": review_in.monitoring_status,
            "admin_notes": review_in.admin_notes
        }
    )

    return _serialize_session_detail(session, db)
