import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Video, Plus, Users, Play, Clock, CheckCircle2, AlertTriangle,
  RotateCcw, Eye, X, Check, Award, ChevronRight, FileText, Send
} from 'lucide-react';
import { videoAssessmentsAPI, recruiterAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const RecruiterVideoAssessmentsTab = ({ jobs = [] }) => {
  const { addToast } = useToast();

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(false);

  // Builder Modal
  const [showBuilderModal, setShowBuilderModal] = useState(false);
  const [jobId, setJobId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');
  const [questions, setQuestions] = useState([
    {
      order_num: 1,
      question_text: 'Introduce yourself and walk us through your most impactful recent project.',
      question_instructions: 'Highlight your architectural decisions and personal contribution.',
      max_duration_seconds: 120,
      prep_time_seconds: 30,
      retake_limit: 2,
      is_required: true
    }
  ]);
  const [savingAssessment, setSavingAssessment] = useState(false);

  // Assign Modal
  const [assigningAssessment, setAssigningAssessment] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedAppIds, setSelectedAppIds] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [assigning, setAssigning] = useState(false);

  // Review Submissions Modal
  const [reviewAssessment, setReviewAssessment] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [loadingAssignments, setLoadingAssignments] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalScore, setEvalScore] = useState(85);
  const [evalDecision, setEvalDecision] = useState('ACCEPTED');
  const [evalFeedback, setEvalFeedback] = useState('');

  const fetchAssessments = async () => {
    setLoading(true);
    try {
      const res = await videoAssessmentsAPI.list();
      setAssessments(res.data);
    } catch (err) {
      addToast({
        title: "Load Error",
        message: err.response?.data?.detail || "Failed to load video assessments.",
        type: "error"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  // Add question to builder
  const handleAddQuestion = () => {
    setQuestions([
      ...questions,
      {
        order_num: questions.length + 1,
        question_text: '',
        question_instructions: '',
        max_duration_seconds: 120,
        prep_time_seconds: 30,
        retake_limit: 2,
        is_required: true
      }
    ]);
  };

  const handleRemoveQuestion = (idx) => {
    if (questions.length === 1) return;
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  // Submit Video Assessment Creation
  const handleCreateAssessment = async (statusToSet = 'PUBLISHED') => {
    if (!jobId || !title.trim()) {
      addToast({ title: "Validation Error", message: "Job and Title are required.", type: "error" });
      return;
    }

    setSavingAssessment(true);
    try {
      await videoAssessmentsAPI.create({
        job_id: jobId,
        title,
        description,
        instructions,
        status: statusToSet,
        questions
      });

      addToast({
        title: statusToSet === 'PUBLISHED' ? "Video Assessment Published" : "Draft Saved",
        message: statusToSet === 'PUBLISHED'
          ? "Video assessment is published and ready for candidate assignment."
          : "Video assessment saved as draft.",
        type: "success"
      });

      setShowBuilderModal(false);
      setTitle('');
      setDescription('');
      setInstructions('');
      fetchAssessments();
    } catch (err) {
      addToast({
        title: "Creation Failed",
        message: err.response?.data?.detail || "Could not save video assessment.",
        type: "error"
      });
    } finally {
      setSavingAssessment(false);
    }
  };

  const handlePublishAssessment = async (assessmentId) => {
    try {
      await videoAssessmentsAPI.publish(assessmentId);
      addToast({
        title: "Published Successfully",
        message: "Video assessment is now published and can be assigned to candidates.",
        type: "success"
      });
      fetchAssessments();
    } catch (err) {
      addToast({
        title: "Publish Failed",
        message: err.response?.data?.detail || "Could not publish video assessment.",
        type: "error"
      });
    }
  };

  // Open Assign Modal
  const handleOpenAssignModal = async (va) => {
    if (va.status !== 'PUBLISHED') {
      addToast({
        title: "Draft Assessment",
        message: "Please publish this video assessment before assigning it to candidates.",
        type: "error"
      });
      return;
    }
    setAssigningAssessment(va);
    setLoadingCandidates(true);
    setSelectedAppIds([]);
    try {
      const res = await recruiterAPI.getApplicants({ job_id: va.job_id });
      setCandidates(res.data || []);
    } catch (err) {
      addToast({
        title: "Candidates Error",
        message: "Could not load applicants for this job.",
        type: "error"
      });
    } finally {
      setLoadingCandidates(false);
    }
  };

  const handleAssignSubmit = async () => {
    if (selectedAppIds.length === 0) return;
    setAssigning(true);
    try {
      await videoAssessmentsAPI.assign(assigningAssessment.id, selectedAppIds);
      addToast({
        title: "Assessment Assigned",
        message: `Assigned to ${selectedAppIds.length} candidate(s). Notifications sent.`,
        type: "success"
      });
      setAssigningAssessment(null);
    } catch (err) {
      addToast({
        title: "Assignment Error",
        message: err.response?.data?.detail || "Failed to assign assessment.",
        type: "error"
      });
    } finally {
      setAssigning(false);
    }
  };

  // Open Review Submissions Modal
  const handleOpenReview = async (va) => {
    setReviewAssessment(va);
    setLoadingAssignments(true);
    setSelectedSubmission(null);
    try {
      const res = await videoAssessmentsAPI.getAssignments(va.id);
      setAssignments(res.data);
    } catch (err) {
      addToast({
        title: "Submissions Error",
        message: "Could not retrieve candidate submissions.",
        type: "error"
      });
    } finally {
      setLoadingAssignments(false);
    }
  };

  // View Candidate Submission Details
  const handleSelectSubmission = async (assignmentId) => {
    try {
      const res = await videoAssessmentsAPI.getReviewDetails(assignmentId);
      setSelectedSubmission(res.data);
    } catch (err) {
      addToast({
        title: "Submission Details Error",
        message: "Could not load candidate responses.",
        type: "error"
      });
    }
  };

  // Grade Candidate Submission
  const handleEvaluateSubmission = async (e) => {
    e.preventDefault();
    if (!selectedSubmission) return;
    setEvaluating(true);
    try {
      await videoAssessmentsAPI.evaluate(selectedSubmission.id, {
        review_status: evalDecision,
        overall_score: parseFloat(evalScore),
        recruiter_feedback: evalFeedback
      });
      addToast({
        title: "Evaluation Saved",
        message: `Candidate submission marked as ${evalDecision}.`,
        type: "success"
      });
      handleOpenReview(reviewAssessment);
      setSelectedSubmission(null);
    } catch (err) {
      addToast({
        title: "Evaluation Failed",
        message: err.response?.data?.detail || "Could not save evaluation.",
        type: "error"
      });
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Top Section */}
      <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory flex items-center gap-2.5">
            <Video className="w-6 h-6 text-oxblood dark:text-rose" />
            <span>Asynchronous Video Assessments</span>
          </h2>
          <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono mt-1">
            Standardized video interview screening &bull; Live recordings stored securely in Cloudinary &bull; Private recruiter evaluation
          </p>
        </div>

        <button
          onClick={() => setShowBuilderModal(true)}
          className="btn-oxblood px-4 py-2 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 shadow-lg"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Video Assessment</span>
        </button>
      </div>

      {/* 2. Assessment Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((n) => <div key={n} className="h-44 glass-card rounded-2xl animate-pulse" />)}
        </div>
      ) : assessments.length === 0 ? (
        <div className="text-center py-16 rounded-3xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
          <Video className="w-12 h-12 text-slate/30 dark:text-ivory/30 mx-auto mb-3" />
          <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory">No Video Assessments Created</h3>
          <p className="text-xs text-slate/60 dark:text-ivory/60 font-mono mt-1 max-w-sm mx-auto">
            Design structured video interview questions with timed answers and assign them to shortlisted applicants.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {assessments.map((va) => (
            <div
              key={va.id}
              className="glass-card p-6 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-md flex flex-col justify-between space-y-4 hover:border-oxblood/40 transition"
            >
              <div>
                <div className="flex justify-between items-start gap-2">
                  <div className="flex items-center gap-2">
                    <span className="badge-selected font-mono text-[10px] px-2.5 py-0.5 rounded-full uppercase">
                      {va.job_title || 'Active Role'}
                    </span>
                    <span className={`font-mono text-[10px] px-2.5 py-0.5 rounded-full uppercase font-bold border ${
                      va.status === 'PUBLISHED'
                        ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                        : 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                    }`}>
                      {va.status || 'DRAFT'}
                    </span>
                  </div>
                  <span className="badge-slate font-mono text-[10px] px-2 py-0.5 rounded">
                    {va.total_questions} Video Prompts
                  </span>
                </div>

                <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory mt-2">
                  {va.title}
                </h3>
                {va.description && (
                  <p className="text-xs text-slate/70 dark:text-ivory/70 line-clamp-2 mt-1">
                    {va.description}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-slate/10 dark:border-rose/10 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {va.status === 'DRAFT' && (
                    <button
                      onClick={() => handlePublishAssessment(va.id)}
                      className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-semibold flex items-center gap-1.5 transition shadow"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Publish</span>
                    </button>
                  )}

                  <button
                    onClick={() => handleOpenAssignModal(va)}
                    disabled={va.status !== 'PUBLISHED'}
                    title={va.status !== 'PUBLISHED' ? 'Publish assessment before assigning to candidates' : 'Assign to shortlisted candidates'}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-mono font-semibold flex items-center gap-1.5 transition ${
                      va.status === 'PUBLISHED'
                        ? 'border-oxblood/30 text-oxblood dark:text-rose hover:bg-oxblood/10'
                        : 'border-slate/20 text-slate/40 cursor-not-allowed opacity-60'
                    }`}
                  >
                    <Users className="w-3.5 h-3.5" />
                    <span>Assign</span>
                  </button>
                </div>

                <button
                  onClick={() => handleOpenReview(va)}
                  className="btn-oxblood px-4 py-1.5 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 shadow"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Submissions</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ==================================================================== */}
      {/* VIDEO ASSESSMENT BUILDER MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showBuilderModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-2xl w-full p-6 sm:p-8 rounded-3xl border border-oxblood/40 space-y-5 bg-[#141820] text-ivory max-h-[90vh] overflow-y-auto shadow-2xl"
            >
              <div className="flex justify-between items-center pb-3 border-b border-ivory/10">
                <h3 className="font-display font-bold text-lg text-white flex items-center gap-2">
                  <Video className="w-5 h-5 text-oxblood dark:text-rose" />
                  <span>Configure Video Assessment</span>
                </h3>
                <button
                  onClick={() => setShowBuilderModal(false)}
                  className="p-1 rounded-lg text-ivory/60 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); handleCreateAssessment('PUBLISHED'); }} className="space-y-4 text-xs font-sans">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="font-mono text-ivory/80 block mb-1">Target Job Position *</label>
                    <select
                      value={jobId}
                      onChange={(e) => setJobId(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black/40 border border-ivory/15 font-mono text-xs text-ivory outline-none focus:border-oxblood"
                      required
                    >
                      <option value="">Select Job Opening</option>
                      {jobs.map((j) => (
                        <option key={j.id} value={j.id}>{j.title}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="font-mono text-ivory/80 block mb-1">Assessment Title *</label>
                    <input
                      type="text"
                      placeholder="e.g. Senior Backend Video Screen"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-black/40 border border-ivory/15 text-xs text-ivory outline-none focus:border-oxblood"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="font-mono text-ivory/80 block mb-1">Instructions for Candidates</label>
                  <textarea
                    rows={2}
                    placeholder="Instructions, guidelines, expectations..."
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 border border-ivory/15 text-xs text-ivory outline-none focus:border-oxblood resize-none"
                  />
                </div>

                {/* Question Prompts Section */}
                <div className="space-y-3 pt-2">
                  <div className="flex justify-between items-center">
                    <h4 className="font-mono text-xs font-bold text-oxblood dark:text-rose uppercase">
                      Video Question Prompts ({questions.length})
                    </h4>
                    <button
                      type="button"
                      onClick={handleAddQuestion}
                      className="text-xs font-mono font-bold text-white hover:text-oxblood flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Question</span>
                    </button>
                  </div>

                  {questions.map((q, idx) => (
                    <div key={idx} className="p-4 rounded-2xl bg-black/40 border border-ivory/10 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-[10px] text-ivory/60 uppercase font-bold">
                          Question #{idx + 1}
                        </span>
                        {questions.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveQuestion(idx)}
                            className="text-red-400 hover:text-red-300 text-xs font-mono"
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      <input
                        type="text"
                        placeholder="Video prompt text (e.g. Describe your experience with microservices)..."
                        value={q.question_text}
                        onChange={(e) => {
                          const updated = [...questions];
                          updated[idx].question_text = e.target.value;
                          setQuestions(updated);
                        }}
                        className="w-full px-3 py-2 rounded-xl bg-black/30 border border-ivory/15 text-xs text-ivory outline-none focus:border-oxblood"
                        required
                      />

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="font-mono text-[10px] text-ivory/60 block mb-0.5">Max Duration (s)</label>
                          <input
                            type="number"
                            min="30"
                            max="300"
                            value={q.max_duration_seconds}
                            onChange={(e) => {
                              const updated = [...questions];
                              updated[idx].max_duration_seconds = parseInt(e.target.value) || 120;
                              setQuestions(updated);
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-ivory/15 text-xs font-mono text-ivory"
                          />
                        </div>

                        <div>
                          <label className="font-mono text-[10px] text-ivory/60 block mb-0.5">Prep Time (s)</label>
                          <input
                            type="number"
                            min="10"
                            max="60"
                            value={q.prep_time_seconds}
                            onChange={(e) => {
                              const updated = [...questions];
                              updated[idx].prep_time_seconds = parseInt(e.target.value) || 30;
                              setQuestions(updated);
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-ivory/15 text-xs font-mono text-ivory"
                          />
                        </div>

                        <div>
                          <label className="font-mono text-[10px] text-ivory/60 block mb-0.5">Retake Limit</label>
                          <input
                            type="number"
                            min="0"
                            max="3"
                            value={q.retake_limit}
                            onChange={(e) => {
                              const updated = [...questions];
                              updated[idx].retake_limit = parseInt(e.target.value) || 0;
                              setQuestions(updated);
                            }}
                            className="w-full px-2 py-1.5 rounded-lg bg-black/30 border border-ivory/15 text-xs font-mono text-ivory"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-3 mt-4">
                  <button
                    type="button"
                    disabled={savingAssessment}
                    onClick={() => handleCreateAssessment('DRAFT')}
                    className="py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 border border-ivory/20 text-ivory hover:bg-white/5 transition"
                  >
                    <FileText className="w-4 h-4 text-ivory/60" />
                    <span>Save as Draft</span>
                  </button>

                  <button
                    type="submit"
                    disabled={savingAssessment}
                    className="btn-oxblood py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 shadow-lg"
                  >
                    <Check className="w-4 h-4" />
                    <span>{savingAssessment ? "Saving..." : "Publish Assessment"}</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* CANDIDATE ASSIGNMENT MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {assigningAssessment && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-lg w-full p-6 rounded-3xl border border-oxblood/40 space-y-4 bg-[#141820] text-ivory"
            >
              <div className="flex justify-between items-center pb-2 border-b border-ivory/10">
                <div>
                  <h3 className="font-display font-bold text-base text-white">
                    Assign Assessment
                  </h3>
                  <p className="text-xs font-mono text-ivory/60">{assigningAssessment.title}</p>
                </div>
                <button
                  onClick={() => setAssigningAssessment(null)}
                  className="p-1 rounded-lg text-ivory/60 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {loadingCandidates ? (
                <div className="py-8 text-center text-xs font-mono text-ivory/50">Loading candidates...</div>
              ) : candidates.length === 0 ? (
                <div className="py-8 text-center text-xs font-mono text-ivory/50">
                  No applicants found for this job opening.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {candidates.map((cand) => {
                    const isSelected = selectedAppIds.includes(cand.id);
                    return (
                      <div
                        key={cand.id}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedAppIds(selectedAppIds.filter(id => id !== cand.id));
                          } else {
                            setSelectedAppIds([...selectedAppIds, cand.id]);
                          }
                        }}
                        className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                          isSelected
                            ? 'bg-oxblood/20 border-oxblood text-white'
                            : 'bg-black/40 border-ivory/10 text-ivory/80 hover:border-ivory/30'
                        }`}
                      >
                        <div>
                          <p className="font-display font-bold text-xs">{cand.candidate_name || 'Applicant'}</p>
                          <p className="font-mono text-[10px] text-ivory/50">{cand.status} &bull; {cand.candidate_email}</p>
                        </div>
                        <div className={`w-5 h-5 rounded-md border flex items-center justify-center ${
                          isSelected ? 'bg-oxblood border-oxblood text-white' : 'border-ivory/20'
                        }`}>
                          {isSelected && <Check className="w-3.5 h-3.5" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setAssigningAssessment(null)}
                  className="flex-1 py-2.5 rounded-xl border border-ivory/20 font-mono text-xs text-ivory"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAssignSubmit}
                  disabled={assigning || selectedAppIds.length === 0}
                  className="flex-1 btn-oxblood py-2.5 rounded-xl font-display font-semibold text-xs flex items-center justify-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{assigning ? "Assigning..." : `Assign (${selectedAppIds.length})`}</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* SUBMISSIONS & EVALUATION MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {reviewAssessment && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-4xl w-full p-6 sm:p-8 rounded-3xl border border-oxblood/40 space-y-6 bg-[#141820] text-ivory max-h-[90vh] overflow-y-auto shadow-2xl"
            >
              <div className="flex justify-between items-center pb-3 border-b border-ivory/10">
                <div>
                  <h3 className="font-display font-bold text-lg text-white">
                    {reviewAssessment.title} &bull; Candidate Submissions
                  </h3>
                  <p className="text-xs font-mono text-ivory/60">
                    Private recruiter review and grading
                  </p>
                </div>
                <button
                  onClick={() => {
                    setReviewAssessment(null);
                    setSelectedSubmission(null);
                  }}
                  className="p-1 rounded-lg text-ivory/60 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Two Column Layout: Submissions List & Video Review */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Column 1: Candidates List */}
                <div className="space-y-3">
                  <h4 className="font-mono text-xs font-bold text-ivory/80 uppercase">
                    Submissions ({assignments.length})
                  </h4>
                  {loadingAssignments ? (
                    <div className="py-8 text-center text-xs font-mono text-ivory/50">Loading...</div>
                  ) : assignments.length === 0 ? (
                    <div className="py-8 text-center text-xs font-mono text-ivory/50">No candidate submissions yet.</div>
                  ) : (
                    <div className="space-y-2">
                      {assignments.map((a) => (
                        <div
                          key={a.id}
                          onClick={() => handleSelectSubmission(a.id)}
                          className={`p-3 rounded-2xl border cursor-pointer transition ${
                            selectedSubmission?.id === a.id
                              ? 'bg-oxblood/20 border-oxblood text-white'
                              : 'bg-black/40 border-ivory/10 text-ivory/80 hover:border-ivory/30'
                          }`}
                        >
                          <p className="font-display font-bold text-xs">Submission #{a.id.slice(0, 8)}</p>
                          <div className="flex items-center justify-between text-[10px] font-mono mt-1">
                            <span className={a.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}>
                              {a.status}
                            </span>
                            <span className="badge-slate px-1.5 py-0.5 rounded uppercase">
                              {a.review_status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Columns 2 & 3: Detailed Response Player & Grading */}
                <div className="md:col-span-2 space-y-4">
                  {selectedSubmission ? (
                    <>
                      <h4 className="font-mono text-xs font-bold text-oxblood dark:text-rose uppercase">
                        Recorded Video Responses
                      </h4>

                      <div className="space-y-4">
                        {selectedSubmission.responses.map((resp, idx) => (
                          <div key={resp.id} className="p-4 rounded-2xl bg-black/40 border border-ivory/10 space-y-3">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="font-mono text-[10px] text-oxblood dark:text-rose font-bold uppercase">
                                  Prompt #{idx + 1}
                                </span>
                                <h5 className="font-display font-bold text-xs text-white">
                                  {resp.question_text}
                                </h5>
                              </div>
                              <span className="font-mono text-[10px] text-ivory/60">
                                {Math.round(resp.duration_seconds)}s
                              </span>
                            </div>

                            {resp.playback_url ? (
                              <div className="rounded-xl overflow-hidden aspect-video bg-black border border-ivory/15 relative flex items-center justify-center">
                                <video
                                  src={resp.playback_url}
                                  controls
                                  className="w-full h-full object-contain"
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                    if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
                                  }}
                                />
                                <div className="hidden flex-col items-center justify-center p-6 text-center space-y-2">
                                  <Video className="w-8 h-8 text-rose" />
                                  <span className="font-mono text-xs text-white">Video stream not reachable</span>
                                  <a
                                    href={resp.playback_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="font-mono text-[10px] text-rose underline truncate max-w-xs"
                                  >
                                    Open direct URL
                                  </a>
                                </div>
                              </div>
                            ) : (
                              <div className="p-4 rounded-xl bg-black/50 text-center text-xs font-mono text-ivory/50">
                                Video URL unavailable
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      {/* Evaluation Form */}
                      <form onSubmit={handleEvaluateSubmission} className="p-5 rounded-2xl bg-black/50 border border-ivory/15 space-y-3">
                        <h5 className="font-display font-bold text-sm text-white">Evaluation Decision</h5>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="font-mono text-[10px] text-ivory/70 block mb-1">Decision</label>
                            <select
                              value={evalDecision}
                              onChange={(e) => setEvalDecision(e.target.value)}
                              className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-ivory/15 font-mono text-xs text-ivory outline-none focus:border-oxblood"
                            >
                              <option value="ACCEPTED">ACCEPTED (Advance)</option>
                              <option value="UNDER_REVIEW">UNDER REVIEW</option>
                              <option value="REJECTED">REJECTED</option>
                            </select>
                          </div>

                          <div>
                            <label className="font-mono text-[10px] text-ivory/70 block mb-1">Score (0 - 100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={evalScore}
                              onChange={(e) => setEvalScore(e.target.value)}
                              className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-ivory/15 font-mono text-xs text-ivory"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="font-mono text-[10px] text-ivory/70 block mb-1">Recruiter Feedback</label>
                          <textarea
                            rows={2}
                            placeholder="Private evaluation feedback..."
                            value={evalFeedback}
                            onChange={(e) => setEvalFeedback(e.target.value)}
                            className="w-full px-3 py-1.5 rounded-xl bg-black/40 border border-ivory/15 text-xs text-ivory resize-none"
                          />
                        </div>

                        <button
                          type="submit"
                          disabled={evaluating}
                          className="btn-oxblood w-full py-2.5 rounded-xl font-display font-semibold text-xs flex items-center justify-center gap-1.5"
                        >
                          <Award className="w-4 h-4" />
                          <span>{evaluating ? "Saving Decision..." : "Submit Candidate Evaluation"}</span>
                        </button>
                      </form>
                    </>
                  ) : (
                    <div className="py-20 text-center text-xs font-mono text-ivory/40">
                      Select a candidate submission on the left to review their recorded responses.
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
