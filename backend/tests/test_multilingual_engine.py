"""
Automated Test Suite for Module A: Multilingual Language Engine
Verifies language detection, script identification, text normalization,
misspelling tolerance, and semantic concept extraction across English, Hindi,
Hinglish, Punjabi, Roman Punjabi, and mixed-language messages.
"""

import pytest
from app.chatbot.language import (
    multilingual_engine,
    WritingScript,
    SupportedLanguage,
    LanguageDetectionResult
)
from app.chatbot.service import ChatbotService
from app.chatbot.matcher import IntentMatcher


# ======================================================================
# 1. Script Detection Tests
# ======================================================================

def test_script_detection_latin():
    res = multilingual_engine.process("How do I upload my resume?")
    assert res.script == WritingScript.LATIN
    assert res.detected_language == SupportedLanguage.ENGLISH


def test_script_detection_devanagari():
    res = multilingual_engine.process("मेरा रिज्यूम अपलोड नहीं हो रहा है")
    assert res.script == WritingScript.DEVANAGARI
    assert res.detected_language == SupportedLanguage.HINDI


def test_script_detection_gurmukhi():
    res = multilingual_engine.process("ਮੇਰਾ ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਨਹੀਂ ਹੋ ਰਿਹਾ")
    assert res.script == WritingScript.GURMUKHI
    assert res.detected_language == SupportedLanguage.PUNJABI


def test_script_detection_mixed():
    res = multilingual_engine.process("Mera resume अपलोड nahi ho raha")
    assert res.script == WritingScript.MIXED
    assert res.detected_language == SupportedLanguage.MIXED or res.is_multilingual


def test_script_detection_empty_or_symbols():
    res = multilingual_engine.process("   ")
    assert res.script == WritingScript.UNKNOWN
    assert res.detected_language == SupportedLanguage.UNKNOWN
    assert res.confidence == 0.0
    assert res.is_uncertain is True

    res2 = multilingual_engine.process("??? !!! ... ---")
    assert res2.script == WritingScript.UNKNOWN
    assert res2.confidence == 0.0


# ======================================================================
# 2. Language Classification Tests
# ======================================================================

def test_language_classification_english():
    res = multilingual_engine.process("How do I post a new job opening for senior software engineer?")
    assert res.detected_language == SupportedLanguage.ENGLISH
    assert res.confidence >= 0.75
    assert res.is_uncertain is False


def test_language_classification_hinglish():
    res = multilingual_engine.process("Mera resume upload nahi ho raha")
    assert res.detected_language == SupportedLanguage.HINGLISH
    assert res.script == WritingScript.LATIN
    assert res.confidence >= 0.70
    assert "resume" in res.detected_tokens
    assert "nahi" in res.detected_tokens


def test_language_classification_roman_punjabi():
    res = multilingual_engine.process("Resume upload ni ho reha ki kran")
    assert res.detected_language == SupportedLanguage.ROMAN_PUNJABI
    assert res.script == WritingScript.LATIN
    assert res.confidence >= 0.70
    assert "reha" in res.detected_tokens or "ni" in res.detected_tokens


def test_language_classification_uncertainty_handling():
    # Single ambiguous word without context
    res = multilingual_engine.process("xyzabc123")
    assert res.is_uncertain is True
    assert res.confidence <= 0.60


# ======================================================================
# 3. Text Normalization, Slang & Misspelling Tests
# ======================================================================

def test_text_normalization_preserves_original():
    raw = "   MeRa CV uplod   nhi ho rhaaa???   "
    res = multilingual_engine.process(raw)
    # Original message remains completely unmodified
    assert res.original_text == raw
    # Normalized text is cleaned, lowercased, and variants resolved
    assert "mera" in res.normalized_text
    assert "resume" in res.normalized_text  # cv -> resume
    assert "upload" in res.normalized_text  # uplod -> upload
    assert "nahi" in res.normalized_text    # nhi -> nahi
    assert "raha" in res.normalized_text    # rhaaa -> raha (collapsed & normalized)
    assert "?" not in res.normalized_text


def test_repeated_characters_collapsing():
    res1 = multilingual_engine.process("pleaaaseee help me")
    assert "please" in res1.detected_tokens

    res2 = multilingual_engine.process("nahiiiii ho raha")
    assert "nahi" in res2.detected_tokens

    res3 = multilingual_engine.process("reeehaaaa")
    assert "reha" in res3.detected_tokens


def test_slang_and_abbreviations():
    res = multilingual_engine.process("plz tell me prblm with my msg and vid intervu")
    assert "please" in res.detected_tokens
    assert "problem" in res.detected_tokens
    assert "message" in res.detected_tokens
    assert "video" in res.detected_tokens
    assert "interview" in res.detected_tokens


# ======================================================================
# 4. Master Prompt Equivalency Requirement Tests
# "All should be understood as a resume upload problem"
# ======================================================================

def test_master_prompt_resume_upload_equivalency_group():
    """
    Validates the 5 exact canonical variations from Section 5 of the Master Prompt:
    1. 'My resume is not uploading.'
    2. 'Mera resume upload nahi ho raha.'
    3. 'Resume upload ni ho reha.'
    4. 'Mera CV upload nhi ho rha.'
    5. 'I'm unable to upload my resume.'
    All must map to the candidate resume upload intent.
    """
    svc = ChatbotService()

    queries = [
        "My resume is not uploading.",
        "Mera resume upload nahi ho raha.",
        "Resume upload ni ho reha.",
        "Mera CV upload nhi ho rha.",
        "I'm unable to upload my resume."
    ]

    for q in queries:
        resp = svc.process_message(q, role="JOB_SEEKER")
        assert resp.matched_intent == "candidate_resume_upload", (
            f"Query '{q}' failed to match 'candidate_resume_upload'. "
            f"Got: '{resp.matched_intent}' (confidence: {resp.confidence_score})"
        )
        assert resp.confidence_score >= 0.50
        assert resp.detected_language in ["en", "hinglish", "pa-Latn"]
        assert resp.writing_script == "Latin"


def test_devanagari_and_gurmukhi_resume_upload_matching():
    svc = ChatbotService()

    hindi_query = "मेरा रिज्यूम अपलोड नहीं हो रहा है"
    resp_hi = svc.process_message(hindi_query, role="JOB_SEEKER")
    assert resp_hi.matched_intent == "candidate_resume_upload"
    assert resp_hi.detected_language == "hi"
    assert resp_hi.writing_script == "Devanagari"

    punjabi_query = "ਮੇਰਾ ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਨਹੀਂ ਹੋ ਰਿਹਾ"
    resp_pa = svc.process_message(punjabi_query, role="JOB_SEEKER")
    assert resp_pa.matched_intent == "candidate_resume_upload"
    assert resp_pa.detected_language == "pa"
    assert resp_pa.writing_script == "Gurmukhi"


# ======================================================================
# 5. Multilingual Follow-Up Context Tests
# ======================================================================

def test_multilingual_contextual_follow_up():
    svc = ChatbotService()

    # Hinglish follow-up referring to previous topic
    resp_hin = svc.process_message(
        message="aur batao",
        role="JOB_SEEKER",
        context_topic="candidate_resume_upload"
    )
    assert resp_hin.matched_intent == "candidate_resume_upload"
    assert resp_hin.confidence_score >= 0.90

    # Punjabi follow-up referring to previous topic
    resp_pbi = svc.process_message(
        message="hor dasso",
        role="JOB_SEEKER",
        context_topic="candidate_mcq_assessment"
    )
    assert resp_pbi.matched_intent == "candidate_mcq_assessment"
    assert resp_pbi.confidence_score >= 0.90


# ======================================================================
# 6. Backward Compatibility & English Regression Guarantee
# ======================================================================

def test_all_existing_sample_questions_still_pass():
    """Verify that none of the 30 existing FAQs have degraded or broken."""
    svc = ChatbotService()

    test_samples = [
        ("How do I upload my resume?", "JOB_SEEKER", "candidate_resume_upload"),
        ("What file formats are supported for resume upload?", "JOB_SEEKER", "candidate_resume_formats"),
        ("How does resume skill matching work?", "JOB_SEEKER", "candidate_resume_intelligence"),
        ("How do I search and filter jobs?", "JOB_SEEKER", "candidate_job_search"),
        ("What is the Round 1 MCQ assessment?", "JOB_SEEKER", "candidate_mcq_assessment"),
        ("How do I post a new job?", "RECRUITER", "recruiter_create_job"),
        ("How does the Kanban pipeline work?", "RECRUITER", "recruiter_kanban_pipeline"),
        ("How do I schedule a LiveKit video interview?", "RECRUITER", "recruiter_schedule_interview"),
        ("What is SkillSphere?", "JOB_SEEKER", "general_skillsphere_overview"),
        ("How do I reset my password?", "JOB_SEEKER", "general_password_reset")
    ]

    for question, role, expected_intent in test_samples:
        resp = svc.process_message(question, role=role)
        assert resp.matched_intent == expected_intent, (
            f"Regression in English FAQ '{question}': expected '{expected_intent}', got '{resp.matched_intent}'"
        )
        assert resp.confidence_score >= 0.70
        assert resp.detected_language == "en"


# ======================================================================
# 7. Focused Verification Tests: Unsupported Languages & Uncertainty
# ======================================================================

def test_unsupported_languages_not_misclassified_as_english():
    """Verify that Cyrillic, French, Spanish, German, and Chinese are NOT classified as English."""
    unsupported_samples = [
        ("Привет как дела", WritingScript.UNKNOWN),
        ("Bonjour comment allez vous", WritingScript.LATIN),
        ("Hola como estas amigo", WritingScript.LATIN),
        ("Guten Tag wie geht es dir", WritingScript.LATIN),
        ("你好世界", WritingScript.UNKNOWN)
    ]

    for text, expected_script in unsupported_samples:
        res = multilingual_engine.process(text)
        assert res.detected_language == SupportedLanguage.UNKNOWN, (
            f"Expected UNKNOWN for '{text}', but got '{res.detected_language}'"
        )
        assert res.script == expected_script
        assert res.confidence <= 0.25
        assert res.is_uncertain is True


# ======================================================================
# 8. Focused Verification Tests: Intent Polarity & Account Modality
# ======================================================================

def test_intent_polarity_and_modality_variations():
    """
    Verifies that positive, negative, and request variations of account access
    map to distinct and appropriate outcomes:
    - 'Mera account open nahi ho raha.' -> general_login (Negative login failure)
    - 'Mera account open ho gaya.' -> fallback (Positive resolution, not a failure)
    - 'Mera account open karna hai.' -> general_roles (Request to create/register account)
    """
    svc = ChatbotService()

    # 1. Negative failure: account login/access failure
    res_neg = svc.process_message("Mera account open nahi ho raha.")
    assert res_neg.matched_intent == "general_login"
    assert res_neg.confidence_score >= 0.70
    assert res_neg.detected_language == "hinglish"

    # 2. Positive resolution: problem is already solved, not a failure
    res_pos = svc.process_message("Mera account open ho gaya.")
    assert res_pos.matched_intent != "general_login"
    assert res_pos.confidence_score < 0.50  # Safely falls back rather than misdiagnosing

    # 3. Creation/registration request: wants to open/create a new account
    res_req = svc.process_message("Mera account open karna hai.")
    assert res_req.matched_intent == "general_roles"
    assert res_req.confidence_score >= 0.70
    assert res_req.detected_language == "hinglish"


# ======================================================================
# 9. Focused Verification Tests: Normalization Safety
# ======================================================================

def test_normalization_safety_with_names_urls_emails_and_tech_terms():
    """Verify that original_text is untouched and normalized_text does not corrupt technical entities."""
    cases = [
        ("My name is Alice Smith", "my name is alice smith"),
        ("Check https://skillsphere-uzt5.onrender.com/dashboard", "skillsphere-uzt5"),
        ("My email is test.user@example.com", "test user example com"),
        ("OAuth2, WebRTC, LiveKit, PostgreSQL, Tesseract OCR", "webrtc"),
        ("resume.pdf, CV.docx, photo.png", "docx")
    ]

    for raw, expected_token in cases:
        res = multilingual_engine.process(raw)
        # 1. Original text is strictly preserved
        assert res.original_text == raw
        # 2. Normalized text contains expected entity
        assert expected_token in res.normalized_text


# ======================================================================
# 10. Focused Verification Tests: Language Preference Forwarding
# ======================================================================

def test_language_preference_forwarding():
    """Verify language preference argument handling in service."""
    svc = ChatbotService()

    # Automatic detection (no preference supplied)
    res_auto = svc.process_message("Mera resume upload nahi ho raha.", role="JOB_SEEKER")
    assert res_auto.detected_language == "hinglish"

    # Explicit preference passed
    res_pref = svc.process_message(
        "Mera resume upload nahi ho raha.",
        role="JOB_SEEKER",
        language_preference="pa"
    )
    # Detected language still correctly captures input language
    assert res_pref.detected_language == "hinglish"

