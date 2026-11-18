from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import get_current_recruiter
from app.models.models import (
    Recruiter, Application, CandidateEvaluation, Job, ResumeAnalysis
)
from app.schemas.schemas import (
    CandidateEvaluationCreate, CandidateEvaluationResponse, CandidateComparisonItem
)
from app.services.activity_service import create_audit_log

router = APIRouter(prefix="/evaluations", tags=["Candidate Evaluations & Scorecards"])

def serialize_evaluation(eval_rec: CandidateEvaluation) -> CandidateEvaluationResponse:
    recruiter_name = eval_rec.recruiter.user.name if eval_rec.recruiter and eval_rec.recruiter.user else "Recruiter"
    overall_avg = round((eval_rec.technical_score + eval_rec.communication_score + eval_rec.experience_score) / 3.0, 2)
    return CandidateEvaluationResponse(
        id=eval_rec.id,
        application_id=eval_rec.application_id,
        recruiter_id=eval_rec.recruiter_id,
        interview_id=eval_rec.interview_id,
        technical_score=eval_rec.technical_score,
        communication_score=eval_rec.communication_score,
        experience_score=eval_rec.experience_score,
        overall_score=overall_avg,
        overall_recommendation=eval_rec.overall_recommendation,
        interview_feedback=eval_rec.interview_feedback,
        internal_notes=eval_rec.internal_notes,
        created_at=eval_rec.created_at,
        updated_at=eval_rec.updated_at,
        recruiter_name=recruiter_name
    )

@router.post("", response_model=CandidateEvaluationResponse, status_code=status.HTTP_201_CREATED)
def submit_candidate_evaluation(
    eval_in: CandidateEvaluationCreate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Submit a structured candidate evaluation scorecard. Internal to recruiters only."""
    app_record = db.query(Application).filter(Application.id == eval_in.application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    # Recruiter must own the job opening
    if app_record.job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only evaluate candidates for your company's job postings."
        )

    evaluation = CandidateEvaluation(
        application_id=eval_in.application_id,
        recruiter_id=recruiter.id,
        interview_id=eval_in.interview_id,
        technical_score=eval_in.technical_score,
        communication_score=eval_in.communication_score,
        experience_score=eval_in.experience_score,
        overall_recommendation=eval_in.overall_recommendation,
        interview_feedback=eval_in.interview_feedback,
        internal_notes=eval_in.internal_notes
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    create_audit_log(
        db=db,
        actor_id=recruiter.user_id,
        action_type="CANDIDATE_EVALUATION",
        target_resource="CandidateEvaluation",
        target_id=evaluation.id,
        details={
            "application_id": app_record.id,
            "overall_recommendation": evaluation.overall_recommendation,
            "overall_score": round((eval_in.technical_score + eval_in.communication_score + eval_in.experience_score) / 3.0, 2)
        }
    )

    return serialize_evaluation(evaluation)

@router.get("/application/{application_id}", response_model=List[CandidateEvaluationResponse])
def get_application_evaluations(
    application_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Retrieve all evaluation scorecards for an application (Recruiters only)."""
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found."
        )

    if app_record.job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only view evaluations for your own job postings."
        )

    evals = db.query(CandidateEvaluation).filter(
        CandidateEvaluation.application_id == application_id
    ).order_by(CandidateEvaluation.created_at.desc()).all()

    return [serialize_evaluation(e) for e in evals]

@router.get("/compare/{job_id}", response_model=List[CandidateComparisonItem])
def compare_candidates_for_job(
    job_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Side-by-side candidate comparison matrix for a specific job (Recruiters only)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )

    if job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot compare candidates for other recruiters' jobs."
        )

    applications = db.query(Application).filter(Application.job_id == job_id).all()
    comparison_items = []

    for app in applications:
        cand = app.candidate
        user = cand.user if cand else None
        if not cand or not user:
            continue

        cand_skills = [s.skill_name.title() for s in cand.skills]

        # Fetch match analysis if available
        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.job_id == job_id,
            ResumeAnalysis.resume_id == app.resume_id
        ).first()

        match_score = analysis.match_score if analysis else None
        matched_skills = analysis.matched_skills if analysis else []
        missing_skills = analysis.missing_skills if analysis else []

        # Average evaluation scores
        evals = app.evaluations
        avg_tech = round(sum(e.technical_score for e in evals) / len(evals), 2) if evals else None
        avg_comm = round(sum(e.communication_score for e in evals) / len(evals), 2) if evals else None
        avg_exp = round(sum(e.experience_score for e in evals) / len(evals), 2) if evals else None
        latest_rec = evals[0].overall_recommendation if evals else None

        comparison_items.append(CandidateComparisonItem(
            application_id=app.id,
            candidate_id=cand.id,
            candidate_name=user.name,
            candidate_email=user.email,
            status=app.status.value,
            match_score=match_score,
            total_years_exp=cand.total_years_exp or 0.0,
            verified_skills=cand_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            evaluations_count=len(evals),
            avg_technical_score=avg_tech,
            avg_communication_score=avg_comm,
            avg_experience_score=avg_exp,
            latest_recommendation=latest_rec
        ))

    # Sort candidates by match_score descending
    comparison_items.sort(key=lambda x: (x.match_score is not None, x.match_score or 0), reverse=True)
    return comparison_items
