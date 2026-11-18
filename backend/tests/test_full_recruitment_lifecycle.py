import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import (
    Job, Skill, JobSkill, Resume, Application, ApplicationStatusEnum,
    ProcessingStatusEnum, JobStatusEnum, Recruiter, Candidate, User, RoleEnum,
    Interview, MediaAsset
)
from app.core.security import get_password_hash, create_access_token
from app.services.cloudinary_service import CloudinaryService

def test_full_recruitment_lifecycle_end_to_end(
    client, db, candidate_user, candidate_token, recruiter_user, recruiter_token
):
    """
    Comprehensive End-to-End Recruitment Lifecycle Verification:
    Tests A through F covering job posting, applicant discovery & apply,
    recruiter review & isolation, status lifecycle & audit logging,
    interview & evaluations confidentiality, and media library integrity.
    """
    recruiter_profile = recruiter_user.recruiter_profile
    candidate_profile = candidate_user.candidate_profile

    # Create a secondary recruiter for cross-tenant isolation tests
    other_recruiter_user = User(
        name="Second Recruiter",
        email="second.recruiter@enterprise.com",
        password_hash=get_password_hash("Secret123!"),
        role=RoleEnum.RECRUITER,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc)
    )
    db.add(other_recruiter_user)
    db.commit()
    db.refresh(other_recruiter_user)

    other_recruiter_profile = Recruiter(
        user_id=other_recruiter_user.id,
        designation="Senior Talent Lead"
    )
    db.add(other_recruiter_profile)
    db.commit()
    db.refresh(other_recruiter_profile)
    other_recruiter_token = create_access_token(
        subject=other_recruiter_user.id,
        role=other_recruiter_user.role.value
    )

    # =========================================================================
    # TEST A: RECRUITER JOB POSTING & MANAGEMENT
    # =========================================================================
    # 1. Create a job posting as Recruiter 1
    create_job_payload = {
        "title": "Principal AI Systems Engineer",
        "description": "Architect and deploy high-performance distributed AI and LLM inference pipelines.",
        "location": "Bengaluru (Hybrid)",
        "experience_min": 5.0,
        "experience_max": 10.0,
        "job_type": "FULL_TIME",
        "salary_min": 3500000.0,
        "salary_max": 5500000.0,
        "status": "ACTIVE",
        "required_skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"]
    }
    job_resp = client.post(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=create_job_payload
    )
    assert job_resp.status_code == 201, f"Create job failed: {job_resp.text}"
    job_data = job_resp.json()
    job_id = job_data["id"]
    assert job_data["title"] == "Principal AI Systems Engineer"
    assert "Python" in job_data["required_skills"]
    assert job_data["status"] == "ACTIVE"

    # 2. Recruiter can update their own job
    update_resp = client.put(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"salary_max": 6000000.0, "location": "Bengaluru (Remote Friendly)"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["salary_max"] == 6000000.0
    assert update_resp.json()["location"] == "Bengaluru (Remote Friendly)"

    # 3. Foreign recruiter CANNOT update Job 1 (403 Forbidden)
    forbidden_update = client.put(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_recruiter_token}"},
        json={"title": "Hacked Title"}
    )
    assert forbidden_update.status_code == 403

    # =========================================================================
    # TEST B: CANDIDATE DISCOVERY, RESUME & APPLICATION WORKFLOW
    # =========================================================================
    # 1. Public job listing lists the active job
    public_jobs = client.get("/api/v1/jobs?keyword=Principal")
    assert public_jobs.status_code == 200
    items = public_jobs.json()["items"]
    assert any(j["id"] == job_id for j in items)

    # 2. Candidate has a valid resume
    resume = Resume(
        candidate_id=candidate_profile.id,
        file_name="candidate_cv.pdf",
        file_path="/dummy/resumes/candidate_cv.pdf",
        file_type="application/pdf",
        file_size=2048,
        processing_status=ProcessingStatusEnum.COMPLETED,
        extracted_text="Experienced in Python, FastAPI, React, and PostgreSQL.",
        parsed_data={"skills": ["Python", "FastAPI", "React", "PostgreSQL"]}
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 3. Candidate applies to the active job
    apply_payload = {
        "resume_id": resume.id,
        "cover_letter": "I have extensive experience building scalable cloud microservices."
    }
    apply_resp = client.post(
        f"/api/v1/jobs/{job_id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json=apply_payload
    )
    assert apply_resp.status_code == 201
    app_data = apply_resp.json()
    application_id = app_data["id"]
    assert app_data["status"] == "APPLIED"

    # 4. Duplicate application prevention: Applying again MUST fail with HTTP 400
    dup_apply = client.post(
        f"/api/v1/jobs/{job_id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json=apply_payload
    )
    assert dup_apply.status_code == 400
    assert "already submitted an active application" in dup_apply.json()["detail"]

    # 5. Candidate views their submitted applications
    my_apps = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert my_apps.status_code == 200
    my_apps_list = my_apps.json()
    assert any(a["id"] == application_id for a in my_apps_list)

    # =========================================================================
    # TEST C: RECRUITER APPLICANT REVIEW & CROSS-TENANT ISOLATION
    # =========================================================================
    # 1. Recruiter 1 views applicants for their job
    rec_apps = client.get(
        f"/api/v1/recruiter/applicants?job_id={job_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_apps.status_code == 200
    rec_apps_list = rec_apps.json()
    assert len(rec_apps_list) >= 1
    target_app = next(a for a in rec_apps_list if a["id"] == application_id)
    assert target_app["candidate"]["name"] == candidate_user.name
    assert target_app["resume"]["id"] == resume.id

    # 2. Foreign Recruiter 2 CANNOT see applicants for Recruiter 1's job
    other_rec_apps = client.get(
        f"/api/v1/recruiter/applicants?job_id={job_id}",
        headers={"Authorization": f"Bearer {other_recruiter_token}"}
    )
    assert other_rec_apps.status_code == 200
    assert len(other_rec_apps.json()) == 0, "Foreign recruiter must NOT see another recruiter's applicants"

    # 3. Foreign Recruiter 2 CANNOT update Recruiter 1's applicant status (403)
    unauth_status = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {other_recruiter_token}"},
        json={"status": "SHORTLISTED"}
    )
    assert unauth_status.status_code == 403

    # =========================================================================
    # TEST D: RECRUITMENT STATUS LIFECYCLE & CONFIDENTIALITY
    # =========================================================================
    # 1. Recruiter advances status: APPLIED -> UNDER_REVIEW
    res_under_review = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": "UNDER_REVIEW", "notes": "Initial resume screening looks promising."}
    )
    assert res_under_review.status_code == 200
    assert res_under_review.json()["status"] == "UNDER_REVIEW"

    # 2. Recruiter advances status: UNDER_REVIEW -> SHORTLISTED
    res_shortlist = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": "SHORTLISTED", "notes": "Candidate shortlisted for technical evaluation."}
    )
    assert res_shortlist.status_code == 200
    assert res_shortlist.json()["status"] == "SHORTLISTED"

    # 3. Recruiter saves private internal notes
    notes_resp = client.put(
        f"/api/v1/applications/{application_id}/notes",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"notes": "Confidential internal note: strong technical profile, salary expectation within budget."}
    )
    assert notes_resp.status_code == 200

    # 4. Confidentiality Check: Candidate views history; internal notes MUST BE SANITIZED (None)
    cand_hist = client.get(
        f"/api/v1/applications/{application_id}/history",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_hist.status_code == 200
    for h in cand_hist.json():
        assert h["notes"] is None, "Candidate must NOT see internal recruiter notes in history!"

    # =========================================================================
    # TEST E: INTERVIEW SCHEDULING, EVALUATION & CONFIDENTIALITY
    # =========================================================================
    # 1. Recruiter schedules an AI Live interview
    sched_payload = {
        "application_id": application_id,
        "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "duration_minutes": 45,
        "interview_type": "TECHNICAL",
        "interview_mode": "AI_LIVE",
        "instructions": "Prepare your webcam and microphone for live AI interview."
    }
    sched_resp = client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=sched_payload
    )
    assert sched_resp.status_code == 201
    interview_data = sched_resp.json()
    interview_id = interview_data["id"]
    assert interview_data["interview_mode"] == "AI_LIVE"

    # 2. AI Live Room Token generation
    token_resp = client.post(
        f"/api/v1/interviews/{interview_id}/room-token",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert token_resp.status_code == 200
    assert "token" in token_resp.json()

    # 3. Recruiter evaluates candidate
    eval_payload = {
        "application_id": application_id,
        "interview_id": interview_id,
        "technical_score": 4.8,
        "communication_score": 4.5,
        "experience_score": 4.7,
        "overall_recommendation": "STRONG_HIRE",
        "interview_feedback": "Demonstrated deep mastery of systems design and clean architecture.",
        "internal_notes": "Top candidate for the position. Proceed with offer."
    }
    eval_resp = client.post(
        "/api/v1/evaluations",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json=eval_payload
    )
    assert eval_resp.status_code == 201

    # 4. Candidate views application: evaluations list MUST be empty / omitted for candidate
    cand_app_view = client.get(
        "/api/v1/applications",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_app_view.status_code == 200
    cand_app = next(a for a in cand_app_view.json() if a["id"] == application_id)
    assert len(cand_app["evaluations"]) == 0, "Candidate must NOT receive evaluations in application response!"

    # 5. Recruiter views application: evaluations list contains the scorecard
    rec_app_view = client.get(
        f"/api/v1/recruiter/applicants?job_id={job_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_app_view.status_code == 200
    rec_app = next(a for a in rec_app_view.json() if a["id"] == application_id)
    assert len(rec_app["evaluations"]) >= 1
    assert rec_app["evaluations"][0]["overall_recommendation"] == "STRONG_HIRE"

    # 6. Recruiter finalizes status: SELECTED
    sel_resp = client.put(
        f"/api/v1/applications/{application_id}/status",
        headers={"Authorization": f"Bearer {recruiter_token}"},
        json={"status": "SELECTED", "notes": "Offer extended and accepted."}
    )
    assert sel_resp.status_code == 200
    assert sel_resp.json()["status"] == "SELECTED"

    # =========================================================================
    # TEST F: CLOUDINARY MEDIA LIBRARY FOLDER STANDARDIZATION & INTEGRATION
    # =========================================================================
    # 1. Verify standardized Cloudinary folder constants
    assert CloudinaryService.ALLOWED_FOLDERS["round1"] == "skillsphere/round1"
    assert CloudinaryService.ALLOWED_FOLDERS["video_assessments"] == "skillsphere/video-assessments"
    assert CloudinaryService.ALLOWED_FOLDERS["live_interviews"] == "skillsphere/live-interviews"
    assert CloudinaryService.ALLOWED_FOLDERS["ai_interviews"] == "skillsphere/ai-interviews"

    # 2. Register media asset for the interview
    media_asset = MediaAsset(
        public_id=f"skillsphere/ai-interviews/interview_{interview_id}",
        original_filename="ai_session_recording.webm",
        resource_type="video",
        file_format="webm",
        secure_url=f"https://res.cloudinary.com/demo/video/upload/skillsphere/ai-interviews/interview_{interview_id}.webm",
        playback_url=f"https://res.cloudinary.com/demo/video/upload/skillsphere/ai-interviews/interview_{interview_id}.webm",
        folder=CloudinaryService.ALLOWED_FOLDERS["ai_interviews"],
        interview_id=interview_id,
        candidate_id=candidate_profile.id,
        job_id=job_id,
        access_classification="CONFIDENTIAL",
        upload_status="COMPLETED"
    )
    db.add(media_asset)
    db.commit()
    db.refresh(media_asset)

    # 3. Candidate CANNOT download/view RECRUITER_CONFIDENTIAL media (403)
    cand_media_resp = client.get(
        f"/api/v1/media/{media_asset.id}/playback",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_media_resp.status_code == 403

    # 4. Recruiter CAN view/playback media
    rec_media_resp = client.get(
        f"/api/v1/media/{media_asset.id}/playback",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_media_resp.status_code == 200
    assert "playback_url" in rec_media_resp.json()

    # =========================================================================
    # TEST G: JOB CLOSING & DISCOVERY EXCLUSION
    # =========================================================================
    # 1. Recruiter closes job
    close_resp = client.delete(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert close_resp.status_code == 200

    # 2. Public job search no longer returns CLOSED job
    closed_search = client.get(f"/api/v1/jobs?keyword=Principal")
    assert closed_search.status_code == 200
    assert not any(j["id"] == job_id for j in closed_search.json()["items"])

    # 3. Applying to closed job fails with HTTP 400
    closed_apply = client.post(
        f"/api/v1/jobs/{job_id}/apply",
        headers={"Authorization": f"Bearer {candidate_token}"},
        json=apply_payload
    )
    assert closed_apply.status_code == 400
    assert "closed and no longer accepting applications" in closed_apply.json()["detail"]
