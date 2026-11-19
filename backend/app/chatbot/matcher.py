import re
import difflib
from typing import List, Dict, Any, Optional, Tuple

class IntentMatcher:
    """
    Modular, deterministic, rule-based intent matching engine for SkillSphere Assistant.
    Strictly local: operates without external LLMs or third-party inference APIs.
    """

    CONFIDENCE_THRESHOLD = 0.50

    # Common follow-up phrases that refer to the previous topic
    FOLLOW_UP_PHRASES = {
        "tell me more",
        "more details",
        "can you elaborate",
        "elaborate",
        "what else",
        "explain more",
        "what next",
        "and then",
        "tell me about that"
    }

    # Follow-up topic shortcuts
    TOPIC_FOLLOW_UPS = {
        "candidate_resume_upload": {
            "formats": "candidate_resume_formats",
            "file formats": "candidate_resume_formats",
            "size": "candidate_resume_formats",
            "file size": "candidate_resume_formats",
            "skill matching": "candidate_resume_intelligence",
            "how does it score": "candidate_resume_intelligence",
            "how does matching work": "candidate_resume_intelligence",
        },
        "candidate_mcq_assessment": {
            "proctoring": "candidate_proctoring",
            "anti cheat": "candidate_proctoring",
            "webcam": "candidate_proctoring",
            "tab switch": "candidate_proctoring",
        },
        "recruiter_create_job": {
            "manage": "recruiter_job_management",
            "pipeline": "recruiter_kanban_pipeline",
            "applicants": "recruiter_kanban_pipeline",
        },
        "recruiter_kanban_pipeline": {
            "resumes": "recruiter_resume_review",
            "interview": "recruiter_schedule_interview",
            "schedule": "recruiter_schedule_interview",
        }
    }

    def __init__(self, faqs: List[Dict[str, Any]]):
        self.faqs = faqs

    @staticmethod
    def normalize_text(text: str) -> str:
        """Lowercase, strip extraneous punctuation, and collapse multiple whitespaces."""
        if not text:
            return ""
        # Lowercase
        cleaned = text.lower().strip()
        # Remove special characters except alphanumeric, hyphen, and spaces
        cleaned = re.sub(r"[^\w\s\-]", " ", cleaned)
        # Collapse multiple whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

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
        Match a user query against the eligible FAQ knowledge base.
        Returns:
            Tuple of (Matched_FAQ_Dict_or_None, confidence_score, match_type)
        """
        norm_query = self.normalize_text(query)
        if not norm_query:
            return None, 0.0, "empty"

        eligible_faqs = self.filter_by_role(role)
        if not eligible_faqs:
            return None, 0.0, "no_eligible_faqs"

        # 1. Check for Contextual Follow-Up Phrases
        if context_topic and (norm_query in self.FOLLOW_UP_PHRASES or any(p in norm_query for p in self.FOLLOW_UP_PHRASES)):
            # Look up context topic FAQ
            context_faq = next((f for f in eligible_faqs if f.get("intent") == context_topic), None)
            if context_faq:
                return context_faq, 0.95, "context_followup"

        # 2. Check for Contextual Shortcut Phrases (e.g. "formats" after asking about resume upload)
        if context_topic and context_topic in self.TOPIC_FOLLOW_UPS:
            subtopics = self.TOPIC_FOLLOW_UPS[context_topic]
            for phrase, target_intent in subtopics.items():
                if phrase in norm_query:
                    target_faq = next((f for f in eligible_faqs if f.get("intent") == target_intent), None)
                    if target_faq:
                        return target_faq, 0.90, "context_shortcut"

        best_faq = None
        highest_score = 0.0
        match_type = "none"

        query_tokens = set(norm_query.split())

        for faq in eligible_faqs:
            score = 0.0

            # A. Exact match against sample questions
            sample_questions = [self.normalize_text(q) for q in faq.get("sample_questions", [])]
            if norm_query in sample_questions:
                return faq, 1.0, "exact_sample_match"

            # B. Sequence similarity against sample questions
            max_sim = 0.0
            for sq in sample_questions:
                sim = difflib.SequenceMatcher(None, norm_query, sq).ratio()
                if sim > max_sim:
                    max_sim = sim
            
            # C. Keyword & synonym matching
            keywords = [self.normalize_text(k) for k in faq.get("keywords", [])]
            synonyms = [self.normalize_text(s) for s in faq.get("synonyms", [])]
            all_terms = keywords + synonyms

            # Count multi-word keyword matches
            multi_word_hits = 0
            for term in all_terms:
                if " " in term and term in norm_query:
                    multi_word_hits += 1

            # Count token overlap
            single_word_terms = {t for t in all_terms if " " not in t}
            overlap = query_tokens.intersection(single_word_terms)

            term_score = 0.0
            if query_tokens:
                term_score = (len(overlap) * 0.25) + (multi_word_hits * 0.40)
                term_score = min(term_score, 1.0)

            # Combined weighted score: 50% sequence similarity + 50% term matching
            score = (max_sim * 0.50) + (term_score * 0.50)

            # Boost if both high similarity and keyword overlap
            if max_sim >= 0.60 and len(overlap) >= 1:
                score = min(score + 0.15, 0.98)

            if score > highest_score:
                highest_score = score
                best_faq = faq
                match_type = "rule_scored"

        # Apply confidence threshold
        if highest_score >= self.CONFIDENCE_THRESHOLD and best_faq:
            return best_faq, round(highest_score, 2), match_type

        return None, round(highest_score, 2), "fallback"
