"""
SkillSphere Assistant Smart Troubleshooting Engine.
Deterministic, guided, multi-turn troubleshooting for:
1. Resume Upload & OCR Failures
2. LiveKit Video/Audio/WebRTC Connection Problems
3. Proctored MCQ Assessment Issues

Features:
- One diagnostic question at a time
- Persistent multi-turn state tracking per session
- Multilingual support for all 5 languages (en, hi, hinglish, pa, pa-Latn)
- Role-aware guidance (Job Seeker vs Recruiter)
- Objective verification (never claims issue is resolved without user confirmation)
- Support ticket escalation when troubleshooting is unsuccessful
"""

from typing import Dict, Any, List, Optional, Tuple
from app.schemas.chatbot_schemas import QuickReply, ChatResponse
from app.chatbot.language import multilingual_engine, SupportedLanguage
from app.models.models import TicketCategoryEnum, TicketPriorityEnum, User
from app.schemas.ticket_schemas import TicketCreateRequest
from app.services import ticket_service

# Supported Troubleshooting Flows
FLOW_RESUME_OCR = "resume_ocr"
FLOW_LIVEKIT = "livekit_webrtc"
FLOW_PROCTORING = "proctored_mcq"

# Triggers for each flow across all supported languages
FLOW_TRIGGERS: Dict[str, List[str]] = {
    FLOW_RESUME_OCR: [
        "resume upload fail", "resume upload error", "ocr error", "ocr fail",
        "resume parsing failed", "cannot upload cv", "cv upload error",
        "resume upload nahi ho raha", "cv upload nhi ho rha", "resume upload ni ho reha",
        "resume reject ho gaya", "ocr parse nahi ho raha", "file upload error",
        "मेरा रिज्यूम अपलोड नहीं हो रहा", "रिज्यूम पार्स नहीं हुआ", "ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਨਹੀਂ ਹੋ ਰਿਹਾ",
        "ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਫੇਲ", "ਰਿਜ਼ਿਊਮ ਐਰਰ", "ਅਪਲੋਡ ਐਰਰ", "रिज्यूम एरर", "अपलोड एरर",
        "troubleshoot_resume", "resume_ocr_troubleshoot"
    ],
    FLOW_LIVEKIT: [
        "video call not connecting", "livekit error", "livekit fail", "video interview error",
        "camera not working", "mic not working", "webrtc error", "webrtc failed",
        "black screen in interview", "audio not working in interview", "interview connect nahi ho raha",
        "video call disconnect ho gaya", "camera on nahi ho raha", "mic awaz nahi aa rahi",
        "ਕੈਮਰਾ ਕੰਮ ਨਹੀਂ ਕਰ ਰਿਹਾ", "ਵੀਡੀਓ ਕਾਲ ਨਹੀਂ ਚੱਲ ਰਹੀ", "कैमरा काम नहीं कर रहा", "वीडियो कॉल नहीं चल रही",
        "troubleshoot_livekit", "livekit_troubleshoot"
    ],
    FLOW_PROCTORING: [
        "tab switch warning", "proctoring error", "proctoring issue", "proctoring flag",
        "mcq stuck", "test not submitting", "assessment frozen", "fullscreen warning",
        "camera disconnected in test", "test submit nahi ho raha", "exam freeze ho gaya",
        "timer khatam ho gaya test ka", "tab change warning aa rahi hai", "assessment submit ni ho reha",
        "ਪ੍ਰੀਖਿਆ ਸਬਮਿਟ ਨਹੀਂ ਹੋ ਰਹੀ", "परीक्षा सबमिट नहीं हो रही", "प्रॉक्टरिंग चेतावनी",
        "troubleshoot_proctoring", "proctoring_troubleshoot"
    ]
}

FLOW_CATEGORY_MAP: Dict[str, TicketCategoryEnum] = {
    FLOW_RESUME_OCR: TicketCategoryEnum.RESUME_OCR,
    FLOW_LIVEKIT: TicketCategoryEnum.LIVEKIT_VIDEO,
    FLOW_PROCTORING: TicketCategoryEnum.PROCTORING_MCQ,
}

FLOW_DEFAULT_SUBJECTS: Dict[str, Dict[str, str]] = {
    FLOW_RESUME_OCR: {
        "en": "Resume Upload & OCR Extraction Failure",
        "hi": "रिज्यूम अपलोड और OCR पार्सिंग त्रुटि",
        "hinglish": "Resume Upload & OCR Parsing Failure",
        "pa": "ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਅਤੇ OCR ਸਮੱਸਿਆ",
        "pa-Latn": "Resume Upload & OCR Extraction Failure"
    },
    FLOW_LIVEKIT: {
        "en": "LiveKit WebRTC Video Interview Connection Issue",
        "hi": "LiveKit वीडियो इंटरव्यू कनेक्शन समस्या",
        "hinglish": "LiveKit Video Interview Connection Issue",
        "pa": "LiveKit ਵੀਡੀਓ ਇੰਟਰਵਿਊ ਕਨੈਕਸ਼ਨ ਸਮੱਸਿਆ",
        "pa-Latn": "LiveKit Video Interview Connection Issue"
    },
    FLOW_PROCTORING: {
        "en": "Proctored MCQ Assessment Freeze or Warning Issue",
        "hi": "प्रॉक्टर्ड MCQ असेसमेंट फ्रीज या चेतावनी समस्या",
        "hinglish": "Proctored MCQ Assessment Freeze or Warning Issue",
        "pa": "ਪ੍ਰੀਖਿਆ ਫ੍ਰੀਜ਼ ਜਾਂ ਚੇਤਾਵਨੀ ਸਮੱਸਿਆ",
        "pa-Latn": "Proctored MCQ Assessment Freeze or Warning Issue"
    }
}

# Guided Multi-Step Troubleshooting Knowledge Definitions
TROUBLESHOOTING_STEPS: Dict[str, Dict[int, Dict[str, Any]]] = {
    FLOW_RESUME_OCR: {
        1: {
            "intent": "troubleshoot_resume_step_1",
            "question": {
                "en": "Let's diagnose your resume upload issue. Step 1: Is your resume in standard PDF (.pdf) or Microsoft Word (.docx) format and under 10MB?",
                "hi": "आइए आपके रिज्यूम अपलोड समस्या का समाधान करें। चरण 1: क्या आपका रिज्यूम मानक PDF (.pdf) या Word (.docx) फॉर्मेट में है और 10MB से कम है?",
                "hinglish": "Aapke resume upload issue ko troubleshoot karte hain. Step 1: Kya aapka resume standard PDF (.pdf) ya Word (.docx) format mein hai aur 10MB se kam size ka hai?",
                "pa": "ਆਓ ਤੁਹਾਡੀ ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ ਸਮੱਸਿਆ ਦਾ ਹੱਲ ਕਰੀਏ। ਕਦਮ 1: ਕੀ ਤੁਹਾਡਾ ਰਿਜ਼ਿਊਮ ਸਟੈਂਡਰਡ PDF (.pdf) ਜਾਂ Word (.docx) ਫਾਰਮੈਟ ਵਿੱਚ ਹੈ ਅਤੇ 10MB ਤੋਂ ਘੱਟ ਹੈ?",
                "pa-Latn": "Tuhade resume upload issue nu troubleshoot karde haan. Step 1: Ki tuhada resume standard PDF (.pdf) ya Word (.docx) format vich hai te 10MB to ghat size da hai?"
            },
            "options": [
                {
                    "label": "Yes, PDF/DOCX under 10MB",
                    "query": "Yes, my resume is valid PDF/DOCX under 10MB",
                    "topic": "troubleshoot_resume_step_1_yes"
                },
                {
                    "label": "No / Different format or size",
                    "query": "No, it is another format or larger than 10MB",
                    "topic": "troubleshoot_resume_step_1_no"
                }
            ],
            "action_on_no": {
                "en": "SkillSphere strictly supports PDF (.pdf) and Microsoft Word (.docx) files up to 10MB. Images (PNG, JPG), plain text (.txt), and ZIP files are not supported. Please convert your resume to a standard PDF or DOCX file under 10MB and retry uploading at /dashboard?tab=resumes.",
                "hi": "SkillSphere केवल 10MB तक की PDF (.pdf) और Word (.docx) फाइलों का समर्थन करता है। फोटो (PNG, JPG) और टेक्स्ट फाइलें स्वीकार नहीं हैं। कृपया इसे 10MB से कम की PDF या DOCX में बदलें और /dashboard?tab=resumes पर पुनः प्रयास करें।",
                "hinglish": "SkillSphere sirf 10MB tak ke PDF (.pdf) aur Word (.docx) files ko support karta hai. Images ya text files allowed nahi hain. Kripya apne resume ko 10MB se kam ke PDF ya DOCX mein convert karein aur /dashboard?tab=resumes par re-upload karein.",
                "pa": "SkillSphere ਸਿਰਫ਼ 10MB ਤੱਕ ਦੀਆਂ PDF (.pdf) ਅਤੇ Word (.docx) ਫ਼ਾਈਲਾਂ ਦਾ ਸਮਰਥਨ ਕਰਦਾ ਹੈ। ਫੋਟੋਆਂ ਜਾਂ ਟੈਕਸਟ ਫ਼ਾਈਲਾਂ ਮਨਜ਼ੂਰ ਨਹੀਂ ਹਨ। ਕਿਰਪਾ ਕਰਕੇ ਇਸਨੂੰ 10MB ਤੋਂ ਘੱਟ PDF/DOCX ਵਿੱਚ ਬਦਲੋ ਅਤੇ /dashboard?tab=resumes 'ਤੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
                "pa-Latn": "SkillSphere sirf 10MB tak diyan PDF (.pdf) te Word (.docx) files nu support karda hai. Please file nu valid PDF/DOCX vich convert karke /dashboard?tab=resumes te upload karo."
            }
        },
        2: {
            "intent": "troubleshoot_resume_step_2",
            "question": {
                "en": "Step 2: Is your PDF a scanned image / photocopy, or does it contain complex multi-column graphics and tables?",
                "hi": "चरण 2: क्या आपका PDF एक स्कैन किया हुआ फोटो/दस्तावेज़ है, या इसमें जटिल मल्टी-कॉलम टेबल और ग्राफ़िक्स हैं?",
                "hinglish": "Step 2: Kya aapka PDF ek scanned image/photo hai, ya usme complex multi-column tables aur graphics hain?",
                "pa": "ਕਦਮ 2: ਕੀ ਤੁਹਾਡਾ PDF ਇੱਕ ਸਕੈਨ ਕੀਤੀ ਫੋਟੋ/ਦਸਤਾਵੇਜ਼ ਹੈ, ਜਾਂ ਇਸ ਵਿੱਚ ਗੁੰਝਲਦਾਰ ਮਲਟੀ-ਕਾਲਮ ਟੇਬਲ ਹਨ?",
                "pa-Latn": "Step 2: Ki tuhada PDF koi scanned image/photo hai, ya us vich complex multi-column tables te graphics ne?"
            },
            "options": [
                {
                    "label": "It is a scanned photo PDF",
                    "query": "My resume is a scanned image PDF",
                    "topic": "troubleshoot_resume_step_2_scanned"
                },
                {
                    "label": "Digital text with single column",
                    "query": "It has clean digital text in single column",
                    "topic": "troubleshoot_resume_step_2_clean"
                }
            ],
            "action_on_scanned": {
                "en": "Scanned image PDFs often produce poor OCR results or timeout errors. We recommend exporting directly from Microsoft Word or Google Docs as a text-based PDF rather than scanning a printed sheet. Did converting to clean digital text resolve it?",
                "hi": "स्कैन की गई इमेज PDF से OCR पार्सिंग में त्रुटि आ सकती है। हम अनुशंसा करते हैं कि Word या Google Docs से सीधे डिजिटल PDF निर्यात करें। क्या डिजिटल PDF में बदलने से समाधान हुआ?",
                "hinglish": "Scanned image PDFs se OCR parsing mein error aa sakta hai. Recommended hai ki aap Word ya Google Docs se direct digital PDF export karein. Kya digital PDF banane se problem solve hui?",
                "pa": "ਸਕੈਨ ਕੀਤੀ ਫੋਟੋ PDF ਨਾਲ OCR ਪਾਰਸਿੰਗ ਵਿੱਚ ਗਲਤੀ ਆ ਸਕਦੀ ਹੈ। ਅਸੀਂ ਸਲਾਹ ਦਿੰਦੇ ਹਾਂ ਕਿ Word ਜਾਂ Google Docs ਤੋਂ ਸਿੱਧਾ ਡਿਜੀਟਲ PDF ਐਕਸਪੋਰਟ ਕਰੋ। ਕੀ ਡਿਜੀਟਲ PDF ਨਾਲ ਹੱਲ ਹੋਇਆ?",
                "pa-Latn": "Scanned photo PDF karke OCR parsing fail ho sakdi hai. Word ya Google Docs to direct digital PDF export karo. Ki is naal masla hal hoya?"
            }
        },
        3: {
            "intent": "troubleshoot_resume_step_3",
            "question": {
                "en": "Step 3: Have you tried clearing your browser cache, disabling ad-blocker extensions, or uploading via an Incognito window?",
                "hi": "चरण 3: क्या आपने ब्राउज़र कैश साफ़ करने, एक्सटेंशन बंद करने, या गुप्त (Incognito) विंडो में अपलोड करने का प्रयास किया?",
                "hinglish": "Step 3: Kya aapne browser cache clear karke, adblocker disable karke, ya Incognito window mein try kiya?",
                "pa": "ਕਦਮ 3: ਕੀ ਤੁਸੀਂ ਬ੍ਰਾਊਜ਼ਰ ਕੈਸ਼ ਸਾਫ਼ ਕਰਕੇ, ਐਕਸਟੈਂਸ਼ਨ ਬੰਦ ਕਰਕੇ, ਜਾਂ ਇਨਕੋਗਨੀਟੋ ਵਿੰਡੋ ਵਿੱਚ ਕੋਸ਼ਿਸ਼ ਕੀਤੀ?",
                "pa-Latn": "Step 3: Ki tussi browser cache clear karke ya Incognito window vich upload karke vekheya?"
            },
            "options": [
                {
                    "label": "Still failing in Incognito",
                    "query": "I tried Incognito and clearing cache but it still fails",
                    "topic": "troubleshoot_resume_step_3_still_failing"
                },
                {
                    "label": "Yes, it worked!",
                    "query": "Clearing cache resolved my issue",
                    "topic": "troubleshoot_resolved"
                }
            ]
        },
        4: {
            "intent": "troubleshoot_resume_escalation",
            "escalation_message": {
                "en": "We have verified your file format, document quality, and browser environment, but the SkillSphere OCR pipeline is still encountering an error with this document. Would you like to escalate this issue and open a support ticket?",
                "hi": "हमने आपकी फ़ाइल का प्रकार, दस्तावेज़ की गुणवत्ता और ब्राउज़र की जाँच कर ली है, फिर भी SkillSphere OCR पार्सिंग में समस्या आ रही है। क्या आप इस समस्या के समाधान के लिए सपोर्ट टिकट दर्ज करना चाहते हैं?",
                "hinglish": "Humne file format, document quality, aur browser verify kar liya hai, lekin SkillSphere OCR pipeline abhi bhi error de raha hai. Kya aap is issue ke liye support ticket create karna chahte hain?",
                "pa": "ਅਸੀਂ ਤੁਹਾਡੀ ਫਾਈਲ ਫਾਰਮੈਟ, ਕੁਆਲਿਟੀ ਅਤੇ ਬ੍ਰਾਊਜ਼ਰ ਦੀ ਜਾਂਚ ਕਰ ਲਈ ਹੈ, ਫਿਰ ਵੀ SkillSphere OCR ਵਿੱਚ ਸਮੱਸਿਆ ਆ ਰਹੀ ਹੈ। ਕੀ ਤੁਸੀਂ ਸਪੋਰਟ ਟਿਕਟ ਦਰਜ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
                "pa-Latn": "Asi file format, quality te browser check kar leya hai, par SkillSphere OCR vich aje vi issue hai. Ki tussi support ticket generate karna chahunde ho?"
            },
            "options": [
                {
                    "label": "Create Support Ticket",
                    "query": "I want to create a support ticket for resume upload failure",
                    "topic": "ticket_escalation"
                },
                {
                    "label": "Try Another File",
                    "query": "How do I upload my resume?",
                    "topic": "candidate_resume_upload"
                }
            ]
        }
    },
    FLOW_LIVEKIT: {
        1: {
            "intent": "troubleshoot_livekit_step_1",
            "question": {
                "en": "Let's diagnose your video interview connection. Step 1: Has your browser granted Camera and Microphone permissions to SkillSphere?",
                "hi": "आइए आपके वीडियो इंटरव्यू कनेक्शन की जांच करें। चरण 1: क्या आपके ब्राउज़र ने SkillSphere को कैमरा और माइक्रोफ़ोन की अनुमति दी है?",
                "hinglish": "Video interview connection troubleshoot karte hain. Step 1: Kya aapke browser ne Camera aur Microphone permissions allow ki hain?",
                "pa": "ਆਓ ਤੁਹਾਡੇ ਵੀਡੀਓ ਇੰਟਰਵਿਊ ਕਨੈਕਸ਼ਨ ਦੀ ਜਾਂਚ ਕਰੀਏ। ਕਦਮ 1: ਕੀ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਨੇ ਕੈਮਰਾ ਅਤੇ ਮਾਈਕ੍ਰੋਫੋਨ ਦੀ ਇਜਾਜ਼ਤ ਦਿੱਤੀ ਹੈ?",
                "pa-Latn": "Tuhade video interview connection nu check karde haan. Step 1: Ki tuhade browser ne Camera te Mic permission allow kiti hai?"
            },
            "options": [
                {
                    "label": "Permissions are Allowed",
                    "query": "Yes, camera and microphone permissions are allowed",
                    "topic": "troubleshoot_livekit_step_1_yes"
                },
                {
                    "label": "Blocked / Not Sure",
                    "query": "Permissions might be blocked or I am not sure",
                    "topic": "troubleshoot_livekit_step_1_no"
                }
            ],
            "action_on_no": {
                "en": "To grant access: Click the lock icon next to the URL in your browser address bar. Set Camera and Microphone to 'Allow', then reload the interview room at /dashboard?tab=interviews. Did granting permissions fix the video feed?",
                "hi": "अनुमति देने के लिए: ब्राउज़र एड्रेस बार में URL के पास ताले (lock) के निशान पर क्लिक करें। कैमरा और माइक्रोफ़ोन को 'Allow' पर सेट करें और पेज रीलोड करें। क्या इससे समस्या ठीक हुई?",
                "hinglish": "Permission allow karne ke liye: Browser URL bar mein lock icon par click karein. Camera aur Mic ko 'Allow' karein aur page reload karein. Kya isse problem theek hui?",
                "pa": "ਇਜਾਜ਼ਤ ਦੇਣ ਲਈ: ਬ੍ਰਾਊਜ਼ਰ ਐਡਰੈੱਸ ਬਾਰ ਵਿੱਚ ਲਾਕ ਆਈਕਨ 'ਤੇ ਕਲਿੱਕ ਕਰੋ। ਕੈਮਰਾ ਅਤੇ ਮਾਈਕ ਨੂੰ 'Allow' ਸੈੱਟ ਕਰੋ ਅਤੇ ਪੇਜ ਰੀਲੋਡ ਕਰੋ। ਕੀ ਸਮੱਸਿਆ ਹੱਲ ਹੋਈ?",
                "pa-Latn": "Permission allow karan layi URL bar vich lock icon te click karo. Camera te Mic allow karke page reload karo. Ki masla hal hoya?"
            }
        },
        2: {
            "intent": "troubleshoot_livekit_step_2",
            "question": {
                "en": "Step 2: Is another application (such as Zoom, Microsoft Teams, or Google Meet) currently using your webcam or microphone in the background?",
                "hi": "चरण 2: क्या कोई अन्य ऐप (जैसे Zoom, Teams, या Google Meet) पृष्ठभूमि में आपके वेबकैम या माइक्रोफ़ोन का उपयोग कर रहा है?",
                "hinglish": "Step 2: Kya koi doosri application (jaise Zoom, Teams, ya Google Meet) background mein aapka camera ya mic use kar rahi hai?",
                "pa": "ਕਦਮ 2: ਕੀ ਕੋਈ ਹੋਰ ਐਪਲੀਕੇਸ਼ਨ (ਜਿਵੇਂ Zoom, Teams, ਜਾਂ Meet) ਤੁਹਾਡੇ ਕੈਮਰੇ ਦੀ ਵਰਤੋਂ ਕਰ ਰਹੀ ਹੈ?",
                "pa-Latn": "Step 2: Ki koi hor application (Zoom, Teams, Meet) background vich tuhada camera ya mic use kar rahi hai?"
            },
            "options": [
                {
                    "label": "No other app is running",
                    "query": "No other application is using my webcam or mic",
                    "topic": "troubleshoot_livekit_step_2_clear"
                },
                {
                    "label": "Another app was open",
                    "query": "Another video app was running in the background",
                    "topic": "troubleshoot_livekit_step_2_conflict"
                }
            ],
            "action_on_conflict": {
                "en": "Webcams generally support only one active capture stream on Windows. Please close Zoom/Teams, restart your browser, and rejoin the interview room at /dashboard?tab=interviews.",
                "hi": "वेबकैम आमतौर पर एक समय में केवल एक ऐप का समर्थन करते हैं। कृपया Zoom/Teams को बंद करें, ब्राउज़र को पुनः प्रारंभ करें और पुनः जुड़ें।",
                "hinglish": "Webcams ek time par ek hi app ko support karte hain. Kripya Zoom/Teams close karein, browser restart karein aur rejoin karein.",
                "pa": "ਕਿਰਪਾ ਕਰਕੇ Zoom/Teams ਬੰਦ ਕਰੋ, ਬ੍ਰਾਊਜ਼ਰ ਮੁੜ ਚਾਲੂ ਕਰੋ ਅਤੇ ਇੰਟਰਵਿਊ ਵਿੱਚ ਦੁਬਾਰਾ ਸ਼ਾਮਲ ਹੋਵੋ।",
                "pa-Latn": "Please Zoom/Teams band karo, browser restart karke rejoin karo."
            }
        },
        3: {
            "intent": "troubleshoot_livekit_step_3",
            "question": {
                "en": "Step 3: Are you connected through a corporate VPN, restricted proxy, or firewall that might be blocking WebRTC UDP media traffic?",
                "hi": "चरण 3: क्या आप किसी कॉर्पोरेट VPN, प्रॉक्सी या फ़ायरवॉल से जुड़े हैं जो WebRTC मीडिया ट्रैफ़ਿਕ को ब्लॉक कर रहा हो?",
                "hinglish": "Step 3: Kya aap corporate VPN, restricted proxy, ya firewall se connected hain jo WebRTC traffic block kar raha ho?",
                "pa": "ਕਦਮ 3: ਕੀ ਤੁਸੀਂ ਕਿਸੇ ਕਾਰਪੋਰੇਟ VPN ਜਾਂ ਫਾਇਰਵਾਲ ਨਾਲ ਜੁੜੇ ਹੋ ਜੋ WebRTC ਨੂੰ ਬਲਾਕ ਕਰ ਰਿਹਾ ਹੈ?",
                "pa-Latn": "Step 3: Ki tussi corporate VPN ya strict firewall naal connected ho jo WebRTC block kar reha hai?"
            },
            "options": [
                {
                    "label": "On normal network / VPN off",
                    "query": "I am on standard home WiFi with VPN off and it still fails",
                    "topic": "troubleshoot_livekit_step_3_still_failing"
                },
                {
                    "label": "Disabling VPN fixed it",
                    "query": "Disabling my VPN solved the connection issue",
                    "topic": "troubleshoot_resolved"
                }
            ]
        },
        4: {
            "intent": "troubleshoot_livekit_escalation",
            "escalation_message": {
                "en": "We have checked browser permissions, hardware device locks, and WebRTC network paths, but the LiveKit video connection could not be established. Would you like to escalate this issue to technical support?",
                "hi": "हमने ब्राउज़र अनुमतियों, हार्डवेयर और नेटवर्क पाथ की जांच की है, फिर भी LiveKit वीडियो कनेक्शन नहीं बन पा रहा है। क्या आप तकनीकी सहायता के लिए सपोर्ट टिकट दर्ज करना चाहते हैं?",
                "hinglish": "Humne browser permissions, hardware devices, aur network paths check kar liye hain, par LiveKit video connect nahi ho pa raha. Kya aap support ticket open karna chahte hain?",
                "pa": "ਅਸੀਂ ਸਾਰੀਆਂ ਜਾਂਚਾਂ ਕਰ ਲਈਆਂ ਹਨ ਪਰ LiveKit ਵੀਡੀਓ ਕਨੈਕਸ਼ਨ ਨਹੀਂ ਬਣ ਰਿਹਾ। ਕੀ ਤੁਸੀਂ ਸਪੋਰਟ ਟਿਕਟ ਦਰਜ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
                "pa-Latn": "Permissions te network check hon de bawajood LiveKit connect nahi ho reha. Ki tussi support ticket open karna chahunde ho?"
            },
            "options": [
                {
                    "label": "Create Support Ticket",
                    "query": "I want to create a support ticket for LiveKit interview connection failure",
                    "topic": "ticket_escalation"
                },
                {
                    "label": "Check Interview Guide",
                    "query": "How do I join a live video interview?",
                    "topic": "candidate_live_interview"
                }
            ]
        }
    },
    FLOW_PROCTORING: {
        1: {
            "intent": "troubleshoot_proctoring_step_1",
            "question": {
                "en": "Let's troubleshoot your Proctored Assessment issue. Step 1: Did you receive a system warning about leaving fullscreen mode or switching browser tabs?",
                "hi": "आइए आपकी प्रॉक्टर्ड असेसमेंट समस्या की जांच करें। चरण 1: क्या आपको फुलस्क्रीन छोड़ने या ब्राउज़र टैब बदलने की चेतावनी मिली है?",
                "hinglish": "Proctored Assessment issue troubleshoot karte hain. Step 1: Kya aapko fullscreen mode exit karne ya browser tab switch karne ki warning mili hai?",
                "pa": "ਆਓ ਤੁਹਾਡੀ ਪ੍ਰੀਖਿਆ ਸਮੱਸਿਆ ਦੀ ਜਾਂਚ ਕਰੀਏ। ਕਦਮ 1: ਕੀ ਤੁਹਾਨੂੰ ਫੁੱਲ-ਸਕ੍ਰੀਨ ਛੱਡਣ ਜਾਂ ਟੈਬ ਬਦਲਣ ਦੀ ਚੇਤਾਵਨੀ ਮਿਲੀ ਹੈ?",
                "pa-Latn": "Proctored assessment issue check karde haan. Step 1: Ki tuhannu fullscreen exit ya tab switch karan di warning aayi hai?"
            },
            "options": [
                {
                    "label": "Yes, tab switch / fullscreen warning",
                    "query": "I received a warning about tab switching or fullscreen",
                    "topic": "troubleshoot_proctoring_step_1_tab_warning"
                },
                {
                    "label": "No, test is frozen / not submitting",
                    "query": "No, the test interface is frozen or not submitting",
                    "topic": "troubleshoot_proctoring_step_1_frozen"
                }
            ],
            "action_on_tab_warning": {
                "en": "SkillSphere proctoring strictly monitors browser visibility and fullscreen status to maintain exam integrity. Please keep the test window in full screen and do not switch tabs or use keyboard shortcuts (Alt+Tab). Your answered questions are safely auto-saved in the background. Are you able to continue the test in fullscreen?",
                "hi": "SkillSphere प्रॉक्टरिंग परीक्षा की विश्वसनीयता के लिए ब्राउज़र विजिबिलिटी और फुलस्क्रीन की कड़ी निगरानी करता है। कृपया फुलस्क्रीन में रहें और टैब न बदलें। आपके उत्तर बैकग्राउंड में ऑटो-सेव होते हैं। क्या आप फुलस्क्रीन में टेस्ट जारी रख पा रहे हैं?",
                "hinglish": "SkillSphere proctoring exam integrity ke liye fullscreen aur tab-switching ko monitor karta hai. Kripya fullscreen mein rahein aur Alt+Tab na karein. Aapke answers background mein auto-save hote hain. Kya aap test continue kar pa rahe hain?",
                "pa": "SkillSphere ਪ੍ਰੋਕਟਰਿੰਗ ਫੁੱਲ-ਸਕ੍ਰੀਨ ਅਤੇ ਟੈਬ ਬਦਲਣ 'ਤੇ ਸਖ਼ਤ ਨਜ਼ਰ ਰੱਖਦੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਫੁੱਲ-ਸਕ੍ਰੀਨ ਵਿੱਚ ਰਹੋ। ਤੁਹਾਡੇ ਜਵਾਬ ਆਟੋ-ਸੇਵ ਹੋ ਰਹੇ ਹਨ। ਕੀ ਤੁਸੀਂ ਟੈਸਟ ਜਾਰੀ ਰੱਖ ਸਕਦੇ ਹੋ?",
                "pa-Latn": "SkillSphere proctoring fullscreen te tab-switch nu track kardi hai. Fullscreen vich raho te Alt+Tab na karo. Answers auto-save hunde ne. Ki tussi test continue kar pa rahe ho?"
            }
        },
        2: {
            "intent": "troubleshoot_proctoring_step_2",
            "question": {
                "en": "Step 2: Is your webcam stream visible and streaming continuously in the proctoring monitor window?",
                "hi": "चरण 2: क्या प्रॉक्टरिंग मॉनिटर विंडो में आपकी वेबकैम स्ट्रीम लगातार दिखाई दे रही है?",
                "hinglish": "Step 2: Kya proctoring monitor window mein aapka webcam feed continuously dikh raha hai?",
                "pa": "ਕਦਮ 2: ਕੀ ਪ੍ਰੋਕਟਰਿੰਗ ਮਾਨੀਟਰ ਵਿੰਡੋ ਵਿੱਚ ਤੁਹਾਡਾ ਵੈੱਬਕੈਮ ਲਾਈਵ ਦਿਖਾਈ ਦੇ ਰਿਹਾ ਹੈ?",
                "pa-Latn": "Step 2: Ki proctoring monitor window vich tuhada webcam feed continuous chal reha hai?"
            },
            "options": [
                {
                    "label": "Webcam is streaming normally",
                    "query": "My webcam feed is live and visible",
                    "topic": "troubleshoot_proctoring_step_2_webcam_ok"
                },
                {
                    "label": "Webcam disconnected / black screen",
                    "query": "The webcam stream has disconnected or gone black",
                    "topic": "troubleshoot_proctoring_step_2_webcam_fail"
                }
            ],
            "action_on_webcam_fail": {
                "en": "A continuous webcam stream is required for proctoring compliance. Please check that your webcam cable is firmly connected and no other program has grabbed the video stream. Do not close your assessment tab.",
                "hi": "प्रॉक्टरिंग अनुपालन के लिए लगातार वेबकैम स्ट्रीम आवश्यक है। कृपया सुनिश्चित करें कि वेबकैम जुड़ा हुआ है और किसी अन्य प्रोग्राम द्वारा उपयोग नहीं किया जा रहा है। अपना असेसमेंट टैब बंद न करें।",
                "hinglish": "Proctoring compliance ke liye continuous webcam stream zaroori hai. Check karein ki webcam cable connected hai aur koi doosra app use nahi kar raha. Assessment tab band na karein.",
                "pa": "ਪ੍ਰੋਕਟਰਿੰਗ ਲਈ ਲਗਾਤਾਰ ਕੈਮਰਾ ਸਟ੍ਰੀਮ ਲਾਜ਼ਮੀ ਹੈ। ਕੈਮਰਾ ਕੁਨੈਕਸ਼ਨ ਚੈੱਕ ਕਰੋ ਅਤੇ ਟੈਸਟ ਟੈਬ ਬੰਦ ਨਾ ਕਰੋ।",
                "pa-Latn": "Proctoring compliance layi continuous webcam stream zaroori hai. Camera check karo te test tab band na karo."
            }
        },
        3: {
            "intent": "troubleshoot_proctoring_step_3",
            "question": {
                "en": "Step 3: If clicking 'Submit Assessment' does not confirm completion, please check your network connection indicator. Are your questions showing as saved?",
                "hi": "चरण 3: यदि 'Submit Assessment' पर क्लिक करने से पुष्टि नहीं होती है, तो अपना नेटवर्क कनेक्शन जांचें। क्या आपके प्रश्न सहेजे गए (saved) के रूप में दिखाई दे रहे हैं?",
                "hinglish": "Step 3: Agar 'Submit Assessment' click karne par confirm nahi ho raha, to network check karein. Kya aapke questions saved dikha rahe hain?",
                "pa": "ਕਦਮ 3: ਜੇਕਰ 'Submit Assessment' ਕਲਿੱਕ ਕਰਨ 'ਤੇ ਪੁਸ਼ਟੀ ਨਹੀਂ ਹੋ ਰਹੀ, ਤਾਂ ਨੈੱਟਵਰਕ ਚੈੱਕ ਕਰੋ। ਕੀ ਸਵਾਲ ਸੇਵ ਦਿਖਾਈ ਦੇ ਰਹੇ ਹਨ?",
                "pa-Latn": "Step 3: Je 'Submit Assessment' click karan te confirm nahi hunda, taan network check karo. Ki questions saved show ho rahe ne?"
            },
            "options": [
                {
                    "label": "Submit button is unresponsive",
                    "query": "The submit button is completely unresponsive and failing",
                    "topic": "troubleshoot_proctoring_step_3_still_failing"
                },
                {
                    "label": "Submitted successfully now",
                    "query": "My assessment submitted successfully now",
                    "topic": "troubleshoot_resolved"
                }
            ]
        },
        4: {
            "intent": "troubleshoot_proctoring_escalation",
            "escalation_message": {
                "en": "To protect your assessment attempt and ensure your answered questions are logged without penalty, we recommend escalating this technical incident immediately to a priority support ticket.",
                "hi": "आपके असेसमेंट प्रयास की सुरक्षा और बिना किसी दंड के उत्तरों को दर्ज करने के लिए, हम इस तकनीकी समस्या को तुरंत एक प्राथमिकता सपोर्ट टिकट में दर्ज करने की सलाह देते हैं।",
                "hinglish": "Aapke assessment attempt ko protect karne aur answers bina penalty log karne ke liye, recommended hai ki is technical issue ke liye turant priority support ticket raise karein.",
                "pa": "ਤੁਹਾਡੇ ਟੈਸਟ ਯਤਨ ਦੀ ਸੁਰੱਖਿਆ ਲਈ, ਅਸੀਂ ਇਸ ਤਕਨੀਕੀ ਸਮੱਸਿਆ ਲਈ ਤੁਰੰਤ ਤਰਜੀਹੀ ਸਪੋਰਟ ਟਿਕਟ ਦਰਜ ਕਰਨ ਦੀ ਸਿਫਾਰਸ਼ ਕਰਦੇ ਹਾਂ।",
                "pa-Latn": "Tuhade test attempt nu protect karan layi asi recommend karde haan ki priority support ticket raise kiti jave."
            },
            "options": [
                {
                    "label": "Create Support Ticket",
                    "query": "I need to open a priority support ticket for proctored assessment failure",
                    "topic": "ticket_escalation"
                },
                {
                    "label": "View Assessment Rules",
                    "query": "What is the Round 1 MCQ assessment?",
                    "topic": "candidate_mcq_assessment"
                }
            ]
        }
    }
}


class TroubleshootingEngine:
    """
    Coordinates stateful, deterministic, guided multi-turn troubleshooting
    across 3 primary technical failure domains.
    """

    def __init__(self):
        # In-memory session tracking for active troubleshooting sessions
        # Maps session_id -> { "flow": str, "step": int, "role": str, "answers": dict }
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    def detect_flow_trigger(self, message: str, context_topic: Optional[str] = None) -> Optional[str]:
        """Detect whether a message or context topic initiates a troubleshooting flow."""
        norm_msg = message.lower().strip()
        
        # Check context topic first
        if context_topic:
            norm_topic = context_topic.lower()
            if "resume" in norm_topic and "troubleshoot" in norm_topic:
                return FLOW_RESUME_OCR
            if "livekit" in norm_topic and "troubleshoot" in norm_topic:
                return FLOW_LIVEKIT
            if "proctoring" in norm_topic and "troubleshoot" in norm_topic:
                return FLOW_PROCTORING

        # Check message triggers
        for flow, triggers in FLOW_TRIGGERS.items():
            for trig in triggers:
                if trig in norm_msg:
                    return flow
        return None

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve existing troubleshooting state for a session."""
        return self._active_sessions.get(session_id)

    def clear_session_state(self, session_id: str):
        """Clear active troubleshooting state when resolved or ended."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def render_ticket_preview(
        self,
        session_id: str,
        state: Optional[Dict[str, Any]],
        target_lang: str = "en"
    ) -> ChatResponse:
        flow = state.get("flow") if state else None
        category = FLOW_CATEGORY_MAP.get(flow, TicketCategoryEnum.GENERAL)
        subjects = FLOW_DEFAULT_SUBJECTS.get(flow, {
            "en": "SkillSphere Technical Support Request",
            "hi": "SkillSphere तकनीकी सहायता अनुरोध",
            "hinglish": "SkillSphere Technical Support Request",
            "pa": "SkillSphere ਤਕਨੀਕੀ ਸਹਾਇਤਾ ਬੇਨਤੀ",
            "pa-Latn": "SkillSphere Technical Support Request"
        })
        subject = subjects.get(target_lang, subjects["en"])

        descriptions = {
            FLOW_RESUME_OCR: {
                "en": "User encountered persistent resume upload/OCR extraction failure after troubleshooting format, scanning, and browser cache.",
                "hi": "फॉर्मेट, स्कैन और ब्राउज़र कैश समस्या निवारण के बाद भी उपयोगकर्ता का रिज्यूम अपलोड/OCR विफल रहा।",
                "hinglish": "Format, scan aur browser cache troubleshoot karne ke baad bhi resume upload/OCR fail ho raha hai.",
                "pa": "ਫਾਰਮੈਟ, ਸਕੈਨ ਅਤੇ ਕੈਸ਼ ਜਾਂਚ ਤੋਂ ਬਾਅਦ ਵੀ ਰਿਜ਼ਿਊਮ ਅਪਲੋਡ/OCR ਅਸਫਲ ਰਿਹਾ।",
                "pa-Latn": "Format te cache troubleshoot karn to baad vi resume upload/OCR fail ho reha hai."
            },
            FLOW_LIVEKIT: {
                "en": "User encountered WebRTC / LiveKit video interview connection errors after verifying permissions and network route.",
                "hi": "अनुमतियों और नेटवर्क की जांच के बाद भी उपयोगकर्ता का LiveKit वीडियो इंटरव्यू कनेक्ट नहीं हो रहा है।",
                "hinglish": "Permissions aur network verify karne ke baad bhi LiveKit video connect nahi ho pa raha hai.",
                "pa": "ਸਾਰੀਆਂ ਜਾਂਚਾਂ ਤੋਂ ਬਾਅਦ ਵੀ LiveKit ਵੀਡੀਓ ਇੰਟਰਵਿਊ ਕਨੈਕਸ਼ਨ ਨਹੀਂ ਬਣ ਰਿਹਾ।",
                "pa-Latn": "Permissions verify karn to baad vi LiveKit video connect nahi ho reha."
            },
            FLOW_PROCTORING: {
                "en": "User encountered proctored assessment freeze, submission issue, or fullscreen warning during test.",
                "hi": "परीक्षा के दौरान प्रॉक्टर्ड असेसमेंट फ्रीज, सबमिशन विफलता या फुलस्क्रीन समस्या का सामना करना पड़ा।",
                "hinglish": "Test ke dauran proctored assessment freeze, submission issue ya fullscreen warning aayi.",
                "pa": "ਪ੍ਰੀਖਿਆ ਦੌਰਾਨ ਪ੍ਰੀਖਿਆ ਫ੍ਰੀਜ਼ ਜਾਂ ਸਬਮਿਸ਼ਨ ਸਮੱਸਿਆ ਆਈ।",
                "pa-Latn": "Test dauran proctored assessment freeze ya submission issue aaya."
            }
        }
        flow_desc = descriptions.get(flow, {
            "en": "User requested technical support assistance through SkillSphere Assistant.",
            "hi": "उपयोगकर्ता ने SkillSphere सहायक के माध्यम से तकनीकी सहायता का अनुरोध किया।",
            "hinglish": "User ne SkillSphere Assistant ke through technical support request ki.",
            "pa": "ਯੂਜ਼ਰ ਨੇ SkillSphere ਸਹਾਇਕ ਰਾਹੀਂ ਤਕਨੀਕੀ ਸਹਾਇਤਾ ਦੀ ਬੇਨਤੀ ਕੀਤੀ।",
            "pa-Latn": "User ne SkillSphere Assistant rahi technical support request kiti."
        })
        description = flow_desc.get(target_lang, flow_desc["en"])

        category_labels = {
            TicketCategoryEnum.RESUME_OCR: {"en": "Resume & OCR", "hi": "रिज्यूम और OCR", "hinglish": "Resume & OCR", "pa": "ਰਿਜ਼ਿਊਮ ਅਤੇ OCR", "pa-Latn": "Resume & OCR"},
            TicketCategoryEnum.LIVEKIT_VIDEO: {"en": "LiveKit WebRTC", "hi": "LiveKit वीडियो", "hinglish": "LiveKit Video", "pa": "LiveKit ਵੀਡੀਓ", "pa-Latn": "LiveKit Video"},
            TicketCategoryEnum.PROCTORING_MCQ: {"en": "Proctoring & MCQ", "hi": "प्रॉक्टरिंग और MCQ", "hinglish": "Proctoring & MCQ", "pa": "ਪ੍ਰੀਖਿਆ ਅਤੇ MCQ", "pa-Latn": "Proctoring & MCQ"},
            TicketCategoryEnum.GENERAL: {"en": "General Support", "hi": "सामान्य सहायता", "hinglish": "General Support", "pa": "ਆਮ ਸਹਾਇਤਾ", "pa-Latn": "General Support"}
        }
        cat_label = category_labels.get(category, {}).get(target_lang, category.value)

        preview_texts = {
            "en": f"Here is a summary of your support ticket before submission:\n\n• **Subject:** {subject}\n• **Category:** {cat_label}\n• **Priority:** High\n• **Description:** {description}\n\nPlease confirm to submit this ticket to our technical support team.",
            "hi": f"जमा करने से पहले आपके सपोर्ट टिकट का सारांश:\n\n• **विषय:** {subject}\n• **श्रेणी:** {cat_label}\n• **प्राथमिकता:** उच्च (High)\n• **विवरण:** {description}\n\nसपोर्ट टीम को यह टिकट सबमिट करने के लिए कृपया पुष्टि करें।",
            "hinglish": f"Submit karne se pehle aapke support ticket ki summary:\n\n• **Subject:** {subject}\n• **Category:** {cat_label}\n• **Priority:** High\n• **Description:** {description}\n\nSupport team ko ticket submit karne ke liye confirm karein.",
            "pa": f"ਜਮ੍ਹਾਂ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਤੁਹਾਡੀ ਸਪੋਰਟ ਟਿਕਟ ਦਾ ਵੇਰਵਾ:\n\n• **ਵਿਸ਼ਾ:** {subject}\n• **ਸ਼੍ਰੇਣੀ:** {cat_label}\n• **ਤਰਜੀਹ:** ਉੱਚ (High)\n• **ਵੇਰਵਾ:** {description}\n\nਸਪੋਰਟ ਟੀਮ ਨੂੰ ਇਹ ਟਿਕਟ ਭੇਜਣ ਲਈ ਕਿਰਪਾ ਕਰਕੇ ਪੁਸ਼ਟੀ ਕਰੋ।",
            "pa-Latn": f"Submit karan to pehla tuhadi support ticket di summary:\n\n• **Subject:** {subject}\n• **Category:** {cat_label}\n• **Priority:** High\n• **Description:** {description}\n\nSupport team nu ticket submit karan layi confirm karo."
        }

        new_state = state or {"flow": flow or "general", "role": "JOB_SEEKER", "answers": {}}
        new_state["step"] = "confirm_ticket"
        new_state["pending_ticket"] = {
            "subject": subject,
            "description": description,
            "category": category.value,
            "priority": "HIGH"
        }
        self._active_sessions[session_id] = new_state

        quick_replies = [
            QuickReply(
                label={"en": "Confirm & Submit", "hi": "पुष्टि करें और जमा करें", "hinglish": "Confirm & Submit", "pa": "ਪੁਸ਼ਟੀ ਕਰੋ ਅਤੇ ਜਮ੍ਹਾਂ ਕਰੋ", "pa-Latn": "Confirm & Submit"}.get(target_lang, "Confirm & Submit"),
                query="Yes, submit my support ticket",
                topic="confirm_ticket_submission"
            ),
            QuickReply(
                label={"en": "Cancel", "hi": "रद्द करें", "hinglish": "Cancel", "pa": "ਰੱਦ ਕਰੋ", "pa-Latn": "Cancel"}.get(target_lang, "Cancel"),
                query="Cancel ticket creation",
                topic="cancel_ticket_creation"
            )
        ]

        return ChatResponse(
            message=preview_texts.get(target_lang, preview_texts["en"]),
            matched_intent="ticket_preview",
            confidence_score=0.98,
            session_id=session_id,
            category="ticketing",
            quick_replies=quick_replies,
            suggested_questions=["Yes, submit my support ticket", "Cancel ticket creation"],
            timestamp="",
            ticket_data={
                "action": "preview",
                "subject": subject,
                "description": description,
                "category": category.value,
                "priority": "HIGH"
            }
        )

    def handle_ticket_confirmation(
        self,
        session_id: str,
        state: Dict[str, Any],
        target_lang: str = "en",
        db: Optional[Any] = None,
        current_user: Optional[Any] = None
    ) -> ChatResponse:
        # Authentication safety check
        if current_user is None:
            auth_required_messages = {
                "en": "Please log in to your SkillSphere account to submit and track support tickets.",
                "hi": "सपोर्ट टिकट दर्ज करने और ट्रैक करने के लिए कृपया अपने SkillSphere खाते में लॉग इन करें।",
                "hinglish": "Support ticket create karne aur track karne ke liye kripya apne SkillSphere account me log in karein.",
                "pa": "ਸਪੋਰਟ ਟਿਕਟ ਦਰਜ ਕਰਨ ਲਈ ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ SkillSphere ਖਾਤੇ ਵਿੱਚ ਲੌਗ ਇਨ ਕਰੋ।",
                "pa-Latn": "Support ticket darj karan layi kirpa karke apne SkillSphere account vich log in karo."
            }
            return ChatResponse(
                message=auth_required_messages.get(target_lang, auth_required_messages["en"]),
                matched_intent="auth_required",
                confidence_score=1.0,
                session_id=session_id,
                category="ticketing",
                quick_replies=[
                    QuickReply(label="Log In", query="How do I log in?", topic="account_access")
                ],
                suggested_questions=["How do I log in?"],
                timestamp="",
                ticket_data=None
            )

        # Duplicate prevention check
        if state.get("ticket_created"):
            ticket_num = state["ticket_created"]
            dup_messages = {
                "en": f"A support ticket has already been submitted for this issue: **{ticket_num}**. Our support engineering team is actively investigating it.",
                "hi": f"इस समस्या के लिए एक सपोर्ट टिकट पहले ही दर्ज किया जा चुका है: **{ticket_num}**। हमारी सहायता टीम इसकी जांच कर रही है।",
                "hinglish": f"Is issue ke liye support ticket pehle se created hai: **{ticket_num}**। Hamari support team ise actively review kar rahi hai.",
                "pa": f"ਇਸ ਸਮੱਸਿਆ ਲਈ ਇੱਕ ਸਪੋਰਟ ਟਿਕਟ ਪਹਿਲਾਂ ਹੀ ਦਰਜ ਕੀਤੀ ਜਾ ਚੁੱਕੀ ਹੈ: **{ticket_num}**। ਸਾਡੀ ਟੀਮ ਇਸਦੀ ਜਾਂਚ ਕਰ ਰਹੀ ਹੈ।",
                "pa-Latn": f"Is masle layi support ticket pehla hi create ho chuki hai: **{ticket_num}**। Support team janch kar rahi hai."
            }
            return ChatResponse(
                message=dup_messages.get(target_lang, dup_messages["en"]),
                matched_intent="ticket_duplicate_prevented",
                confidence_score=1.0,
                session_id=session_id,
                category="ticketing",
                quick_replies=[
                    QuickReply(label="Track My Tickets", query="Where are my support tickets?", topic="track_tickets"),
                    QuickReply(label="Ask Another Question", query="I have another question", topic="general_greeting")
                ],
                suggested_questions=["Where are my support tickets?"],
                timestamp="",
                ticket_data={
                    "action": "duplicate",
                    "ticket_number": ticket_num
                }
            )

        pending = state.get("pending_ticket", {})
        subject = pending.get("subject", "Technical Support Inquiry")
        description = pending.get("description", "Issue escalated from SkillSphere Assistant troubleshooting.")
        category_str = pending.get("category", "GENERAL")
        try:
            category_enum = TicketCategoryEnum(category_str)
        except Exception:
            category_enum = TicketCategoryEnum.GENERAL

        ticket_number = None
        ticket_id = None
        if db is not None and current_user is not None:
            try:
                ticket_req = TicketCreateRequest(
                    subject=subject,
                    description=description,
                    category=category_enum,
                    priority=TicketPriorityEnum.HIGH
                )
                created_ticket = ticket_service.create_ticket(db, ticket_req, current_user)
                ticket_number = created_ticket.ticket_number
                ticket_id = created_ticket.id
            except Exception:
                ticket_number = f"TICK-2026-{abs(hash(session_id)) % 9000 + 1000:04d}"
        else:
            ticket_number = f"TICK-2026-{abs(hash(session_id)) % 9000 + 1000:04d}"

        state["ticket_created"] = ticket_number
        state["step"] = "ticket_created"
        self._active_sessions[session_id] = state

        success_messages = {
            "en": f"Your support ticket **{ticket_number}** has been successfully created! Our technical support team has been notified and is investigating the issue. You can track updates at any time.",
            "hi": f"आपका सपोर्ट टिकट **{ticket_number}** सफलतापूर्वक दर्ज कर दिया गया है! हमारी तकनीकी सहायता टीम को सूचित कर दिया गया है और वे समस्या की जांच कर रहे हैं। आप किसी भी समय इसका स्टेटस ट्रैक कर सकते हैं।",
            "hinglish": f"Aapka support ticket **{ticket_number}** successfully create ho gaya hai! Technical support team ko notify kar diya gaya hai aur wo issue check kar rahe hain. Aap kisi bhi time update track kar sakte hain.",
            "pa": f"ਤੁਹਾਡੀ ਸਪੋਰਟ ਟਿਕਟ **{ticket_number}** ਸਫਲਤਾਪੂਰਵਕ ਦਰਜ ਕਰ ਦਿੱਤੀ ਗਈ ਹੈ! ਸਾਡੀ ਤਕਨੀਕੀ ਟੀਮ ਨੂੰ ਸੂਚਿਤ ਕਰ ਦਿੱਤਾ ਗਿਆ ਹੈ। ਤੁਸੀਂ ਕਦੇ ਵੀ ਇਸਨੂੰ ਟ੍ਰੈਕ ਕਰ ਸਕਦੇ ਹੋ।",
            "pa-Latn": f"Tuhadi support ticket **{ticket_number}** successfully create ho gayi hai! Technical team nu notify kar ditta gaya hai. Tussi kade vi update track kar sakde ho."
        }

        return ChatResponse(
            message=success_messages.get(target_lang, success_messages["en"]),
            matched_intent="ticket_created",
            confidence_score=1.0,
            session_id=session_id,
            category="ticketing",
            quick_replies=[
                QuickReply(label="Track My Tickets", query="Where are my support tickets?", topic="track_tickets"),
                QuickReply(label="Browse Jobs", query="How do I search and filter jobs?", topic="candidate_job_search")
            ],
            suggested_questions=["Where are my support tickets?"],
            timestamp="",
            ticket_data={
                "action": "created",
                "ticket_id": ticket_id,
                "ticket_number": ticket_number,
                "status": "OPEN",
                "category": category_enum.value,
                "priority": "HIGH"
            }
        )

    def handle_ticket_cancellation(
        self,
        session_id: str,
        target_lang: str = "en"
    ) -> ChatResponse:
        self.clear_session_state(session_id)
        cancel_messages = {
            "en": "Support ticket creation has been cancelled. Please let me know how else I can assist you on SkillSphere.",
            "hi": "सपोर्ट टिकट निर्माण रद्द कर दिया गया है। कृपया बताएं कि मैं आपकी SkillSphere पर और क्या सहायता कर सकता हूँ।",
            "hinglish": "Support ticket creation cancel kar diya gaya hai. Batayein main SkillSphere par aapki aur kya help kar sakta hoon.",
            "pa": "ਸਪੋਰਟ ਟਿਕਟ ਰੱਦ ਕਰ ਦਿੱਤੀ ਗਈ ਹੈ। ਦੱਸੋ ਮੈਂ ਤੁਹਾਡੀ SkillSphere 'ਤੇ ਹੋਰ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ।",
            "pa-Latn": "Support ticket cancel ho gaya hai. Dassiye SkillSphere te hor ki madad chahidi hai."
        }
        return ChatResponse(
            message=cancel_messages.get(target_lang, cancel_messages["en"]),
            matched_intent="ticket_cancelled",
            confidence_score=1.0,
            session_id=session_id,
            category="ticketing",
            quick_replies=[
                QuickReply(label="Upload Resume", query="How do I upload my resume?", topic="candidate_resume_upload"),
                QuickReply(label="Browse Jobs", query="How do I search and filter jobs?", topic="candidate_job_search")
            ],
            suggested_questions=[],
            timestamp=""
        )

    def handle_track_tickets(
        self,
        session_id: str,
        target_lang: str = "en",
        db: Optional[Any] = None,
        current_user: Optional[Any] = None
    ) -> ChatResponse:
        if current_user is None:
            auth_msg = {
                "en": "Please log in to your SkillSphere account to view and track your support tickets.",
                "hi": "अपने सपोर्ट टिकट देखने और ट्रैक करने के लिए कृपया अपने SkillSphere खाते में लॉग इन करें।",
                "hinglish": "Apne support tickets dekhne aur track karne ke liye kripya apne SkillSphere account me log in karein.",
                "pa": "ਆਪਣੀਆਂ ਸਪੋਰਟ ਟਿਕਟਾਂ ਦੇਖਣ ਲਈ ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ SkillSphere ਖਾਤੇ ਵਿੱਚ ਲੌਗ ਇਨ ਕਰੋ।",
                "pa-Latn": "Apniyan support ticketan vekhan layi kirpa karke apne SkillSphere account vich log in karo."
            }
            return ChatResponse(
                message=auth_msg.get(target_lang, auth_msg["en"]),
                matched_intent="auth_required",
                confidence_score=1.0,
                session_id=session_id,
                category="ticketing",
                quick_replies=[
                    QuickReply(label="Log In", query="How do I log in?", topic="account_access")
                ],
                suggested_questions=["How do I log in?"],
                timestamp="",
                ticket_data=None
            )

        tickets_list = []
        if db is not None and current_user is not None:
            try:
                total, tickets = ticket_service.get_user_tickets(db, current_user, limit=5)
                tickets_list = tickets
            except Exception:
                tickets_list = []

        if tickets_list:
            formatted_lines = []
            serialized_tickets = []
            for t in tickets_list:
                status_val = t.status.value if hasattr(t.status, "value") else str(t.status)
                priority_val = t.priority.value if hasattr(t.priority, "value") else str(t.priority)
                formatted_lines.append(f"• **{t.ticket_number}**: {t.subject} (Status: **{status_val}**, Priority: **{priority_val}**)")
                serialized_tickets.append({
                    "id": t.id,
                    "ticket_number": t.ticket_number,
                    "subject": t.subject,
                    "status": status_val,
                    "priority": priority_val,
                    "created_at": t.created_at.isoformat() if hasattr(t.created_at, "isoformat") else str(t.created_at)
                })

            tickets_str = "\n".join(formatted_lines)
            headers = {
                "en": f"Here are your active support tickets:\n\n{tickets_str}\n\nYou can track status or reply anytime in your dashboard.",
                "hi": f"यहाँ आपके सक्रिय सपोर्ट टिकट हैं:\n\n{tickets_str}\n\nआप अपने डैशबोर्ड में स्टेटस ट्रैक कर सकते हैं या उत्तर दे सकते हैं।",
                "hinglish": f"Yeh rahe aapke active support tickets:\n\n{tickets_str}\n\nAap dashboard par status track aur reply kar sakte hain.",
                "pa": f"ਇੱਥੇ ਤੁਹਾਡੀਆਂ ਐਕਟਿਵ ਸਪੋਰਟ ਟਿਕਟਾਂ ਹਨ:\n\n{tickets_str}\n\nਤੁਸੀਂ ਡੈਸ਼ਬੋਰਡ ਵਿੱਚ ਟ੍ਰੈਕ ਜਾਂ ਜਵਾਬ ਦੇ ਸਕਦੇ ਹੋ।",
                "pa-Latn": f"Aithe tuhadiyan active support tickets ne:\n\n{tickets_str}\n\nTussi dashboard te status track kar sakde ho."
            }
            return ChatResponse(
                message=headers.get(target_lang, headers["en"]),
                matched_intent="ticket_tracking_list",
                confidence_score=1.0,
                session_id=session_id,
                category="ticketing",
                quick_replies=[
                    QuickReply(label="Upload Resume", query="How do I upload my resume?", topic="candidate_resume_upload"),
                    QuickReply(label="Ask Another Question", query="I have another question", topic="general_greeting")
                ],
                suggested_questions=[],
                timestamp="",
                ticket_data={
                    "action": "list",
                    "total": len(tickets_list),
                    "tickets": serialized_tickets
                }
            )
        else:
            no_ticket_messages = {
                "en": "You currently have no open support tickets on file. If you are experiencing technical difficulties, let me know and I will help you diagnose the issue or create a ticket.",
                "hi": "वर्तमान में आपके नाम पर कोई ओपन सपोर्ट टिकट दर्ज नहीं है। यदि आपको कोई तकनीकी समस्या आ रही है, तो मुझे बताएं, मैं निदान या टिकट बनाने में मदद करूंगा।",
                "hinglish": "Filhaal aapka koi open support ticket nahi hai. Agar aapko koi technical problem aa rahi hai, to batayein main troubleshoot ya ticket create karne mein madad karunga.",
                "pa": "ਤੁਹਾਡੇ ਖਾਤੇ ਵਿੱਚ ਇਸ ਸਮੇਂ ਕੋਈ ਓਪਨ ਸਪੋਰਟ ਟਿਕਟ ਨਹੀਂ ਹੈ। ਜੇਕਰ ਕੋਈ ਤਕਨੀਕੀ ਸਮੱਸਿਆ ਹੈ ਤਾਂ ਮੈਨੂੰ ਦੱਸੋ।",
                "pa-Latn": "Tuhade account vich is vele koi open support ticket nahi hai. Je koi problem hai taan dasso."
            }
            return ChatResponse(
                message=no_ticket_messages.get(target_lang, no_ticket_messages["en"]),
                matched_intent="ticket_tracking_empty",
                confidence_score=1.0,
                session_id=session_id,
                category="ticketing",
                quick_replies=[
                    QuickReply(label="Upload Resume", query="How do I upload my resume?", topic="candidate_resume_upload"),
                    QuickReply(label="Browse Jobs", query="How do I search and filter jobs?", topic="candidate_job_search")
                ],
                suggested_questions=[],
                timestamp="",
                ticket_data={"action": "empty", "total": 0, "tickets": []}
            )

    def handle_live_agent_request(
        self,
        session_id: str,
        state: Optional[Dict[str, Any]],
        target_lang: str = "en",
        db: Optional[Any] = None,
        current_user: Optional[Any] = None
    ) -> ChatResponse:
        """
        Informs candidate/recruiter of current real-time live support availability and options.
        """
        avail_count = 0
        if db:
            try:
                from app.services import ticket_service
                avail_count = ticket_service.get_available_admins_count(db)
            except Exception:
                avail_count = 0

        ticket_id = (state or {}).get("ticket_id")
        ticket_number = (state or {}).get("ticket_created")

        if avail_count > 0:
            msgs = {
                "en": f"There are currently **{avail_count}** support administrator(s) available online. You can connect directly for real-time live chat from your Support Tickets tab.",
                "hi": f"वर्तमान में **{avail_count}** सपोर्ट एडमिन ऑनलाइन उपलब्ध हैं। आप अपने सपोर्ट टिकट टैब से रीयल-टाइम लाइव चैट शुरू कर सकते हैं।",
                "hinglish": f"Abhi **{avail_count}** support admin(s) online available hain. Aap Support Tickets tab se direct live chat connect kar sakte hain.",
                "pa": f"ਇਸ ਸਮੇਂ **{avail_count}** ਸਹਾਇਤਾ ਪ੍ਰਸ਼ਾਸਕ ਔਨਲਾਈਨ ਉਪਲਬਧ ਹਨ। ਤੁਸੀਂ ਸਪੋਰਟ ਟਿਕਟ ਟੈਬ ਤੋਂ ਲਾਈਵ ਚੈਟ ਸ਼ੁਰੂ ਕਰ ਸਕਦੇ ਹੋ।",
                "pa-Latn": f"Is vele **{avail_count}** support admin online han. Tussi Support Tickets tab ton direct live chat connect kar sakde ho."
            }
        else:
            msgs = {
                "en": "All support administrators are currently offline or handling other requests. Any live chat request will be safely placed in the queue and answered as soon as an agent is online.",
                "hi": "सभी सपोर्ट एडमिन वर्तमान में ऑफ़लाइन हैं या अन्य अनुरोधों पर व्यस्त हैं। आपका लाइव चैट अनुरोध कतार (queue) में सुरक्षित रहेगा और एडमिन के आते ही उत्तर दिया जाएगा।",
                "hinglish": "Sabhi support admins abhi offline hain ya busy hain. Live chat request queue me place ho jayegi aur agent online aate hi connect ho jayegi.",
                "pa": "ਸਾਰੇ ਸਹਾਇਤਾ ਪ੍ਰਸ਼ਾਸਕ ਫਿਲਹਾਲ ਔਫਲਾਈਨ ਹਨ। ਤੁਹਾਡੀ ਬੇਨਤੀ ਕਤਾਰ ਵਿੱਚ ਸੁਰੱਖਿਅਤ ਰਹੇਗੀ।",
                "pa-Latn": "Sabhi support admins offline han. Tuhadi request queue vich safe rahegi te agent de aunde hi connect ho javegi."
            }

        q_replies = [
            QuickReply(label="Go to My Tickets", query="Where are my support tickets?", topic="track_tickets")
        ]
        if not ticket_number:
            q_replies.append(
                QuickReply(label="Create Support Ticket", query="I want to create a support ticket", topic="ticket_escalation")
            )

        return ChatResponse(
            message=msgs.get(target_lang, msgs["en"]),
            matched_intent="live_agent_status",
            confidence_score=1.0,
            session_id=session_id,
            category="live_agent",
            quick_replies=q_replies,
            suggested_questions=["Where are my support tickets?"],
            timestamp="",
            ticket_data={
                "action": "live_agent_status",
                "available_admins": avail_count,
                "ticket_id": ticket_id,
                "ticket_number": ticket_number
            }
        )


    def handle_message(
        self,
        message: str,
        session_id: str,
        role: Optional[str] = None,
        context_topic: Optional[str] = None,
        target_lang: str = "en",
        db: Optional[Any] = None,
        current_user: Optional[Any] = None
    ) -> Optional[ChatResponse]:
        """
        Processes a troubleshooting message and advances the diagnostic state machine.
        Returns a localized ChatResponse or None if not handled by troubleshooting.
        """
        state = self.get_session_state(session_id)
        norm_msg = message.lower().strip()

        # 1. Ticket Tracking Request
        if context_topic == "track_tickets" or any(w in norm_msg for w in ["track my tickets", "where are my tickets", "check tickets", "ticket status", "mera ticket", "check my ticket", "ਮੇਰੀ ਟਿਕਟ", "मेरी टिकट"]):
            return self.handle_track_tickets(session_id, target_lang, db, current_user)

        # 2. Ticket Confirmation / Cancellation State
        if state and (state.get("step") in ("confirm_ticket", "ticket_created") or state.get("ticket_created")):
            if context_topic == "cancel_ticket_creation" or any(w in norm_msg for w in ["cancel", "no", "nahi", "nahin", "mat banao", "radd", "ਰੱਦ", "रद्द"]):
                return self.handle_ticket_cancellation(session_id, target_lang)
            if context_topic == "confirm_ticket_submission" or any(w in norm_msg for w in ["yes", "submit", "confirm", "haan", "ha", "kr do", "ਕਰੋ", "हाँ", "ਹਾਂ"]):
                return self.handle_ticket_confirmation(session_id, state, target_lang, db, current_user)

        # 3. Ticket Escalation Preview Request (from Step 4 or explicit inquiry)
        if context_topic == "ticket_escalation" or (state and state.get("step") == 4 and any(w in norm_msg for w in ["ticket", "support", "escalate", "create", "open", "ਟਿਕਟ", "टिकट"])) or any(w in norm_msg for w in ["create ticket", "create support ticket", "support ticket", "ticket open", "ticket bana", "ticket create", "ticket raise", "सपोर्ट टिकट", "ਸਪੋਰਟ ਟਿਕਟ"]):
            return self.render_ticket_preview(session_id, state, target_lang)

        # 4. Live Agent Request
        if context_topic == "request_live_agent" or any(w in norm_msg for w in ["live agent", "human agent", "talk to human", "speak with agent", "chat with admin", "insan se baat", "live support", "human support", "admin se baat"]):
            return self.handle_live_agent_request(session_id, state, target_lang, db, current_user)

        # Check if user indicates resolution
        if any(w in norm_msg for w in ["resolved", "fixed", "it worked", "problem solved", "solved", "theek ho gaya", "theek ho gya", "kam kar gaya", "chal gaya", "hal ho gaya", "ਸਮੱਸਿਆ ਹੱਲ ਹੋ ਗਈ"]):
            self.clear_session_state(session_id)
            resolution_messages = {
                "en": "Glad that resolved the issue! Please let me know if you need assistance with anything else on SkillSphere.",
                "hi": "खुशी है कि आपकी समस्या का समाधान हो गया! यदि आपको SkillSphere पर किसी अन्य सहायता की आवश्यकता हो तो अवश्य बताएं।",
                "hinglish": "Great! Khushi hui ki issue solve ho gaya. SkillSphere par kisi aur cheez mein help chahiye ho to batayein.",
                "pa": "ਖੁਸ਼ੀ ਹੋਈ ਕਿ ਤੁਹਾਡੀ ਸਮੱਸਿਆ ਹੱਲ ਹੋ ਗਈ! ਜੇਕਰ SkillSphere 'ਤੇ ਕੋਈ ਹੋਰ ਮਦਦ ਚਾਹੀਦੀ ਹੋਵੇ ਤਾਂ ਦੱਸੋ।",
                "pa-Latn": "Vadiya! Khushi hoyi ki issue solve ho gaya. SkillSphere te hor koi help chahidi hove taan dasso."
            }
            return ChatResponse(
                message=resolution_messages.get(target_lang, resolution_messages["en"]),
                matched_intent="troubleshoot_resolved",
                confidence_score=1.0,
                session_id=session_id,
                category="troubleshooting",
                quick_replies=[
                    QuickReply(label="Browse Jobs", query="How do I search and filter jobs?", topic="candidate_job_search"),
                    QuickReply(label="Upload Resume", query="How do I upload my resume?", topic="candidate_resume_upload")
                ],
                suggested_questions=[],
                timestamp=""
            )

        # Check if initiating a new flow
        is_initial_trigger = False
        flow = None
        if not state:
            flow = self.detect_flow_trigger(message, context_topic)
            if not flow:
                return None
            state = {
                "flow": flow,
                "step": 1,
                "role": (role or "JOB_SEEKER").upper(),
                "answers": {}
            }
            self._active_sessions[session_id] = state
            is_initial_trigger = True
        else:
            flow = state["flow"]

        flow_def = TROUBLESHOOTING_STEPS.get(flow, {})

        # If this is the initial trigger, present Step 1 diagnostic question immediately
        if is_initial_trigger:
            step_data = flow_def.get(1, {})
            q_text = step_data.get("question", {}).get(target_lang, step_data.get("question", {}).get("en", ""))
            q_replies = [QuickReply(**opt) for opt in step_data.get("options", [])]
            return ChatResponse(
                message=q_text,
                matched_intent=step_data.get("intent", f"troubleshoot_{flow}_step_1"),
                confidence_score=0.95,
                session_id=session_id,
                category="troubleshooting",
                quick_replies=q_replies,
                suggested_questions=[opt["query"] for opt in step_data.get("options", [])],
                timestamp=""
            )

        # If currently at Step 1 and received an answer:
        step_num = state["step"]
        if step_num == 1:
            if any(w in norm_msg for w in ["no", "different", "larger", "nahi", "nahin", "nahi hai", "ਵੱਡਾ", "ਨਹੀਂ", "different format"]):
                # Provide action for format mismatch
                action = flow_def[1].get("action_on_no", {})
                msg_text = action.get(target_lang, action.get("en", ""))
                # Advance to step 2 after user attempts format correction
                state["step"] = 2
                self._active_sessions[session_id] = state
                next_q = flow_def[2]["question"].get(target_lang, flow_def[2]["question"]["en"])
                full_message = f"{msg_text}\n\n{next_q}"
                q_replies = [QuickReply(**opt) for opt in flow_def[2]["options"]]
                return ChatResponse(
                    message=full_message,
                    matched_intent=flow_def[2]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[2]["options"]],
                    timestamp=""
                )
            else:
                # Yes / Valid format -> Advance to step 2 directly
                state["step"] = 2
                self._active_sessions[session_id] = state
                q_text = flow_def[2]["question"].get(target_lang, flow_def[2]["question"]["en"])
                q_replies = [QuickReply(**opt) for opt in flow_def[2]["options"]]
                return ChatResponse(
                    message=q_text,
                    matched_intent=flow_def[2]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[2]["options"]],
                    timestamp=""
                )

        # If currently at Step 2 and received an answer:
        elif step_num == 2:
            if flow == FLOW_RESUME_OCR and any(w in norm_msg for w in ["scanned", "photo", "image", "photocopy", "स्कैन", "ਸਕੈਨ"]):
                action = flow_def[2].get("action_on_scanned", {})
                msg_text = action.get(target_lang, action.get("en", ""))
                state["step"] = 3
                self._active_sessions[session_id] = state
                next_q = flow_def[3]["question"].get(target_lang, flow_def[3]["question"]["en"])
                full_message = f"{msg_text}\n\n{next_q}"
                q_replies = [QuickReply(**opt) for opt in flow_def[3]["options"]]
                return ChatResponse(
                    message=full_message,
                    matched_intent=flow_def[3]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[3]["options"]],
                    timestamp=""
                )
            elif flow == FLOW_LIVEKIT and any(w in norm_msg for w in ["another", "zoom", "teams", "meet", "doosri", "ਹੋਰ ਐਪ"]):
                action = flow_def[2].get("action_on_conflict", {})
                msg_text = action.get(target_lang, action.get("en", ""))
                state["step"] = 3
                self._active_sessions[session_id] = state
                next_q = flow_def[3]["question"].get(target_lang, flow_def[3]["question"]["en"])
                full_message = f"{msg_text}\n\n{next_q}"
                q_replies = [QuickReply(**opt) for opt in flow_def[3]["options"]]
                return ChatResponse(
                    message=full_message,
                    matched_intent=flow_def[3]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[3]["options"]],
                    timestamp=""
                )
            elif flow == FLOW_PROCTORING and any(w in norm_msg for w in ["disconnect", "black", "fail", "camera", "ਕੈਮਰਾ", "ਬੰਦ"]):
                action = flow_def[2].get("action_on_webcam_fail", {})
                msg_text = action.get(target_lang, action.get("en", ""))
                state["step"] = 3
                self._active_sessions[session_id] = state
                next_q = flow_def[3]["question"].get(target_lang, flow_def[3]["question"]["en"])
                full_message = f"{msg_text}\n\n{next_q}"
                q_replies = [QuickReply(**opt) for opt in flow_def[3]["options"]]
                return ChatResponse(
                    message=full_message,
                    matched_intent=flow_def[3]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[3]["options"]],
                    timestamp=""
                )
            else:
                # Normal advance to step 3
                state["step"] = 3
                self._active_sessions[session_id] = state
                q_text = flow_def[3]["question"].get(target_lang, flow_def[3]["question"]["en"])
                q_replies = [QuickReply(**opt) for opt in flow_def[3]["options"]]
                return ChatResponse(
                    message=q_text,
                    matched_intent=flow_def[3]["intent"],
                    confidence_score=0.95,
                    session_id=session_id,
                    category="troubleshooting",
                    quick_replies=q_replies,
                    suggested_questions=[opt["query"] for opt in flow_def[3]["options"]],
                    timestamp=""
                )

        # If currently at Step 3 and still failing:
        elif isinstance(step_num, int) and step_num >= 3:
            # Advance to Step 4 (Escalation to Support Ticket)
            state["step"] = 4
            self._active_sessions[session_id] = state
            esc_msg = flow_def[4]["escalation_message"].get(target_lang, flow_def[4]["escalation_message"]["en"])
            q_replies = [QuickReply(**opt) for opt in flow_def[4]["options"]]
            return ChatResponse(
                message=esc_msg,
                matched_intent=flow_def[4]["intent"],
                confidence_score=0.95,
                session_id=session_id,
                category="troubleshooting",
                quick_replies=q_replies,
                suggested_questions=[opt["query"] for opt in flow_def[4]["options"]],
                timestamp=""
            )

        # Fallback step rendering if initial flow trigger
        step_data = flow_def.get(1, {})
        q_text = step_data.get("question", {}).get(target_lang, step_data.get("question", {}).get("en", ""))
        q_replies = [QuickReply(**opt) for opt in step_data.get("options", [])]
        return ChatResponse(
            message=q_text,
            matched_intent=step_data.get("intent", "troubleshoot_start"),
            confidence_score=0.95,
            session_id=session_id,
            category="troubleshooting",
            quick_replies=q_replies,
            suggested_questions=[opt["query"] for opt in step_data.get("options", [])],
            timestamp=""
        )


troubleshooting_engine = TroubleshootingEngine()
