from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
from app.models.models import RoleEnum, JobTypeEnum, JobStatusEnum, ApplicationStatusEnum, ProcessingStatusEnum

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)

class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: RoleEnum = RoleEnum.JOB_SEEKER

class UserLogin(BaseModel):
    email: str = Field(..., max_length=255)
    password: str

class UserResponse(UserBase):
    id: str
    role: RoleEnum
    is_active: bool
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Skill Schemas ---
class SkillBase(BaseModel):
    skill_name: str
    category: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillResponse(SkillBase):
    id: str

    class Config:
        from_attributes = True

# --- Company Schemas ---
class CompanyBase(BaseModel):
    company_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    logo_url: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    logo_url: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Candidate Profile Schemas ---
class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    grade: Optional[str] = None

class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class CandidateProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    total_years_exp: Optional[float] = None
    skills: Optional[List[str]] = None

class CandidateProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    total_years_exp: float = 0.0
    skills: List[str] = []

    class Config:
        from_attributes = True

# --- Resume Schemas ---
class ResumeResponse(BaseModel):
    id: str
    candidate_id: str
    file_name: str
    file_type: str
    file_size: int
    processing_status: ProcessingStatusEnum
    error_message: Optional[str] = None
    upload_date: datetime
    parsed_data: Dict[str, Any] = {}
    confidence_score: Optional[float] = 100.0
    missing_fields: List[str] = []

    class Config:
        from_attributes = True

class ResumeAnalyzeRequest(BaseModel):
    resume_id: str
    job_id: str

class ResumeAnalyzeResponse(BaseModel):
    match_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    recommendations: Optional[str] = None
    message: Optional[str] = None

class ResumeQualityResponse(BaseModel):
    completeness_score: float
    formatting_score: float
    confidence_score: float
    missing_fields: List[str] = []
    section_breakdown: Dict[str, bool] = {}
    suggestions: List[str] = []
    job_alignment: Optional[Dict[str, Any]] = None

# --- Job Schemas ---
class JobCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10)
    department: Optional[str] = None
    location: str
    experience_min: Optional[float] = 0.0
    experience_max: Optional[float] = 0.0
    job_type: JobTypeEnum = JobTypeEnum.FULL_TIME
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: JobStatusEnum = JobStatusEnum.ACTIVE
    required_skills: List[str] = []

    @field_validator('experience_min', 'experience_max', mode='before')
    @classmethod
    def default_none_to_zero(cls, v):
        if v is None or v == '':
            return 0.0
        return float(v)

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    job_type: Optional[JobTypeEnum] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: Optional[JobStatusEnum] = None
    required_skills: Optional[List[str]] = None

class JobResponse(BaseModel):
    id: str
    title: str
    description: str
    department: Optional[str] = None
    location: str
    experience_min: float
    experience_max: float
    job_type: JobTypeEnum
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: JobStatusEnum
    created_at: datetime
    company: Optional[CompanyResponse] = None
    required_skills: List[str] = []

    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    pages: int

# --- Application Schemas & Pipeline ---
class ApplicationCreate(BaseModel):
    resume_id: str
    cover_letter: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatusEnum
    notes: Optional[str] = None

class ApplicationHistoryResponse(BaseModel):
    id: str
    from_status: Optional[str] = None
    to_status: str
    changed_by_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Interview Schemas ---
class InterviewCreate(BaseModel):
    application_id: str
    interview_type: str = "ONLINE"  # ONLINE, PHONE, IN_PERSON
    interview_mode: Optional[str] = "HUMAN"  # HUMAN, AI_LIVE, HYBRID, CONFIGURED
    scheduled_time: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 45
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    instructions: Optional[str] = None
    round_number: Optional[int] = 1
    round_title: Optional[str] = "Round 1 - Technical Screen"
    recording_enabled: Optional[bool] = False
    ai_config_json: Optional[Dict[str, Any]] = None
    questions: Optional[List[Dict[str, Any]]] = None
    voice: Optional[str] = "alloy"
    allow_recruiter_takeover: Optional[bool] = True
    difficulty: Optional[str] = "INTERMEDIATE"
    categories: Optional[List[str]] = None

    @model_validator(mode='before')
    @classmethod
    def resolve_scheduled_time(cls, data: Any):
        if isinstance(data, dict):
            sched_time = data.get("scheduled_time")
            sched_at = data.get("scheduled_at")
            if not sched_time and sched_at:
                data["scheduled_time"] = sched_at
            elif not sched_at and sched_time:
                data["scheduled_at"] = sched_time
            if not data.get("scheduled_time"):
                raise ValueError("Interview scheduled date/time is required.")
        return data

class InterviewUpdate(BaseModel):
    interview_type: Optional[str] = None
    interview_mode: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None  # SCHEDULED, COMPLETED, RESCHEDULED, CANCELLED
    round_number: Optional[int] = None
    round_title: Optional[str] = None
    recording_enabled: Optional[bool] = None
    ai_config_json: Optional[Dict[str, Any]] = None
    ai_takeover_status: Optional[str] = None
    current_question_index: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def resolve_scheduled_time(cls, data: Any):
        if isinstance(data, dict):
            sched_time = data.get("scheduled_time")
            sched_at = data.get("scheduled_at")
            if not sched_time and sched_at:
                data["scheduled_time"] = sched_at
            elif not sched_at and sched_time:
                data["scheduled_at"] = sched_time
        return data

class InterviewResponse(BaseModel):
    id: str
    application_id: str
    recruiter_id: str
    candidate_id: str
    interview_type: str
    interview_mode: Optional[str] = "HUMAN"
    scheduled_time: datetime
    duration_minutes: int
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    instructions: Optional[str] = None
    status: str
    email_status: Optional[str] = "PENDING"
    brevo_message_id: Optional[str] = None
    email_sent_at: Optional[datetime] = None
    email_error_message: Optional[str] = None
    room_id: Optional[str] = None
    room_status: Optional[str] = "WAITING"
    room_started_at: Optional[datetime] = None
    room_ended_at: Optional[datetime] = None
    round_number: Optional[int] = 1
    round_title: Optional[str] = "Round 1 - Technical Screen"
    recording_enabled: Optional[bool] = False
    recording_status: Optional[str] = "NOT_RECORDED"
    is_admitted: Optional[bool] = False
    ai_config_json: Optional[Dict[str, Any]] = None
    ai_takeover_status: Optional[str] = "AI_ACTIVE"
    current_question_index: Optional[int] = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    candidate_name: Optional[str] = None
    recruiter_name: Optional[str] = None

    class Config:
        from_attributes = True

# --- Candidate Evaluation Schemas ---
class CandidateEvaluationCreate(BaseModel):
    application_id: str
    interview_id: Optional[str] = None
    technical_score: float = Field(..., ge=1.0, le=5.0)
    communication_score: float = Field(..., ge=1.0, le=5.0)
    experience_score: float = Field(..., ge=1.0, le=5.0)
    overall_recommendation: str = "HIRE"  # STRONG_HIRE, HIRE, NEUTRAL, DO_NOT_HIRE
    interview_feedback: Optional[str] = None
    internal_notes: Optional[str] = None

class CandidateEvaluationResponse(BaseModel):
    id: str
    application_id: str
    recruiter_id: str
    interview_id: Optional[str] = None
    technical_score: float
    communication_score: float
    experience_score: float
    overall_score: float
    overall_recommendation: str
    interview_feedback: Optional[str] = None
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    recruiter_name: Optional[str] = None

    class Config:
        from_attributes = True

class CandidateComparisonItem(BaseModel):
    application_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    status: str
    match_score: Optional[float] = None
    total_years_exp: float
    verified_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    evaluations_count: int
    avg_technical_score: Optional[float] = None
    avg_communication_score: Optional[float] = None
    avg_experience_score: Optional[float] = None
    latest_recommendation: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    resume_id: str
    status: ApplicationStatusEnum
    cover_letter: Optional[str] = None
    recruiter_notes: Optional[str] = None
    application_date: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None
    candidate: Optional[CandidateProfileResponse] = None
    resume: Optional[ResumeResponse] = None
    history: List[ApplicationHistoryResponse] = []
    interviews: List[InterviewResponse] = []
    evaluations: List[CandidateEvaluationResponse] = []

    class Config:
        from_attributes = True

# --- Notification Schemas ---
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Message Schemas ---
class MessageCreate(BaseModel):
    receiver_id: str
    application_id: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=5000)

class MessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    application_id: Optional[str] = None
    content: str
    is_read: bool
    created_at: datetime
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    partner_id: str
    partner_name: str
    partner_role: str
    partner_email: str
    last_message: str
    last_message_time: datetime
    unread_count: int

# --- Saved Job Schemas ---
class SavedJobResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    created_at: datetime
    job: JobResponse

    class Config:
        from_attributes = True

class RecommendedJobResponse(BaseModel):
    job: JobResponse
    match_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    recommendation_reason: str

# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_email: Optional[str] = None
    action_type: str
    target_resource: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Admin Analytics Schemas ---
class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_candidates: int
    total_recruiters: int
    total_jobs: int
    active_jobs: int
    total_applications: int
    applications_by_status: Dict[str, int]
    growth_trends: Optional[Dict[str, Any]] = None

# --- Recruiter Analytics Schemas ---
class RecruiterAnalyticsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    total_applicants: int
    shortlisted_candidates: int
    interviewed_candidates: int
    selected_candidates: int
    rejected_candidates: int
    application_to_interview_rate: float
    interview_to_offer_rate: float
    avg_days_to_hire: Optional[float] = None
    pipeline_funnel: Dict[str, int]

# --- Password Reset Schemas ---
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=255)

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., max_length=100)
    confirm_password: str = Field(..., max_length=100)

class ResendResetEmailRequest(BaseModel):
    email: str = Field(..., max_length=255)

class PasswordResetResponse(BaseModel):
    message: str
    success: bool = True

# --- Email Verification Schemas ---
class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)

class VerifyEmailResponse(BaseModel):
    message: str
    success: bool = True
    email: Optional[str] = None
    already_verified: bool = False
    email_verified: bool = True

class ResendVerificationRequest(BaseModel):
    email: str = Field(..., max_length=255)

class ResendVerificationResponse(BaseModel):
    message: str
    success: bool = True
    already_verified: bool = False
    cooldown_seconds: Optional[int] = 60

class VerificationStatusResponse(BaseModel):
    email: str
    email_verified: bool
    email_verified_at: Optional[datetime] = None

# --- Technical Practice & Technology Schemas ---
class CandidateTechnologyBase(BaseModel):
    technology_name: str
    category: str = "LANGUAGE"
    proficiency_level: str = "INTERMEDIATE"

class CandidateTechnologyCreate(CandidateTechnologyBase):
    pass

class CandidateTechnologyResponse(CandidateTechnologyBase):
    id: str
    candidate_id: str
    is_resume_detected: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PracticeQuestionResponse(BaseModel):
    id: str
    technology: str
    difficulty: str
    question_type: str
    title: str
    prompt: str
    options: Optional[List[Dict[str, Any]]] = None
    hint: Optional[str] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    sample_test_cases: Optional[List[Dict[str, Any]]] = None
    is_ai_generated: bool = False
    batch_number: int = 1
    created_at: datetime

    class Config:
        from_attributes = True

class PracticeAttemptRequest(BaseModel):
    candidate_answer: str
    time_spent_seconds: Optional[int] = 0
    hints_used: Optional[int] = 0

class PracticeAttemptResponse(BaseModel):
    id: str
    question_id: str
    technology: str
    difficulty: str
    candidate_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    correct_answer: str
    completed_at: datetime

    class Config:
        from_attributes = True

class PracticeAnalyticsResponse(BaseModel):
    total_attempted: int
    total_correct: int
    overall_accuracy: float
    technologies_detected_count: int
    technology_breakdown: Dict[str, Dict[str, Any]]
    difficulty_breakdown: Dict[str, Dict[str, Any]]
    recent_attempts: List[Dict[str, Any]] = []

# ==============================================================================
# First-Round MCQ Assessment Schemas
# ==============================================================================

class AssessmentOptionCreate(BaseModel):
    option_key: str = Field(..., min_length=1, max_length=10)
    option_text: str = Field(..., min_length=1)
    is_correct: bool = False

class AssessmentQuestionCreate(BaseModel):
    bank_question_id: Optional[str] = None
    question_text: str = Field(..., min_length=3)
    explanation: Optional[str] = None
    order_num: int = 1
    marks: int = Field(1, ge=1)
    options: List[AssessmentOptionCreate] = Field(..., min_length=2, max_length=5)

class AssessmentCreate(BaseModel):
    job_id: str
    title: str = Field(..., min_length=3, max_length=200)
    instructions: Optional[str] = None
    duration_minutes: int = Field(30, ge=1, le=180)
    passing_marks: int = Field(..., ge=1)
    randomize_questions: bool = False
    randomize_options: bool = False
    auto_selection_config: Optional[Dict[str, Any]] = None
    questions: List[AssessmentQuestionCreate] = Field(..., min_length=1)

class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=180)
    passing_marks: Optional[int] = Field(None, ge=1)
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    auto_selection_config: Optional[Dict[str, Any]] = None
    questions: Optional[List[AssessmentQuestionCreate]] = None

class AssessmentOptionResponse(BaseModel):
    id: str
    option_key: str
    option_text: str
    is_correct: Optional[bool] = None  # None for candidate views

    class Config:
        from_attributes = True

class AssessmentQuestionResponse(BaseModel):
    id: str
    bank_question_id: Optional[str] = None
    question_text: str
    explanation: Optional[str] = None
    order_num: int
    marks: int
    options: List[AssessmentOptionResponse]

    class Config:
        from_attributes = True

class AssessmentResponse(BaseModel):
    id: str
    job_id: str
    job_title: Optional[str] = None
    recruiter_id: str
    title: str
    instructions: Optional[str] = None
    duration_minutes: int
    total_marks: int
    passing_marks: int
    question_count: int = 0
    status: str
    randomize_questions: bool = False
    randomize_options: bool = False
    auto_selection_config: Optional[Dict[str, Any]] = None
    version: int = 1
    created_at: datetime
    published_at: Optional[datetime] = None
    questions: Optional[List[AssessmentQuestionResponse]] = None

    class Config:
        from_attributes = True

class AssessmentAssignRequest(BaseModel):
    candidate_ids: List[str] = Field(..., min_length=1)
    deadline_at: Optional[datetime] = None

class ShortlistedCandidateItem(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: str
    application_id: str
    application_status: str
    is_assigned: bool
    assignment_id: Optional[str] = None
    assignment_status: Optional[str] = None

class CandidateAssignmentResponse(BaseModel):
    id: str
    assessment_id: str
    assessment_title: str
    job_id: str
    job_title: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    application_id: str
    status: str
    review_status: Optional[str] = "PENDING_REVIEW"
    final_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    assigned_at: datetime
    deadline_at: Optional[datetime] = None
    duration_minutes: int
    total_marks: int
    passing_marks: int
    question_count: int
    has_started: bool = False
    is_completed: bool = False
    result: Optional[str] = None
    marks_obtained: Optional[int] = None
    percentage: Optional[float] = None

    class Config:
        from_attributes = True

class CandidateAssessmentInstructions(BaseModel):
    assignment_id: str
    assessment_id: str
    title: str
    job_title: str
    instructions: Optional[str] = None
    duration_minutes: int
    question_count: int
    total_marks: int
    passing_marks: int
    status: str

class CandidateAnswerSubmit(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None

class SaveAnswersRequest(BaseModel):
    answers: List[CandidateAnswerSubmit]

class AttemptStatusResponse(BaseModel):
    attempt_id: str
    assignment_id: str
    status: str
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    total_questions: int
    saved_answers: Dict[str, str] = {}
    questions: List[AssessmentQuestionResponse]

class CandidateSubmissionConfirmationResponse(BaseModel):
    assignment_id: str
    attempt_id: str
    assessment_title: str
    job_title: str
    status: str = "SUBMITTED"
    submission_status: str = "PENDING_REVIEW"
    review_status: str = "PENDING_REVIEW"
    submitted_at: datetime
    total_questions: int
    questions_answered: int
    message: str
    candidate_message: Optional[str] = None

    class Config:
        from_attributes = True

class CandidateAssessmentStatusResponse(BaseModel):
    assignment_id: str
    assessment_title: str
    job_title: str
    review_status: str
    submitted_at: Optional[datetime] = None
    message: str
    candidate_message: Optional[str] = None
    application_status: Optional[str] = None
    status_headline: Optional[str] = "Assessment Under Review"
    status_message: Optional[str] = None
    is_completed: bool = True

    @model_validator(mode="before")
    @classmethod
    def populate_headline_and_msg(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("status_headline"):
                data["status_headline"] = "Assessment Under Review"
            if not data.get("status_message"):
                data["status_message"] = data.get("message", "Thank you for completing your assessment.")
        return data

    class Config:
        from_attributes = True

class CandidateResultResponse(BaseModel):
    assignment_id: str
    assessment_title: str
    job_title: str
    total_questions: int
    questions_answered: int
    total_marks: int
    marks_obtained: int
    passing_marks: int
    percentage: float
    result: str
    completed_at: datetime
    application_status: str

class RecruiterCandidateAnswerItem(BaseModel):
    question_id: str
    question_text: str
    order_num: int
    marks: int
    options: List[AssessmentOptionResponse]
    selected_option_id: Optional[str] = None
    correct_option_id: str
    is_correct: bool
    marks_awarded: int

class RecruiterCandidateReviewResponse(BaseModel):
    assignment_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str
    job_title: str
    assessment_title: str
    total_marks: int
    marks_obtained: int
    passing_marks: int
    percentage: float
    result: str
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    answers: List[RecruiterCandidateAnswerItem]

class RecruiterDetailedAnswerItem(BaseModel):
    question_id: str
    question_text: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    explanation: Optional[str] = None
    order_num: int
    marks: int
    options: List[AssessmentOptionResponse]
    selected_option_id: Optional[str] = None
    selected_option_key: Optional[str] = None
    selected_option_text: Optional[str] = None
    correct_option_id: Optional[str] = None
    correct_option_key: Optional[str] = None
    correct_option_text: Optional[str] = None
    correct_answer: Optional[str] = None
    candidate_selected_option: Optional[str] = None
    status: str  # "CORRECT", "INCORRECT", "UNANSWERED"
    is_correct: bool
    marks_awarded: float

    @model_validator(mode="before")
    @classmethod
    def populate_answer_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("correct_answer") is None:
                data["correct_answer"] = data.get("correct_option_key")
            if data.get("candidate_selected_option") is None:
                data["candidate_selected_option"] = data.get("selected_option_key")
        return data

class DecisionHistoryItemResponse(BaseModel):
    id: str
    previous_status: Optional[str] = None
    new_status: str
    decision: str
    recruiter_name: Optional[str] = None
    reason: Optional[str] = None
    remarks: Optional[str] = None
    candidate_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecruiterAssessmentReviewItem(BaseModel):
    assignment_id: str
    attempt_id: Optional[str] = None
    candidate_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    candidate_title: Optional[str] = None
    job_id: str
    job_title: str
    assessment_id: str
    assessment_title: str
    assigned_at: datetime
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    time_taken_formatted: Optional[str] = None
    total_questions: int
    questions_answered: int
    correct_answers_count: int
    incorrect_answers_count: int
    unanswered_count: int
    total_marks: float
    marks_obtained: float
    score_obtained: Optional[float] = None
    passing_marks: float
    percentage: float
    accuracy_percentage: Optional[float] = None
    score_based_outcome: Optional[str] = None
    is_score_adjusted: bool = False
    original_marks_obtained: Optional[float] = None
    internal_outcome: str  # "MET_THRESHOLD", "BELOW_THRESHOLD", "PENDING"
    review_status: str     # "PENDING_REVIEW", "UNDER_REVIEW", "ACCEPTED", "REJECTED", "ON_HOLD", "MOVED_TO_INTERVIEW"
    final_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    recruiter_remarks: Optional[str] = None
    candidate_message: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by_name: Optional[str] = None
    warning_count: int = 0
    decision_email_status: str = "NOT_SENT"
    decision_email_error: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_review_item(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("score_obtained") is None and data.get("marks_obtained") is not None:
                data["score_obtained"] = float(data["marks_obtained"])
            if data.get("marks_obtained") is None and data.get("score_obtained") is not None:
                data["marks_obtained"] = float(data["score_obtained"])
            if data.get("accuracy_percentage") is None and data.get("percentage") is not None:
                data["accuracy_percentage"] = float(data["percentage"])
            if data.get("percentage") is None and data.get("accuracy_percentage") is not None:
                data["percentage"] = float(data["accuracy_percentage"])
            if not data.get("score_based_outcome"):
                passing = data.get("passing_marks", 0)
                score = data.get("score_obtained", data.get("marks_obtained", 0))
                data["score_based_outcome"] = "PASSED" if score >= passing else "FAILED"
        return data

    class Config:
        from_attributes = True

class RecruiterDetailedReviewResponse(RecruiterAssessmentReviewItem):
    review_item: Optional[RecruiterAssessmentReviewItem] = None
    answers: List[RecruiterDetailedAnswerItem] = []
    decision_history: List[DecisionHistoryItemResponse] = []
    monitoring_events: List[Dict[str, Any]] = []
    proctoring_timeline: List[Dict[str, Any]] = []
    session_recording: Optional[Dict[str, Any]] = None
    original_score: Optional[float] = None
    score_adjustment_reason: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_detailed_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            ri = data.get("review_item")
            if ri:
                ri_dict = ri.model_dump() if hasattr(ri, "model_dump") else (ri if isinstance(ri, dict) else ri.__dict__)
                for k, v in ri_dict.items():
                    if k not in data or data[k] is None:
                        data[k] = v
            if "original_score" not in data or data["original_score"] is None:
                data["original_score"] = data.get("original_marks_obtained")
            if "score_adjustment_reason" not in data or data["score_adjustment_reason"] is None:
                data["score_adjustment_reason"] = data.get("decision_reason")
            if not data.get("proctoring_timeline") and data.get("monitoring_events"):
                data["proctoring_timeline"] = data["monitoring_events"]
            elif not data.get("monitoring_events") and data.get("proctoring_timeline"):
                data["monitoring_events"] = data["proctoring_timeline"]
        return data

class RecruiterDecisionRequest(BaseModel):
    decision: str  # ACCEPTED, REJECTED, MOVED_TO_INTERVIEW, ON_HOLD, UNDER_REVIEW
    reason: Optional[str] = None
    decision_reason: Optional[str] = None
    remarks: Optional[str] = None
    recruiter_remarks: Optional[str] = None
    candidate_message: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_decision_req(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "decision_reason" in data and not data.get("reason"):
                data["reason"] = data["decision_reason"]
            if "reason" in data and not data.get("decision_reason"):
                data["decision_reason"] = data["reason"]
            if "recruiter_remarks" in data and not data.get("remarks"):
                data["remarks"] = data["recruiter_remarks"]
            if "remarks" in data and not data.get("recruiter_remarks"):
                data["recruiter_remarks"] = data["remarks"]
        return data

class RecruiterDecisionResponse(BaseModel):
    assignment_id: str
    decision: str
    review_status: str
    application_status: str
    decision_email_status: str
    email_dispatched: bool = False
    history_id: str
    message: str

class ScoreAdjustmentRequest(BaseModel):
    new_score: Optional[float] = None
    adjusted_score: Optional[float] = None
    reason: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            score = data.get("adjusted_score") if data.get("adjusted_score") is not None else data.get("new_score")
            data["new_score"] = float(score) if score is not None else None
            data["adjusted_score"] = float(score) if score is not None else None
        return data

class CandidateComparisonItem(BaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: str
    total_score: float
    score_obtained: Optional[float] = None
    total_marks: float
    accuracy_percentage: float
    time_taken_seconds: Optional[int] = None
    time_taken_formatted: Optional[str] = None
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    review_status: str
    final_decision: Optional[str] = None
    topic_breakdown: Dict[str, Dict[str, Any]] = {}
    difficulty_breakdown: Dict[str, Dict[str, Any]] = {}

    @model_validator(mode="before")
    @classmethod
    def normalize_comparison_item(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("score_obtained") is None and data.get("total_score") is not None:
                data["score_obtained"] = float(data["total_score"])
            if data.get("total_score") is None and data.get("score_obtained") is not None:
                data["total_score"] = float(data["score_obtained"])
        return data

class AssessmentAnalyticsOverview(BaseModel):
    total_assigned: int
    total_started: int
    total_submitted: int
    pending_reviews: int
    accepted_count: int
    rejected_count: int
    on_hold_count: int
    moved_to_interview_count: int
    average_score: float
    average_percentage: float
    average_time_seconds: float
    score_distribution: Dict[str, int] = {}

class AssessmentComparisonResponse(BaseModel):
    assessment_id: str
    assessment_title: str
    job_id: str
    job_title: str
    analytics: AssessmentAnalyticsOverview
    candidates: List[CandidateComparisonItem]

# ==============================================================================
# Question Bank Schemas
# ==============================================================================

class QuestionBankOptionCreate(BaseModel):
    option_key: str = Field(..., min_length=1, max_length=10)
    option_text: str = Field(..., min_length=1)
    is_correct: bool = False

class QuestionBankOptionResponse(BaseModel):
    id: str
    option_key: str
    option_text: str
    is_correct: Optional[bool] = None

    class Config:
        from_attributes = True

class QuestionBankItemCreate(BaseModel):
    technology: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=1, max_length=100)
    subtopic: Optional[str] = None
    difficulty: str = "INTERMEDIATE"
    question_text: str = Field(..., min_length=5)
    explanation: Optional[str] = None
    marks: int = Field(5, ge=1, le=50)
    tags: List[str] = []
    options: List[QuestionBankOptionCreate] = Field(..., min_length=2, max_length=5)

class QuestionBankItemUpdate(BaseModel):
    technology: Optional[str] = None
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None
    question_text: Optional[str] = None
    explanation: Optional[str] = None
    marks: Optional[int] = Field(None, ge=1, le=50)
    tags: Optional[List[str]] = None
    options: Optional[List[QuestionBankOptionCreate]] = None
    status: Optional[str] = None

class QuestionBankItemResponse(BaseModel):
    id: str
    technology: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    question_type: str = "SINGLE_CORRECT_MCQ"
    question_text: str
    explanation: Optional[str] = None
    marks: int
    tags: List[str] = []
    is_global: bool
    created_by_user_id: Optional[str] = None
    creator_name: Optional[str] = None
    status: str
    usage_count: int = 0
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    options: List[QuestionBankOptionResponse] = []

    class Config:
        from_attributes = True

class QuestionCollectionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    technology: Optional[str] = None
    question_ids: List[str] = []

class QuestionCollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    technology: Optional[str] = None
    question_count: int = 0
    created_at: datetime
    updated_at: datetime
    questions: Optional[List[QuestionBankItemResponse]] = None

    class Config:
        from_attributes = True

class AutoGenerateAssessmentRequest(BaseModel):
    job_id: str
    title: str = Field(..., min_length=3, max_length=200)
    instructions: Optional[str] = None
    duration_minutes: int = Field(30, ge=1, le=180)
    passing_marks: int = Field(..., ge=1)
    technology: str = Field(..., min_length=1)
    topic: Optional[str] = None
    question_count: int = Field(5, ge=1, le=100)
    total_questions: Optional[int] = None
    marks_per_question: Optional[int] = Field(None, ge=1, le=100)
    difficulty_distribution: Optional[Dict[str, Any]] = None
    randomize_questions: bool = True
    randomize_options: bool = True

    @model_validator(mode='after')
    def sync_question_count(self):
        if self.total_questions and not self.question_count:
            self.question_count = self.total_questions
        elif self.total_questions and self.question_count == 5 and self.total_questions != 5:
            self.question_count = self.total_questions
        return self

class BulkImportRequest(BaseModel):
    csv_content: str = Field(..., min_length=1)
    commit: bool = False

class DuplicateCheckRequest(BaseModel):
    question_text: Optional[str] = None
    text: Optional[str] = None
    exclude_id: Optional[str] = None

    @model_validator(mode='after')
    def sync_text(self):
        if not self.question_text and self.text:
            self.question_text = self.text
        if not self.question_text:
            self.question_text = ""
        return self

class BulkImportRowValidation(BaseModel):
    row_index: int
    is_valid: bool
    question_text: str
    technology: str
    topic: str
    difficulty: str
    marks: int = 1
    errors: List[str] = []

class BulkImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    rows: List[BulkImportRowValidation]
    can_commit: bool

class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    similar_question_id: Optional[str] = None
    similarity_reason: Optional[str] = None

class ExtractedOptionItem(BaseModel):
    option_key: str
    option_text: str
    is_correct: bool = False

class ExtractedQuestionItem(BaseModel):
    temp_id: str
    row_index: int
    question_text: str
    options: List[ExtractedOptionItem]
    correct_option: Optional[str] = None
    has_correct_answer: bool = False
    explanation: Optional[str] = None
    marks: int = 1
    difficulty: str = "INTERMEDIATE"
    technology: str = "General"
    topic: str = "General"
    source_file: Optional[str] = None
    source_page: Optional[int] = 1
    validation_status: str = "VALID"
    errors: List[str] = []
    similar_to_id: Optional[str] = None
    similarity_reason: Optional[str] = None
    is_approved: bool = True

class QuestionUploadExtractResponse(BaseModel):
    filename: str
    file_type: str
    is_scanned: bool = False
    total_extracted: int
    valid_count: int
    missing_answer_count: int
    duplicate_count: int
    questions: List[ExtractedQuestionItem]

class BatchImportOptionItem(BaseModel):
    option_key: str = Field(..., max_length=10)
    option_text: str = Field(..., min_length=1)
    is_correct: bool = False

class BatchImportItem(BaseModel):
    question_text: str = Field(..., min_length=5)
    options: List[BatchImportOptionItem]
    difficulty: str = "INTERMEDIATE"
    marks: int = Field(1, ge=1, le=50)
    explanation: Optional[str] = None
    technology: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    subtopic: Optional[str] = None
    tags: List[str] = []
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    is_approved: bool = True

class BatchImportRequest(BaseModel):
    filename: str
    file_type: str
    file_size: Optional[int] = 0
    technology: str
    topic: Optional[str] = None
    questions: List[BatchImportItem]

class BatchImportResponse(BaseModel):
    imported_count: int
    import_batch_id: str
    imported_question_ids: List[str] = []
    message: str

class AssessmentAnalyticsResponse(BaseModel):
    assessment_id: str
    title: str
    total_assigned: int
    total_started: int
    total_completed: int
    total_passed: int
    total_failed: int
    pass_percentage: float
    average_marks: float
    questions_analytics: List[Dict[str, Any]] = []
    difficulty_performance: Dict[str, Any] = {}
    high_failure_questions: List[Dict[str, Any]] = []

# ==============================================================================
# Assessment Proctoring & Surveillance Schemas
# ==============================================================================

class ProctoringSessionStartRequest(BaseModel):
    attempt_id: str
    camera_permission_granted: bool = True

class ProctoringEventCreate(BaseModel):
    event_type: str = Field(..., description="FACE_NOT_DETECTED, MULTIPLE_FACES_DETECTED, TAB_SWITCH, WINDOW_BLUR, CAMERA_INTERRUPTED, CAMERA_RESTORED, SUSPICIOUS_ACTIVITY")
    duration_seconds: float = 0.0
    severity: str = Field("LOW", description="LOW, MEDIUM, HIGH")
    details_json: Optional[Dict[str, Any]] = None

class ProctoringEventResponse(BaseModel):
    id: str
    proctoring_session_id: str
    event_type: str
    event_timestamp: datetime
    duration_seconds: float
    severity: str
    details_json: Dict[str, Any]
    reviewed_status: str
    reviewed_by_admin_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProctoringSessionResponse(BaseModel):
    id: str
    assessment_attempt_id: str
    candidate_id: str
    assessment_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    camera_permission_granted: bool
    monitoring_status: str
    total_warning_count: int
    tab_switch_count: int
    face_not_detected_count: int
    multiple_faces_count: int
    camera_interruption_count: int
    warning_level: str = "NORMAL"
    created_at: datetime

    class Config:
        from_attributes = True

class ProctoringSessionDetailResponse(BaseModel):
    id: str
    assessment_attempt_id: str
    candidate_id: str
    assessment_id: str
    candidate_name: str
    candidate_email: str
    assessment_title: str
    job_title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    camera_permission_granted: bool
    monitoring_status: str
    total_warning_count: int
    tab_switch_count: int
    face_not_detected_count: int
    multiple_faces_count: int
    camera_interruption_count: int
    warning_level: str = "NORMAL"
    score: Optional[int] = None
    total_marks: Optional[int] = None
    percentage: Optional[float] = None
    result: Optional[str] = None
    events: List[ProctoringEventResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

class AdminEventReviewRequest(BaseModel):
    reviewed_status: str = Field(..., pattern="^(REVIEWED|DISMISSED)$")
    admin_notes: Optional[str] = None

class AdminSessionReviewRequest(BaseModel):
    monitoring_status: str = Field(..., pattern="^(ACTIVE|COMPLETED|FLAGGED)$")
    admin_notes: Optional[str] = None

class AdminProctoringListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ProctoringSessionDetailResponse]

# ============================================================================
# CLOUDINARY MEDIA & ASSET MANAGEMENT SCHEMAS
# ============================================================================

class MediaAssetResponse(BaseModel):
    id: str
    public_id: str
    asset_id: Optional[str] = None
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    interview_id: Optional[str] = None
    video_assessment_id: Optional[str] = None
    original_filename: str
    resource_type: str
    file_format: str
    file_size_bytes: int
    video_duration_seconds: Optional[float] = None
    secure_url: str
    playback_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    folder: str
    upload_status: str
    access_classification: str
    created_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True

class MediaUploadSignatureRequest(BaseModel):
    folder_key: str = "interviews"  # resumes, interviews, assessments, candidate_responses, attachments
    resource_type: str = "video"
    tags: Optional[str] = None

class MediaUploadSignatureResponse(BaseModel):
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    resource_type: str
    upload_url: str

class MediaSignedPlaybackResponse(BaseModel):
    asset_id: str
    public_id: str
    playback_url: str
    thumbnail_url: Optional[str] = None
    expires_in_seconds: int = 3600
    access_classification: str
    resource_type: Optional[str] = "video"
    file_format: Optional[str] = None
    secure_url: Optional[str] = None
    upload_status: Optional[str] = "COMPLETED"

class SessionRecordingUploadRequest(BaseModel):
    public_id: str
    asset_id: Optional[str] = None
    secure_url: str
    playback_url: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    file_size_bytes: Optional[int] = 0
    file_format: Optional[str] = "webm"
    original_filename: Optional[str] = "session_recording.webm"
    resource_type: Optional[str] = "video"

# ============================================================================
# LIVE VIDEO INTERVIEW & LIVEKIT SCHEMAS
# ============================================================================

class InterviewRoomTokenResponse(BaseModel):
    token: str
    server_url: str
    room_name: str
    identity: str
    display_name: str
    role: str
    is_recruiter: bool
    is_admitted: bool
    expires_at: str

class RecordingConsentRequest(BaseModel):
    consent_granted: bool

class RecordingConsentResponse(BaseModel):
    interview_id: str
    user_id: str
    role: str
    consent_granted: bool
    consent_timestamp: datetime
    both_consented: bool

class InterviewRecordingResponse(BaseModel):
    id: str
    interview_id: str
    media_asset_id: Optional[str] = None
    egress_id: Optional[str] = None
    status: str
    recording_consent_recruiter: bool
    recording_consent_candidate: bool
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: int = 0
    playback_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewRoomStatusResponse(BaseModel):
    interview_id: str
    room_id: str
    room_status: str
    is_admitted: bool
    recording_enabled: bool
    recording_status: str
    both_consented_recording: bool
    scheduled_time: datetime
    duration_minutes: int
    candidate_name: Optional[str] = None
    recruiter_name: Optional[str] = None
    job_title: Optional[str] = None
    interview_mode: Optional[str] = "HUMAN"
    ai_takeover_status: Optional[str] = "AI_ACTIVE"
    current_question_index: Optional[int] = 0

# ============================================================================
# SCORECARD & INTERVIEW TRANSCRIPT SCHEMAS
# ============================================================================

class InterviewScorecardCreate(BaseModel):
    technical_knowledge_score: float = Field(..., ge=1.0, le=5.0)
    technical_evidence_notes: Optional[str] = None
    communication_score: float = Field(..., ge=1.0, le=5.0)
    communication_evidence_notes: Optional[str] = None
    problem_solving_score: float = Field(..., ge=1.0, le=5.0)
    problem_solving_notes: Optional[str] = None
    role_specific_score: float = Field(..., ge=1.0, le=5.0)
    role_specific_notes: Optional[str] = None
    cultural_alignment_score: float = Field(..., ge=1.0, le=5.0)
    cultural_alignment_notes: Optional[str] = None
    overall_recommendation: str = Field(..., pattern="^(RECOMMENDED|NOT_RECOMMENDED|UNDER_REVIEW|ADDITIONAL_INTERVIEW_REQUIRED)$")
    strengths: Optional[str] = None
    improvement_areas: Optional[str] = None
    private_evaluation_notes: Optional[str] = None

class InterviewScorecardResponse(BaseModel):
    id: str
    interview_id: str
    recruiter_id: str
    application_id: str
    technical_knowledge_score: float
    technical_evidence_notes: Optional[str] = None
    communication_score: float
    communication_evidence_notes: Optional[str] = None
    problem_solving_score: float
    problem_solving_notes: Optional[str] = None
    role_specific_score: float
    role_specific_notes: Optional[str] = None
    cultural_alignment_score: float
    cultural_alignment_notes: Optional[str] = None
    overall_score: float
    overall_recommendation: str
    strengths: Optional[str] = None
    improvement_areas: Optional[str] = None
    private_evaluation_notes: Optional[str] = None
    is_submitted: bool
    created_at: datetime
    updated_at: datetime
    recruiter_name: Optional[str] = None

    class Config:
        from_attributes = True

class InterviewTranscriptResponse(BaseModel):
    id: str
    interview_id: str
    full_transcript_text: Optional[str] = None
    timestamps_json: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None
    technical_topics_json: List[str] = []
    candidate_strengths_summary: Optional[str] = None
    candidate_concerns_summary: Optional[str] = None
    draft_feedback_json: Dict[str, Any] = {}
    is_approved_by_recruiter: bool
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApproveTranscriptRequest(BaseModel):
    edited_summary: Optional[str] = None
    edited_feedback: Optional[Dict[str, Any]] = None

# --- AI Live & Hybrid Interview Schemas ---
class InterviewQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=3)
    question_type: str = Field("TECHNICAL", description="TECHNICAL, BEHAVIORAL, PROBLEM_SOLVING, ROLE_SPECIFIC, SITUATIONAL")
    source: str = Field("CUSTOM", description="CUSTOM or AI_GENERATED")
    sequence_number: int = 1
    expected_concepts: Optional[List[str]] = None
    max_duration_seconds: int = 180

class InterviewQuestionResponse(BaseModel):
    id: str
    interview_id: str
    question_text: str
    question_type: str
    source: str
    sequence_number: int
    expected_concepts: Optional[List[str]] = []
    max_duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True

class GenerateAIQuestionsRequest(BaseModel):
    job_id: Optional[str] = None
    application_id: Optional[str] = None
    interview_id: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    difficulty: Optional[str] = "INTERMEDIATE"  # ENTRY, INTERMEDIATE, SENIOR, LEAD
    question_count: Optional[int] = 5
    categories: Optional[List[str]] = None

class InterviewConfigureAIRequest(BaseModel):
    interview_mode: str = Field("AI_LIVE", description="AI_LIVE, HYBRID, CONFIGURED")
    duration_minutes: Optional[int] = 30
    difficulty: Optional[str] = "INTERMEDIATE"
    question_count: Optional[int] = 5
    categories: Optional[List[str]] = None
    voice: Optional[str] = "alloy"
    allow_recruiter_takeover: Optional[bool] = True
    prep_time_seconds: Optional[int] = 30
    questions: Optional[List[InterviewQuestionCreate]] = None

class InterviewResponseItemCreate(BaseModel):
    question_id: str
    transcript: str
    response_duration: Optional[float] = 0.0
    evaluation: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    score: Optional[float] = 3.0

class InterviewResponseItemResponse(BaseModel):
    id: str
    interview_id: str
    question_id: str
    transcript: Optional[str] = None
    response_duration: float
    evaluation: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    score: float
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewEvaluationResponse(BaseModel):
    id: str
    interview_id: str
    overall_summary: Optional[str] = None
    overall_score: float
    competency_scores: Dict[str, Any] = {}
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    generated_at: datetime
    reviewed_by: Optional[str] = None
    review_status: str
    recruiter_notes: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterviewEvaluationUpdate(BaseModel):
    overall_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    competency_scores: Optional[Dict[str, Any]] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    review_status: Optional[str] = Field(None, description="PENDING_REVIEW, ACCEPTED, OVERRIDDEN")
    recruiter_notes: Optional[str] = None

class HybridTakeoverRequest(BaseModel):
    takeover: bool = Field(..., description="True to mute AI and activate recruiter; False to hand back to AI")

# ============================================================================
# VIDEO ASSESSMENT SCHEMAS
# ============================================================================

class VideoAssessmentQuestionCreate(BaseModel):
    order_num: int = 1
    question_text: str
    question_instructions: Optional[str] = None
    max_duration_seconds: int = 120
    prep_time_seconds: int = 30
    retake_limit: int = 2
    is_required: bool = True

class VideoAssessmentQuestionResponse(BaseModel):
    id: str
    video_assessment_id: str
    order_num: int
    question_text: str
    question_instructions: Optional[str] = None
    max_duration_seconds: int
    prep_time_seconds: int
    retake_limit: int
    is_required: bool
    created_at: datetime

    class Config:
        from_attributes = True

class VideoAssessmentCreate(BaseModel):
    job_id: str
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    questions: List[VideoAssessmentQuestionCreate]

class VideoAssessmentResponse(BaseModel):
    id: str
    job_id: str
    recruiter_id: str
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    total_questions: int
    submission_deadline: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    questions: List[VideoAssessmentQuestionResponse] = []

    class Config:
        from_attributes = True

class CandidateVideoResponseCreate(BaseModel):
    question_id: str
    media_asset_id: str
    duration_seconds: float
    retake_count: int = 0

class CandidateVideoResponseItem(BaseModel):
    id: str
    question_id: str
    question_text: str
    max_duration_seconds: int
    media_asset_id: Optional[str] = None
    duration_seconds: float
    retake_count: int
    submitted_at: datetime
    playback_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    recruiter_rating: Optional[float] = None
    recruiter_notes: Optional[str] = None

class CandidateVideoAssignmentResponse(BaseModel):
    id: str
    video_assessment_id: str
    candidate_id: str
    application_id: str
    title: str
    job_title: str
    total_questions: int
    status: str
    review_status: str
    assigned_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CandidateVideoAssignmentDetailResponse(BaseModel):
    id: str
    video_assessment_id: str
    candidate_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    job_title: str
    status: str
    review_status: str
    assigned_at: datetime
    submitted_at: Optional[datetime] = None
    questions: List[VideoAssessmentQuestionResponse] = []
    responses: List[CandidateVideoResponseItem] = []

class VideoAssessmentReviewRequest(BaseModel):
    review_status: str = Field(..., pattern="^(ACCEPTED|REJECTED|UNDER_REVIEW)$")
    overall_score: Optional[float] = None
    recruiter_feedback: Optional[str] = None
    question_notes: Optional[Dict[str, str]] = None


