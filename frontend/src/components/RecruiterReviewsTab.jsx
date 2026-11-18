import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Award, Clock, CheckCircle2, XCircle, AlertTriangle, ShieldCheck,
  Search, Filter, Eye, Edit3, Send, Check, X, ChevronDown,
  HelpCircle, Briefcase, History, User, Mail, FileText, RotateCcw,
  BarChart3, ArrowRight, Sparkles, AlertCircle, Info, RefreshCw, Video
} from 'lucide-react';
import { assessmentsAPI } from '../services/api';
import { GlassModal, useToast, AnimatedCounter } from './MotionComponents';

export const RecruiterReviewsTab = ({ jobs = [], assessments = [] }) => {
  const { addToast } = useToast();

  // Review List State
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [jobFilter, setJobFilter] = useState('');
  const [assessmentFilter, setAssessmentFilter] = useState('');
  const [sortBy, setSortBy] = useState('submitted_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Detailed Review Modal State
  const [selectedAssignmentId, setSelectedAssignmentId] = useState(null);
  const [detailedReview, setDetailedReview] = useState(null);
  const [detailedLoading, setDetailedLoading] = useState(false);
  const [sessionVideoError, setSessionVideoError] = useState(false);
  const [activeReviewTab, setActiveReviewTab] = useState('answers'); // 'answers' | 'adjustment' | 'proctoring' | 'history'
  const [answerFilter, setAnswerFilter] = useState('ALL'); // 'ALL' | 'CORRECT' | 'INCORRECT' | 'UNANSWERED'

  // Score Adjustment Form State
  const [adjScore, setAdjScore] = useState('');
  const [adjReason, setAdjReason] = useState('');
  const [isAdjusting, setIsAdjusting] = useState(false);

  // Decision Confirmation Dialog State
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisionTarget, setDecisionTarget] = useState(null); // 'ACCEPTED' | 'REJECTED' | 'MOVED_TO_INTERVIEW' | 'ON_HOLD'
  const [decisionReason, setDecisionReason] = useState('');
  const [decisionRemarks, setDecisionRemarks] = useState('');
  const [candidateMessage, setCandidateMessage] = useState('');
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);

  // Comparison & Analytics Modal State
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [comparisonAssessmentId, setComparisonAssessmentId] = useState(null);
  const [comparisonAssessmentTitle, setComparisonAssessmentTitle] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Fetch reviews list from backend
  const fetchReviews = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (statusFilter && statusFilter !== 'ALL') params.review_status = statusFilter;
      if (jobFilter) params.job_id = jobFilter;
      if (assessmentFilter) params.assessment_id = assessmentFilter;
      if (sortBy) params.sort_by = sortBy;
      if (sortOrder) params.sort_order = sortOrder;

      const res = await assessmentsAPI.listReviews(params);
      setReviews(res.data || []);
    } catch (err) {
      console.error('Failed to load assessment reviews:', err);
      setError(err.response?.data?.detail || 'Failed to retrieve assessment reviews.');
      addToast('Could not load assessment reviews.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [statusFilter, jobFilter, assessmentFilter, sortBy, sortOrder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchReviews();
  };

  // Open Detailed Review
  const handleOpenDetailedReview = async (assignmentId) => {
    setSelectedAssignmentId(assignmentId);
    setActiveReviewTab('answers');
    setAnswerFilter('ALL');
    try {
      setDetailedLoading(true);
      const res = await assessmentsAPI.getDetailedReview(assignmentId);
      setDetailedReview(res.data);
      setSessionVideoError(false);
      setAdjScore(res.data.marks_obtained);
      setAdjReason('');
    } catch (err) {
      console.error('Failed to load detailed review:', err);
      addToast(err.response?.data?.detail || 'Failed to load detailed review.', 'error');
      setSelectedAssignmentId(null);
    } finally {
      setDetailedLoading(false);
    }
  };

  // Refresh current detailed review
  const reloadCurrentDetailedReview = async () => {
    if (!selectedAssignmentId) return;
    try {
      const res = await assessmentsAPI.getDetailedReview(selectedAssignmentId);
      setDetailedReview(res.data);
      setSessionVideoError(false);
      setAdjScore(res.data.marks_obtained);
      setAdjReason('');
    } catch (err) {
      console.error('Failed to reload detailed review:', err);
    }
  };

  // Submit Score Adjustment
  const handleScoreAdjustmentSubmit = async (e) => {
    e.preventDefault();
    if (!adjReason || adjReason.trim().length < 3) {
      addToast('A clear justification reason (at least 3 characters) is required for score adjustments.', 'error');
      return;
    }
    const numScore = Number(adjScore);
    if (isNaN(numScore) || numScore < 0 || numScore > (detailedReview?.total_marks || 100)) {
      addToast(`Adjusted score must be between 0 and ${detailedReview?.total_marks || 100}.`, 'error');
      return;
    }

    try {
      setIsAdjusting(true);
      await assessmentsAPI.adjustScore(selectedAssignmentId, {
        adjusted_score: numScore,
        reason: adjReason.trim()
      });
      addToast('Candidate score adjusted successfully. Decision history updated.', 'success');
      await reloadCurrentDetailedReview();
      fetchReviews();
    } catch (err) {
      console.error('Failed to adjust score:', err);
      addToast(err.response?.data?.detail || 'Failed to adjust score.', 'error');
    } finally {
      setIsAdjusting(false);
    }
  };

  // Prompt Decision Dialog
  const handlePromptDecision = (decision) => {
    setDecisionTarget(decision);
    setDecisionReason('');
    setDecisionRemarks('');
    setCandidateMessage('');
    setShowDecisionModal(true);
  };

  // Submit Decision
  const handleConfirmDecision = async () => {
    if (decisionTarget === 'REJECTED' && (!decisionReason || decisionReason.trim().length < 3)) {
      addToast('A decision reason is mandatory when rejecting a candidate.', 'error');
      return;
    }

    try {
      setIsSubmittingDecision(true);
      const payload = {
        decision: decisionTarget,
        decision_reason: decisionReason.trim() || null,
        recruiter_remarks: decisionRemarks.trim() || null,
        candidate_message: candidateMessage.trim() || null
      };

      const res = await assessmentsAPI.makeDecision(selectedAssignmentId, payload);
      addToast(`Decision recorded: ${decisionTarget.replace(/_/g, ' ')}. Notification email dispatched: ${res.data.email_dispatched ? 'Yes' : 'No'}.`, 'success');
      setShowDecisionModal(false);
      await reloadCurrentDetailedReview();
      fetchReviews();
    } catch (err) {
      console.error('Failed to record decision:', err);
      addToast(err.response?.data?.detail || 'Failed to record decision.', 'error');
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  // Retry Failed Decision Email
  const handleRetryEmail = async (assignmentId) => {
    try {
      await assessmentsAPI.retryEmail(assignmentId);
      addToast('Decision email retry triggered successfully.', 'success');
      if (selectedAssignmentId === assignmentId) {
        await reloadCurrentDetailedReview();
      }
      fetchReviews();
    } catch (err) {
      console.error('Failed to retry email:', err);
      addToast(err.response?.data?.detail || 'Failed to retry email.', 'error');
    }
  };

  // Open Comparison Modal
  const handleOpenComparison = async (assessmentId, assessmentTitle) => {
    setComparisonAssessmentId(assessmentId);
    setComparisonAssessmentTitle(assessmentTitle);
    setShowComparisonModal(true);
    try {
      setComparisonLoading(true);
      const res = await assessmentsAPI.getComparison(assessmentId);
      setComparisonData(res.data);
    } catch (err) {
      console.error('Failed to load assessment comparison:', err);
      addToast(err.response?.data?.detail || 'Failed to load assessment comparison data.', 'error');
    } finally {
      setComparisonLoading(false);
    }
  };

  // Helper for Status Badges
  const renderReviewStatusBadge = (status) => {
    const map = {
      PENDING_REVIEW: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      UNDER_REVIEW: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      ACCEPTED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      REJECTED: 'bg-oxblood/30 text-rose border-rose/30',
      ON_HOLD: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
      MOVED_TO_INTERVIEW: 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    };
    const label = status ? status.replace(/_/g, ' ') : 'PENDING';
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase border ${
        map[status] || 'bg-white/10 text-ivory/70 border-white/20'
      }`}>
        {label}
      </span>
    );
  };

  // Helper for Email Status Badges
  const renderEmailStatusPill = (status, assignmentId) => {
    if (!status || status === 'NOT_APPLICABLE') {
      return <span className="text-[10px] font-mono text-slate/40 dark:text-ivory/30">N/A</span>;
    }
    if (status === 'SENT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-400">
          <CheckCircle2 size={12} /> SENT
        </span>
      );
    }
    if (status === 'FAILED') {
      return (
        <div className="inline-flex items-center gap-1.5">
          <span className="text-[10px] font-mono font-bold text-rose inline-flex items-center gap-1">
            <XCircle size={12} /> FAILED
          </span>
          <button
            onClick={() => handleRetryEmail(assignmentId)}
            title="Retry Email Dispatch"
            className="p-1 rounded-lg bg-rose/20 hover:bg-rose/30 text-rose transition-colors"
          >
            <RotateCcw size={11} />
          </button>
        </div>
      );
    }
    return (
      <span className="text-[10px] font-mono text-amber-400 inline-flex items-center gap-1">
        <Clock size={12} /> PENDING
      </span>
    );
  };

  // Filtered Detailed Answers
  const filteredAnswers = useMemo(() => {
    if (!detailedReview?.answers) return [];
    if (answerFilter === 'ALL') return detailedReview.answers;
    return detailedReview.answers.filter((a) => a.status === answerFilter);
  }, [detailedReview, answerFilter]);

  return (
    <div className="space-y-6">
      {/* Search & Filter Header Toolbar */}
      <div className="glass-card p-5 sm:p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h2 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
              <ShieldCheck className="text-oxblood dark:text-rose w-5 h-5" />
              Assessment Reviews & Hiring Decisions
            </h2>
            <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 mt-1">
              Private candidate evaluations, answer-by-answer audits, score overrides, proctoring timeline, and decision actions.
            </p>
          </div>

          <button
            onClick={fetchReviews}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-2 min-h-[40px] shrink-0"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh Reviews
          </button>
        </div>

        {/* Filter Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2 border-t border-slate/10 dark:border-white/5">
          {/* Search by Candidate */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate/40 dark:text-ivory/40" />
            <input
              type="text"
              placeholder="Candidate name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            />
          </form>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            >
              <option value="ALL">All Review Statuses</option>
              <option value="PENDING_REVIEW">Pending Review</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected</option>
              <option value="MOVED_TO_INTERVIEW">Moved to Interview</option>
              <option value="ON_HOLD">On Hold</option>
            </select>
          </div>

          {/* Job Filter */}
          <div>
            <select
              value={jobFilter}
              onChange={(e) => setJobFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            >
              <option value="">All Job Positions</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>{j.title}</option>
              ))}
            </select>
          </div>

          {/* Assessment Filter */}
          <div>
            <select
              value={assessmentFilter}
              onChange={(e) => setAssessmentFilter(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            >
              <option value="">All Assessments</option>
              {assessments.map((a) => (
                <option key={a.id} value={a.id}>{a.title}</option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex gap-1.5">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-2/3 px-2.5 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            >
              <option value="submitted_at">Submitted</option>
              <option value="score">Score</option>
              <option value="accuracy">Accuracy</option>
              <option value="candidate_name">Candidate</option>
              <option value="time_taken">Time Taken</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="w-1/3 px-2 py-2 text-xs font-mono uppercase font-bold rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory flex items-center justify-center min-h-[38px]"
              title="Toggle sort order"
            >
              {sortOrder.toUpperCase()}
            </button>
          </div>
        </div>
      </div>

      {/* Reviews Table */}
      {loading ? (
        <div className="py-20 text-center font-mono text-xs text-slate/60 dark:text-ivory/50 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 text-oxblood animate-spin" />
          <p>Retrieving private assessment submissions & telemetry...</p>
        </div>
      ) : reviews.length === 0 ? (
        <div className="glass-card p-12 text-center rounded-3xl border border-dashed border-slate/20 dark:border-rose/20 space-y-3">
          <Award className="w-12 h-12 text-slate/40 dark:text-rose/40 mx-auto" />
          <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
            No Assessment Submissions Found
          </h3>
          <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 max-w-md mx-auto">
            {statusFilter !== 'ALL' || search || jobFilter || assessmentFilter
              ? 'No candidate submissions match your active filter criteria. Try adjusting your filters.'
              : 'When shortlisted candidates submit their Round 1 MCQ assessments, their private scores and review dossiers will appear here.'}
          </p>
        </div>
      ) : (
        <div className="glass-card rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate/5 dark:bg-white/5 border-b border-slate/10 dark:border-white/10 uppercase text-[10px] text-slate/50 dark:text-ivory/40">
                <tr>
                  <th className="py-3.5 px-4 font-bold">Candidate</th>
                  <th className="py-3.5 px-4 font-bold">Job & Assessment</th>
                  <th className="py-3.5 px-4 font-bold">Submitted At</th>
                  <th className="py-3.5 px-4 font-bold">Score & Accuracy</th>
                  <th className="py-3.5 px-4 font-bold text-center">Benchmark</th>
                  <th className="py-3.5 px-4 font-bold text-center">Telemetry</th>
                  <th className="py-3.5 px-4 font-bold text-center">Review Status</th>
                  <th className="py-3.5 px-4 font-bold text-center">Decision Email</th>
                  <th className="py-3.5 px-4 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate/10 dark:divide-white/5">
                {reviews.map((rev) => {
                  const minutesTaken = rev.completion_time_seconds ? Math.round(rev.completion_time_seconds / 60) : 0;
                  return (
                    <tr key={rev.assignment_id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                      {/* Candidate Column */}
                      <td className="py-4 px-4">
                        <div className="font-sans font-bold text-sm text-charcoal dark:text-ivory">
                          {rev.candidate_name}
                        </div>
                        <div className="text-[11px] text-slate/50 dark:text-ivory/50 mt-0.5">
                          {rev.candidate_email}
                        </div>
                      </td>

                      {/* Job & Assessment Column */}
                      <td className="py-4 px-4 max-w-[200px]">
                        <div className="text-charcoal dark:text-ivory font-bold truncate">
                          {rev.assessment_title}
                        </div>
                        <div className="text-[10px] text-slate/50 dark:text-ivory/50 truncate mt-0.5">
                          {rev.job_title}
                        </div>
                      </td>

                      {/* Submitted At */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <div className="text-charcoal dark:text-ivory">
                          {rev.submitted_at ? new Date(rev.submitted_at).toLocaleDateString() : 'N/A'}
                        </div>
                        <div className="text-[10px] text-slate/50 dark:text-ivory/50">
                          {rev.submitted_at ? new Date(rev.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''} ({minutesTaken}m)
                        </div>
                      </td>

                      {/* Score & Accuracy */}
                      <td className="py-4 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 font-bold text-sm text-charcoal dark:text-ivory">
                          <span>{rev.score_obtained}</span>
                          <span className="text-[10px] text-slate/40 dark:text-ivory/40">/ {rev.total_marks}</span>
                          {rev.is_score_adjusted && (
                            <span className="text-[9px] px-1 rounded bg-amber-500/20 text-amber-400 font-normal" title={`Adjusted from ${rev.original_score}`}>
                              Adj
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate/50 dark:text-ivory/50 mt-0.5">
                          {rev.accuracy_percentage}% &bull; {rev.correct_count}C / {rev.incorrect_count}I
                        </div>
                      </td>

                      {/* Benchmark Outcome */}
                      <td className="py-4 px-4 text-center whitespace-nowrap">
                        {rev.score_based_outcome === 'PASSED' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/15 text-emerald-400 font-bold">
                            <Check size={11} /> Pass ({rev.passing_marks})
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-oxblood/20 text-rose font-bold">
                            <X size={11} /> Below ({rev.passing_marks})
                          </span>
                        )}
                      </td>

                      {/* Telemetry / Warnings */}
                      <td className="py-4 px-4 text-center whitespace-nowrap">
                        {rev.proctoring_warning_count > 0 ? (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            rev.proctoring_warning_count >= 3 ? 'bg-oxblood/30 text-rose' : 'bg-amber-500/20 text-amber-400'
                          }`}>
                            <AlertTriangle size={11} /> {rev.proctoring_warning_count} Warnings
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400">
                            <ShieldCheck size={11} /> Clean
                          </span>
                        )}
                      </td>

                      {/* Review Status Badge */}
                      <td className="py-4 px-4 text-center whitespace-nowrap">
                        {renderReviewStatusBadge(rev.review_status)}
                      </td>

                      {/* Decision Email Status */}
                      <td className="py-4 px-4 text-center whitespace-nowrap">
                        {renderEmailStatusPill(rev.decision_email_status, rev.assignment_id)}
                      </td>

                      {/* Actions */}
                      <td className="py-4 px-4 text-right whitespace-nowrap space-x-1.5">
                        <button
                          onClick={() => handleOpenComparison(rev.assessment_id, rev.assessment_title)}
                          title="View Leaderboard & Analytics"
                          className="px-2.5 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory text-[11px] font-bold inline-flex items-center gap-1 min-h-[32px]"
                        >
                          <BarChart3 size={13} />
                        </button>

                        <button
                          onClick={() => handleOpenDetailedReview(rev.assignment_id)}
                          className="px-3.5 py-1.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-[11px] font-bold uppercase tracking-wider inline-flex items-center gap-1.5 min-h-[32px] shadow-sm shadow-oxblood/20"
                        >
                          <Eye size={12} /> Review
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 1: DETAILED RECRUITER REVIEW DOSSIER */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={Boolean(selectedAssignmentId)}
        onClose={() => setSelectedAssignmentId(null)}
        title="Candidate Assessment Dossier & Decision Portal"
        subtitle={detailedReview ? `${detailedReview.candidate_name} &bull; ${detailedReview.assessment_title}` : 'Evaluating Candidate'}
      >
        <div className="space-y-6 max-h-[80vh] overflow-y-auto pr-1 text-charcoal dark:text-ivory">
          {detailedLoading ? (
            <div className="py-16 text-center font-mono text-xs space-y-3">
              <RefreshCw className="w-8 h-8 text-oxblood animate-spin mx-auto" />
              <p>Loading candidate response breakdown, audit trail, and proctoring telemetry...</p>
            </div>
          ) : detailedReview ? (
            <>
              {/* Candidate Dossier Summary Card */}
              <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-4 font-mono">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div>
                    <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
                      {detailedReview.candidate_name}
                    </h3>
                    <p className="text-xs text-slate/50 dark:text-ivory/50">
                      {detailedReview.candidate_email} &bull; Position: <span className="text-charcoal dark:text-ivory font-semibold">{detailedReview.job_title}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {renderReviewStatusBadge(detailedReview.review_status)}
                    {detailedReview.final_decision && detailedReview.final_decision !== detailedReview.review_status && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/10 border border-white/20">
                        {detailedReview.final_decision.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                </div>

                {/* Score & Telemetry Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Score Obtained</p>
                    <p className="text-xl font-bold mt-0.5 text-charcoal dark:text-ivory">
                      {detailedReview.marks_obtained} <span className="text-xs text-slate/40 dark:text-ivory/40">/ {detailedReview.total_marks}</span>
                    </p>
                    {detailedReview.is_score_adjusted && (
                      <p className="text-[9px] text-amber-400 mt-0.5">
                        Adj from {detailedReview.original_score}
                      </p>
                    )}
                  </div>

                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Accuracy Rate</p>
                    <p className={`text-xl font-bold mt-0.5 ${
                      detailedReview.accuracy_percentage >= 70 ? 'text-emerald-400' : 'text-rose'
                    }`}>
                      {detailedReview.accuracy_percentage}%
                    </p>
                    <p className="text-[9px] text-slate/40 dark:text-ivory/40 mt-0.5">
                      {detailedReview.correct_count} correct &bull; {detailedReview.incorrect_count} wrong
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Benchmark (Pass)</p>
                    <p className="text-xl font-bold mt-0.5 text-oxblood dark:text-rose">
                      {detailedReview.passing_marks}
                    </p>
                    <p className="text-[9px] text-slate/40 dark:text-ivory/40 mt-0.5">
                      {detailedReview.marks_obtained >= detailedReview.passing_marks ? 'Benchmark Met' : 'Benchmark Not Met'}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Proctoring Telemetry</p>
                    <p className={`text-xl font-bold mt-0.5 ${
                      detailedReview.proctoring_warning_count > 0 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {detailedReview.proctoring_warning_count} Warnings
                    </p>
                    <p className="text-[9px] text-slate/40 dark:text-ivory/40 mt-0.5">
                      Time: {detailedReview.completion_time_seconds ? Math.round(detailedReview.completion_time_seconds / 60) : 0} mins
                    </p>
                  </div>
                </div>

                {/* Score Adjustment Reason Banner (if previously adjusted) */}
                {detailedReview.is_score_adjusted && detailedReview.score_adjustment_reason && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs">
                    <span className="font-bold text-amber-400 uppercase tracking-wider text-[10px] block mb-1">
                      Score Adjustment Justification:
                    </span>
                    <p className="font-sans text-ivory/85 italic">
                      "{detailedReview.score_adjustment_reason}"
                    </p>
                  </div>
                )}
              </div>

              {/* Dossier Navigation Sub-Tabs */}
              <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 font-mono text-xs overflow-x-auto pb-1">
                <button
                  onClick={() => setActiveReviewTab('answers')}
                  className={`py-2 px-4 rounded-xl font-bold uppercase tracking-wider transition-colors min-h-[38px] ${
                    activeReviewTab === 'answers'
                      ? 'bg-oxblood text-ivory'
                      : 'bg-white/5 text-slate/60 dark:text-ivory/60 hover:text-ivory'
                  }`}
                >
                  Question Responses ({detailedReview.answers?.length || 0})
                </button>

                <button
                  onClick={() => setActiveReviewTab('adjustment')}
                  className={`py-2 px-4 rounded-xl font-bold uppercase tracking-wider transition-colors min-h-[38px] ${
                    activeReviewTab === 'adjustment'
                      ? 'bg-oxblood text-ivory'
                      : 'bg-white/5 text-slate/60 dark:text-ivory/60 hover:text-ivory'
                  }`}
                >
                  Score Override
                </button>

                <button
                  onClick={() => setActiveReviewTab('proctoring')}
                  className={`py-2 px-4 rounded-xl font-bold uppercase tracking-wider transition-colors min-h-[38px] ${
                    activeReviewTab === 'proctoring'
                      ? 'bg-oxblood text-ivory'
                      : 'bg-white/5 text-slate/60 dark:text-ivory/60 hover:text-ivory'
                  }`}
                >
                  Proctoring Timeline ({detailedReview.proctoring_timeline?.length || 0})
                </button>

                <button
                  onClick={() => setActiveReviewTab('history')}
                  className={`py-2 px-4 rounded-xl font-bold uppercase tracking-wider transition-colors min-h-[38px] ${
                    activeReviewTab === 'history'
                      ? 'bg-oxblood text-ivory'
                      : 'bg-white/5 text-slate/60 dark:text-ivory/60 hover:text-ivory'
                  }`}
                >
                  Decision Audit Trail ({detailedReview.decision_history?.length || 0})
                </button>

                <button
                  onClick={() => setActiveReviewTab('video')}
                  className={`py-2 px-4 rounded-xl font-bold uppercase tracking-wider transition-colors min-h-[38px] flex items-center gap-1.5 ${
                    activeReviewTab === 'video'
                      ? 'bg-oxblood text-ivory'
                      : 'bg-white/5 text-slate/60 dark:text-ivory/60 hover:text-ivory'
                  }`}
                >
                  <Video size={13} />
                  <span>Session Video {detailedReview.session_recording ? '(Recorded)' : ''}</span>
                </button>
              </div>

              {/* TAB 1: QUESTION RESPONSES */}
              {activeReviewTab === 'answers' && (
                <div className="space-y-4">
                  {/* Answers Filter Pill Row */}
                  <div className="flex items-center gap-2 font-mono text-xs">
                    <span className="text-slate/40 dark:text-ivory/40 uppercase text-[10px]">Filter:</span>
                    {['ALL', 'CORRECT', 'INCORRECT', 'UNANSWERED'].map((filterKey) => (
                      <button
                        key={filterKey}
                        onClick={() => setAnswerFilter(filterKey)}
                        className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider transition-colors ${
                          answerFilter === filterKey
                            ? 'bg-oxblood text-ivory'
                            : 'bg-white/5 text-slate/50 dark:text-ivory/50 hover:bg-white/10'
                        }`}
                      >
                        {filterKey}
                      </button>
                    ))}
                  </div>

                  {filteredAnswers.length === 0 ? (
                    <div className="p-8 text-center font-mono text-xs text-slate/50 dark:text-ivory/50 bg-white/5 rounded-2xl">
                      No questions match the "{answerFilter}" filter.
                    </div>
                  ) : (
                    filteredAnswers.map((ans, idx) => {
                      const isCorrect = ans.status === 'CORRECT';
                      const isUnanswered = ans.status === 'UNANSWERED';
                      return (
                        <div
                          key={ans.question_id || idx}
                          className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3 font-mono"
                        >
                          <div className="flex justify-between items-start gap-2">
                            <div className="flex items-center gap-2">
                              <span className="w-6 h-6 rounded-lg bg-oxblood/20 text-rose font-bold text-xs flex items-center justify-center">
                                Q{ans.question_order}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 uppercase text-slate/60 dark:text-ivory/60">
                                {ans.technology} &bull; {ans.topic}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 uppercase text-slate/60 dark:text-ivory/60">
                                {ans.difficulty}
                              </span>
                            </div>

                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              isCorrect
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : isUnanswered
                                ? 'bg-slate/30 text-slate-400 border border-slate-500/30'
                                : 'bg-oxblood/30 text-rose border border-rose/30'
                            }`}>
                              {ans.status} ({ans.marks_awarded} / {ans.max_marks} pts)
                            </span>
                          </div>

                          {/* Question Text */}
                          <p className="font-sans text-sm font-semibold text-charcoal dark:text-ivory pt-1">
                            {ans.question_text}
                          </p>

                          {/* Options Breakdown */}
                          <div className="space-y-1.5 pt-2">
                            {Object.entries(ans.options || {}).map(([optKey, optVal]) => {
                              const isCandidateChoice = ans.candidate_selected_option === optKey;
                              const isCorrectChoice = ans.correct_answer === optKey;

                              let optBorder = 'border-white/10 bg-white/5';
                              let optBadge = null;

                              if (isCorrectChoice) {
                                optBorder = 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300';
                                optBadge = <span className="text-[9px] font-bold text-emerald-400 ml-auto uppercase">Correct Key</span>;
                              }
                              if (isCandidateChoice) {
                                if (isCorrectChoice) {
                                  optBorder = 'border-emerald-500 bg-emerald-500/20 text-emerald-200';
                                  optBadge = <span className="text-[9px] font-bold text-emerald-300 ml-auto uppercase">Candidate Pick (Correct)</span>;
                                } else {
                                  optBorder = 'border-rose/50 bg-oxblood/20 text-rose';
                                  optBadge = <span className="text-[9px] font-bold text-rose ml-auto uppercase">Candidate Pick (Incorrect)</span>;
                                }
                              }

                              return (
                                <div
                                  key={optKey}
                                  className={`p-2.5 rounded-xl border text-xs font-sans flex items-center gap-2.5 ${optBorder}`}
                                >
                                  <span className="w-5 h-5 rounded-md bg-white/10 font-mono font-bold text-[11px] flex items-center justify-center shrink-0">
                                    {optKey}
                                  </span>
                                  <span className="flex-1">{optVal}</span>
                                  {optBadge}
                                </div>
                              );
                            })}
                          </div>

                          {/* Explanation (if provided) */}
                          {ans.explanation && (
                            <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs font-sans text-slate/70 dark:text-ivory/70 space-y-1">
                              <span className="font-mono text-[10px] uppercase font-bold text-oxblood dark:text-rose block">
                                Explanation & Solution:
                              </span>
                              <p>{ans.explanation}</p>
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* TAB 2: SCORE OVERRIDE */}
              {activeReviewTab === 'adjustment' && (
                <form onSubmit={handleScoreAdjustmentSubmit} className="p-6 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-4 font-mono">
                  <div className="flex items-start gap-3">
                    <Edit3 className="w-5 h-5 text-oxblood dark:text-rose shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-display text-sm font-bold text-charcoal dark:text-ivory">
                        Manual Score Adjustment & Audit Trail
                      </h4>
                      <p className="text-xs text-slate/60 dark:text-ivory/60 mt-0.5">
                        Recruiters may adjust candidate scores post-review. The original auto-calculated score ({detailedReview.original_score}) remains permanently recorded. A justification reason is mandatory.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <div>
                      <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                        New Score Obtained (Max: {detailedReview.total_marks})
                      </label>
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        max={detailedReview.total_marks}
                        value={adjScore}
                        onChange={(e) => setAdjScore(e.target.value)}
                        required
                        className="w-full px-3 py-2 text-sm font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[42px]"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                        Recalculated Percentage
                      </label>
                      <div className="px-3 py-2 text-sm font-mono font-bold rounded-xl bg-white/5 border border-white/10 text-charcoal dark:text-ivory min-h-[42px] flex items-center">
                        {detailedReview.total_marks ? ((Number(adjScore) / detailedReview.total_marks) * 100).toFixed(1) : 0}%
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                      Mandatory Justification Reason <span className="text-rose">*</span>
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Explain the basis for adjusting this candidate's score (e.g. partial credit granted on question 4, ambiguity acknowledged, technical disruption review)..."
                      value={adjReason}
                      onChange={(e) => setAdjReason(e.target.value)}
                      required
                      className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={isAdjusting}
                      className="px-5 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-oxblood/20 min-h-[42px]"
                    >
                      {isAdjusting ? <RefreshCw size={13} className="animate-spin" /> : <SaveIcon size={13} />}
                      Save Adjusted Score
                    </button>
                  </div>
                </form>
              )}

              {/* TAB 3: PROCTORING TELEMETRY TIMELINE */}
              {activeReviewTab === 'proctoring' && (
                <div className="space-y-4 font-mono">
                  <div className="p-4 rounded-xl bg-oxblood/10 border border-oxblood/20 text-xs flex items-start gap-3 text-rose">
                    <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold uppercase tracking-wider text-[11px]">Supervisory Telemetry Policy</p>
                      <p className="text-ivory/80 text-xs mt-0.5 leading-relaxed font-sans">
                        Events below are recorded automatically to assist human recruiters in assessing testing integrity. They do not constitute automatic proof of cheating and should be weighed in the context of the entire technical interview process.
                      </p>
                    </div>
                  </div>

                  {detailedReview.proctoring_timeline?.length === 0 ? (
                    <div className="p-8 rounded-2xl bg-white/5 border border-white/10 text-center text-xs text-slate/50 dark:text-ivory/50">
                      No proctoring anomalies or warning events recorded during this session.
                    </div>
                  ) : (
                    <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/10">
                      {detailedReview.proctoring_timeline.map((evt) => (
                        <div key={evt.id} className="relative p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-xs">
                          <div className="absolute -left-[23px] top-4 w-3 h-3 rounded-full bg-oxblood border-2 border-charcoal" />
                          <div className="flex justify-between items-start gap-2">
                            <div>
                              <span className="font-bold text-charcoal dark:text-ivory uppercase tracking-wider">
                                {evt.event_type.replace(/_/g, ' ')}
                              </span>
                              <span className={`ml-2 px-2 py-0.2 rounded text-[9px] font-bold uppercase ${
                                evt.severity === 'HIGH' ? 'bg-oxblood/30 text-rose' : evt.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate/30 text-slate-300'
                              }`}>
                                {evt.severity}
                              </span>
                            </div>

                            <span className="text-[10px] text-slate/40 dark:text-ivory/40">
                              {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : ''}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate/60 dark:text-ivory/60 mt-1 font-sans">
                            Duration: {evt.duration_seconds ? `${evt.duration_seconds.toFixed(1)}s` : 'Instantaneous'}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: DECISION AUDIT TRAIL */}
              {activeReviewTab === 'history' && (
                <div className="space-y-4 font-mono">
                  {detailedReview.decision_history?.length === 0 ? (
                    <div className="p-8 rounded-2xl bg-white/5 border border-white/10 text-center text-xs text-slate/50 dark:text-ivory/50">
                      No hiring decisions or score modifications recorded yet.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {detailedReview.decision_history.map((hist) => (
                        <div
                          key={hist.id}
                          className="p-4 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-xs space-y-1.5"
                        >
                          <div className="flex justify-between items-start gap-2">
                            <span className="font-bold text-charcoal dark:text-ivory uppercase tracking-wider text-[11px]">
                              {hist.decision.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[10px] text-slate/40 dark:text-ivory/40">
                              {hist.decided_at ? new Date(hist.decided_at).toLocaleString() : ''}
                            </span>
                          </div>

                          <div className="text-slate/60 dark:text-ivory/60 text-[11px]">
                            By Recruiter: <span className="text-charcoal dark:text-ivory font-semibold">{hist.recruiter_name}</span>
                          </div>

                          {hist.decision_reason && (
                            <p className="text-ivory/80 font-sans italic text-xs pt-1">
                              Reason: "{hist.decision_reason}"
                            </p>
                          )}

                          {hist.recruiter_remarks && (
                            <p className="text-ivory/60 font-sans text-xs">
                              Remarks: {hist.recruiter_remarks}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: SESSION VIDEO RECORDING PLAYBACK */}
              {activeReviewTab === 'video' && (
                <div className="space-y-4 font-mono">
                  {detailedReview.session_recording ? (
                    <div className="p-5 rounded-2xl bg-black/40 border border-slate/15 dark:border-rose/20 space-y-4">
                      <div className="flex justify-between items-center pb-2 border-b border-white/10">
                        <div className="flex items-center gap-2">
                          <Video className="w-4 h-4 text-oxblood dark:text-rose" />
                          <span className="font-bold text-xs uppercase tracking-wider text-charcoal dark:text-ivory">
                            Proctored Session Video
                          </span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          Cloudinary Archived
                        </span>
                      </div>

                      {/* Video Player */}
                      <div className="relative rounded-2xl overflow-hidden bg-black border border-white/10 shadow-2xl min-h-[220px] flex items-center justify-center">
                        {sessionVideoError ? (
                          <div className="p-8 text-center space-y-3 max-w-md">
                            <AlertCircle className="w-8 h-8 text-rose mx-auto" />
                            <p className="text-xs font-bold text-white">Video Stream Unavailable</p>
                            <p className="text-[11px] font-mono text-ivory/60">
                              The proctored session video could not be retrieved from Cloudinary CDN.
                            </p>
                            <a
                              href={detailedReview.session_recording.playback_url || detailedReview.session_recording.secure_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] font-mono text-rose underline block truncate"
                            >
                              {detailedReview.session_recording.playback_url || detailedReview.session_recording.secure_url}
                            </a>
                          </div>
                        ) : (
                          <video
                            src={detailedReview.session_recording.playback_url}
                            controls
                            playsInline
                            poster={detailedReview.session_recording.thumbnail_url}
                            className="w-full max-h-[460px] object-contain mx-auto"
                            onError={() => setSessionVideoError(true)}
                          />
                        )}
                      </div>

                      {/* Recording Metadata Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                          <span className="text-[9px] uppercase text-ivory/50 block">Duration</span>
                          <span className="font-bold text-ivory text-sm">
                            {detailedReview.session_recording.duration_seconds
                              ? `${Math.round(detailedReview.session_recording.duration_seconds)}s`
                              : 'Full Attempt'}
                          </span>
                        </div>
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                          <span className="text-[9px] uppercase text-ivory/50 block">File Size</span>
                          <span className="font-bold text-ivory text-sm">
                            {detailedReview.session_recording.file_size_bytes
                              ? `${(detailedReview.session_recording.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
                              : 'Standard'}
                          </span>
                        </div>
                        <div className="p-3 rounded-xl bg-white/5 border border-white/10 col-span-2">
                          <span className="text-[9px] uppercase text-ivory/50 block">Cloudinary Public ID</span>
                          <span className="font-mono text-[10px] text-ivory/80 truncate block" title={detailedReview.session_recording.public_id}>
                            {detailedReview.session_recording.public_id}
                          </span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-10 rounded-2xl bg-white/5 border border-white/10 text-center space-y-2">
                      <Video className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto" />
                      <p className="text-xs font-bold text-charcoal dark:text-ivory">No Session Video Recording Available</p>
                      <p className="text-[11px] text-slate/50 dark:text-ivory/50 max-w-md mx-auto font-sans">
                        The candidate either took the assessment without active camera authorization, or the recording upload was interrupted.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Recruiter Decision Action Bar */}
              <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3 pt-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase font-bold text-slate/50 dark:text-ivory/40">
                    Recruiter Hiring Determination & Stage Progression
                  </span>
                  {detailedReview.decision_email_status === 'FAILED' && (
                    <button
                      onClick={() => handleRetryEmail(detailedReview.assignment_id)}
                      className="px-3 py-1 rounded-lg bg-rose/20 hover:bg-rose/30 text-rose text-xs font-mono font-bold uppercase inline-flex items-center gap-1"
                    >
                      <RotateCcw size={12} /> Retry Decision Email
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <button
                    onClick={() => handlePromptDecision('ACCEPTED')}
                    className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-md shadow-emerald-900/30 min-h-[42px]"
                  >
                    <CheckCircle2 size={14} /> Accept
                  </button>

                  <button
                    onClick={() => handlePromptDecision('MOVED_TO_INTERVIEW')}
                    className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-md shadow-purple-900/30 min-h-[42px]"
                  >
                    <ArrowRight size={14} /> Move to Interview
                  </button>

                  <button
                    onClick={() => handlePromptDecision('ON_HOLD')}
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-md shadow-indigo-900/30 min-h-[42px]"
                  >
                    <Clock size={14} /> Hold for Review
                  </button>

                  <button
                    onClick={() => handlePromptDecision('REJECTED')}
                    className="px-4 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-md shadow-oxblood/30 min-h-[42px]"
                  >
                    <XCircle size={14} /> Reject
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 2: CONFIRM RECRUITER DECISION DIALOG */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showDecisionModal}
        onClose={() => setShowDecisionModal(false)}
        title={`Confirm Decision: ${decisionTarget ? decisionTarget.replace(/_/g, ' ') : ''}`}
        subtitle={`Candidate: ${detailedReview?.candidate_name} &bull; ${detailedReview?.candidate_email}`}
      >
        <div className="space-y-4 font-mono text-charcoal dark:text-ivory">
          {/* Email Notification Disclaimer Notice */}
          <div className={`p-4 rounded-xl border text-xs leading-relaxed font-sans ${
            decisionTarget === 'ON_HOLD'
              ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
              : 'bg-oxblood/10 border-rose/30 text-rose'
          }`}>
            <span className="font-mono uppercase font-bold block mb-0.5">
              {decisionTarget === 'ON_HOLD' ? 'Notification Notice:' : 'Automated Brevo Dispatch:'}
            </span>
            {decisionTarget === 'ON_HOLD'
              ? 'Marking as On-Hold keeps the candidate under review. No notification email is dispatched.'
              : `Upon confirmation, an official SkillSphere decision update will be securely dispatched to ${detailedReview?.candidate_email} via Brevo.`}
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
              Decision Reason {decisionTarget === 'REJECTED' ? <span className="text-rose">* (Mandatory for rejection)</span> : '(Optional)'}
            </label>
            <textarea
              rows={2}
              placeholder={decisionTarget === 'REJECTED' ? 'Required: specify reason for rejection...' : 'Reason for this decision...'}
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              required={decisionTarget === 'REJECTED'}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
              Candidate-Facing Message (Optional)
            </label>
            <textarea
              rows={2}
              placeholder="Custom note visible to the candidate on their dashboard and included in their decision email..."
              value={candidateMessage}
              onChange={(e) => setCandidateMessage(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
              Internal Recruiter Remarks (Private - Visible only to team)
            </label>
            <input
              type="text"
              placeholder="Internal recruiter evaluation note..."
              value={decisionRemarks}
              onChange={(e) => setDecisionRemarks(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood/50 min-h-[38px]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate/15 dark:border-white/10">
            <button
              type="button"
              onClick={() => setShowDecisionModal(false)}
              className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs font-mono uppercase font-bold tracking-wider min-h-[40px]"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleConfirmDecision}
              disabled={isSubmittingDecision}
              className="px-5 py-2 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-oxblood/20 min-h-[40px]"
            >
              {isSubmittingDecision ? <RefreshCw size={13} className="animate-spin" /> : <Check size={14} />}
              Confirm & Execute Decision
            </button>
          </div>
        </div>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 3: CANDIDATE COMPARISON & COHORT ANALYTICS */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        title="Candidate Cohort Comparison & Performance Analytics"
        subtitle={comparisonAssessmentTitle || 'Comparative Evaluation'}
      >
        <div className="space-y-6 max-h-[80vh] overflow-y-auto pr-1 text-charcoal dark:text-ivory font-mono">
          {comparisonLoading ? (
            <div className="py-16 text-center font-mono text-xs space-y-3">
              <RefreshCw className="w-8 h-8 text-oxblood animate-spin mx-auto" />
              <p>Calculating cohort percentiles, difficulty breakdowns, and leaderboard rankings...</p>
            </div>
          ) : comparisonData ? (
            <>
              {/* Cohort Overview Metrics */}
              {comparisonData.analytics && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-center">
                    <span className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Total Assigned</span>
                    <p className="text-xl font-bold mt-0.5 text-charcoal dark:text-ivory">
                      {comparisonData.analytics.total_assigned}
                    </p>
                    <span className="text-[9px] text-slate/40 dark:text-ivory/40">
                      {comparisonData.analytics.total_submitted} Submitted
                    </span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-center">
                    <span className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Average Score</span>
                    <p className="text-xl font-bold mt-0.5 text-oxblood dark:text-rose">
                      {comparisonData.analytics.average_score} <span className="text-xs font-normal">pts</span>
                    </p>
                    <span className="text-[9px] text-slate/40 dark:text-ivory/40">
                      {comparisonData.analytics.average_percentage}% avg accuracy
                    </span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-center">
                    <span className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Pending Review</span>
                    <p className="text-xl font-bold mt-0.5 text-amber-400">
                      {comparisonData.analytics.pending_reviews}
                    </p>
                    <span className="text-[9px] text-slate/40 dark:text-ivory/40">
                      {comparisonData.analytics.accepted_count} Accepted &bull; {comparisonData.analytics.rejected_count} Rejected
                    </span>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-center">
                    <span className="text-[9px] uppercase text-slate/40 dark:text-ivory/40">Average Time</span>
                    <p className="text-xl font-bold mt-0.5 text-charcoal dark:text-ivory">
                      {comparisonData.analytics.average_time_minutes} <span className="text-xs font-normal">mins</span>
                    </p>
                    <span className="text-[9px] text-slate/40 dark:text-ivory/40">
                      Passing Benchmark: {comparisonData.analytics.passing_marks}
                    </span>
                  </div>
                </div>
              )}

              {/* Score Distribution Breakdown */}
              {comparisonData.analytics?.score_distribution && (
                <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate/40 dark:text-ivory/40">
                    Cohort Score Distribution
                  </span>
                  <div className="grid grid-cols-4 gap-2 pt-1 text-center">
                    {Object.entries(comparisonData.analytics.score_distribution).map(([range, count]) => (
                      <div key={range} className="p-2 rounded-xl bg-white/5 border border-white/10">
                        <span className="text-[9px] text-slate/40 dark:text-ivory/40 block">{range}</span>
                        <span className="text-sm font-bold text-charcoal dark:text-ivory">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Leaderboard Table */}
              <div className="space-y-2">
                <span className="text-[10px] uppercase font-bold text-slate/40 dark:text-ivory/40">
                  Candidate Performance Ranking ({comparisonData.candidates?.length || 0})
                </span>

                <div className="overflow-x-auto rounded-2xl border border-slate/15 dark:border-rose/15">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate/5 dark:bg-white/5 border-b border-slate/10 dark:border-white/10 uppercase text-[9px] text-slate/50 dark:text-ivory/40">
                      <tr>
                        <th className="py-2.5 px-3">Rank</th>
                        <th className="py-2.5 px-3">Candidate</th>
                        <th className="py-2.5 px-3">Score & Accuracy</th>
                        <th className="py-2.5 px-3">Time</th>
                        <th className="py-2.5 px-3">Breakdown (C/I/U)</th>
                        <th className="py-2.5 px-3 text-center">Status</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate/10 dark:divide-white/5">
                      {comparisonData.candidates?.map((c, idx) => (
                        <tr key={c.assignment_id} className="hover:bg-white/5">
                          <td className="py-3 px-3 font-bold text-oxblood dark:text-rose">
                            #{idx + 1}
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-sans font-bold text-charcoal dark:text-ivory">
                              {c.candidate_name}
                            </div>
                            <div className="text-[10px] text-slate/40 dark:text-ivory/40">
                              {c.candidate_email}
                            </div>
                          </td>
                          <td className="py-3 px-3">
                            <span className="font-bold">{c.score_obtained}</span> / {c.total_marks} ({c.accuracy_percentage}%)
                          </td>
                          <td className="py-3 px-3">
                            {c.completion_time_seconds ? `${Math.round(c.completion_time_seconds / 60)}m` : 'N/A'}
                          </td>
                          <td className="py-3 px-3 text-[11px]">
                            {c.correct_count}C / {c.incorrect_count}I / {c.unanswered_count}U
                          </td>
                          <td className="py-3 px-3 text-center">
                            {renderReviewStatusBadge(c.review_status)}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => {
                                setShowComparisonModal(false);
                                handleOpenDetailedReview(c.assignment_id);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-oxblood text-ivory text-[10px] font-bold uppercase"
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </GlassModal>
    </div>
  );
};

// Simple internal icon helper for Save
const SaveIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
    <polyline points="17 21 17 13 7 13 7 21"></polyline>
    <polyline points="7 3 7 8 15 8"></polyline>
  </svg>
);

export default RecruiterReviewsTab;
