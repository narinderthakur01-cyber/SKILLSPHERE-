import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, BookOpen, HelpCircle, CheckCircle2, Shield, Layers, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { chatAPI } from '../services/api';
import { ChatWindow } from '../components/chatbot/ChatWindow';

export const AssistantPage = () => {
  const { user, role } = useAuth();
  const [faqs, setFaqs] = useState([]);
  const [loadingFaqs, setLoadingFaqs] = useState(true);
  const [activeCategory, setActiveCategory] = useState('all');
  const [chatKey, setChatKey] = useState(1);

  // Load verified FAQs from the backend
  useEffect(() => {
    let isMounted = true;
    const fetchFaqs = async () => {
      try {
        setLoadingFaqs(true);
        const res = await chatAPI.getFAQs(role);
        if (isMounted) {
          setFaqs(res.data?.faqs || []);
        }
      } catch (err) {
        console.error('Failed to load FAQs:', err);
      } finally {
        if (isMounted) setLoadingFaqs(false);
      }
    };
    fetchFaqs();
    return () => {
      isMounted = false;
    };
  }, [role]);

  const filteredFaqs = faqs.filter((f) => {
    if (activeCategory === 'all') return true;
    return f.category === activeCategory;
  });

  const handleStartNewChat = () => {
    sessionStorage.removeItem('skillsphere_chat_session_id');
    setChatKey((prev) => prev + 1);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      {/* Editorial Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-oxblood/10 dark:border-white/10 pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-oxblood/10 dark:bg-white/10 text-oxblood dark:text-ivory text-xs font-mono mb-2">
            <Bot className="w-3.5 h-3.5 text-oxblood" />
            <span>Deterministic Support Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-charcoal dark:text-ivory">
            SkillSphere Assistant
          </h1>
          <p className="text-xs sm:text-sm text-slate/70 dark:text-ivory/60 mt-1 max-w-2xl">
            Get instant guidance on resume parsing & OCR intelligence, job discovery, Round 1 proctored assessments, candidate pipelines, and LiveKit meetings.
          </p>
        </div>

        <button
          type="button"
          onClick={handleStartNewChat}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-oxblood text-white text-xs sm:text-sm font-medium hover:bg-oxblood-dark active:scale-95 transition shadow-sm shrink-0"
        >
          <RefreshCw className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Main Grid: Chat on Left/Center, Verified FAQ Explorer on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Chat Interface Column */}
        <div className="lg:col-span-7 xl:col-span-8 h-[680px]">
          <ChatWindow key={chatKey} isFullPage={true} />
        </div>

        {/* Verified Knowledge Base Explorer Column */}
        <div className="lg:col-span-5 xl:col-span-4 flex flex-col gap-4">
          <div className="bg-white/90 dark:bg-charcoal/90 rounded-2xl border border-oxblood/15 dark:border-white/10 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-charcoal dark:text-ivory flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-oxblood" />
                Verified FAQ Knowledge Base
              </h2>
              <span className="text-[10px] font-mono text-slate/60 dark:text-ivory/50 bg-oxblood/5 dark:bg-white/5 px-2 py-0.5 rounded">
                {filteredFaqs.length} Entries
              </span>
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap gap-1.5 mb-3.5">
              {[
                { id: 'all', label: 'All Topics' },
                { id: 'candidate', label: 'Candidate' },
                { id: 'recruiter', label: 'Recruiter' },
                { id: 'general', label: 'General' },
              ].map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-2.5 py-1 text-xs rounded-lg transition font-medium ${
                    activeCategory === cat.id
                      ? 'bg-oxblood text-white shadow-2xs'
                      : 'bg-black/5 dark:bg-white/5 text-slate/70 dark:text-ivory/70 hover:bg-black/10'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* FAQ List */}
            <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
              {loadingFaqs ? (
                <div className="py-8 text-center text-xs text-slate/50 dark:text-ivory/40">
                  Loading verified topics...
                </div>
              ) : filteredFaqs.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate/50 dark:text-ivory/40">
                  No topics in this category for your role.
                </div>
              ) : (
                filteredFaqs.map((faq) => (
                  <details
                    key={faq.id}
                    className="group border border-oxblood/10 dark:border-white/10 rounded-xl bg-ivory-warm/40 dark:bg-charcoal-light/40 overflow-hidden text-xs transition-all open:bg-white dark:open:bg-charcoal open:shadow-xs"
                  >
                    <summary className="cursor-pointer font-medium p-3 text-charcoal dark:text-ivory hover:text-oxblood dark:hover:text-ivory flex items-center justify-between list-none">
                      <span className="pr-2">{faq.title}</span>
                      <span className="text-oxblood/60 dark:text-ivory/40 group-open:rotate-180 transition-transform">
                        ▾
                      </span>
                    </summary>
                    <div className="px-3 pb-3 text-slate/80 dark:text-ivory/80 leading-relaxed border-t border-oxblood/5 dark:border-white/5 pt-2">
                      <p>{faq.response}</p>
                      {faq.sample_questions && faq.sample_questions.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-black/5 dark:border-white/5">
                          <span className="text-[10px] uppercase font-mono text-slate/50 dark:text-ivory/40 block mb-1">
                            Sample Queries:
                          </span>
                          <ul className="list-disc list-inside space-y-0.5 text-[11px] text-slate/70 dark:text-ivory/60">
                            {faq.sample_questions.slice(0, 3).map((sq, i) => (
                              <li key={i}>{sq}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </details>
                ))
              )}
            </div>
          </div>

          {/* Privacy & Rule-Based Trust Notice */}
          <div className="p-3.5 rounded-2xl bg-oxblood/5 dark:bg-white/5 border border-oxblood/10 dark:border-white/10 text-xs text-slate/70 dark:text-ivory/60 flex items-start gap-2.5">
            <Shield className="w-4 h-4 text-oxblood shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-charcoal dark:text-ivory block mb-0.5">
                Privacy & Data Security
              </span>
              SkillSphere Assistant operates strictly on verified system rules and local knowledge bases. It never submits your questions to public LLMs or external artificial intelligence APIs.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
