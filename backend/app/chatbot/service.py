import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.chatbot.language import multilingual_engine
from app.chatbot.matcher import IntentMatcher
from app.chatbot.history import get_history_store, SessionOwnershipError
from app.chatbot.troubleshooter import troubleshooting_engine, TroubleshootingEngine
from app.chatbot.llm import llm_fallback_engine, HybridLLMFallback
from app.schemas.chatbot_schemas import (
    ChatResponse, QuickReply, FAQItem, FAQListResponse, ChatbotHealthResponse
)

class ChatbotService:
    """
    Coordinates FAQ knowledge loading, intent matching, role gating,
    guided troubleshooting state machine, hybrid LLM fallback,
    and conversation persistence for SkillSphere Assistant.
    """

    def __init__(
        self,
        kb_path: Optional[str] = None,
        llm_fallback: Optional[HybridLLMFallback] = None,
        troubleshooter: Optional[TroubleshootingEngine] = None
    ):
        if kb_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.join(current_dir, "knowledge_base.json")
        self.kb_path = kb_path
        self.data = self._load_knowledge_base()
        self.faqs: List[Dict[str, Any]] = self.data.get("faqs", [])
        self.matcher = IntentMatcher(self.faqs)
        self.llm_fallback = llm_fallback or llm_fallback_engine
        self.troubleshooter = troubleshooter or troubleshooting_engine

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
                    multilingual_responses=f.get("multilingual_responses", {}),
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
        context_topic: Optional[str] = None,
        language_preference: Optional[str] = None,
        db: Optional[Any] = None,
        current_user: Optional[Any] = None
    ) -> ChatResponse:
        """
        Process a user message through multilingual detection, ambiguity check,
        and intent matching, returning an appropriately localized structured response.
        """
        active_session = session_id or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Multilingual processing
        detection = multilingual_engine.process(message)

        # Resolve effective language for response generation (manual preference takes precedence)
        effective_lang = (language_preference or detection.detected_language.value).lower().strip()
        if effective_lang in ["hi", "hi-deva"]:
            target_key = "hi"
        elif effective_lang in ["pa"]:
            target_key = "pa"
        elif effective_lang in ["pa-latn"]:
            target_key = "pa-Latn"
        elif effective_lang in ["hinglish"]:
            target_key = "hinglish"
        else:
            target_key = "en"

        # 1. Active Troubleshooting Session or Ticket Tracking / Escalation
        existing_tb_state = self.troubleshooter.get_session_state(active_session)
        if existing_tb_state or context_topic in ["track_tickets", "ticket_escalation", "confirm_ticket_submission", "cancel_ticket_creation"]:
            tb_response = self.troubleshooter.handle_message(
                message=message,
                session_id=active_session,
                role=role,
                context_topic=context_topic,
                target_lang=target_key,
                db=db,
                current_user=current_user
            )
            if tb_response:
                tb_response.session_id = active_session
                tb_response.timestamp = timestamp
                tb_response.detected_language = detection.detected_language.value
                tb_response.writing_script = detection.script.value
                tb_response.language_confidence = detection.confidence
                return tb_response

        # 2. Check for Exact FAQ Match First (Preserves Master Prompt Canonical Questions)
        matched_faq, score, match_type = self.matcher.match(
            query=message,
            role=role,
            context_topic=context_topic
        )
        if matched_faq and match_type in ["exact_sample_match", "exact_aligned_match"]:
            q_replies = [QuickReply(**qr) for qr in matched_faq.get("quick_replies", [])]
            resp_text = (
                matched_faq.get("multilingual_responses", {}).get(target_key) or
                matched_faq.get("response", "")
            )
            return ChatResponse(
                message=resp_text,
                matched_intent=matched_faq.get("intent", "unknown"),
                confidence_score=score,
                session_id=active_session,
                category=matched_faq.get("category", "general"),
                quick_replies=q_replies,
                suggested_questions=matched_faq.get("related_questions", []),
                timestamp=timestamp,
                detected_language=detection.detected_language.value,
                writing_script=detection.script.value,
                language_confidence=detection.confidence
            )

        # 3. Smart Guided Troubleshooting Engine Layer (New Flow Initialization)
        tb_response = self.troubleshooter.handle_message(
            message=message,
            session_id=active_session,
            role=role,
            context_topic=context_topic,
            target_lang=target_key,
            db=db,
            current_user=current_user
        )
        if tb_response:
            tb_response.session_id = active_session
            tb_response.timestamp = timestamp
            tb_response.detected_language = detection.detected_language.value
            tb_response.writing_script = detection.script.value
            tb_response.language_confidence = detection.confidence
            return tb_response

        # 4. Standard Rule-Based / Keyword / Ambiguity FAQ Match
        if matched_faq:
            q_replies = [QuickReply(**qr) for qr in matched_faq.get("quick_replies", [])]
            resp_text = (
                matched_faq.get("multilingual_responses", {}).get(target_key) or
                matched_faq.get("response", "")
            )
            return ChatResponse(
                message=resp_text,
                matched_intent=matched_faq.get("intent", "unknown"),
                confidence_score=score,
                session_id=active_session,
                category=matched_faq.get("category", "general"),
                quick_replies=q_replies,
                suggested_questions=matched_faq.get("related_questions", []),
                timestamp=timestamp,
                detected_language=detection.detected_language.value,
                writing_script=detection.script.value,
                language_confidence=detection.confidence
            )

        # 5. Grounded Hybrid LLM Fallback Layer (Optional, temperature=0.0)
        llm_answer = self.llm_fallback.generate_grounded_response(
            user_message=message,
            detected_language=detection.detected_language.value,
            language_preference=language_preference,
            user_role=role
        )
        if llm_answer:
            return ChatResponse(
                message=llm_answer,
                matched_intent="llm_grounded_fallback",
                confidence_score=0.75,
                session_id=active_session,
                category="llm_fallback",
                quick_replies=self.get_default_quick_replies(role),
                suggested_questions=[
                    "How do I upload my resume?",
                    "What is the Round 1 MCQ assessment?",
                    "How do I get technical support?"
                ],
                timestamp=timestamp,
                detected_language=detection.detected_language.value,
                writing_script=detection.script.value,
                language_confidence=detection.confidence
            )

        # 4. Fallback response for unmapped queries with localized guidance
        fallback_messages = {
            "en": (
                "I'm not quite sure I understand that question about SkillSphere. "
                "I can help with resume uploads & OCR parsing, job search & bookmarks, "
                "proctored MCQ assessments, video assessments, pipeline tracking, or live video meetings. "
                "Please try selecting one of the suggested topics below or rephrasing your question."
            ),
            "hi": (
                "मुझे SkillSphere के बारे में आपका प्रश्न पूरी तरह समझ नहीं आया। "
                "मैं रिज्यूम अपलोड और OCR पार्सिंग, नौकरी खोज, प्रॉक्टर्ड MCQ असेसमेंट, "
                "वीडियो असेसमेंट और लाइव वीडियो इंटरव्यू में सहायता कर सकता हूँ। "
                "कृपया नीचे दिए गए सुझावों में से चुनें या अपना प्रश्न पुनः लिखें।"
            ),
            "hinglish": (
                "Mujhe SkillSphere ke baare mein aapka question samajh nahi aaya. "
                "Main resume upload & OCR parsing, job search, proctored MCQ assessments, "
                "video assessments, aur live video interviews mein aapki help kar sakta hoon. "
                "Kripya neeche diye gaye topics mein se select karein ya question rephrase karein."
            ),
            "pa": (
                "ਮੈਨੂੰ SkillSphere ਬਾਰੇ ਤੁਹਾਡਾ ਸਵਾਲ ਪੂਰੀ ਤਰ੍ਹਾਂ ਸਮਝ ਨਹੀਂ ਆਇਆ। "
                "ਮੈਂ ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ, ਨੌਕਰੀਆਂ ਦੀ ਭਾਲ, ਪ੍ਰੋਕਟਰਡ MCQ ਟੈਸਟ, "
                "ਵੀਡੀਓ ਅਸੈਸਮੈਂਟ ਅਤੇ ਲਾਈਵ ਵੀਡੀਓ ਇੰਟਰਵਿਊਆਂ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ। "
                "ਕਿਰਪਾ ਕਰਕੇ ਹੇਠਾਂ ਦਿੱਤੇ ਵਿਕਲਪਾਂ ਵਿੱਚੋਂ ਚੁਣੋ।"
            ),
            "pa-Latn": (
                "Mainu SkillSphere baare tuhada swal samajh nahi aaya. "
                "Main resume upload, job search, MCQ assessments, "
                "video assessments, te live video interviews vich help kar sakda han. "
                "Please thalle ditte topics cho select karo ya swal dubara likho."
            )
        }
        fallback_msg = fallback_messages.get(target_key, fallback_messages["en"])

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
            timestamp=timestamp,
            detected_language=detection.detected_language.value,
            writing_script=detection.script.value,
            language_confidence=detection.confidence
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
