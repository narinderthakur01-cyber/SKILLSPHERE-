import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_recruiter, get_current_admin
from app.models.models import User, RoleEnum, Recruiter, Assessment, QuestionBankItem
from app.schemas.schemas import (
    QuestionBankItemCreate, QuestionBankItemUpdate, QuestionBankItemResponse,
    QuestionCollectionCreate, QuestionCollectionResponse,
    AutoGenerateAssessmentRequest, BulkImportRequest, BulkImportPreviewResponse,
    DuplicateCheckRequest, DuplicateCheckResponse, AssessmentAnalyticsResponse,
    AssessmentResponse, AssessmentQuestionCreate, AssessmentOptionCreate, AssessmentCreate,
    QuestionUploadExtractResponse, BatchImportRequest, BatchImportResponse
)
from app.services.question_bank_service import QuestionBankService
from app.services.assessment_service import AssessmentService
from app.services.question_extractor_service import QuestionExtractorService

router = APIRouter(prefix="/question-bank", tags=["Question Bank & Assessment Management"])

# ==============================================================================
# QUESTION BANK BROWSING & MANAGEMENT
# ==============================================================================

@router.get("/questions")
def list_questions(
    technology: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status_filter: str = Query("ACTIVE", alias="status"),
    only_mine: bool = Query(False),
    include_custom: bool = Query(True),
    page: Optional[int] = Query(None),
    skip: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Browse questions with flexible search, filtering, and pagination."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Question Bank access is restricted to recruiters."
        )
    resolved_page = page if page is not None else ((skip // limit) + 1 if skip is not None else 1)
    return QuestionBankService.list_questions(
        db=db,
        user=current_user,
        technology=technology,
        topic=topic,
        difficulty=difficulty,
        search=search,
        status_filter=status_filter,
        only_mine=only_mine,
        page=resolved_page,
        limit=limit
    )

@router.post("/questions", response_model=QuestionBankItemResponse)
def create_question(
    data: QuestionBankItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new question.
    Admins create system-wide predefined questions (is_global=True).
    Recruiters create custom private questions (is_global=False).
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters and admins can create questions.")

    q = QuestionBankService.create_question(db, current_user, data)
    return QuestionBankItemResponse.model_validate(q)

@router.get("/questions/{question_id}", response_model=QuestionBankItemResponse)
def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch single question details."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Question Bank access is restricted to recruiters."
        )
    q = db.query(QuestionBankItem).filter(QuestionBankItem.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")
    return QuestionBankItemResponse.model_validate(q)

@router.put("/questions/{question_id}", response_model=QuestionBankItemResponse)
def update_question(
    question_id: str,
    data: QuestionBankItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update question.
    Admins can modify any question. Recruiters can only modify their own custom questions.
    """
    q = QuestionBankService.update_question(db, current_user, question_id, data)
    return QuestionBankItemResponse.model_validate(q)

@router.post("/questions/{question_id}/duplicate", response_model=QuestionBankItemResponse)
def duplicate_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate a global or existing question into recruiter's custom questions for customized editing."""
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    new_q = QuestionBankService.duplicate_question(db, current_user, question_id)
    return QuestionBankItemResponse.model_validate(new_q)

@router.post("/questions/{question_id}/archive")
def archive_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft-archive a question without deleting historical records."""
    QuestionBankService.archive_question(db, current_user, question_id)
    return {"message": "Question successfully archived."}

@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate_question(
    data: DuplicateCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check whether a question with identical text already exists."""
    is_dup, dup_id, msg = QuestionBankService.check_duplicate(db, data.question_text, data.exclude_id)
    return DuplicateCheckResponse(
        is_duplicate=is_dup,
        similar_question_id=dup_id,
        similarity_reason=msg
    )

@router.get("/technologies")
def get_technologies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available technologies and topics with their question counts."""
    return QuestionBankService.get_technologies_and_topics(db)

@router.get("/availability")
def check_availability(
    technology: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check total active questions available for a given technology/topic and breakdown by difficulty."""
    return QuestionBankService.get_availability(db, technology, topic)

# ==============================================================================
# AUTOMATIC QUESTION SAMPLING & GENERATION
# ==============================================================================

@router.post("/sample")
def sample_questions(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sample questions from the question bank matching technology, topic, and difficulty distribution.
    Payload: {"technology": str, "topic": Optional[str], "count": int, "difficulty_distribution": Optional[Dict[str, int]], "marks_per_question": Optional[int]}
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Question Bank access is restricted to recruiters.")

    technology = data.get("technology", "")
    topic = data.get("topic")
    count = int(data.get("count", 5))
    difficulty_dist = data.get("difficulty_distribution")
    marks_per_q = data.get("marks_per_question")

    items = QuestionBankService.sample_questions_from_bank(
        db=db,
        technology=technology,
        topic=topic,
        count=count,
        difficulty_dist=difficulty_dist,
        marks_per_question=int(marks_per_q) if marks_per_q is not None else None
    )

    results = []
    for q in items:
        opts = [
            {
                "option_key": o.option_key,
                "option_text": o.option_text,
                "is_correct": o.is_correct
            } for o in sorted(q.options, key=lambda x: x.option_key)
        ]
        results.append({
            "bank_question_id": q.id,
            "question_text": q.question_text,
            "explanation": q.explanation,
            "marks": q.marks,
            "difficulty": q.difficulty.value,
            "technology": q.technology,
            "topic": q.topic,
            "options": opts
        })
    return {"count": len(results), "questions": results}

@router.post("/auto-generate-assessment", response_model=AssessmentResponse)
def auto_generate_assessment(
    data: AutoGenerateAssessmentRequest,
    recruiter: Recruiter = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """
    Automatically generate an assessment from the question bank based on criteria.
    Creates isolated snapshots of selected bank questions.
    """
    sampled = QuestionBankService.sample_questions_from_bank(
        db=db,
        technology=data.technology,
        topic=data.topic,
        count=data.question_count,
        difficulty_dist=data.difficulty_distribution,
        marks_per_question=data.marks_per_question
    )

    q_creates = []
    for idx, sq in enumerate(sampled):
        opt_creates = [
            AssessmentOptionCreate(
                option_key=o.option_key,
                option_text=o.option_text,
                is_correct=o.is_correct
            ) for o in sorted(sq.options, key=lambda x: x.option_key)
        ]
        q_creates.append(AssessmentQuestionCreate(
            bank_question_id=sq.id,
            question_text=sq.question_text,
            explanation=sq.explanation,
            order_num=idx + 1,
            marks=sq.marks,
            options=opt_creates
        ))

    calculated_total = sum(sq.marks for sq in sampled)
    passing_marks = data.passing_marks
    if passing_marks > calculated_total:
        passing_marks = max(1, int(calculated_total * 0.6))

    create_payload = AssessmentCreate(
        job_id=data.job_id,
        title=data.title,
        instructions=data.instructions,
        duration_minutes=data.duration_minutes,
        passing_marks=passing_marks,
        randomize_questions=data.randomize_questions,
        randomize_options=data.randomize_options,
        auto_selection_config={
            "technology": data.technology,
            "topic": data.topic,
            "question_count": data.question_count,
            "difficulty_distribution": data.difficulty_distribution,
            "marks_per_question": data.marks_per_question
        },
        questions=q_creates
    )

    assessment = AssessmentService.create_assessment(db, recruiter, create_payload)
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

# ==============================================================================
# RECRUITER QUESTION COLLECTIONS
# ==============================================================================

@router.get("/collections", response_model=List[QuestionCollectionResponse])
def list_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List custom collections belonging to the current user."""
    return QuestionBankService.list_collections(db, current_user)

@router.post("/collections", response_model=QuestionCollectionResponse)
def create_collection(
    data: QuestionCollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save questions into a reusable custom collection."""
    coll = QuestionBankService.create_collection(db, current_user, data)
    return QuestionCollectionResponse.model_validate(coll)

@router.get("/collections/{collection_id}", response_model=QuestionCollectionResponse)
def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single collection with questions."""
    return QuestionBankService.get_collection(db, current_user, collection_id)

# ==============================================================================
# BULK CSV IMPORT
# ==============================================================================

@router.post("/bulk-import", response_model=BulkImportPreviewResponse)
def bulk_import_questions(
    data: BulkImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate or commit questions from CSV.
    Expected CSV columns:
    technology,topic,subtopic,difficulty,question_text,explanation,marks,option_a,option_b,option_c,option_d,correct_option,tags
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    return QuestionBankService.bulk_import_csv(
        db=db,
        user=current_user,
        csv_content=data.csv_content,
        commit=data.commit
    )

# ==============================================================================
# INLINE QUESTION FILE UPLOAD & EXTRACTION PIPELINE
# ==============================================================================

@router.post("/upload-extract", response_model=QuestionUploadExtractResponse)
async def upload_and_extract_questions(
    file: UploadFile = File(...),
    technology: Optional[str] = Form("Python"),
    topic: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and extract MCQs from PDF, DOCX, XLSX, CSV, TXT, or Image files.
    Supports digital PDF text, scanned OCR, table parsing, and duplicate detection.
    Returns preview with validation status for recruiter review.
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.RECRUITER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Recruiter access required.")

    # Validate filename & extension
    original_filename = Path(file.filename).name
    ext = Path(original_filename).suffix.lower()
    if ext not in QuestionExtractorService.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(QuestionExtractorService.SUPPORTED_EXTENSIONS))}"
        )

    # Read content and validate size (max 15MB)
    content = await file.read()
    max_bytes = 15 * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 15MB limit."
        )

    # Secure file save
    upload_dir = Path(settings.UPLOAD_DIR) / "question_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{original_filename}"
    saved_path = upload_dir / safe_filename

    with open(saved_path, "wb") as f:
        f.write(content)

    try:
        result = QuestionExtractorService.extract_from_file(
            file_path=str(saved_path),
            filename=original_filename,
            content_type=file.content_type or "",
            technology_hint=technology or "Python",
            topic_hint=topic,
            db=db
        )
        return QuestionUploadExtractResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extraction failed: {str(e)}"
        )

@router.post("/batch-import", response_model=BatchImportResponse)
def batch_import_questions(
    data: BatchImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save approved extracted questions into the recruiter's Question Bank.
    Enforces required options, verified correct answer keys, and duplicate prevention.
    """
    return QuestionBankService.batch_import_questions(db, current_user, data)

# ==============================================================================
# ASSESSMENT ANALYTICS
# ==============================================================================

@router.get("/assessments/{assessment_id}/analytics", response_model=AssessmentAnalyticsResponse)
def get_assessment_analytics(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed recruiter assessment analytics:
    - Candidate performance distribution & pass/fail percentage
    - Average score
    - Question-by-question correctness vs failure rates
    - Questions with >= 60% failure rate flagged for review
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if current_user.role != RoleEnum.ADMIN:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

    return QuestionBankService.get_assessment_analytics(db, assessment_id)
