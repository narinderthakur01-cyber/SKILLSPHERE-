import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    Assessment, AssessmentQuestion, AssessmentQuestionOption,
    CandidateAssessmentAssignment, AssessmentAttempt, AssessmentCandidateAnswer,
    AssessmentResult, AssessmentStatusEnum, AssessmentAssignmentStatusEnum,
    AttemptStatusEnum, AssessmentResultEnum, Job, Application,
    ApplicationStatusEnum, ApplicationHistory, Candidate, Recruiter, User,
    QuestionBankItem, AssessmentDecisionHistory, ProctoringSession, ProctoringEvent,
    MediaAsset
)
from app.schemas.schemas import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentQuestionResponse, AssessmentOptionResponse,
    CandidateAssignmentResponse, ShortlistedCandidateItem,
    AttemptStatusResponse, CandidateResultResponse,
    RecruiterCandidateReviewResponse, RecruiterCandidateAnswerItem,
    CandidateSubmissionConfirmationResponse, CandidateAssessmentStatusResponse,
    RecruiterAssessmentReviewItem, RecruiterDetailedAnswerItem,
    RecruiterDetailedReviewResponse, DecisionHistoryItemResponse,
    RecruiterDecisionResponse, AssessmentComparisonResponse,
    AssessmentAnalyticsOverview, CandidateComparisonItem
)
from app.services.activity_service import create_notification, create_audit_log
from app.services.email_service import EmailService

class AssessmentService:

    @staticmethod
    def validate_assessment_questions(questions_data: List[Any], duration_minutes: int, passing_marks: int) -> Tuple[int, str]:
        """Validate MCQ assessment rules: options 2-5, exactly 1 correct answer, marks > 0, passing <= total."""
        if duration_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment duration must be greater than 0 minutes."
            )
        if not questions_data or len(questions_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment must contain at least one question."
            )

        calculated_total = 0
        for idx, q in enumerate(questions_data):
            q_text = getattr(q, "question_text", None) or (q.get("question_text") if isinstance(q, dict) else "")
            if not q_text or not q_text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question #{idx+1} cannot have empty text."
                )

            marks = getattr(q, "marks", None) if hasattr(q, "marks") else (q.get("marks") if isinstance(q, dict) else 1)
            if marks is None or marks < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question #{idx+1} must award at least 1 mark."
                )
            calculated_total += marks

            options = getattr(q, "options", None) or (q.get("options") if isinstance(q, dict) else [])
            if not options or len(options) < 2 or len(options) > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question #{idx+1} must have between 2 and 5 options."
                )

            correct_count = 0
            for opt in options:
                is_corr = getattr(opt, "is_correct", False) if hasattr(opt, "is_correct") else bool(opt.get("is_correct") if isinstance(opt, dict) else False)
                if is_corr:
                    correct_count += 1

            if correct_count != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question #{idx+1} must have exactly one correct answer (found {correct_count})."
                )

        if passing_marks > calculated_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Passing marks ({passing_marks}) cannot exceed total marks ({calculated_total})."
            )
        if passing_marks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passing marks must be greater than 0."
            )

        return calculated_total, ""

    @classmethod
    def create_assessment(cls, db: Session, recruiter: Recruiter, data: AssessmentCreate) -> Assessment:
        # Check job ownership
        job = db.query(Job).filter(Job.id == data.job_id).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        if job.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this job posting.")

        total_marks, _ = cls.validate_assessment_questions(data.questions, data.duration_minutes, data.passing_marks)

        assessment = Assessment(
            job_id=job.id,
            recruiter_id=recruiter.id,
            title=data.title.strip(),
            instructions=data.instructions.strip() if data.instructions else None,
            duration_minutes=data.duration_minutes,
            total_marks=total_marks,
            passing_marks=data.passing_marks,
            randomize_questions=data.randomize_questions,
            randomize_options=data.randomize_options,
            auto_selection_config=data.auto_selection_config,
            version=1,
            status=AssessmentStatusEnum.DRAFT
        )
        db.add(assessment)
        db.flush()

        for idx, q_data in enumerate(data.questions):
            bank_qid = getattr(q_data, "bank_question_id", None)
            explanation = getattr(q_data, "explanation", None)
            question = AssessmentQuestion(
                assessment_id=assessment.id,
                bank_question_id=bank_qid,
                question_text=q_data.question_text.strip(),
                explanation=explanation.strip() if explanation else None,
                order_num=idx + 1,
                marks=q_data.marks
            )
            db.add(question)
            db.flush()

            if bank_qid:
                db.query(QuestionBankItem).filter(
                    QuestionBankItem.id == bank_qid
                ).update({QuestionBankItem.usage_count: QuestionBankItem.usage_count + 1})

            for opt_data in q_data.options:
                opt = AssessmentQuestionOption(
                    question_id=question.id,
                    option_key=opt_data.option_key.strip().upper(),
                    option_text=opt_data.option_text.strip(),
                    is_correct=opt_data.is_correct
                )
                db.add(opt)

        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def update_draft_assessment(cls, db: Session, recruiter: Recruiter, assessment_id: str, data: AssessmentUpdate) -> Assessment:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        if assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this assessment.")
        # Invariant: Lock structural changes if candidate attempts have already started
        attempts_count = db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == assessment.id).count()
        if attempts_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify assessment: candidate attempts have already started. Create a new version instead."
            )

        if assessment.status != AssessmentStatusEnum.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only DRAFT assessments can be modified.")

        if data.title is not None:
            assessment.title = data.title.strip()
        if data.instructions is not None:
            assessment.instructions = data.instructions.strip()
        if data.duration_minutes is not None:
            assessment.duration_minutes = data.duration_minutes
        if data.passing_marks is not None:
            assessment.passing_marks = data.passing_marks
        if data.randomize_questions is not None:
            assessment.randomize_questions = data.randomize_questions
        if data.randomize_options is not None:
            assessment.randomize_options = data.randomize_options
        if data.auto_selection_config is not None:
            assessment.auto_selection_config = data.auto_selection_config

        if data.questions is not None:
            total_marks, _ = cls.validate_assessment_questions(data.questions, assessment.duration_minutes, assessment.passing_marks)
            assessment.total_marks = total_marks

            # Replace questions and options safely
            existing_questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
            q_ids = [q.id for q in existing_questions]
            if q_ids:
                db.query(AssessmentQuestionOption).filter(AssessmentQuestionOption.question_id.in_(q_ids)).delete(synchronize_session=False)
            db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).delete(synchronize_session=False)
            db.flush()

            for idx, q_data in enumerate(data.questions):
                bank_qid = getattr(q_data, "bank_question_id", None)
                explanation = getattr(q_data, "explanation", None)
                question = AssessmentQuestion(
                    assessment_id=assessment.id,
                    bank_question_id=bank_qid,
                    question_text=q_data.question_text.strip(),
                    explanation=explanation.strip() if explanation else None,
                    order_num=idx + 1,
                    marks=q_data.marks
                )
                db.add(question)
                db.flush()

                if bank_qid:
                    db.query(QuestionBankItem).filter(
                        QuestionBankItem.id == bank_qid
                    ).update({QuestionBankItem.usage_count: QuestionBankItem.usage_count + 1})

                for opt_data in q_data.options:
                    opt = AssessmentQuestionOption(
                        question_id=question.id,
                        option_key=opt_data.option_key.strip().upper(),
                        option_text=opt_data.option_text.strip(),
                        is_correct=opt_data.is_correct
                    )
                    db.add(opt)

            assessment.version = (assessment.version or 1) + 1

        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def publish_assessment(cls, db: Session, recruiter: Recruiter, assessment_id: str) -> Assessment:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        if assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this assessment.")
        if assessment.status == AssessmentStatusEnum.PUBLISHED:
            return assessment

        # Re-validate before publication
        questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
        if not questions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An assessment cannot be published without questions.")

        q_dicts = []
        for q in questions:
            opts = db.query(AssessmentQuestionOption).filter(AssessmentQuestionOption.question_id == q.id).all()
            q_dicts.append({
                "question_text": q.question_text,
                "marks": q.marks,
                "options": [{"is_correct": o.is_correct} for o in opts]
            })

        total_marks, _ = cls.validate_assessment_questions(q_dicts, assessment.duration_minutes, assessment.passing_marks)
        assessment.total_marks = total_marks
        assessment.status = AssessmentStatusEnum.PUBLISHED
        assessment.published_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def get_shortlisted_candidates_for_job(cls, db: Session, recruiter: Recruiter, assessment_id: str) -> List[ShortlistedCandidateItem]:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        if assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        # Find applications for this job that have status SHORTLISTED
        applications = db.query(Application).filter(
            Application.job_id == assessment.job_id,
            Application.status == ApplicationStatusEnum.SHORTLISTED
        ).all()

        results = []
        for app in applications:
            cand = app.candidate
            if not cand or not cand.user:
                continue

            assignment = db.query(CandidateAssessmentAssignment).filter(
                CandidateAssessmentAssignment.assessment_id == assessment.id,
                CandidateAssessmentAssignment.candidate_id == cand.id
            ).first()

            results.append(ShortlistedCandidateItem(
                candidate_id=cand.id,
                candidate_name=cand.user.name,
                candidate_email=cand.user.email,
                application_id=app.id,
                application_status=app.status.value,
                is_assigned=assignment is not None,
                assignment_id=assignment.id if assignment else None,
                assignment_status=assignment.status.value if assignment else None
            ))

        return results

    @classmethod
    def assign_to_candidates(
        cls,
        db: Session,
        recruiter: Recruiter,
        assessment_id: str,
        candidate_ids: List[str],
        deadline_at: Optional[datetime] = None
    ) -> List[CandidateAssessmentAssignment]:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        if assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
        if assessment.status != AssessmentStatusEnum.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment must be PUBLISHED before it can be assigned.")

        assigned_records = []
        for cand_id in candidate_ids:
            # Check candidate application is SHORTLISTED for this job
            app = db.query(Application).filter(
                Application.job_id == assessment.job_id,
                Application.candidate_id == cand_id,
                Application.status == ApplicationStatusEnum.SHORTLISTED
            ).first()

            if not app:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Candidate {cand_id} does not have a SHORTLISTED application for this job."
                )

            # Prevent duplicate assignments
            existing = db.query(CandidateAssessmentAssignment).filter(
                CandidateAssessmentAssignment.assessment_id == assessment.id,
                CandidateAssessmentAssignment.candidate_id == cand_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Candidate {cand_id} has already been assigned this assessment."
                )

            assignment = CandidateAssessmentAssignment(
                assessment_id=assessment.id,
                candidate_id=cand_id,
                application_id=app.id,
                assigned_by_user_id=recruiter.user_id,
                status=AssessmentAssignmentStatusEnum.ASSIGNED,
                deadline_at=deadline_at
            )
            db.add(assignment)
            db.flush()
            assigned_records.append(assignment)

            # Send in-app notification to candidate
            cand = db.query(Candidate).filter(Candidate.id == cand_id).first()
            if cand and cand.user_id:
                create_notification(
                    db=db,
                    user_id=cand.user_id,
                    title="First-Round Assessment Assigned",
                    message="You have been selected for the next round. Your First-Round MCQ Assessment is ready. Complete it within the given time limit.",
                    notification_type="ASSESSMENT",
                    link="/dashboard?tab=assessments"
                )

        db.commit()
        return assigned_records

    @classmethod
    def get_candidate_instructions(cls, db: Session, candidate: Candidate, assignment_id: str) -> Dict[str, Any]:
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
        if assignment.candidate_id != candidate.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: This assessment is not assigned to you.")

        assessment = assignment.assessment
        if not assessment or assessment.status != AssessmentStatusEnum.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This assessment is not published or is currently unavailable.")
        job = assessment.job if assessment else None
        q_count = len(assessment.questions) if assessment else 0

        return {
            "assignment_id": assignment.id,
            "assessment_id": assessment.id,
            "title": assessment.title,
            "job_title": job.title if job else "N/A",
            "instructions": assessment.instructions,
            "duration_minutes": assessment.duration_minutes,
            "question_count": q_count,
            "total_marks": assessment.total_marks,
            "passing_marks": assessment.passing_marks,
            "status": assignment.status.value
        }

    @classmethod
    def start_or_resume_attempt(cls, db: Session, candidate: Candidate, assignment_id: str) -> AttemptStatusResponse:
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
        if assignment.candidate_id != candidate.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: This assessment is not assigned to you.")

        assessment = assignment.assessment
        if not assessment or assessment.status != AssessmentStatusEnum.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This assessment is not published or is currently unavailable.")
        now = datetime.now(timezone.utc)

        # Look for existing attempt
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.assignment_id == assignment.id).first()

        if attempt:
            # Check if permanently finalized
            if attempt.status in [AttemptStatusEnum.SUBMITTED, AttemptStatusEnum.EXPIRED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This assessment attempt has already been finalized and cannot be retaken."
                )

            # Check if time expired
            expires_at = attempt.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if now >= expires_at:
                # Auto-finalize expired attempt!
                cls.auto_finalize_attempt(db, attempt.id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assessment time limit has expired and answers have been automatically submitted."
                )

            # Resume in-progress attempt
            remaining_seconds = max(0, int((expires_at - now).total_seconds()))
        else:
            # First attempt: enforce single attempt policy
            # Calculate strict server-side deadline
            expires_at = now + timedelta(minutes=assessment.duration_minutes)

            # Determine randomized or natural question order
            all_questions = sorted(assessment.questions, key=lambda x: x.order_num)
            question_ids = [q.id for q in all_questions]
            if assessment.randomize_questions:
                import random
                random.shuffle(question_ids)

            # Determine randomized or natural option orders
            option_orders = {}
            for q in all_questions:
                opts = sorted(q.options, key=lambda x: x.option_key)
                opt_ids = [o.id for o in opts]
                if assessment.randomize_options:
                    import random
                    random.shuffle(opt_ids)
                option_orders[q.id] = opt_ids

            attempt = AssessmentAttempt(
                assignment_id=assignment.id,
                candidate_id=candidate.id,
                assessment_id=assessment.id,
                started_at=now,
                expires_at=expires_at,
                status=AttemptStatusEnum.IN_PROGRESS,
                question_order=question_ids,
                option_orders=option_orders
            )
            assignment.status = AssessmentAssignmentStatusEnum.STARTED
            db.add(attempt)
            db.commit()
            db.refresh(attempt)
            remaining_seconds = assessment.duration_minutes * 60

        # Load saved answers
        saved_records = db.query(AssessmentCandidateAnswer).filter(
            AssessmentCandidateAnswer.attempt_id == attempt.id
        ).all()
        saved_dict = {
            a.question_id: a.selected_option_id for a in saved_records if a.selected_option_id
        }

        # Build lookup for questions and options
        q_map = {q.id: q for q in assessment.questions}

        # Determine sequence of questions based on stored order
        if attempt.question_order:
            ordered_q_ids = [qid for qid in attempt.question_order if qid in q_map]
            for qid in q_map:
                if qid not in ordered_q_ids:
                    ordered_q_ids.append(qid)
        else:
            ordered_q_ids = [q.id for q in sorted(assessment.questions, key=lambda x: x.order_num)]

        q_responses = []
        option_letters = ["A", "B", "C", "D", "E"]
        for display_idx, q_id in enumerate(ordered_q_ids):
            q = q_map[q_id]
            opts_map = {o.id: o for o in q.options}

            # Determine option order for this question based on stored order
            saved_opt_order = (attempt.option_orders or {}).get(q_id, [])
            if saved_opt_order:
                ordered_opt_ids = [oid for oid in saved_opt_order if oid in opts_map]
                for oid in opts_map:
                    if oid not in ordered_opt_ids:
                        ordered_opt_ids.append(oid)
            else:
                ordered_opt_ids = [o.id for o in sorted(q.options, key=lambda x: x.option_key)]

            opt_responses = []
            for opt_idx, oid in enumerate(ordered_opt_ids):
                opt = opts_map[oid]
                display_key = option_letters[opt_idx] if opt_idx < len(option_letters) else f"OPT_{opt_idx+1}"
                opt_responses.append(AssessmentOptionResponse(
                    id=opt.id,
                    option_key=display_key,
                    option_text=opt.option_text,
                    is_correct=None  # STRIPPED: Confidential
                ))

            q_responses.append(AssessmentQuestionResponse(
                id=q.id,
                bank_question_id=q.bank_question_id,
                question_text=q.question_text,
                explanation=None,  # Confidential during candidate attempt
                order_num=display_idx + 1,
                marks=q.marks,
                options=opt_responses
            ))

        return AttemptStatusResponse(
            attempt_id=attempt.id,
            assignment_id=assignment.id,
            status=attempt.status.value,
            started_at=attempt.started_at,
            expires_at=attempt.expires_at,
            remaining_seconds=remaining_seconds,
            total_questions=len(q_responses),
            saved_answers=saved_dict,
            questions=q_responses
        )

    @classmethod
    def save_candidate_answers(
        cls,
        db: Session,
        candidate: Candidate,
        attempt_id: str,
        answers_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")
        if attempt.candidate_id != candidate.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this attempt.")
        if attempt.status != AttemptStatusEnum.IN_PROGRESS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt is already finalized.")

        now = datetime.now(timezone.utc)
        expires_at = attempt.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now >= expires_at:
            cls.auto_finalize_attempt(db, attempt.id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test time expired. Submission finalized.")

        for item in answers_data:
            q_id = item.get("question_id")
            opt_id = item.get("selected_option_id")
            if not q_id:
                continue

            existing_ans = db.query(AssessmentCandidateAnswer).filter(
                AssessmentCandidateAnswer.attempt_id == attempt.id,
                AssessmentCandidateAnswer.question_id == q_id
            ).first()

            if existing_ans:
                existing_ans.selected_option_id = opt_id
                existing_ans.answered_at = now
            else:
                new_ans = AssessmentCandidateAnswer(
                    attempt_id=attempt.id,
                    question_id=q_id,
                    selected_option_id=opt_id,
                    answered_at=now
                )
                db.add(new_ans)

        db.commit()
        return {"status": "saved", "count": len(answers_data)}

    @classmethod
    def evaluate_and_submit(
        cls,
        db: Session,
        candidate: Candidate,
        attempt_id: str,
        is_auto_timeout: bool = False
    ) -> CandidateSubmissionConfirmationResponse:
        """
        Finalize and submit the assessment attempt.
        Calculates and stores private assessment scores for recruiter review.
        Enforces candidate privacy: NEVER leaks scores, percentage, pass/fail, or answer keys.
        Assessment enters PENDING_REVIEW; hiring decision is solely made by recruiter.
        """
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")
        if attempt.candidate_id != candidate.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this attempt.")

        assessment = attempt.assessment
        assignment = attempt.assignment
        application = assignment.application
        job = application.job if application else (assessment.job if assessment else None)

        confirmation_text = (
            "Thank you for completing your assessment!\n\n"
            "Your responses have been successfully submitted and your assessment is now under review.\n\n"
            "The recruitment team will evaluate your performance and notify you about the next stage of the recruitment process.\n\n"
            "Your assessment activity may be reviewed according to the monitoring policy explained before the assessment.\n\n"
            "You can safely leave this page. Your submission has been recorded."
        )

        # Idempotency: check if attempt was already submitted
        existing_result = db.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()
        if existing_result:
            return CandidateSubmissionConfirmationResponse(
                assignment_id=assignment.id,
                attempt_id=attempt.id,
                assessment_title=assessment.title if assessment else "Assessment",
                job_title=job.title if job else "Position",
                status="SUBMITTED",
                submission_status="PENDING_REVIEW",
                review_status=assignment.review_status or "PENDING_REVIEW",
                submitted_at=existing_result.completed_at,
                total_questions=existing_result.total_questions,
                questions_answered=existing_result.questions_answered,
                message=confirmation_text,
                candidate_message=assignment.candidate_message
            )

        now = datetime.now(timezone.utc)

        # Calculate scores privately on the backend
        questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
        answers = db.query(AssessmentCandidateAnswer).filter(AssessmentCandidateAnswer.attempt_id == attempt.id).all()
        answer_map = {a.question_id: a for a in answers}

        total_marks = assessment.total_marks if (assessment.total_marks and assessment.total_marks > 0) else sum(q.marks for q in questions)
        marks_obtained = 0
        correct_count = 0
        answered_count = 0

        for q in questions:
            ans = answer_map.get(q.id)
            if ans and ans.selected_option_id:
                answered_count += 1
                opt = db.query(AssessmentQuestionOption).filter(AssessmentQuestionOption.id == ans.selected_option_id).first()
                if opt and opt.is_correct:
                    ans.is_correct = True
                    ans.marks_awarded = q.marks
                    marks_obtained += q.marks
                    correct_count += 1
                else:
                    ans.is_correct = False
                    ans.marks_awarded = 0
            else:
                if ans:
                    ans.is_correct = False
                    ans.marks_awarded = 0

        percentage = round((marks_obtained / total_marks * 100.0), 2) if total_marks > 0 else 0.0
        is_passed = marks_obtained >= assessment.passing_marks
        result_enum = AssessmentResultEnum.PASSED if is_passed else AssessmentResultEnum.FAILED

        # Update attempt
        attempt.status = AttemptStatusEnum.EXPIRED if is_auto_timeout else AttemptStatusEnum.SUBMITTED
        attempt.submitted_at = now

        # Update assignment status to SUBMITTED and review_status to PENDING_REVIEW
        assignment.status = AssessmentAssignmentStatusEnum.SUBMITTED
        assignment.review_status = "PENDING_REVIEW"

        # Record private assessment result
        res = AssessmentResult(
            assignment_id=assignment.id,
            attempt_id=attempt.id,
            candidate_id=candidate.id,
            assessment_id=assessment.id,
            application_id=application.id,
            total_questions=len(questions),
            questions_answered=answered_count,
            correct_answers_count=correct_count,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            original_marks_obtained=marks_obtained,
            passing_marks=assessment.passing_marks,
            percentage=percentage,
            result=result_enum,
            is_score_adjusted=False,
            completed_at=now,
            details={
                "auto_timeout": is_auto_timeout,
                "passing_marks": assessment.passing_marks,
                "duration_minutes": assessment.duration_minutes
            }
        )
        db.add(res)

        # Record application history WITHOUT automatically advancing application status
        hist = ApplicationHistory(
            application_id=application.id,
            from_status=application.status.value,
            to_status=application.status.value,
            changed_by_user_id=candidate.user_id,
            notes=f"Completed First-Round Assessment '{assessment.title}'. Assessment status is now PENDING REVIEW by hiring team."
        )
        db.add(hist)

        # In-app notification for candidate (Zero Score Exposure)
        create_notification(
            db=db,
            user_id=candidate.user_id,
            title="First-Round Assessment Submitted",
            message=f"Your responses for '{assessment.title}' have been successfully recorded and are now under review by the hiring team.",
            notification_type="ASSESSMENT",
            link="/dashboard?tab=assessments"
        )

        # In-app notification for recruiter
        recruiter = assessment.recruiter
        if recruiter and recruiter.user_id:
            cand_user = candidate.user
            cand_name = cand_user.name if cand_user else "Candidate"
            create_notification(
                db=db,
                user_id=recruiter.user_id,
                title=f"Assessment Submitted for Review: {cand_name}",
                message=f"{cand_name} submitted '{assessment.title}' ({answered_count}/{len(questions)} answered). Pending your review.",
                notification_type="ASSESSMENT",
                link="/recruiter?tab=assessments"
            )

        db.commit()
        db.refresh(res)

        return CandidateSubmissionConfirmationResponse(
            assignment_id=assignment.id,
            attempt_id=attempt.id,
            assessment_title=assessment.title,
            job_title=job.title if job else "Position",
            status="SUBMITTED",
            submission_status="PENDING_REVIEW",
            review_status=assignment.review_status,
            submitted_at=now,
            total_questions=len(questions),
            questions_answered=answered_count,
            message=confirmation_text,
            candidate_message=assignment.candidate_message
        )

    @classmethod
    def get_candidate_status(cls, db: Session, candidate: Candidate, assignment_id: str) -> CandidateAssessmentStatusResponse:
        """
        Candidate-facing assessment status and feedback endpoint.
        Strictly preserves result privacy: reveals NO marks, percentages, or answer keys.
        Surfaces recruiter decision messages once a hiring determination has been made.
        """
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
        if assignment.candidate_id != candidate.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Not assigned to you.")

        assessment = assignment.assessment
        app = assignment.application
        job = app.job if app else (assessment.job if assessment else None)
        attempt = assignment.attempt

        # Check genuine completion status before returning completed state
        is_submitted = (
            assignment.status in [
                AssessmentAssignmentStatusEnum.SUBMITTED,
                AssessmentAssignmentStatusEnum.PASSED,
                AssessmentAssignmentStatusEnum.FAILED,
                AssessmentAssignmentStatusEnum.EXPIRED
            ]
            or (attempt is not None and attempt.status in [
                AttemptStatusEnum.SUBMITTED,
                AttemptStatusEnum.EVALUATED,
                AttemptStatusEnum.EXPIRED
            ])
        )
        if not is_submitted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment has not been completed or submitted yet."
            )

        submitted_at = attempt.submitted_at if attempt else None
        review_status = assignment.review_status or "PENDING_REVIEW"

        # Standardized candidate-facing message based on recruiter decision
        if review_status == "ACCEPTED":
            message = "Congratulations! Your assessment has been reviewed, and you have been shortlisted for the next stage. The recruitment team will share the next steps shortly."
        elif review_status == "REJECTED":
            message = "Thank you for participating in the assessment. After reviewing your application and assessment, the recruitment team has decided not to proceed with your application at this stage. We appreciate your time and interest."
        elif review_status == "MOVED_TO_INTERVIEW":
            message = "You have successfully progressed to the interview stage. Please check your email and dashboard for further details."
        elif review_status == "ON_HOLD":
            message = "Your assessment is currently under review. We will notify you when there is an update."
        else:
            message = (
                "Thank you for completing your assessment! "
                "Your responses have been successfully submitted and your assessment is now under review. "
                "The recruitment team will evaluate your performance and notify you about the next stage of the recruitment process."
            )

        return CandidateAssessmentStatusResponse(
            assignment_id=assignment.id,
            assessment_title=assessment.title if assessment else "Assessment",
            job_title=job.title if job else "Position",
            review_status=review_status,
            submitted_at=submitted_at,
            message=message,
            candidate_message=assignment.candidate_message,
            application_status=app.status.value if app else None
        )

    @classmethod
    def auto_finalize_attempt(cls, db: Session, attempt_id: str) -> None:
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
        if not attempt or attempt.status in [AttemptStatusEnum.SUBMITTED, AttemptStatusEnum.EXPIRED]:
            return
        candidate = attempt.candidate
        if candidate:
            try:
                cls.evaluate_and_submit(db, candidate, attempt.id, is_auto_timeout=True)
            except Exception as e:
                db.rollback()
                print(f"[ASSESSMENT AUTO-FINALIZE ERROR]: {e}", flush=True)

    @classmethod
    def _format_time_taken(cls, seconds: Optional[int]) -> Optional[str]:
        if seconds is None or seconds < 0:
            return None
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s" if m > 0 else f"{s}s"

    @classmethod
    def list_recruiter_assessment_reviews(
        cls,
        db: Session,
        recruiter: Recruiter,
        assessment_id: Optional[str] = None,
        job_id: Optional[str] = None,
        review_status: Optional[str] = None,
        search: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: Optional[str] = "submitted_at",
        sort_order: Optional[str] = "desc"
    ) -> List[RecruiterAssessmentReviewItem]:
        """
        List candidate submitted assessments for recruiter review with full metrics,
        proctoring telemetry, score breakdowns, search, and filtering.
        """
        query = db.query(CandidateAssessmentAssignment).join(
            Assessment, CandidateAssessmentAssignment.assessment_id == Assessment.id
        ).filter(Assessment.recruiter_id == recruiter.id)

        if assessment_id:
            query = query.filter(CandidateAssessmentAssignment.assessment_id == assessment_id)
        if job_id:
            query = query.filter(Assessment.job_id == job_id)
        if review_status and review_status.upper() != "ALL":
            query = query.filter(CandidateAssessmentAssignment.review_status == review_status.upper())

        assignments = query.all()
        results: List[RecruiterAssessmentReviewItem] = []

        for asgn in assignments:
            attempt = asgn.attempt
            res = asgn.result
            cand = asgn.candidate
            cand_user = cand.user if cand else None
            app = asgn.application
            job = app.job if app else (asgn.assessment.job if asgn.assessment else None)

            # Search filter (name, email)
            if search and search.strip():
                s = search.strip().lower()
                c_name = (cand_user.name if cand_user else "").lower()
                c_email = (cand_user.email if cand_user else "").lower()
                if s not in c_name and s not in c_email:
                    continue

            # Time taken calculation
            time_taken_sec = None
            if attempt and attempt.started_at and attempt.submitted_at:
                start = attempt.started_at.replace(tzinfo=timezone.utc) if attempt.started_at.tzinfo is None else attempt.started_at
                end = attempt.submitted_at.replace(tzinfo=timezone.utc) if attempt.submitted_at.tzinfo is None else attempt.submitted_at
                time_taken_sec = max(0, int((end - start).total_seconds()))

            # Proctoring warnings count
            warning_count = 0
            if attempt:
                proctor_session = db.query(ProctoringSession).filter(
                    ProctoringSession.assessment_attempt_id == attempt.id
                ).first()
                if proctor_session:
                    warning_count = proctor_session.total_warning_count

            # Review and decision fields
            total_marks = res.total_marks if res else asgn.assessment.total_marks
            marks_obtained = res.marks_obtained if res else 0
            passing_marks = res.passing_marks if res else asgn.assessment.passing_marks
            percentage = res.percentage if res else 0.0

            # Score range filters
            if min_score is not None and marks_obtained < min_score:
                continue
            if max_score is not None and marks_obtained > max_score:
                continue

            total_q = res.total_questions if res else len(asgn.assessment.questions)
            answered_q = res.questions_answered if res else 0
            correct_q = res.correct_answers_count if res else 0
            incorrect_q = max(0, answered_q - correct_q)
            unanswered_q = max(0, total_q - answered_q)

            internal_outcome = "MET_THRESHOLD" if marks_obtained >= passing_marks else "BELOW_THRESHOLD"
            if not asgn.attempt or asgn.attempt.status == AttemptStatusEnum.IN_PROGRESS:
                internal_outcome = "IN_PROGRESS"

            reviewed_by_user = db.query(User).filter(User.id == asgn.reviewed_by_user_id).first() if asgn.reviewed_by_user_id else None

            item = RecruiterAssessmentReviewItem(
                assignment_id=asgn.id,
                attempt_id=attempt.id if attempt else None,
                candidate_id=cand.id if cand else "",
                candidate_name=cand_user.name if cand_user else "Candidate",
                candidate_email=cand_user.email if cand_user else "",
                candidate_phone=cand.phone if cand else None,
                candidate_title=cand.title if cand else None,
                job_id=job.id if job else "",
                job_title=job.title if job else "",
                assessment_id=asgn.assessment_id,
                assessment_title=asgn.assessment.title if asgn.assessment else "",
                assigned_at=asgn.assigned_at,
                started_at=attempt.started_at if attempt else None,
                submitted_at=attempt.submitted_at if attempt else None,
                time_taken_seconds=time_taken_sec,
                time_taken_formatted=cls._format_time_taken(time_taken_sec),
                total_questions=total_q,
                questions_answered=answered_q,
                correct_answers_count=correct_q,
                incorrect_answers_count=incorrect_q,
                unanswered_count=unanswered_q,
                total_marks=total_marks,
                marks_obtained=marks_obtained,
                passing_marks=passing_marks,
                percentage=percentage,
                is_score_adjusted=res.is_score_adjusted if res else False,
                original_marks_obtained=res.original_marks_obtained if res else None,
                internal_outcome=internal_outcome,
                review_status=asgn.review_status or "PENDING_REVIEW",
                final_decision=asgn.final_decision,
                decision_reason=asgn.decision_reason,
                recruiter_remarks=asgn.recruiter_remarks,
                candidate_message=asgn.candidate_message,
                reviewed_at=asgn.reviewed_at,
                reviewed_by_name=reviewed_by_user.name if reviewed_by_user else None,
                warning_count=warning_count,
                decision_email_status=asgn.decision_email_status or "NOT_SENT",
                decision_email_error=asgn.decision_email_error
            )
            results.append(item)

        # Sorting
        reverse = (sort_order or "desc").lower() == "desc"
        if sort_by == "score":
            results.sort(key=lambda x: x.marks_obtained, reverse=reverse)
        elif sort_by == "percentage":
            results.sort(key=lambda x: x.percentage, reverse=reverse)
        elif sort_by == "time_taken":
            results.sort(key=lambda x: (x.time_taken_seconds or 0), reverse=reverse)
        elif sort_by == "name":
            results.sort(key=lambda x: x.candidate_name.lower(), reverse=reverse)
        else:
            # Default by submitted_at or assigned_at
            results.sort(key=lambda x: (x.submitted_at or x.assigned_at), reverse=reverse)

        return results

    @classmethod
    def get_recruiter_detailed_review(
        cls,
        db: Session,
        recruiter: Recruiter,
        assignment_id: str
    ) -> RecruiterDetailedReviewResponse:
        """
        Fetch full detailed answer review for a single candidate assessment attempt.
        Includes candidate snapshot answers, answer keys, explanations, proctoring events timeline,
        and decision audit history.
        """
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

        assessment = assignment.assessment
        if not assessment or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

        attempt = assignment.attempt
        result = assignment.result
        candidate = assignment.candidate
        cand_user = candidate.user if candidate else None
        job = assessment.job

        # Questions & Answers snapshot
        questions = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == assessment.id
        ).order_by(AssessmentQuestion.order_num).all()

        answers = db.query(AssessmentCandidateAnswer).filter(
            AssessmentCandidateAnswer.attempt_id == attempt.id
        ).all() if attempt else []
        ans_map = {a.question_id: a for a in answers}

        answer_items: List[RecruiterDetailedAnswerItem] = []
        for q in questions:
            opts = db.query(AssessmentQuestionOption).filter(
                AssessmentQuestionOption.question_id == q.id
            ).order_by(AssessmentQuestionOption.option_key).all()

            opt_responses = [
                AssessmentOptionResponse(
                    id=o.id,
                    option_key=o.option_key,
                    option_text=o.option_text,
                    is_correct=o.is_correct  # Confidential ground truth revealed to recruiter
                ) for o in opts
            ]

            corr_opt = next((o for o in opts if o.is_correct), None)
            ans = ans_map.get(q.id)
            sel_opt = next((o for o in opts if ans and o.id == ans.selected_option_id), None)

            if not ans or not ans.selected_option_id:
                answer_status = "UNANSWERED"
                is_correct = False
                marks_aw = 0
            elif ans.is_correct:
                answer_status = "CORRECT"
                is_correct = True
                marks_aw = ans.marks_awarded
            else:
                answer_status = "INCORRECT"
                is_correct = False
                marks_aw = 0

            # Topic / difficulty from bank question if present
            topic_str = q.bank_question.topic if q.bank_question else None
            diff_str = q.bank_question.difficulty.value if (q.bank_question and q.bank_question.difficulty) else None

            answer_items.append(RecruiterDetailedAnswerItem(
                question_id=q.id,
                question_text=q.question_text,
                topic=topic_str,
                difficulty=diff_str,
                explanation=q.explanation,
                order_num=q.order_num,
                marks=q.marks,
                options=opt_responses,
                selected_option_id=sel_opt.id if sel_opt else None,
                selected_option_key=sel_opt.option_key if sel_opt else None,
                selected_option_text=sel_opt.option_text if sel_opt else None,
                correct_option_id=corr_opt.id if corr_opt else None,
                correct_option_key=corr_opt.option_key if corr_opt else None,
                correct_option_text=corr_opt.option_text if corr_opt else None,
                status=answer_status,
                is_correct=is_correct,
                marks_awarded=marks_aw
            ))

        # Proctoring Events Timeline
        monitoring_events: List[Dict[str, Any]] = []
        warning_count = 0
        if attempt:
            proctor_session = db.query(ProctoringSession).filter(
                ProctoringSession.assessment_attempt_id == attempt.id
            ).first()
            if proctor_session:
                warning_count = proctor_session.total_warning_count
                events = db.query(ProctoringEvent).filter(
                    ProctoringEvent.proctoring_session_id == proctor_session.id
                ).order_by(ProctoringEvent.event_timestamp.asc()).all()
                for ev in events:
                    monitoring_events.append({
                        "id": ev.id,
                        "event_type": ev.event_type.value,
                        "timestamp": ev.event_timestamp.isoformat(),
                        "duration_seconds": ev.duration_seconds,
                        "severity": ev.severity,
                        "details": ev.details_json,
                        "reviewed_status": ev.reviewed_status
                    })

        # Decision History
        history_records = db.query(AssessmentDecisionHistory).filter(
            AssessmentDecisionHistory.assignment_id == assignment.id
        ).order_by(AssessmentDecisionHistory.created_at.desc()).all()

        history_items: List[DecisionHistoryItemResponse] = []
        for h in history_records:
            rec_user = db.query(User).filter(User.id == h.recruiter_user_id).first() if h.recruiter_user_id else None
            history_items.append(DecisionHistoryItemResponse(
                id=h.id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                decision=h.decision,
                recruiter_name=rec_user.name if rec_user else "Recruiter",
                reason=h.reason,
                remarks=h.remarks,
                candidate_message=h.candidate_message,
                created_at=h.created_at
            ))

        # Time taken
        time_taken_sec = None
        if attempt and attempt.started_at and attempt.submitted_at:
            start = attempt.started_at.replace(tzinfo=timezone.utc) if attempt.started_at.tzinfo is None else attempt.started_at
            end = attempt.submitted_at.replace(tzinfo=timezone.utc) if attempt.submitted_at.tzinfo is None else attempt.submitted_at
            time_taken_sec = max(0, int((end - start).total_seconds()))

        total_marks = result.total_marks if result else assessment.total_marks
        marks_obtained = result.marks_obtained if result else 0
        passing_marks = result.passing_marks if result else assessment.passing_marks
        percentage = result.percentage if result else 0.0

        total_q = len(questions)
        answered_q = sum(1 for a in answer_items if a.status != "UNANSWERED")
        correct_q = sum(1 for a in answer_items if a.is_correct)
        incorrect_q = sum(1 for a in answer_items if a.status == "INCORRECT")
        unanswered_q = total_q - answered_q

        internal_outcome = "MET_THRESHOLD" if marks_obtained >= passing_marks else "BELOW_THRESHOLD"
        reviewed_by_user = db.query(User).filter(User.id == assignment.reviewed_by_user_id).first() if assignment.reviewed_by_user_id else None

        review_item = RecruiterAssessmentReviewItem(
            assignment_id=assignment.id,
            attempt_id=attempt.id if attempt else None,
            candidate_id=candidate.id if candidate else "",
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            candidate_phone=candidate.phone if candidate else None,
            candidate_title=candidate.title if candidate else None,
            job_id=job.id if job else "",
            job_title=job.title if job else "",
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            assigned_at=assignment.assigned_at,
            started_at=attempt.started_at if attempt else None,
            submitted_at=attempt.submitted_at if attempt else None,
            time_taken_seconds=time_taken_sec,
            time_taken_formatted=cls._format_time_taken(time_taken_sec),
            total_questions=total_q,
            questions_answered=answered_q,
            correct_answers_count=correct_q,
            incorrect_answers_count=incorrect_q,
            unanswered_count=unanswered_q,
            total_marks=total_marks,
            marks_obtained=marks_obtained,
            passing_marks=passing_marks,
            percentage=percentage,
            is_score_adjusted=result.is_score_adjusted if result else False,
            original_marks_obtained=result.original_marks_obtained if result else None,
            internal_outcome=internal_outcome,
            review_status=assignment.review_status or "PENDING_REVIEW",
            final_decision=assignment.final_decision,
            decision_reason=assignment.decision_reason,
            recruiter_remarks=assignment.recruiter_remarks,
            candidate_message=assignment.candidate_message,
            reviewed_at=assignment.reviewed_at,
            reviewed_by_name=reviewed_by_user.name if reviewed_by_user else None,
            warning_count=warning_count,
            decision_email_status=assignment.decision_email_status or "NOT_SENT",
            decision_email_error=assignment.decision_email_error
        )

        score_adj_reason = (result.score_adjustment_reason if result else None) or assignment.score_adjustment_reason
        orig_score = (result.original_marks_obtained if result else None)

        session_recording_info = None
        if attempt:
            media_asset = None
            if getattr(attempt, "session_recording_asset_id", None):
                media_asset = db.query(MediaAsset).filter(MediaAsset.id == attempt.session_recording_asset_id).first()
            if not media_asset:
                media_asset = db.query(MediaAsset).filter(
                    MediaAsset.attempt_id == attempt.id,
                    MediaAsset.assessment_type == "MCQ"
                ).first()

            if media_asset:
                from app.services.cloudinary_service import CloudinaryService
                signed_playback_url = CloudinaryService.generate_signed_playback_url(
                    public_id=media_asset.public_id,
                    resource_type=media_asset.resource_type or "video",
                    file_format=media_asset.file_format,
                    secure_url=media_asset.secure_url
                )
                thumbnail_url = CloudinaryService.generate_thumbnail_url(
                    public_id=media_asset.public_id,
                    resource_type=media_asset.resource_type or "video"
                )
                session_recording_info = {
                    "id": media_asset.id,
                    "public_id": media_asset.public_id,
                    "secure_url": media_asset.secure_url,
                    "playback_url": signed_playback_url or media_asset.playback_url or media_asset.secure_url,
                    "thumbnail_url": thumbnail_url or media_asset.thumbnail_url,
                    "duration_seconds": media_asset.video_duration_seconds or 0.0,
                    "file_size_bytes": media_asset.file_size_bytes or 0,
                    "upload_status": media_asset.upload_status,
                    "created_at": media_asset.created_at.isoformat() if media_asset.created_at else None
                }

        return RecruiterDetailedReviewResponse(
            review_item=review_item,
            answers=answer_items,
            decision_history=history_items,
            monitoring_events=monitoring_events,
            session_recording=session_recording_info,
            score_adjustment_reason=score_adj_reason,
            original_score=orig_score
        )

    @classmethod
    def adjust_candidate_score(
        cls,
        db: Session,
        recruiter: Recruiter,
        assignment_id: str,
        new_score: float,
        reason: str
    ) -> RecruiterDetailedReviewResponse:
        """
        Adjust a candidate's assessment score with mandatory justification.
        Preserves original automatically computed score, recruiter ID, and timestamp in audit history.
        """
        if not reason or len(reason.strip()) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid reason (minimum 3 characters) is required for manual score adjustment.")

        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

        assessment = assignment.assessment
        if not assessment or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

        result = assignment.result
        if not result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No submitted result exists to adjust.")

        if new_score < 0 or new_score > result.total_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adjusted score must be between 0 and total marks ({result.total_marks})."
            )

        now = datetime.now(timezone.utc)
        orig_score = result.original_marks_obtained if result.original_marks_obtained is not None else result.marks_obtained
        result.original_marks_obtained = orig_score
        result.marks_obtained = new_score
        result.percentage = round((new_score / result.total_marks * 100.0), 2) if result.total_marks > 0 else 0.0
        result.is_score_adjusted = True
        result.score_adjustment_reason = reason.strip()
        result.adjusted_by_user_id = recruiter.user_id
        result.adjusted_at = now

        # Update assignment tracking
        assignment.score_adjustment = new_score - orig_score
        assignment.score_adjustment_reason = reason.strip()
        assignment.adjusted_by_user_id = recruiter.user_id
        assignment.adjusted_at = now

        # Record immutable audit history
        hist = AssessmentDecisionHistory(
            application_id=assignment.application_id,
            assessment_id=assignment.assessment_id,
            assignment_id=assignment.id,
            attempt_id=assignment.attempt.id if assignment.attempt else "",
            previous_status=assignment.review_status,
            new_status=assignment.review_status,
            decision="SCORE_ADJUSTED",
            recruiter_id=recruiter.id,
            recruiter_user_id=recruiter.user_id,
            reason=reason.strip(),
            remarks=f"Manual score adjustment from {orig_score} to {new_score} / {result.total_marks}.",
            created_at=now
        )
        db.add(hist)
        db.commit()

        return cls.get_recruiter_detailed_review(db, recruiter, assignment_id)

    @classmethod
    def make_recruiter_decision(
        cls,
        db: Session,
        recruiter: Recruiter,
        assignment_id: str,
        decision: str,
        reason: Optional[str] = None,
        remarks: Optional[str] = None,
        candidate_message: Optional[str] = None
    ) -> RecruiterDecisionResponse:
        """
        Execute recruiter's final hiring decision: ACCEPT, REJECT, MOVE_TO_INTERVIEW, or ON_HOLD.
        Synchronizes application status, records immutable decision history, and dispatches candidate notifications.
        """
        valid_decisions = ["ACCEPTED", "REJECTED", "MOVED_TO_INTERVIEW", "ON_HOLD", "UNDER_REVIEW"]
        decision_upper = decision.upper().strip()
        if decision_upper not in valid_decisions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision '{decision}'. Must be one of: {', '.join(valid_decisions)}"
            )

        if decision_upper == "REJECTED" and not (reason and reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A clear decision reason is mandatory when rejecting a candidate."
            )

        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

        assessment = assignment.assessment
        if not assessment or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

        app = assignment.application
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated application not found.")

        now = datetime.now(timezone.utc)
        prev_status = assignment.review_status or "PENDING_REVIEW"
        old_app_status = app.status.value

        # Update assignment review fields
        assignment.review_status = decision_upper
        assignment.final_decision = decision_upper
        assignment.decision_reason = reason.strip() if reason else None
        assignment.recruiter_remarks = remarks.strip() if remarks else None
        assignment.candidate_message = candidate_message.strip() if candidate_message else None
        assignment.reviewed_by_user_id = recruiter.user_id
        assignment.reviewed_at = now

        # Update Application pipeline status consistently
        if decision_upper == "ACCEPTED":
            app.status = ApplicationStatusEnum.SHORTLISTED
            app_status_label = "SHORTLISTED"
        elif decision_upper == "REJECTED":
            app.status = ApplicationStatusEnum.REJECTED
            app_status_label = "REJECTED"
        elif decision_upper == "MOVED_TO_INTERVIEW":
            app.status = ApplicationStatusEnum.INTERVIEW
            app_status_label = "INTERVIEW"
        elif decision_upper in ["ON_HOLD", "UNDER_REVIEW"]:
            app.status = ApplicationStatusEnum.UNDER_REVIEW
            app_status_label = "UNDER_REVIEW"
        else:
            app_status_label = app.status.value

        app.updated_at = now

        # Record Application history
        app_hist = ApplicationHistory(
            application_id=app.id,
            from_status=old_app_status,
            to_status=app_status_label,
            changed_by_user_id=recruiter.user_id,
            notes=f"Recruiter Assessment Decision: {decision_upper}. Reason: {reason or 'N/A'}"
        )
        db.add(app_hist)

        # Record immutable Assessment Decision History
        decision_hist = AssessmentDecisionHistory(
            application_id=app.id,
            assessment_id=assessment.id,
            assignment_id=assignment.id,
            attempt_id=assignment.attempt.id if assignment.attempt else "",
            previous_status=prev_status,
            new_status=decision_upper,
            decision=decision_upper,
            recruiter_id=recruiter.id,
            recruiter_user_id=recruiter.user_id,
            reason=reason.strip() if reason else None,
            remarks=remarks.strip() if remarks else None,
            candidate_message=candidate_message.strip() if candidate_message else None,
            created_at=now
        )
        db.add(decision_hist)
        db.commit()
        db.refresh(decision_hist)

        # ----------------------------------------------------------------------
        # Post-Commit Candidate Notifications (In-App + Brevo Email)
        # ----------------------------------------------------------------------
        cand = assignment.candidate
        cand_user = cand.user if cand else None
        cand_name = cand_user.name if cand_user else "Candidate"
        cand_email = cand_user.email if cand_user else ""
        job_title = app.job.title if app.job else assessment.title
        company_name = recruiter.company.company_name if recruiter.company else "SkillSphere Partner"

        # 1. In-app notification
        if cand_user:
            notif_titles = {
                "ACCEPTED": "Assessment Shortlisted — Next Stage",
                "REJECTED": "SkillSphere Application Status Update",
                "MOVED_TO_INTERVIEW": "Progressed to Interview Stage!",
                "ON_HOLD": "Assessment Status: Under Review",
                "UNDER_REVIEW": "Assessment Status: Under Review"
            }
            notif_msgs = {
                "ACCEPTED": f"Congratulations! Your assessment for '{assessment.title}' has been reviewed, and you have been shortlisted for the next stage.",
                "REJECTED": f"Thank you for participating in the assessment for '{assessment.title}'. The recruitment team has updated your application status.",
                "MOVED_TO_INTERVIEW": f"You have successfully progressed to the interview stage for '{assessment.title}'!",
                "ON_HOLD": f"Your assessment for '{assessment.title}' is currently on hold under review.",
                "UNDER_REVIEW": f"Your assessment for '{assessment.title}' is under review."
            }
            create_notification(
                db=db,
                user_id=cand_user.id,
                title=notif_titles.get(decision_upper, "Assessment Status Update"),
                message=notif_msgs.get(decision_upper, f"Your assessment for '{assessment.title}' has been updated."),
                notification_type="ASSESSMENT",
                link="/dashboard?tab=applications"
            )

        # 2. Brevo Email dispatch
        email_status = "NOT_SENT"
        if decision_upper in ["ACCEPTED", "REJECTED", "MOVED_TO_INTERVIEW"] and cand_email:
            try:
                res = EmailService.send_assessment_decision_email(
                    to_email=cand_email,
                    candidate_name=cand_name,
                    job_title=job_title,
                    company_name=company_name,
                    assessment_title=assessment.title,
                    decision=decision_upper,
                    candidate_message=candidate_message
                )
                if res.get("delivered") or res.get("success"):
                    email_status = "SENT"
                    assignment.decision_email_status = "SENT"
                    assignment.brevo_message_id = res.get("message_id")
                    assignment.decision_email_sent_at = datetime.now(timezone.utc)
                    assignment.decision_email_error = None
                else:
                    email_status = "FAILED"
                    assignment.decision_email_status = "FAILED"
                    assignment.decision_email_error = res.get("detail", "Brevo email delivery failed")
            except Exception as e:
                email_status = "FAILED"
                assignment.decision_email_status = "FAILED"
                assignment.decision_email_error = str(e)
            db.commit()
        elif decision_upper in ["ON_HOLD", "UNDER_REVIEW"]:
            email_status = "NOT_APPLICABLE"
            assignment.decision_email_status = "NOT_APPLICABLE"
            db.commit()

        return RecruiterDecisionResponse(
            assignment_id=assignment.id,
            decision=decision_upper,
            review_status=assignment.review_status,
            application_status=app.status.value,
            decision_email_status=email_status,
            email_dispatched=(email_status == "SENT"),
            history_id=decision_hist.id,
            message=f"Candidate successfully marked as {decision_upper}."
        )

    @classmethod
    def retry_decision_email(
        cls,
        db: Session,
        recruiter: Recruiter,
        assignment_id: str
    ) -> Dict[str, Any]:
        """
        Retry sending decision notification email to candidate following previous delivery failure.
        """
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

        assessment = assignment.assessment
        if not assessment or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        decision = assignment.final_decision or assignment.review_status
        if not decision or decision in ["PENDING_REVIEW", "ON_HOLD", "UNDER_REVIEW"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email notification is applicable for this review status.")

        cand = assignment.candidate
        cand_user = cand.user if cand else None
        if not cand_user or not cand_user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate email is missing.")

        app = assignment.application
        job_title = app.job.title if (app and app.job) else assessment.title
        company_name = recruiter.company.company_name if recruiter.company else "SkillSphere Partner"

        try:
            res = EmailService.send_assessment_decision_email(
                to_email=cand_user.email,
                candidate_name=cand_user.name,
                job_title=job_title,
                company_name=company_name,
                assessment_title=assessment.title,
                decision=decision,
                candidate_message=assignment.candidate_message
            )
            if res.get("delivered"):
                assignment.decision_email_status = "SENT"
                assignment.brevo_message_id = res.get("message_id")
                assignment.decision_email_sent_at = datetime.now(timezone.utc)
                assignment.decision_email_error = None
                db.commit()
                return {"status": "SENT", "message": "Notification email sent successfully."}
            else:
                assignment.decision_email_status = "FAILED"
                assignment.decision_email_error = res.get("detail", "Brevo email retry failed")
                db.commit()
                return {"status": "FAILED", "detail": assignment.decision_email_error}
        except Exception as e:
            assignment.decision_email_status = "FAILED"
            assignment.decision_email_error = str(e)
            db.commit()
            return {"status": "FAILED", "detail": str(e)}

    @classmethod
    def get_assessment_comparison_and_analytics(
        cls,
        db: Session,
        recruiter: Recruiter,
        assessment_id: str
    ) -> AssessmentComparisonResponse:
        """
        Candidate comparison matrix and aggregate recruiter analytics for an assessment.
        Calculates topic-wise and difficulty-wise performance, time taken, score distribution, and hiring metrics.
        """
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
        if assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        assignments = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.assessment_id == assessment.id
        ).all()

        total_assigned = len(assignments)
        total_started = 0
        total_submitted = 0
        pending_reviews = 0
        accepted_count = 0
        rejected_count = 0
        on_hold_count = 0
        moved_to_interview_count = 0

        scores_list: List[int] = []
        percentages_list: List[float] = []
        times_list: List[int] = []

        score_buckets = {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0}
        candidate_items: List[CandidateComparisonItem] = []

        for asgn in assignments:
            attempt = asgn.attempt
            res = asgn.result
            cand = asgn.candidate
            cand_user = cand.user if cand else None

            if attempt:
                total_started += 1
            if res:
                total_submitted += 1
                scores_list.append(res.marks_obtained)
                percentages_list.append(res.percentage)

                # Time taken
                if attempt and attempt.started_at and attempt.submitted_at:
                    start = attempt.started_at.replace(tzinfo=timezone.utc) if attempt.started_at.tzinfo is None else attempt.started_at
                    end = attempt.submitted_at.replace(tzinfo=timezone.utc) if attempt.submitted_at.tzinfo is None else attempt.submitted_at
                    time_sec = max(0, int((end - start).total_seconds()))
                    times_list.append(time_sec)
                else:
                    time_sec = None

                # Score distribution
                pct = res.percentage
                if pct <= 25.0:
                    score_buckets["0-25%"] += 1
                elif pct <= 50.0:
                    score_buckets["26-50%"] += 1
                elif pct <= 75.0:
                    score_buckets["51-75%"] += 1
                else:
                    score_buckets["76-100%"] += 1

                # Topic-wise & difficulty-wise breakdown for this candidate
                answers = db.query(AssessmentCandidateAnswer).filter(
                    AssessmentCandidateAnswer.attempt_id == attempt.id
                ).all() if attempt else []
                ans_map = {a.question_id: a for a in answers}

                topic_breakdown: Dict[str, Dict[str, Any]] = {}
                diff_breakdown: Dict[str, Dict[str, Any]] = {}

                for q in assessment.questions:
                    t = q.bank_question.topic if q.bank_question else "General"
                    d = q.bank_question.difficulty.value if (q.bank_question and q.bank_question.difficulty) else "INTERMEDIATE"

                    if t not in topic_breakdown:
                        topic_breakdown[t] = {"total": 0, "correct": 0, "marks": 0}
                    if d not in diff_breakdown:
                        diff_breakdown[d] = {"total": 0, "correct": 0, "marks": 0}

                    topic_breakdown[t]["total"] += 1
                    diff_breakdown[d]["total"] += 1

                    ans = ans_map.get(q.id)
                    if ans and ans.is_correct:
                        topic_breakdown[t]["correct"] += 1
                        topic_breakdown[t]["marks"] += ans.marks_awarded
                        diff_breakdown[d]["correct"] += 1
                        diff_breakdown[d]["marks"] += ans.marks_awarded

                # Status counters
                status_curr = asgn.review_status or "PENDING_REVIEW"
                if status_curr == "PENDING_REVIEW":
                    pending_reviews += 1
                elif status_curr == "ACCEPTED":
                    accepted_count += 1
                elif status_curr == "REJECTED":
                    rejected_count += 1
                elif status_curr in ["ON_HOLD", "UNDER_REVIEW"]:
                    on_hold_count += 1
                elif status_curr == "MOVED_TO_INTERVIEW":
                    moved_to_interview_count += 1

                candidate_items.append(CandidateComparisonItem(
                    candidate_id=cand.id if cand else "",
                    candidate_name=cand_user.name if cand_user else "Candidate",
                    candidate_email=cand_user.email if cand_user else "",
                    total_score=res.marks_obtained,
                    total_marks=res.total_marks,
                    accuracy_percentage=res.percentage,
                    time_taken_seconds=time_sec,
                    time_taken_formatted=cls._format_time_taken(time_sec),
                    correct_count=res.correct_answers_count,
                    incorrect_count=max(0, res.questions_answered - res.correct_answers_count),
                    unanswered_count=max(0, res.total_questions - res.questions_answered),
                    review_status=status_curr,
                    final_decision=asgn.final_decision,
                    topic_breakdown=topic_breakdown,
                    difficulty_breakdown=diff_breakdown
                ))

        # Sort candidate comparison items by score desc
        candidate_items.sort(key=lambda x: x.total_score, reverse=True)

        avg_score = round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0
        avg_pct = round(sum(percentages_list) / len(percentages_list), 2) if percentages_list else 0.0
        avg_time = round(sum(times_list) / len(times_list), 1) if times_list else 0.0

        analytics = AssessmentAnalyticsOverview(
            total_assigned=total_assigned,
            total_started=total_started,
            total_submitted=total_submitted,
            pending_reviews=pending_reviews,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            on_hold_count=on_hold_count,
            moved_to_interview_count=moved_to_interview_count,
            average_score=avg_score,
            average_percentage=avg_pct,
            average_time_seconds=avg_time,
            score_distribution=score_buckets
        )

        job = assessment.job
        return AssessmentComparisonResponse(
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            job_id=job.id if job else "",
            job_title=job.title if job else "",
            analytics=analytics,
            candidates=candidate_items
        )

    @classmethod
    def get_recruiter_candidate_review(
        cls,
        db: Session,
        recruiter: Recruiter,
        assignment_id: str
    ) -> RecruiterCandidateReviewResponse:
        """Backward-compatible endpoint for existing UI components."""
        assignment = db.query(CandidateAssessmentAssignment).filter(
            CandidateAssessmentAssignment.id == assignment_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")

        assessment = assignment.assessment
        if not assessment or assessment.recruiter_id != recruiter.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You do not own this assessment.")

        attempt = assignment.attempt
        result = assignment.result
        candidate = assignment.candidate
        cand_user = candidate.user if candidate else None
        job = assessment.job

        questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).order_by(AssessmentQuestion.order_num).all()
        answers = db.query(AssessmentCandidateAnswer).filter(AssessmentCandidateAnswer.attempt_id == attempt.id).all() if attempt else []
        ans_map = {a.question_id: a for a in answers}

        answer_items = []
        for q in questions:
            opts = db.query(AssessmentQuestionOption).filter(AssessmentQuestionOption.question_id == q.id).order_by(AssessmentQuestionOption.option_key).all()
            opt_responses = [
                AssessmentOptionResponse(
                    id=o.id,
                    option_key=o.option_key,
                    option_text=o.option_text,
                    is_correct=o.is_correct  # Disclosed to recruiter only
                ) for o in opts
            ]

            corr_opt = next((o for o in opts if o.is_correct), None)
            ans = ans_map.get(q.id)

            answer_items.append(RecruiterCandidateAnswerItem(
                question_id=q.id,
                question_text=q.question_text,
                order_num=q.order_num,
                marks=q.marks,
                options=opt_responses,
                selected_option_id=ans.selected_option_id if ans else None,
                correct_option_id=corr_opt.id if corr_opt else "",
                is_correct=ans.is_correct if (ans and ans.is_correct is not None) else False,
                marks_awarded=ans.marks_awarded if ans else 0
            ))

        return RecruiterCandidateReviewResponse(
            assignment_id=assignment.id,
            candidate_id=candidate.id if candidate else "",
            candidate_name=cand_user.name if cand_user else "Candidate",
            candidate_email=cand_user.email if cand_user else "",
            job_title=job.title if job else "",
            assessment_title=assessment.title,
            total_marks=result.total_marks if result else assessment.total_marks,
            marks_obtained=result.marks_obtained if result else 0,
            passing_marks=result.passing_marks if result else assessment.passing_marks,
            percentage=result.percentage if result else 0.0,
            result=result.result.value if result else assignment.status.value,
            started_at=attempt.started_at if attempt else None,
            submitted_at=attempt.submitted_at if attempt else None,
            answers=answer_items
        )
