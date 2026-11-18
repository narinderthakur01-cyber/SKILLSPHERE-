from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_candidate
from app.models.models import Candidate, Job, SavedJob, JobStatusEnum
from app.schemas.schemas import SavedJobResponse, RecommendedJobResponse, JobResponse, CompanyResponse
from app.services.matching_service import calculate_skill_match

router = APIRouter(tags=["Saved Jobs & Recommendations"])

def serialize_job_schema(job: Job) -> JobResponse:
    company_data = None
    if job.company:
        company_data = CompanyResponse.model_validate(job.company)
    skills = [js.skill.skill_name.title() for js in job.job_skills if js.skill]
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        department=job.department,
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

@router.post("/saved-jobs/{job_id}", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
def save_job(
    job_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Bookmark a job posting for the candidate. Prevents duplicate bookmarks."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )

    # Check if already saved
    existing = db.query(SavedJob).filter(
        SavedJob.candidate_id == candidate.id,
        SavedJob.job_id == job_id
    ).first()
    if existing:
        return SavedJobResponse(
            id=existing.id,
            candidate_id=existing.candidate_id,
            job_id=existing.job_id,
            created_at=existing.created_at,
            job=serialize_job_schema(job)
        )

    saved = SavedJob(
        candidate_id=candidate.id,
        job_id=job_id
    )
    db.add(saved)
    try:
        db.commit()
        db.refresh(saved)
    except IntegrityError:
        db.rollback()
        existing = db.query(SavedJob).filter(
            SavedJob.candidate_id == candidate.id,
            SavedJob.job_id == job_id
        ).first()
        return SavedJobResponse(
            id=existing.id,
            candidate_id=existing.candidate_id,
            job_id=existing.job_id,
            created_at=existing.created_at,
            job=serialize_job_schema(job)
        )

    return SavedJobResponse(
        id=saved.id,
        candidate_id=saved.candidate_id,
        job_id=saved.job_id,
        created_at=saved.created_at,
        job=serialize_job_schema(job)
    )

@router.delete("/saved-jobs/{job_id}", response_model=dict)
def unsave_job(
    job_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Remove a bookmarked job for the candidate."""
    saved = db.query(SavedJob).filter(
        SavedJob.candidate_id == candidate.id,
        SavedJob.job_id == job_id
    ).first()
    if not saved:
        return {"status": "success", "message": "Job bookmark removed or was not saved."}

    db.delete(saved)
    db.commit()
    return {"status": "success", "message": "Job bookmark removed successfully."}

@router.get("/saved-jobs", response_model=List[SavedJobResponse])
def get_saved_jobs(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """List all bookmarked jobs for the authenticated candidate."""
    saved_items = db.query(SavedJob).filter(
        SavedJob.candidate_id == candidate.id
    ).order_by(SavedJob.created_at.desc()).all()

    return [
        SavedJobResponse(
            id=item.id,
            candidate_id=item.candidate_id,
            job_id=item.job_id,
            created_at=item.created_at,
            job=serialize_job_schema(item.job)
        )
        for item in saved_items if item.job
    ]

@router.get("/jobs/recommendations", response_model=List[RecommendedJobResponse])
def get_job_recommendations(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Explainable job recommendations tailored to candidate's verified skills and experience.
    Uses deterministic skill overlap calculations and returns actionable reasons.
    """
    active_jobs = db.query(Job).filter(Job.status == JobStatusEnum.ACTIVE).all()
    candidate_skills = [s.skill_name.lower() for s in candidate.skills]

    recommendations = []
    for job in active_jobs:
        job_req_skills = [js.skill.skill_name.lower() for js in job.job_skills if js.skill]
        match_result = calculate_skill_match(candidate_skills, job_req_skills)

        score = match_result["match_score"]
        matched = [s.title() for s in match_result["matched_skills"]]
        missing = [s.title() for s in match_result["missing_skills"]]

        if score is not None and score >= 40.0:
            reason = f"Strong match: You possess {len(matched)} of {len(job_req_skills)} required skills ({', '.join(matched[:3])})."
        elif score is None:
            reason = "Open domain role: Training provided. Welcomes applicants from all backgrounds."
        else:
            reason = f"Explore role: Matches {len(matched)} of {len(job_req_skills)} skills ({', '.join(matched) if matched else 'Entry role'})."

        recommendations.append(RecommendedJobResponse(
            job=serialize_job_schema(job),
            match_score=score,
            matched_skills=matched,
            missing_skills=missing,
            recommendation_reason=reason
        ))

    # Sort primarily by match score descending, placing high match first
    recommendations.sort(key=lambda r: (r.match_score is not None, r.match_score or 0), reverse=True)
    return recommendations
