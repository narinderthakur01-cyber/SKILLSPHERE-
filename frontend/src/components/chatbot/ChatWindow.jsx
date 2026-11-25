import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Bot, AlertCircle, RefreshCw, X, Sparkles, CheckCircle2, Maximize2, Minimize2, Languages } from 'lucide-react';
import { chatAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { ChatMessage } from './ChatMessage';
import { QuickReplies } from './QuickReplies';

export const ChatWindow = ({
  onClose,
  isFullPage = false,
  initialTopic = null,
  externalSessionId = null
}) => {
  const { user, role } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(() => {
    return externalSessionId || sessionStorage.getItem('skillsphere_chat_session_id') || null;
  });
  const [currentTopic, setCurrentTopic] = useState(initialTopic);
  const [quickReplies, setQuickReplies] = useState([]);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom on message list updates
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load existing history or initialize welcome message
  useEffect(() => {
    let isMounted = true;

    const initChat = async () => {
      if (sessionId) {
        try {
          setLoading(true);
          const res = await chatAPI.getHistory(sessionId);
          if (isMounted && res.data?.messages?.length > 0) {
            setMessages(res.data.messages);
            if (res.data.last_topic) {
              setCurrentTopic(res.data.last_topic);
            }
            setLoading(false);
            return;
          }
        } catch {
          sessionStorage.removeItem('skillsphere_chat_session_id');
          if (isMounted) setSessionId(null);
        }
      }

      if (isMounted) {
        const defaultReplies = role === 'RECRUITER'
          ? [
              { label: 'Post a Job', query: 'How do I post a new job?', topic: 'recruiter_create_job' },
              { label: 'Kanban Pipeline', query: 'How does the Kanban pipeline work?', topic: 'recruiter_kanban_pipeline' },
              { label: 'Question Bank', query: 'How do I manage the Question Bank for tests?', topic: 'recruiter_question_bank' },
              { label: 'LiveKit Interview', query: 'How do I schedule a LiveKit video interview?', topic: 'recruiter_schedule_interview' },
              { label: 'Track My Tickets', query: 'Where are my support tickets?', topic: 'track_tickets' }
            ]
          : [
              { label: 'Upload Resume', query: 'How do I upload my resume?', topic: 'candidate_resume_upload' },
              { label: 'Browse Jobs', query: 'How do I search and filter jobs?', topic: 'candidate_job_search' },
              { label: 'MCQ Assessment', query: 'What is the Round 1 MCQ assessment?', topic: 'candidate_mcq_assessment' },
              { label: 'Live Interview', query: 'How do I join a live video interview?', topic: 'candidate_live_interview' },
              { label: 'Track My Tickets', query: 'Where are my support tickets?', topic: 'track_tickets' }
            ];

        setMessages([
          {
            id: 'welcome',
            sender: 'assistant',
            content: `Hello ${user?.name ? user.name.split(' ')[0] : 'there'}! I am your SkillSphere Multilingual Assistant. I can help you with resumes, jobs, assessments, interviews, and support tickets in English, Hindi, Hinglish, and Punjabi.`,
            intent: 'general_greeting',
            created_at: new Date().toISOString()
          }
        ]);
        setQuickReplies(defaultReplies);
        setLoading(false);
      }
    };

    initChat();

    return () => {
      isMounted = false;
    };
  }, [sessionId, role, user]);

  const handleSend = async (messageText = input, topicHint = null) => {
    const textToSend = messageText.trim();
    if (!textToSend || loading) return;

    setError(null);
    setInput('');

    // Add user message to UI state immediately
    const userMsg = {
      id: `temp-${Date.now()}`,
      sender: 'user',
      content: textToSend,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const activeTopic = topicHint || currentTopic;
      const res = await chatAPI.sendMessage(textToSend, sessionId, activeTopic);
      const data = res.data;

      // Update session ID if newly assigned
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        sessionStorage.setItem('skillsphere_chat_session_id', data.session_id);
      }

      // Update active topic if recognized
      if (data.matched_intent && data.matched_intent !== 'fallback') {
        setCurrentTopic(data.matched_intent);
      }

      // Add assistant response
      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        content: data.message,
        intent: data.matched_intent,
        confidence: data.confidence_score,
        ticket_data: data.ticket_data || null,
        created_at: data.timestamp || new Date().toISOString()
      };
      setMessages((prev) => [...prev, botMsg]);

      // Update quick replies from assistant response
      if (data.quick_replies && data.quick_replies.length > 0) {
        setQuickReplies(data.quick_replies);
      }
    } catch (err) {
      console.error('Chat error:', err);
      const errDetail = err.response?.data?.detail || 'Unable to connect to SkillSphere Assistant. Please check your connection and try again.';
      setError(errDetail);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = async () => {
    if (sessionId) {
      try {
        await chatAPI.deleteHistory(sessionId);
      } catch (e) {
        console.warn('Failed to delete history on server:', e);
      }
    }
    sessionStorage.removeItem('skillsphere_chat_session_id');
    setSessionId(null);
    setCurrentTopic(null);
    setShowClearConfirm(false);

    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'assistant',
        content: 'Conversation cleared. How else can I assist you with SkillSphere?',
        intent: 'general_greeting',
        created_at: new Date().toISOString()
      }
    ]);
  };

  return (
    <div
      className={`flex flex-col bg-[#FDFBF9] dark:bg-[#181619] border border-slate-200/80 dark:border-white/10 shadow-2xl overflow-hidden transition-all duration-300 ${
        isFullPage
          ? 'w-full h-full rounded-3xl'
          : isExpanded
          ? 'w-[96vw] sm:w-[620px] md:w-[680px] h-[720px] max-h-[90vh] rounded-3xl'
          : 'w-[94vw] sm:w-[460px] md:w-[490px] h-[620px] max-h-[85vh] rounded-3xl'
      }`}
    >
      {/* Header with Liquid Metal & Thermal Accent */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-white/95 dark:bg-[#201E22]/95 border-b border-slate-200/70 dark:border-white/10 shrink-0 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-oxblood to-oxblood-600 text-white flex items-center justify-center shadow-md liquid-metal-pill">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-display font-bold text-charcoal dark:text-ivory leading-tight">
                SkillSphere Assistant
              </h3>
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-mono font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>ONLINE</span>
              </span>
            </div>
            <p className="text-[10px] text-slate-500 dark:text-rose font-mono flex items-center gap-1.5 mt-0.5">
              <Languages className="w-3 h-3 text-oxblood" />
              <span>EN • HI • Hinglish • PA</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* Expand / Minimize Window (Non-full-page only) */}
          {!isFullPage && (
            <button
              type="button"
              onClick={() => setIsExpanded((prev) => !prev)}
              title={isExpanded ? "Collapse to standard size" : "Expand conversation area"}
              className="p-2 rounded-xl text-slate-500 dark:text-ivory/70 hover:text-charcoal dark:hover:text-ivory hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          )}

          {/* Clear Chat Confirmation Trigger */}
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            title="Clear conversation"
            className="p-2 rounded-xl text-slate-500 dark:text-ivory/70 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          {/* Close Button (if floating modal) */}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Close Assistant"
              className="p-2 rounded-xl text-slate-500 dark:text-ivory/70 hover:text-charcoal dark:hover:text-ivory hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Clear Chat Confirmation Dialog */}
      {showClearConfirm && (
        <div className="bg-rose-50 dark:bg-rose-950/50 border-b border-rose-200 dark:border-rose-900/60 p-3.5 flex items-center justify-between gap-3 text-xs text-rose-900 dark:text-rose-200 shrink-0">
          <span className="font-medium">Clear conversation history and reset session?</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleClearChat}
              className="px-3 py-1.5 rounded-xl bg-rose-600 text-white font-bold hover:bg-rose-700 transition shadow-xs text-xs"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={() => setShowClearConfirm(false)}
              className="px-2.5 py-1.5 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-black/10 text-xs font-medium transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Message Feed Container */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-5 py-4 space-y-3 select-text scrollbar-thin">
        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            message={m}
            onAction={(query, topic) => handleSend(query, topic)}
          />
        ))}

        {/* Natural Typing & Thinking Indicator */}
        {loading && (
          <div className="flex items-center gap-2.5 text-xs text-slate-500 dark:text-rose py-2">
            <div className="w-7 h-7 rounded-full bg-oxblood/15 text-oxblood dark:text-rose flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="flex items-center gap-1.5 px-4 py-2.5 rounded-2xl bg-white dark:bg-[#252327] border border-slate-200/80 dark:border-white/10 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-oxblood dark:bg-rose animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-oxblood dark:bg-rose animate-bounce" style={{ animationDelay: '160ms' }} />
              <span className="w-2 h-2 rounded-full bg-oxblood dark:bg-rose animate-bounce" style={{ animationDelay: '320ms' }} />
            </div>
          </div>
        )}

        {/* Error Alert Banner */}
        {error && (
          <div className="p-3.5 my-2 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* Quick Replies below latest message */}
        {!loading && quickReplies.length > 0 && (
          <div className="pt-2">
            <p className="text-[11px] font-mono font-bold text-slate-500 dark:text-rose uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-oxblood" />
              <span>Suggested Queries</span>
            </p>
            <QuickReplies
              quickReplies={quickReplies}
              onSelect={(query, topic) => handleSend(query, topic)}
              disabled={loading}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box & Action Bar with Fixed Contrast & Typing Bugs */}
      <div className="p-3.5 bg-white/95 dark:bg-[#201E22]/95 border-t border-slate-200/70 dark:border-white/10 shrink-0">
        <div className="flex items-center gap-2 relative">
          <input
            ref={inputRef}
            type="text"
            value={input}
            disabled={loading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything in English, Hindi, Hinglish, Punjabi..."
            maxLength={1000}
            className="flex-1 bg-[#F5F2EE] dark:bg-[#2A282D] border border-slate-300/80 dark:border-white/15 rounded-2xl px-4 py-3 text-sm text-[#1B1A1B] dark:text-[#EFE9E3] placeholder:text-slate-400 dark:placeholder:text-[#C5A49B]/60 focus:outline-none focus:ring-2 focus:ring-oxblood/40 focus:border-oxblood dark:focus:ring-rose/40 dark:focus:border-rose transition-all disabled:opacity-50 caret-oxblood dark:caret-rose shadow-inner"
          />

          <button
            type="button"
            disabled={!input.trim() || loading}
            onClick={() => handleSend()}
            className="p-3 rounded-2xl bg-oxblood text-white hover:bg-oxblood-600 active:scale-95 transition-all shadow-md disabled:opacity-40 disabled:pointer-events-none shrink-0 liquid-metal-shimmer"
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-1.5 px-2 text-[10px] font-mono text-slate-400 dark:text-rose/70">
          <span>Enter ↵ to send • Shift+Enter for new line</span>
          <span>{input.length}/1000</span>
        </div>
      </div>
    </div>
  );
};
