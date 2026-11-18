import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_recruiter, get_current_candidate
from app.models.models import (
    User, RoleEnum, Candidate, Recruiter, Job, Application,
    VideoAssessment, VideoAssessmentQuestion, CandidateVideoAssignment,
    CandidateVideoResponse, MediaAsset
)
from app.schemas.schemas import (
    VideoAssessmentCreate, VideoAssessmentResponse,
    VideoAssessmentQuestionResponse, CandidateVideoAssignmentResponse,
    CandidateVideoAssignmentDetailResponse, CandidateVideoResponseCreate,
    CandidateVideoResponseItem, VideoAssessmentReviewRequest
)
from app.services.activity_service import create_notification, create_audit_log
from app.services.cloudinary_service import CloudinaryService

router = APIRouter(tags=["Video Assessments"])

def serialize_video_assessment(va: VideoAssessment) -> VideoAssessmentResponse:
    job_title = va.job.title if va.job else None
    questions = [
        VideoAssessmentQuestionResponse(
            id=q.id,
            video_assessment_id=q.video_assessment_id,
            order_num=q.order_num,
            question_text=q.question_text,
            question_instructions=q.question_instructions,
            max_duration_seconds=q.max_duration_seconds,
            prep_time_seconds=q.prep_time_seconds,
            retake_limit=q.retake_limit,
            is_required=q.is_required,
            created_at=q.created_at
        )
        for q in sorted(va.questions, key=lambda x: x.order_num)
    ]
    return VideoAssessmentResponse(
        id=va.id,
        job_id=va.job_id,
        recruiter_id=va.recruiter_id,
        title=va.title,
        description=va.description,
        instructions=va.instructions,
        total_questions=len(questions),
        submission_deadline=va.submission_deadline,
        status=va.status,
        created_at=va.created_at,
        updated_at=va.updated_at,
        job_title=job_title,
        questions=questions
    )

# ============================================================================
# RECRUITER VIDEO ASSESSMENT MANAGEMENT
# ============================================================================

@router.post("/video-assessments", response_model=VideoAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_video_assessment(
    req: VideoAssessmentCreate,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Create a new video assessment configuration with structured video prompts.
    Recruiter configures instructions, prep time, max duration, retake limits, and submission deadline.
    """
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if job.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only create assessments for your own job postings.")

    if not req.questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one video question is required.")

    status_val = "PUBLISHED"
    req_status = getattr(req, "status", None)
    if req_status == "DRAFT":
        status_val = "DRAFT"
    elif req_status in ["PUBLISHED", "ACTIVE"]:
        status_val = "PUBLISHED"

    va = VideoAssessment(
        job_id=job.id,
        recruiter_id=recruiter.id,
        title=req.title,
        description=req.description,
        instructions=req.instructions,
        total_questions=len(req.questions),
        submission_deadline=req.submission_deadline,
        status=status_val
    )
    db.add(va)
    db.flush()

    for i, q in enumerate(req.questions, 1):
        question = VideoAssessmentQuestion(
            video_assessment_id=va.id,
            order_num=q.order_num or i,
            question_text=q.question_text,
            question_instructions=q.question_instructions,
            max_duration_seconds=q.max_duration_seconds,
            prep_time_seconds=q.prep_time_seconds,
            retake_limit=q.retake_limit,
            is_required=q.is_required
        )
        db.add(question)

    db.commit()
    db.refresh(va)

    create_audit_log(
        db=db,
        actor_id=recruiter.user_id,
        action_type="VIDEO_ASSESSMENT_CREATE",
        target_resource="VideoAssessment",
        target_id=va.id,
        details={"job_id": job.id, "title": va.title, "questions_count": len(req.questions)}
    )

    return serialize_video_assessment(va)

@router.get("/video-assessments", response_model=List[VideoAssessmentResponse])
def list_video_assessments(
    job_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List video assessments created by the recruiter."""
    query = db.query(VideoAssessment)
    if current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            return []
        query = query.filter(VideoAssessment.recruiter_id == recruiter.id)
    elif current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters and admins can list video assessments.")

    if job_id:
        query = query.filter(VideoAssessment.job_id == job_id)

    assessments = query.order_by(VideoAssessment.created_at.desc()).all()
    return [serialize_video_assessment(va) for va in assessments]

@router.get("/video-assessments/{assessment_id}", response_model=VideoAssessmentResponse)
def get_video_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get video assessment details with questions."""
    va = db.query(VideoAssessment).filter(VideoAssessment.id == assessment_id).first()
    if not va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video assessment not found.")
    return serialize_video_assessment(va)

@router.post("/video-assessments/{assessment_id}/publish", response_model=VideoAssessmentResponse)
def publish_video_assessment(
    assessment_id: str,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Publish a draft video assessment, making it assignable to shortlisted candidates.
    Requires at least one question.
    """
    va = db.query(VideoAssessment).filter(VideoAssessment.id == assessment_id).first()
    if not va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video assessment not found.")

    if va.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this video assessment.")

    if not va.questions or len(va.questions) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish a video assessment with no questions."
        )

    va.status = "PUBLISHED"
    db.commit()
    db.refresh(va)

    create_audit_log(
        db=db,
        actor_id=recruiter.user_id,
        action_type="VIDEO_ASSESSMENT_PUBLISH",
        target_resource="VideoAssessment",
        target_id=va.id,
        details={"job_id": va.job_id, "title": va.title, "questions_count": len(va.questions)}
    )

    return serialize_video_assessment(va)

@router.post("/video-assessments/{assessment_id}/assign", response_model=List[CandidateVideoAssignmentResponse])
def assign_video_assessment(
    assessment_id: str,
    payload: Dict[str, Any],
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Assign a video assessment to shortlisted candidates/applications.
    """
    va = db.query(VideoAssessment).filter(VideoAssessment.id == assessment_id).first()
    if not va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video assessment not found.")

    if va.recruiter_id != recruiter.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You can only assign your own assessments.")

    if va.status != "PUBLISHED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign a draft video assessment. Please publish it first."
        )

    application_ids = payload.get("application_ids", [])
    if not application_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application_ids list is required.")

    created_assignments = []
    for app_id in application_ids:
        app_record = db.query(Application).filter(Application.id == app_id).first()
        if not app_record:
            continue

        existing = db.query(CandidateVideoAssignment).filter(
            CandidateVideoAssignment.video_assessment_id == va.id,
            CandidateVideoAssignment.application_id == app_record.id
        ).first()

        if existing:
            created_assignments.append(existing)
            continue

        assignment = CandidateVideoAssignment(
            video_assessment_id=va.id,
            candidate_id=app_record.candidate_id,
            application_id=app_record.id,
            status="ASSIGNED",
            review_status="PENDING"
        )
        db.add(assignment)
        db.flush()

        # In-app notification to candidate
        create_notification(
            db=db,
            user_id=app_record.candidate.user_id,
            title="Video Assessment Assigned",
            message=f"You have been assigned the video assessment '{va.title}' for '{app_record.job.title}'.",
            notification_type="VIDEO_ASSESSMENT_ASSIGNED",
            link="/dashboard?tab=video-assessments"
        )
        created_assignments.append(assignment)

    db.commit()

    results = []
    for a in created_assignments:
        db.refresh(a)
        job_title = a.application.job.title if (a.application and a.application.job) else "Job"
        results.append(CandidateVideoAssignmentResponse(
            id=a.id,
            video_assessment_id=a.video_assessment_id,
            candidate_id=a.candidate_id,
            application_id=a.application_id,
            title=va.title,
            job_title=job_title,
            total_questions=va.total_questions,
            status=a.status,
            review_status=a.review_status,
            assigned_at=a.assigned_at,
            submitted_at=a.submitted_at
        ))
    return results

@router.get("/video-assessments/{assessment_id}/assignments", response_model=List[CandidateVideoAssignmentResponse])
def list_video_assessment_assignments(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all candidate assignments for a specific video assessment."""
    va = db.query(VideoAssessment).filter(VideoAssessment.id == assessment_id).first()
    if not va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video assessment not found.")

    assignments = db.query(CandidateVideoAssignment).filter(
        CandidateVideoAssignment.video_assessment_id == va.id
    ).order_by(CandidateVideoAssignment.assigned_at.desc()).all()

    results = []
    for a in assignments:
        job_title = a.application.job.title if (a.application and a.application.job) else "Job"
        results.append(CandidateVideoAssignmentResponse(
            id=a.id,
            video_assessment_id=a.video_assessment_id,
            candidate_id=a.candidate_id,
            application_id=a.application_id,
            title=va.title,
            job_title=job_title,
            total_questions=va.total_questions,
            status=a.status,
            review_status=a.review_status,
            assigned_at=a.assigned_at,
            submitted_at=a.submitted_at
        ))
    return results

@router.get("/video-assessments/assignments/{assignment_id}/review", response_model=CandidateVideoAssignmentDetailResponse)
def get_assignment_review_details(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recruiter review view of a candidate's video assessment:
    Questions and video responses with signed playback URLs.
    """
    assignment = db.query(CandidateVideoAssignment).filter(CandidateVideoAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    va = assignment.video_assessment
    if not va:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video assessment not found.")
    job_title = assignment.application.job.title if (assignment.application and assignment.application.job) else "Job"

    questions_res = [
        VideoAssessmentQuestionResponse(
            id=q.id,
            video_assessment_id=q.video_assessment_id,
            order_num=q.order_num,
            question_text=q.question_text,
            question_instructions=q.question_instructions,
            max_duration_seconds=q.max_duration_seconds,
            prep_time_seconds=q.prep_time_seconds,
            retake_limit=q.retake_limit,
            is_required=q.is_required,
            created_at=q.created_at
        )
        for q in sorted(va.questions, key=lambda x: x.order_num)
    ]

    responses_res = []
    for r in sorted(assignment.responses, key=lambda x: x.question.order_num if x.question else 0):
        playback_url = None
        thumbnail_url = None
        if r.media_asset:
            playback_url = CloudinaryService.generate_signed_playback_url(
                public_id=r.media_asset.public_id,
                resource_type=r.media_asset.resource_type or "video",
                file_format=r.media_asset.file_format,
                secure_url=r.media_asset.secure_url
            )
            thumbnail_url = CloudinaryService.generate_thumbnail_url(
                public_id=r.media_asset.public_id,
                resource_type=r.media_asset.resource_type or "video"
            )

        responses_res.append(CandidateVideoResponseItem(
            id=r.id,
            question_id=r.question_id,
            question_text=r.question.question_text if r.question else "",
            max_duration_seconds=r.question.max_duration_seconds if r.question else 120,
            media_asset_id=r.media_asset_id,
            duration_seconds=r.duration_seconds,
            retake_count=r.retake_count,
            submitted_at=r.submitted_at,
            playback_url=playback_url,
            thumbnail_url=thumbnail_url,
            recruiter_rating=r.recruiter_rating,
            recruiter_notes=r.recruiter_notes
        ))

    return CandidateVideoAssignmentDetailResponse(
        id=assignment.id,
        video_assessment_id=assignment.video_assessment_id,
        candidate_id=assignment.candidate_id,
        title=va.title,
        description=va.description,
        instructions=va.instructions,
        job_title=job_title,
        status=assignment.status,
        review_status=assignment.review_status,
        assigned_at=assignment.assigned_at,
        submitted_at=assignment.submitted_at,
        questions=questions_res,
        responses=responses_res
    )

@router.post("/video-assessments/assignments/{assignment_id}/evaluate", response_model=CandidateVideoAssignmentDetailResponse)
def evaluate_candidate_video_assignment(
    assignment_id: str,
    req: VideoAssessmentReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recruiter grades candidate video responses and marks review status (ACCEPTED, REJECTED, UNDER_REVIEW).
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Only recruiters can evaluate video assessments.")

    assignment = db.query(CandidateVideoAssignment).filter(CandidateVideoAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    assignment.review_status = req.review_status
    if req.overall_score is not None:
        assignment.overall_score = req.overall_score
    if req.recruiter_feedback is not None:
        assignment.recruiter_feedback = req.recruiter_feedback

    if req.question_notes:
        for resp in assignment.responses:
            if resp.question_id in req.question_notes:
                resp.recruiter_notes = req.question_notes[resp.question_id]

    db.commit()
    db.refresh(assignment)

    # In-app notification to candidate if accepted or reviewed
    create_notification(
        db=db,
        user_id=assignment.candidate.user_id,
        title="Video Assessment Evaluated",
        message=f"Your video assessment for '{assignment.video_assessment.title}' has been evaluated.",
        notification_type="VIDEO_ASSESSMENT_EVALUATED",
        link="/dashboard?tab=video-assessments"
    )

    return get_assignment_review_details(assignment_id, current_user, db)

# ============================================================================
# CANDIDATE VIDEO ASSESSMENT WORKFLOW
# ============================================================================

@router.get("/candidate/video-assessments", response_model=List[CandidateVideoAssignmentResponse])
def get_my_video_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all video assessments assigned to the logged-in candidate."""
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        return []

    assignments = (
        db.query(CandidateVideoAssignment)
        .join(VideoAssessment, CandidateVideoAssignment.video_assessment_id == VideoAssessment.id)
        .filter(
            CandidateVideoAssignment.candidate_id == candidate.id,
            VideoAssessment.status == "PUBLISHED"
        )
        .order_by(CandidateVideoAssignment.assigned_at.desc())
        .all()
    )

    results = []
    for a in assignments:
        va = a.video_assessment
        job_title = a.application.job.title if (a.application and a.application.job) else "Job"
        results.append(CandidateVideoAssignmentResponse(
            id=a.id,
            video_assessment_id=a.video_assessment_id,
            candidate_id=a.candidate_id,
            application_id=a.application_id,
            title=va.title if va else "Video Assessment",
            job_title=job_title,
            total_questions=va.total_questions if va else 0,
            status=a.status,
            review_status=a.review_status,
            assigned_at=a.assigned_at,
            submitted_at=a.submitted_at
        ))
    return results

@router.get("/candidate/video-assessments/{assignment_id}", response_model=CandidateVideoAssignmentDetailResponse)
def get_candidate_video_assignment_detail(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Candidate views video assessment instructions, questions, timers, and submission status."""
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate profile not found.")

    assignment = db.query(CandidateVideoAssignment).filter(CandidateVideoAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    if current_user.role != RoleEnum.ADMIN and assignment.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot access another candidate's video assessment.")

    va = assignment.video_assessment
    if not va or (current_user.role != RoleEnum.ADMIN and va.status != "PUBLISHED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This video assessment is not published or is currently unavailable.")
    job_title = assignment.application.job.title if (assignment.application and assignment.application.job) else "Job"

    questions_res = [
        VideoAssessmentQuestionResponse(
            id=q.id,
            video_assessment_id=q.video_assessment_id,
            order_num=q.order_num,
            question_text=q.question_text,
            question_instructions=q.question_instructions,
            max_duration_seconds=q.max_duration_seconds,
            prep_time_seconds=q.prep_time_seconds,
            retake_limit=q.retake_limit,
            is_required=q.is_required,
            created_at=q.created_at
        )
        for q in sorted(va.questions, key=lambda x: x.order_num)
    ]

    responses_res = []
    for r in sorted(assignment.responses, key=lambda x: x.question.order_num if x.question else 0):
        playback_url = None
        thumbnail_url = None
        if r.media_asset:
            playback_url = CloudinaryService.generate_signed_playback_url(
                public_id=r.media_asset.public_id,
                resource_type=r.media_asset.resource_type or "video",
                file_format=r.media_asset.file_format,
                secure_url=r.media_asset.secure_url
            )
            thumbnail_url = CloudinaryService.generate_thumbnail_url(
                public_id=r.media_asset.public_id,
                resource_type=r.media_asset.resource_type or "video"
            )

        responses_res.append(CandidateVideoResponseItem(
            id=r.id,
            question_id=r.question_id,
            question_text=r.question.question_text if r.question else "",
            max_duration_seconds=r.question.max_duration_seconds if r.question else 120,
            media_asset_id=r.media_asset_id,
            duration_seconds=r.duration_seconds,
            retake_count=r.retake_count,
            submitted_at=r.submitted_at,
            playback_url=playback_url,
            thumbnail_url=thumbnail_url,
            recruiter_rating=None,  # Do not leak recruiter ratings before recruiter decisions
            recruiter_notes=None
        ))

    return CandidateVideoAssignmentDetailResponse(
        id=assignment.id,
        video_assessment_id=assignment.video_assessment_id,
        candidate_id=assignment.candidate_id,
        title=va.title,
        description=va.description,
        instructions=va.instructions,
        job_title=job_title,
        status=assignment.status,
        review_status=assignment.review_status,
        assigned_at=assignment.assigned_at,
        submitted_at=assignment.submitted_at,
        questions=questions_res,
        responses=responses_res
    )

@router.post("/candidate/video-assessments/{assignment_id}/responses", response_model=CandidateVideoResponseItem)
def submit_question_response(
    assignment_id: str,
    resp_in: CandidateVideoResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Candidate submits video recording for a specific question.
    Enforces retake limits and associates Cloudinary MediaAsset.
    """
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate profile not found.")

    assignment = db.query(CandidateVideoAssignment).filter(CandidateVideoAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    if current_user.role != RoleEnum.ADMIN and assignment.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot submit responses for another candidate.")

    if assignment.status == "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This video assessment has already been finalized.")

    question = db.query(VideoAssessmentQuestion).filter(
        VideoAssessmentQuestion.id == resp_in.question_id,
        VideoAssessmentQuestion.video_assessment_id == assignment.video_assessment_id
    ).first()

    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in this assessment.")

    # Enforce retake limit
    if resp_in.retake_count > question.retake_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Retake limit exceeded: Question allows at most {question.retake_limit} retake(s)."
        )

    # Check media asset exists
    media_asset = db.query(MediaAsset).filter(MediaAsset.id == resp_in.media_asset_id).first()
    if not media_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")

    if assignment.video_assessment and assignment.video_assessment.status != "PUBLISHED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This video assessment is not published or is currently unavailable.")

    media_asset.video_assessment_id = assignment.video_assessment_id
    media_asset.question_id = question.id
    media_asset.assessment_type = "VIDEO_ASSESSMENT"

    # Update or create response
    existing_response = db.query(CandidateVideoResponse).filter(
        CandidateVideoResponse.assignment_id == assignment.id,
        CandidateVideoResponse.question_id == question.id
    ).first()

    if existing_response:
        existing_response.media_asset_id = media_asset.id
        existing_response.duration_seconds = resp_in.duration_seconds
        existing_response.retake_count = resp_in.retake_count
        existing_response.submitted_at = datetime.now(timezone.utc)
        resp_obj = existing_response
    else:
        resp_obj = CandidateVideoResponse(
            assignment_id=assignment.id,
            question_id=question.id,
            media_asset_id=media_asset.id,
            duration_seconds=resp_in.duration_seconds,
            retake_count=resp_in.retake_count
        )
        db.add(resp_obj)

    # Mark assignment as in progress
    if assignment.status == "ASSIGNED":
        assignment.status = "IN_PROGRESS"

    db.commit()
    db.refresh(resp_obj)

    playback_url = CloudinaryService.generate_signed_playback_url(
        public_id=media_asset.public_id,
        resource_type=media_asset.resource_type or "video",
        file_format=media_asset.file_format,
        secure_url=media_asset.secure_url
    )
    thumbnail_url = CloudinaryService.generate_thumbnail_url(
        public_id=media_asset.public_id,
        resource_type=media_asset.resource_type or "video"
    )

    return CandidateVideoResponseItem(
        id=resp_obj.id,
        question_id=resp_obj.question_id,
        question_text=question.question_text,
        max_duration_seconds=question.max_duration_seconds,
        media_asset_id=resp_obj.media_asset_id,
        duration_seconds=resp_obj.duration_seconds,
        retake_count=resp_obj.retake_count,
        submitted_at=resp_obj.submitted_at,
        playback_url=playback_url,
        thumbnail_url=thumbnail_url,
        recruiter_rating=None,
        recruiter_notes=None
    )

@router.post("/candidate/video-assessments/{assignment_id}/finalize", response_model=CandidateVideoAssignmentDetailResponse)
def finalize_video_assessment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Candidate finalizes and submits their video assessment.
    Verifies that all required questions have recorded responses.
    Transitions status to COMPLETED and sets review_status to PENDING.
    """
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate profile not found.")

    assignment = db.query(CandidateVideoAssignment).filter(CandidateVideoAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

    if current_user.role != RoleEnum.ADMIN and assignment.candidate_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot finalize another candidate's assessment.")

    # Check that required questions are answered
    required_questions = [q for q in assignment.video_assessment.questions if q.is_required]
    answered_question_ids = {r.question_id for r in assignment.responses}
    missing_required = [q for q in required_questions if q.id not in answered_question_ids]

    if missing_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please record responses for all required questions before submitting ({len(missing_required)} missing)."
        )

    assignment.status = "COMPLETED"
    assignment.review_status = "PENDING"
    assignment.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assignment)

    # In-app notification to recruiter
    if assignment.video_assessment.recruiter:
        create_notification(
            db=db,
            user_id=assignment.video_assessment.recruiter.user_id,
            title="Video Assessment Submitted",
            message=f"{current_user.name} submitted video responses for '{assignment.video_assessment.title}'.",
            notification_type="VIDEO_ASSESSMENT_SUBMITTED",
            link="/recruiter/dashboard?tab=video-assessments"
        )

    return get_candidate_video_assignment_detail(assignment_id, current_user, db)
