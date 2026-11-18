import os
import uuid
import shutil
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_candidate, require_role
from app.models.models import (
    Candidate, Resume, ProcessingStatusEnum, RoleEnum, Skill,
    Job, ResumeAnalysis, User
)
from app.schemas.schemas import (
    ResumeResponse, CandidateProfileResponse, CandidateProfileUpdate,
    ResumeAnalyzeRequest, ResumeAnalyzeResponse, ResumeQualityResponse
)
from app.services.ocr_service import extract_resume_text
from app.services.parser_service import parse_resume_text, SKILL_DISPLAY_MAP
from app.services.matching_service import calculate_skill_match

router = APIRouter(prefix="/resume", tags=["Resumes & OCR"])

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Upload resume file (PDF, JPG, JPEG, PNG <= 10MB).
    Runs PyMuPDF digital extraction + Tesseract OCR fallback, parses candidate data,
    stores resume in database, and returns preview for candidate review.
    """
    # 1. Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: PDF, JPG, JPEG, PNG."
        )

    # 2. Generate unique safe storage path
    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}{file_ext}"
    dest_path = settings.UPLOAD_DIR / stored_filename

    # 3. Read and check file size (max 10MB)
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )

    # Write content to disk
    with open(dest_path, "wb") as f:
        f.write(content)

    # 4. Create initial Resume record in DB
    resume = Resume(
        candidate_id=candidate.id,
        file_name=file.filename,
        file_path=str(dest_path),
        file_type=file.content_type or file_ext,
        file_size=file_size,
        processing_status=ProcessingStatusEnum.PROCESSING
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 5. Execute OCR and parsing pipeline
    try:
        extraction_result = extract_resume_text(str(dest_path), file_ext)
        raw_text = extraction_result.get("text", "")
        
        parsed_data = parse_resume_text(raw_text)
        parsed_data["page_count"] = extraction_result.get("page_count", 1)
        parsed_data["is_scanned"] = extraction_result.get("is_scanned", False)

        # Calculate extraction confidence and identify missing attributes
        missing = []
        if not parsed_data.get("name"): missing.append("name")
        if not parsed_data.get("phone"): missing.append("phone")
        if not parsed_data.get("email"): missing.append("email")
        if not parsed_data.get("education"): missing.append("education")
        if not parsed_data.get("experience"): missing.append("experience")
        if not parsed_data.get("skills"): missing.append("skills")

        conf = round(max(100.0 - (len(missing) * 14.0), 30.0), 1)

        resume.extracted_text = raw_text
        resume.parsed_data = parsed_data
        resume.confidence_score = conf
        resume.missing_fields = missing
        resume.processing_status = ProcessingStatusEnum.COMPLETED
        db.commit()
        db.refresh(resume)

        # Synchronize candidate profile fields from parsed resume data
        if parsed_data.get("name"):
            current_name = candidate.user.name or ""
            if len(parsed_data["name"].split()) >= len(current_name.split()) or not current_name:
                candidate.user.name = parsed_data["name"]

        if parsed_data.get("phone"):
            candidate.phone = parsed_data["phone"]
        if parsed_data.get("education"):
            candidate.education = parsed_data["education"]
        if parsed_data.get("experience"):
            candidate.experience = parsed_data["experience"]
        if parsed_data.get("title"):
            candidate.title = parsed_data["title"]
        if parsed_data.get("total_years_exp") is not None:
            candidate.total_years_exp = parsed_data["total_years_exp"]
        if parsed_data.get("bio") and not candidate.bio:
            candidate.bio = parsed_data["bio"]
            
        # Synchronize detected skills into skills table and candidate_skills association
        for skill_name in parsed_data.get("skills", []):
            skill_record = db.query(Skill).filter(Skill.skill_name == skill_name.lower()).first()
            if not skill_record:
                skill_record = Skill(skill_name=skill_name.lower())
                db.add(skill_record)
                db.commit()
                db.refresh(skill_record)
            if skill_record not in candidate.skills:
                candidate.skills.append(skill_record)
                
        db.commit()

    except Exception as e:
        resume.processing_status = ProcessingStatusEnum.FAILED
        resume.error_message = str(e)
        db.commit()
        db.refresh(resume)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Resume processing error: {str(e)}"
        )

    return ResumeResponse.model_validate(resume)

@router.get("/profile", response_model=CandidateProfileResponse)
def get_candidate_profile(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Retrieve full candidate profile data with verified skills."""
    user = candidate.user
    skill_names = [SKILL_DISPLAY_MAP.get(s.skill_name.lower(), s.skill_name.title()) for s in candidate.skills]
    
    return CandidateProfileResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        name=user.name,
        email=user.email,
        phone=candidate.phone,
        title=candidate.title,
        location=candidate.location,
        bio=candidate.bio,
        education=candidate.education or [],
        experience=candidate.experience or [],
        total_years_exp=candidate.total_years_exp or 0.0,
        skills=skill_names
    )

@router.put("/profile", response_model=CandidateProfileResponse)
def update_candidate_profile(
    profile_in: CandidateProfileUpdate,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Save reviewed and verified candidate profile data from editable review form."""
    user = candidate.user
    
    if profile_in.name:
        user.name = profile_in.name
    if profile_in.phone is not None:
        candidate.phone = profile_in.phone
    if profile_in.title is not None:
        candidate.title = profile_in.title
    if profile_in.location is not None:
        candidate.location = profile_in.location
    if profile_in.bio is not None:
        candidate.bio = profile_in.bio
    if profile_in.education is not None:
        candidate.education = profile_in.education
    if profile_in.experience is not None:
        candidate.experience = profile_in.experience
    if profile_in.total_years_exp is not None:
        candidate.total_years_exp = profile_in.total_years_exp

    if profile_in.skills is not None:
        candidate.skills = []
        for s_name in profile_in.skills:
            clean_name = s_name.strip().lower()
            if not clean_name:
                continue
            skill_record = db.query(Skill).filter(Skill.skill_name == clean_name).first()
            if not skill_record:
                skill_record = Skill(skill_name=clean_name)
                db.add(skill_record)
                db.commit()
                db.refresh(skill_record)
            if skill_record not in candidate.skills:
                candidate.skills.append(skill_record)

    db.commit()
    db.refresh(candidate)

    skill_names = [SKILL_DISPLAY_MAP.get(s.skill_name.lower(), s.skill_name.title()) for s in candidate.skills]
    return CandidateProfileResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        name=user.name,
        email=user.email,
        phone=candidate.phone,
        title=candidate.title,
        location=candidate.location,
        bio=candidate.bio,
        education=candidate.education or [],
        experience=candidate.experience or [],
        total_years_exp=candidate.total_years_exp or 0.0,
        skills=skill_names
    )

@router.get("/my-resumes", response_model=List[ResumeResponse])
def get_my_resumes(
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """List all resumes uploaded by the authenticated candidate."""
    resumes = db.query(Resume).filter(
        Resume.candidate_id == candidate.id
    ).order_by(Resume.upload_date.desc()).all()
    return [ResumeResponse.model_validate(r) for r in resumes]

@router.get("/{resume_id}/download")
def download_resume(
    resume_id: str,
    db: Session = Depends(get_db)
):
    """Download stored resume file by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found."
        )
    if not os.path.exists(resume.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume physical file not found on disk."
        )
    return FileResponse(
        path=resume.file_path,
        filename=resume.file_name,
        media_type=resume.file_type or "application/pdf"
    )

@router.post("/analyze", response_model=ResumeAnalyzeResponse)
def analyze_resume_match(
    request: ResumeAnalyzeRequest,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    Compare candidate resume skills with job required skills.
    Calculates deterministic match score %, matched vs missing skills, and gap recommendations.
    Edge case: if job has 0 required skills, returns match_score: None with message.
    """
    # 1. Verify candidate owns the resume
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.candidate_id == candidate.id
    ).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to you."
        )

    # 2. Fetch the target job
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found."
        )

    # 3. Collect candidate skills (from resume parsed_data and candidate verified skills)
    resume_skills = resume.parsed_data.get("skills", []) if resume.parsed_data else []
    profile_skills = [s.skill_name for s in candidate.skills]
    combined_candidate_skills = list(set(resume_skills + profile_skills))

    # 4. Collect required job skills
    job_skills = [js.skill.skill_name for js in job.job_skills]

    # 5. Run matching calculation
    analysis_result = calculate_skill_match(combined_candidate_skills, job_skills)

    # 6. Save or update ResumeAnalysis record
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.resume_id == resume.id,
        ResumeAnalysis.job_id == job.id
    ).first()
    
    if not analysis:
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            job_id=job.id,
            match_score=analysis_result["match_score"],
            matched_skills=analysis_result["matched_skills"],
            missing_skills=analysis_result["missing_skills"],
            recommendations=analysis_result["recommendations"]
        )
        db.add(analysis)
    else:
        analysis.match_score = analysis_result["match_score"]
        analysis.matched_skills = analysis_result["matched_skills"]
        analysis.missing_skills = analysis_result["missing_skills"]
        analysis.recommendations = analysis_result["recommendations"]

    db.commit()

    return ResumeAnalyzeResponse(
        match_score=analysis_result["match_score"],
        matched_skills=analysis_result["matched_skills"],
        missing_skills=analysis_result["missing_skills"],
        recommendations=analysis_result["recommendations"],
        message=analysis_result["message"]
    )

@router.post("/quality-feedback", response_model=ResumeQualityResponse)
def get_resume_quality_feedback(
    job_id: Optional[str] = None,
    candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """
    AI Resume Intelligence:
    Evaluates resume completeness, formatting, section breakdown, and provides actionable suggestions.
    If job_id is provided, includes target skill alignment and tailored resume improvement tips.
    """
    user = candidate.user
    cand_skills = [s.skill_name.title() for s in candidate.skills]
    has_contact = bool(candidate.phone and user.email)
    has_title = bool(candidate.title)
    has_bio = bool(candidate.bio and len(candidate.bio.strip()) >= 20)
    has_edu = bool(candidate.education and len(candidate.education) > 0)
    has_exp = bool(candidate.experience and len(candidate.experience) > 0)
    has_skills = bool(len(cand_skills) >= 3)

    section_breakdown = {
        "Contact Information": has_contact,
        "Professional Title": has_title,
        "Executive Summary": has_bio,
        "Education History": has_edu,
        "Work Experience": has_exp,
        "Technical Skills": has_skills
    }

    completeness = (
        (15.0 if has_contact else 0.0) +
        (10.0 if has_title else 0.0) +
        (15.0 if has_bio else 0.0) +
        (20.0 if has_edu else 0.0) +
        (20.0 if has_exp else 0.0) +
        (20.0 if has_skills else (len(cand_skills) * 5.0))
    )
    completeness = min(round(completeness, 1), 100.0)

    # Formatting and readability evaluation
    formatting = 95.0
    if not has_bio: formatting -= 5.0
    if not has_edu: formatting -= 5.0
    if len(cand_skills) < 5: formatting -= 5.0
    formatting = max(round(formatting, 1), 70.0)

    # Missing fields list
    missing = []
    if not candidate.phone: missing.append("Contact Phone")
    if not has_title: missing.append("Professional Title")
    if not has_bio: missing.append("Executive Summary")
    if not has_edu: missing.append("Education Credentials")
    if not has_exp: missing.append("Work History")
    if len(cand_skills) < 3: missing.append("Verified Competencies")

    # Generate tailored, actionable suggestions
    suggestions = []
    if not candidate.phone:
        suggestions.append("Add your phone number so corporate recruiters can schedule phone screens directly.")
    if not has_bio:
        suggestions.append("Craft a concise 2-3 sentence executive summary highlighting your engineering focus and years of hands-on impact.")
    if len(cand_skills) < 8:
        suggestions.append("Expand your skill inventory with 3-5 additional relevant technologies (databases, cloud platforms, testing suites).")
    if candidate.experience:
        suggestions.append("Incorporate quantifiable impact metrics in experience bullets (e.g., 'optimized latency by 35%', 'reduced build time to 8s').")
    else:
        suggestions.append("Add academic capstone projects, open-source repositories, or internships under experience to demonstrate practical aptitude.")

    # Target job alignment if requested
    job_alignment = None
    if job_id:
        target_job = db.query(Job).filter(Job.id == job_id).first()
        if target_job:
            req_skills = [js.skill.skill_name for js in target_job.job_skills if js.skill]
            match_res = calculate_skill_match([s.lower() for s in cand_skills], req_skills)
            job_alignment = {
                "job_title": target_job.title,
                "match_score": match_res["match_score"],
                "matched_skills": [s.title() for s in match_res["matched_skills"]],
                "missing_skills": [s.title() for s in match_res["missing_skills"]]
            }
            if match_res["missing_skills"]:
                missing_str = ", ".join([s.title() for s in match_res["missing_skills"][:3]])
                suggestions.insert(0, f"Tailor your profile for '{target_job.title}' by demonstrating experience or personal projects involving: {missing_str}.")

    # Confidence score from latest resume or derived from completeness
    latest_resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.upload_date.desc()).first()
    conf_score = latest_resume.confidence_score if latest_resume and latest_resume.confidence_score else completeness

    return ResumeQualityResponse(
        completeness_score=completeness,
        formatting_score=formatting,
        confidence_score=conf_score,
        missing_fields=missing,
        section_breakdown=section_breakdown,
        suggestions=suggestions,
        job_alignment=job_alignment
    )
