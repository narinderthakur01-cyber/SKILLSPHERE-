import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar, Video, Sparkles, User, Users, Brain, Shield,
  Clock, CheckCircle2, AlertCircle, Plus, RefreshCw,
  ChevronRight, Award, Edit3, Trash2, ArrowUpRight, Play,
  Sliders, Star, Check, X, FileText, Bot, Mic, Eye, XCircle
} from 'lucide-react';
import { interviewsAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const RecruiterInterviewHubTab = ({
  interviews = [],
  loading = false,
  onRefresh,
  onOpenDossier,
  jobs = [],
  applicants = [],
  onScheduleNewInterview
}) => {
  const { addToast } = useToast();

  // Status Section Filter State: UPCOMING, ONGOING, COMPLETED, CANCELLED, ALL
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Mode Selection State: ALL, HUMAN, AI_LIVE, HYBRID, CONFIGURED
  const [filterMode, setFilterMode] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // AI Configuration & Question Studio Modal
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configInterview, setConfigInterview] = useState(null);
  const [selectedMode, setSelectedMode] = useState('AI_LIVE');
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [difficulty, setDifficulty] = useState('INTERMEDIATE');
  const [questionCount, setQuestionCount] = useState(4);
  const [voice, setVoice] = useState('alloy');
  const [allowTakeover, setAllowTakeover] = useState(true);
  const [selectedCategories, setSelectedCategories] = useState([
    'TECHNICAL', 'PROBLEM_SOLVING', 'BEHAVIORAL'
  ]);
  const [questions, setQuestions] = useState([]);
  const [generatingQuestions, setGeneratingQuestions] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);

  // New Custom Question Input
  const [newQuestionText, setNewQuestionText] = useState('');
  const [newQuestionType, setNewQuestionType] = useState('TECHNICAL');
  const [newQuestionDuration, setNewQuestionDuration] = useState(180);

  // Evaluation & Scorecard Modal
  const [showEvalModal, setShowEvalModal] = useState(false);
  const [selectedEvalInterview, setSelectedEvalInterview] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [recruiterOverrideScore, setRecruiterOverrideScore] = useState(4.0);
  const [recruiterNotes, setRecruiterNotes] = useState('');
  const [savingOverride, setSavingOverride] = useState(false);

  // Details Modal State
  const [selectedDetailInterview, setSelectedDetailInterview] = useState(null);

  // Edit Schedule Modal State
  const [selectedEditInterview, setSelectedEditInterview] = useState(null);
  const [editDate, setEditDate] = useState('');
  const [editTime, setEditTime] = useState('14:00');
  const [editDuration, setEditDuration] = useState(45);
  const [editInstructions, setEditInstructions] = useState('');
  const [editLink, setEditLink] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Video Recording Playback Modal State
  const [selectedRecordingInterview, setSelectedRecordingInterview] = useState(null);

  // Candidate Selection Modal (when scheduling from Hub)
  const [showCandidatePickerModal, setShowCandidatePickerModal] = useState(false);

  // Open Details Modal
  const handleOpenDetails = (interview) => {
    setSelectedDetailInterview(interview);
  };

  // Open Edit Modal
  const handleOpenEdit = (interview) => {
    setSelectedEditInterview(interview);
    const dateObj = new Date(interview.scheduled_time || interview.scheduled_at);
    if (!isNaN(dateObj.getTime())) {
      setEditDate(dateObj.toISOString().slice(0, 10));
      const hours = dateObj.getHours().toString().padStart(2, '0');
      const mins = dateObj.getMinutes().toString().padStart(2, '0');
      setEditTime(`${hours}:${mins}`);
    } else {
      setEditDate('');
      setEditTime('14:00');
    }
    setEditDuration(interview.duration_minutes || 45);
    setEditInstructions(interview.instructions || '');
    setEditLink(interview.meeting_link || '');
  };

  // Save Edit Schedule
  const handleSaveEdit = async () => {
    if (!selectedEditInterview || !editDate) {
      addToast("Please provide date and time", "warning");
      return;
    }
    setSavingEdit(true);
    try {
      const scheduledIso = new Date(`${editDate}T${editTime || '14:00'}:00`).toISOString();
      await interviewsAPI.update(selectedEditInterview.id, {
        scheduled_time: scheduledIso,
        duration_minutes: Number(editDuration),
        meeting_link: editLink,
        instructions: editInstructions
      });
      addToast("Interview updated successfully!", "success");
      setSelectedEditInterview(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to update interview:", err);
      addToast(err.response?.data?.detail || "Failed to update interview", "error");
    } finally {
      setSavingEdit(false);
    }
  };

  // Cancel Interview
  const handleCancelInterview = async (interviewId) => {
    if (!window.confirm("Are you sure you want to cancel this scheduled interview? Candidate will receive an update notification.")) {
      return;
    }
    try {
      await interviewsAPI.cancel(interviewId);
      addToast("Interview marked as CANCELLED", "success");
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to cancel interview:", err);
      addToast(err.response?.data?.detail || "Failed to cancel interview", "error");
    }
  };

  // Open AI Config Studio for an interview
  const handleOpenConfigStudio = async (interview) => {
    setConfigInterview(interview);
    setSelectedMode(interview.interview_mode || 'AI_LIVE');
    setDurationMinutes(interview.duration_minutes || 30);
    const cfg = interview.ai_config_json || {};
    setDifficulty(cfg.difficulty || 'INTERMEDIATE');
    setQuestionCount(cfg.question_count || 4);
    setVoice(cfg.voice || 'alloy');
    setAllowTakeover(cfg.allow_recruiter_takeover !== false);
    if (cfg.categories && cfg.categories.length > 0) {
      setSelectedCategories(cfg.categories);
    }

    try {
      const qRes = await interviewsAPI.getQuestions(interview.id);
      setQuestions(qRes.data || []);
    } catch (err) {
      setQuestions([]);
    }
    setShowConfigModal(true);
  };

  // Generate Questions via AI
  const handleGenerateQuestions = async () => {
    if (!configInterview) return;
    setGeneratingQuestions(true);
    try {
      const res = await interviewsAPI.generateAIQuestions({
        interview_id: configInterview.id,
        difficulty: difficulty,
        question_count: questionCount,
        categories: selectedCategories
      });
      setQuestions(res.data || []);
      addToast(`Generated ${res.data?.length || 0} tailored interview questions!`, "success");
    } catch (err) {
      console.error("Failed to generate AI questions:", err);
      addToast("Failed to generate questions. Please try again.", "error");
    } finally {
      setGeneratingQuestions(false);
    }
  };

  // Add Custom Question
  const handleAddCustomQuestion = () => {
    if (!newQuestionText.trim()) return;
    const newQ = {
      sequence_number: questions.length + 1,
      question_text: newQuestionText.trim(),
      question_type: newQuestionType,
      source: 'CUSTOM',
      expected_concepts: [],
      max_duration_seconds: Number(newQuestionDuration) || 180
    };
    setQuestions([...questions, newQ]);
    setNewQuestionText('');
  };

  // Remove Question
  const handleRemoveQuestion = (idx) => {
    const updated = questions.filter((_, i) => i !== idx).map((q, i) => ({
      ...q,
      sequence_number: i + 1
    }));
    setQuestions(updated);
  };

  // Save Interview AI Configuration
  const handleSaveConfig = async () => {
    if (!configInterview) return;
    setSavingConfig(true);
    try {
      await interviewsAPI.configureAI(configInterview.id, {
        interview_mode: selectedMode,
        duration_minutes: Number(durationMinutes),
        difficulty,
        question_count: questions.length,
        categories: selectedCategories,
        voice,
        allow_recruiter_takeover: allowTakeover,
        questions: questions
      });
      addToast("Interview AI configuration & questions saved!", "success");
      setShowConfigModal(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to save AI configuration:", err);
      addToast(err.response?.data?.detail || "Failed to save configuration.", "error");
    } finally {
      setSavingConfig(false);
    }
  };

  // Open Evaluation Report Modal
  const handleViewEvaluation = async (interview) => {
    setSelectedEvalInterview(interview);
    setShowEvalModal(true);
    setEvalLoading(true);
    setEvaluationData(null);
    try {
      const res = await interviewsAPI.getAIEvaluation(interview.id);
      setEvaluationData(res.data);
      setRecruiterOverrideScore(res.data.overall_score || 4.0);
      setRecruiterNotes(res.data.recruiter_notes || '');
    } catch (err) {
      console.warn("AI Evaluation not yet generated, creating on-demand...");
      try {
        const genRes = await interviewsAPI.generateAIEvaluation(interview.id);
        setEvaluationData(genRes.data);
        setRecruiterOverrideScore(genRes.data.overall_score || 4.0);
        setRecruiterNotes(genRes.data.recruiter_notes || '');
      } catch (genErr) {
        console.error("Could not load evaluation:", genErr);
        addToast("Evaluation report is not yet available for this interview.", "info");
      }
    } finally {
      setEvalLoading(false);
    }
  };

  // Save Recruiter Evaluation Override
  const handleSaveEvaluationOverride = async () => {
    if (!selectedEvalInterview) return;
    setSavingOverride(true);
    try {
      const res = await interviewsAPI.updateAIEvaluation(selectedEvalInterview.id, {
        overall_score: Number(recruiterOverrideScore),
        review_status: 'ACCEPTED',
        recruiter_notes: recruiterNotes
      });
      setEvaluationData(res.data);
      addToast("Recruiter evaluation override and notes saved!", "success");
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to update evaluation:", err);
      addToast("Failed to update evaluation.", "error");
    } finally {
      setSavingOverride(false);
    }
  };

  // Category toggle helper
  const toggleCategory = (cat) => {
    if (selectedCategories.includes(cat)) {
      if (selectedCategories.length > 1) {
        setSelectedCategories(selectedCategories.filter(c => c !== cat));
      }
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  // Calculated Status Section Counts
  const now = new Date();
  const counts = {
    all: interviews.length,
    upcoming: interviews.filter(i => (i.status === 'SCHEDULED' || i.status === 'WAITING' || i.status === 'RESCHEDULED') && new Date(i.scheduled_time || i.scheduled_at) >= now).length,
    ongoing: interviews.filter(i => i.status === 'IN_PROGRESS' || i.room_status === 'IN_PROGRESS').length,
    completed: interviews.filter(i => i.status === 'COMPLETED').length,
    cancelled: interviews.filter(i => i.status === 'CANCELLED').length
  };

  // Filtered Interviews List
  const filteredInterviews = interviews.filter(inv => {
    const mode = inv.interview_mode || 'HUMAN';
    if (filterMode !== 'ALL' && mode !== filterMode) return false;

    const schedDate = new Date(inv.scheduled_time || inv.scheduled_at);
    if (statusFilter === 'UPCOMING') {
      if (inv.status !== 'SCHEDULED' && inv.status !== 'WAITING' && inv.status !== 'RESCHEDULED') return false;
      if (schedDate < now) return false;
    } else if (statusFilter === 'ONGOING') {
      if (inv.status !== 'IN_PROGRESS' && inv.room_status !== 'IN_PROGRESS') return false;
    } else if (statusFilter === 'COMPLETED') {
      if (inv.status !== 'COMPLETED') return false;
    } else if (statusFilter === 'CANCELLED') {
      if (inv.status !== 'CANCELLED') return false;
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const cand = (inv.candidate_name || inv.application?.candidate?.name || '').toLowerCase();
      const job = (inv.job_title || inv.application?.job?.title || '').toLowerCase();
      return cand.includes(q) || job.includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Overview */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose border border-oxblood/20">
                Unified Interview Hub
              </span>
              <span className="text-xs text-slate/60 dark:text-ivory/60 font-mono">
                LiveKit WebRTC + AI Conversation Engine
              </span>
            </div>
            <h2 className="font-display text-2xl font-black text-charcoal dark:text-ivory">
              Interview Architecture & Intelligence
            </h2>
            <p className="text-sm text-slate/70 dark:text-ivory/70 mt-1 max-w-2xl">
              Conduct high-fidelity LiveKit technical interviews across Human, Autonomous AI, and Hybrid Recruiter-Takeover modes. All sessions are archived to Cloudinary with structured competency scorecards.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <button
              onClick={() => {
                if (onScheduleNewInterview && applicants.length > 0) {
                  setShowCandidatePickerModal(true);
                } else if (onScheduleNewInterview) {
                  onScheduleNewInterview(null);
                } else {
                  addToast("Please select a candidate from the Pipeline tab to schedule.", "info");
                }
              }}
              className="btn-oxblood px-4 py-2.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-2 min-h-[44px] shadow"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Schedule Interview</span>
            </button>

            <button
              onClick={onRefresh}
              className="px-4 py-2.5 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood dark:hover:border-rose transition flex items-center gap-2 min-h-[44px]"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Schedule</span>
            </button>
          </div>
        </div>

        {/* 4 Mode Architectural Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <div
            onClick={() => setFilterMode('HUMAN')}
            className={`p-4 rounded-2xl cursor-pointer transition border ${
              filterMode === 'HUMAN'
                ? 'bg-oxblood/10 border-oxblood dark:border-rose'
                : 'bg-white/40 dark:bg-white/5 border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                <Users className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-mono font-bold text-slate/50">Option A</span>
            </div>
            <h4 className="font-bold text-sm text-charcoal dark:text-ivory">Human Live Interview</h4>
            <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">
              Direct recruiter-to-candidate LiveKit WebRTC call with collaborative tools.
            </p>
          </div>

          <div
            onClick={() => setFilterMode('AI_LIVE')}
            className={`p-4 rounded-2xl cursor-pointer transition border ${
              filterMode === 'AI_LIVE'
                ? 'bg-oxblood/10 border-oxblood dark:border-rose'
                : 'bg-white/40 dark:bg-white/5 border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
                <Bot className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-mono font-bold text-slate/50">Option B</span>
            </div>
            <h4 className="font-bold text-sm text-charcoal dark:text-ivory">AI Live Interview</h4>
            <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">
              Autonomous AI agent conducts voice interview with adaptive follow-ups.
            </p>
          </div>

          <div
            onClick={() => setFilterMode('HYBRID')}
            className={`p-4 rounded-2xl cursor-pointer transition border ${
              filterMode === 'HYBRID'
                ? 'bg-oxblood/10 border-oxblood dark:border-rose'
                : 'bg-white/40 dark:bg-white/5 border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-mono font-bold text-slate/50">Option C</span>
            </div>
            <h4 className="font-bold text-sm text-charcoal dark:text-ivory">Hybrid AI + Human</h4>
            <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">
              AI interviews candidate; recruiter observes and can take over seamlessly.
            </p>
          </div>

          <div
            onClick={() => setFilterMode('CONFIGURED')}
            className={`p-4 rounded-2xl cursor-pointer transition border ${
              filterMode === 'CONFIGURED'
                ? 'bg-oxblood/10 border-oxblood dark:border-rose'
                : 'bg-white/40 dark:bg-white/5 border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold">
                <Sliders className="w-4 h-4" />
              </div>
              <span className="text-[10px] font-mono font-bold text-slate/50">Option D</span>
            </div>
            <h4 className="font-bold text-sm text-charcoal dark:text-ivory">Configured Studio</h4>
            <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">
              Recruiter-curated custom questions with timed segments & rubric scoring.
            </p>
          </div>
        </div>
      </div>

      {/* DEDICATED STATUS SECTION NAVIGATION */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-2 border-b border-slate/15 dark:border-rose/15">
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {[
            { key: 'ALL', label: 'All Interviews', count: counts.all },
            { key: 'UPCOMING', label: 'Upcoming', count: counts.upcoming },
            { key: 'ONGOING', label: 'Ongoing', count: counts.ongoing },
            { key: 'COMPLETED', label: 'Completed', count: counts.completed },
            { key: 'CANCELLED', label: 'Cancelled', count: counts.cancelled },
          ].map((sec) => (
            <button
              key={sec.key}
              onClick={() => setStatusFilter(sec.key)}
              className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition flex items-center gap-2 ${
                statusFilter === sec.key
                  ? 'bg-oxblood text-white shadow'
                  : 'bg-white/40 dark:bg-white/5 text-slate/70 dark:text-ivory/70 hover:text-charcoal dark:hover:text-ivory border border-slate/15'
              }`}
            >
              <span>{sec.label}</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                statusFilter === sec.key ? 'bg-white/20 text-white' : 'bg-slate/10 text-slate/60 dark:text-ivory/60'
              }`}>
                {sec.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="w-full md:w-72">
          <input
            type="text"
            placeholder="Search candidate or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 text-xs rounded-xl border border-slate/20 dark:border-rose/20 bg-white/60 dark:bg-black/20 text-charcoal dark:text-ivory placeholder-slate/40 focus:outline-none focus:border-oxblood"
          />
        </div>
      </div>

      {/* Mode Sub-Filter Pill Row */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-[11px] font-mono text-slate/50 uppercase tracking-wider mr-1">
          Mode Filter:
        </span>
        {['ALL', 'HUMAN', 'AI_LIVE', 'HYBRID', 'CONFIGURED'].map((mode) => (
          <button
            key={mode}
            onClick={() => setFilterMode(mode)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition ${
              filterMode === mode
                ? 'bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal font-bold'
                : 'text-slate/60 hover:text-charcoal dark:text-ivory/60 hover:bg-slate/10'
            }`}
          >
            {mode === 'ALL' ? 'All Modes' : mode.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Interviews List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(n => <div key={n} className="h-32 glass-card rounded-2xl animate-pulse"></div>)}
        </div>
      ) : filteredInterviews.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-3xl border border-slate/15 dark:border-rose/15">
          <Calendar className="w-12 h-12 text-slate/30 dark:text-ivory/30 mx-auto mb-3" />
          <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">
            No interviews found in this section
          </h4>
          <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1 max-w-md mx-auto">
            Try adjusting your status filter ({statusFilter}) or mode filter ({filterMode}), or schedule a new interview.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredInterviews.map((inv) => {
            const mode = inv.interview_mode || 'HUMAN';
            const scheduledDate = new Date(inv.scheduled_time || inv.scheduled_at);
            const candName = inv.candidate_name || inv.application?.candidate?.name || 'Candidate';
            const jobTitle = inv.job_title || inv.application?.job?.title || 'Engineering Role';
            const isCompleted = inv.status === 'COMPLETED';
            const isOngoing = inv.status === 'IN_PROGRESS' || inv.room_status === 'IN_PROGRESS';
            const isCancelled = inv.status === 'CANCELLED';

            return (
              <div
                key={inv.id}
                className="glass-card p-5 sm:p-6 rounded-2xl border border-slate/15 dark:border-rose/15 hover:border-oxblood/30 transition flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    {/* Mode Tag */}
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full uppercase flex items-center gap-1 ${
                      mode === 'AI_LIVE' ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30' :
                      mode === 'HYBRID' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' :
                      mode === 'CONFIGURED' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30' :
                      'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                    }`}>
                      {mode === 'AI_LIVE' && <Bot className="w-3 h-3" />}
                      {mode === 'HYBRID' && <Sparkles className="w-3 h-3" />}
                      {mode === 'CONFIGURED' && <Sliders className="w-3 h-3" />}
                      {mode === 'HUMAN' && <User className="w-3 h-3" />}
                      <span>{mode.replace('_', ' ')}</span>
                    </span>

                    {/* Status Badge */}
                    <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full uppercase ${
                      isOngoing ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 animate-pulse' :
                      isCompleted ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' :
                      isCancelled ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30' :
                      'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                    }`}>
                      {inv.status}
                    </span>

                    <span className="text-xs text-slate/50 font-mono">
                      {inv.duration_minutes || 30} mins
                    </span>
                  </div>

                  <h3 className="font-display font-bold text-lg text-charcoal dark:text-ivory">
                    {candName} <span className="font-normal text-slate/60 text-sm">— {jobTitle}</span>
                  </h3>

                  <div className="flex items-center gap-3 text-xs text-slate/60 dark:text-ivory/60 mt-1 flex-wrap">
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                      {scheduledDate.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                    {inv.round_title && (
                      <span className="font-mono text-slate/50">| {inv.round_title}</span>
                    )}
                    {inv.room_id && (
                      <span className="font-mono text-slate/40 text-[11px]">Room: {inv.room_id}</span>
                    )}
                  </div>
                </div>

                {/* Complete Action Set (Phase 2 Requirement) */}
                <div className="flex items-center gap-2 flex-wrap shrink-0">
                  {/* View Details */}
                  <button
                    type="button"
                    onClick={() => handleOpenDetails(inv)}
                    className="px-3 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood transition flex items-center gap-1.5"
                    title="View Full Interview Details"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Details</span>
                  </button>

                  {/* Edit Schedule (Permitted if Scheduled) */}
                  {!isCompleted && !isCancelled && (
                    <button
                      type="button"
                      onClick={() => handleOpenEdit(inv)}
                      className="px-3 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood transition flex items-center gap-1.5"
                      title="Edit Schedule, Duration & Instructions"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </button>
                  )}

                  {/* Configure AI / Questions Studio */}
                  {(mode === 'AI_LIVE' || mode === 'HYBRID' || mode === 'CONFIGURED') && !isCompleted && !isCancelled && (
                    <button
                      type="button"
                      onClick={() => handleOpenConfigStudio(inv)}
                      className="px-3.5 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood transition flex items-center gap-1.5"
                      title="Configure AI & Question Studio"
                    >
                      <Sliders className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                      <span>Configure AI</span>
                    </button>
                  )}

                  {/* Evaluation Report Button */}
                  <button
                    type="button"
                    onClick={() => handleViewEvaluation(inv)}
                    className="px-3.5 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood transition flex items-center gap-1.5"
                  >
                    <Award className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                    <span>Evaluation</span>
                  </button>

                  {/* Candidate Dossier */}
                  {inv.candidate_id && onOpenDossier && (
                    <button
                      type="button"
                      onClick={() => onOpenDossier(inv.candidate_id)}
                      className="px-3 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono font-bold hover:border-oxblood transition flex items-center gap-1"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Dossier</span>
                    </button>
                  )}

                  {/* Cancel Interview (Permitted if Scheduled) */}
                  {!isCompleted && !isCancelled && (
                    <button
                      type="button"
                      onClick={() => handleCancelInterview(inv.id)}
                      className="px-3 py-2 rounded-xl border border-rose-500/20 text-xs font-mono font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition flex items-center gap-1"
                      title="Cancel Interview"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Cancel</span>
                    </button>
                  )}

                  {/* Enter / Review Live Room */}
                  <a
                    href={`/interview-room/${inv.id}`}
                    className="px-4 py-2 rounded-xl bg-oxblood text-white text-xs font-mono font-bold hover:bg-oxblood/90 transition shadow flex items-center gap-1.5"
                  >
                    <Video className="w-3.5 h-3.5" />
                    <span>{isCompleted ? 'Review Room' : isOngoing ? 'Join Room (Live)' : 'Enter Room'}</span>
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL: VIEW INTERVIEW DETAILS */}
      <AnimatePresence>
        {selectedDetailInterview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-ivory dark:bg-charcoal p-6 sm:p-8 rounded-3xl border border-slate/20 dark:border-rose/20 shadow-2xl max-w-xl w-full space-y-5"
            >
              <div className="flex justify-between items-start border-b border-slate/15 pb-3">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                    Interview Dossier
                  </span>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory mt-1">
                    {selectedDetailInterview.candidate_name || 'Candidate'}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedDetailInterview(null)}
                  className="p-1.5 rounded-xl hover:bg-slate/10 transition"
                >
                  <X className="w-5 h-5 text-slate/60" />
                </button>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-white/50 dark:bg-black/20 border border-slate/15">
                  <div>
                    <span className="text-[10px] text-slate/50 block">Target Role</span>
                    <span className="font-bold text-charcoal dark:text-ivory">
                      {selectedDetailInterview.job_title || selectedDetailInterview.application?.job?.title || "Role"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate/50 block">Interview Workflow</span>
                    <span className="font-bold text-oxblood dark:text-rose uppercase">
                      {selectedDetailInterview.interview_mode || "HUMAN"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate/50 block">Scheduled Time</span>
                    <span className="font-bold text-charcoal dark:text-ivory">
                      {new Date(selectedDetailInterview.scheduled_time || selectedDetailInterview.scheduled_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate/50 block">Duration</span>
                    <span className="font-bold text-charcoal dark:text-ivory">
                      {selectedDetailInterview.duration_minutes || 45} Minutes
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate/50 block">Room ID</span>
                    <span className="font-bold text-slate/70 dark:text-ivory/70">
                      {selectedDetailInterview.room_id || "Auto-assigned"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate/50 block">Status</span>
                    <span className="font-bold text-charcoal dark:text-ivory">
                      {selectedDetailInterview.status}
                    </span>
                  </div>
                </div>

                {selectedDetailInterview.meeting_link && (
                  <div>
                    <span className="text-[10px] text-slate/50 block mb-0.5">Meeting Link</span>
                    <a
                      href={selectedDetailInterview.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-oxblood dark:text-rose underline break-all"
                    >
                      {selectedDetailInterview.meeting_link}
                    </a>
                  </div>
                )}

                {selectedDetailInterview.instructions && (
                  <div>
                    <span className="text-[10px] text-slate/50 block mb-0.5">Instructions</span>
                    <p className="p-3 rounded-xl bg-white/40 dark:bg-black/20 text-slate/80 dark:text-ivory/80 whitespace-pre-wrap">
                      {selectedDetailInterview.instructions}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedDetailInterview(null)}
                  className="px-4 py-2 rounded-xl border border-slate/20 text-xs font-bold"
                >
                  Close
                </button>
                <a
                  href={`/interview-room/${selectedDetailInterview.id}`}
                  className="px-5 py-2 rounded-xl btn-oxblood text-xs font-bold flex items-center gap-1.5"
                >
                  <Video className="w-3.5 h-3.5" />
                  <span>Launch Room</span>
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL: EDIT SCHEDULE */}
      <AnimatePresence>
        {selectedEditInterview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-ivory dark:bg-charcoal p-6 sm:p-8 rounded-3xl border border-slate/20 dark:border-rose/20 shadow-2xl max-w-lg w-full space-y-4"
            >
              <div className="flex justify-between items-start border-b border-slate/15 pb-3">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                    Reschedule & Edit
                  </span>
                  <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory mt-1">
                    Edit Interview Schedule
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedEditInterview(null)}
                  className="p-1.5 rounded-xl hover:bg-slate/10 transition"
                >
                  <X className="w-5 h-5 text-slate/60" />
                </button>
              </div>

              <div className="space-y-4 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate/70 mb-1">Date</label>
                    <input
                      type="date"
                      value={editDate}
                      onChange={(e) => setEditDate(e.target.value)}
                      className="w-full glass-input text-xs min-h-[40px]"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate/70 mb-1">Time</label>
                    <input
                      type="time"
                      value={editTime}
                      onChange={(e) => setEditTime(e.target.value)}
                      className="w-full glass-input text-xs min-h-[40px]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 mb-1">Duration (Mins)</label>
                  <select
                    value={editDuration}
                    onChange={(e) => setEditDuration(e.target.value)}
                    className="w-full glass-input text-xs min-h-[40px]"
                  >
                    <option value="30">30 Minutes</option>
                    <option value="45">45 Minutes</option>
                    <option value="60">60 Minutes</option>
                    <option value="90">90 Minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 mb-1">Meeting Link</label>
                  <input
                    type="text"
                    value={editLink}
                    onChange={(e) => setEditLink(e.target.value)}
                    className="w-full glass-input text-xs min-h-[40px]"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 mb-1">Instructions</label>
                  <textarea
                    rows="2"
                    value={editInstructions}
                    onChange={(e) => setEditInstructions(e.target.value)}
                    className="w-full glass-input text-xs font-sans"
                    placeholder="Candidate preparation notes..."
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setSelectedEditInterview(null)}
                  className="px-4 py-2 rounded-xl border border-slate/20 text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={savingEdit}
                  className="px-5 py-2 rounded-xl btn-oxblood text-xs font-bold"
                >
                  {savingEdit ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL: CANDIDATE PICKER (WHEN SCHEDULING FROM INTERVIEW HUB) */}
      <AnimatePresence>
        {showCandidatePickerModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-ivory dark:bg-charcoal p-6 sm:p-8 rounded-3xl border border-slate/20 dark:border-rose/20 shadow-2xl max-w-xl w-full space-y-4"
            >
              <div className="flex justify-between items-start border-b border-slate/15 pb-3">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                    Schedule Interview
                  </span>
                  <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory mt-1">
                    Select Candidate to Interview
                  </h3>
                </div>
                <button
                  onClick={() => setShowCandidatePickerModal(false)}
                  className="p-1.5 rounded-xl hover:bg-slate/10 transition"
                >
                  <X className="w-5 h-5 text-slate/60" />
                </button>
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {applicants.length === 0 ? (
                  <p className="text-xs text-slate/50 text-center py-6">No active applicants available.</p>
                ) : (
                  applicants.map((app) => (
                    <div
                      key={app.id}
                      onClick={() => {
                        setShowCandidatePickerModal(false);
                        if (onScheduleNewInterview) onScheduleNewInterview(app);
                      }}
                      className="p-3 rounded-2xl border border-slate/15 dark:border-rose/15 hover:border-oxblood/40 hover:bg-oxblood/5 cursor-pointer transition flex items-center justify-between"
                    >
                      <div>
                        <span className="font-display font-bold text-sm text-charcoal dark:text-ivory block">
                          {app.candidate?.name || "Applicant"}
                        </span>
                        <span className="text-xs text-slate/60 dark:text-ivory/60 font-mono">
                          {app.job?.title || "Role"} · Status: {app.status}
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate/40" />
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL 1: AI Configuration & Question Studio */}
      <AnimatePresence>
        {showConfigModal && configInterview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-ivory dark:bg-charcoal p-6 sm:p-8 rounded-3xl border border-slate/20 dark:border-rose/20 shadow-2xl max-w-3xl w-full my-8 space-y-6 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b border-slate/15 pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                      AI Interview Studio
                    </span>
                    <span className="text-xs text-slate/50 font-mono">
                      {configInterview.candidate_name || 'Candidate'}
                    </span>
                  </div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">
                    Configure Interview Mode & Question Protocol
                  </h3>
                </div>
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="p-1.5 rounded-xl hover:bg-slate/10 transition"
                >
                  <X className="w-5 h-5 text-slate/60" />
                </button>
              </div>

              {/* Workflow Mode Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-charcoal dark:text-ivory uppercase tracking-wider">
                  Select Workflow Mode
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { key: 'AI_LIVE', label: 'Autonomous AI Live', desc: 'AI agent leads voice interview' },
                    { key: 'HYBRID', label: 'Hybrid AI + Recruiter', desc: 'Recruiter can take over and hand back' },
                    { key: 'CONFIGURED', label: 'Configured Script', desc: 'Strict question rubric sequence' }
                  ].map((m) => (
                    <div
                      key={m.key}
                      onClick={() => setSelectedMode(m.key)}
                      className={`p-3.5 rounded-2xl border cursor-pointer transition ${
                        selectedMode === m.key
                          ? 'bg-oxblood/10 border-oxblood dark:border-rose'
                          : 'border-slate/15 hover:border-oxblood/30'
                      }`}
                    >
                      <span className="font-bold text-xs text-charcoal dark:text-ivory block">{m.label}</span>
                      <span className="text-[11px] text-slate/60 dark:text-ivory/60 mt-0.5 block">{m.desc}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Engine Parameters */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate/60 mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    min="15"
                    max="90"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-slate/60 mb-1">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                  >
                    <option value="ENTRY">Entry Level</option>
                    <option value="INTERMEDIATE">Intermediate Level</option>
                    <option value="SENIOR">Senior Level</option>
                    <option value="LEAD">Staff / Principal Lead</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-slate/60 mb-1">Voice Profile</label>
                  <select
                    value={voice}
                    onChange={(e) => setVoice(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                  >
                    <option value="alloy">Alloy (Balanced)</option>
                    <option value="echo">Echo (Authoritative)</option>
                    <option value="fable">Fable (Warm)</option>
                    <option value="onyx">Onyx (Deep)</option>
                    <option value="nova">Nova (Energetic)</option>
                    <option value="shimmer">Shimmer (Precise)</option>
                  </select>
                </div>
              </div>

              {/* Hybrid Takeover Setting */}
              {selectedMode === 'HYBRID' && (
                <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-xs text-emerald-800 dark:text-emerald-300 block">
                      Recruiter Takeover Permissions
                    </span>
                    <span className="text-[11px] text-emerald-700 dark:text-emerald-400">
                      Allows recruiters in the LiveKit room to pause the AI speech and ask questions directly.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={allowTakeover}
                    onChange={(e) => setAllowTakeover(e.target.checked)}
                    className="w-4 h-4 accent-emerald-600 rounded"
                  />
                </div>
              )}

              {/* Competency Categories */}
              <div>
                <label className="text-xs font-bold text-charcoal dark:text-ivory uppercase tracking-wider block mb-2">
                  Evaluation Competency Areas
                </label>
                <div className="flex flex-wrap gap-2">
                  {['TECHNICAL', 'PROBLEM_SOLVING', 'BEHAVIORAL', 'ROLE_SPECIFIC', 'SITUATIONAL'].map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => toggleCategory(cat)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-mono transition ${
                        selectedCategories.includes(cat)
                          ? 'bg-oxblood text-white font-bold'
                          : 'bg-white/40 dark:bg-white/5 text-slate/60 border border-slate/15'
                      }`}
                    >
                      {cat.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Questions Management */}
              <div className="space-y-3 pt-2 border-t border-slate/15">
                <div className="flex justify-between items-center">
                  <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                    Approved Interview Questions ({questions.length})
                  </h4>
                  <button
                    type="button"
                    onClick={handleGenerateQuestions}
                    disabled={generatingQuestions}
                    className="px-3 py-1.5 rounded-xl bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose border border-oxblood/20 text-xs font-bold hover:bg-oxblood/20 transition flex items-center gap-1.5"
                  >
                    <Sparkles className={`w-3.5 h-3.5 ${generatingQuestions ? 'animate-spin' : ''}`} />
                    <span>{generatingQuestions ? 'Generating...' : 'Auto-Generate Questions'}</span>
                  </button>
                </div>

                {/* Questions List */}
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {questions.length === 0 ? (
                    <div className="text-center py-6 border border-dashed border-slate/20 rounded-2xl">
                      <p className="text-xs text-slate/50">
                        No questions added yet. Click Auto-Generate or add custom questions below.
                      </p>
                    </div>
                  ) : (
                    questions.map((q, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-white/50 dark:bg-black/20 border border-slate/15 flex justify-between items-start gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded-md bg-slate/10 text-[10px] font-mono font-bold">
                              Q{idx + 1}
                            </span>
                            <span className="px-2 py-0.5 rounded-md bg-oxblood/10 text-oxblood text-[10px] font-mono font-bold">
                              {q.question_type}
                            </span>
                            <span className="text-[10px] text-slate/50 font-mono">
                              Max: {q.max_duration_seconds || 180}s
                            </span>
                          </div>
                          <p className="text-xs text-charcoal dark:text-ivory font-sans leading-relaxed">
                            {q.question_text}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveQuestion(idx)}
                          className="p-1 hover:text-error transition"
                          title="Remove question"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Custom Question Row */}
                <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-2">
                  <span className="text-xs font-bold text-slate/70 block">Add Custom Question</span>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text"
                      placeholder="Enter tailored question for candidate..."
                      value={newQuestionText}
                      onChange={(e) => setNewQuestionText(e.target.value)}
                      className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                    />
                    <select
                      value={newQuestionType}
                      onChange={(e) => setNewQuestionType(e.target.value)}
                      className="px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                    >
                      <option value="TECHNICAL">TECHNICAL</option>
                      <option value="PROBLEM_SOLVING">PROBLEM SOLVING</option>
                      <option value="BEHAVIORAL">BEHAVIORAL</option>
                      <option value="ROLE_SPECIFIC">ROLE SPECIFIC</option>
                    </select>
                    <button
                      type="button"
                      onClick={handleAddCustomQuestion}
                      className="px-4 py-2 rounded-xl bg-oxblood text-white text-xs font-bold hover:bg-oxblood/90 transition"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t border-slate/15">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
                  className="px-4 py-2.5 rounded-xl border border-slate/20 text-xs font-mono font-bold hover:border-slate/40 transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveConfig}
                  disabled={savingConfig}
                  className="px-5 py-2.5 rounded-xl bg-oxblood text-white text-xs font-mono font-bold hover:bg-oxblood/90 transition shadow flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{savingConfig ? 'Saving Protocol...' : 'Save Protocol'}</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL 2: Evaluation & Competency Scorecard */}
      <AnimatePresence>
        {showEvalModal && selectedEvalInterview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-ivory dark:bg-charcoal p-6 sm:p-8 rounded-3xl border border-slate/20 dark:border-rose/20 shadow-2xl max-w-2xl w-full my-8 space-y-6 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b border-slate/15 pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                      AI Competency Scorecard
                    </span>
                    <span className="text-xs text-slate/50 font-mono">
                      {selectedEvalInterview.candidate_name || 'Candidate'}
                    </span>
                  </div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">
                    Interview Evaluation & Performance Insights
                  </h3>
                </div>
                <button
                  onClick={() => setShowEvalModal(false)}
                  className="p-1.5 rounded-xl hover:bg-slate/10 transition"
                >
                  <X className="w-5 h-5 text-slate/60" />
                </button>
              </div>

              {evalLoading ? (
                <div className="py-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-oxblood animate-spin mx-auto" />
                  <p className="text-xs text-slate/60 font-mono">Synthesizing candidate competency evaluation...</p>
                </div>
              ) : evaluationData ? (
                <div className="space-y-6">
                  {/* Overall Rating & Recommendation */}
                  <div className="p-4 rounded-2xl bg-oxblood/5 dark:bg-rose/5 border border-oxblood/20 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-mono uppercase text-slate/60 dark:text-rose block">Overall Assessment</span>
                      <h4 className="font-display font-bold text-xl text-charcoal dark:text-ivory mt-0.5">
                        Score: {evaluationData.overall_score || 4.0} / 5.0
                      </h4>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                      {evaluationData.review_status || 'RECOMMENDED'}
                    </span>
                  </div>

                  {/* Summary */}
                  {evaluationData.overall_summary && (
                    <div className="p-4 rounded-2xl bg-white/50 dark:bg-black/20 border border-slate/15">
                      <span className="text-xs font-bold text-charcoal dark:text-ivory block mb-1">
                        Executive Summary
                      </span>
                      <p className="text-xs text-slate/70 dark:text-ivory/70 leading-relaxed font-sans">
                        {evaluationData.overall_summary}
                      </p>
                    </div>
                  )}

                  {/* Competency Spider/List Breakdown */}
                  {evaluationData.competency_scores && (
                    <div>
                      <span className="text-xs font-bold text-charcoal dark:text-ivory uppercase tracking-wider block mb-3">
                        Competency Breakdown
                      </span>
                      <div className="space-y-2">
                        {Object.entries(evaluationData.competency_scores).map(([comp, score]) => (
                          <div key={comp} className="flex items-center justify-between text-xs font-mono">
                            <span className="capitalize text-slate/70 dark:text-ivory/70">
                              {comp.replace('_', ' ')}
                            </span>
                            <div className="flex items-center gap-3">
                              <div className="w-32 h-2 rounded-full bg-slate/10 dark:bg-white/10 overflow-hidden">
                                <div
                                  className="h-full bg-oxblood rounded-full"
                                  style={{ width: `${(Number(score) / 5) * 100}%` }}
                                ></div>
                              </div>
                              <span className="font-bold text-charcoal dark:text-ivory w-8 text-right">
                                {score}/5
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Strengths & Recommendations */}
                  <div className="space-y-3">
                    {evaluationData.strengths && (
                      <div>
                        <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 block mb-1">
                          Key Strengths Observed
                        </span>
                        <p className="text-xs text-slate/70 dark:text-ivory/70 whitespace-pre-line leading-relaxed">
                          {evaluationData.strengths}
                        </p>
                      </div>
                    )}

                    {evaluationData.recommendations && (
                      <div>
                        <span className="text-xs font-bold text-oxblood dark:text-rose block mb-1">
                          Hiring Recommendation
                        </span>
                        <p className="text-xs text-slate/70 dark:text-ivory/70 leading-relaxed">
                          {evaluationData.recommendations}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Recruiter Override & Notes */}
                  <div className="p-4 rounded-2xl border border-oxblood/30 space-y-3">
                    <span className="text-xs font-bold text-charcoal dark:text-ivory block">
                      Recruiter Override & Calibration
                    </span>
                    <div className="flex items-center gap-4">
                      <label className="text-xs text-slate/60">Adjust Score:</label>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        step="0.1"
                        value={recruiterOverrideScore}
                        onChange={(e) => setRecruiterOverrideScore(e.target.value)}
                        className="flex-1 accent-oxblood"
                      />
                      <span className="font-mono font-bold text-sm text-oxblood">{recruiterOverrideScore}</span>
                    </div>

                    <div>
                      <label className="text-xs text-slate/60 block mb-1">Recruiter Notes:</label>
                      <textarea
                        rows="2"
                        placeholder="Add confidential recruiter notes or feedback justification..."
                        value={recruiterNotes}
                        onChange={(e) => setRecruiterNotes(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-slate/20 bg-white/60 dark:bg-black/20"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={handleSaveEvaluationOverride}
                        disabled={savingOverride}
                        className="px-4 py-2 rounded-xl bg-oxblood text-white text-xs font-mono font-bold hover:bg-oxblood/90 transition shadow flex items-center gap-1.5"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{savingOverride ? 'Saving...' : 'Accept & Calibrate'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="w-8 h-8 text-slate/40 mx-auto mb-2" />
                  <p className="text-xs text-slate/60">No evaluation data available yet.</p>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
