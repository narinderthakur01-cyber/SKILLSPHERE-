import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Bot, AlertCircle, RefreshCw, X, Sparkles, CheckCircle2 } from 'lucide-react';
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
          // If session not found or expired, clear local storage
          sessionStorage.removeItem('skillsphere_chat_session_id');
          if (isMounted) setSessionId(null);
        }
      }

      // If no prior session, send initial welcome
      if (isMounted) {
        const defaultReplies = role === 'RECRUITER'
          ? [
              { label: 'Post a Job', query: 'How do I post a new job?', topic: 'recruiter_create_job' },
              { label: 'Kanban Pipeline', query: 'How does the Kanban pipeline work?', topic: 'recruiter_kanban_pipeline' },
              { label: 'Question Bank', query: 'How do I manage the Question Bank for tests?', topic: 'recruiter_question_bank' },
              { label: 'LiveKit Interview', query: 'How do I schedule a LiveKit video interview?', topic: 'recruiter_schedule_interview' }
            ]
          : [
              { label: 'Upload Resume', query: 'How do I upload my resume?', topic: 'candidate_resume_upload' },
              { label: 'Browse Jobs', query: 'How do I search and filter jobs?', topic: 'candidate_job_search' },
              { label: 'MCQ Assessment', query: 'What is the Round 1 MCQ assessment?', topic: 'candidate_mcq_assessment' },
              { label: 'Live Interview', query: 'How do I join a live video interview?', topic: 'candidate_live_interview' }
            ];

        setMessages([
          {
            id: 'welcome',
            sender: 'assistant',
            content: `Hello ${user?.name ? user.name.split(' ')[0] : 'there'}! I am your SkillSphere Assistant. How can I help you today? You can select any question below or type your own question.`,
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
  }, [sessionId, role]);

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

    // Reset messages to welcome
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
      className={`flex flex-col bg-ivory-warm/95 dark:bg-charcoal/95 backdrop-blur-md border border-oxblood/15 dark:border-white/10 shadow-xl overflow-hidden transition-all ${
        isFullPage
          ? 'w-full h-full rounded-2xl'
          : 'w-[92vw] sm:w-[420px] h-[560px] max-h-[82vh] rounded-2xl'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white/90 dark:bg-charcoal-light/90 border-b border-oxblood/10 dark:border-white/10 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-oxblood text-white flex items-center justify-center shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-semibold text-charcoal dark:text-ivory leading-tight flex items-center gap-1.5">
              SkillSphere Assistant
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="Online" />
            </h3>
            <p className="text-[10px] text-slate/70 dark:text-ivory/50 font-mono tracking-wide">
              Rule-Based • Zero External AI
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* Clear Chat Confirmation Trigger */}
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            title="Clear conversation"
            className="p-1.5 rounded-lg text-slate/70 dark:text-ivory/60 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          {/* Close Button (if floating modal) */}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Close Assistant"
              className="p-1.5 rounded-lg text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Clear Chat Confirmation Dialog */}
      {showClearConfirm && (
        <div className="bg-rose-50 dark:bg-rose-950/40 border-b border-rose-200 dark:border-rose-900/50 p-3 flex items-center justify-between gap-2 text-xs text-rose-900 dark:text-rose-200 shrink-0">
          <span>Clear conversation history?</span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleClearChat}
              className="px-2.5 py-1 rounded bg-rose-600 text-white font-medium hover:bg-rose-700 transition"
            >
              Yes, Clear
            </button>
            <button
              type="button"
              onClick={() => setShowClearConfirm(false)}
              className="px-2 py-1 rounded bg-black/5 dark:bg-white/10 hover:bg-black/10 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Message Feed Container */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2 select-text">
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}

        {/* Typing / Thinking Indicator */}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate/70 dark:text-ivory/50 py-2">
            <div className="w-6 h-6 rounded-full bg-oxblood/10 text-oxblood flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 animate-spin" />
            </div>
            <div className="flex items-center gap-1 px-3 py-2 rounded-2xl bg-white dark:bg-charcoal border border-oxblood/10 dark:border-white/10 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-oxblood/60 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-oxblood/60 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-oxblood/60 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        {/* Error Alert Banner */}
        {error && (
          <div className="p-3 my-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div className="flex-1">
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Quick Replies below latest message */}
        {!loading && quickReplies.length > 0 && (
          <div className="pt-2">
            <p className="text-[11px] font-medium text-slate/60 dark:text-ivory/50 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-oxblood/70" />
              Suggested Queries
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

      {/* Input Box & Action Bar */}
      <div className="p-3 bg-white/95 dark:bg-charcoal-light/95 border-t border-oxblood/10 dark:border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            disabled={loading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about SkillSphere..."
            maxLength={1000}
            className="flex-1 bg-ivory-warm/70 dark:bg-charcoal/70 border border-oxblood/15 dark:border-white/10 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 focus:outline-none focus:ring-2 focus:ring-oxblood/30 focus:border-oxblood transition-all disabled:opacity-50"
          />

          <button
            type="button"
            disabled={!input.trim() || loading}
            onClick={() => handleSend()}
            className="p-2.5 rounded-xl bg-oxblood text-white hover:bg-oxblood-dark active:scale-95 transition-all shadow-xs disabled:opacity-40 disabled:pointer-events-none shrink-0"
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-1 px-1 text-[10px] text-slate/50 dark:text-ivory/30">
          <span>Press Enter to send</span>
          <span>{input.length}/1000</span>
        </div>
      </div>
    </div>
  );
};
