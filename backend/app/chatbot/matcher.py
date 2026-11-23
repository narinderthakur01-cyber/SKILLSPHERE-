import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from app.chatbot.language import multilingual_engine, LanguageDetectionResult

class IntentMatcher:
    """
    Modular, deterministic, rule-based intent matching engine for SkillSphere Assistant.
    Enhanced with multilingual understanding, script detection, and semantic concept alignment.
    Strictly local: operates without external LLMs or third-party inference APIs.
    """

    CONFIDENCE_THRESHOLD = 0.50

    # Common follow-up phrases that refer to the previous topic (English, Hinglish, Punjabi)
    FOLLOW_UP_PHRASES = {
        "tell me more",
        "more details",
        "can you elaborate",
        "elaborate",
        "what else",
        "explain more",
        "what next",
        "and then",
        "tell me about that",
        # Hinglish follow-ups
        "aur batao",
        "aur detail",
        "aur details",
        "kuch aur batao",
        "aur samjhao",
        # Punjabi follow-ups
        "hor dasso",
        "hor detail",
        "hor ki"
    }

    # Follow-up topic shortcuts
    TOPIC_FOLLOW_UPS = {
        "candidate_resume_upload": {
            "formats": "candidate_resume_formats",
            "file formats": "candidate_resume_formats",
            "size": "candidate_resume_formats",
            "file size": "candidate_resume_formats",
            "kitna size": "candidate_resume_formats",
            "kehdian formats": "candidate_resume_formats",
            "skill matching": "candidate_resume_intelligence",
            "how does it score": "candidate_resume_intelligence",
            "how does matching work": "candidate_resume_intelligence",
            "score": "candidate_resume_intelligence",
            "scoring": "candidate_resume_intelligence",
            "skills": "candidate_resume_intelligence"
        },
        "candidate_job_search": {
            "apply": "candidate_apply_job",
            "save": "candidate_save_jobs",
            "bookmark": "candidate_save_jobs",
            "status": "candidate_application_status",
            "tracking": "candidate_application_status"
        },
        "candidate_apply_job": {
            "status": "candidate_application_status",
            "tracking": "candidate_application_status",
            "recruiter message": "candidate_messaging",
            "chat": "candidate_messaging"
        },
        "candidate_mcq_assessment": {
            "proctoring": "candidate_proctoring",
            "anti cheat": "candidate_proctoring",
            "webcam": "candidate_proctoring",
            "camera": "candidate_proctoring",
            "tab switch": "candidate_proctoring",
            "video": "candidate_video_assessment",
            "interview": "candidate_live_interview"
        },
        "recruiter_create_job": {
            "manage": "recruiter_job_management",
            "pipeline": "recruiter_kanban_pipeline",
            "applicants": "recruiter_kanban_pipeline",
            "candidates": "recruiter_kanban_pipeline",
            "questions": "recruiter_question_bank"
        },
        "recruiter_kanban_pipeline": {
            "resumes": "recruiter_resume_review",
            "interview": "recruiter_schedule_interview",
            "schedule": "recruiter_schedule_interview",
            "test results": "recruiter_mcq_review",
            "videos": "recruiter_video_review"
        },
        "general_login": {
            "password": "general_password_reset",
            "reset": "general_password_reset",
            "forgot": "general_password_reset",
            "verify": "candidate_email_verification",
            "verification": "candidate_email_verification"
        }
    }

    # Ambiguous broad keywords requiring safe clarification
    AMBIGUOUS_QUERIES = {
        "status": {
            "title": "Which status would you like to check?",
            "options": [
                {"label": "Job Application Status", "query": "How do I track my application status?", "topic": "candidate_application_status"},
                {"label": "Candidate Pipeline Status", "query": "How does the Kanban pipeline work?", "topic": "recruiter_kanban_pipeline"},
                {"label": "Job Requisition Status", "query": "How do I view, edit, or close existing job postings?", "topic": "recruiter_job_management"}
            ]
        },
        "upload": {
            "title": "What would you like to upload?",
            "options": [
                {"label": "Upload Resume", "query": "How do I upload my resume?", "topic": "candidate_resume_upload"},
                {"label": "Video Assessment", "query": "How does the one-way asynchronous video assessment work?", "topic": "candidate_video_assessment"},
                {"label": "Question Bank Import", "query": "How do I manage the Question Bank for technical assessments?", "topic": "recruiter_question_bank"}
            ]
        },
        "interview": {
            "title": "What interview information are you looking for?",
            "options": [
                {"label": "Join Live Interview", "query": "How do I join a live video interview?", "topic": "candidate_live_interview"},
                {"label": "Schedule Interview (Recruiter)", "query": "How do I schedule and host a LiveKit live video interview?", "topic": "recruiter_schedule_interview"},
                {"label": "Video Assessment", "query": "How does the one-way asynchronous video assessment work?", "topic": "candidate_video_assessment"}
            ]
        }
    }

    def __init__(self, faqs: List[Dict[str, Any]]):
        self.faqs = faqs

    @staticmethod
    def normalize_text(text: str) -> str:
        """Lowercase, strip extraneous punctuation, collapse whitespace, and normalize variants."""
        if not text:
            return ""
        return multilingual_engine.normalize_text(text)

    def filter_by_role(self, role: Optional[str]) -> List[Dict[str, Any]]:
        """Filter FAQs by user role to prevent unauthorized or irrelevant information leak."""
        if not role:
            # Default / unauthenticated: return general FAQs only
            return [f for f in self.faqs if "JOB_SEEKER" in f.get("roles", []) and "RECRUITER" in f.get("roles", [])]
        
        normalized_role = role.upper()
        if normalized_role == "ADMIN":
            return self.faqs
        
        return [f for f in self.faqs if normalized_role in [r.upper() for r in f.get("roles", [])]]

    def match(
        self,
        query: str,
        role: Optional[str] = None,
        context_topic: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], float, str]:
        """
        Match a user query against the eligible FAQ knowledge base with multilingual awareness.
        Returns:
            Tuple of (Matched_FAQ_Dict_or_None, confidence_score, match_type)
        """
        detection = multilingual_engine.process(query)
        norm_query = detection.normalized_text
        if not norm_query:
            return None, 0.0, "empty"

        eligible_faqs = self.filter_by_role(role)
        if not eligible_faqs:
            return None, 0.0, "no_eligible_faqs"

        # 1. Check for Standalone Ambiguous Broad Keywords (e.g. 'status', 'upload', 'interview')
        ambiguous_key = None
        if not context_topic:
            if norm_query in self.AMBIGUOUS_QUERIES:
                ambiguous_key = norm_query
            elif detection.aligned_query and detection.aligned_query.strip() in self.AMBIGUOUS_QUERIES:
                ambiguous_key = detection.aligned_query.strip()
            elif len(norm_query.split()) <= 2:
                for kw in detection.intent_keywords:
                    if kw in self.AMBIGUOUS_QUERIES:
                        ambiguous_key = kw
                        break

        if ambiguous_key and ambiguous_key in self.AMBIGUOUS_QUERIES:
            clarification = self.AMBIGUOUS_QUERIES[ambiguous_key]
            allowed_opts = []
            for opt in clarification["options"]:
                target_intent = opt["topic"]
                if any(f.get("intent") == target_intent for f in eligible_faqs):
                    allowed_opts.append(opt)
            if allowed_opts:
                clarification_faq = {
                    "id": f"clarify_{ambiguous_key}",
                    "intent": "ambiguous_clarification",
                    "category": "clarification",
                    "title": clarification["title"],
                    "response": f"Your question is a bit broad. {clarification['title']} Please select an option below:",
                    "quick_replies": allowed_opts,
                    "related_questions": [opt["query"] for opt in allowed_opts],
                    "multilingual_responses": {
                        "en": f"Your question is a bit broad. {clarification['title']} Please select an option below:",
                        "hi": f"आपका प्रश्न थोड़ा सामान्य है। {clarification['title']} कृपया नीचे दिए गए विकल्पों में से एक चुनें:",
                        "hinglish": f"Aapka question thoda general hai. {clarification['title']} Kripya neeche diye gaye options mein se select karein:",
                        "pa": f"ਤੁਹਾਡਾ ਸਵਾਲ ਕਾਫ਼ੀ ਆਮ ਹੈ। {clarification['title']} ਕਿਰਪਾ ਕਰਕੇ ਹੇਠਾਂ ਦਿੱਤੇ ਵਿਕਲਪਾਂ ਵਿੱਚੋਂ ਚੁਣੋ:",
                        "pa-Latn": f"Tuhada swal thoda broad hai. {clarification['title']} Please thalle ditte options cho select karo:"
                    }
                }
                return clarification_faq, 0.85, "ambiguous_clarification"

        # 2. Check for Contextual Follow-Up Phrases
        if context_topic and (norm_query in self.FOLLOW_UP_PHRASES or any(p in norm_query for p in self.FOLLOW_UP_PHRASES)):
            # Look up context topic FAQ
            context_faq = next((f for f in eligible_faqs if f.get("intent") == context_topic), None)
            if context_faq:
                return context_faq, 0.95, "context_followup"

        # 3. Check for Contextual Shortcut Phrases (e.g. "formats" after asking about resume upload)
        if context_topic and context_topic in self.TOPIC_FOLLOW_UPS:
            subtopics = self.TOPIC_FOLLOW_UPS[context_topic]
            for phrase, target_intent in subtopics.items():
                if phrase in norm_query:
                    target_faq = next((f for f in eligible_faqs if f.get("intent") == target_intent), None)
                    if target_faq:
                        return target_faq, 0.90, "context_shortcut"

        best_faq = None
        second_faq = None
        highest_score = 0.0
        second_highest_score = 0.0
        match_type = "none"

        query_tokens = set(norm_query.split())
        if detection.intent_keywords:
            query_tokens = query_tokens.union(set(detection.intent_keywords))

        for faq in eligible_faqs:
            score = 0.0

            # A. Exact match against sample questions
            sample_questions = [self.normalize_text(q) for q in faq.get("sample_questions", [])]
            if norm_query in sample_questions:
                return faq, 1.0, "exact_sample_match"

            if detection.aligned_query and detection.aligned_query in sample_questions:
                return faq, 0.98, "exact_aligned_match"

            # B. Sequence similarity against sample questions
            max_sim = 0.0
            for sq in sample_questions:
                sim = difflib.SequenceMatcher(None, norm_query, sq).ratio()
                if detection.aligned_query:
                    aligned_sim = difflib.SequenceMatcher(None, detection.aligned_query, sq).ratio()
                    sim = max(sim, aligned_sim)
                if sim > max_sim:
                    max_sim = sim
            
            # C. Keyword & synonym matching
            keywords = [self.normalize_text(k) for k in faq.get("keywords", [])]
            synonyms = [self.normalize_text(s) for s in faq.get("synonyms", [])]
            all_terms = keywords + synonyms

            # Count multi-word keyword matches
            multi_word_hits = 0
            for term in all_terms:
                if " " in term and (term in norm_query or (detection.aligned_query and term in detection.aligned_query)):
                    multi_word_hits += 1

            # Count token overlap
            single_word_terms = {t for t in all_terms if " " not in t}
            overlap = query_tokens.intersection(single_word_terms)

            term_score = 0.0
            if query_tokens:
                term_score = (len(overlap) * 0.35) + (multi_word_hits * 0.40)
                term_score = min(term_score, 1.0)

            # Combined weighted score: 50% sequence similarity + 50% term matching
            score = (max_sim * 0.50) + (term_score * 0.50)

            # Boost if high similarity and keyword overlap, or multiple key domain keyword matches
            if max_sim >= 0.60 and len(overlap) >= 1:
                score = min(score + 0.15, 0.98)
            elif len(overlap) >= 2:
                score = min(score + 0.15, 0.98)

            if score > highest_score:
                second_highest_score = highest_score
                second_faq = best_faq
                highest_score = score
                best_faq = faq
                match_type = "rule_scored"
            elif score > second_highest_score:
                second_highest_score = score
                second_faq = faq

        # 4. Ambiguity Safety: If top two matches are nearly tied and confidence is moderate, clarify
        if (
            highest_score >= self.CONFIDENCE_THRESHOLD
            and highest_score < 0.65
            and second_faq is not None
            and (highest_score - second_highest_score) < 0.04
            and best_faq is not None
        ):
            clarification_options = [
                {"label": best_faq.get("title", "Option A")[:40], "query": best_faq.get("sample_questions", [""])[0], "topic": best_faq.get("intent")},
                {"label": second_faq.get("title", "Option B")[:40], "query": second_faq.get("sample_questions", [""])[0], "topic": second_faq.get("intent")}
            ]
            clarification_faq = {
                "id": "clarify_tied_matches",
                "intent": "ambiguous_clarification",
                "category": "clarification",
                "title": "Which of these topics are you inquiring about?",
                "response": "Your question could relate to multiple topics. Did you mean:",
                "quick_replies": clarification_options,
                "related_questions": [opt["query"] for opt in clarification_options],
                "multilingual_responses": {
                    "en": "Your question could relate to multiple topics. Did you mean:",
                    "hi": "आपका प्रश्न कई विषयों से संबंधित हो सकता है। क्या आपका तात्पर्य इससे था:",
                    "hinglish": "Aapka question multiple topics se related ho sakta hai. Kya aap inme se kisi baare mein puch rahe hain:",
                    "pa": "ਤੁਹਾਡਾ ਸਵਾਲ ਕਈ ਵਿਸ਼ਿਆਂ ਨਾਲ ਸੰਬੰਧਿਤ ਹੋ ਸਕਦਾ ਹੈ। ਕੀ ਤੁਹਾਡਾ ਮਤਲਬ ਸੀ:",
                    "pa-Latn": "Tuhada swal multiple topics naal related ho sakda hai. Ki tuhada matlab eh si:"
                }
            }
            return clarification_faq, 0.80, "ambiguous_clarification"

        # Apply confidence threshold
        if highest_score >= self.CONFIDENCE_THRESHOLD and best_faq:
            return best_faq, round(highest_score, 2), match_type

        return None, round(highest_score, 2), "fallback"
