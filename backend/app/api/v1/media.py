import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_recruiter
from app.models.models import User, RoleEnum, Recruiter, Candidate, MediaAsset
from app.schemas.schemas import (
    MediaAssetResponse, MediaUploadSignatureRequest,
    MediaUploadSignatureResponse, MediaSignedPlaybackResponse
)
from app.services.cloudinary_service import CloudinaryService

router = APIRouter(prefix="/media", tags=["Media Management"])

@router.post("/signature", response_model=MediaUploadSignatureResponse)
def get_upload_signature(
    req: MediaUploadSignatureRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate signed upload parameters for Cloudinary direct client uploads.
    API Secret is never exposed to the browser.
    """
    # Authorization checks based on requested folder
    if req.folder_key in ["interviews", "assessments"] and current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only recruiters can upload to interview and assessment folders."
        )

    sig_data = CloudinaryService.generate_upload_signature(
        folder_key=req.folder_key,
        resource_type=req.resource_type,
        tags=req.tags
    )
    return sig_data

def _sanitize_id(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip()
    if s.lower() in ("undefined", "null", "none", ""):
        return None
    return s

@router.post("/upload", response_model=MediaAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_media_file(
    request: Request,
    file: UploadFile = File(...),
    folder_key: str = Form("interviews"),
    candidate_id: Optional[str] = Form(None),
    recruiter_id: Optional[str] = Form(None),
    job_id: Optional[str] = Form(None),
    interview_id: Optional[str] = Form(None),
    access_classification: str = Form("CONFIDENTIAL"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct upload endpoint: receives file via multipart form-data, securely
    persists or pushes to Cloudinary, and registers MediaAsset metadata in PostgreSQL.
    Enforces strict candidate UUID isolation and prevents 'undefined' or spoofed identities.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    effective_candidate_id = _sanitize_id(candidate_id)
    effective_recruiter_id = _sanitize_id(recruiter_id)
    sanitized_job_id = _sanitize_id(job_id)
    sanitized_interview_id = _sanitize_id(interview_id)

    if current_user.role == RoleEnum.JOB_SEEKER:
        # Strictly resolve authenticated candidate database record
        cand = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if not cand:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Candidate profile not found for authenticated user."
            )
        effective_candidate_id = cand.id
        effective_recruiter_id = None
    elif current_user.role == RoleEnum.RECRUITER:
        rec = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Recruiter profile not found for authenticated user."
            )
        effective_recruiter_id = rec.id
        if effective_candidate_id:
            # Validate candidate exists
            target_cand = db.query(Candidate).filter(Candidate.id == effective_candidate_id).first()
            if not target_cand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specified candidate does not exist."
                )
    elif current_user.role == RoleEnum.ADMIN:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: User role not authorized for media upload."
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    asset = CloudinaryService.upload_media_asset(
        db=db,
        file_bytes=file_bytes,
        filename=file.filename or f"upload_{uuid.uuid4().hex[:8]}",
        folder_key=folder_key,
        candidate_id=effective_candidate_id,
        recruiter_id=effective_recruiter_id,
        job_id=sanitized_job_id,
        interview_id=sanitized_interview_id,
        access_classification=access_classification,
        actor_user_id=current_user.id,
        client_ip=client_ip,
        user_agent=user_agent
    )

    return asset

@router.get("", response_model=List[MediaAssetResponse])
def list_media_assets(
    folder: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    interview_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List media assets with role-based scoping and filtering.
    Recruiters see assets related to their jobs, interviews, assessments, and candidate responses.
    Candidates see only their own permitted non-confidential media assets.
    Admins see all assets.
    """
    query = db.query(MediaAsset).filter(MediaAsset.is_deleted == False)

    if current_user.role == RoleEnum.JOB_SEEKER:
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if not candidate:
            return []
        query = query.filter(MediaAsset.candidate_id == candidate.id)
        # Exclude recruiter internal interview recordings and internal confidential files
        query = query.filter(
            ~MediaAsset.folder.ilike("%interviews%"),
            MediaAsset.access_classification != "CONFIDENTIAL"
        )
    elif current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter:
            return []
        query = query.filter(
            or_(
                MediaAsset.uploader_user_id == current_user.id,
                MediaAsset.job.has(recruiter_id=recruiter.id),
                MediaAsset.interview.has(recruiter_id=recruiter.id),
                MediaAsset.video_assessment.has(recruiter_id=recruiter.id),
                MediaAsset.assessment.has(recruiter_id=recruiter.id)
            )
        )
    elif current_user.role == RoleEnum.ADMIN:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only recruiters, candidates, and administrators can access the Media Library."
        )

    sanitized_folder = _sanitize_id(folder)
    sanitized_cand_id = _sanitize_id(candidate_id)
    sanitized_job_id = _sanitize_id(job_id)
    sanitized_interview_id = _sanitize_id(interview_id)

    if sanitized_folder:
        query = query.filter(MediaAsset.folder.ilike(f"%{sanitized_folder}%"))
    if sanitized_cand_id and current_user.role != RoleEnum.JOB_SEEKER:
        query = query.filter(MediaAsset.candidate_id == sanitized_cand_id)
    if sanitized_job_id:
        query = query.filter(MediaAsset.job_id == sanitized_job_id)
    if sanitized_interview_id:
        query = query.filter(MediaAsset.interview_id == sanitized_interview_id)
    if resource_type:
        query = query.filter(MediaAsset.resource_type == resource_type)
    if search:
        query = query.filter(
            or_(
                MediaAsset.original_filename.ilike(f"%{search}%"),
                MediaAsset.public_id.ilike(f"%{search}%"),
                MediaAsset.folder.ilike(f"%{search}%")
            )
        )

    assets = query.order_by(MediaAsset.created_at.desc()).all()

    # Generate fresh playback URLs preserving resource type and extension
    for asset in assets:
        if asset.public_id:
            asset.playback_url = CloudinaryService.generate_signed_playback_url(
                asset.public_id,
                resource_type=asset.resource_type or "video",
                file_format=asset.file_format,
                secure_url=asset.secure_url
            )
            if not asset.thumbnail_url and asset.resource_type == "video":
                asset.thumbnail_url = CloudinaryService.generate_thumbnail_url(
                    asset.public_id,
                    resource_type="video",
                    file_format="jpg"
                )

    return assets

@router.get("/{asset_id}/playback", response_model=MediaSignedPlaybackResponse)
def get_signed_playback_url(
    asset_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an authenticated, time-limited signed URL for secure playback of confidential media.
    Enforces authorization check and logs media access audit record.
    """
    asset = db.query(MediaAsset).filter(
        MediaAsset.id == asset_id,
        MediaAsset.is_deleted == False
    ).first()

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")

    # Authorization verification
    authorized = False
    if current_user.role == RoleEnum.ADMIN:
        authorized = True
    elif current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if recruiter:
            if (
                asset.uploader_user_id == current_user.id
                or (asset.job and asset.job.recruiter_id == recruiter.id)
                or (asset.interview and asset.interview.recruiter_id == recruiter.id)
                or (asset.video_assessment and asset.video_assessment.recruiter_id == recruiter.id)
                or (asset.assessment and asset.assessment.recruiter_id == recruiter.id)
            ):
                authorized = True
    elif current_user.role == RoleEnum.JOB_SEEKER:
        candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
        if candidate and asset.candidate_id == candidate.id:
            # Candidates can view their own resume or their own video assessment responses, but NOT recruiter internal interview recordings
            if not (asset.folder and "interviews" in asset.folder) and asset.access_classification != "CONFIDENTIAL":
                authorized = True

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view or play this media asset."
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    CloudinaryService.log_media_access(
        db=db,
        media_asset_id=asset.id,
        actor_user_id=current_user.id,
        action="PLAYBACK_REQUESTED",
        client_ip=client_ip,
        user_agent=user_agent
    )

    signed_url = CloudinaryService.generate_signed_playback_url(
        asset.public_id,
        resource_type=asset.resource_type or "video",
        file_format=asset.file_format,
        secure_url=asset.secure_url
    )

    thumbnail_url = asset.thumbnail_url or (
        CloudinaryService.generate_thumbnail_url(asset.public_id, resource_type=asset.resource_type or "video")
        if asset.resource_type == "video" else asset.secure_url
    )

    return MediaSignedPlaybackResponse(
        asset_id=asset.id,
        public_id=asset.public_id,
        playback_url=signed_url,
        thumbnail_url=thumbnail_url,
        expires_in_seconds=3600,
        access_classification=asset.access_classification or "CONFIDENTIAL",
        resource_type=asset.resource_type or "video",
        file_format=asset.file_format,
        secure_url=asset.secure_url,
        upload_status=asset.upload_status or "COMPLETED"
    )

@router.delete("/{asset_id}", status_code=status.HTTP_200_OK)
def delete_media_asset(
    asset_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authorized deletion of media asset from Cloudinary and soft deletion in database.
    Only authorized recruiter or administrator can delete assets.
    """
    if current_user.role not in [RoleEnum.RECRUITER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only recruiters and administrators can delete media assets."
        )

    asset = db.query(MediaAsset).filter(
        MediaAsset.id == asset_id,
        MediaAsset.is_deleted == False
    ).first()

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")

    if current_user.role == RoleEnum.RECRUITER:
        recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
        if not recruiter or not (
            asset.uploader_user_id == current_user.id
            or (asset.job and asset.job.recruiter_id == recruiter.id)
            or (asset.interview and asset.interview.recruiter_id == recruiter.id)
            or (asset.video_assessment and asset.video_assessment.recruiter_id == recruiter.id)
            or (asset.assessment and asset.assessment.recruiter_id == recruiter.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only delete media assets associated with your own postings."
            )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    success = CloudinaryService.delete_asset(
        db=db,
        media_asset_id=asset.id,
        actor_user_id=current_user.id,
        client_ip=client_ip,
        user_agent=user_agent
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media asset."
        )

    return {"success": True, "message": "Media asset deleted successfully."}
