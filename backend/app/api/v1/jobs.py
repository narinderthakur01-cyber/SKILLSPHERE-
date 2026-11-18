from typing import Optional, List
import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.database import get_db
from app.core.deps import get_current_recruiter, get_current_user, require_role
from app.models.models import Job, JobSkill, Skill, Recruiter, RoleEnum, JobStatusEnum, JobTypeEnum, User
from app.schemas.schemas import JobCreate, JobUpdate, JobResponse, JobListResponse, CompanyResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def serialize_job(job: Job) -> JobResponse:
    """Helper to serialize a Job model to JobResponse schema."""
    company_data = None
    if job.company:
        company_data = CompanyResponse.model_validate(job.company)
        
    skills = [js.skill.skill_name.title() for js in job.job_skills if js.skill]
    
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        location=job.location,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        status=job.status,
        created_at=job.created_at,
        company=company_data,
        required_skills=skills
    )

@router.get("", response_model=JobListResponse)
def list_jobs(
    keyword: Optional[str] = Query(None, description="Search in title and description"),
    location: Optional[str] = Query(None, description="Filter by location"),
    job_type: Optional[JobTypeEnum] = Query(None, description="Filter by job type"),
    min_exp: Optional[float] = Query(None, description="Minimum experience required"),
    max_exp: Optional[float] = Query(None, description="Maximum experience allowed"),
    skill: Optional[str] = Query(None, description="Filter by skill tag"),
    sort_by: Optional[str] = Query("newest", description="Sort by 'newest', 'experience', 'salary'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search and filter active job postings with pagination and sorting.
    """
    query = db.query(Job).filter(Job.status == JobStatusEnum.ACTIVE)

    # Keyword filter
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term)
            )
        )

    # Location filter
    if location and location.strip():
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    # Job type filter
    if job_type:
        query = query.filter(Job.job_type == job_type)

    # Experience filter
    if min_exp is not None:
        query = query.filter(Job.experience_min >= min_exp)
    if max_exp is not None:
        query = query.filter(Job.experience_max <= max_exp)

    # Skill filter
    if skill and skill.strip():
        clean_skill = skill.strip().lower()
        query = query.join(Job.job_skills).join(JobSkill.skill).filter(
            Skill.skill_name.ilike(f"%{clean_skill}%")
        )

    # Sorting
    if sort_by == "experience":
        query = query.order_by(Job.experience_min.asc())
    elif sort_by == "salary":
        query = query.order_by(desc(Job.salary_max))
    else:
        query = query.order_by(desc(Job.created_at))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    jobs = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [serialize_job(j) for j in jobs]

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages
    )

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Create a new job posting with skill requirements (Recruiter only).
    """
    new_job = Job(
        recruiter_id=recruiter.id,
        company_id=recruiter.company_id,
        title=job_in.title,
        description=job_in.description,
        location=job_in.location,
        experience_min=job_in.experience_min,
        experience_max=job_in.experience_max,
        job_type=job_in.job_type,
        salary_min=job_in.salary_min,
        salary_max=job_in.salary_max,
        status=job_in.status
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Associate required skills
    for skill_name in job_in.required_skills:
        clean_skill = skill_name.strip().lower()
        if not clean_skill:
            continue
        skill_record = db.query(Skill).filter(Skill.skill_name == clean_skill).first()
        if not skill_record:
            skill_record = Skill(skill_name=clean_skill)
            db.add(skill_record)
            db.commit()
            db.refresh(skill_record)

        job_skill = JobSkill(job_id=new_job.id, skill_id=skill_record.id, is_required=True)
        db.add(job_skill)

    db.commit()
    db.refresh(new_job)

    return serialize_job(new_job)

@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: str, db: Session = Depends(get_db)):
    """Retrieve complete job posting details."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )
    return serialize_job(job)

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Update job posting details (Recruiter owner only)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )
    if job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot modify a job posted by another recruiter."
        )

    if job_in.title is not None:
        job.title = job_in.title
    if job_in.description is not None:
        job.description = job_in.description
    if job_in.location is not None:
        job.location = job_in.location
    if job_in.experience_min is not None:
        job.experience_min = job_in.experience_min
    if job_in.experience_max is not None:
        job.experience_max = job_in.experience_max
    if job_in.job_type is not None:
        job.job_type = job_in.job_type
    if job_in.salary_min is not None:
        job.salary_min = job_in.salary_min
    if job_in.salary_max is not None:
        job.salary_max = job_in.salary_max
    if job_in.status is not None:
        job.status = job_in.status

    if job_in.required_skills is not None:
        # Clear existing job skills
        db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
        for skill_name in job_in.required_skills:
            clean_skill = skill_name.strip().lower()
            if not clean_skill:
                continue
            skill_record = db.query(Skill).filter(Skill.skill_name == clean_skill).first()
            if not skill_record:
                skill_record = Skill(skill_name=clean_skill)
                db.add(skill_record)
                db.commit()
                db.refresh(skill_record)

            job_skill = JobSkill(job_id=job.id, skill_id=skill_record.id, is_required=True)
            db.add(job_skill)

    db.commit()
    db.refresh(job)
    return serialize_job(job)

@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def close_or_delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Close or remove job posting (Recruiter owner or Admin)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )

    # Permission check: Owner recruiter or Admin
    if current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or job.recruiter_id != recruiter.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot modify a job posted by another recruiter."
            )
    elif current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Insufficient privileges."
        )

    job.status = JobStatusEnum.CLOSED
    db.commit()
    return {"message": "Job successfully closed."}
