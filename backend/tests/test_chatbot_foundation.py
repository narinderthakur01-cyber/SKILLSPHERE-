import pytest
from app.chatbot.service import ChatbotService
from app.chatbot.matcher import IntentMatcher

@pytest.fixture
def service():
    return ChatbotService()

def test_knowledge_base_loaded(service):
    """Verify knowledge base loads at least 25-30 FAQs with valid categories."""
    assert len(service.faqs) >= 25
    categories = {f["category"] for f in service.faqs}
    assert "candidate" in categories
    assert "recruiter" in categories
    assert "general" in categories

def test_health_check(service):
    """Verify chatbot health diagnostic metrics."""
    health = service.get_health()
    assert health.status == "healthy"
    assert health.engine == "rule_based_deterministic"
    assert health.total_faqs >= 25
    assert health.candidate_faqs > 0
    assert health.recruiter_faqs > 0
    assert health.general_faqs > 0

def test_exact_candidate_faq_match(service):
    """Verify exact match resolves to candidate resume upload intent with confidence 1.0."""
    res = service.process_message("How do I upload my resume?", role="JOB_SEEKER")
    assert res.matched_intent == "candidate_resume_upload"
    assert res.confidence_score == 1.0
    assert "OCR & Intelligence" in res.message
    assert len(res.quick_replies) >= 2

def test_wording_variation_and_synonyms(service):
    """Verify query with synonyms ('CV', 'attach') matches candidate resume upload."""
    res = service.process_message("Where can I attach my CV for parsing?", role="JOB_SEEKER")
    assert res.matched_intent == "candidate_resume_upload"
    assert res.confidence_score >= 0.50
    assert "PDF and DOCX" in res.message

def test_uppercase_and_whitespace_normalization(service):
    """Verify uppercase with extra spaces normalizes cleanly."""
    res = service.process_message("   HOW DO I SEARCH FOR JOBS?   ", role="JOB_SEEKER")
    assert res.matched_intent == "candidate_job_search"
    assert res.confidence_score >= 0.70
    assert "Browse Jobs" in res.message

def test_recruiter_faq_matching(service):
    """Verify recruiter questions match recruiter intents."""
    res = service.process_message("How do I post a new job?", role="RECRUITER")
    assert res.matched_intent == "recruiter_create_job"
    assert res.confidence_score >= 0.70
    assert "/recruiter" in res.message

def test_recruiter_kanban_pipeline(service):
    """Verify Kanban pipeline matching for recruiters."""
    res = service.process_message("How does the Kanban pipeline work?", role="RECRUITER")
    assert res.matched_intent == "recruiter_kanban_pipeline"
    assert "Screening" in res.message or "Shortlisted" in res.message

def test_role_based_filtering_blocks_recruiter_faq_for_candidate(service):
    """Verify a candidate cannot match a recruiter-only intent like recruiter_create_job."""
    # When role=JOB_SEEKER, recruiter-only intents are excluded from the eligible pool
    res = service.process_message("How do I post a new job opening?", role="JOB_SEEKER")
    # Must NOT match recruiter_create_job
    assert res.matched_intent != "recruiter_create_job"

def test_contextual_follow_up_phrase(service):
    """Verify follow-up phrase 'tell me more' preserves active topic."""
    res = service.process_message(
        message="tell me more",
        role="JOB_SEEKER",
        context_topic="candidate_resume_upload"
    )
    assert res.matched_intent == "candidate_resume_upload"
    assert res.confidence_score >= 0.90

def test_contextual_follow_up_shortcut(service):
    """Verify follow-up question 'what file formats' under resume upload resolves to formats FAQ."""
    res = service.process_message(
        message="what file formats are supported?",
        role="JOB_SEEKER",
        context_topic="candidate_resume_upload"
    )
    assert res.matched_intent in ["candidate_resume_formats", "candidate_resume_upload"]
    assert res.confidence_score >= 0.60

def test_fallback_on_unrelated_query(service):
    """Verify unrelated queries trigger friendly fallback response with default quick replies."""
    res = service.process_message("What is the recipe for chocolate cake?", role="JOB_SEEKER")
    assert res.matched_intent == "fallback"
    assert res.category == "fallback"
    assert "I'm not quite sure I understand that question about SkillSphere" in res.message
    assert len(res.quick_replies) >= 4
    assert any(qr.topic == "candidate_resume_upload" for qr in res.quick_replies)

def test_recruiter_default_quick_replies(service):
    """Verify recruiter fallback returns recruiter-focused quick replies."""
    res = service.process_message("Random gibberish xyz123", role="RECRUITER")
    assert res.matched_intent == "fallback"
    assert any(qr.topic == "recruiter_create_job" for qr in res.quick_replies)
    assert any(qr.topic == "recruiter_kanban_pipeline" for qr in res.quick_replies)
