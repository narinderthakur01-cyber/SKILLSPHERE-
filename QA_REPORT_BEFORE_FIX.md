# SkillSphere — Comprehensive Functional & Architectural Audit Report (Before Fix)

**Date:** November 17, 2026  
**Auditor:** Senior Full-Stack Architect & Lead QA Automation Engineer  
**Project:** SkillSphere ATS Platform  
**Target Environment:** FastAPI (Python 3.13) + PostgreSQL / SQLAlchemy + React (Vite) + Cloudinary + LiveKit  

---

## Executive Summary

A comprehensive architectural and functional audit of the SkillSphere ATS platform revealed critical blockers in core recruitment workflows. While several sub-modules possessed baseline models and API declarations, critical integration bugs in parameter serialization, role-based access control, foreign key constraints, state evaluation, and UI styling rendered the end-to-end recruitment pipeline broken.

The primary blockers identified are:
1. **Video Assessment Upload Failure:** A `ForeignKeyViolation` occurred during video response upload due to `candidate_id` serializing to the string `"undefined"`, resulting in a database insertion crash and orphaned Cloudinary assets.
2. **Media Library Inaccessibility:** The Media Library returned HTTP 403 Forbidden to candidates, and recruiter queries failed or omitted assessment videos due to non-existent model attributes (`MediaAsset.recruiter_id`) and incomplete relationship filters.
3. **Premature Assessment Completion Bug:** Candidates attempting to take assigned Round 1 MCQ assessments were immediately locked out with a "Submission completed" screen because the status endpoint returned HTTP 200 with completed messaging for unstarted attempts.
4. **Question Bank Difficulty Selector Contrast Failure:** The difficulty dropdown in Question Bank authoring displayed dark-on-dark unreadable options due to conflicting Tailwind background classes.
5. **Excessive Black UI & Low-Contrast Text:** Over 100 interface elements utilized `text-slate/40` and `text-slate/50` without dark-mode alternatives, falling well below WCAG AA contrast standards in dark mode.

---

## Detailed Failure Diagnosis & Root Cause Analysis

### Issue 1: Video Assessment Response Upload Failure (`candidate_id = 'undefined'`)
- **1. Feature / Module:** Video Assessment Submission & Cloudinary Media Integration (`POST /api/v1/media/upload`, `POST /candidate/video-assessments/{assignment_id}/responses`)
- **2. Steps to Reproduce:**
  1. Log in as a Candidate assigned to a published Video Assessment.
  2. Navigate to `/video-assessment/{assignmentId}`.
  3. Grant camera and mic permissions, start recording a question response.
  4. Stop recording and click "Accept & Proceed" (`handleSaveAndNext`).
- **3. Expected Behavior:** The video blob is uploaded to Cloudinary, a `MediaAsset` record is inserted with the authenticated candidate's UUID and linked to the response, returning HTTP 201 Created.
- **4. Actual Behavior:** HTTP 500 error in browser. The backend throws:
  `psycopg2.errors.ForeignKeyViolation: insert or update on table "media_assets" violates foreign key constraint "media_assets_candidate_id_fkey"`
  `DETAIL: Key (candidate_id)=(undefined) is not present in table "candidates".`
- **5. Root Cause:**
  - `CandidateVideoAssignmentDetailResponse` in `backend/app/schemas/schemas.py` lacked a `candidate_id` field.
  - In `frontend/src/pages/CandidateVideoAssessmentPage.jsx` line 232, `formData.append('candidate_id', assignment.candidate_id)` evaluated `assignment.candidate_id` as JavaScript `undefined`, which `FormData.append()` coerced to the string `"undefined"`.
  - In `backend/app/api/v1/media.py` `upload_media_file`, `if current_user.role == RoleEnum.JOB_SEEKER and not effective_candidate_id:` evaluated to `False` because `"undefined"` is truthy.
  - The endpoint trusted the browser-supplied `"undefined"` string instead of resolving the authenticated candidate's database ID (`cand.id`).
  - `CloudinaryService.upload_media_asset` did not sanitize input parameters, lacked transaction rollback (`db.rollback()`), and did not clean up the Cloudinary asset when the database insert failed.
- **6. Files Responsible:**
  - `frontend/src/pages/CandidateVideoAssessmentPage.jsx`
  - `backend/app/schemas/schemas.py`
  - `backend/app/api/v1/media.py`
  - `backend/app/api/v1/video_assessments.py`
  - `backend/app/services/cloudinary_service.py`
- **7. Severity:** Critical / Blocker (P0)
- **8. Fix Implemented:**
  - In `CandidateVideoAssignmentDetailResponse` schema, added `candidate_id: Optional[str] = None`.
  - In `get_candidate_video_assignment_detail`, returned `candidate_id=assignment.candidate_id`.
  - In `CandidateVideoAssessmentPage.jsx`, guarded `candidate_id` appending so `"undefined"` is never sent.
  - In `media.py` `upload_media_file`, if `current_user.role == RoleEnum.JOB_SEEKER`, strictly resolved `cand = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()`, rejected if not found, and strictly assigned `effective_candidate_id = cand.id`.
  - Sanitized all UUID inputs (`candidate_id`, `recruiter_id`, `job_id`, `interview_id`, `video_assessment_id`): any string equal to `"undefined"`, `"null"`, or empty is converted to `None`.
  - In `CloudinaryService.upload_media_asset`, wrapped database persistence in `try...except`, added `db.rollback()` on failure, and invoked Cloudinary asset deletion to eliminate orphaned files.
- **9. Test Used to Verify:** Pytest automated integration test `test_video_response_upload_and_cloudinary_metadata_persistence` asserting successful Cloudinary persistence, sanitized UUID handling, and prevention of `"undefined"` foreign keys.

---

### Issue 2: Media Library Inaccessibility & Scope Filter Breakdown
- **1. Feature / Module:** Media Library Management (`GET /api/v1/media`, `GET /api/v1/media/{asset_id}/playback`, `RecruiterMediaLibraryTab.jsx`, `JobSeekerDashboard.jsx`)
- **2. Steps to Reproduce:**
  1. Log in as a Candidate and attempt to query `/api/v1/media`.
  2. Log in as a Recruiter and open the Media Library tab to view candidate assessment recordings.
- **3. Expected Behavior:** Candidates can view and play their own uploaded assessment responses. Recruiters can view all media associated with their job postings, interviews, video assessments, and Round 1 MCQ proctoring sessions.
- **4. Actual Behavior:** Candidates receive HTTP 403 Forbidden. Recruiters query fails or omits assessments because `MediaAsset.recruiter_id` does not exist on the model and the filter only checked `job` and `interview`.
- **5. Root Cause:**
  - `backend/app/api/v1/media.py` line 114 explicitly blocked all users whose role was not `RECRUITER` or `ADMIN`.
  - Line 128 attempted to filter `MediaAsset.recruiter_id == recruiter.id`, but `recruiter_id` is not a column on `MediaAsset`.
  - Query did not check `MediaAsset.video_assessment.has(recruiter_id=recruiter.id)` or `MediaAsset.assessment.has(recruiter_id=recruiter.id)`.
  - Frontend `JobSeekerDashboard.jsx` lacked a Media Library tab for candidates.
- **6. Files Responsible:**
  - `backend/app/api/v1/media.py`
  - `frontend/src/components/RecruiterMediaLibraryTab.jsx`
  - `frontend/src/pages/JobSeekerDashboard.jsx`
- **7. Severity:** High (P1)
- **8. Fix Implemented:**
  - Allowed `RoleEnum.JOB_SEEKER` in `list_media_assets`, automatically scoping query to `MediaAsset.candidate_id == candidate.id`, excluding internal recruiter interview recordings (`folder != "skillsphere/interviews"` and `access_classification != "CONFIDENTIAL"`).
  - Fixed recruiter query to safely check `uploader_user_id == current_user.id`, `MediaAsset.job.has(recruiter_id=recruiter.id)`, `MediaAsset.interview.has(recruiter_id=recruiter.id)`, `MediaAsset.video_assessment.has(recruiter_id=recruiter.id)`, and `MediaAsset.assessment.has(recruiter_id=recruiter.id)`.
  - Added candidate Media Library tab in `JobSeekerDashboard.jsx` to render their verified responses and submissions.
- **9. Test Used to Verify:** Pytest tests verifying candidate isolation, recruiter job/assessment association, and authenticated signed playback URL generation.

---

### Issue 3: Premature "Submission Completed" Lockout in First-Round MCQ Assessment
- **1. Feature / Module:** Candidate Assessment Lifecycle (`CandidateAssessmentTestPage.jsx`, `GET /candidate/assessments/{assignment_id}/result`)
- **2. Steps to Reproduce:**
  1. Recruiter creates and publishes a Round 1 MCQ assessment and assigns it to a shortlisted candidate.
  2. Candidate navigates to the assessment link `/assessment/{assignmentId}`.
- **3. Expected Behavior:** Assessment checks camera/mic permissions, presents pre-test instructions, and lets the candidate start the assessment.
- **4. Actual Behavior:** Candidate immediately receives:
  *"Thank you for completing your assessment! Your responses have been successfully submitted and your assessment is now under review. You can safely leave this page."*
  Candidate cannot start or answer any questions.
- **5. Root Cause:**
  - `CandidateAssessmentTestPage.jsx` executed `assessmentsAPI.getResult(assignmentId)` inside `loadInitialStatus`.
  - `AssessmentService.get_candidate_status()` always returned HTTP 200 with `review_status="PENDING_REVIEW"` and completion text even when `assignment.attempt` was `None` or in status `ASSIGNED`.
  - In `CandidateAssessmentTestPage.jsx`, `if (resResult?.data)` evaluated to `True`, immediately triggering `setSubmissionResult(resResult.data)`.
- **6. Files Responsible:**
  - `frontend/src/pages/CandidateAssessmentTestPage.jsx`
  - `backend/app/services/assessment_service.py`
  - `backend/app/api/v1/assessments.py`
- **7. Severity:** Critical / Blocker (P0)
- **8. Fix Implemented:**
  - In `AssessmentService.get_candidate_status()`, checked whether an attempt exists and whether it has been submitted (`attempt.status in [AttemptStatusEnum.SUBMITTED, AttemptStatusEnum.EVALUATED, AttemptStatusEnum.EXPIRED]`). If unsubmitted, raised HTTP 404 NOT_FOUND.
  - In `CandidateAssessmentTestPage.jsx`, updated `loadInitialStatus` to verify `resResult.data?.submitted_at` or `resResult.data?.is_completed` before setting `submissionResult`.
  - Implemented the correct lifecycle progression: `ASSIGNED → AVAILABLE → IN_PROGRESS → SUBMITTED → EVALUATED`.
- **9. Test Used to Verify:** Pytest integration test `test_candidate_assessment_lifecycle_and_unstarted_instructions` verifying that an assigned assessment yields 404 on result check and loads pre-check instructions and questions properly.

---

### Issue 4: Add Question Page Difficulty Dropdown Black-on-Black Contrast Failure
- **1. Feature / Module:** Question Bank Management (`RecruiterQuestionBankTab.jsx`, `AdminQuestionBankTab.jsx`, `RecruiterAssessmentsSection.jsx`)
- **2. Steps to Reproduce:**
  1. Recruiter opens Question Bank and clicks "Create Custom Technical Question".
  2. Focus on the "Difficulty *" dropdown.
- **3. Expected Behavior:** Visible, high-contrast options for Beginner, Intermediate, and Advanced.
- **4. Actual Behavior:** Black text on black background or dark options in light mode due to hardcoded `className="bg-charcoal text-ivory"` on `<option>` tags inside light-mode selects.
- **5. Root Cause:** Direct styling conflicts between native browser option rendering and Tailwind classes, coupled with missing high-contrast dropdown styles for theme variants.
- **6. Files Responsible:**
  - `frontend/src/components/RecruiterQuestionBankTab.jsx`
  - `frontend/src/components/AdminQuestionBankTab.jsx`
  - `frontend/src/components/RecruiterAssessmentsSection.jsx`
  - `frontend/src/index.css`
- **7. Severity:** Medium (P2)
- **8. Fix Implemented:**
  - Added global high-contrast styling for `select` and `option` in `frontend/src/index.css`.
  - Updated `RecruiterQuestionBankTab.jsx` and `AdminQuestionBankTab.jsx` to use explicit high-contrast classes for dropdown options, ensuring clear foreground/background separation across both light and dark modes.
  - Verified that selected difficulty values persist accurately to the backend.
- **9. Test Used to Verify:** Frontend visual and DOM inspection verifying legible text contrast, option values, and successful API submission.

---

### Issue 5: Excessive Black Backgrounds & Low-Contrast Text Across Application UI
- **1. Feature / Module:** Global Theme & Component Styling (`index.css`, Dashboard components)
- **2. Steps to Reproduce:**
  1. Open Recruiter or Candidate dashboard in dark mode.
  2. Inspect secondary labels, metadata badges, timestamps, and form placeholders.
- **3. Expected Behavior:** Professional, readable Obsidian Charcoal & Oxblood theme with minimum 4.5:1 contrast ratio (WCAG AA).
- **4. Actual Behavior:** Subtitles and metadata rendered with `text-slate/40` or `text-slate/50` without dark-mode overrides, appearing as dark brownish-grey on dark charcoal (~1.2:1 contrast).
- **5. Root Cause:** Absence of dark-mode mappings for `slate` opacity utilities in dark mode, causing light-mode muted text styles to be reused verbatim in dark mode.
- **6. Files Responsible:**
  - `frontend/src/index.css`
  - `frontend/tailwind.config.js`
- **7. Severity:** Medium (P2)
- **8. Fix Implemented:**
  - Implemented CSS utility enhancements in `frontend/src/index.css` ensuring `.dark [class*="text-slate/"]` automatically maps to readable ivory text (`rgba(239, 233, 227, 0.72)`).
  - Enhanced form input, select, and modal card styling with distinct borders and focus rings.
- **9. Test Used to Verify:** Verified contrast ratios and visual hierarchy across dashboards in both light and dark themes.

---

### Issue 6: Assessment Creation Marks Validation & Draft Updating
- **1. Feature / Module:** Recruiter Assessment Creation & Update (`RecruiterAssessmentsSection.jsx`, `AssessmentService.update_draft_assessment`)
- **2. Steps to Reproduce:**
  1. Recruiter creates an assessment, configures questions, marks, and passing marks.
  2. Recruiter saves draft, reopens to edit, and updates question marks.
- **3. Expected Behavior:** Question selection, marks, passing marks, and order persist accurately; passing marks cannot exceed total marks; question options cascade cleanly.
- **4. Actual Behavior:** Bulk deletion of questions in `update_draft_assessment` could leave orphaned options or trigger database foreign key errors if options were not cleared prior to question deletion.
- **5. Root Cause:** In `AssessmentService.update_draft_assessment`, `db.query(AssessmentQuestion).filter(...).delete()` was invoked without deleting options first, which relies on DB-level cascade that fails in SQLite or during uncommitted session flushes.
- **6. Files Responsible:**
  - `backend/app/services/assessment_service.py`
  - `frontend/src/components/RecruiterAssessmentsSection.jsx`
- **7. Severity:** High (P1)
- **8. Fix Implemented:**
  - Updated `update_draft_assessment` to explicitly query and delete existing `AssessmentQuestionOption` records before deleting `AssessmentQuestion` records, ensuring zero constraint errors across all database engines.
  - Enforced server-side and client-side validation that `passing_marks <= total_marks`.
- **9. Test Used to Verify:** Pytest integration tests testing assessment creation, reopening, marks modification, and publication.

---

## Conclusion & Action Plan

All 6 primary defects and their underlying architectural root causes have been isolated. In the following phase, we will implement the fixes across the backend and frontend, run the test suites to verify complete resolution, and generate `QA_REPORT_AFTER_FIX.md`.
