import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_recruiter, get_current_candidate
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Application, Interview,
    ApplicationStatusEnum, InterviewRecording, RecordingConsent,
    InterviewScorecard, InterviewTranscript, MediaAsset,
    CandidateAssessmentAssignment, InterviewQuestion, InterviewResponse as InterviewResponseModel,
    InterviewEvaluation, Job
)
from app.schemas.schemas import (
    InterviewCreate, InterviewUpdate, InterviewResponse,
    InterviewRoomTokenResponse, RecordingConsentRequest,
    RecordingConsentResponse, InterviewRecordingResponse,
    InterviewRoomStatusResponse, InterviewScorecardCreate,
    InterviewScorecardResponse, InterviewTranscriptResponse,
    ApproveTranscriptRequest, InterviewQuestionCreate,
    InterviewQuestionResponse, GenerateAIQuestionsRequest,
    InterviewConfigureAIRequest, InterviewResponseItemCreate,
    InterviewResponseItemResponse, InterviewEvaluationResponse,
    InterviewEvaluationUpdate, HybridTakeoverRequest
)
from app.services.activity_service import create_notification, create_audit_log
from app.services.email_service import EmailService
from app.services.livekit_service import LiveKitService
from app.services.interview_ai_service import InterviewAIService
from app.services.cloudinary_service import CloudinaryService
from app.services.ai_interviewer_agent import AIInterviewerAgent

router = APIRouter(prefix="/interviews", tags=["Interviews"])

def serialize_interview(interview: Interview) -> InterviewResponse:
    candidate_name = None
    if interview.candidate and interview.candidate.user:
        candidate_name = interview.candidate.user.name
    
    recruiter_name = None
    if interview.recruiter and interview.recruiter.user:
        recruiter_name = interview.recruiter.user.name

    job_title = None
    if interview.application and interview.application.job:
        job_title = interview.application.job.title

    return InterviewResponse(
        id=interview.id,
        application_id=interview.application_id,
        recruiter_id=interview.recruiter_id,
        candidate_id=interview.candidate_id,
        interview_type=interview.interview_type,
        interview_mode=getattr(interview, "interview_mode", "HUMAN") or "HUMAN",
        scheduled_time=interview.scheduled_time,
        duration_minutes=interview.duration_minutes,
        meeting_link=interview.meeting_link,
        location=interview.location,
        instructions=interview.instructions,
        status=interview.status,
        email_status=getattr(interview, "email_status", "PENDING") or "PENDING",
        brevo_message_id=getattr(interview, "brevo_message_id", None),
        email_sent_at=getattr(interview, "email_sent_at", None),
        email_error_message=getattr(interview, "email_error_message", None),
        room_id=getattr(interview, "room_id", None),
        room_status=getattr(interview, "room_status", "WAITING") or "WAITING",
        room_started_at=getattr(interview, "room_started_at", None),
        room_ended_at=getattr(interview, "room_ended_at", None),
        round_number=getattr(interview, "round_number", 1) or 1,
        round_title=getattr(interview, "round_title", "Round 1 - Technical Screen") or "Round 1 - Technical Screen",
        recording_enabled=bool(getattr(interview, "recording_enabled", False)),
        recording_status=getattr(interview, "recording_status", "NOT_RECORDED") or "NOT_RECORDED",
        is_admitted=bool(getattr(interview, "is_admitted", False)),
        ai_config_json=getattr(interview, "ai_config_json", None) or {},
        ai_takeover_status=getattr(interview, "ai_takeover_status", "AI_ACTIVE") or "AI_ACTIVE",
        current_question_index=getattr(interview, "current_question_index", 0) or 0,
        started_at=getattr(interview, "started_at", None),
        ended_at=getattr(interview, "ended_at", None),
        created_at=interview.created_at,
        updated_at=interview.updated_at,
        job_title=job_title,
        candidate_name=candidate_name,
        recruiter_name=recruiter_name
    )

@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def schedule_interview(
    interview_in: InterviewCreate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Schedule an interview for an applicant. Notifies candidate and logs audit trail."""
    app_record = db.query(Application).filter(Application.id == interview_in.application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Recruiter must own the job opening
    if app_record.job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only schedule interviews for your own job postings."
        )

    # Validate schedule date is not in the past
    now_utc = datetime.now(timezone.utc)
    sched_time = interview_in.scheduled_time
    if sched_time.tzinfo is None:
        sched_time = sched_time.replace(tzinfo=timezone.utc)
    if sched_time < now_utc - timedelta(minutes=15):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Schedule Date: Interview cannot be scheduled in the past."
        )

    # Check for scheduling conflicts for the recruiter
    conflict = db.query(Interview).filter(
        Interview.recruiter_id == recruiter.id,
        Interview.scheduled_time == interview_in.scheduled_time,
        Interview.status.in_(["SCHEDULED", "RESCHEDULED", "WAITING", "IN_PROGRESS"])
    ).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduling Conflict: You already have an interview scheduled at this exact time."
        )

    room_id = f"room_{uuid.uuid4().hex[:12]}"
    meeting_link = interview_in.meeting_link
    if interview_in.interview_type == "ONLINE" and not meeting_link:
        meeting_link = f"/interview-room/{room_id}"

    # Build comprehensive AI & workflow configuration
    ai_config = getattr(interview_in, "ai_config_json", None) or {}
    if getattr(interview_in, "voice", None):
        ai_config["voice"] = interview_in.voice
    if getattr(interview_in, "difficulty", None):
        ai_config["difficulty"] = interview_in.difficulty
    if getattr(interview_in, "allow_recruiter_takeover", None) is not None:
        ai_config["allow_recruiter_takeover"] = interview_in.allow_recruiter_takeover
    if getattr(interview_in, "categories", None):
        ai_config["categories"] = interview_in.categories

    interview = Interview(
        application_id=app_record.id,
        recruiter_id=recruiter.id,
        candidate_id=app_record.candidate_id,
        interview_type=interview_in.interview_type,
        interview_mode=getattr(interview_in, "interview_mode", "HUMAN") or "HUMAN",
        ai_config_json=ai_config,
        scheduled_time=interview_in.scheduled_time,
        duration_minutes=interview_in.duration_minutes,
        meeting_link=meeting_link,
        location=interview_in.location,
        instructions=interview_in.instructions,
        status="SCHEDULED",
        email_status="PENDING",
        room_id=room_id,
        room_status="WAITING",
        round_number=getattr(interview_in, "round_number", 1) or 1,
        round_title=getattr(interview_in, "round_title", "Round 1 - Technical Screen") or "Round 1 - Technical Screen",
        recording_enabled=bool(getattr(interview_in, "recording_enabled", False)),
        recording_status="NOT_RECORDED",
        is_admitted=False
    )
    db.add(interview)

    # If application is not yet in INTERVIEW status, transition it
    if app_record.status not in [ApplicationStatusEnum.INTERVIEW, ApplicationStatusEnum.SELECTED]:
        app_record.status = ApplicationStatusEnum.INTERVIEW

    # 1. Commit DB transaction first
    db.commit()
    db.refresh(interview)

    # Persist interview questions if provided
    has_questions = False
    if interview_in.questions:
        for idx, q in enumerate(interview_in.questions):
            q_text = q.get("question_text") if isinstance(q, dict) else getattr(q, "question_text", "")
            if q_text:
                q_type = q.get("question_type", "TECHNICAL") if isinstance(q, dict) else getattr(q, "question_type", "TECHNICAL")
                q_source = q.get("source", "CUSTOM") if isinstance(q, dict) else getattr(q, "source", "CUSTOM")
                q_seq = q.get("sequence_number", idx + 1) if isinstance(q, dict) else getattr(q, "sequence_number", idx + 1)
                q_concepts = q.get("expected_concepts", []) if isinstance(q, dict) else getattr(q, "expected_concepts", [])
                q_duration = int(q.get("max_duration_seconds", 180) if isinstance(q, dict) else getattr(q, "max_duration_seconds", 180))
                db.add(InterviewQuestion(
                    interview_id=interview.id,
                    question_text=q_text,
                    question_type=q_type,
                    source=q_source,
                    sequence_number=q_seq,
                    expected_concepts=q_concepts,
                    max_duration_seconds=q_duration
                ))
                has_questions = True
        db.commit()

    # Seed initial AI questions automatically if AI_LIVE or HYBRID and no custom questions provided
    if not has_questions and interview.interview_mode in ["AI_LIVE", "HYBRID", "CONFIGURED"]:
        auto_qs = InterviewAIService.generate_ai_interview_questions(
            job_title=app_record.job.title if app_record.job else "Software Engineer",
            job_description=app_record.job.description if app_record.job else None,
            difficulty=ai_config.get("difficulty", "INTERMEDIATE"),
            question_count=4,
            categories=ai_config.get("categories")
        )
        for idx, q_data in enumerate(auto_qs):
            db.add(InterviewQuestion(
                interview_id=interview.id,
                question_text=q_data["question_text"],
                question_type=q_data.get("question_type", "TECHNICAL"),
                source="AI_GENERATED",
                sequence_number=idx + 1,
                expected_concepts=q_data.get("expected_concepts", []),
                max_duration_seconds=q_data.get("max_duration_seconds", 180)
            ))
        db.commit()

    # 2. In-app notification
    create_notification(
        db=db,
        user_id=app_record.candidate.user_id,
        title="Interview Scheduled",
        message=f"An interview for '{app_record.job.title}' has been scheduled on {interview.scheduled_time.strftime('%b %d, %Y at %H:%M UTC')}.",
        notification_type="INTERVIEW_SCHEDULED",
        link="/dashboard?tab=interviews"
    )

    # 3. Audit log
    create_audit_log(
        db=db,
        actor_id=recruiter.user_id,
        action_type="INTERVIEW_SCHEDULE",
        target_resource="Interview",
        target_id=interview.id,
        details={
            "application_id": app_record.id,
            "job_title": app_record.job.title,
            "scheduled_time": interview.scheduled_time.isoformat(),
            "interview_type": interview.interview_type
        }
    )

    # 4. Dispatch transactional email via Brevo EmailService
    candidate_user = app_record.candidate.user if app_record.candidate else None
    if candidate_user and candidate_user.email:
        company_name = (
            app_record.job.company.name if (app_record.job and app_record.job.company and app_record.job.company.name)
            else (recruiter.company.name if (recruiter.company and recruiter.company.name) else "SkillSphere Partner")
        )
        recruiter_name = recruiter.user.name if (recruiter.user and recruiter.user.name) else None
        recruiter_email = recruiter.user.email if (recruiter.user and recruiter.user.email) else None

        try:
            email_res = EmailService.send_interview_invitation_email(
                to_email=candidate_user.email,
                candidate_name=candidate_user.name,
                job_title=app_record.job.title,
                company_name=company_name,
                interview_type=interview.interview_type,
                scheduled_time=interview.scheduled_time,
                duration_minutes=interview.duration_minutes,
                meeting_link=interview.meeting_link,
                location=interview.location,
                instructions=interview.instructions,
                recruiter_name=recruiter_name,
                recruiter_email=recruiter_email
            )
            if email_res.get("delivered") or email_res.get("status") == "delivered":
                interview.email_status = "ACCEPTED_BY_BREVO"
                interview.brevo_message_id = email_res.get("message_id")
                interview.email_sent_at = datetime.now(timezone.utc)
                interview.email_error_message = None
            else:
                interview.email_status = "FAILED"
                interview.email_error_message = str(email_res.get("detail") or "Brevo API delivery rejection")
        except Exception as e:
            interview.email_status = "FAILED"
            interview.email_error_message = str(e)

        db.commit()
        db.refresh(interview)

    return serialize_interview(interview)

@router.get("/my", response_model=List[InterviewResponse])
def get_my_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all interviews for the authenticated candidate or recruiter."""
    if current_user.role == RoleEnum.JOB_SEEKER:
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if not candidate:
            return []
        interviews = db.query(Interview).filter(
            Interview.candidate_id == candidate.id
        ).order_by(Interview.scheduled_time.asc()).all()
    elif current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            return []
        interviews = db.query(Interview).filter(
            Interview.recruiter_id == recruiter.id
        ).order_by(Interview.scheduled_time.asc()).all()
    else:  # ADMIN
        interviews = db.query(Interview).order_by(Interview.scheduled_time.asc()).all()

    return [serialize_interview(i) for i in interviews]

@router.get("/application/{application_id}", response_model=List[InterviewResponse])
def get_interviews_for_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve interviews associated with an application (authorized participants only)."""
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Permission check: must be the candidate, the recruiter, or admin
    is_owner_candidate = app_record.candidate.user_id == current_user.id
    is_owner_recruiter = app_record.job.recruiter.user_id == current_user.id
    is_admin = current_user.role == RoleEnum.ADMIN

    if not (is_owner_candidate or is_owner_recruiter or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to view this application's interviews."
        )

    interviews = db.query(Interview).filter(
        Interview.application_id == application_id
    ).order_by(Interview.scheduled_time.asc()).all()

    return [serialize_interview(i) for i in interviews]

@router.put("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: str,
    update_in: InterviewUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Reschedule or update interview details (meeting link, instructions, or cancellation)."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found."
        )

    if interview.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot modify interviews scheduled by another recruiter."
        )

    old_status = interview.status
    old_time = interview.scheduled_time
    old_type = interview.interview_type
    old_link = interview.meeting_link
    old_loc = interview.location

    if update_in.interview_type:
        interview.interview_type = update_in.interview_type
    if update_in.scheduled_time:
        interview.scheduled_time = update_in.scheduled_time
    if update_in.duration_minutes is not None:
        interview.duration_minutes = update_in.duration_minutes
    if update_in.meeting_link is not None:
        interview.meeting_link = update_in.meeting_link
    if update_in.location is not None:
        interview.location = update_in.location
    if update_in.instructions is not None:
        interview.instructions = update_in.instructions
    if update_in.status:
        interview.status = update_in.status
    if update_in.round_number is not None:
        interview.round_number = update_in.round_number
    if update_in.round_title is not None:
        interview.round_title = update_in.round_title
    if update_in.recording_enabled is not None:
        interview.recording_enabled = update_in.recording_enabled

    interview.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interview)

    status_changed_to_cancelled = (interview.status == "CANCELLED" and old_status != "CANCELLED")
    schedule_details_changed = (
        (interview.scheduled_time != old_time) or
        (interview.meeting_link != old_link) or
        (interview.location != old_loc) or
        (interview.interview_type != old_type)
    )

    # In-app notification if rescheduled or cancelled
    if status_changed_to_cancelled:
        notif_msg = f"Your interview for '{interview.application.job.title}' has been cancelled."
        notif_type = "INTERVIEW_CANCELLED"
    else:
        notif_msg = f"Your interview for '{interview.application.job.title}' has been updated to {interview.scheduled_time.strftime('%b %d, %Y at %H:%M UTC')}."
        notif_type = "INTERVIEW_RESCHEDULED"

    create_notification(
        db=db,
        user_id=interview.candidate.user_id,
        title="Interview Update",
        message=notif_msg,
        notification_type=notif_type,
        link="/dashboard?tab=interviews"
    )

    create_audit_log(
        db=db,
        actor_id=recruiter.user_id,
        action_type="INTERVIEW_UPDATE",
        target_resource="Interview",
        target_id=interview.id,
        details={"status": interview.status, "scheduled_time": interview.scheduled_time.isoformat()}
    )

    # Dispatch email if schedule changed or interview cancelled (prevent duplicate emails if details unchanged)
    candidate_user = interview.candidate.user if interview.candidate else None
    if candidate_user and candidate_user.email:
        job = interview.application.job if interview.application else None
        job_title = job.title if job else "Technical Interview"
        company_name = (
            job.company.name if (job and job.company and job.company.name)
            else (recruiter.company.name if (recruiter.company and recruiter.company.name) else "SkillSphere Partner")
        )
        recruiter_name = recruiter.user.name if (recruiter.user and recruiter.user.name) else None
        recruiter_email = recruiter.user.email if (recruiter.user and recruiter.user.email) else None

        if status_changed_to_cancelled:
            try:
                res = EmailService.send_interview_cancellation_email(
                    to_email=candidate_user.email,
                    candidate_name=candidate_user.name,
                    job_title=job_title,
                    company_name=company_name,
                    scheduled_time=interview.scheduled_time,
                    recruiter_name=recruiter_name,
                    reason=interview.instructions
                )
                if res.get("delivered") or res.get("status") == "delivered":
                    interview.email_status = "ACCEPTED_BY_BREVO"
                    interview.brevo_message_id = res.get("message_id")
                    interview.email_sent_at = datetime.now(timezone.utc)
                    interview.email_error_message = None
                else:
                    interview.email_status = "FAILED"
                    interview.email_error_message = str(res.get("detail") or "Brevo API delivery rejection")
            except Exception as e:
                interview.email_status = "FAILED"
                interview.email_error_message = str(e)
            db.commit()
            db.refresh(interview)

        elif schedule_details_changed and interview.status != "CANCELLED":
            changes = []
            if interview.scheduled_time != old_time:
                changes.append(f"Scheduled time moved from {old_time.strftime('%b %d, %Y %H:%M UTC')} to {interview.scheduled_time.strftime('%b %d, %Y %H:%M UTC')}")
            if interview.meeting_link != old_link:
                changes.append("Updated meeting connection link")
            if interview.location != old_loc:
                changes.append("Updated interview location")
            if interview.interview_type != old_type:
                changes.append(f"Format updated to {interview.interview_type}")
            summary = "; ".join(changes) if changes else "Schedule details updated."

            try:
                res = EmailService.send_interview_update_email(
                    to_email=candidate_user.email,
                    candidate_name=candidate_user.name,
                    job_title=job_title,
                    company_name=company_name,
                    interview_type=interview.interview_type,
                    scheduled_time=interview.scheduled_time,
                    duration_minutes=interview.duration_minutes,
                    meeting_link=interview.meeting_link,
                    location=interview.location,
                    instructions=interview.instructions,
                    recruiter_name=recruiter_name,
                    recruiter_email=recruiter_email,
                    changes_summary=summary
                )
                if res.get("delivered") or res.get("status") == "delivered":
                    interview.email_status = "ACCEPTED_BY_BREVO"
                    interview.brevo_message_id = res.get("message_id")
                    interview.email_sent_at = datetime.now(timezone.utc)
                    interview.email_error_message = None
                else:
                    interview.email_status = "FAILED"
                    interview.email_error_message = str(res.get("detail") or "Brevo API delivery rejection")
            except Exception as e:
                interview.email_status = "FAILED"
                interview.email_error_message = str(e)
            db.commit()
            db.refresh(interview)

    return serialize_interview(interview)

@router.post("/{interview_id}/cancel", response_model=InterviewResponse)
def cancel_interview(
    interview_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled interview, updates status and notifies candidate."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found."
        )
    if interview.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot cancel an interview scheduled by another recruiter."
        )

    interview.status = "CANCELLED"
    interview.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interview)

    if interview.candidate and interview.candidate.user_id:
        create_notification(
            db=db,
            user_id=interview.candidate.user_id,
            title="Interview Cancelled",
            message="Your scheduled interview has been cancelled.",
            notification_type="INTERVIEW_CANCELLED",
            link="/dashboard?tab=interviews"
        )
    return serialize_interview(interview)

@router.post("/{interview_id}/resend-email", response_model=InterviewResponse)
def resend_interview_email(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Safely re-trigger interview invitation email dispatch without modifying interview record."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    # Permissions: recruiter who owns it or admin
    if current_user.role != RoleEnum.ADMIN:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or interview.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only resend invitations for your own interviews.")

    candidate_user = interview.candidate.user if interview.candidate else None
    if not candidate_user or not candidate_user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate email address not found.")

    job = interview.application.job if interview.application else None
    job_title = job.title if job else "Technical Interview"
    company_name = job.company.name if (job and job.company and job.company.name) else "SkillSphere Partner"
    recruiter_name = interview.recruiter.user.name if (interview.recruiter and interview.recruiter.user) else None
    recruiter_email = interview.recruiter.user.email if (interview.recruiter and interview.recruiter.user) else None

    try:
        email_res = EmailService.send_interview_invitation_email(
            to_email=candidate_user.email,
            candidate_name=candidate_user.name,
            job_title=job_title,
            company_name=company_name,
            interview_type=interview.interview_type,
            scheduled_time=interview.scheduled_time,
            duration_minutes=interview.duration_minutes,
            meeting_link=interview.meeting_link,
            location=interview.location,
            instructions=interview.instructions,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email
        )
        if email_res.get("delivered") or email_res.get("status") == "delivered":
            interview.email_status = "ACCEPTED_BY_BREVO"
            interview.brevo_message_id = email_res.get("message_id")
            interview.email_sent_at = datetime.now(timezone.utc)
            interview.email_error_message = None
        else:
            interview.email_status = "FAILED"
            interview.email_error_message = str(email_res.get("detail") or "Brevo API delivery rejection")
    except Exception as e:
        interview.email_status = "FAILED"
        interview.email_error_message = str(e)

    db.commit()
    db.refresh(interview)
    return serialize_interview(interview)


# ============================================================================
# LIVE VIDEO INTERVIEW ROOM & LIVEKIT TOKEN ENDPOINTS
# ============================================================================

@router.post("/{interview_id}/room-token", response_model=InterviewRoomTokenResponse)
def get_interview_room_token(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a secure short-lived LiveKit WebRTC room token for the interview room.
    Ensures that only the assigned recruiter, candidate, or admin can enter.
    Candidate entry starts in the waiting room until admitted by recruiter.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    is_recruiter = False
    is_candidate = False
    is_admin = current_user.role == RoleEnum.ADMIN

    if current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if recruiter and interview.recruiter_id == recruiter.id:
            is_recruiter = True
            if not interview.recruiter_joined_at:
                interview.recruiter_joined_at = datetime.now(timezone.utc)
                db.commit()

    elif current_user.role == RoleEnum.JOB_SEEKER:
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if candidate and interview.candidate_id == candidate.id:
            is_candidate = True
            if not interview.candidate_joined_at:
                interview.candidate_joined_at = datetime.now(timezone.utc)
                db.commit()

    if not (is_recruiter or is_candidate or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not an authorized participant in this interview."
        )

    # Ensure interview has a room_id
    if not interview.room_id:
        interview.room_id = f"room_{uuid.uuid4().hex[:12]}"
        db.commit()

    role_str = "recruiter" if (is_recruiter or is_admin) else "candidate"
    token_data = LiveKitService.generate_room_token(
        room_name=interview.room_id,
        user_id=current_user.id,
        user_name=current_user.name,
        role=role_str
    )

    # Recruiters are auto-admitted; candidates are admitted if is_admitted is True
    is_admitted = True if (is_recruiter or is_admin) else bool(interview.is_admitted)

    return InterviewRoomTokenResponse(
        token=token_data["token"],
        server_url=token_data["server_url"],
        room_name=token_data["room_name"],
        identity=token_data["identity"],
        display_name=token_data["display_name"],
        role=token_data["role"],
        is_recruiter=(is_recruiter or is_admin),
        is_admitted=is_admitted,
        expires_at=token_data["expires_at"]
    )

@router.get("/{interview_id}/room-status", response_model=InterviewRoomStatusResponse)
def get_room_status(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve real-time room status, admission state, and mutual consent status.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    consent_info = LiveKitService.verify_recording_consents(db, interview.id)
    both_consented_bool = consent_info.get("both_consented", False) if isinstance(consent_info, dict) else bool(consent_info)

    candidate_name = interview.candidate.user.name if (interview.candidate and interview.candidate.user) else None
    recruiter_name = interview.recruiter.user.name if (interview.recruiter and interview.recruiter.user) else None
    job_title = interview.application.job.title if (interview.application and interview.application.job) else None

    return InterviewRoomStatusResponse(
        interview_id=interview.id,
        room_id=interview.room_id or interview.id,
        room_status=interview.room_status or "WAITING",
        is_admitted=bool(interview.is_admitted),
        recording_enabled=bool(interview.recording_enabled),
        recording_status=interview.recording_status or "NOT_RECORDED",
        both_consented_recording=both_consented_bool,
        scheduled_time=interview.scheduled_time,
        duration_minutes=interview.duration_minutes,
        candidate_name=candidate_name,
        recruiter_name=recruiter_name,
        job_title=job_title,
        interview_mode=getattr(interview, "interview_mode", "HUMAN") or "HUMAN",
        ai_takeover_status=getattr(interview, "ai_takeover_status", "AI_ACTIVE") or "AI_ACTIVE",
        current_question_index=getattr(interview, "current_question_index", 0) or 0
    )

@router.post("/{interview_id}/admission", response_model=InterviewRoomStatusResponse)
def admit_participant(
    interview_id: str,
    admitted: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recruiter admits candidate from the waiting room into the active interview room.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    if current_user.role != RoleEnum.ADMIN:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or interview.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the recruiter can admit candidates.")

    interview.is_admitted = admitted
    if admitted and interview.room_status == "WAITING":
        interview.room_status = "IN_PROGRESS"
        interview.room_started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interview)

    return get_room_status(interview.id, current_user, db)

@router.post("/{interview_id}/room-start")
def start_interview_room(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    interview.room_status = "IN_PROGRESS"
    if not interview.room_started_at:
        interview.room_started_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "IN_PROGRESS", "room_started_at": interview.room_started_at}

@router.post("/{interview_id}/room-end")
def end_interview_room(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    interview.room_status = "COMPLETED"
    interview.status = "COMPLETED"
    interview.room_ended_at = datetime.now(timezone.utc)

    # Stop active recording if running
    if interview.recording_status == "RECORDING":
        try:
            LiveKitService.stop_recording_and_transfer_to_cloudinary(db, interview.id)
        except Exception:
            pass

    db.commit()
    return {"status": "COMPLETED", "room_ended_at": interview.room_ended_at}

# ============================================================================
# RECORDING & INFORMED CONSENT ENDPOINTS
# ============================================================================

@router.post("/{interview_id}/consent", response_model=RecordingConsentResponse)
def record_interview_consent(
    interview_id: str,
    req: RecordingConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record participant's explicit informed consent to be recorded.
    Tracks user ID, role, timestamp, IP, and user-agent.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    role = "recruiter" if current_user.role in [RoleEnum.RECRUITER, RoleEnum.ADMIN] else "candidate"
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    consent = LiveKitService.record_consent(
        db=db,
        interview_id=interview.id,
        user_id=current_user.id,
        role=role,
        consent_granted=req.consent_granted,
        ip_address=client_ip,
        user_agent=user_agent
    )

    consent_info = LiveKitService.verify_recording_consents(db, interview.id)
    both_consented_bool = consent_info.get("both_consented", False) if isinstance(consent_info, dict) else bool(consent_info)

    return RecordingConsentResponse(
        interview_id=interview.id,
        user_id=current_user.id,
        role=role,
        consent_granted=consent.consent_granted,
        consent_timestamp=consent.consent_timestamp,
        both_consented=both_consented_bool
    )

@router.post("/{interview_id}/recording/start", response_model=InterviewRecordingResponse)
def start_interview_recording(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start recording the live interview room.
    Strictly verifies mutual informed consent before recording starts.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    if current_user.role != RoleEnum.ADMIN:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or interview.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the assigned recruiter can start recording.")

    consent_info = LiveKitService.verify_recording_consents(db, interview.id)
    both_consented_bool = consent_info.get("both_consented", False) if isinstance(consent_info, dict) else bool(consent_info)
    if not both_consented_bool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start recording: Both candidate and recruiter must give explicit consent first."
        )

    try:
        recording = LiveKitService.start_recording(db, interview, current_user)
        return InterviewRecordingResponse(
            id=recording.id,
            interview_id=recording.interview_id,
            media_asset_id=recording.media_asset_id,
            egress_id=recording.egress_id,
            status=recording.status,
            recording_consent_recruiter=recording.recording_consent_recruiter,
            recording_consent_candidate=recording.recording_consent_candidate,
            started_at=recording.started_at,
            stopped_at=recording.stopped_at,
            duration_seconds=recording.duration_seconds,
            file_size_bytes=recording.file_size_bytes or 0,
            playback_url=None,
            thumbnail_url=None,
            created_at=recording.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{interview_id}/recording/stop", response_model=InterviewRecordingResponse)
def stop_interview_recording(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop active interview recording and coordinate background transfer into Cloudinary.
    """
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    if current_user.role != RoleEnum.ADMIN:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or interview.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only the assigned recruiter can stop recording.")

    recording = LiveKitService.stop_recording_and_transfer_to_cloudinary(db, interview, current_user)

    playback_url = None
    thumbnail_url = None
    if recording.media_asset:
        playback_url = CloudinaryService.generate_signed_playback_url(recording.media_asset.public_id, "video")
        thumbnail_url = CloudinaryService.generate_thumbnail_url(recording.media_asset.public_id)

    return InterviewRecordingResponse(
        id=recording.id,
        interview_id=recording.interview_id,
        media_asset_id=recording.media_asset_id,
        egress_id=recording.egress_id,
        status=recording.status,
        recording_consent_recruiter=recording.recording_consent_recruiter,
        recording_consent_candidate=recording.recording_consent_candidate,
        started_at=recording.started_at,
        stopped_at=recording.stopped_at,
        duration_seconds=recording.duration_seconds,
        file_size_bytes=recording.file_size_bytes or 0,
        playback_url=playback_url,
        thumbnail_url=thumbnail_url,
        created_at=recording.created_at
    )

@router.get("/{interview_id}/recordings", response_model=List[InterviewRecordingResponse])
def get_interview_recordings(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve interview recordings with signed playback URLs.
    Restricted to recruiters and admins. Candidates are strictly forbidden.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Candidates cannot access recruiter interview recordings.")

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    recordings = db.query(InterviewRecording).filter(InterviewRecording.interview_id == interview.id).all()
    results = []
    for rec in recordings:
        playback_url = None
        thumbnail_url = None
        if rec.media_asset:
            playback_url = CloudinaryService.generate_signed_playback_url(rec.media_asset.public_id, "video")
            thumbnail_url = CloudinaryService.generate_thumbnail_url(rec.media_asset.public_id)
        results.append(InterviewRecordingResponse(
            id=rec.id,
            interview_id=rec.interview_id,
            media_asset_id=rec.media_asset_id,
            egress_id=rec.egress_id,
            status=rec.status,
            recording_consent_recruiter=rec.recording_consent_recruiter,
            recording_consent_candidate=rec.recording_consent_candidate,
            started_at=rec.started_at,
            stopped_at=rec.stopped_at,
            duration_seconds=rec.duration_seconds,
            file_size_bytes=rec.file_size_bytes or 0,
            playback_url=playback_url,
            thumbnail_url=thumbnail_url,
            created_at=rec.created_at
        ))
    return results

@router.post("/{interview_id}/recording/retry", response_model=InterviewRecordingResponse)
def retry_failed_recording_upload(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry transferring a failed recording into Cloudinary."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    rec = db.query(InterviewRecording).filter(
        InterviewRecording.interview_id == interview.id,
        InterviewRecording.status == "FAILED"
    ).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No failed recording found to retry.")

    # Re-trigger stop/transfer
    LiveKitService.stop_recording_and_transfer_to_cloudinary(db, interview.id)
    return stop_interview_recording(interview.id, current_user, db)

# ============================================================================
# STRUCTURED RECRUITER SCORECARD ENDPOINTS
# ============================================================================

@router.post("/{interview_id}/scorecard", response_model=InterviewScorecardResponse)
def submit_interview_scorecard(
    interview_id: str,
    card_in: InterviewScorecardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit structured recruiter evaluation scorecard for an interview.
    Grades technical knowledge, communication, problem-solving, role-specific skills, and cultural alignment.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters can submit interview scorecards.")

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    if not recruiter:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiter profile not found.")

    scores = [
        card_in.technical_knowledge_score,
        card_in.communication_score,
        card_in.problem_solving_score,
        card_in.role_specific_score,
        card_in.cultural_alignment_score
    ]
    avg_score = round(sum(scores) / len(scores), 2)

    scorecard = db.query(InterviewScorecard).filter(InterviewScorecard.interview_id == interview.id).first()
    if not scorecard:
        scorecard = InterviewScorecard(
            interview_id=interview.id,
            recruiter_id=recruiter.id,
            application_id=interview.application_id,
            technical_knowledge_score=card_in.technical_knowledge_score,
            technical_evidence_notes=card_in.technical_evidence_notes,
            communication_score=card_in.communication_score,
            communication_evidence_notes=card_in.communication_evidence_notes,
            problem_solving_score=card_in.problem_solving_score,
            problem_solving_notes=card_in.problem_solving_notes,
            role_specific_score=card_in.role_specific_score,
            role_specific_notes=card_in.role_specific_notes,
            cultural_alignment_score=card_in.cultural_alignment_score,
            cultural_alignment_notes=card_in.cultural_alignment_notes,
            overall_score=avg_score,
            overall_recommendation=card_in.overall_recommendation,
            strengths=card_in.strengths,
            improvement_areas=card_in.improvement_areas,
            private_evaluation_notes=card_in.private_evaluation_notes,
            is_submitted=True
        )
        db.add(scorecard)
    else:
        scorecard.technical_knowledge_score = card_in.technical_knowledge_score
        scorecard.technical_evidence_notes = card_in.technical_evidence_notes
        scorecard.communication_score = card_in.communication_score
        scorecard.communication_evidence_notes = card_in.communication_evidence_notes
        scorecard.problem_solving_score = card_in.problem_solving_score
        scorecard.problem_solving_notes = card_in.problem_solving_notes
        scorecard.role_specific_score = card_in.role_specific_score
        scorecard.role_specific_notes = card_in.role_specific_notes
        scorecard.cultural_alignment_score = card_in.cultural_alignment_score
        scorecard.cultural_alignment_notes = card_in.cultural_alignment_notes
        scorecard.overall_score = avg_score
        scorecard.overall_recommendation = card_in.overall_recommendation
        scorecard.strengths = card_in.strengths
        scorecard.improvement_areas = card_in.improvement_areas
        scorecard.private_evaluation_notes = card_in.private_evaluation_notes
        scorecard.is_submitted = True

    db.commit()
    db.refresh(scorecard)

    return InterviewScorecardResponse(
        id=scorecard.id,
        interview_id=scorecard.interview_id,
        recruiter_id=scorecard.recruiter_id,
        application_id=scorecard.application_id,
        technical_knowledge_score=scorecard.technical_knowledge_score,
        technical_evidence_notes=scorecard.technical_evidence_notes,
        communication_score=scorecard.communication_score,
        communication_evidence_notes=scorecard.communication_evidence_notes,
        problem_solving_score=scorecard.problem_solving_score,
        problem_solving_notes=scorecard.problem_solving_notes,
        role_specific_score=scorecard.role_specific_score,
        role_specific_notes=scorecard.role_specific_notes,
        cultural_alignment_score=scorecard.cultural_alignment_score,
        cultural_alignment_notes=scorecard.cultural_alignment_notes,
        overall_score=scorecard.overall_score,
        overall_recommendation=scorecard.overall_recommendation,
        strengths=scorecard.strengths,
        improvement_areas=scorecard.improvement_areas,
        private_evaluation_notes=scorecard.private_evaluation_notes,
        is_submitted=scorecard.is_submitted,
        created_at=scorecard.created_at,
        updated_at=scorecard.updated_at,
        recruiter_name=recruiter.user.name if (recruiter and recruiter.user) else None
    )

@router.get("/{interview_id}/scorecard", response_model=Optional[InterviewScorecardResponse])
def get_interview_scorecard(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve scorecard for an interview.
    Candidates are strictly forbidden from viewing internal recruiter scorecards.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Candidates cannot access internal recruiter scorecards."
        )

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    scorecard = db.query(InterviewScorecard).filter(InterviewScorecard.interview_id == interview.id).first()
    if not scorecard:
        return None

    return InterviewScorecardResponse(
        id=scorecard.id,
        interview_id=scorecard.interview_id,
        recruiter_id=scorecard.recruiter_id,
        application_id=scorecard.application_id,
        technical_knowledge_score=scorecard.technical_knowledge_score,
        technical_evidence_notes=scorecard.technical_evidence_notes,
        communication_score=scorecard.communication_score,
        communication_evidence_notes=scorecard.communication_evidence_notes,
        problem_solving_score=scorecard.problem_solving_score,
        problem_solving_notes=scorecard.problem_solving_notes,
        role_specific_score=scorecard.role_specific_score,
        role_specific_notes=scorecard.role_specific_notes,
        cultural_alignment_score=scorecard.cultural_alignment_score,
        cultural_alignment_notes=scorecard.cultural_alignment_notes,
        overall_score=scorecard.overall_score,
        overall_recommendation=scorecard.overall_recommendation,
        strengths=scorecard.strengths,
        improvement_areas=scorecard.improvement_areas,
        private_evaluation_notes=scorecard.private_evaluation_notes,
        is_submitted=scorecard.is_submitted,
        created_at=scorecard.created_at,
        updated_at=scorecard.updated_at,
        recruiter_name=scorecard.recruiter.user.name if (scorecard.recruiter and scorecard.recruiter.user) else None
    )

# ============================================================================
# AI INTERVIEW INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/{interview_id}/ai-transcript", response_model=InterviewTranscriptResponse)
def generate_interview_ai_transcript(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate or retrieve AI-powered transcript, summary, topic breakdown, and draft feedback.
    Labeled as assistant draft requiring recruiter approval.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters can access AI interview intelligence.")

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    transcript = InterviewAIService.generate_interview_intelligence(db, interview, current_user)
    return transcript

@router.post("/{interview_id}/ai-transcript/approve", response_model=InterviewTranscriptResponse)
def approve_interview_ai_transcript(
    interview_id: str,
    req: ApproveTranscriptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recruiter reviews, edits, and approves AI assistant draft feedback.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters can approve AI feedback.")

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    transcript = db.query(InterviewTranscript).filter(InterviewTranscript.interview_id == interview.id).first()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found. Please generate it first.")

    approved = InterviewAIService.approve_transcript_and_feedback(
        db=db,
        transcript_id=transcript.id,
        recruiter_id=current_user.id,
        edited_summary=req.edited_summary,
        edited_feedback=req.edited_feedback
    )
    return approved

# ============================================================================
# CENTRALIZED CANDIDATE RECRUITMENT DOSSIER
# ============================================================================

@router.get("/candidate/{candidate_id}/dossier")
def get_candidate_dossier(
    candidate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Centralized candidate evaluation dossier for recruiters:
    Candidate profile, resume, MCQ assessment results, video assessment responses,
    interview recordings, and scorecards in one holistic view.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters can view candidate dossiers.")

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    # 1. Candidate Info
    user = candidate.user

    # 2. Resumes
    resumes_list = []
    for r in getattr(candidate, "resumes", []):
        parsed = getattr(r, "parsed_data", {})
        skills = []
        if isinstance(parsed, dict):
            skills = parsed.get("skills", [])
        resumes_list.append({
            "id": r.id,
            "filename": getattr(r, "file_name", getattr(r, "original_filename", "Resume.pdf")),
            "file_url": getattr(r, "file_path", None),
            "parsed_skills": skills,
            "created_at": getattr(r, "upload_date", getattr(r, "created_at", None))
        })

    # 3. MCQ Assessments
    mcq_assessments = []
    assignments = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.candidate_id == candidate.id
    ).all()
    for a in assignments:
        mcq_assessments.append({
            "id": a.id,
            "assessment_title": a.assessment.title if a.assessment else "Technical Assessment",
            "score": a.score,
            "passed": a.passed,
            "status": a.status,
            "review_status": a.review_status,
            "completed_at": a.completed_at
        })

    # 4. Video Assessments
    video_assessments = []
    vid_assignments = getattr(candidate, "video_assignments", [])
    for va in vid_assignments:
        responses = []
        for r in getattr(va, "responses", []):
            purl = None
            if r.media_asset:
                purl = CloudinaryService.generate_signed_playback_url(r.media_asset.public_id, "video")
            responses.append({
                "question": r.question.question_text if r.question else "",
                "duration_seconds": r.duration_seconds,
                "retake_count": r.retake_count,
                "playback_url": purl,
                "rating": r.recruiter_rating,
                "notes": r.recruiter_notes
            })
        video_assessments.append({
            "id": va.id,
            "title": va.video_assessment.title if va.video_assessment else "Video Assessment",
            "status": va.status,
            "review_status": va.review_status,
            "overall_score": va.overall_score,
            "responses": responses
        })

    # 5. Interviews, Recordings & Scorecards
    interviews = db.query(Interview).filter(Interview.candidate_id == candidate.id).all()
    interview_history = []
    for i in interviews:
        recordings = []
        for rec in getattr(i, "recordings", []):
            purl = None
            if rec.media_asset:
                purl = CloudinaryService.generate_signed_playback_url(rec.media_asset.public_id, "video")
            recordings.append({
                "id": rec.id,
                "status": rec.status,
                "duration_seconds": rec.duration_seconds,
                "playback_url": purl
            })
        scorecard = db.query(InterviewScorecard).filter(InterviewScorecard.interview_id == i.id).first()
        sc_data = None
        if scorecard:
            sc_data = {
                "overall_score": scorecard.overall_score,
                "recommendation": scorecard.overall_recommendation,
                "technical_score": scorecard.technical_knowledge_score,
                "communication_score": scorecard.communication_score,
                "problem_solving_score": scorecard.problem_solving_score,
                "strengths": scorecard.strengths,
                "improvement_areas": scorecard.improvement_areas
            }
        interview_history.append({
            "id": i.id,
            "round_number": i.round_number,
            "round_title": i.round_title,
            "scheduled_time": i.scheduled_time,
            "status": i.status,
            "recordings": recordings,
            "scorecard": sc_data
        })

    return {
        "candidate": {
            "id": candidate.id,
            "name": user.name if user else "",
            "email": user.email if user else "",
            "phone": getattr(candidate, "phone", None),
            "experience_years": getattr(candidate, "experience_years", 0),
            "skills": getattr(candidate, "skills", [])
        },
        "resumes": resumes_list,
        "mcq_assessments": mcq_assessments,
        "video_assessments": video_assessments,
        "interviews": interview_history
    }


# ============================================================================
# AI INTERVIEW HUB, LIVEKIT AGENT & EVALUATION WORKFLOWS
# ============================================================================

@router.post("/ai-questions/generate", response_model=List[Dict[str, Any]])
def generate_ai_questions(
    req: GenerateAIQuestionsRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Generate interview questions tailored to job requirements, difficulty, and categories."""
    job_title = req.job_title
    job_desc = req.job_description
    skills = req.required_skills or []

    if req.job_id:
        job = db.query(Job).filter(Job.id == req.job_id).first()
        if job:
            job_title = job_title or job.title
            job_desc = job_desc or job.description
            if not skills and hasattr(job, "skills") and job.skills:
                skills = [s.name for s in job.skills]
    elif req.application_id:
        app_rec = db.query(Application).filter(Application.id == req.application_id).first()
        if app_rec and app_rec.job:
            job_title = job_title or app_rec.job.title
            job_desc = job_desc or app_rec.job.description
            if not skills and hasattr(app_rec.job, "skills") and app_rec.job.skills:
                skills = [s.name for s in app_rec.job.skills]
    elif req.interview_id:
        interview = db.query(Interview).filter(Interview.id == req.interview_id).first()
        if interview and interview.application and interview.application.job:
            job_title = job_title or interview.application.job.title
            job_desc = job_desc or interview.application.job.description
            if not skills and hasattr(interview.application.job, "skills") and interview.application.job.skills:
                skills = [s.name for s in interview.application.job.skills]

    questions = InterviewAIService.generate_ai_interview_questions(
        job_title=job_title or "Software Engineer",
        job_description=job_desc,
        skills=skills,
        difficulty=req.difficulty or "INTERMEDIATE",
        question_count=req.question_count or 5,
        categories=req.categories
    )
    return questions


@router.post("/{interview_id}/configure-ai", response_model=InterviewResponse)
def configure_ai_interview(
    interview_id: str,
    req: InterviewConfigureAIRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Configure AI or Hybrid interview mode with questions, voice, and rules."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    interview.interview_mode = req.interview_mode
    if req.duration_minutes:
        interview.duration_minutes = req.duration_minutes
    interview.ai_config_json = {
        "difficulty": req.difficulty,
        "question_count": req.question_count,
        "categories": req.categories or [],
        "voice": req.voice or "alloy",
        "allow_recruiter_takeover": req.allow_recruiter_takeover,
        "prep_time_seconds": req.prep_time_seconds
    }

    if req.questions:
        db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).delete()
        for idx, q_data in enumerate(req.questions):
            new_q = InterviewQuestion(
                interview_id=interview.id,
                question_text=q_data.question_text,
                question_type=q_data.question_type or "TECHNICAL",
                source=q_data.source or "CUSTOM",
                sequence_number=q_data.sequence_number or (idx + 1),
                expected_concepts=q_data.expected_concepts or [],
                max_duration_seconds=q_data.max_duration_seconds or 180
            )
            db.add(new_q)

    db.commit()
    db.refresh(interview)
    return serialize_interview(interview)


@router.get("/{interview_id}/questions", response_model=List[InterviewQuestionResponse])
def get_interview_questions(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve configured questions for this interview."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id
    ).order_by(InterviewQuestion.sequence_number.asc()).all()
    return questions


@router.put("/{interview_id}/questions", response_model=List[InterviewQuestionResponse])
def update_interview_questions(
    interview_id: str,
    questions_in: List[InterviewQuestionCreate],
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Update or reorder interview questions before launch."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).delete()
    created = []
    for idx, q in enumerate(questions_in):
        record = InterviewQuestion(
            interview_id=interview.id,
            question_text=q.question_text,
            question_type=q.question_type,
            source=q.source,
            sequence_number=idx + 1,
            expected_concepts=q.expected_concepts or [],
            max_duration_seconds=q.max_duration_seconds
        )
        db.add(record)
        created.append(record)
    db.commit()
    for c in created:
        db.refresh(c)
    return created


@router.get("/{interview_id}/ai-state")
def get_ai_state(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active state of the AI Interviewer agent in the room."""
    try:
        return AIInterviewerAgent.get_interview_state(db, interview_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{interview_id}/ai-state/advance")
def advance_ai_state(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Advance to next AI question."""
    try:
        return AIInterviewerAgent.advance_question(db, interview_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{interview_id}/hybrid/takeover")
def hybrid_takeover(
    interview_id: str,
    req: HybridTakeoverRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Toggle recruiter speaking takeover vs AI agent conversation."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    updated = InterviewAIService.set_takeover_state(db, interview.id, req.takeover)
    return {"status": "ok", "ai_takeover_status": updated.ai_takeover_status}


@router.post("/{interview_id}/ai-responses", response_model=List[InterviewResponseItemResponse])
def submit_ai_responses(
    interview_id: str,
    responses_in: List[InterviewResponseItemCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store transcript and response evaluations per question."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    saved_items = []
    for r_item in responses_in:
        resp = db.query(InterviewResponseModel).filter(
            InterviewResponseModel.interview_id == interview.id,
            InterviewResponseModel.question_id == r_item.question_id
        ).first()
        if not resp:
            resp = InterviewResponseModel(
                interview_id=interview.id,
                question_id=r_item.question_id,
                transcript=r_item.transcript,
                response_duration=r_item.response_duration or 0.0,
                evaluation=r_item.evaluation or "Candidate responded with structured explanation.",
                strengths=r_item.strengths or "Clear delivery and domain familiarity.",
                weaknesses=r_item.weaknesses or "Could expand on production metric trade-offs.",
                score=r_item.score or 4.0
            )
            db.add(resp)
        else:
            resp.transcript = r_item.transcript
            resp.response_duration = r_item.response_duration or resp.response_duration
            if r_item.score is not None:
                resp.score = r_item.score
        saved_items.append(resp)

    db.commit()
    for s in saved_items:
        db.refresh(s)
    return saved_items


@router.post("/{interview_id}/evaluation/generate", response_model=InterviewEvaluationResponse)
def generate_ai_evaluation(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate structured multi-competency AI evaluation report."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    evaluation = InterviewAIService.evaluate_ai_interview(db, interview.id)
    return evaluation


@router.get("/{interview_id}/evaluation", response_model=InterviewEvaluationResponse)
def get_ai_evaluation(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve AI evaluation (strictly recruiter and admin only)."""
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Evaluations are strictly confidential for recruiter review."
        )

    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    evaluation = db.query(InterviewEvaluation).filter(
        InterviewEvaluation.interview_id == interview.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI evaluation not yet generated.")
    return evaluation


@router.put("/{interview_id}/evaluation", response_model=InterviewEvaluationResponse)
def update_ai_evaluation(
    interview_id: str,
    eval_in: InterviewEvaluationUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Recruiter review and score override for AI evaluation."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    if interview.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    evaluation = db.query(InterviewEvaluation).filter(
        InterviewEvaluation.interview_id == interview.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    if eval_in.overall_score is not None:
        evaluation.overall_score = eval_in.overall_score
    if eval_in.competency_scores is not None:
        evaluation.competency_scores = eval_in.competency_scores
    if eval_in.strengths is not None:
        evaluation.strengths = eval_in.strengths
    if eval_in.weaknesses is not None:
        evaluation.weaknesses = eval_in.weaknesses
    if eval_in.recommendations is not None:
        evaluation.recommendations = eval_in.recommendations
    if eval_in.review_status is not None:
        evaluation.review_status = eval_in.review_status
    if eval_in.recruiter_notes is not None:
        evaluation.recruiter_notes = eval_in.recruiter_notes

    evaluation.reviewed_by = recruiter.user_id
    evaluation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.post("/{interview_id}/archive-recording")
def archive_interview_recording(
    interview_id: str,
    recording_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive interview recording to Cloudinary folder skillsphere/ai-interviews/."""
    interview = db.query(Interview).filter(
        (Interview.id == interview_id) | (Interview.room_id == interview_id)
    ).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    result = AIInterviewerAgent.finalize_and_archive_to_cloudinary(
        db=db,
        interview_id=interview.id,
        recording_file_url=recording_url
    )
    return result

