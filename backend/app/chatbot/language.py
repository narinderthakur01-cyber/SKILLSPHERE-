"""
SkillSphere Assistant — Multilingual Language Engine
Module A: Language detection, script identification, text normalization, and semantic mapping.

Supports:
- English (en)
- Hindi in Devanagari (hi)
- Punjabi in Gurmukhi (pa)
- Roman Hindi & Hinglish (hinglish)
- Roman Punjabi (pa-Latn)
- Mixed-script and mixed-language messages
- Common spelling variations, slang, abbreviations, and repeated characters
- Uncertainty scoring and non-destructive normalization (preserves original input)
"""

import re
import unicodedata
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional
from pydantic import BaseModel, Field


class WritingScript(str, Enum):
    LATIN = "Latin"
    DEVANAGARI = "Devanagari"
    GURMUKHI = "Gurmukhi"
    MIXED = "Mixed"
    UNKNOWN = "Unknown"


class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    HINGLISH = "hinglish"
    PUNJABI = "pa"
    ROMAN_PUNJABI = "pa-Latn"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class LanguageDetectionResult(BaseModel):
    original_text: str = Field(..., description="Unmodified original user message")
    normalized_text: str = Field(..., description="Cleaned, normalized, lowercased text")
    script: WritingScript = Field(..., description="Identified writing script")
    detected_language: SupportedLanguage = Field(..., description="Classified language code")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    is_uncertain: bool = Field(False, description="Flag indicating ambiguous or low-confidence detection")
    is_multilingual: bool = Field(False, description="True if mixed languages/scripts are present")
    detected_tokens: List[str] = Field(default_factory=list, description="Normalized word tokens")
    intent_keywords: List[str] = Field(default_factory=list, description="Domain semantic concepts mapped to English")
    aligned_query: str = Field("", description="Standardized query representation for intent matching")


class MultilingualEngine:
    """
    Lightweight, maintainable, dependency-free multilingual language processing layer.
    Operates 100% locally with zero external API calls or latency overhead.
    """

    # Unicode ranges
    DEVANAGARI_RANGE = (0x0900, 0x097F)
    GURMUKHI_RANGE = (0x0A00, 0x0A7F)

    # -------------------------------------------------------------
    # Lexicons for Classification
    # -------------------------------------------------------------

    # Devanagari Hindi markers
    DEVANAGARI_HINDI_WORDS: Set[str] = {
        "है", "हैं", "था", "थी", "थे", "का", "की", "के", "को", "से", "में", "पर",
        "और", "या", "नहीं", "मत", "ना", "क्या", "कैसे", "कब", "कहाँ", "क्यों",
        "मेरा", "मेरी", "मेरे", "मुझे", "मुझको", "हम", "हमारा", "हमारी", "आप", "आपका", "आपकी",
        "तुम", "तुम्हारा", "करना", "करो", "करें", "हो", "रहा", "रही", "रहे", "हुआ", "हुई",
        "रिज्यूम", "सीवी", "अपलोड", "नौकरी", "जॉब", "पासवर्ड", "लॉगिन", "खाता", "प्रोफाइल",
        "असेसमेंट", "टेस्ट", "परीक्षा", "वीडियो", "इंटरव्यू", "सवाल", "मदद", "सहायता"
    }

    # Gurmukhi Punjabi markers
    GURMUKHI_PUNJABI_WORDS: Set[str] = {
        "ਹੈ", "ਹਨ", "ਸੀ", "ਸਨ", "ਦਾ", "ਦੀ", "ਦੇ", "ਨੂੰ", "ਤੋਂ", "ਵਿੱਚ", "ਅਤੇ", "ਜਾਂ",
        "ਨਹੀਂ", "ਨੀ", "ਨਾ", "ਕੀ", "ਕਿਵੇਂ", "ਕਦੋਂ", "ਕਿੱਥੇ", "ਕਿਉਂ", "ਮੇਰਾ", "ਮੇਰੀ", "ਮੇਰੇ",
        "ਮੈਨੂੰ", "ਅਸੀਂ", "ਸਾਡਾ", "ਤੁਸੀਂ", "ਤੁਹਾਡਾ", "ਤੁਹਾਡੀ", "ਕਰਨਾ", "ਕਰੋ", "ਹੋ", "ਰਿਹਾ",
        "ਰਹੀ", "ਰਹੇ", "ਪਿਆ", "ਪਈ", "ਰਿਜ਼ਿਊਮ", "ਸੀਵੀ", "ਅਪਲੋਡ", "ਨੌਕਰੀ", "ਜੌਬ", "ਪਾਸਵਰਡ",
        "ਲੌਗਇਨ", "ਖਾਤਾ", "ਪ੍ਰੋਫਾਈਲ", "ਅਸੈਸਮੈਂਟ", "ਟੈਸਟ", "ਪ੍ਰੀਖਿਆ", "ਵੀਡੀਓ", "ਇੰਟਰਵਿਊ", "ਸਵਾਲ", "ਮਦਦ"
    }

    # Roman Hindi / Hinglish stopwords and characteristic words
    HINGLISH_WORDS: Set[str] = {
        # Pronouns
        "mera", "meri", "mere", "mujhe", "mujhko", "hum", "humara", "humari", "humare",
        "aap", "aapka", "aapki", "aapke", "tum", "tumhara", "tumhari", "tumhare",
        "apna", "apni", "apne", "koi", "kisi", "kuch",
        # Negation & Auxiliaries
        "nahi", "nhi", "nahin", "nai", "naahi", "mat", "na",
        "hai", "hain", "h", "he", "tha", "thi", "the", "ho", "hoga", "hogi", "honge",
        "raha", "rahi", "rahe", "rha", "rhi", "rhe", "hua", "hui", "hue",
        # Question words
        "kya", "kaise", "kaisa", "kaisi", "kyu", "kyun", "kab", "kahan", "kidhar", "kaun", "kitna", "kitni",
        # Verbs & common actions
        "karo", "karna", "karein", "kare", "krna", "kra", "kiya", "kiye",
        "de", "do", "dena", "dijiye", "batao", "btao", "btaiye", "dikhao", "dekho",
        "bol", "bolo", "sun", "samjhao", "bhejo", "bhejna", "chahiye", "aata", "aati",
        # Common terms
        "naukri", "kaam", "madad", "sahayata", "sawal", "samasya", "dikkat", "pareshani",
        "accha", "theek", "bura", "bohot", "bahut", "bht", "thoda", "zyada", "jaldi"
    }

    # Roman Punjabi specific markers (distinguishes Punjabi from Hindi in Latin script)
    ROMAN_PUNJABI_WORDS: Set[str] = {
        # Specific pronouns
        "mainu", "mennu", "sanu", "tussi", "tusan", "tuhanu", "thonu", "twada", "tuhada",
        "tuhadi", "tuhade", "sada", "sadi", "sade",
        # Negation & Auxiliaries
        "ni", "nahie", "reha", "rehi", "rehe", "pyeya", "pyi", "si", "san", "aa", "ve", "va", "vaa",
        # Question words
        "kive", "kiven", "kiddan", "kidan", "kyon", "kyo", "kadon", "kithe", "kinna", "kinni",
        # Verbs & common actions
        "dasso", "dso", "dassiye", "daso", "dass", "kitta", "kiti", "kite",
        "vekho", "labho", "labhna", "labh", "aunda", "aundi", "aunde", "chalda", "chaldi",
        "hunda", "hundi", "hunde", "kamm", "nokri", "naukari", "chahida", "chahidi"
    }

    # English function words and distinct markers
    ENGLISH_WORDS: Set[str] = {
        "the", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "shall", "will", "should", "would", "may", "might", "must", "can", "could",
        "what", "how", "why", "when", "where", "who", "whom", "which",
        "my", "me", "myself", "i", "you", "your", "yours", "we", "our", "ours", "us",
        "they", "them", "their", "theirs", "he", "him", "his", "she", "her", "hers", "it", "its",
        "not", "unable", "cannot", "cant", "wont", "dont", "doesnt", "didnt", "fail", "failed", "failing",
        "failure", "error", "issue", "problem", "upload", "uploading", "uploaded",
        "please", "tell", "help", "show", "guide", "explain", "about", "with", "from", "for", "to", "in", "on"
    }

    # Common spelling & slang normalizations (phonetic / informal -> standardized)
    NORMALIZATION_MAP: Dict[str, str] = {
        # Negation & auxiliaries
        "nhi": "nahi",
        "nahin": "nahi",
        "naahi": "nahi",
        "nai": "nahi",
        "rha": "raha",
        "rhi": "rahi",
        "rhe": "rahe",
        "krna": "karna",
        "krne": "karna",
        "kra": "kiya",
        "kro": "karo",
        "btao": "batao",
        "btaiye": "batao",
        "dso": "dasso",
        "daso": "dasso",
        # Slang & short forms
        "plz": "please",
        "pls": "please",
        "thx": "thanks",
        "tks": "thanks",
        "ty": "thanks",
        "prob": "problem",
        "prblm": "problem",
        "msg": "message",
        "pic": "image",
        "img": "image",
        "vid": "video",
        # Domain terminology normalizations
        "cv": "resume",
        "biodata": "resume",
        "resum": "resume",
        "uplod": "upload",
        "uplode": "upload",
        "uploading": "upload",
        "uploade": "upload",
        "downlod": "download",
        "pasword": "password",
        "paswrd": "password",
        "passwrd": "password",
        "pwd": "password",
        "intervew": "interview",
        "intervu": "interview",
        "intrvw": "interview",
        "asessment": "assessment",
        "assesment": "assessment",
        "assessement": "assessment"
    }

    # Cross-lingual semantic concept mapping to English keywords for grounded matching
    SEMANTIC_CONCEPT_MAP: Dict[str, List[str]] = {
        # Resume Upload & Formats
        "resume": ["resume"],
        "cv": ["resume"],
        "biodata": ["resume"],
        "रिज्यूम": ["resume"],
        "रिज्यूमे": ["resume"],
        "सीवी": ["resume"],
        "ਰਿਜ਼ਿਊਮ": ["resume"],
        "ਰੈਜ਼ਿਊਮੇ": ["resume"],
        "ਰਿਜ਼ਿਊਮੇ": ["resume"],
        "upload": ["upload"],
        "अपलोड": ["upload"],
        "ਅਪਲੋਡ": ["upload"],
        "ਅੱਪਲੋਡ": ["upload"],
        "format": ["format", "formats"],
        "formats": ["format", "formats"],
        "size": ["size"],
        "pdf": ["pdf", "formats"],
        "docx": ["docx", "formats"],
        "file": ["file"],
        # Failure / Inability / Negative states
        "nahi": ["not", "unable", "fail"],
        "ni": ["not", "unable", "fail"],
        "not": ["not", "unable", "fail"],
        "unable": ["not", "unable", "fail"],
        "cannot": ["not", "unable", "fail"],
        "fail": ["fail", "error"],
        "failed": ["fail", "error"],
        "error": ["error", "problem"],
        "problem": ["problem", "issue"],
        "dikkat": ["problem", "issue"],
        "samasya": ["problem", "issue"],
        "stuck": ["stuck", "fail"],
        "fas": ["stuck", "fail"],
        "fasi": ["stuck", "fail"],
        "fasa": ["stuck", "fail"],
        # Skills & Matching
        "skill": ["skill", "skills", "matching"],
        "skills": ["skill", "skills", "matching"],
        "score": ["score", "matching"],
        "scoring": ["score", "matching"],
        "matching": ["matching", "score"],
        "match": ["matching", "score"],
        # Jobs & Search
        "job": ["job", "jobs", "search"],
        "jobs": ["job", "jobs", "search"],
        "naukri": ["job", "jobs", "search"],
        "nokri": ["job", "jobs", "search"],
        "ਨੌਕਰੀ": ["job", "jobs", "search"],
        "नौकरी": ["job", "jobs", "search"],
        "search": ["search", "find"],
        "find": ["search", "find"],
        "dhundna": ["search", "find"],
        "labhna": ["search", "find"],
        "apply": ["apply", "application"],
        "application": ["application", "status"],
        "status": ["status", "tracking"],
        "स्टेटस": ["status", "tracking"],
        "ਸਟੇਟਸ": ["status", "tracking"],
        "post": ["post", "create", "job"],
        "पोस्ट": ["post", "create", "job"],
        "ਪੋਸਟ": ["post", "create", "job"],
        # Assessments & Proctoring
        "assessment": ["assessment", "mcq"],
        "mcq": ["mcq", "assessment"],
        "test": ["test", "assessment"],
        "pariksha": ["test", "assessment"],
        "ਪ੍ਰੀਖਿਆ": ["test", "assessment"],
        "परीक्षा": ["test", "assessment"],
        "proctoring": ["proctoring", "anti-cheating"],
        "webcam": ["webcam", "camera"],
        "camera": ["webcam", "camera"],
        "tab": ["tab", "switch"],
        "video": ["video", "assessment"],
        "recording": ["video", "recording"],
        # Interviews & LiveKit
        "interview": ["interview", "livekit"],
        "livekit": ["livekit", "interview"],
        "meeting": ["interview", "livekit"],
        "ਇੰਟਰਵਿਊ": ["interview", "livekit"],
        "इंटरव्यू": ["interview", "livekit"],
        # Account & Auth
        "login": ["login", "account"],
        "password": ["password", "reset"],
        "लॉगिन": ["login", "account"],
        "ਪਾਸਵਰਡ": ["password", "reset"],
        "पासवर्ड": ["password", "reset"],
        "reset": ["reset", "password"],
        "verification": ["verification", "email"],
        "verify": ["verification", "email"],
        # Recruiter
        "pipeline": ["pipeline", "kanban"],
        "kanban": ["pipeline", "kanban"],
        "post": ["post", "create", "job"],
        "applicant": ["applicant", "candidates"],
        "applicants": ["applicant", "candidates"],
        "candidate": ["candidate", "candidates"],
        "candidates": ["candidate", "candidates"],
        "question": ["question", "bank"],
        "questions": ["question", "bank"]
    }

    @classmethod
    def detect_script(cls, text: str) -> WritingScript:
        """
        Identify the writing script based on character codepoint distribution.
        """
        if not text or not text.strip():
            return WritingScript.UNKNOWN

        deva_count = 0
        gurm_count = 0
        latn_count = 0
        total_alpha = 0

        for char in text:
            cp = ord(char)
            if cls.DEVANAGARI_RANGE[0] <= cp <= cls.DEVANAGARI_RANGE[1]:
                deva_count += 1
                total_alpha += 1
            elif cls.GURMUKHI_RANGE[0] <= cp <= cls.GURMUKHI_RANGE[1]:
                gurm_count += 1
                total_alpha += 1
            elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
                latn_count += 1
                total_alpha += 1

        if total_alpha == 0:
            return WritingScript.UNKNOWN

        # Check for mixed script
        scripts_present = sum(1 for c in [deva_count, gurm_count, latn_count] if c > 0)
        if scripts_present > 1:
            # If one script strongly dominates (> 85%), assign dominant script
            if deva_count / total_alpha >= 0.85:
                return WritingScript.DEVANAGARI
            if gurm_count / total_alpha >= 0.85:
                return WritingScript.GURMUKHI
            if latn_count / total_alpha >= 0.85:
                return WritingScript.LATIN
            return WritingScript.MIXED

        if deva_count > 0:
            return WritingScript.DEVANAGARI
        if gurm_count > 0:
            return WritingScript.GURMUKHI
        if latn_count > 0:
            return WritingScript.LATIN

        return WritingScript.UNKNOWN

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalize text non-destructively:
        - Unicode NFKC decomposition/composition.
        - Collapse 3+ repeating characters (e.g. 'nahiiii' -> 'nahi', 'pleaaase' -> 'please').
        - Lowercase Latin characters.
        - Strip extraneous punctuation and excessive whitespace while preserving Indic characters.
        - Standardize common informal spellings and abbreviations.
        """
        if not text:
            return ""

        # Unicode normalization
        clean = unicodedata.normalize("NFKC", text.strip())

        # Collapse 3+ consecutive identical characters to 1 (or 2 for letters like 'ee', 'oo')
        clean = re.sub(r"(.)\1{2,}", r"\1", clean)

        # Lowercase
        clean = clean.lower()

        # Remove special characters except alphanumeric, Indic characters, hyphens, and spaces
        # Devanagari: \u0900-\u097F, Gurmukhi: \u0A00-\u0A7F, Latin: a-z 0-9
        clean = re.sub(r"[^\w\s\-\u0900-\u097F\u0A00-\u0A7F]", " ", clean)

        # Tokenize and normalize known variants
        tokens = clean.split()
        normalized_tokens = [cls.NORMALIZATION_MAP.get(t, t) for t in tokens]

        return " ".join(normalized_tokens)

    @classmethod
    def classify_language(
        cls,
        text: str,
        script: WritingScript,
        tokens: List[str]
    ) -> Tuple[SupportedLanguage, float, bool, bool]:
        """
        Classifies input language, returns:
        (detected_language, confidence_score, is_uncertain, is_multilingual)
        """
        if not tokens:
            return SupportedLanguage.UNKNOWN, 0.0, True, False

        token_set = set(tokens)

        # 0. Script is Unknown (e.g. Cyrillic, Arabic, Chinese/Japanese, emojis only)
        if script == WritingScript.UNKNOWN:
            return SupportedLanguage.UNKNOWN, 0.10, True, False

        # 1. Script is pure Devanagari
        if script == WritingScript.DEVANAGARI:
            hindi_matches = len(token_set.intersection(cls.DEVANAGARI_HINDI_WORDS))
            confidence = min(0.85 + (hindi_matches * 0.05), 1.0)
            return SupportedLanguage.HINDI, round(confidence, 2), False, False

        # 2. Script is pure Gurmukhi
        if script == WritingScript.GURMUKHI:
            punjabi_matches = len(token_set.intersection(cls.GURMUKHI_PUNJABI_WORDS))
            confidence = min(0.85 + (punjabi_matches * 0.05), 1.0)
            return SupportedLanguage.PUNJABI, round(confidence, 2), False, False

        # 3. Script is Mixed (e.g. Devanagari + Latin words)
        if script == WritingScript.MIXED:
            return SupportedLanguage.MIXED, 0.80, False, True

        # 4. Script is Latin: Distinguish English, Hinglish, Roman Punjabi, or Unknown
        # Score word overlaps
        eng_matches = len(token_set.intersection(cls.ENGLISH_WORDS))
        hin_matches = len(token_set.intersection(cls.HINGLISH_WORDS))
        pbi_matches = len(token_set.intersection(cls.ROMAN_PUNJABI_WORDS))

        total_matches = eng_matches + hin_matches + pbi_matches
        total_tokens = len(tokens)

        # Check for characteristic multi-word grammatical collocations
        raw_joined = " " + " ".join(tokens) + " "

        # Hinglish collocations
        hinglish_collocations = [
            " nahi ho ", " nhi ho ", " kaise kare", " kaise karu", " mera resume", " meri profile",
            " password bhul ", " upload nahi", " upload nhi", " kya hai", " batao ", " karna hai",
            " open nahi", " login nahi", " ho gaya", " ho gya", " account open"
        ]
        has_hinglish_collocation = any(c in raw_joined for c in hinglish_collocations)

        # Roman Punjabi collocations
        punjabi_collocations = [
            " ni ho reha", " ni ho rha", " kive ", " kiven ", " kiddan ", " kidan ",
            " dasso ", " dso ", " mainu ", " tuhanu ", " twada ", " labhna ", " nokri ",
            " ho gya", " ho reha", " chal reha"
        ]
        has_punjabi_collocation = any(c in raw_joined for c in punjabi_collocations)

        if has_punjabi_collocation:
            pbi_matches += 3
        if has_hinglish_collocation:
            hin_matches += 3

        total_matches = eng_matches + hin_matches + pbi_matches

        # Ambiguous or very short query (1 token)
        if total_tokens <= 1 and total_matches == 0:
            # Check domain terms like 'resume', 'jobs'
            if any(t in cls.SEMANTIC_CONCEPT_MAP for t in token_set):
                return SupportedLanguage.ENGLISH, 0.60, True, False
            return SupportedLanguage.UNKNOWN, 0.10, True, False

        # Zero matches across all supported languages (e.g. French, Spanish, German, Latin gibberish)
        if total_matches == 0:
            domain_hits = sum(1 for t in token_set if t in cls.SEMANTIC_CONCEPT_MAP)
            if domain_hits >= 1:
                return SupportedLanguage.ENGLISH, 0.55, True, False
            # Safely report UNKNOWN rather than misclassifying unsupported languages as English
            return SupportedLanguage.UNKNOWN, 0.15, True, False

        # Punjabi in Latin script
        if pbi_matches > 0 and pbi_matches >= hin_matches and pbi_matches >= eng_matches:
            confidence = min(0.70 + (pbi_matches * 0.10), 0.98)
            is_multi = (eng_matches > 0)
            return SupportedLanguage.ROMAN_PUNJABI, round(confidence, 2), False, is_multi

        # Hinglish / Roman Hindi
        if hin_matches > 0 and hin_matches >= eng_matches:
            confidence = min(0.70 + (hin_matches * 0.10), 0.98)
            is_multi = (eng_matches > 0)
            return SupportedLanguage.HINGLISH, round(confidence, 2), False, is_multi

        # Pure English or English-dominant with a loan word
        if eng_matches > 0 and eng_matches > hin_matches and eng_matches > pbi_matches:
            confidence = min(0.75 + (eng_matches * 0.08), 0.99)
            return SupportedLanguage.ENGLISH, round(confidence, 2), False, False

        # If Hinglish words present with English nouns (classic code-switching)
        if hin_matches > 0 and eng_matches > 0:
            return SupportedLanguage.HINGLISH, 0.85, False, True

        # Fallback when matches are zero but Latin letters present
        return SupportedLanguage.UNKNOWN, 0.20, True, False

    @classmethod
    def extract_semantic_intent_keywords(cls, tokens: List[str]) -> Tuple[List[str], str]:
        """
        Maps normalized tokens in any script/language to standardized English domain concepts.
        Produces an aligned search query for downstream intent matching with polarity awareness.
        """
        extracted_keywords: List[str] = []
        seen: Set[str] = set()
        token_set = set(tokens)

        # Detect polarity and intent modality
        has_negation = any(n in token_set for n in ["nahi", "nhi", "ni", "not", "unable", "fail", "failed", "error", "dikkat", "samasya"])
        has_positive_resolution = any(p in token_set for p in ["gaya", "gya", "resolved", "solved", "success"])
        has_creation_intent = any(c in token_set for c in ["karna", "banana", "create", "register", "open"])

        # Contextual domain detection: Account handling (Negative failure vs Positive resolution vs Creation request)
        if "account" in token_set or "khata" in token_set:
            if has_negation:
                for c in ["login", "access account", "login issues", "credentials", "fail"]:
                    if c not in seen:
                        seen.add(c)
                        extracted_keywords.append(c)
            elif has_positive_resolution and not has_negation:
                for c in ["resolved", "success"]:
                    if c not in seen:
                        seen.add(c)
                        extracted_keywords.append(c)
            elif has_creation_intent and not has_negation:
                for c in ["roles", "register", "account types", "candidate", "recruiter"]:
                    if c not in seen:
                        seen.add(c)
                        extracted_keywords.append(c)

        for token in tokens:
            if token in cls.SEMANTIC_CONCEPT_MAP:
                for concept in cls.SEMANTIC_CONCEPT_MAP[token]:
                    if concept not in seen:
                        seen.add(concept)
                        extracted_keywords.append(concept)
            else:
                # Include alphanumeric domain-relevant tokens as-is
                if len(token) >= 3 and token not in cls.HINGLISH_WORDS and token not in cls.ROMAN_PUNJABI_WORDS:
                    if token not in seen:
                        seen.add(token)
                        extracted_keywords.append(token)

        aligned_query = " ".join(extracted_keywords)
        return extracted_keywords, aligned_query

    @classmethod
    def process(cls, text: str) -> LanguageDetectionResult:
        """
        Main entrypoint: analyzes user message, classifies language & script,
        normalizes text non-destructively, and extracts semantic intent keywords.
        """
        original = text if text is not None else ""
        if not original.strip():
            return LanguageDetectionResult(
                original_text=original,
                normalized_text="",
                script=WritingScript.UNKNOWN,
                detected_language=SupportedLanguage.UNKNOWN,
                confidence=0.0,
                is_uncertain=True,
                is_multilingual=False,
                detected_tokens=[],
                intent_keywords=[],
                aligned_query=""
            )

        # Check if text contains any alphabetic or Indic characters
        has_letters = any(
            c.isalpha() or
            (cls.DEVANAGARI_RANGE[0] <= ord(c) <= cls.DEVANAGARI_RANGE[1]) or
            (cls.GURMUKHI_RANGE[0] <= ord(c) <= cls.GURMUKHI_RANGE[1])
            for c in original
        )
        if not has_letters:
            return LanguageDetectionResult(
                original_text=original,
                normalized_text="",
                script=WritingScript.UNKNOWN,
                detected_language=SupportedLanguage.UNKNOWN,
                confidence=0.0,
                is_uncertain=True,
                is_multilingual=False,
                detected_tokens=[],
                intent_keywords=[],
                aligned_query=""
            )

        script = cls.detect_script(original)
        normalized = cls.normalize_text(original)
        tokens = normalized.split()

        lang, confidence, is_uncertain, is_multi = cls.classify_language(original, script, tokens)
        keywords, aligned_query = cls.extract_semantic_intent_keywords(tokens)

        return LanguageDetectionResult(
            original_text=original,
            normalized_text=normalized,
            script=script,
            detected_language=lang,
            confidence=confidence,
            is_uncertain=is_uncertain,
            is_multilingual=is_multi,
            detected_tokens=tokens,
            intent_keywords=keywords,
            aligned_query=aligned_query
        )


# Global singleton instance
multilingual_engine = MultilingualEngine()
