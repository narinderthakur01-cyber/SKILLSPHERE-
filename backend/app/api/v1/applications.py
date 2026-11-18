import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_candidate, get_current_recruiter, get_current_user
from app.models.models import (
    Application, Job, Resume, Candidate, Recruiter, User,
    ApplicationStatusEnum, JobStatusEnum, ApplicationHistory, RoleEnum,
    CandidateAssessmentAssignment
)
from app.schemas.schemas import (
    ApplicationCreate, ApplicationStatusUpdate, ApplicationResponse,
    JobResponse, CandidateProfileResponse, ResumeResponse, CompanyResponse,
    ApplicationHistoryResponse, InterviewResponse, CandidateEvaluationResponse
)
from app.services.activity_service import create_notification, create_audit_log
from app.services.email_service import EmailService

logger = logging.getLogger("skillsphere.applications")

router = APIRouter(tags=["Applications"])

def serialize_history_item(h: ApplicationHistory) -> ApplicationHistoryResponse:
    changed_by_name = h.changed_by.name if h.changed_by else "System"
    return ApplicationHistoryResponse(
        id=h.id,
        from_status=h.from_status,
        to_status=h.to_status,
        changed_by_name=changed_by_name,
        notes=h.notes,
        created_at=h.created_at
    )

def serialize_application(app_record: Application, is_recruiter: bool = False) -> ApplicationResponse:
    """Helper to serialize an Application model into ApplicationResponse."""
    job_data = None
    if app_record.job:
        company_data = None
        if app_record.job.company:
            company_data = CompanyResponse.model_validate(app_record.job.company)
        skills = [js.skill.skill_name.title() for js in app_record.job.job_skills if js.skill]
        job_data = JobResponse(
            id=app_record.job.id,
            title=app_record.job.title,
            description=app_record.job.description,
            department=app_record.job.department,
            location=app_record.job.location,
            experience_min=app_record.job.experience_min,
            experience_max=app_record.job.experience_max,
            job_type=app_record.job.job_type,
            salary_min=app_record.job.salary_min,
            salary_max=app_record.job.salary_max,
            status=app_record.job.status,
            created_at=app_record.job.created_at,
            company=company_data,
            required_skills=skills
        )

    cand_data = None
    if app_record.candidate:
        cand_skills = [s.skill_name.title() for s in app_record.candidate.skills]
        cand_data = CandidateProfileResponse(
            id=app_record.candidate.id,
            user_id=app_record.candidate.user_id,
            name=app_record.candidate.user.name,
            email=app_record.candidate.user.email,
            phone=app_record.candidate.phone,
            title=app_record.candidate.title,
            location=app_record.candidate.location,
            bio=app_record.candidate.bio,
            education=app_record.candidate.education or [],
            experience=app_record.candidate.experience or [],
            total_years_exp=app_record.candidate.total_years_exp or 0.0,
            skills=cand_skills
        )

    resume_data = None
    if app_record.resume:
        resume_data = ResumeResponse.model_validate(app_record.resume)

    # History entries
    history_data = [serialize_history_item(h) for h in sorted(app_record.history, key=lambda x: x.created_at)]

    # Interviews
    interviews_data = []
    for i in app_record.interviews:
        interviews_data.append(InterviewResponse(
            id=i.id,
            application_id=i.application_id,
            recruiter_id=i.recruiter_id,
            candidate_id=i.candidate_id,
            interview_type=i.interview_type,
            scheduled_time=i.scheduled_time,
            duration_minutes=i.duration_minutes,
            meeting_link=i.meeting_link,
            location=i.location,
            instructions=i.instructions,
            status=i.status,
            created_at=i.created_at,
            updated_at=i.updated_at,
            job_title=app_record.job.title if app_record.job else None,
            candidate_name=app_record.candidate.user.name if app_record.candidate and app_record.candidate.user else None
        ))

    # Evaluations (Recruiter only)
    evaluations_data = []
    if is_recruiter:
        for e in app_record.evaluations:
            overall_avg = round((e.technical_score + e.communication_score + e.experience_score) / 3.0, 2)
            evaluations_data.append(CandidateEvaluationResponse(
                id=e.id,
                application_id=e.application_id,
                recruiter_id=e.recruiter_id,
                interview_id=e.interview_id,
                technical_score=e.technical_score,
                communication_score=e.communication_score,
                experience_score=e.experience_score,
                overall_score=overall_avg,
                overall_recommendation=e.overall_recommendation,
                interview_feedback=e.interview_feedback,
                internal_notes=e.internal_notes,
                created_at=e.created_at,
                updated_at=e.updated_at,
                recruiter_name=e.recruiter.user.name if e.recruiter and e.recruiter.user else "Recruiter"
            ))

    return ApplicationResponse(
        id=app_record.id,
        job_id=app_record.job_id,
        candidate_id=app_record.candidate_id,
        resume_id=app_record.resume_id,
        status=app_record.status,
        cover_letter=app_record.cover_letter,
        recruiter_notes=app_record.recruiter_notes if is_recruiter else None,
        application_date=app_record.application_date,
        updated_at=app_record.updated_at,
        job=job_data,
        candidate=cand_data,
        resume=resume_data,
        history=history_data,
        interviews=interviews_data,
        evaluations=evaluations_data
    )

@router.post("/jobs/{job_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: str,
    app_in: ApplicationCreate,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Submit job application.
    Enforces strict duplicate application prevention via both active status check
    and PostgreSQL partial unique index transaction handling.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )
    if job.status != JobStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job posting is closed and no longer accepting applications."
        )

    resume = db.query(Resume).filter(
        Resume.id == app_in.resume_id,
        Resume.candidate_id == candidate.id
    ).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified resume not found or does not belong to you."
        )

    existing_active = db.query(Application).filter(
        Application.job_id == job.id,
        Application.candidate_id == candidate.id,
        Application.status != ApplicationStatusEnum.WITHDRAWN
    ).first()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted an active application for this job."
        )

    new_application = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        cover_letter=app_in.cover_letter,
        status=ApplicationStatusEnum.APPLIED
    )
    db.add(new_application)
    try:
        db.commit()
        db.refresh(new_application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted an active application for this job."
        )

    # Initial history record
    init_hist = ApplicationHistory(
        application_id=new_application.id,
        from_status=None,
        to_status="APPLIED",
        changed_by_user_id=candidate.user_id,
        notes="Application submitted by candidate."
    )
    db.add(init_hist)

    # Notify recruiter
    if job.recruiter and job.recruiter.user:
        create_notification(
            db=db,
            user_id=job.recruiter.user_id,
            title="New Application Received",
            message=f"{candidate.user.name} applied for '{job.title}'.",
            notification_type="APPLICATION_RECEIVED",
            link=f"/recruiter?tab=candidates&job={job.id}"
        )

    db.commit()
    return serialize_application(new_application, is_recruiter=False)

@router.get("/applications", response_model=List[ApplicationResponse])
def get_candidate_applications(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """View application history and statuses for the logged-in candidate."""
    applications = db.query(Application).filter(
        Application.candidate_id == candidate.id
    ).order_by(Application.application_date.desc()).all()
    
    return [serialize_application(app, is_recruiter=False) for app in applications]

@router.put("/applications/{application_id}/withdraw", response_model=ApplicationResponse)
def withdraw_application(
    application_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Withdraw application if candidate owns it and status allows withdrawal."""
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )
    if app_record.candidate_id != candidate.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot withdraw another candidate's application."
        )
    if app_record.status in [ApplicationStatusEnum.SELECTED, ApplicationStatusEnum.REJECTED, ApplicationStatusEnum.WITHDRAWN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot withdraw an application with status '{app_record.status.value}'."
        )

    old_status = app_record.status.value
    app_record.status = ApplicationStatusEnum.WITHDRAWN
    app_record.updated_at = datetime.now(timezone.utc)

    # Record history
    hist = ApplicationHistory(
        application_id=app_record.id,
        from_status=old_status,
        to_status="WITHDRAWN",
        changed_by_user_id=candidate.user_id,
        notes="Withdrawn by applicant."
    )
    db.add(hist)
    db.commit()
    db.refresh(app_record)

    return serialize_application(app_record, is_recruiter=False)

@router.put("/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: str,
    status_in: ApplicationStatusUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Update candidate application status (Screening, Shortlist, Interview, Selected, Rejected).
    Validates recruiter ownership, enforces transition rules, creates audit log, and notifies candidate.
    """
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Verify recruiter owns the job associated with this application
    if app_record.job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot modify applicants for jobs posted by another recruiter."
        )

    # Validation: cannot transition from WITHDRAWN
    if app_record.status == ApplicationStatusEnum.WITHDRAWN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update an application that has been withdrawn by candidate."
        )

    old_status = app_record.status.value
    app_record.status = status_in.status
    if status_in.notes:
        app_record.recruiter_notes = status_in.notes
    app_record.updated_at = datetime.now(timezone.utc)

    # Add history entry
    hist = ApplicationHistory(
        application_id=app_record.id,
        from_status=old_status,
        to_status=status_in.status.value,
        changed_by_user_id=recruiter.user_id,
        notes=status_in.notes
    )
    db.add(hist)
    db.commit()
    db.refresh(app_record)

    # Shortlisting specific workflow with idempotency protection
    is_newly_shortlisted = (
        status_in.status == ApplicationStatusEnum.SHORTLISTED and 
        old_status != ApplicationStatusEnum.SHORTLISTED.value
    )

    if is_newly_shortlisted:
        # Check if Round 1 assessment already assigned
        assessment_info = None
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.candidate_id == app_record.candidate_id,
            (CandidateAssessmentAssignment.application_id == app_record.id) |
            (CandidateAssessmentAssignment.assessment.has(job_id=app_record.job_id))
        ).first()

        if assignment and assignment.assessment:
            assessment_info = {
                "title": assignment.assessment.title,
                "duration_minutes": assignment.assessment.duration_minutes,
                "deadline_at": assignment.deadline_at,
                "instructions": assignment.assessment.instructions,
            }

        # Candidate in-app notification for shortlisting
        create_notification(
            db=db,
            user_id=app_record.candidate.user_id,
            title="Congratulations! You Have Been Shortlisted",
            message=f"Congratulations! Your application for '{app_record.job.title}' has been shortlisted by the recruiting team.",
            notification_type="SHORTLISTED",
            link="/dashboard?tab=assessments" if assessment_info else "/dashboard?tab=applications"
        )

        # Trigger Brevo transactional email safely (post-commit)
        email_result = {"status": "skipped"}
        try:
            cand_user = app_record.candidate.user
            company_name = "SkillSphere Partner"
            if app_record.job and app_record.job.company and app_record.job.company.name:
                company_name = app_record.job.company.name
            elif recruiter and getattr(recruiter, "company", None) and recruiter.company.name:
                company_name = recruiter.company.name
            email_result = EmailService.send_shortlisting_email(
                to_email=cand_user.email,
                candidate_name=cand_user.name,
                job_title=app_record.job.title,
                company_name=company_name,
                assessment_info=assessment_info
            )
            logger.info(
                f"[Shortlisting Email] Dispatched to candidate {cand_user.email} for job '{app_record.job.title}'. "
                f"Status: {email_result.get('status')}"
            )
        except Exception as ex:
            logger.error(
                f"[Shortlisting Email] Failed delivery to candidate {app_record.candidate.user.email}: {str(ex)}"
            )
            email_result = {"status": "error", "error": str(ex)}

        # Audit log for shortlisting milestone
        create_audit_log(
            db=db,
            actor_id=recruiter.user_id,
            action_type="APPLICATION_SHORTLISTED",
            target_resource="Application",
            target_id=app_record.id,
            details={
                "from_status": old_status,
                "to_status": "SHORTLISTED",
                "job_title": app_record.job.title,
                "candidate_name": app_record.candidate.user.name,
                "email_delivery": email_result.get("status"),
                "has_assessment": bool(assessment_info)
            }
        )
    else:
        # Standard notification for other status updates
        stage_label = status_in.status.value.replace("_", " ").title()
        create_notification(
            db=db,
            user_id=app_record.candidate.user_id,
            title="Application Status Update",
            message=f"Your application for '{app_record.job.title}' has progressed to: {stage_label}.",
            notification_type="APPLICATION_STATUS",
            link="/dashboard?tab=applications"
        )

        # Standard audit log
        create_audit_log(
            db=db,
            actor_id=recruiter.user_id,
            action_type="APPLICATION_STATUS_CHANGE",
            target_resource="Application",
            target_id=app_record.id,
            details={
                "from_status": old_status,
                "to_status": status_in.status.value,
                "job_title": app_record.job.title,
                "candidate_name": app_record.candidate.user.name
            }
        )

    return serialize_application(app_record, is_recruiter=True)

@router.put("/applications/{application_id}/notes", response_model=dict)
def update_application_notes(
    application_id: str,
    notes_payload: dict,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Save or update internal recruiter notes for an application (private to recruiters)."""
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    if app_record.job.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    app_record.recruiter_notes = notes_payload.get("notes", "")
    db.commit()
    return {"status": "success", "recruiter_notes": app_record.recruiter_notes}

@router.get("/applications/{application_id}/history", response_model=List[ApplicationHistoryResponse])
def get_application_history(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status transition history for an application."""
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    is_cand = app_record.candidate.user_id == current_user.id
    is_rec = app_record.job.recruiter.user_id == current_user.id
    is_admin = current_user.role == RoleEnum.ADMIN
    if not (is_cand or is_rec or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    history_items = db.query(ApplicationHistory).filter(
        ApplicationHistory.application_id == application_id
    ).order_by(ApplicationHistory.created_at.asc()).all()

    # For candidates, sanitize internal recruiter notes
    results = []
    for h in history_items:
        clean_notes = h.notes if (is_rec or is_admin) else None
        results.append(ApplicationHistoryResponse(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by_name=h.changed_by.name if h.changed_by else "System",
            notes=clean_notes,
            created_at=h.created_at
        ))
    return results
