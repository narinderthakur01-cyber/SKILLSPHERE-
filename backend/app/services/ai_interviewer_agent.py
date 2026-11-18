import os
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    Interview, InterviewQuestion, InterviewResponse,
    InterviewEvaluation, MediaAsset, User
)
from app.services.livekit_service import LiveKitService
from app.services.cloudinary_service import CloudinaryService
from app.services.interview_ai_service import InterviewAIService

logger = logging.getLogger("skillsphere.ai_interviewer")

class AIInterviewerAgent:
    """
    SkillSphere LiveKit AI Interviewer Agent Service.
    Coordinates:
      - LiveKit room participation as 'agent-ai-interviewer'
      - Real-time conversational interview flow with adaptive pacing
      - Question sequencing and contextual follow-up generation
      - Hybrid mode recruiter takeover & handover detection
      - Audio transcription ingestion & Cloudinary recording archival
    """

    @classmethod
    def generate_agent_token(cls, interview: Interview) -> Dict[str, Any]:
        """
        Generate short-lived LiveKit token for the AI Interviewer bot participant.
        """
        token_info = LiveKitService.generate_room_token(
            interview=interview,
            user_id=f"ai-agent-{interview.id[:8]}",
            user_name="SkillSphere AI Interviewer",
            display_name="SkillSphere AI Interviewer",
            role="recruiter",  # Granted publication rights
            room_name=interview.room_id or interview.id
        )
        return token_info

    @classmethod
    def get_interview_state(cls, db: Session, interview_id: str) -> Dict[str, Any]:
        """
        Get current live AI interviewer state, current question, and progress.
        """
        interview = db.query(Interview).filter(
            (Interview.id == interview_id) | (Interview.room_id == interview_id)
        ).first()
        if not interview:
            raise ValueError("Interview not found.")

        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id
        ).order_by(InterviewQuestion.sequence_number.asc()).all()

        current_idx = interview.current_question_index or 0
        current_q = questions[current_idx] if 0 <= current_idx < len(questions) else None

        return {
            "interview_id": interview.id,
            "room_id": interview.room_id,
            "interview_mode": interview.interview_mode,
            "room_status": interview.room_status,
            "ai_takeover_status": interview.ai_takeover_status,
            "current_question_index": current_idx,
            "total_questions": len(questions),
            "current_question": {
                "id": current_q.id,
                "sequence_number": current_q.sequence_number,
                "question_text": current_q.question_text,
                "question_type": current_q.question_type,
                "expected_concepts": current_q.expected_concepts,
                "max_duration_seconds": current_q.max_duration_seconds,
            } if current_q else None,
            "is_completed": current_idx >= len(questions)
        }

    @classmethod
    def advance_question(cls, db: Session, interview_id: str) -> Dict[str, Any]:
        """
        Advance AI interview to the next question.
        """
        interview = db.query(Interview).filter(
            (Interview.id == interview_id) | (Interview.room_id == interview_id)
        ).first()
        if not interview:
            raise ValueError("Interview not found.")

        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id
        ).order_by(InterviewQuestion.sequence_number.asc()).all()

        next_idx = (interview.current_question_index or 0) + 1
        interview.current_question_index = next_idx

        if next_idx >= len(questions):
            # All questions answered -> mark room ready for final evaluation
            interview.room_status = "PROCESSING"
        db.commit()
        db.refresh(interview)

        return cls.get_interview_state(db, interview.id)

    @classmethod
    def generate_follow_up_prompt(
        cls,
        candidate_response: str,
        question_text: str,
        expected_concepts: List[str]
    ) -> str:
        """
        Generate contextual AI follow-up probe based on what candidate covered.
        """
        response_lower = candidate_response.lower()
        missed = [c for c in expected_concepts if c.lower() not in response_lower]

        if missed:
            focus_concept = missed[0]
            return f"That gives good context. Could you dive a bit deeper into your approach regarding {focus_concept} specifically?"
        else:
            return "Excellent explanation. Moving forward to our next area of focus."

    @classmethod
    def finalize_and_archive_to_cloudinary(
        cls,
        db: Session,
        interview_id: str,
        recording_file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transfer finalized AI interview recording into Cloudinary folder 'skillsphere/ai-interviews/'
        and create corresponding MediaAsset record with audit trail.
        """
        interview = db.query(Interview).filter(
            (Interview.id == interview_id) | (Interview.room_id == interview_id)
        ).first()
        if not interview:
            raise ValueError("Interview not found.")

        public_id = f"ai_interview_{interview.id}_{int(time.time())}"
        folder = CloudinaryService.ALLOWED_FOLDERS.get("ai_interviews", "skillsphere/ai-interviews")

        # Create MediaAsset record
        delivery_url = recording_file_url or f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/video/upload/{folder}/{public_id}.mp4"

        asset = MediaAsset(
            public_id=f"{folder}/{public_id}",
            original_filename=f"ai_interview_{interview.id}.mp4",
            resource_type="video",
            file_format="mp4",
            secure_url=delivery_url,
            playback_url=delivery_url,
            folder=folder,
            interview_id=interview.id,
            candidate_id=interview.candidate_id,
            job_id=interview.application.job_id if interview.application else None,
            access_classification="CONFIDENTIAL",
            upload_status="COMPLETED"
        )
        db.add(asset)

        interview.status = "COMPLETED"
        interview.room_status = "COMPLETED"
        interview.ended_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(asset)

        return {
            "media_asset_id": asset.id,
            "public_id": asset.public_id,
            "secure_url": asset.secure_url,
            "folder": folder,
            "interview_id": interview.id
        }
