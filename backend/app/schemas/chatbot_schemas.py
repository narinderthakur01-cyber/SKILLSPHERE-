from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User question or input")
    session_id: Optional[str] = Field(None, max_length=100, description="Session ID for context tracking")
    context_topic: Optional[str] = Field(None, max_length=100, description="Active topic hint from client")
    language_preference: Optional[str] = Field(None, max_length=10, description="Optional manual language preference: en, hi, pa, etc.")

class QuickReply(BaseModel):
    label: str
    query: str
    topic: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    matched_intent: str
    confidence_score: float
    session_id: str
    category: str
    quick_replies: List[QuickReply] = []
    suggested_questions: List[str] = []
    timestamp: str
    detected_language: Optional[str] = Field(None, description="Detected input language code")
    writing_script: Optional[str] = Field(None, description="Identified writing script")
    language_confidence: Optional[float] = Field(None, description="Confidence of language detection")
    ticket_data: Optional[Dict[str, Any]] = Field(None, description="Structured support ticket data (preview or created ticket)")

class FAQItem(BaseModel):
    id: str
    category: str
    roles: List[str]
    intent: str
    title: str
    sample_questions: List[str]
    keywords: List[str]
    synonyms: List[str] = []
    response: str
    multilingual_responses: Optional[Dict[str, str]] = Field(default_factory=dict, description="Translations keyed by language code")
    related_questions: List[str] = []
    quick_replies: List[QuickReply] = []

class FAQListResponse(BaseModel):
    total: int
    role: str
    faqs: List[FAQItem]

class ChatbotHealthResponse(BaseModel):
    status: str
    engine: str
    total_faqs: int
    candidate_faqs: int
    recruiter_faqs: int
    general_faqs: int
    storage_backend: str
    storage_healthy: bool
    version: str

# --- Conversation History Schemas ---

class ChatHistoryMessage(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    created_at: str

class ChatSessionSummary(BaseModel):
    id: str
    user_id: str
    user_role: str
    title: Optional[str] = None
    last_topic: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int = 0

class ChatHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    title: Optional[str] = None
    last_topic: Optional[str] = None
    messages: List[ChatHistoryMessage] = []
    total_messages: int = 0

class DeleteSessionResponse(BaseModel):
    session_id: str
    message: str
    deleted: bool
