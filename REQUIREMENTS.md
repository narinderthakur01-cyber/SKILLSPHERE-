# SkillSphere — Comprehensive System Requirements Document (SRS) [REVISED]

## 1. Executive Summary & Problem Statement

**SkillSphere** is an end-to-end recruitment and career platform bridging Job Seekers, Recruiters, and Platform Administrators. Built as an enterprise-grade MVP, SkillSphere combines modern web technologies (React + Vite, FastAPI, PostgreSQL) with intelligent document processing (PyMuPDF, Tesseract/OCR engine) to streamline hiring workflows.

The system automates candidate onboarding through resume OCR parsing, enables granular skill-based matching against real job openings, facilitates transparent application lifecycles, provides recruiters with candidate pipeline management tools, and offers platform administrators oversight and governance.

---

## 2. Stakeholders & User Roles

| Role | Description | Access Scope |
| :--- | :--- | :--- |
| **Job Seeker (Candidate)** | Individual looking for career opportunities. | Can create/edit candidate profile, upload resumes (PDF/Images), review OCR extraction, search/filter jobs, view match analysis, apply to jobs, track/withdraw applications. |
| **Recruiter** | Talent acquisition specialist or hiring manager representing an organization. | Can manage company profile, create/edit/close job postings, view applicants for own jobs, filter candidate pool by skill/experience, inspect candidate resumes, and update application statuses. |
| **Admin** | System operator and compliance administrator. | Can oversee all registered users and recruiters, moderate/disable inappropriate job postings, and review platform-level metrics and analytics. |

---

## 3. Functional Requirements

### 3.1 Authentication & Authorization
- **FR-AUTH-01:** Users can register as either `JOB_SEEKER` or `RECRUITER`.
- **FR-AUTH-02:** Email addresses must be unique and validated for correct format.
- **FR-AUTH-03:** Passwords must be securely hashed using Bcrypt or Argon2.
- **FR-AUTH-04:** Authentication issues stateless JWT access tokens with standard claims (user ID, email, role, expiration).
- **FR-AUTH-05:** Protected routes enforce Role-Based Access Control (RBAC). Unauthorized attempts return HTTP 401 or 403.
- **FR-AUTH-06:** Client-side logout clears tokens from local storage; backend catches expired/invalid tokens and returns HTTP 401 with standard detail.
- **FR-AUTH-07:** Admin account is seeded securely using environment variables (`ADMIN_EMAIL`, `ADMIN_PASSWORD`), avoiding hardcoded production credentials.

### 3.2 Candidate Profile & Incremental OCR Workflow
- **FR-OCR-01 (File Validation):** Accept PDF, JPG, JPEG, and PNG files up to 10 MB. Validate both file extension and MIME type.
- **FR-OCR-02 (Digital PDF Extraction):** Extract direct text from digital PDFs using PyMuPDF (`fitz`) for sub-second, lossless text extraction.
- **FR-OCR-03 (Scanned PDF & Image OCR):** For scanned documents or image formats, render high-contrast images, apply preprocessing (grayscale, contrast normalization), and run OCR.
- **FR-OCR-04 (Contact Details Parsing):** Use robust regex to extract candidate email address and normalized phone numbers.
- **FR-OCR-05 (Skills Extraction):** Match candidate text against a comprehensive taxonomy dictionary of 200+ industry skills.
- **FR-OCR-06 (Candidate Review & Verification):** Present extracted fields in an editable review UI so the candidate can inspect, correct, and add missing data before committing to their profile.
- **FR-OCR-07 (Error Handling):** Unreadable, corrupted, or unsupported files must return descriptive HTTP 400/422 responses with clear user feedback without crashing the server.

### 3.3 Resume-to-Job Matching Engine
- **FR-MATCH-01:** Compare candidate profile skills against required skills of an active job opening.
- **FR-MATCH-02:** Calculate deterministic match percentage:
  $$\text{Match Score} = \left(\frac{|\text{Candidate Skills} \cap \text{Job Skills}|}{|\text{Job Skills}|}\right) \times 100$$
- **FR-MATCH-03 (Edge Case Handling):** When a job has no required skills specified ($|S_{job}| = 0$), the service returns:
  `{"match_score": null, "matched_skills": [], "missing_skills": [], "message": "This job does not specify any required skills. Match score cannot be calculated."}`.
- **FR-MATCH-04:** Return separate lists of matched skills and missing skills.
- **FR-MATCH-05:** Provide actionable, explainable gap recommendations for missing skills.

### 3.4 Job Postings & Search
- **FR-JOB-01:** Recruiters can create, edit, publish, and close job postings.
- **FR-JOB-02:** Job postings include: Title, Company, Description, Location, Job Type (`FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERNSHIP`, `REMOTE`), Experience Range, Salary Range, and Required Skills tags.
- **FR-JOB-03:** Job seekers can search jobs by keywords and filter by location, experience, job type, and required skills.
- **FR-JOB-04:** Provide sorting and server-side pagination for job results.

### 3.5 Applications & Strict Duplicate Prevention
- **FR-APP-01:** Candidates can submit an application attaching an uploaded resume and an optional cover note.
- **FR-APP-02 (Duplicate Prevention):** Enforce strict duplicate application prevention using a database Unique Constraint on `(job_id, candidate_id)` and wrap insertion with transaction error handling to catch `IntegrityError` and return HTTP 400.
- **FR-APP-03 (Status Workflow):** Supported statuses: `Applied`, `Under Review`, `Shortlisted`, `Interview`, `Selected`, `Rejected`, and `Withdrawn`.
- **FR-APP-04 (Ownership & Isolation):**
  - Candidates can only view and withdraw their own applications.
  - Recruiters can only view and modify status for applicants to jobs they own.
- **FR-APP-05 (Withdrawal):** Candidates can withdraw applications while in `Applied` or `Under Review` status.

### 3.6 Administration & Platform Governance
- **FR-ADM-01:** Admins can view platform metrics: total users, candidate/recruiter breakdown, active jobs, and application counts.
- **FR-ADM-02:** Admins can toggle user active/disabled status.
- **FR-ADM-03:** Admins can moderate, flag, or remove inappropriate job postings.

---

## 4. Scope Breakdown: Mandatory MVP vs Optional Features

### 4.1 Mandatory MVP Requirements (Immediate Focus)
- [x] Multi-role JWT Auth (Job Seeker, Recruiter, Admin) with Bcrypt hashing and secure admin seeding.
- [x] Strict Role-Based Authorization and resource ownership enforcement (recruiters see only their jobs/applicants; candidates see only their resumes/applications).
- [x] Tabbed Dashboard UI (reducing frontend routing complexity to 3 consolidated dashboards).
- [x] Incremental Resume Processing:
  1. Digital PDF extraction (PyMuPDF)
  2. Scanned image/PDF OCR fallback
  3. Email and phone regex parsing
  4. Skill taxonomy extraction
  5. Editable candidate review form
- [x] Explainable Skill Matching Engine with null-score edge case handling for jobs without required skills.
- [x] Job Search with multi-criteria filtering, sorting, and pagination.
- [x] Application submission with database-enforced duplicate prevention.
- [x] Application tracking and status progression (`Applied` to `Selected`/`Rejected`) and candidate withdrawal.
- [x] Recruiter pipeline management and Admin platform metrics.
- [x] Automated test suite verifying Auth, RBAC, OCR, Matching, and Applications.

### 4.2 Optional Bonus Features (Post-MVP)
- [ ] Email notifications on application status change.
- [ ] Real-time notifications via WebSockets.
- [ ] Downloadable PDF analysis report.
- [ ] Export recruiter applicant data to Excel.
- [ ] Multi-language OCR support.
