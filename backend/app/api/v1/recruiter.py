from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.deps import get_current_recruiter
from app.models.models import Recruiter, Job, Application, Company, ApplicationStatusEnum, Skill, JobStatusEnum
from app.schemas.schemas import (
    JobResponse, ApplicationResponse, CompanyResponse, CompanyUpdate, CompanyCreate, RecruiterAnalyticsResponse
)
from app.api.v1.jobs import serialize_job
from app.api.v1.applications import serialize_application

router = APIRouter(prefix="/recruiter", tags=["Recruiter Operations"])

@router.get("/jobs", response_model=List[JobResponse])
def get_my_jobs(
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all jobs created by the logged-in recruiter."""
    jobs = db.query(Job).filter(
        Job.recruiter_id == recruiter.id
    ).order_by(desc(Job.created_at)).all()
    
    return [serialize_job(j) for j in jobs]

@router.get("/applicants", response_model=List[ApplicationResponse])
def get_my_applicants(
    job_id: Optional[str] = Query(None, description="Filter applicants by specific job"),
    status: Optional[ApplicationStatusEnum] = Query(None, description="Filter applicants by status"),
    skill: Optional[str] = Query(None, description="Filter applicants having a specific skill"),
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    View applicants for jobs posted by this recruiter.
    Strict isolation: Recruiters can NEVER view applicants for jobs posted by others.
    """
    query = db.query(Application).join(Job).filter(Job.recruiter_id == recruiter.id)

    if job_id:
        query = query.filter(Application.job_id == job_id)
    if status:
        query = query.filter(Application.status == status)
    if skill and skill.strip():
        clean_skill = skill.strip().lower()
        query = query.join(Application.candidate).join(Skill, Application.candidate.has(skills=Skill)).filter(
            Skill.skill_name.ilike(f"%{clean_skill}%")
        )

    applicants = query.order_by(desc(Application.application_date)).all()
    return [serialize_application(app, is_recruiter=True) for app in applicants]

@router.get("/analytics", response_model=RecruiterAnalyticsResponse)
def get_recruiter_analytics(
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Real aggregation analytics for the logged-in recruiter's pipeline."""
    # Jobs metrics
    total_jobs = db.query(Job).filter(Job.recruiter_id == recruiter.id).count()
    active_jobs = db.query(Job).filter(Job.recruiter_id == recruiter.id, Job.status == JobStatusEnum.ACTIVE).count()

    # Applications metrics
    apps = db.query(Application).join(Job).filter(Job.recruiter_id == recruiter.id).all()
    total_applicants = len(apps)

    funnel: Dict[str, int] = {s.value: 0 for s in ApplicationStatusEnum}
    hire_durations_days = []

    for a in apps:
        funnel[a.status.value] = funnel.get(a.status.value, 0) + 1
        if a.status == ApplicationStatusEnum.SELECTED and a.application_date and a.updated_at:
            delta = (a.updated_at - a.application_date).total_seconds() / 86400.0
            hire_durations_days.append(max(delta, 0.5))

    shortlisted = funnel.get(ApplicationStatusEnum.SHORTLISTED.value, 0)
    interviewed = funnel.get(ApplicationStatusEnum.INTERVIEW.value, 0)
    selected = funnel.get(ApplicationStatusEnum.SELECTED.value, 0)
    rejected = funnel.get(ApplicationStatusEnum.REJECTED.value, 0)

    # Conversion calculations
    interview_pool = interviewed + selected
    app_to_interview_rate = round((interview_pool / total_applicants) * 100.0, 1) if total_applicants > 0 else 0.0
    interview_to_offer_rate = round((selected / interview_pool) * 100.0, 1) if interview_pool > 0 else 0.0
    avg_days_to_hire = round(sum(hire_durations_days) / len(hire_durations_days), 1) if hire_durations_days else None

    return RecruiterAnalyticsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applicants=total_applicants,
        shortlisted_candidates=shortlisted,
        interviewed_candidates=interviewed,
        selected_candidates=selected,
        rejected_candidates=rejected,
        application_to_interview_rate=app_to_interview_rate,
        interview_to_offer_rate=interview_to_offer_rate,
        avg_days_to_hire=avg_days_to_hire,
        pipeline_funnel=funnel
    )

@router.get("/company", response_model=Optional[CompanyResponse])
def get_my_company(
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Retrieve recruiter's associated company profile."""
    if not recruiter.company_id:
        return None
    company = db.query(Company).filter(Company.id == recruiter.company_id).first()
    return CompanyResponse.model_validate(company) if company else None

@router.put("/company", response_model=CompanyResponse)
def update_my_company(
    company_in: CompanyUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Create or update recruiter's company profile."""
    if recruiter.company_id:
        company = db.query(Company).filter(Company.id == recruiter.company_id).first()
    else:
        company = None

    if not company:
        company = Company(
            company_name=company_in.company_name or "My Company",
            description=company_in.description,
            website=company_in.website,
            location=company_in.location,
            contact_email=company_in.contact_email,
            logo_url=company_in.logo_url
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        recruiter.company_id = company.id
        db.commit()
    else:
        if company_in.company_name:
            company.company_name = company_in.company_name
        if company_in.description is not None:
            company.description = company_in.description
        if company_in.website is not None:
            company.website = company_in.website
        if company_in.location is not None:
            company.location = company_in.location
        if company_in.contact_email is not None:
            company.contact_email = company_in.contact_email
        if company_in.logo_url is not None:
            company.logo_url = company_in.logo_url
        db.commit()
        db.refresh(company)

    return CompanyResponse.model_validate(company)
