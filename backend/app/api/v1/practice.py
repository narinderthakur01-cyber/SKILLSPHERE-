from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, RoleEnum, Candidate, CandidateTechnology, PracticeQuestion
from app.schemas.schemas import (
    CandidateTechnologyResponse, CandidateTechnologyCreate,
    PracticeQuestionResponse, PracticeAttemptRequest, PracticeAttemptResponse,
    PracticeAnalyticsResponse
)
from app.services.tech_detection_service import TechDetectionService, TECH_NORMALIZATION_MAP
from app.services.practice_service import PracticeService

router = APIRouter(prefix="/practice", tags=["Technical Practice"])

def get_current_candidate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Candidate:
    """Enforce that current user is a Job Seeker and resolve their Candidate profile."""
    if current_user.role != RoleEnum.JOB_SEEKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technical practice portal is exclusively available for candidates."
        )
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile record not found."
        )
    return candidate

@router.get("/technologies", response_model=List[CandidateTechnologyResponse])
def get_technologies(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Retrieve candidate's detected and manually added technologies."""
    # If candidate has zero technologies, attempt auto-sync from their resume
    existing = db.query(CandidateTechnology).filter(
        CandidateTechnology.candidate_id == candidate.id
    ).order_by(CandidateTechnology.category, CandidateTechnology.technology_name).all()

    if not existing:
        existing = TechDetectionService.sync_candidate_technologies(db, candidate.id)

    return existing

@router.post("/technologies", response_model=CandidateTechnologyResponse, status_code=status.HTTP_201_CREATED)
def add_manual_technology(
    tech_in: CandidateTechnologyCreate,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Allow candidate to add a technology manually to their practice roadmap."""
    raw_name = tech_in.technology_name.strip()
    if not raw_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technology name cannot be empty.")

    # Canonical normalization
    lower = raw_name.lower()
    canonical_name, category = TECH_NORMALIZATION_MAP.get(lower, (raw_name.title(), tech_in.category or "LANGUAGE"))

    # Check if technology already exists for this candidate
    existing = db.query(CandidateTechnology).filter(
        CandidateTechnology.candidate_id == candidate.id,
        CandidateTechnology.technology_name == canonical_name
    ).first()

    if existing:
        return existing

    new_tech = CandidateTechnology(
        candidate_id=candidate.id,
        technology_name=canonical_name,
        category=category,
        is_resume_detected=False,
        proficiency_level=tech_in.proficiency_level or "INTERMEDIATE"
    )
    db.add(new_tech)
    db.commit()
    db.refresh(new_tech)
    return new_tech

@router.delete("/technologies/{tech_name}")
def remove_technology(
    tech_name: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Remove a technology from the candidate's active roadmap."""
    record = db.query(CandidateTechnology).filter(
        CandidateTechnology.candidate_id == candidate.id,
        CandidateTechnology.technology_name.ilike(tech_name.strip())
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technology '{tech_name}' not found in candidate roadmap."
        )

    db.delete(record)
    db.commit()
    return {"message": f"Technology '{record.technology_name}' removed from practice roadmap.", "success": True}

@router.post("/technologies/detect-from-resume", response_model=List[CandidateTechnologyResponse])
def detect_from_resume(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Re-scan the candidate's latest resume and synchronize detected technologies."""
    synced = TechDetectionService.sync_candidate_technologies(db, candidate.id)
    return synced

@router.get("/technologies/{tech_name}/questions", response_model=List[PracticeQuestionResponse])
def get_practice_questions(
    tech_name: str,
    batch: int = Query(1, ge=1, le=50),
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Fetch 10 practice questions for the selected technology in batches."""
    clean_tech = tech_name.strip()
    questions = PracticeService.get_questions_for_batch(db, clean_tech, batch_number=batch, limit=10)
    return questions

@router.post("/technologies/{tech_name}/generate-more", response_model=List[PracticeQuestionResponse])
def generate_more_questions(
    tech_name: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Generate 10 additional non-duplicate questions for the specified technology."""
    clean_tech = tech_name.strip()
    new_questions = PracticeService.generate_more_questions(db, clean_tech, count=10)
    return new_questions

@router.post("/questions/{question_id}/attempt", response_model=PracticeAttemptResponse)
def submit_question_attempt(
    question_id: str,
    req: PracticeAttemptRequest,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Submit candidate's answer to a practice question and calculate score/feedback."""
    try:
        attempt = PracticeService.record_attempt(
            db=db,
            candidate_id=candidate.id,
            question_id=question_id,
            candidate_answer=req.candidate_answer,
            time_spent_seconds=req.time_spent_seconds or 0,
            hints_used=req.hints_used or 0
        )
        question = db.query(PracticeQuestion).filter(PracticeQuestion.id == question_id).first()
        return PracticeAttemptResponse(
            id=attempt.id,
            question_id=attempt.question_id,
            technology=attempt.technology,
            difficulty=attempt.difficulty,
            candidate_answer=attempt.candidate_answer or "",
            is_correct=attempt.is_correct,
            explanation=question.explanation if question else None,
            correct_answer=question.correct_answer if question else "",
            completed_at=attempt.completed_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/analytics", response_model=PracticeAnalyticsResponse)
def get_practice_analytics(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Fetch aggregated performance analytics, accuracy, and practice history for candidate."""
    analytics = PracticeService.get_candidate_analytics(db, candidate.id)
    return analytics
