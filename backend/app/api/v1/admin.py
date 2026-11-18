from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.deps import require_role
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    JobStatusEnum, ApplicationStatusEnum, Interview, CandidateEvaluation,
    SavedJob, Message
)
from app.schemas.schemas import (
    AdminAnalyticsResponse, UserResponse, JobResponse
)
from app.api.v1.jobs import serialize_job
from app.services.activity_service import create_audit_log

router = APIRouter(prefix="/admin", tags=["Admin Operations"], dependencies=[Depends(require_role([RoleEnum.ADMIN]))])

@router.get("/analytics", response_model=AdminAnalyticsResponse)
def get_platform_analytics(db: Session = Depends(get_db)):
    """Retrieve platform-level summary statistics, KPIs, and subsystem metrics."""
    total_users = db.query(User).count()
    total_candidates = db.query(User).filter(User.role == RoleEnum.JOB_SEEKER).count()
    total_recruiters = db.query(User).filter(User.role == RoleEnum.RECRUITER).count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status == JobStatusEnum.ACTIVE).count()
    total_applications = db.query(Application).count()

    # Applications breakdown by status
    status_counts = db.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    
    app_status_dict = {s.value: 0 for s in ApplicationStatusEnum}
    for stat, count in status_counts:
        app_status_dict[stat.value] = count

    growth_trends = {
        "total_interviews": db.query(Interview).count(),
        "total_evaluations": db.query(CandidateEvaluation).count(),
        "total_saved_jobs": db.query(SavedJob).count(),
        "active_messages": db.query(Message).count()
    }

    return AdminAnalyticsResponse(
        total_users=total_users,
        total_candidates=total_candidates,
        total_recruiters=total_recruiters,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        applications_by_status=app_status_dict,
        growth_trends=growth_trends
    )

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """List all registered users across the platform."""
    users = db.query(User).order_by(desc(User.created_at)).all()
    return [UserResponse.model_validate(u) for u in users]

@router.put("/users/{user_id}/status", response_model=UserResponse)
def toggle_user_active_status(user_id: str, is_active: bool, db: Session = Depends(get_db)):
    """Activate or deactivate user account with audit logging."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    user.is_active = is_active
    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        actor_id=None,
        action_type="USER_STATUS_CHANGE",
        target_resource="User",
        target_id=user.id,
        details={"user_email": user.email, "is_active": is_active}
    )

    return UserResponse.model_validate(user)

@router.get("/jobs", response_model=List[JobResponse])
def get_all_jobs_for_moderation(db: Session = Depends(get_db)):
    """View all platform jobs for compliance and moderation."""
    jobs = db.query(Job).order_by(desc(Job.created_at)).all()
    return [serialize_job(j) for j in jobs]

@router.put("/jobs/{job_id}/moderate", response_model=JobResponse)
def moderate_job_status(job_id: str, new_status: JobStatusEnum, db: Session = Depends(get_db)):
    """Approve, close, or flag job postings with audit logging."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )
    old_status = job.status.value
    job.status = new_status
    db.commit()
    db.refresh(job)

    create_audit_log(
        db=db,
        actor_id=None,
        action_type="JOB_MODERATE",
        target_resource="Job",
        target_id=job.id,
        details={"from_status": old_status, "to_status": new_status.value, "title": job.title}
    )

    return serialize_job(job)
