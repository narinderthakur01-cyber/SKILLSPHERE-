from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.core.deps import get_current_recruiter, get_current_candidate, get_current_user
from app.models.models import (
    Assessment, AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAttempt, AssessmentResult,
    Candidate, Recruiter, User, Job, Application, AssessmentStatusEnum,
    AssessmentAssignmentStatusEnum, AttemptStatusEnum, MediaAsset
)
from app.schemas.schemas import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentQuestionResponse, AssessmentOptionResponse,
    AssessmentAssignRequest, CandidateAssignmentResponse,
    ShortlistedCandidateItem, CandidateAssessmentInstructions,
    SaveAnswersRequest, AttemptStatusResponse, CandidateResultResponse,
    RecruiterCandidateReviewResponse, CandidateSubmissionConfirmationResponse,
    CandidateAssessmentStatusResponse, RecruiterAssessmentReviewItem,
    RecruiterDetailedReviewResponse, RecruiterDecisionRequest,
    RecruiterDecisionResponse, ScoreAdjustmentRequest,
    AssessmentComparisonResponse, SessionRecordingUploadRequest
)
from app.services.assessment_service import AssessmentService

router = APIRouter(tags=["First-Round Assessments"])

# ==============================================================================
# RECRUITER ASSESSMENT APIS
# ==============================================================================

@router.post("/recruiter/assessments", response_model=AssessmentResponse)
def create_assessment(
    data: AssessmentCreate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Recruiter creates a new MCQ assessment in DRAFT status."""
    assessment = AssessmentService.create_assessment(db, recruiter, data)
    q_count = len(assessment.questions)
    return AssessmentResponse(
        id=assessment.id,
        job_id=assessment.job_id,
        job_title=assessment.job.title if assessment.job else None,
        recruiter_id=assessment.recruiter_id,
        title=assessment.title,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        total_marks=assessment.total_marks,
        passing_marks=assessment.passing_marks,
        question_count=q_count,
        status=assessment.status.value,
        randomize_questions=assessment.randomize_questions,
        randomize_options=assessment.randomize_options,
        auto_selection_config=assessment.auto_selection_config,
        version=assessment.version or 1,
        created_at=assessment.created_at,
        published_at=assessment.published_at
    )

@router.get("/recruiter/assessments", response_model=List[AssessmentResponse])
def list_recruiter_assessments(
    job_id: Optional[str] = Query(None),
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all assessments created by the recruiter, optionally filtered by job_id."""
    query = db.query(Assessment).filter(Assessment.recruiter_id == recruiter.id)
    if job_id:
        query = query.filter(Assessment.job_id == job_id)

    assessments = query.order_by(Assessment.created_at.desc()).all()
    resp = []
    for a in assessments:
        resp.append(AssessmentResponse(
            id=a.id,
            job_id=a.job_id,
            job_title=a.job.title if a.job else None,
            recruiter_id=a.recruiter_id,
            title=a.title,
            instructions=a.instructions,
            duration_minutes=a.duration_minutes,
            total_marks=a.total_marks,
            passing_marks=a.passing_marks,
            question_count=len(a.questions),
            status=a.status.value,
            randomize_questions=a.randomize_questions,
            randomize_options=a.randomize_options,
            auto_selection_config=a.auto_selection_config,
            version=a.version or 1,
            created_at=a.created_at,
            published_at=a.published_at
        ))
    return resp

@router.get("/recruiter/assessments/reviews", response_model=List[RecruiterAssessmentReviewItem])
def list_recruiter_reviews(
    assessment_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("submitted_at"),
    sort_order: Optional[str] = Query("desc"),
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    List candidate assessment submissions for recruiter review.
    Supports filtering by review status, score range, candidate search, and sorting.
    """
    return AssessmentService.list_recruiter_assessment_reviews(
        db=db,
        recruiter=recruiter,
        assessment_id=assessment_id,
        job_id=job_id,
        review_status=review_status,
        search=search,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/recruiter/assessments/assignments/{assignment_id}/candidate-answers", response_model=RecruiterCandidateReviewResponse)
def get_recruiter_candidate_review(
    assignment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Recruiter inspection of a candidate's submitted assessment answers."""
    return AssessmentService.get_recruiter_candidate_review(db, recruiter, assignment_id)

@router.get("/recruiter/assessments/assignments/{assignment_id}/detailed-review", response_model=RecruiterDetailedReviewResponse)
def get_recruiter_detailed_review(
    assignment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Fetch comprehensive candidate assessment review:
    - Detailed question-by-question breakdown with option keys, submitted answer, correct answer, and explanations
    - Chronological proctoring events timeline
    - Immutable decision audit history
    """
    return AssessmentService.get_recruiter_detailed_review(db, recruiter, assignment_id)

@router.post("/recruiter/assessments/assignments/{assignment_id}/adjust-score", response_model=RecruiterDetailedReviewResponse)
def adjust_candidate_score(
    assignment_id: str,
    req: ScoreAdjustmentRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Manually adjust candidate's assessment score.
    Requires justification; preserves original automatically calculated score in audit trail.
    """
    score = req.new_score if req.new_score is not None else req.adjusted_score
    if score is None:
        raise HTTPException(status_code=400, detail="Score is required.")
    if not req.reason or len(req.reason.strip()) < 3:
        raise HTTPException(status_code=400, detail="A valid reason (minimum 3 characters) is required for manual score adjustment.")
    return AssessmentService.adjust_candidate_score(
        db=db,
        recruiter=recruiter,
        assignment_id=assignment_id,
        new_score=score,
        reason=req.reason.strip()
    )

@router.post("/recruiter/assessments/assignments/{assignment_id}/decision", response_model=RecruiterDecisionResponse)
def make_recruiter_decision(
    assignment_id: str,
    req: RecruiterDecisionRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Execute final hiring decision: ACCEPT, REJECT, MOVE_TO_INTERVIEW, or ON_HOLD.
    Synchronizes application status, records immutable decision history, and sends candidate notifications.
    """
    reason = req.reason or req.decision_reason
    remarks = req.remarks or req.recruiter_remarks
    return AssessmentService.make_recruiter_decision(
        db=db,
        recruiter=recruiter,
        assignment_id=assignment_id,
        decision=req.decision,
        reason=reason,
        remarks=remarks,
        candidate_message=req.candidate_message
    )

@router.post("/recruiter/assessments/assignments/{assignment_id}/retry-email")
def retry_decision_email(
    assignment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Retry sending candidate decision notification email following delivery failure."""
    return AssessmentService.retry_decision_email(db, recruiter, assignment_id)

@router.get("/recruiter/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment_details(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Preview complete assessment including private ground-truth answers for the recruiter."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    if assessment.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

    questions = []
    for q in sorted(assessment.questions, key=lambda x: x.order_num):
        options = []
        for opt in sorted(q.options, key=lambda x: x.option_key):
            options.append(AssessmentOptionResponse(
                id=opt.id,
                option_key=opt.option_key,
                option_text=opt.option_text,
                is_correct=opt.is_correct  # Visible to recruiter for preview
            ))
        questions.append(AssessmentQuestionResponse(
            id=q.id,
            bank_question_id=q.bank_question_id,
            question_text=q.question_text,
            explanation=q.explanation,
            order_num=q.order_num,
            marks=q.marks,
            options=options
        ))

    return AssessmentResponse(
        id=assessment.id,
        job_id=assessment.job_id,
        job_title=assessment.job.title if assessment.job else None,
        recruiter_id=assessment.recruiter_id,
        title=assessment.title,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        total_marks=assessment.total_marks,
        passing_marks=assessment.passing_marks,
        question_count=len(questions),
        status=assessment.status.value,
        randomize_questions=assessment.randomize_questions,
        randomize_options=assessment.randomize_options,
        auto_selection_config=assessment.auto_selection_config,
        version=assessment.version or 1,
        created_at=assessment.created_at,
        published_at=assessment.published_at,
        questions=questions
    )

@router.put("/recruiter/assessments/{assessment_id}", response_model=AssessmentResponse)
def update_draft_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Update an unpublished (DRAFT) assessment."""
    assessment = AssessmentService.update_draft_assessment(db, recruiter, assessment_id, data)
    return AssessmentResponse(
        id=assessment.id,
        job_id=assessment.job_id,
        job_title=assessment.job.title if assessment.job else None,
        recruiter_id=assessment.recruiter_id,
        title=assessment.title,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        total_marks=assessment.total_marks,
        passing_marks=assessment.passing_marks,
        question_count=len(assessment.questions),
        status=assessment.status.value,
        randomize_questions=assessment.randomize_questions,
        randomize_options=assessment.randomize_options,
        auto_selection_config=assessment.auto_selection_config,
        version=assessment.version or 1,
        created_at=assessment.created_at,
        published_at=assessment.published_at
    )

@router.post("/recruiter/assessments/{assessment_id}/publish", response_model=AssessmentResponse)
def publish_assessment(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Publish a validated assessment so it can be assigned to shortlisted candidates."""
    assessment = AssessmentService.publish_assessment(db, recruiter, assessment_id)
    return AssessmentResponse(
        id=assessment.id,
        job_id=assessment.job_id,
        job_title=assessment.job.title if assessment.job else None,
        recruiter_id=assessment.recruiter_id,
        title=assessment.title,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        total_marks=assessment.total_marks,
        passing_marks=assessment.passing_marks,
        question_count=len(assessment.questions),
        status=assessment.status.value,
        randomize_questions=assessment.randomize_questions,
        randomize_options=assessment.randomize_options,
        auto_selection_config=assessment.auto_selection_config,
        version=assessment.version or 1,
        created_at=assessment.created_at,
        published_at=assessment.published_at
    )

@router.get("/recruiter/assessments/{assessment_id}/shortlisted-candidates", response_model=List[ShortlistedCandidateItem])
def get_shortlisted_candidates(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all shortlisted candidates for the assessment's job."""
    return AssessmentService.get_shortlisted_candidates_for_job(db, recruiter, assessment_id)

@router.post("/recruiter/assessments/{assessment_id}/assign", response_model=List[CandidateAssignmentResponse])
def assign_assessment(
    assessment_id: str,
    req: AssessmentAssignRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Assign published assessment to selected shortlisted candidates."""
    assignments = AssessmentService.assign_to_candidates(
        db, recruiter, assessment_id, req.candidate_ids, req.deadline_at
    )
    result = []
    for asgn in assignments:
        cand_user = asgn.candidate.user if (asgn.candidate and asgn.candidate.user) else None
        assessment = asgn.assessment
        result.append(CandidateAssignmentResponse(
            id=asgn.id,
            assessment_id=asgn.assessment_id,
            assessment_title=assessment.title if assessment else "",
            job_id=assessment.job_id if assessment else "",
            job_title=assessment.job.title if (assessment and assessment.job) else "",
            candidate_id=asgn.candidate_id,
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            application_id=asgn.application_id,
            status=asgn.status.value,
            assigned_at=asgn.assigned_at,
            deadline_at=asgn.deadline_at,
            duration_minutes=assessment.duration_minutes if assessment else 0,
            total_marks=assessment.total_marks if assessment else 0,
            passing_marks=assessment.passing_marks if assessment else 0,
            question_count=len(assessment.questions) if assessment else 0,
            has_started=asgn.attempt is not None,
            is_completed=asgn.result is not None,
            result=asgn.result.result.value if asgn.result else None,
            marks_obtained=asgn.result.marks_obtained if asgn.result else None,
            percentage=asgn.result.percentage if asgn.result else None
        ))
    return result

@router.get("/recruiter/assessments/{assessment_id}/assignments", response_model=List[CandidateAssignmentResponse])
def list_assessment_assignments(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all candidate assignments for a specific assessment."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    if assessment.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    assignments = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.assessment_id == assessment.id
    ).order_by(CandidateAssessmentAssignment.assigned_at.desc()).all()

    result = []
    for asgn in assignments:
        cand_user = asgn.candidate.user if (asgn.candidate and asgn.candidate.user) else None
        result.append(CandidateAssignmentResponse(
            id=asgn.id,
            assessment_id=asgn.assessment_id,
            assessment_title=assessment.title,
            job_id=assessment.job_id,
            job_title=assessment.job.title if assessment.job else "",
            candidate_id=asgn.candidate_id,
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            application_id=asgn.application_id,
            status=asgn.status.value,
            assigned_at=asgn.assigned_at,
            deadline_at=asgn.deadline_at,
            duration_minutes=assessment.duration_minutes,
            total_marks=assessment.total_marks,
            passing_marks=assessment.passing_marks,
            question_count=len(assessment.questions),
            has_started=asgn.attempt is not None,
            is_completed=asgn.result is not None,
            result=asgn.result.result.value if asgn.result else None,
            marks_obtained=asgn.result.marks_obtained if asgn.result else None,
            percentage=asgn.result.percentage if asgn.result else None
        ))
    return result

@router.get("/recruiter/assessments/{assessment_id}/results", response_model=List[CandidateAssignmentResponse])
def list_assessment_results(
    assessment_id: str,
    filter_status: Optional[str] = Query("all"),  # all, assigned, in_progress, passed, failed, expired
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Filter and view candidate assessment results."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    if assessment.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    query = db.query(CandidateAssessmentAssignment).filter(
        CandidateAssessmentAssignment.assessment_id == assessment.id
    )

    if filter_status and filter_status != "all":
        status_map = {
            "assigned": AssessmentAssignmentStatusEnum.ASSIGNED,
            "in_progress": AssessmentAssignmentStatusEnum.STARTED,
            "passed": AssessmentAssignmentStatusEnum.PASSED,
            "failed": AssessmentAssignmentStatusEnum.FAILED,
            "expired": AssessmentAssignmentStatusEnum.EXPIRED
        }
        if filter_status.lower() in status_map:
            query = query.filter(CandidateAssessmentAssignment.status == status_map[filter_status.lower()])

    assignments = query.order_by(CandidateAssessmentAssignment.assigned_at.desc()).all()
    result = []
    for asgn in assignments:
        cand_user = asgn.candidate.user if (asgn.candidate and asgn.candidate.user) else None
        result.append(CandidateAssignmentResponse(
            id=asgn.id,
            assessment_id=asgn.assessment_id,
            assessment_title=assessment.title,
            job_id=assessment.job_id,
            job_title=assessment.job.title if assessment.job else "",
            candidate_id=asgn.candidate_id,
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            application_id=asgn.application_id,
            status=asgn.status.value,
            assigned_at=asgn.assigned_at,
            deadline_at=asgn.deadline_at,
            duration_minutes=assessment.duration_minutes,
            total_marks=assessment.total_marks,
            passing_marks=assessment.passing_marks,
            question_count=len(assessment.questions),
            has_started=asgn.attempt is not None,
            is_completed=asgn.result is not None,
            result=asgn.result.result.value if asgn.result else None,
            marks_obtained=asgn.result.marks_obtained if asgn.result else None,
            percentage=asgn.result.percentage if asgn.result else None
        ))
    return result

@router.get("/recruiter/assessments/{assessment_id}/comparison", response_model=AssessmentComparisonResponse)
def get_assessment_comparison(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Candidate comparison table and recruiter analytics for an assessment.
    Provides topic-wise & difficulty-wise performance, time taken, and score distribution.
    """
    return AssessmentService.get_assessment_comparison_and_analytics(db, recruiter, assessment_id)

# ==============================================================================
# CANDIDATE ASSESSMENT APIS
# ==============================================================================

@router.get("/candidate/assessments", response_model=List[CandidateAssignmentResponse])
def list_candidate_assigned_assessments(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    List all first-round assessments assigned to the logged-in candidate.
    PRIVACY CONTRACT: Never reveals scores, percentages, or correct answers to candidates.
    """
    assignments = (
        db.query(CandidateAssessmentAssignment)
        .join(Assessment, CandidateAssessmentAssignment.assessment_id == Assessment.id)
        .filter(
            CandidateAssessmentAssignment.candidate_id == candidate.id,
            Assessment.status == AssessmentStatusEnum.PUBLISHED
        )
        .order_by(CandidateAssessmentAssignment.assigned_at.desc())
        .all()
    )

    resp = []
    for asgn in assignments:
        assessment = asgn.assessment
        job = assessment.job if assessment else None
        cand_user = candidate.user

        is_done = asgn.result is not None or asgn.status in [
            AssessmentAssignmentStatusEnum.SUBMITTED,
            AssessmentAssignmentStatusEnum.PASSED,
            AssessmentAssignmentStatusEnum.FAILED,
            AssessmentAssignmentStatusEnum.EXPIRED
        ]

        resp.append(CandidateAssignmentResponse(
            id=asgn.id,
            assessment_id=asgn.assessment_id,
            assessment_title=assessment.title if assessment else "",
            job_id=assessment.job_id if assessment else "",
            job_title=job.title if job else "",
            candidate_id=asgn.candidate_id,
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            application_id=asgn.application_id,
            status=asgn.status.value,
            review_status=asgn.review_status or "PENDING_REVIEW",
            final_decision=asgn.final_decision,
            decision_reason=None,  # Private to recruiter
            reviewed_at=asgn.reviewed_at,
            assigned_at=asgn.assigned_at,
            deadline_at=asgn.deadline_at,
            duration_minutes=assessment.duration_minutes if assessment else 0,
            total_marks=assessment.total_marks if assessment else 0,
            passing_marks=assessment.passing_marks if assessment else 0,
            question_count=len(assessment.questions) if assessment else 0,
            has_started=asgn.attempt is not None,
            is_completed=is_done,
            result=None,          # Confidential
            marks_obtained=None,  # Confidential
            percentage=None       # Confidential
        ))
    return resp

@router.get("/candidate/assessments/{assignment_id}/instructions", response_model=CandidateAssessmentInstructions)
def get_assessment_instructions(
    assignment_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Fetch instructions and metadata for an assigned assessment before starting."""
    info = AssessmentService.get_candidate_instructions(db, candidate, assignment_id)
    return CandidateAssessmentInstructions(**info)

@router.post("/candidate/assessments/{assignment_id}/start", response_model=AttemptStatusResponse)
def start_or_resume_assessment(
    assignment_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Start a new assessment attempt or resume an active one.
    Enforces one-attempt policy and calculates server-controlled deadline.
    """
    return AssessmentService.start_or_resume_attempt(db, candidate, assignment_id)

@router.get("/candidate/assessments/{assignment_id}/attempt", response_model=AttemptStatusResponse)
def get_current_attempt_status(
    assignment_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Fetch active attempt status, saved answers, and server-calculated remaining time."""
    return AssessmentService.start_or_resume_attempt(db, candidate, assignment_id)

@router.post("/candidate/assessments/attempts/{attempt_id}/answers")
def save_candidate_answers(
    attempt_id: str,
    req: SaveAnswersRequest,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Save or update answers while assessment is IN_PROGRESS."""
    answers_dicts = [a.model_dump() for a in req.answers]
    return AssessmentService.save_candidate_answers(db, candidate, attempt_id, answers_dicts)

@router.post("/candidate/assessments/attempts/{attempt_id}/submit", response_model=CandidateSubmissionConfirmationResponse)
def submit_assessment(
    attempt_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Finalize and submit the assessment attempt.
    Privately calculates scores and places attempt in PENDING_REVIEW.
    Returns submission confirmation; strictly withholds scores and PASS/FAIL status.
    """
    return AssessmentService.evaluate_and_submit(db, candidate, attempt_id, is_auto_timeout=False)

@router.post("/candidate/assessments/attempts/{attempt_id}/session-recording", response_model=Dict[str, Any])
def upload_session_recording_metadata(
    attempt_id: str,
    req: SessionRecordingUploadRequest,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Associate Cloudinary session video recording metadata with a Round 1 MCQ attempt.
    """
    attempt = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == attempt_id,
        AssessmentAttempt.candidate_id == candidate.id
    ).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found.")

    asset = db.query(MediaAsset).filter(
        or_(
            MediaAsset.public_id == req.public_id,
            and_(
                MediaAsset.attempt_id == attempt.id,
                MediaAsset.assessment_type == "MCQ"
            )
        )
    ).first()

    if not asset:
        asset = MediaAsset(
            public_id=req.public_id,
            asset_id=req.asset_id,
            candidate_id=candidate.id,
            job_id=attempt.assessment.job_id if attempt.assessment else None,
            assessment_id=attempt.assessment_id,
            assessment_type="MCQ",
            attempt_id=attempt.id,
            original_filename=req.original_filename or f"assessment_session_{attempt.id}.webm",
            resource_type=req.resource_type or "video",
            file_format=req.file_format or "webm",
            file_size_bytes=req.file_size_bytes or 0,
            video_duration_seconds=req.duration_seconds or 0.0,
            secure_url=req.secure_url,
            playback_url=req.playback_url or req.secure_url,
            folder="skillsphere/assessments",
            upload_status="COMPLETED",
            access_classification="CONFIDENTIAL",
            uploader_user_id=candidate.user_id
        )
        db.add(asset)
        db.flush()
    else:
        asset.public_id = req.public_id
        asset.asset_id = req.asset_id
        asset.attempt_id = attempt.id
        asset.assessment_id = attempt.assessment_id
        asset.assessment_type = "MCQ"
        asset.secure_url = req.secure_url
        asset.playback_url = req.playback_url or req.secure_url
        asset.video_duration_seconds = req.duration_seconds or asset.video_duration_seconds
        asset.file_size_bytes = req.file_size_bytes or asset.file_size_bytes
        asset.upload_status = "COMPLETED"

    attempt.session_recording_asset_id = asset.id
    db.commit()
    db.refresh(asset)

    return {
        "status": "COMPLETED",
        "media_asset_id": asset.id,
        "public_id": asset.public_id,
        "secure_url": asset.secure_url
    }

@router.get("/candidate/assessments/{assignment_id}/result", response_model=CandidateAssessmentStatusResponse)
def get_candidate_result(
    assignment_id: str,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Get candidate-facing assessment status and feedback.
    Shows PENDING_REVIEW or recruiter final decision message without leaking scores.
    """
    return AssessmentService.get_candidate_status(db, candidate, assignment_id)
