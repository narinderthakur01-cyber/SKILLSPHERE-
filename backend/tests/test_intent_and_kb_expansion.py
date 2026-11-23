"""
Stage 2 Test Suite: Intent Recognition, Knowledge Base Expansion & Contextual Conversation.
Tests multilingual response retrieval, language preference overrides, ambiguous queries,
contextual multi-turn follow-ups, role isolation, and backward compatibility across all 30 FAQs.
"""

import json
from pathlib import Path
import pytest

from app.chatbot.language import multilingual_engine, SupportedLanguage, WritingScript
from app.chatbot.matcher import IntentMatcher
from app.chatbot.service import ChatbotService
from app.schemas.chatbot_schemas import ChatResponse, FAQItem


@pytest.fixture
def service() -> ChatbotService:
    return ChatbotService()


@pytest.fixture
def matcher(service) -> IntentMatcher:
    return service.matcher


@pytest.fixture
def raw_kb() -> dict:
    kb_path = Path(__file__).resolve().parent.parent / "app" / "chatbot" / "knowledge_base.json"
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# 1. KNOWLEDGE BASE INTEGRITY & BACKWARD COMPATIBILITY
# ============================================================================

def test_kb_contains_all_30_original_faqs(raw_kb):
    """Ensure exactly 30 FAQs exist and all original IDs are intact."""
    faqs = raw_kb.get("faqs", [])
    assert len(faqs) == 30

    expected_ids = {
        "faq_cand_01", "faq_cand_02", "faq_cand_03", "faq_cand_04",
        "faq_cand_05", "faq_cand_06", "faq_cand_07", "faq_cand_08",
        "faq_cand_09", "faq_cand_10", "faq_cand_11", "faq_cand_12",
        "faq_cand_13",
        "faq_rec_01", "faq_rec_02", "faq_rec_03", "faq_rec_04",
        "faq_rec_05", "faq_rec_06", "faq_rec_07", "faq_rec_08",
        "faq_rec_09",
        "faq_gen_01", "faq_gen_02", "faq_gen_03", "faq_gen_04",
        "faq_gen_05", "faq_gen_06", "faq_gen_07", "faq_gen_08"
    }
    actual_ids = {faq["id"] for faq in faqs}
    assert actual_ids == expected_ids


def test_all_faqs_have_all_five_multilingual_responses(raw_kb):
    """Ensure every FAQ contains complete translations for en, hi, hinglish, pa, pa-Latn."""
    faqs = raw_kb.get("faqs", [])
    required_keys = {"en", "hi", "hinglish", "pa", "pa-Latn"}

    for faq in faqs:
        ml = faq.get("multilingual_responses")
        assert ml is not None, f"FAQ {faq['id']} missing multilingual_responses dict"
        assert set(ml.keys()) == required_keys, f"FAQ {faq['id']} missing expected lang keys: {set(ml.keys())}"
        for lang, text in ml.items():
            assert isinstance(text, str) and len(text.strip()) > 10, f"FAQ {faq['id']} has empty translation for {lang}"
        # English multilingual response must strictly match canonical response
        assert ml["en"].strip() == faq["response"].strip()


def test_technical_entities_preserved_in_all_translations(raw_kb):
    """Verify that route paths, technical specs, and subsystem names are preserved verbatim."""
    faqs = {f["id"]: f for f in raw_kb.get("faqs", [])}

    # Resume upload (faq_cand_01): PDF, DOCX, 10MB, /dashboard?tab=resumes
    resume_faq = faqs["faq_cand_01"]["multilingual_responses"]
    for lang in ["en", "hi", "hinglish", "pa", "pa-Latn"]:
        resp = resume_faq[lang]
        assert "PDF" in resp
        assert "DOCX" in resp
        assert "10MB" in resp or "10 MB" in resp
        assert "/dashboard?tab=resumes" in resp

    # Recruiter post job (faq_rec_01): /recruiter
    job_faq = faqs["faq_rec_01"]["multilingual_responses"]
    for lang in ["en", "hi", "hinglish", "pa", "pa-Latn"]:
        resp = job_faq[lang]
        assert "/recruiter" in resp

    # Practice interview (faq_cand_11): LiveKit, webcam
    interview_faq = faqs["faq_cand_11"]["multilingual_responses"]
    for lang in ["en", "hi", "hinglish", "pa", "pa-Latn"]:
        resp = interview_faq[lang]
        assert "LiveKit" in resp or "webcam" in resp or "/dashboard?tab=interviews" in resp


# ============================================================================
# 2. MULTILINGUAL RESPONSE RETRIEVAL (AUTOMATIC DETECTION)
# ============================================================================

def test_multilingual_response_automatic_detection_hindi(service):
    """Hindi Devanagari query receives Hindi response."""
    response = service.process_message(
        message="मैं अपना रिज्यूमे कैसे अपलोड करूं?",
        role="JOB_SEEKER",
    )
    assert response.matched_intent == "candidate_resume_upload"
    assert response.confidence_score >= 0.50
    # Response message should be in Hindi Devanagari
    assert "रिज्यूम" in response.message or "अपलोड" in response.message
    assert "/dashboard?tab=resumes" in response.message


def test_multilingual_response_automatic_detection_hinglish(service):
    """Hinglish query receives Hinglish response."""
    response = service.process_message(
        message="resume kaise upload karein SkillSphere par?",
        role="JOB_SEEKER",
    )
    assert response.matched_intent == "candidate_resume_upload"
    assert response.confidence_score >= 0.50
    assert "Resume upload karne ke liye" in response.message or "dashboard" in response.message


def test_multilingual_response_automatic_detection_punjabi_gurmukhi(service):
    """Punjabi Gurmukhi query receives Punjabi response."""
    response = service.process_message(
        message="ਮੈਂ ਆਪਣਾ ਰੈਜ਼ਿਊਮੇ ਕਿਵੇਂ ਅੱਪਲੋਡ ਕਰਾਂ?",
        role="JOB_SEEKER",
    )
    assert response.matched_intent == "candidate_resume_upload"
    assert response.confidence_score >= 0.50
    assert "ਰਿਜ਼ਿਊਮ" in response.message or "ਅਪਲੋਡ" in response.message


def test_multilingual_response_automatic_detection_roman_punjabi(service):
    """Roman Punjabi query receives Roman Punjabi response."""
    response = service.process_message(
        message="main apna resume kive upload kara?",
        role="JOB_SEEKER",
    )
    assert response.matched_intent == "candidate_resume_upload"
    assert response.confidence_score >= 0.50
    assert "Resume upload karan layi" in response.message or "dashboard" in response.message


def test_multilingual_response_automatic_detection_english(service):
    """English query receives standard English response."""
    response = service.process_message(
        message="How do I upload my resume?",
        role="JOB_SEEKER",
    )
    assert response.matched_intent == "candidate_resume_upload"
    assert response.confidence_score >= 0.70
    assert "To upload your resume in SkillSphere, go to your Job Seeker Dashboard" in response.message


# ============================================================================
# 3. EXPLICIT LANGUAGE PREFERENCE OVERRIDES
# ============================================================================

def test_explicit_language_preference_overrides_detection(service):
    """When language_preference is provided, response must match it regardless of input language."""
    # 1. English query, but language_preference='hi' -> Hindi response
    resp_hi = service.process_message(
        message="How do I upload my resume?",
        role="JOB_SEEKER",
        language_preference="hi",
    )
    assert resp_hi.matched_intent == "candidate_resume_upload"
    assert "रिज्यूम" in resp_hi.message

    # 2. Hindi query, but language_preference='en' -> English response
    resp_en = service.process_message(
        message="मैं अपना रिज्यूमे कैसे अपलोड करूं?",
        role="JOB_SEEKER",
        language_preference="en",
    )
    assert resp_en.matched_intent == "candidate_resume_upload"
    assert "To upload your resume in SkillSphere" in resp_en.message

    # 3. English query, but language_preference='hinglish' -> Hinglish response
    resp_hing = service.process_message(
        message="How do I upload my resume?",
        role="JOB_SEEKER",
        language_preference="hinglish",
    )
    assert resp_hing.matched_intent == "candidate_resume_upload"
    assert "resume upload karne ke liye" in resp_hing.message.lower()

    # 4. English query, but language_preference='pa' -> Punjabi response
    resp_pa = service.process_message(
        message="How do I upload my resume?",
        role="JOB_SEEKER",
        language_preference="pa",
    )
    assert resp_pa.matched_intent == "candidate_resume_upload"
    assert "ਰਿਜ਼ਿਊਮ" in resp_pa.message or "ਅਪਲੋਡ" in resp_pa.message

    # 5. English query, but language_preference='pa-Latn' -> Roman Punjabi response
    resp_pa_latn = service.process_message(
        message="How do I upload my resume?",
        role="JOB_SEEKER",
        language_preference="pa-Latn",
    )
    assert resp_pa_latn.matched_intent == "candidate_resume_upload"
    assert "resume upload karan layi" in resp_pa_latn.message.lower()


# ============================================================================
# 4. AMBIGUOUS QUERY HANDLING & CLARIFICATION
# ============================================================================

def test_standalone_ambiguous_queries_trigger_clarification(matcher):
    """Vague single-keyword queries must trigger clarification instead of confident wrong FAQ."""
    # 'status' is ambiguous
    matched_faq, score, match_type = matcher.match("status", role="JOB_SEEKER")
    assert matched_faq is not None
    assert match_type == "ambiguous_clarification"
    assert matched_faq.get("intent") == "ambiguous_clarification"
    assert len(matched_faq.get("quick_replies", [])) > 0

    # 'upload' is ambiguous
    matched_faq_up, score_up, match_type_up = matcher.match("upload", role="JOB_SEEKER")
    assert matched_faq_up is not None
    assert match_type_up == "ambiguous_clarification"
    assert matched_faq_up.get("intent") == "ambiguous_clarification"

    # 'interview' is ambiguous
    matched_faq_int, score_int, match_type_int = matcher.match("interview", role="JOB_SEEKER")
    assert matched_faq_int is not None
    assert match_type_int == "ambiguous_clarification"
    assert matched_faq_int.get("intent") == "ambiguous_clarification"


def test_ambiguity_clarification_in_service(service):
    """ChatbotService returns user-facing clarification message and options."""
    resp = service.process_message("status", role="JOB_SEEKER")
    assert resp.matched_intent == "ambiguous_clarification"
    assert "broad" in resp.message.lower() or "select an option" in resp.message.lower() or "clarify" in resp.message.lower()
    assert len(resp.quick_replies) >= 1


def test_ambiguous_queries_in_hindi_and_punjabi(service):
    """Multilingual ambiguous queries also trigger clarification."""
    # Hindi "स्टेटस"
    resp_hi = service.process_message("स्टेटस", role="JOB_SEEKER")
    assert resp_hi.matched_intent == "ambiguous_clarification"
    assert len(resp_hi.quick_replies) >= 1

    # Punjabi "ਸਟੇਟਸ"
    resp_pa = service.process_message("ਸਟੇਟਸ", role="JOB_SEEKER")
    assert resp_pa.matched_intent == "ambiguous_clarification"
    assert len(resp_pa.quick_replies) >= 1


# ============================================================================
# 5. CONTEXTUAL MULTI-TURN FOLLOW-UPS
# ============================================================================

def test_contextual_follow_up_within_topic(matcher):
    """Follow-up questions reference previous context topic."""
    # Follow up with short "formats" referencing candidate_resume_upload
    matched_faq, score, match_type = matcher.match(
        "formats",
        role="JOB_SEEKER",
        context_topic="candidate_resume_upload",
    )
    assert matched_faq is not None
    assert match_type == "context_shortcut"
    # Should resolve to resume formats topic
    assert "candidate_resume_formats" in matched_faq.get("intent") or "candidate_resume_upload" in matched_faq.get("intent")


def test_topic_switching_clears_or_overrides_follow_up(matcher):
    """When user clearly asks about a new topic, it switches cleanly."""
    matched_faq, score, match_type = matcher.match(
        "How do I reset my password?",
        role="JOB_SEEKER",
        context_topic="candidate_resume_upload",
    )
    assert matched_faq is not None
    assert matched_faq.get("intent") == "general_password_reset"


# ============================================================================
# 6. ROLE ISOLATION ACROSS LANGUAGES
# ============================================================================

def test_candidate_cannot_access_recruiter_faqs_in_any_language(service):
    """Job seeker asking recruiter questions receives fallback or role-restricted response."""
    # 1. English
    resp_en = service.process_message("How do I post a new job opening?", role="JOB_SEEKER")
    assert resp_en.matched_intent != "recruiter_create_job"

    # 2. Hindi
    resp_hi = service.process_message("नयी नौकरी की रिक्ति कैसे पोस्ट करें?", role="JOB_SEEKER")
    assert resp_hi.matched_intent != "recruiter_create_job"

    # 3. Hinglish
    resp_hing = service.process_message("recruiter portal par job kaise post karein?", role="JOB_SEEKER")
    assert resp_hing.matched_intent != "recruiter_create_job"

    # 4. Punjabi
    resp_pa = service.process_message("ਨਵੀਂ ਨੌਕਰੀ ਕਿਵੇਂ ਪੋਸਟ ਕਰਨੀ ਹੈ?", role="JOB_SEEKER")
    assert resp_pa.matched_intent != "recruiter_create_job"


def test_recruiter_can_access_recruiter_faqs_in_all_languages(service):
    """Recruiter asking recruiter questions matches recruiter FAQ."""
    # 1. English
    resp_en = service.process_message("How do I post a new job?", role="RECRUITER")
    assert resp_en.matched_intent == "recruiter_create_job"

    # 2. Hindi
    resp_hi = service.process_message("नौकरी कैसे पोस्ट करें?", role="RECRUITER")
    assert resp_hi.matched_intent == "recruiter_create_job"

    # 3. Punjabi
    resp_pa = service.process_message("ਨੌਕਰੀ ਕਿਵੇਂ ਪੋਸਟ ਕਰਨੀ ਹੈ?", role="RECRUITER")
    assert resp_pa.matched_intent == "recruiter_create_job"


# ============================================================================
# 7. MULTILINGUAL FALLBACK LOCALIZATION
# ============================================================================

def test_unmatched_query_returns_localized_fallback(service):
    """Unmatched queries receive fallback message in the detected language or preferred language."""
    # Hindi unmatched query
    resp_hi = service.process_message(
        message="मौसम आज कैसा रहेगा SkillSphere पर?",
        role="JOB_SEEKER",
    )
    assert resp_hi.matched_intent == "fallback"
    # Hindi fallback should be in Devanagari Hindi
    assert "सहायता" in resp_hi.message or "प्रश्न" in resp_hi.message or "SkillSphere" in resp_hi.message

    # Punjabi Gurmukhi unmatched query
    resp_pa = service.process_message(
        message="ਅੱਜ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਹੈ?",
        role="JOB_SEEKER",
    )
    assert resp_pa.matched_intent == "fallback"
    assert "ਮਦਦ" in resp_pa.message or "ਸਵਾਲ" in resp_pa.message or "SkillSphere" in resp_pa.message

    # Hinglish unmatched query
    resp_hing = service.process_message(
        message="aaj ka mausam kaisa hai bhai?",
        role="JOB_SEEKER",
    )
    assert resp_hing.matched_intent == "fallback"
    assert "help" in resp_hing.message.lower() or "question" in resp_hing.message.lower() or "samajh" in resp_hing.message.lower()
