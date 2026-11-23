"""
SkillSphere Assistant — AI Support System & Chatbot Engine.
Provides multilingual language processing, rule-based intent matching,
role-gated FAQ retrieval, contextual assistance, and support ticket integration.
"""

from app.chatbot.language import (
    multilingual_engine,
    MultilingualEngine,
    WritingScript,
    SupportedLanguage,
    LanguageDetectionResult
)
from app.chatbot.troubleshooter import (
    troubleshooting_engine,
    TroubleshootingEngine
)
from app.chatbot.llm import (
    llm_fallback_engine,
    HybridLLMFallback
)

__all__ = [
    "multilingual_engine",
    "MultilingualEngine",
    "WritingScript",
    "SupportedLanguage",
    "LanguageDetectionResult",
    "troubleshooting_engine",
    "TroubleshootingEngine",
    "llm_fallback_engine",
    "HybridLLMFallback"
]
