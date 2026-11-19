# SkillSphere Assistant — Technical Documentation

## 1. Overview and Architecture

SkillSphere Assistant is a deterministic, rule-based AI support assistant built natively into the SkillSphere recruitment and talent intelligence platform.

### Strict Compliance Guarantee:
- **No External LLM:** Zero reliance on OpenAI, Gemini, Claude, or third-party paid inference APIs.
- **No API Key Dependency:** Functions 100% locally and offline without external credentials.
- **Dual Presentation:** Available as a floating assistant widget on authenticated dashboard views and as a dedicated portal at `/assistant`.
- **Role-Aware:** Custom-tailored knowledge pools for Job Seekers (Candidates) and Recruiters.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER INPUT (Web Client)                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ POST /api/v1/chat/message + JWT
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 FASTAPI ROUTER (/api/v1/chat)                          │
│   1. Extracts authenticated user ID and role from JWT claims.          │
│   2. Validates session ownership (raises HTTP 403 on mismatch).        │
│   3. Restores active context topic from session history.               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 RULE-BASED INTENT MATCHER                              │
│   • Text Normalization: Lowercase, punctuation strip, whitespace trim  │
│   • Role-based FAQ Pool Gating (Job Seeker vs. Recruiter)              │
│   • Contextual Follow-Up Resolver ("tell me more", topic shortcuts)   │
│   • Scoring: Exact match (1.0), difflib SequenceMatcher (0.50),        │
│     Keyword & synonym token overlap (0.50), confidence boost (0.15)    │
│   • Threshold Evaluation: Score >= 0.50 -> Match; < 0.50 -> Fallback   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               HYBRID CONVERSATION STORAGE ADAPTER                      │
│   • SQLite: Local evaluation (backend/data/chatbot_history.db)         │
│   • PostgreSQL: Dedicated tables (chatbot_sessions, chatbot_messages)  │
│   • Strict user isolation: user_id foreign key validation              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Knowledge Base & FAQ Coverage

The knowledge base (`backend/app/chatbot/knowledge_base.json`) contains **30 verified FAQs** grounded exclusively in real SkillSphere capabilities:

### Candidate Topics (13 FAQs):
1. **Resume Upload:** File upload at `/dashboard?tab=resumes`, automated OCR text extraction.
2. **Supported Formats:** PDF and DOCX documents up to 10MB limit.
3. **Skill Extraction & Scoring:** Matching against 139 standardized skills, calculating match scores (0–100%).
4. **Job Search:** Filtering openings at `/dashboard?tab=jobs` by role type, remote status, and skills.
5. **Saved Jobs:** Bookmarking jobs to `/dashboard?tab=saved`.
6. **Applying:** One-click job application with latest uploaded resume.
7. **Application Stages:** APPLIED, SCREENING, UNDER_REVIEW, SHORTLISTED, INTERVIEW, SELECTED, REJECTED.
8. **Round 1 MCQ Assessment:** Randomized technical testing at `/dashboard?tab=assessments`.
9. **Automated Proctoring:** Webcam integrity, tab switch tracking, and infraction logging.
10. **Video Assessment:** Asynchronous recorded video answers uploaded to Cloudinary.
11. **LiveKit Interviews:** Virtual WebRTC meeting room at `/interview-room/:id`.
12. **Messaging:** Direct candidate-to-recruiter chat at `/dashboard?tab=messages`.
13. **Email Verification:** Account activation link via Brevo.

### Recruiter Topics (9 FAQs):
1. **Job Creation:** Publishing new requisitions at `/recruiter`.
2. **Job Management:** Active vs. closed status management at `/recruiter?tab=jobs`.
3. **Kanban Pipeline:** Interactive applicant board at `/recruiter?tab=pipeline`.
4. **Resume & Dossier Review:** Viewing OCR extracted skills, resume previews, match percentages.
5. **Question Bank Management:** 191 technical questions repository, inline question uploads.
6. **MCQ Review & Proctoring Logs:** Scorecards and anti-cheating infraction reports.
7. **Video Submission Review:** Grading video assessment recordings streamed via Cloudinary.
8. **Interview Scheduling:** Generating LiveKit meeting tokens and conducting live video calls.
9. **Direct Messaging:** Real-time messaging with applicants at `/recruiter?tab=messages`.

### General Platform Topics (8 FAQs):
1. SkillSphere Platform Overview.
2. User Account Roles (Job Seeker, Recruiter, Administrator).
3. Login & Authentication (`/auth`).
4. Password Reset flow (15-min token).
5. Technical Support & Browser Compatibility.
6. Welcome Greeting & Assistant capabilities.
7. Help & Topic Command Menu.
8. Dark/Light Theme Switcher.

---

## 3. API Endpoints and Payloads

All endpoints reside under the `/api/v1/chat` prefix.

### 1. Send Message
- **Endpoint:** `POST /api/v1/chat/message`
- **Headers:** `Authorization: Bearer <JWT>`
- **Request Body:**
```json
{
  "message": "How do I upload my resume?",
  "session_id": "optional-uuid4-session-id",
  "context_topic": null
}
```
- **Response Body (HTTP 200):**
```json
{
  "message": "To upload your resume in SkillSphere, go to your Job Seeker Dashboard and click the 'OCR & Intelligence' tab...",
  "matched_intent": "candidate_resume_upload",
  "confidence_score": 1.0,
  "session_id": "4a71e620-8025-4c07-9fa4-7e793963426d",
  "category": "candidate",
  "quick_replies": [
    { "label": "Supported Formats", "query": "What file formats are supported for resume upload?", "topic": "candidate_resume_upload" },
    { "label": "Skill Extraction", "query": "How does resume skill matching work?", "topic": "candidate_resume_intelligence" }
  ],
  "suggested_questions": [
    "What file formats are supported for resume upload?",
    "How does resume skill matching work?"
  ],
  "timestamp": "2026-11-19T12:00:00Z"
}
```

### 2. Retrieve FAQs
- **Endpoint:** `GET /api/v1/chat/faqs?role=JOB_SEEKER`
- **Response Body (HTTP 200):**
```json
{
  "total": 21,
  "role": "JOB_SEEKER",
  "faqs": [ ... ]
}
```

### 3. Retrieve Session History
- **Endpoint:** `GET /api/v1/chat/history/{session_id}`
- **Headers:** `Authorization: Bearer <JWT>`
- **Response Body (HTTP 200):**
```json
{
  "session_id": "4a71e620-8025-4c07-9fa4-7e793963426d",
  "user_id": "3b2e59e1-6789-4012-9012-345678901234",
  "title": "How do I upload my resume?",
  "last_topic": "candidate_resume_upload",
  "messages": [
    {
      "id": "msg-1",
      "session_id": "4a71e620-8025-4c07-9fa4-7e793963426d",
      "sender": "user",
      "content": "How do I upload my resume?",
      "intent": null,
      "confidence": null,
      "created_at": "2026-11-19T12:00:00Z"
    },
    {
      "id": "msg-2",
      "session_id": "4a71e620-8025-4c07-9fa4-7e793963426d",
      "sender": "assistant",
      "content": "To upload your resume...",
      "intent": "candidate_resume_upload",
      "confidence": 1.0,
      "created_at": "2026-11-19T12:00:01Z"
    }
  ],
  "total_messages": 2
}
```

### 4. Delete Session History
- **Endpoint:** `DELETE /api/v1/chat/history/{session_id}`
- **Headers:** `Authorization: Bearer <JWT>`
- **Response Body (HTTP 200):**
```json
{
  "session_id": "4a71e620-8025-4c07-9fa4-7e793963426d",
  "message": "Chat session and conversation history successfully deleted.",
  "deleted": true
}
```

### 5. Chatbot Health Diagnostics
- **Endpoint:** `GET /api/v1/chat/health`
- **Response Body (HTTP 200):**
```json
{
  "status": "healthy",
  "engine": "rule_based_deterministic",
  "total_faqs": 30,
  "candidate_faqs": 13,
  "recruiter_faqs": 9,
  "general_faqs": 8,
  "storage_backend": "sqlite",
  "storage_healthy": true,
  "version": "1.0.0"
}
```

---

## 4. Configuration and Storage Modes

Configuration is managed in `backend/app/core/config.py`:

```bash
# Storage Backend Selection: "sqlite" (default) or "postgres"
CHATBOT_STORAGE=sqlite

# Optional: Custom SQLite database path (defaults to backend/data/chatbot_history.db)
CHATBOT_SQLITE_PATH=
```

### Storage Backends:
1. **`sqlite` (Default):**
   - Ideal for local development, automated testing, and offline grading.
   - Requires zero external database services.
   - Automatically initializes `chatbot_sessions` and `chatbot_messages` with SQLite foreign key enforcement enabled (`PRAGMA foreign_keys = ON;`).
2. **`postgres`:**
   - Activated by setting `CHATBOT_STORAGE=postgres`.
   - Uses the existing `DATABASE_URL` to create dedicated, isolated tables (`chatbot_sessions`, `chatbot_messages`).
   - Uses `VARCHAR(36)` foreign keys matching SkillSphere's `users.id` type.
   - Does not touch or modify existing business tables.

---

## 5. Security & Ownership Enforcement

1. **Zero Client Trust:**
   - User ID and user role are **never** accepted from incoming request payloads.
   - Derived strictly from the cryptographically verified JWT bearer token via `Depends(get_current_user)`.
2. **Session Ownership Protection:**
   - On every request to read, append to, or delete a session, the backend checks:
     ```python
     if session["user_id"] != current_user.id:
         raise HTTPException(status_code=403, detail="Forbidden: You do not have permission...")
     ```
   - Cross-user history inspection or manipulation is impossible.
3. **Route Distraction Suppression:**
   - The floating `<ChatWidget />` automatically suppresses itself during high-focus activities:
     - MCQ Assessments (`/assessment/*`)
     - One-way Video Assessments (`/video-assessment/*`)
     - LiveKit Video Interviews (`/interview-room/*`)
     - Authentication and password reset screens.

---

## 6. How to Run Tests

### Running Chatbot Tests:
```bash
# Run isolated chatbot suite (30 FAQs, rule matcher, SQLite history store, route controllers)
python -m pytest backend/tests/test_chatbot_isolated_suite.py -v

# Run foundation knowledge base tests
python -m pytest backend/tests/test_chatbot_foundation.py -v
```

### Compiling Frontend:
```bash
npm --prefix frontend run build
```
Generates production chunks in `frontend/dist/` with physical route fallbacks for SPA direct-navigation.

---

## 7. Known Limitations

- **Rule-Based Specificity:** The assistant recognizes questions mapped to its 30 verified SkillSphere topics and phrasing variations. It does not synthesize open-ended creative text outside platform workflows (by design, adhering to assignment restrictions against external LLMs).
- **Ephemeral Storage on Render Free Tier:** When using SQLite on Render free/starter instances, local history resets upon container redeployments. For persistent multi-deploy history on Render, configure `CHATBOT_STORAGE=postgres`.
