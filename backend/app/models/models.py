import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, ForeignKey, DateTime, Enum, JSON, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class RoleEnum(str, PyEnum):
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"

class ProcessingStatusEnum(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobTypeEnum(str, PyEnum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    REMOTE = "REMOTE"

class JobStatusEnum(str, PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

class ApplicationStatusEnum(str, PyEnum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

# Association table for Candidate <-> Skill (many-to-many)
candidate_skills = Table(
    "candidate_skills",
    Base.metadata,
    Column("candidate_id", String(36), ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
)

# Association table for Job <-> Skill (many-to-many)
class JobSkill(Base):
    __tablename__ = "job_skills"
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    is_required = Column(Boolean, default=True)

    skill = relationship("Skill")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.JOB_SEEKER)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    candidate_profile = relationship("Candidate", back_populates="user", uselist=False, cascade="all, delete-orphan")
    recruiter_profile = relationship("Recruiter", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="actor")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    created_questions = relationship("QuestionBankItem", back_populates="created_by")
    question_collections = relationship("QuestionCollection", back_populates="user", cascade="all, delete-orphan")
    import_batches = relationship("QuestionImportBatch", back_populates="user", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    location = Column(String(150), nullable=True)
    contact_email = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    recruiters = relationship("Recruiter", back_populates="company")
    jobs = relationship("Job", back_populates="company")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    title = Column(String(150), nullable=True)
    location = Column(String(150), nullable=True)
    bio = Column(Text, nullable=True)
    education = Column(JSON, default=list)      # [{degree, institution, year, grade}]
    experience = Column(JSON, default=list)     # [{title, company, duration, description}]
    total_years_exp = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="candidate_profile")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary=candidate_skills, back_populates="candidates")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    technologies = relationship("CandidateTechnology", back_populates="candidate", cascade="all, delete-orphan")
    practice_attempts = relationship("PracticeAttempt", back_populates="candidate", cascade="all, delete-orphan")
    assessment_assignments = relationship("CandidateAssessmentAssignment", back_populates="candidate", cascade="all, delete-orphan")
    video_assignments = relationship("CandidateVideoAssignment", back_populates="candidate", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="candidate")

class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    designation = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="recruiter_profile")
    company = relationship("Company", back_populates="recruiters")
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="recruiter", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="recruiter", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="recruiter", cascade="all, delete-orphan")
    video_assessments = relationship("VideoAssessment", back_populates="recruiter", cascade="all, delete-orphan")
    interview_scorecards = relationship("InterviewScorecard", back_populates="recruiter", cascade="all, delete-orphan")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    skill_name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=True)

    candidates = relationship("Candidate", secondary=candidate_skills, back_populates="skills")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, default=dict)
    confidence_score = Column(Float, nullable=True, default=100.0)
    missing_fields = Column(JSON, default=list)
    processing_status = Column(Enum(ProcessingStatusEnum), default=ProcessingStatusEnum.PENDING)
    error_message = Column(String(500), nullable=True)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String(100), nullable=True)
    location = Column(String(150), nullable=False)
    experience_min = Column(Float, default=0.0)
    experience_max = Column(Float, default=0.0)
    job_type = Column(Enum(JobTypeEnum), default=JobTypeEnum.FULL_TIME)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    recruiter = relationship("Recruiter", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    job_skills = relationship("JobSkill", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    analyses = relationship("ResumeAnalysis", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="job", cascade="all, delete-orphan")
    video_assessments = relationship("VideoAssessment", back_populates="job", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="job")

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.APPLIED)
    cover_letter = Column(Text, nullable=True)
    recruiter_notes = Column(Text, nullable=True)  # Internal recruiter notes (private to recruiters)
    application_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    history = relationship("ApplicationHistory", back_populates="application", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    evaluations = relationship("CandidateEvaluation", back_populates="application", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="application")
    assessment_assignments = relationship("CandidateAssessmentAssignment", back_populates="application", cascade="all, delete-orphan")
    assessment_results = relationship("AssessmentResult", back_populates="application", cascade="all, delete-orphan")
    video_assignments = relationship("CandidateVideoAssignment", back_populates="application", cascade="all, delete-orphan")
    scorecards = relationship("InterviewScorecard", back_populates="application", cascade="all, delete-orphan")

    # Partial unique index: prevents duplicate active applications while permitting re-application after WITHDRAWN
    __table_args__ = (
        Index(
            "uq_job_candidate_active",
            "job_id",
            "candidate_id",
            unique=True,
            postgresql_where=(status != ApplicationStatusEnum.WITHDRAWN)
        ),
    )

class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Float, nullable=True)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    recommendations = Column(Text, nullable=True)
    analysis_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="analyses")
    job = relationship("Job", back_populates="analyses")

class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="history")
    changed_by = relationship("User")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    interview_type = Column(String(50), nullable=False, default="ONLINE")  # ONLINE, PHONE, IN_PERSON
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=45)
    meeting_link = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String(50), default="SCHEDULED")  # SCHEDULED, COMPLETED, RESCHEDULED, CANCELLED
    email_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ACCEPTED_BY_BREVO, FAILED, RETRY_PENDING
    brevo_message_id = Column(String(255), nullable=True)
    email_sent_at = Column(DateTime, nullable=True)
    email_error_message = Column(Text, nullable=True)

    # Live Video Meeting, Room State & Recording Telemetry
    room_id = Column(String(100), default=generate_uuid, unique=True, index=True)
    room_status = Column(String(50), default="SCHEDULED")  # SCHEDULED, WAITING, IN_PROGRESS, COMPLETED, CANCELLED
    room_started_at = Column(DateTime, nullable=True)
    room_ended_at = Column(DateTime, nullable=True)
    round_number = Column(Integer, default=1)
    round_title = Column(String(100), default="Technical Interview")
    recording_enabled = Column(Boolean, default=False)
    recording_status = Column(String(50), default="OFF")  # OFF, CONSENT_PENDING, RECORDING, PROCESSING, COMPLETED, FAILED
    is_admitted = Column(Boolean, default=True)
    candidate_joined_at = Column(DateTime, nullable=True)
    recruiter_joined_at = Column(DateTime, nullable=True)

    # AI & Hybrid Interview Extensions
    interview_mode = Column(String(50), default="HUMAN", nullable=False)  # HUMAN, AI_LIVE, HYBRID, CONFIGURED
    ai_config_json = Column(JSON, default=dict, nullable=False)
    ai_takeover_status = Column(String(50), default="AI_ACTIVE", nullable=False)  # AI_ACTIVE, RECRUITER_ACTIVE, PAUSED
    current_question_index = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="interviews")
    recruiter = relationship("Recruiter", back_populates="interviews")
    candidate = relationship("Candidate", back_populates="interviews")
    evaluations = relationship("CandidateEvaluation", back_populates="interview")
    recordings = relationship("InterviewRecording", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewRecording.created_at.desc()")
    consents = relationship("RecordingConsent", back_populates="interview", cascade="all, delete-orphan")
    transcripts = relationship("InterviewTranscript", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewTranscript.created_at.desc()")
    scorecards = relationship("InterviewScorecard", back_populates="interview", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="interview")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.sequence_number.asc()")
    responses = relationship("InterviewResponse", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewResponse.created_at.asc()")
    ai_evaluation = relationship("InterviewEvaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")

class CandidateEvaluation(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True)
    technical_score = Column(Float, nullable=False, default=3.0)       # 1 to 5
    communication_score = Column(Float, nullable=False, default=3.0)   # 1 to 5
    experience_score = Column(Float, nullable=False, default=3.0)      # 1 to 5
    overall_recommendation = Column(String(50), nullable=False, default="HIRE")  # STRONG_HIRE, HIRE, NEUTRAL, DO_NOT_HIRE
    interview_feedback = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="evaluations")
    recruiter = relationship("Recruiter", back_populates="evaluations")
    interview = relationship("Interview", back_populates="evaluations")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="SYSTEM")  # APPLICATION_STATUS, INTERVIEW_SCHEDULED, MESSAGE, SYSTEM
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sender_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    application = relationship("Application", back_populates="messages")

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")

    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_saved_job"),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)  # JOB_CREATE, JOB_MODERATE, STATUS_CHANGE, USER_STATUS, INTERVIEW_SCHEDULE, etc.
    target_resource = Column(String(100), nullable=False)
    target_id = Column(String(36), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    actor = relationship("User", back_populates="audit_logs")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = Column(String(50), nullable=True)

    user = relationship("User", back_populates="password_reset_tokens")

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="verification_tokens")

class CandidateTechnology(Base):
    __tablename__ = "candidate_technologies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    technology_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default="LANGUAGE")  # LANGUAGE, FRAMEWORK, DATABASE, TOOL, CLOUD
    is_resume_detected = Column(Boolean, default=True, nullable=False)
    proficiency_level = Column(String(50), default="INTERMEDIATE", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    candidate = relationship("Candidate", back_populates="technologies")

    __table_args__ = (
        UniqueConstraint("candidate_id", "technology_name", name="uq_candidate_technology"),
    )

class PracticeQuestion(Base):
    __tablename__ = "practice_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    technology = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, default="INTERMEDIATE", index=True)  # BEGINNER, INTERMEDIATE, ADVANCED
    question_type = Column(String(20), nullable=False, default="MULTIPLE_CHOICE")        # MULTIPLE_CHOICE, CONCEPTUAL, CODING
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)           # list of { key: "A", text: "..." }
    correct_answer = Column(Text, nullable=False)   # option key (e.g. "A") or reference answer
    hint = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    code_template = Column(Text, nullable=True)
    sample_test_cases = Column(JSON, nullable=True)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    batch_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    attempts = relationship("PracticeAttempt", back_populates="question", cascade="all, delete-orphan")

class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), ForeignKey("practice_questions.id", ondelete="CASCADE"), nullable=False)
    technology = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False, default="INTERMEDIATE")
    candidate_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False, nullable=False)
    explanation_viewed = Column(Boolean, default=False, nullable=False)
    hints_used = Column(Integer, default=0, nullable=False)
    attempt_count = Column(Integer, default=1, nullable=False)
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    candidate = relationship("Candidate", back_populates="practice_attempts")
    question = relationship("PracticeQuestion", back_populates="attempts")

# ==============================================================================
# First-Round MCQ Assessment System Models
# ==============================================================================

class QuestionDifficultyEnum(str, PyEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class QuestionStatusEnum(str, PyEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class AssessmentStatusEnum(str, PyEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class AssessmentAssignmentStatusEnum(str, PyEnum):
    ASSIGNED = "ASSIGNED"
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"
    PASSED = "PASSED"
    FAILED = "FAILED"

class AttemptStatusEnum(str, PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"

class AssessmentResultEnum(str, PyEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    instructions = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    total_marks = Column(Integer, nullable=False, default=0)
    passing_marks = Column(Integer, nullable=False, default=0)
    status = Column(Enum(AssessmentStatusEnum), default=AssessmentStatusEnum.DRAFT, nullable=False, index=True)
    randomize_questions = Column(Boolean, default=False, nullable=False)
    randomize_options = Column(Boolean, default=False, nullable=False)
    auto_selection_config = Column(JSON, default=dict, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("Job", back_populates="assessments")
    recruiter = relationship("Recruiter", back_populates="assessments")
    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.order_num")
    assignments = relationship("CandidateAssessmentAssignment", back_populates="assessment", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_question_id = Column(String(36), ForeignKey("question_bank_items.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    order_num = Column(Integer, nullable=False, default=1)
    marks = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assessment = relationship("Assessment", back_populates="questions")
    bank_question = relationship("QuestionBankItem")
    options = relationship("AssessmentQuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="AssessmentQuestionOption.option_key")
    answers = relationship("AssessmentCandidateAnswer", back_populates="question", cascade="all, delete-orphan")

class AssessmentQuestionOption(Base):
    __tablename__ = "assessment_question_options"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_key = Column(String(10), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)  # Confidential server-side ground truth
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    question = relationship("AssessmentQuestion", back_populates="options")
    selected_in_answers = relationship("AssessmentCandidateAnswer", back_populates="selected_option")

class CandidateAssessmentAssignment(Base):
    __tablename__ = "candidate_assessment_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(AssessmentAssignmentStatusEnum), default=AssessmentAssignmentStatusEnum.ASSIGNED, nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    deadline_at = Column(DateTime, nullable=True)

    # Recruiter review & decision fields
    review_status = Column(String(50), default="PENDING_REVIEW", nullable=False, index=True)  # PENDING_REVIEW, UNDER_REVIEW, ACCEPTED, REJECTED, ON_HOLD, MOVED_TO_INTERVIEW
    final_decision = Column(String(50), nullable=True, index=True)
    decision_reason = Column(Text, nullable=True)
    recruiter_remarks = Column(Text, nullable=True)
    candidate_message = Column(Text, nullable=True)
    reviewed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    score_adjustment = Column(Integer, default=0, nullable=False)
    score_adjustment_reason = Column(Text, nullable=True)
    adjusted_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    adjusted_at = Column(DateTime, nullable=True)
    decision_email_status = Column(String(50), default="NOT_SENT", nullable=False)  # NOT_SENT, PENDING, SENT, FAILED, NOT_APPLICABLE
    decision_email_error = Column(Text, nullable=True)
    decision_email_sent_at = Column(DateTime, nullable=True)
    brevo_message_id = Column(String(255), nullable=True)

    assessment = relationship("Assessment", back_populates="assignments")
    candidate = relationship("Candidate", back_populates="assessment_assignments")
    application = relationship("Application", back_populates="assessment_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    adjusted_by = relationship("User", foreign_keys=[adjusted_by_user_id])
    attempt = relationship("AssessmentAttempt", back_populates="assignment", uselist=False, cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="assignment", uselist=False, cascade="all, delete-orphan")
    decision_history = relationship("AssessmentDecisionHistory", back_populates="assignment", cascade="all, delete-orphan", order_by="AssessmentDecisionHistory.created_at.desc()")

    __table_args__ = (
        UniqueConstraint("assessment_id", "candidate_id", name="uq_assessment_candidate_assignment"),
    )

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("candidate_assessment_assignments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Server-calculated strict deadline
    submitted_at = Column(DateTime, nullable=True)
    status = Column(Enum(AttemptStatusEnum), default=AttemptStatusEnum.IN_PROGRESS, nullable=False, index=True)
    question_order = Column(JSON, default=list, nullable=True)
    option_orders = Column(JSON, default=dict, nullable=True)
    session_recording_asset_id = Column(String(36), ForeignKey("media_assets.id", ondelete="SET NULL", use_alter=True), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assignment = relationship("CandidateAssessmentAssignment", back_populates="attempt")
    candidate = relationship("Candidate")
    assessment = relationship("Assessment")
    answers = relationship("AssessmentCandidateAnswer", back_populates="attempt", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="attempt", uselist=False, cascade="all, delete-orphan")
    proctoring_session = relationship("ProctoringSession", back_populates="attempt", uselist=False, cascade="all, delete-orphan")
    session_recording = relationship("MediaAsset", foreign_keys=[session_recording_asset_id])

class AssessmentCandidateAnswer(Base):
    __tablename__ = "assessment_candidate_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option_id = Column(String(36), ForeignKey("assessment_question_options.id", ondelete="SET NULL"), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    marks_awarded = Column(Integer, default=0, nullable=False)
    answered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("AssessmentQuestion", back_populates="answers")
    selected_option = relationship("AssessmentQuestionOption", back_populates="selected_in_answers")

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),
    )

class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("candidate_assessment_assignments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    total_questions = Column(Integer, nullable=False, default=0)
    questions_answered = Column(Integer, nullable=False, default=0)
    correct_answers_count = Column(Integer, nullable=False, default=0)
    total_marks = Column(Integer, nullable=False, default=0)
    marks_obtained = Column(Integer, nullable=False, default=0)
    passing_marks = Column(Integer, nullable=False, default=0)
    percentage = Column(Float, nullable=False, default=0.0)
    result = Column(Enum(AssessmentResultEnum), nullable=False, index=True)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    details = Column(JSON, default=dict)
    original_marks_obtained = Column(Integer, nullable=True)
    is_score_adjusted = Column(Boolean, default=False, nullable=False)
    score_adjustment_reason = Column(Text, nullable=True)
    adjusted_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    adjusted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assignment = relationship("CandidateAssessmentAssignment", back_populates="result")
    attempt = relationship("AssessmentAttempt", back_populates="result")
    candidate = relationship("Candidate")
    assessment = relationship("Assessment", back_populates="results")
    application = relationship("Application", back_populates="assessment_results")
    adjusted_by = relationship("User", foreign_keys=[adjusted_by_user_id])

class AssessmentDecisionHistory(Base):
    """
    Immutable audit history of all recruiter review decisions and status transitions.
    """
    __tablename__ = "assessment_decision_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(String(36), ForeignKey("candidate_assessment_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    decision = Column(String(50), nullable=False)  # ACCEPTED, REJECTED, MOVED_TO_INTERVIEW, ON_HOLD, SCORE_ADJUSTED, UNDER_REVIEW
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True)
    recruiter_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    decision_reason = synonym("reason")
    remarks = Column(Text, nullable=True)
    candidate_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    decided_at = synonym("created_at")

    application = relationship("Application")
    assessment = relationship("Assessment")
    assignment = relationship("CandidateAssessmentAssignment", back_populates="decision_history")
    attempt = relationship("AssessmentAttempt")
    recruiter = relationship("Recruiter")
    recruiter_user = relationship("User", foreign_keys=[recruiter_user_id])

# ==============================================================================
# Central Question Bank Models
# ==============================================================================

class QuestionBankItem(Base):
    __tablename__ = "question_bank_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    technology = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    subtopic = Column(String(100), nullable=True)
    difficulty = Column(Enum(QuestionDifficultyEnum), default=QuestionDifficultyEnum.INTERMEDIATE, nullable=False, index=True)
    question_type = Column(String(50), default="SINGLE_CORRECT_MCQ", nullable=False)
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    marks = Column(Integer, default=1, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    is_global = Column(Boolean, default=True, nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(QuestionStatusEnum), default=QuestionStatusEnum.ACTIVE, nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    source_file = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    import_batch_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    created_by = relationship("User", back_populates="created_questions")
    options = relationship("QuestionBankOption", back_populates="question_bank_item", cascade="all, delete-orphan", order_by="QuestionBankOption.option_key")
    collection_items = relationship("QuestionCollectionItem", back_populates="question_bank_item", cascade="all, delete-orphan")

class QuestionBankOption(Base):
    __tablename__ = "question_bank_options"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_bank_id = Column(String(36), ForeignKey("question_bank_items.id", ondelete="CASCADE"), nullable=False, index=True)
    option_key = Column(String(10), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    question_bank_item = relationship("QuestionBankItem", back_populates="options")

class QuestionCollection(Base):
    __tablename__ = "question_collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    technology = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="question_collections")
    items = relationship("QuestionCollectionItem", back_populates="collection", cascade="all, delete-orphan", order_by="QuestionCollectionItem.order_num")

class QuestionCollectionItem(Base):
    __tablename__ = "question_collection_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    collection_id = Column(String(36), ForeignKey("question_collections.id", ondelete="CASCADE"), nullable=False, index=True)
    question_bank_id = Column(String(36), ForeignKey("question_bank_items.id", ondelete="CASCADE"), nullable=False, index=True)
    order_num = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    collection = relationship("QuestionCollection", back_populates="items")
    question_bank_item = relationship("QuestionBankItem", back_populates="collection_items")

    __table_args__ = (
        UniqueConstraint("collection_id", "question_bank_id", name="uq_collection_question"),
    )

class QuestionImportBatch(Base):
    __tablename__ = "question_import_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    total_extracted = Column(Integer, nullable=False, default=0)
    total_approved = Column(Integer, nullable=False, default=0)
    technology = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="import_batches")

# ==============================================================================
# Assessment Proctoring & Surveillance Models (Strict Privacy: Zero Media Stored)
# ==============================================================================

class ProctoringSessionStatusEnum(str, PyEnum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    INTERRUPTED = "INTERRUPTED"
    COMPLETED = "COMPLETED"
    FLAGGED = "FLAGGED"

class ProctoringEventTypeEnum(str, PyEnum):
    FACE_NOT_DETECTED = "FACE_NOT_DETECTED"
    MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
    TAB_SWITCH = "TAB_SWITCH"
    WINDOW_BLUR = "WINDOW_BLUR"
    CAMERA_INTERRUPTED = "CAMERA_INTERRUPTED"
    CAMERA_RESTORED = "CAMERA_RESTORED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"

class ProctoringSession(Base):
    """
    Tracks assessment proctoring telemetry per attempt.
    PRIVACY CONTRACT: Strictly stores structured numeric/metadata signals.
    Never stores or transmits video, audio, or raw photos to database or storage.
    """
    __tablename__ = "proctoring_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    camera_permission_granted = Column(Boolean, default=True, nullable=False)
    monitoring_status = Column(Enum(ProctoringSessionStatusEnum), default=ProctoringSessionStatusEnum.ACTIVE, nullable=False, index=True)
    total_warning_count = Column(Integer, default=0, nullable=False)
    tab_switch_count = Column(Integer, default=0, nullable=False)
    face_not_detected_count = Column(Integer, default=0, nullable=False)
    multiple_faces_count = Column(Integer, default=0, nullable=False)
    camera_interruption_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="proctoring_session")
    candidate = relationship("Candidate")
    assessment = relationship("Assessment")
    events = relationship("ProctoringEvent", back_populates="session", cascade="all, delete-orphan", order_by="ProctoringEvent.event_timestamp")

class ProctoringEvent(Base):
    """
    Granular audit log of monitored behavioral events during an assessment.
    """
    __tablename__ = "proctoring_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    proctoring_session_id = Column(String(36), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(Enum(ProctoringEventTypeEnum), nullable=False, index=True)
    event_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    severity = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH
    details_json = Column(JSON, default=dict, nullable=False)
    reviewed_status = Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, REVIEWED, DISMISSED
    reviewed_by_admin_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("ProctoringSession", back_populates="events")
    reviewed_by = relationship("User")

# ============================================================================
# CLOUDINARY MEDIA ASSETS & RECORDING INFRASTRUCTURE
# ============================================================================

class MediaAsset(Base):
    """
    Centralized Cloudinary media metadata storage.
    Organized into structured folder paths:
      - skillsphere/resumes/
      - skillsphere/interviews/
      - skillsphere/assessments/
      - skillsphere/candidate-responses/
      - skillsphere/interview-attachments/
    """
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    public_id = Column(String(255), nullable=False, index=True)
    asset_id = Column(String(255), nullable=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True, index=True)
    video_assessment_id = Column(String(36), ForeignKey("video_assessments.id", ondelete="SET NULL"), nullable=True, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True, index=True)
    assessment_type = Column(String(50), nullable=True, default=None)  # MCQ, VIDEO_ASSESSMENT
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="SET NULL"), nullable=True, index=True)
    question_id = Column(String(36), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False, default="video")  # video, image, raw
    file_format = Column(String(50), nullable=False, default="mp4")
    file_size_bytes = Column(Integer, default=0, nullable=False)
    video_duration_seconds = Column(Float, nullable=True)
    secure_url = Column(String(1000), nullable=False)
    playback_url = Column(String(1000), nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)
    folder = Column(String(255), nullable=False, default="skillsphere/interviews")
    upload_status = Column(String(50), nullable=False, default="COMPLETED")  # PENDING, PROCESSING, COMPLETED, FAILED
    access_classification = Column(String(50), nullable=False, default="CONFIDENTIAL")  # CONFIDENTIAL, PRIVATE, INTERNAL, PUBLIC
    retention_expires_at = Column(DateTime, nullable=True)
    uploader_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    cloudinary_public_id = synonym("public_id")
    cloudinary_asset_id = synonym("asset_id")
    duration = synonym("video_duration_seconds")
    bytes = synonym("file_size_bytes")
    format = synonym("file_format")

    candidate = relationship("Candidate", back_populates="media_assets")
    job = relationship("Job", back_populates="media_assets")
    interview = relationship("Interview", back_populates="media_assets")
    video_assessment = relationship("VideoAssessment", back_populates="media_assets")
    assessment = relationship("Assessment")
    attempt = relationship("AssessmentAttempt", foreign_keys=[attempt_id])
    uploader = relationship("User", foreign_keys=[uploader_user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
    audit_logs = relationship("MediaAuditLog", back_populates="media_asset", cascade="all, delete-orphan")


class RecordingConsent(Base):
    """
    Mandatory informed consent tracking for interview recording.
    Recordings can only initiate after explicit consent is recorded.
    """
    __tablename__ = "recording_consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # RECRUITER, JOB_SEEKER
    consent_granted = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)

    interview = relationship("Interview", back_populates="consents")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("interview_id", "user_id", name="uq_interview_user_consent"),
    )


class InterviewRecording(Base):
    """
    Tracks server-side meeting recording lifecycle, egress tasks, and Cloudinary storage.
    """
    __tablename__ = "interview_recordings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    media_asset_id = Column(String(36), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    egress_id = Column(String(255), nullable=True)
    status = Column(String(50), default="REQUESTED", nullable=False)  # REQUESTED, STARTING, RECORDING, STOPPED, UPLOADING, COMPLETED, FAILED
    recording_consent_recruiter = Column(Boolean, default=False, nullable=False)
    recording_consent_candidate = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="recordings")
    media_asset = relationship("MediaAsset")


class InterviewTranscript(Base):
    """
    Optional AI speech-to-text transcription, topic extraction, and draft feedback summary.
    Presented as editable assistant-generated drafts for recruiter review.
    """
    __tablename__ = "interview_transcripts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    full_transcript_text = Column(Text, nullable=True)
    timestamps_json = Column(JSON, default=list, nullable=False)  # [{time: "00:15", speaker: "Candidate", text: "..."}]
    ai_summary = Column(Text, nullable=True)
    technical_topics_json = Column(JSON, default=list, nullable=False)  # ["System Design", "PostgreSQL Indexing"]
    candidate_strengths_summary = Column(Text, nullable=True)
    candidate_concerns_summary = Column(Text, nullable=True)
    draft_feedback_json = Column(JSON, default=dict, nullable=False)
    is_approved_by_recruiter = Column(Boolean, default=False, nullable=False)
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="transcripts")
    approved_by = relationship("User")


class InterviewScorecard(Base):
    """
    Structured recruiter scorecard and qualitative feedback per interview round.
    """
    __tablename__ = "interview_scorecards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    technical_knowledge_score = Column(Float, default=3.0, nullable=False)  # 1 to 5
    technical_evidence_notes = Column(Text, nullable=True)
    communication_score = Column(Float, default=3.0, nullable=False)       # 1 to 5
    communication_evidence_notes = Column(Text, nullable=True)
    problem_solving_score = Column(Float, default=3.0, nullable=False)     # 1 to 5
    problem_solving_notes = Column(Text, nullable=True)
    role_specific_score = Column(Float, default=3.0, nullable=False)       # 1 to 5
    role_specific_notes = Column(Text, nullable=True)
    cultural_alignment_score = Column(Float, default=3.0, nullable=False)   # 1 to 5
    cultural_alignment_notes = Column(Text, nullable=True)
    overall_score = Column(Float, default=3.0, nullable=False)
    overall_recommendation = Column(String(50), default="RECOMMENDED", nullable=False)  # RECOMMENDED, NOT_RECOMMENDED, UNDER_REVIEW, ADDITIONAL_INTERVIEW_REQUIRED
    strengths = Column(Text, nullable=True)
    improvement_areas = Column(Text, nullable=True)
    private_evaluation_notes = Column(Text, nullable=True)
    is_submitted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="scorecards")
    recruiter = relationship("Recruiter", back_populates="interview_scorecards")
    application = relationship("Application", back_populates="scorecards")


class InterviewQuestion(Base):
    """
    Questions prepared or AI-generated for an interview (AI, Hybrid, or Configured).
    """
    __tablename__ = "interview_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="TECHNICAL", nullable=False)  # TECHNICAL, BEHAVIORAL, PROBLEM_SOLVING, ROLE_SPECIFIC, SITUATIONAL
    source = Column(String(50), default="CUSTOM", nullable=False)  # CUSTOM, AI_GENERATED
    sequence_number = Column(Integer, default=1, nullable=False)
    expected_concepts = Column(JSON, default=list, nullable=False)
    max_duration_seconds = Column(Integer, default=180, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="questions")
    responses = relationship("InterviewResponse", back_populates="question", cascade="all, delete-orphan")


class InterviewResponse(Base):
    """
    Candidate response and real-time evaluation per question in an AI/Hybrid interview.
    """
    __tablename__ = "interview_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    transcript = Column(Text, nullable=True)
    response_duration = Column(Float, default=0.0, nullable=False)
    evaluation = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    score = Column(Float, default=3.0, nullable=False)  # 1.0 to 5.0
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="responses")
    question = relationship("InterviewQuestion", back_populates="responses")


class InterviewEvaluation(Base):
    """
    Structured overall AI interview evaluation with recruiter review/override status.
    """
    __tablename__ = "interview_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    overall_summary = Column(Text, nullable=True)
    overall_score = Column(Float, default=3.0, nullable=False)
    competency_scores = Column(JSON, default=dict, nullable=False)  # {"technical": 4.0, "communication": 3.5, ...}
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_status = Column(String(50), default="PENDING_REVIEW", nullable=False)  # PENDING_REVIEW, ACCEPTED, OVERRIDDEN
    recruiter_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    interview = relationship("Interview", back_populates="ai_evaluation")
    reviewer = relationship("User")


# ============================================================================
# VIDEO ASSESSMENT CAPABILITY (COEXISTS WITH MCQ ASSESSMENTS)
# ============================================================================

class VideoAssessment(Base):
    """
    Asynchronous video assessment with structured timed video response questions.
    """
    __tablename__ = "video_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    total_questions = Column(Integer, default=1, nullable=False)
    submission_deadline = Column(DateTime, nullable=True)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)  # DRAFT, PUBLISHED, ARCHIVED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("Job", back_populates="video_assessments")
    recruiter = relationship("Recruiter", back_populates="video_assessments")
    questions = relationship("VideoAssessmentQuestion", back_populates="video_assessment", cascade="all, delete-orphan", order_by="VideoAssessmentQuestion.order_num")
    assignments = relationship("CandidateVideoAssignment", back_populates="video_assessment", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="video_assessment")


class VideoAssessmentQuestion(Base):
    """
    Individual video response prompt with max recording duration and retake allowances.
    """
    __tablename__ = "video_assessment_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_assessment_id = Column(String(36), ForeignKey("video_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    order_num = Column(Integer, default=1, nullable=False)
    question_text = Column(Text, nullable=False)
    question_instructions = Column(Text, nullable=True)
    max_duration_seconds = Column(Integer, default=120, nullable=False)  # e.g. 2 minutes max
    prep_time_seconds = Column(Integer, default=30, nullable=False)      # e.g. 30s prep countdown
    retake_limit = Column(Integer, default=2, nullable=False)            # e.g. max 2 retakes
    is_required = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    video_assessment = relationship("VideoAssessment", back_populates="questions")
    responses = relationship("CandidateVideoResponse", back_populates="question", cascade="all, delete-orphan")


class CandidateVideoAssignment(Base):
    """
    Assignment of a video assessment to a shortlisted candidate.
    """
    __tablename__ = "candidate_video_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_assessment_id = Column(String(36), ForeignKey("video_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="ASSIGNED", nullable=False, index=True)  # ASSIGNED, IN_PROGRESS, SUBMITTED, REVIEWED
    review_status = Column(String(50), default="PENDING_REVIEW", nullable=False, index=True)  # PENDING_REVIEW, UNDER_REVIEW, ACCEPTED, REJECTED
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    recruiter_feedback = Column(Text, nullable=True)
    overall_score = Column(Float, nullable=True)

    video_assessment = relationship("VideoAssessment", back_populates="assignments")
    candidate = relationship("Candidate", back_populates="video_assignments")
    application = relationship("Application", back_populates="video_assignments")
    responses = relationship("CandidateVideoResponse", back_populates="assignment", cascade="all, delete-orphan")


class CandidateVideoResponse(Base):
    """
    Submitted video recording response for a specific question, linked to Cloudinary media.
    """
    __tablename__ = "candidate_video_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("candidate_video_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("video_assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    media_asset_id = Column(String(36), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    retake_count = Column(Integer, default=0, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    recruiter_rating = Column(Float, nullable=True)
    recruiter_notes = Column(Text, nullable=True)

    assignment = relationship("CandidateVideoAssignment", back_populates="responses")
    question = relationship("VideoAssessmentQuestion", back_populates="responses")
    media_asset = relationship("MediaAsset")


class MediaAuditLog(Base):
    """
    Security audit trail for media access, signed URL generation, playback, and deletion.
    """
    __tablename__ = "media_audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    media_asset_id = Column(String(36), ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # PLAY, DOWNLOAD, DELETE, TRANSCRIPT_GENERATE
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    media_asset = relationship("MediaAsset", back_populates="audit_logs")
    actor = relationship("User")
