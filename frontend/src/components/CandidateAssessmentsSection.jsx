import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Award, Clock, CheckCircle, AlertTriangle, Play, HelpCircle,
  FileText, ShieldCheck, ArrowRight, XCircle, Info, Sparkles
} from 'lucide-react';
import { assessmentsAPI } from '../services/api';
import { GlassModal, useToast } from './MotionComponents';

export const CandidateAssessmentsSection = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Instructions Modal state
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [acknowledged, setAcknowledged] = useState(false);

  // Submission / Review Status Modal state
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusData, setStatusData] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const res = await assessmentsAPI.listCandidate();
      setAssignments(res.data || []);
    } catch (err) {
      console.error('Failed to load candidate assessments:', err);
      addToast('Failed to load assigned assessments.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, []);

  // Open Pre-Test Instructions Modal
  const handleOpenInstructions = (assignment) => {
    setSelectedAssignment(assignment);
    setAcknowledged(false);
    setShowInstructionsModal(true);
  };

  // Begin Test -> navigate to dedicated test page
  const handleBeginTest = () => {
    if (!acknowledged) {
      addToast('Please confirm you have read the test instructions.', 'error');
      return;
    }
    setShowInstructionsModal(false);
    navigate(`/assessment/${selectedAssignment.id}`);
  };

  // View Assessment Status Modal (Strictly Privacy-Preserved)
  const handleViewStatus = async (assignmentId) => {
    try {
      setStatusLoading(true);
      setShowStatusModal(true);
      const res = await assessmentsAPI.getResult(assignmentId);
      setStatusData(res.data);
    } catch (err) {
      console.error('Failed to load assessment status:', err);
      addToast('Failed to load submission status details.', 'error');
      setShowStatusModal(false);
    } finally {
      setStatusLoading(false);
    }
  };

  const pendingAssignments = assignments.filter((a) => a.status === 'ASSIGNED' || a.status === 'STARTED');

  // Status Badge Helper
  const renderStatusBadge = (asgn) => {
    const status = asgn.final_decision || asgn.review_status || asgn.status;
    const map = {
      ASSIGNED: 'bg-primary/20 text-primary border-primary/30',
      STARTED: 'bg-warning/20 text-warning border-warning/30 animate-pulse',
      SUBMITTED: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      PENDING_REVIEW: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      UNDER_REVIEW: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      ACCEPTED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      SHORTLISTED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      MOVED_TO_INTERVIEW: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      INTERVIEW: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      ON_HOLD: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
      REJECTED: 'bg-oxblood/30 text-rose border-rose/30',
      PASSED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      FAILED: 'bg-oxblood/30 text-rose border-rose/30',
      EXPIRED: 'bg-slate/30 text-slate-400 border-slate-500/30'
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

  return (
    <div className="space-y-6">
      {/* Shortlist Alert Banner */}
      {pendingAssignments.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 sm:p-6 rounded-3xl bg-oxblood/15 border border-oxblood/40 text-charcoal dark:text-ivory shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-oxblood text-ivory flex items-center justify-center shrink-0 shadow-md">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="font-display text-base font-bold text-oxblood dark:text-rose">
                You have been selected for the next round!
              </h3>
              <p className="text-xs font-mono text-slate/70 dark:text-ivory/70 mt-0.5">
                Please complete your First-Round MCQ Assessment within the allocated time limit.
              </p>
            </div>
          </div>

          <button
            onClick={() => handleOpenInstructions(pendingAssignments[0])}
            className="px-5 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory font-mono font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-oxblood/20 min-h-[44px] shrink-0"
          >
            Start Assessment <ArrowRight size={14} />
          </button>
        </motion.div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-2 border-b border-slate/15 dark:border-rose/15">
        <div>
          <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory">
            First-Round Technical Assessments
          </h2>
          <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 mt-1">
            Time-bound screening evaluations assigned by hiring teams for your shortlisted job applications.
          </p>
        </div>

        <span className="text-xs font-mono text-slate/50 dark:text-ivory/40">
          Total Assigned: <strong>{assignments.length}</strong>
        </span>
      </div>

      {/* Assessment Cards Grid */}
      {loading ? (
        <div className="min-h-[180px] flex items-center justify-center font-mono text-xs text-slate/60 dark:text-ivory/50">
          <div className="w-6 h-6 rounded-full border-2 border-oxblood/30 border-t-oxblood animate-spin mr-2" />
          Loading assessments...
        </div>
      ) : assignments.length === 0 ? (
        <div className="glass-card p-12 text-center rounded-3xl border border-dashed border-slate/20 dark:border-rose/20 space-y-3">
          <Award className="w-12 h-12 text-slate/40 dark:text-rose/40 mx-auto" />
          <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
            No Assessments Assigned Yet
          </h3>
          <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 max-w-md mx-auto">
            When a recruiter shortlists your application for a job, your time-bound first-round assessment will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {assignments.map((asgn) => {
            const isCompleted = asgn.is_completed || asgn.status === 'SUBMITTED' || asgn.status === 'PASSED' || asgn.status === 'FAILED';
            const isStarted = asgn.status === 'STARTED';

            return (
              <motion.div
                key={asgn.id}
                layout
                className="glass-card p-6 sm:p-7 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col justify-between space-y-6"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-mono uppercase text-slate/50 dark:text-ivory/40 font-bold truncate max-w-[200px]">
                      {asgn.job_title}
                    </span>
                    {renderStatusBadge(asgn)}
                  </div>

                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory leading-snug">
                    {asgn.assessment_title}
                  </h3>

                  {/* Metadata Specs Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-5 pt-4 border-t border-slate/10 dark:border-white/5 text-center">
                    <div className="p-2.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                      <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Questions</p>
                      <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory mt-0.5">
                        {asgn.question_count} MCQs
                      </p>
                    </div>

                    <div className="p-2.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                      <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Time Limit</p>
                      <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory mt-0.5">
                        {asgn.duration_minutes} Mins
                      </p>
                    </div>

                    <div className="p-2.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                      <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Total Marks</p>
                      <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory mt-0.5">
                        {asgn.total_marks}
                      </p>
                    </div>

                    <div className="p-2.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                      <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Passing Score</p>
                      <p className="text-sm font-bold font-mono text-oxblood dark:text-rose mt-0.5">
                        {asgn.passing_marks}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Card Footer Actions */}
                <div className="pt-4 border-t border-slate/10 dark:border-white/5 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate/50 dark:text-ivory/40">
                    Assigned: {new Date(asgn.assigned_at).toLocaleDateString()}
                  </span>

                  <div>
                    {isCompleted ? (
                      <button
                        onClick={() => handleViewStatus(asgn.id)}
                        className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs font-mono font-bold uppercase tracking-wider text-charcoal dark:text-ivory min-h-[44px] flex items-center gap-1.5"
                      >
                        <ShieldCheck size={14} className="text-emerald-400" /> View Status
                      </button>
                    ) : isStarted ? (
                      <button
                        onClick={() => navigate(`/assessment/${asgn.id}`)}
                        className="px-5 py-2 rounded-xl bg-warning hover:bg-warning/80 text-charcoal font-mono font-bold text-xs uppercase tracking-wider min-h-[44px] flex items-center gap-1.5 shadow-md shadow-warning/20"
                      >
                        <Play size={14} /> Resume Test
                      </button>
                    ) : (
                      <button
                        onClick={() => handleOpenInstructions(asgn)}
                        className="px-5 py-2 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory font-mono font-bold text-xs uppercase tracking-wider min-h-[44px] flex items-center gap-1.5 shadow-md shadow-oxblood/20"
                      >
                        <Play size={14} /> Start Assessment
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL 1: PRE-TEST INSTRUCTIONS */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showInstructionsModal}
        onClose={() => setShowInstructionsModal(false)}
        title="Assessment Instructions & Guidelines"
      >
        {selectedAssignment && (
          <div className="space-y-6 text-charcoal dark:text-ivory">
            <div>
              <span className="text-xs font-mono text-slate/50 dark:text-ivory/40 uppercase">
                {selectedAssignment.job_title}
              </span>
              <h3 className="text-xl font-display font-bold mt-0.5">
                {selectedAssignment.assessment_title}
              </h3>
            </div>

            {/* Crucial Instructions Banner */}
            <div className="p-4 rounded-2xl bg-oxblood/10 border border-oxblood/30 space-y-2">
              <div className="flex items-center gap-2 text-oxblood dark:text-rose font-mono font-bold text-xs uppercase tracking-wider">
                <AlertTriangle size={16} /> Strict Examination Rules
              </div>
              <ul className="text-xs font-mono text-charcoal/90 dark:text-ivory/90 space-y-1.5 pl-2 list-disc list-inside">
                <li><strong>Time-Bound Test:</strong> The countdown timer will start immediately when you click &ldquo;Begin Assessment Now&rdquo;.</li>
                <li><strong>Server-Controlled Clock:</strong> The timer is validated by the server and will not reset if you reload the page.</li>
                <li><strong>One Attempt Policy:</strong> The assessment can only be attempted once and cannot be retaken.</li>
                <li><strong>Auto-Submit:</strong> When the time reaches zero, your answers are automatically submitted and evaluated.</li>
                <li><strong>Single Answer:</strong> Each question contains exactly one correct option.</li>
                <li><strong>Stable Connection:</strong> Do not navigate away or close the test window while an attempt is active.</li>
              </ul>
            </div>

            {/* Test Specs Bar */}
            <div className="flex justify-between p-4 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 text-xs font-mono">
              <span><strong>Duration:</strong> {selectedAssignment.duration_minutes} Mins</span>
              <span><strong>Questions:</strong> {selectedAssignment.question_count} MCQs</span>
              <span><strong>Passing Marks:</strong> {selectedAssignment.passing_marks} / {selectedAssignment.total_marks}</span>
            </div>

            {/* Acknowledgment Checkbox */}
            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-slate/20 dark:border-white/10 bg-slate/5 dark:bg-white/5 cursor-pointer">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="w-4 h-4 text-oxblood rounded mt-0.5 cursor-pointer"
              />
              <span className="text-xs font-mono text-charcoal/90 dark:text-ivory/90 leading-tight">
                I understand that this assessment is strictly time-bound, can only be attempted once, and will auto-submit when the countdown expires.
              </span>
            </label>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-3 border-t border-slate/15 dark:border-white/10">
              <button
                type="button"
                onClick={() => setShowInstructionsModal(false)}
                className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase tracking-wider min-h-[44px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleBeginTest}
                disabled={!acknowledged}
                className="px-6 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 disabled:opacity-40 disabled:cursor-not-allowed text-ivory text-xs font-mono font-bold uppercase tracking-wider shadow-lg shadow-oxblood/20 min-h-[44px] flex items-center gap-1.5"
              >
                Begin Assessment Now <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 2: CANDIDATE SUBMISSION STATUS (STRICT PRIVACY) */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title="Assessment & Application Status"
      >
        {statusLoading ? (
          <div className="p-8 text-center font-mono text-xs">Loading submission status...</div>
        ) : statusData ? (
          <div className="space-y-6 text-charcoal dark:text-ivory text-center">
            <div className="flex justify-center">
              {statusData.final_decision === 'ACCEPTED' || statusData.final_decision === 'MOVED_TO_INTERVIEW' ? (
                <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/40 flex items-center justify-center">
                  <CheckCircle size={36} />
                </div>
              ) : statusData.final_decision === 'REJECTED' ? (
                <div className="w-16 h-16 rounded-full bg-oxblood/20 text-rose border-2 border-oxblood/40 flex items-center justify-center">
                  <XCircle size={36} />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-full bg-amber-500/20 text-amber-400 border-2 border-amber-500/40 flex items-center justify-center">
                  <Clock size={36} />
                </div>
              )}
            </div>

            <div>
              <span className="inline-block px-3 py-1 text-[11px] font-mono font-bold rounded-full uppercase tracking-wider mb-2 bg-oxblood/25 text-rose border border-rose/30">
                {statusData.review_status ? statusData.review_status.replace(/_/g, ' ') : 'UNDER REVIEW'}
              </span>
              <h3 className="text-xl font-display font-bold">{statusData.assessment_title}</h3>
              <p className="text-xs font-mono text-slate/50 dark:text-ivory/50 mt-1">
                Position: {statusData.job_title}
              </p>
            </div>

            {/* Submission Time Info */}
            <div className="p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 flex items-center justify-between text-xs font-mono">
              <span className="text-slate/50 dark:text-ivory/50 uppercase">Submission Recorded</span>
              <span className="font-semibold text-charcoal dark:text-ivory">
                {statusData.submitted_at ? new Date(statusData.submitted_at).toLocaleString() : 'Recorded'}
              </span>
            </div>

            {/* Status Message Box */}
            <div className="p-5 rounded-2xl bg-oxblood/10 border border-rose/25 text-left space-y-2">
              <p className="text-xs font-mono uppercase font-bold text-rose">
                {statusData.status_headline || 'Assessment Under Review'}
              </p>
              <p className="text-xs sm:text-sm font-sans text-charcoal/90 dark:text-ivory/85 leading-relaxed">
                {statusData.status_message}
              </p>
            </div>

            {/* Candidate-specific Note from Recruiter (if any) */}
            {statusData.candidate_message && (
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-left">
                <p className="text-[10px] font-mono uppercase text-slate/50 dark:text-ivory/50 font-bold mb-1">
                  Message from Recruitment Team:
                </p>
                <p className="text-xs font-sans text-charcoal dark:text-ivory italic">
                  "{statusData.candidate_message}"
                </p>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-slate/15 dark:border-white/10">
              <button
                onClick={() => setShowStatusModal(false)}
                className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs font-mono uppercase tracking-wider min-h-[44px]"
              >
                Close
              </button>
            </div>
          </div>
        ) : null}
      </GlassModal>
    </div>
  );
};

export default CandidateAssessmentsSection;
