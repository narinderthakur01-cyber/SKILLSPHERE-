import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.chatbot.matcher import IntentMatcher
from app.chatbot.history import get_history_store, SessionOwnershipError
from app.schemas.chatbot_schemas import (
    ChatResponse, QuickReply, FAQItem, FAQListResponse, ChatbotHealthResponse
)

class ChatbotService:
    """
    Coordinates FAQ knowledge loading, intent matching, role gating,
    context restoration, and conversation persistence for SkillSphere Assistant.
    """

    def __init__(self, kb_path: Optional[str] = None):
        if kb_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.join(current_dir, "knowledge_base.json")
        self.kb_path = kb_path
        self.data = self._load_knowledge_base()
        self.faqs: List[Dict[str, Any]] = self.data.get("faqs", [])
        self.matcher = IntentMatcher(self.faqs)

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Safely load JSON knowledge base from disk."""
        if not os.path.exists(self.kb_path):
            return {"version": "1.0.0", "faqs": []}
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading SkillSphere FAQ knowledge base: {e}")
            return {"version": "1.0.0", "faqs": []}

    def reload(self):
        """Reload FAQ definitions from file."""
        self.data = self._load_knowledge_base()
        self.faqs = self.data.get("faqs", [])
        self.matcher = IntentMatcher(self.faqs)

    def get_faqs_for_role(self, role: Optional[str]) -> List[FAQItem]:
        """Return FAQ items accessible to the given role."""
        raw_faqs = self.matcher.filter_by_role(role)
        results = []
        for f in raw_faqs:
            q_replies = [QuickReply(**qr) for qr in f.get("quick_replies", [])]
            results.append(
                FAQItem(
                    id=f.get("id"),
                    category=f.get("category"),
                    roles=f.get("roles", []),
                    intent=f.get("intent"),
                    title=f.get("title"),
                    sample_questions=f.get("sample_questions", []),
                    keywords=f.get("keywords", []),
                    synonyms=f.get("synonyms", []),
                    response=f.get("response"),
                    related_questions=f.get("related_questions", []),
                    quick_replies=q_replies
                )
            )
        return results

    def get_default_quick_replies(self, role: Optional[str]) -> List[QuickReply]:
        """Return standard introductory quick replies tailored by user role."""
        norm_role = (role or "").upper()
        if norm_role == "RECRUITER":
            return [
                QuickReply(label="Post a Job", query="How do I post a new job?", topic="recruiter_create_job"),
                QuickReply(label="Kanban Pipeline", query="How does the Kanban pipeline work?", topic="recruiter_kanban_pipeline"),
                QuickReply(label="Question Bank", query="How do I manage the Question Bank for tests?", topic="recruiter_question_bank"),
                QuickReply(label="LiveKit Meeting", query="How do I schedule a LiveKit video interview?", topic="recruiter_schedule_interview")
            ]
        
        # Default / Job Seeker / Candidate
        return [
            QuickReply(label="Upload Resume", query="How do I upload my resume?", topic="candidate_resume_upload"),
            QuickReply(label="Browse Jobs", query="How do I search and filter jobs?", topic="candidate_job_search"),
            QuickReply(label="MCQ Assessment", query="What is the Round 1 MCQ assessment?", topic="candidate_mcq_assessment"),
            QuickReply(label="Live Interview", query="How do I join a live video interview?", topic="candidate_live_interview")
        ]

    def process_message(
        self,
        message: str,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        context_topic: Optional[str] = None
    ) -> ChatResponse:
        """
        Process a user message through intent matching and return a structured response.
        """
        active_session = session_id or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Execute rule-based matching
        matched_faq, score, match_type = self.matcher.match(
            query=message,
            role=role,
            context_topic=context_topic
        )

        if matched_faq:
            q_replies = [QuickReply(**qr) for qr in matched_faq.get("quick_replies", [])]
            return ChatResponse(
                message=matched_faq.get("response", ""),
                matched_intent=matched_faq.get("intent", "unknown"),
                confidence_score=score,
                session_id=active_session,
                category=matched_faq.get("category", "general"),
                quick_replies=q_replies,
                suggested_questions=matched_faq.get("related_questions", []),
                timestamp=timestamp
            )

        # Fallback response for unmapped queries
        fallback_msg = (
            "I'm not quite sure I understand that question about SkillSphere. "
            "I can help with resume uploads & OCR parsing, job search & bookmarks, "
            "proctored MCQ assessments, video assessments, pipeline tracking, or live video meetings. "
            "Please try selecting one of the suggested topics below or rephrasing your question."
        )
        return ChatResponse(
            message=fallback_msg,
            matched_intent="fallback",
            confidence_score=score,
            session_id=active_session,
            category="fallback",
            quick_replies=self.get_default_quick_replies(role),
            suggested_questions=[
                "How do I upload my resume?",
                "What is the Round 1 MCQ assessment?",
                "How does the Kanban pipeline work?",
                "How do I get technical support?"
            ],
            timestamp=timestamp
        )

    def get_health(self) -> ChatbotHealthResponse:
        """Return diagnostic health metrics for the chatbot engine and storage backend."""
        total = len(self.faqs)
        cand = sum(1 for f in self.faqs if f.get("category") == "candidate")
        rec = sum(1 for f in self.faqs if f.get("category") == "recruiter")
        gen = sum(1 for f in self.faqs if f.get("category") == "general")
        
        storage_healthy = False
        storage_backend = "unknown"
        try:
            store = get_history_store()
            storage_healthy = store.is_healthy()
            storage_backend = getattr(settings, "CHATBOT_STORAGE", "sqlite")
        except Exception:
            storage_healthy = False

        return ChatbotHealthResponse(
            status="healthy" if storage_healthy else "degraded",
            engine="rule_based_deterministic",
            total_faqs=total,
            candidate_faqs=cand,
            recruiter_faqs=rec,
            general_faqs=gen,
            storage_backend=storage_backend,
            storage_healthy=storage_healthy,
            version=self.data.get("version", "1.0.0")
        )

# Global service instance for the application
chatbot_service = ChatbotService()
