import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3, AlertTriangle, CheckCircle2, XCircle, Clock, Award,
  Users, TrendingUp, HelpCircle, ArrowUpRight, ShieldCheck, RefreshCw
} from 'lucide-react';
import { questionBankAPI } from '../services/api';
import { GlassModal, AnimatedCounter } from './MotionComponents';

export const AssessmentAnalyticsModal = ({ isOpen, onClose, assessmentId, assessmentTitle }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    if (!assessmentId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await questionBankAPI.getAssessmentAnalytics(assessmentId);
      setAnalytics(res.data);
    } catch (err) {
      console.error('Failed to load assessment analytics:', err);
      setError(err.response?.data?.detail || 'Failed to retrieve assessment analytics telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && assessmentId) {
      fetchAnalytics();
    } else {
      setAnalytics(null);
    }
  }, [isOpen, assessmentId]);

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title="Assessment Performance Analytics"
      subtitle={assessmentTitle || 'First-Round MCQ Telemetry'}
    >
      <div className="space-y-6 text-charcoal dark:text-ivory max-h-[75vh] overflow-y-auto pr-1">
        {loading ? (
          <div className="py-16 text-center space-y-3 font-mono text-xs text-slate/60 dark:text-ivory/50">
            <RefreshCw className="w-7 h-7 text-oxblood animate-spin mx-auto" />
            <p>Aggregating candidate performance metrics & question accuracy telemetry...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-2xl bg-oxblood/10 border border-oxblood/20 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-rose mx-auto" />
            <p className="text-xs font-mono text-rose">{error}</p>
            <button
              onClick={fetchAnalytics}
              className="px-4 py-2 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase min-h-[38px]"
            >
              Retry
            </button>
          </div>
        ) : analytics ? (
          <>
            {/* Top Key Performance Indicators */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                <span className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40">Total Assigned</span>
                <div className="text-2xl font-black text-charcoal dark:text-ivory mt-1">
                  <AnimatedCounter value={analytics.total_assigned || 0} />
                </div>
                <span className="text-[10px] text-slate/40 dark:text-ivory/30">
                  {analytics.total_started || 0} In Progress
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                <span className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40">Completed</span>
                <div className="text-2xl font-black text-charcoal dark:text-ivory mt-1">
                  <AnimatedCounter value={analytics.total_completed || 0} />
                </div>
                <span className="text-[10px] text-slate/40 dark:text-ivory/30">
                  {analytics.total_assigned ? Math.round(((analytics.total_completed || 0) / analytics.total_assigned) * 100) : 0}% completion
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                <span className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40">Pass Rate</span>
                <div className={`text-2xl font-black mt-1 ${
                  analytics.pass_percentage >= 70 ? 'text-success' : analytics.pass_percentage >= 50 ? 'text-amber-500' : 'text-rose'
                }`}>
                  {analytics.pass_percentage}%
                </div>
                <span className="text-[10px] text-slate/40 dark:text-ivory/30">
                  {analytics.total_passed} Passed &bull; {analytics.total_failed} Failed
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                <span className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40">Average Score</span>
                <div className="text-2xl font-black text-oxblood dark:text-rose mt-1">
                  {analytics.average_marks}
                </div>
                <span className="text-[10px] text-slate/40 dark:text-ivory/30">Mean marks scored</span>
              </div>
            </div>

            {/* High Failure Rate Warning Banner (>= 60% Failure Rate) */}
            {analytics.high_failure_questions && analytics.high_failure_questions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-5 rounded-2xl bg-oxblood/15 border-2 border-rose/40 text-charcoal dark:text-ivory space-y-3"
              >
                <div className="flex items-center gap-2.5 text-oxblood dark:text-rose">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <h4 className="font-display font-bold text-sm tracking-wide">
                    High Failure Rate Alert ({analytics.high_failure_questions.length} Question{analytics.high_failure_questions.length > 1 ? 's' : ''} Flagged &ge; 60% Error Rate)
                  </h4>
                </div>
                <p className="text-xs font-sans text-slate/80 dark:text-ivory/70 leading-relaxed">
                  The following questions have a failure rate of 60% or higher among completed attempts. These questions may be overly ambiguous, misconfigured, or excessively difficult for this screening tier.
                </p>

                <div className="space-y-2 pt-1 font-mono text-xs">
                  {analytics.high_failure_questions.map((hf) => (
                    <div
                      key={hf.question_id}
                      className="p-3 rounded-xl bg-black/20 border border-rose/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                    >
                      <div className="space-y-0.5">
                        <span className="font-bold text-oxblood dark:text-rose">
                          Q{hf.order_num}: {hf.question_text}
                        </span>
                        <div className="flex items-center gap-2 text-[10px] text-slate/50 dark:text-ivory/40">
                          <span className="uppercase">{hf.difficulty}</span> &bull; 
                          <span>{hf.attempts_count} attempt(s)</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="px-2.5 py-1 rounded-full bg-rose/20 text-rose font-bold text-xs border border-rose/30">
                          {hf.failure_rate_percentage}% Failed
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-slate/10 text-slate/70 dark:text-ivory/70 text-xs">
                          {hf.correct_count} Correct
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Difficulty Breakdown */}
            {analytics.difficulty_performance && (
              <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3 font-mono">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate/70 dark:text-ivory/60 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-oxblood dark:text-rose" />
                  Accuracy by Difficulty Tier
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {['BEGINNER', 'INTERMEDIATE', 'ADVANCED'].map((tier) => {
                    const stats = analytics.difficulty_performance[tier] || { total: 0, correct: 0 };
                    const pct = stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0;
                    return (
                      <div key={tier} className="p-3.5 rounded-xl bg-white/5 border border-slate/10 dark:border-white/5 space-y-1.5">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-bold uppercase text-[11px]">{tier}</span>
                          <span className="font-bold text-oxblood dark:text-rose">{pct}%</span>
                        </div>
                        <div className="w-full bg-black/20 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-oxblood h-full rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-slate/50 dark:text-ivory/40">
                          {stats.correct} / {stats.total} correct responses
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Question-by-Question Accuracy Telemetry */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-ivory/60">
                  Question-by-Question Accuracy Breakdown ({analytics.questions_analytics?.length || 0})
                </h4>
              </div>

              {analytics.questions_analytics && analytics.questions_analytics.length > 0 ? (
                <div className="overflow-x-auto rounded-2xl border border-slate/15 dark:border-rose/15 font-mono text-xs">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate/5 dark:bg-white/5 border-b border-slate/15 dark:border-rose/15 text-[10px] uppercase text-slate/60 dark:text-ivory/50 tracking-wider">
                        <th className="py-3 px-3">#</th>
                        <th className="py-3 px-4">Question Prompt</th>
                        <th className="py-3 px-3">Difficulty</th>
                        <th className="py-3 px-3 text-center">Marks</th>
                        <th className="py-3 px-3 text-center">Attempts</th>
                        <th className="py-3 px-3 text-center">Correct</th>
                        <th className="py-3 px-3 text-right">Accuracy Rate</th>
                        <th className="py-3 px-3 text-right">Failure Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate/10 dark:divide-rose/10">
                      {analytics.questions_analytics.map((q) => {
                        const isHighFailure = q.attempts_count >= 1 && q.failure_rate_percentage >= 60.0;
                        return (
                          <tr
                            key={q.question_id}
                            className={`transition-colors ${
                              isHighFailure ? 'bg-oxblood/10 hover:bg-oxblood/15' : 'hover:bg-white/5'
                            }`}
                          >
                            <td className="py-3 px-3 font-bold text-slate/50">Q{q.order_num}</td>
                            <td className="py-3 px-4 font-sans text-xs font-medium max-w-xs truncate text-charcoal dark:text-ivory">
                              {q.question_text}
                            </td>
                            <td className="py-3 px-3">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                q.difficulty === 'BEGINNER' ? 'badge-selected' : q.difficulty === 'ADVANCED' ? 'badge-oxblood' : 'badge-slate'
                              }`}>
                                {q.difficulty}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center font-bold text-oxblood dark:text-rose">
                              {q.marks}
                            </td>
                            <td className="py-3 px-3 text-center text-slate/70 dark:text-ivory/70">
                              {q.attempts_count}
                            </td>
                            <td className="py-3 px-3 text-center text-emerald-600 dark:text-emerald-400 font-bold">
                              {q.correct_count}
                            </td>
                            <td className="py-3 px-3 text-right font-bold text-emerald-600 dark:text-emerald-400">
                              {q.correct_rate_percentage}%
                            </td>
                            <td className="py-3 px-3 text-right">
                              <span className={`font-bold ${
                                isHighFailure ? 'text-rose font-black flex items-center justify-end gap-1' : 'text-slate/60 dark:text-ivory/60'
                              }`}>
                                {isHighFailure && <AlertTriangle className="w-3.5 h-3.5 text-rose shrink-0" />}
                                {q.failure_rate_percentage}%
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center rounded-2xl bg-slate/5 dark:bg-white/5 border border-dashed border-slate/15 dark:border-rose/15 font-mono text-xs text-slate/50">
                  No questions found for this assessment.
                </div>
              )}
            </div>
          </>
        ) : null}

        <div className="flex justify-end pt-3 border-t border-slate/15 dark:border-white/10 font-mono">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs uppercase tracking-wider font-bold min-h-[44px]"
          >
            Close Telemetry
          </button>
        </div>
      </div>
    </GlassModal>
  );
};
