import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Plus, CheckCircle2, Clock, Award, Users, Filter,
  Eye, Edit3, Send, Check, X, AlertCircle, AlertTriangle, ChevronDown, HelpCircle,
  Search, ShieldCheck, ArrowRight, UserCheck, RefreshCw, Layers,
  BarChart3, Sparkles, Shuffle, Database, Sliders, Briefcase, Upload
} from 'lucide-react';
import { assessmentsAPI, questionBankAPI, recruiterAPI } from '../services/api';
import { GlassModal, useToast, AnimatedCounter } from './MotionComponents';
import { AssessmentAnalyticsModal } from './AssessmentAnalyticsModal';
import { RecruiterQuestionBankTab } from './RecruiterQuestionBankTab';
import { InlineQuestionUploadModal } from './InlineQuestionUploadModal';
import { RecruiterReviewsTab } from './RecruiterReviewsTab';

export const RecruiterAssessmentsSection = ({ jobs = [] }) => {
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL-driven Sub-Navigation: 'assessments' | 'question_bank' | 'reviews'
  const subtabParam = searchParams.get('subtab');
  const activeSectionTab = subtabParam === 'question_bank'
    ? 'question_bank'
    : subtabParam === 'reviews'
    ? 'reviews'
    : 'assessments';

  const setSectionTab = (tabName) => {
    const next = new URLSearchParams(searchParams);
    if (tabName === 'question_bank') {
      next.set('subtab', 'question_bank');
    } else if (tabName === 'reviews') {
      next.set('subtab', 'reviews');
    } else {
      next.delete('subtab');
    }
    setSearchParams(next);
  };

  // Local state for recruiter jobs (fallback if parent hasn't loaded yet)
  const [internalJobs, setInternalJobs] = useState(jobs || []);

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAssessmentId, setEditingAssessmentId] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Shortlist Assignment Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [currentAssignAssessment, setCurrentAssignAssessment] = useState(null);
  const [shortlistedCandidates, setShortlistedCandidates] = useState([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);
  const [isAssigning, setIsAssigning] = useState(false);

  // Results Dashboard Modal
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [resultsAssessment, setResultsAssessment] = useState(null);
  const [candidateResults, setCandidateResults] = useState([]);
  const [resultFilter, setResultFilter] = useState('all');
  const [resultsLoading, setResultsLoading] = useState(false);

  // Detailed Candidate Answers Review Modal
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewData, setReviewData] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  // Analytics Telemetry Modal
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [analyticsAssessment, setAnalyticsAssessment] = useState(null);

  // Auto-Generate Assessment Modal
  const [showAutoGenerateModal, setShowAutoGenerateModal] = useState(false);
  const [autoGenForm, setAutoGenForm] = useState({
    job_id: '',
    title: '',
    instructions: 'Answer all multiple-choice questions within the allocated time. Each question has exactly one correct answer.',
    technology: 'Python',
    topic: '',
    total_questions: 5,
    duration_minutes: 30,
    passing_marks: 3,
    marks_per_question: 1,
    uniform_marks_enabled: true,
    randomize_questions: true,
    randomize_options: true,
    beginner_pct: 40,
    intermediate_pct: 40,
    advanced_pct: 20
  });
  const [autoGenLoading, setAutoGenLoading] = useState(false);
  const [techMetadata, setTechMetadata] = useState({ technologies: [], topics_by_technology: {} });
  const [availability, setAvailability] = useState(null);
  const [loadingAvailability, setLoadingAvailability] = useState(false);

  // Fetch question availability when technology or topic changes
  useEffect(() => {
    if (showAutoGenerateModal && autoGenForm.technology) {
      setLoadingAvailability(true);
      questionBankAPI.checkAvailability(autoGenForm.technology, autoGenForm.topic || null)
        .then((res) => {
          setAvailability(res.data);
        })
        .catch((err) => {
          console.error('Failed to check availability:', err);
        })
        .finally(() => {
          setLoadingAvailability(false);
        });
    }
  }, [showAutoGenerateModal, autoGenForm.technology, autoGenForm.topic]);

  // Add from Question Bank Modal (inside manual builder)
  const [showAddFromBankModal, setShowAddFromBankModal] = useState(false);
  const [bankQuestions, setBankQuestions] = useState([]);
  const [loadingBankQuestions, setLoadingBankQuestions] = useState(false);
  const [bankSearch, setBankSearch] = useState('');
  const [bankTech, setBankTech] = useState('');
  const [bankDifficulty, setBankDifficulty] = useState('');
  const [selectedBankQuestions, setSelectedBankQuestions] = useState([]);

  // Inline Question Upload Modal State
  const [showUploadFileModal, setShowUploadFileModal] = useState(false);
  const [uploadModalContext, setUploadModalContext] = useState('auto_generate'); // 'auto_generate' | 'manual_builder'
  const [bankPickerContext, setBankPickerContext] = useState('manual_builder'); // 'manual_builder' | 'auto_generate'

  const handleUploadSuccess = async (importResult) => {
    // 1. Refresh availability for autoGenForm while preserving all existing form state
    if (autoGenForm.technology) {
      setLoadingAvailability(true);
      try {
        const res = await questionBankAPI.checkAvailability(
          autoGenForm.technology,
          autoGenForm.topic || null
        );
        setAvailability(res.data);
      } catch (err) {
        console.error('Failed to refresh question availability:', err);
      } finally {
        setLoadingAvailability(false);
      }
    }

    // 2. Refresh bank questions if bank modal is open
    fetchBankQuestionsForImport();

    addToast(`Successfully enriched Question Bank with ${importResult?.imported_count || 'new'} approved questions!`, 'success');
  };

  // Form State for Manual Create/Edit
  const [formData, setFormData] = useState({
    job_id: '',
    title: '',
    instructions: '',
    duration_minutes: 30,
    passing_marks: 5,
    randomize_questions: false,
    randomize_options: false,
    questions: [
      {
        question_text: '',
        order_num: 1,
        marks: 1,
        explanation: '',
        options: [
          { option_key: 'A', option_text: '', is_correct: true },
          { option_key: 'B', option_text: '', is_correct: false },
        ]
      }
    ]
  });

  const handleApplyUniformMarks = (uniformMark) => {
    const markVal = Math.max(1, parseInt(uniformMark, 10) || 1);
    setFormData((prev) => ({
      ...prev,
      questions: prev.questions.map((q) => ({ ...q, marks: markVal })),
      passing_marks: Math.max(1, Math.round(prev.questions.length * markVal * 0.6))
    }));
    addToast(`Applied uniform ${markVal} mark(s) across all ${formData.questions.length} questions.`, 'info');
  };

  // Calculate dynamic total marks from questions
  const totalCalculatedMarks = useMemo(() => {
    return formData.questions.reduce((acc, q) => acc + (parseInt(q.marks, 10) || 0), 0);
  }, [formData.questions]);

  // Keep internal jobs synchronized
  useEffect(() => {
    if (jobs && jobs.length > 0) {
      setInternalJobs(jobs);
    } else {
      recruiterAPI.getJobs()
        .then((res) => {
          if (res.data && res.data.length > 0) {
            setInternalJobs(res.data);
          }
        })
        .catch((err) => console.error('Failed to load recruiter jobs in assessments:', err));
    }
  }, [jobs]);

  // When internalJobs populate, seed default job_id if blank
  useEffect(() => {
    if (internalJobs.length > 0) {
      setFormData((prev) => (prev.job_id ? prev : { ...prev, job_id: internalJobs[0].id }));
      setAutoGenForm((prev) => (
        prev.job_id
          ? prev
          : {
              ...prev,
              job_id: internalJobs[0].id,
              title: `${internalJobs[0].title || 'Technical'} Screening Assessment`
            }
      ));
    }
  }, [internalJobs]);

  // Fetch assessments for recruiter
  const fetchAssessments = async () => {
    try {
      setLoading(true);
      const res = await assessmentsAPI.listRecruiter(selectedJobId || null);
      setAssessments(res.data || []);
    } catch (err) {
      console.error('Failed to load assessments:', err);
      addToast('Failed to load assessments.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch technologies catalog
  const fetchTechCatalog = async () => {
    try {
      const res = await questionBankAPI.getTechnologies();
      const data = res.data || {};
      const techs = Array.isArray(data.technologies)
        ? data.technologies.map((t) => (typeof t === 'string' ? t : t.technology || String(t)))
        : [];
      const topicsByTech = data.topics_by_technology || {};
      setTechMetadata({
        technologies: techs,
        topics_by_technology: topicsByTech
      });

      if (techs.length > 0) {
        setAutoGenForm((prev) => ({
          ...prev,
          technology: prev.technology && techs.includes(prev.technology) ? prev.technology : techs[0],
          topic: prev.topic || (topicsByTech[techs[0]]?.[0] || '')
        }));
      }
    } catch (err) {
      console.error('Failed to load technologies catalog:', err);
    }
  };

  useEffect(() => {
    fetchAssessments();
    fetchTechCatalog();
  }, [selectedJobId]);

  // Open Manual Create Modal
  const handleOpenCreate = () => {
    if (internalJobs.length === 0) {
      addToast('Please post at least one active job opening before creating an assessment.', 'warning');
      return;
    }
    setEditingAssessmentId(null);
    setFormData({
      job_id: internalJobs[0]?.id || '',
      title: `${internalJobs[0]?.title || 'Core'} Technical Assessment`,
      instructions: 'Please answer all multiple-choice questions within the allocated time. Each question has exactly one correct answer.',
      duration_minutes: 30,
      passing_marks: 5,
      randomize_questions: false,
      randomize_options: false,
      questions: [
        {
          question_text: '',
          order_num: 1,
          marks: 5,
          explanation: '',
          options: [
            { option_key: 'A', option_text: '', is_correct: true },
            { option_key: 'B', option_text: '', is_correct: false },
          ]
        }
      ]
    });
    setShowCreateModal(true);
  };

  // Open Edit Modal for Draft
  const handleOpenEdit = async (assessment) => {
    if (assessment.status !== 'DRAFT') {
      addToast('Only DRAFT assessments can be modified.', 'info');
      return;
    }
    try {
      const res = await assessmentsAPI.getDetails(assessment.id);
      const data = res.data;
      setEditingAssessmentId(assessment.id);
      setFormData({
        job_id: data.job_id,
        title: data.title,
        instructions: data.instructions || '',
        duration_minutes: data.duration_minutes,
        passing_marks: data.passing_marks,
        randomize_questions: Boolean(data.randomize_questions),
        randomize_options: Boolean(data.randomize_options),
        questions: data.questions.map((q) => ({
          bank_question_id: q.bank_question_id || null,
          question_text: q.question_text,
          order_num: q.order_num,
          marks: q.marks,
          explanation: q.explanation || '',
          options: q.options.map((o) => ({
            option_key: o.option_key,
            option_text: o.option_text,
            is_correct: o.is_correct || false
          }))
        }))
      });
      setShowCreateModal(true);
    } catch (err) {
      console.error('Failed to load assessment for editing:', err);
      addToast('Failed to load assessment details.', 'error');
    }
  };

  // Question manipulations
  const handleAddQuestion = () => {
    setFormData((prev) => ({
      ...prev,
      questions: [
        ...prev.questions,
        {
          question_text: '',
          order_num: prev.questions.length + 1,
          marks: 5,
          explanation: '',
          options: [
            { option_key: 'A', option_text: '', is_correct: true },
            { option_key: 'B', option_text: '', is_correct: false },
          ]
        }
      ]
    }));
  };

  const handleRemoveQuestion = (idx) => {
    if (formData.questions.length <= 1) {
      addToast('An assessment must have at least one question.', 'error');
      return;
    }
    setFormData((prev) => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== idx)
    }));
  };

  const handleAddOption = (qIdx) => {
    const q = formData.questions[qIdx];
    if (q.options.length >= 5) {
      addToast('Maximum 5 options allowed per question.', 'error');
      return;
    }
    const nextKey = String.fromCharCode(65 + q.options.length);
    const newOptions = [...q.options, { option_key: nextKey, option_text: '', is_correct: false }];

    setFormData((prev) => {
      const updatedQ = [...prev.questions];
      updatedQ[qIdx] = { ...updatedQ[qIdx], options: newOptions };
      return { ...prev, questions: updatedQ };
    });
  };

  const handleRemoveOption = (qIdx, optIdx) => {
    const q = formData.questions[qIdx];
    if (q.options.length <= 2) {
      addToast('Each question must have at least 2 options.', 'error');
      return;
    }
    const filtered = q.options.filter((_, i) => i !== optIdx);
    const rekeyed = filtered.map((opt, i) => ({
      ...opt,
      option_key: String.fromCharCode(65 + i),
      is_correct: i === 0 && !filtered.some((o) => o.is_correct) ? true : opt.is_correct
    }));

    setFormData((prev) => {
      const updatedQ = [...prev.questions];
      updatedQ[qIdx] = { ...updatedQ[qIdx], options: rekeyed };
      return { ...prev, questions: updatedQ };
    });
  };

  const handleSetCorrectOption = (qIdx, optIdx) => {
    setFormData((prev) => {
      const updatedQ = [...prev.questions];
      const opts = updatedQ[qIdx].options.map((opt, i) => ({
        ...opt,
        is_correct: i === optIdx
      }));
      updatedQ[qIdx] = { ...updatedQ[qIdx], options: opts };
      return { ...prev, questions: updatedQ };
    });
  };

  // Save / Submit Manual Assessment Form
  const handleSaveAssessment = async (e) => {
    e.preventDefault();

    if (!formData.job_id) {
      addToast('Please select a target job posting.', 'error');
      return;
    }
    if (!formData.title.trim()) {
      addToast('Please enter an assessment title.', 'error');
      return;
    }
    if (formData.duration_minutes <= 0) {
      addToast('Duration must be greater than zero minutes.', 'error');
      return;
    }
    if (formData.passing_marks <= 0) {
      addToast('Passing marks must be greater than zero.', 'error');
      return;
    }
    if (formData.passing_marks > totalCalculatedMarks) {
      addToast(`Passing marks (${formData.passing_marks}) cannot exceed total marks (${totalCalculatedMarks}).`, 'error');
      return;
    }

    for (let i = 0; i < formData.questions.length; i++) {
      const q = formData.questions[i];
      if (!q.question_text.trim()) {
        addToast(`Question #${i + 1} prompt cannot be empty.`, 'error');
        return;
      }
      for (let j = 0; j < q.options.length; j++) {
        if (!q.options[j].option_text.trim()) {
          addToast(`Option ${q.options[j].option_key} in Question #${i + 1} cannot be empty.`, 'error');
          return;
        }
      }
      const hasCorrect = q.options.some((o) => o.is_correct);
      if (!hasCorrect) {
        addToast(`Question #${i + 1} must have one correct answer marked.`, 'error');
        return;
      }
    }

    try {
      const payload = {
        title: formData.title.trim(),
        instructions: formData.instructions,
        duration_minutes: Number(formData.duration_minutes),
        passing_marks: Number(formData.passing_marks),
        randomize_questions: Boolean(formData.randomize_questions),
        randomize_options: Boolean(formData.randomize_options),
        questions: formData.questions
      };

      if (editingAssessmentId) {
        await assessmentsAPI.updateDraft(editingAssessmentId, payload);
        addToast('Draft assessment updated successfully!', 'success');
      } else {
        await assessmentsAPI.create({
          ...payload,
          job_id: formData.job_id
        });
        addToast('Assessment created in DRAFT status!', 'success');
      }
      setShowCreateModal(false);
      fetchAssessments();
    } catch (err) {
      console.error('Failed to save assessment:', err);
      addToast(err.response?.data?.detail || 'Failed to save assessment.', 'error');
    }
  };

  // Open Auto-Generate Modal
  const handleOpenAutoGenerate = () => {
    if (internalJobs.length === 0) {
      addToast('Please post at least one active job opening before generating assessments.', 'warning');
      return;
    }
    const defaultTech = techMetadata.technologies[0] || 'Python';
    const defaultTopic = techMetadata.topics_by_technology[defaultTech]?.[0] || '';
    setAutoGenForm({
      job_id: internalJobs[0]?.id || '',
      title: `${internalJobs[0]?.title || 'Technical'} Screening Assessment`,
      instructions: 'Answer all multiple-choice questions within the allocated time. Each question has exactly one correct answer.',
      technology: defaultTech,
      topic: defaultTopic,
      total_questions: 5,
      duration_minutes: 30,
      marks_per_question: 1,
      uniform_marks_enabled: true,
      passing_marks: 3,
      randomize_questions: true,
      randomize_options: true,
      beginner_pct: 40,
      intermediate_pct: 40,
      advanced_pct: 20
    });
    setShowAutoGenerateModal(true);
  };

  // Submit Auto-Generate Assessment
  const handleAutoGenerateSubmit = async (e) => {
    e.preventDefault();

    if (!autoGenForm.job_id) {
      addToast('Please select a target job posting.', 'error');
      return;
    }
    if (!autoGenForm.title.trim()) {
      addToast('Please enter an assessment title.', 'error');
      return;
    }
    const pctSum = Number(autoGenForm.beginner_pct) + Number(autoGenForm.intermediate_pct) + Number(autoGenForm.advanced_pct);
    if (pctSum !== 100) {
      addToast(`Difficulty distribution percentages must sum to exactly 100% (currently ${pctSum}%).`, 'error');
      return;
    }

    try {
      setAutoGenLoading(true);
      const count = Number(autoGenForm.total_questions) || 5;
      const marksPerQ = autoGenForm.uniform_marks_enabled ? (Number(autoGenForm.marks_per_question) || 1) : null;
      const begCount = Math.max(0, Math.round(count * (Number(autoGenForm.beginner_pct) / 100)));
      const advCount = Math.max(0, Math.round(count * (Number(autoGenForm.advanced_pct) / 100)));
      const intCount = Math.max(0, count - begCount - advCount);

      const calculatedTotalMarks = count * (marksPerQ || 1);
      let passingMarks = Number(autoGenForm.passing_marks) || Math.max(1, Math.round(calculatedTotalMarks * 0.6));
      if (passingMarks > calculatedTotalMarks) {
        passingMarks = Math.max(1, Math.round(calculatedTotalMarks * 0.6));
      }

      await questionBankAPI.autoGenerateAssessment({
        job_id: autoGenForm.job_id,
        title: autoGenForm.title.trim(),
        instructions: autoGenForm.instructions,
        duration_minutes: Number(autoGenForm.duration_minutes),
        passing_marks: passingMarks,
        marks_per_question: marksPerQ,
        randomize_questions: Boolean(autoGenForm.randomize_questions),
        randomize_options: Boolean(autoGenForm.randomize_options),
        technology: autoGenForm.technology,
        topic: autoGenForm.topic || null,
        question_count: count,
        total_questions: count,
        difficulty_distribution: {
          BEGINNER: begCount,
          INTERMEDIATE: intCount,
          ADVANCED: advCount,
          beginner_pct: Number(autoGenForm.beginner_pct),
          intermediate_pct: Number(autoGenForm.intermediate_pct),
          advanced_pct: Number(autoGenForm.advanced_pct)
        }
      });
      addToast('Assessment automatically generated from Question Bank in DRAFT status!', 'success');
      setShowAutoGenerateModal(false);
      fetchAssessments();
    } catch (err) {
      console.error('Failed to auto-generate assessment:', err);
      addToast(err.response?.data?.detail || 'Failed to auto-generate assessment.', 'error');
    } finally {
      setAutoGenLoading(false);
    }
  };

  // Fetch Bank Questions for Import Modal
  const fetchBankQuestionsForImport = async () => {
    try {
      setLoadingBankQuestions(true);
      const params = {
        page: 1,
        limit: 100,
        include_custom: true
      };
      if (bankSearch.trim()) params.search = bankSearch.trim();
      if (bankTech) params.technology = bankTech;
      if (bankDifficulty) params.difficulty = bankDifficulty;

      const res = await questionBankAPI.list(params);
      setBankQuestions(res.data?.items || []);
    } catch (err) {
      console.error('Failed to load bank questions for import:', err);
      addToast('Failed to load questions from bank.', 'error');
    } finally {
      setLoadingBankQuestions(false);
    }
  };

  // Confirm Import from Question Bank into Assessment Builder
  const handleConfirmImportFromBank = () => {
    if (selectedBankQuestions.length === 0) {
      addToast('Select at least one question from the bank to import.', 'error');
      return;
    }

    const existingBankIds = new Set(
      formData.questions.map((q) => q.bank_question_id).filter(Boolean)
    );
    const existingTexts = new Set(
      formData.questions.map((q) => (q.question_text || '').trim().toLowerCase())
    );

    const nonDuplicateBankQuestions = selectedBankQuestions.filter(
      (bq) => !existingBankIds.has(bq.id) && !existingTexts.has((bq.question_text || '').trim().toLowerCase())
    );

    if (nonDuplicateBankQuestions.length === 0) {
      addToast('All selected questions are already present in this assessment.', 'info');
      setShowAddFromBankModal(false);
      setSelectedBankQuestions([]);
      return;
    }

    const importedQuestions = nonDuplicateBankQuestions.map((bq, idx) => ({
      bank_question_id: bq.id,
      question_text: bq.question_text,
      order_num: formData.questions.length + idx + 1,
      marks: bq.marks || 1,
      explanation: bq.explanation || '',
      options: (bq.options || []).map((o) => ({
        option_key: o.option_key,
        option_text: o.option_text,
        is_correct: o.is_correct || false
      }))
    }));

    setFormData((prev) => ({
      ...prev,
      questions: [...prev.questions, ...importedQuestions]
    }));

    if (bankPickerContext === 'auto_generate') {
      setShowAutoGenerateModal(false);
      setShowCreateModal(true);
      addToast(`Imported ${importedQuestions.length} question(s) into your Assessment Builder!`, 'success');
    } else {
      addToast(`Successfully imported ${importedQuestions.length} question(s) from Question Bank!`, 'success');
    }

    setShowAddFromBankModal(false);
    setSelectedBankQuestions([]);
  };

  // Preview Assessment
  const handlePreview = async (assessmentId) => {
    try {
      const res = await assessmentsAPI.getDetails(assessmentId);
      setPreviewData(res.data);
      setShowPreviewModal(true);
    } catch (err) {
      console.error('Failed to load preview:', err);
      addToast('Failed to load assessment preview.', 'error');
    }
  };

  // Publish Assessment
  const handlePublish = async (assessmentId) => {
    try {
      await assessmentsAPI.publish(assessmentId);
      addToast('Assessment published! You can now assign it to shortlisted candidates.', 'success');
      fetchAssessments();
    } catch (err) {
      console.error('Failed to publish assessment:', err);
      addToast(err.response?.data?.detail || 'Failed to publish assessment.', 'error');
    }
  };

  // Open Shortlist Assignment Modal
  const handleOpenAssignModal = async (assessment) => {
    setCurrentAssignAssessment(assessment);
    setSelectedCandidateIds([]);
    try {
      const res = await assessmentsAPI.getShortlistedCandidates(assessment.id);
      setShortlistedCandidates(res.data || []);
      setShowAssignModal(true);
    } catch (err) {
      console.error('Failed to load shortlisted candidates:', err);
      addToast('Failed to load shortlisted candidates for this job.', 'error');
    }
  };

  const handleToggleCandidateSelect = (candId) => {
    setSelectedCandidateIds((prev) =>
      prev.includes(candId) ? prev.filter((id) => id !== candId) : [...prev, candId]
    );
  };

  const handleAssignCandidatesSubmit = async () => {
    if (selectedCandidateIds.length === 0) {
      addToast('Select at least one candidate to assign.', 'error');
      return;
    }
    try {
      setIsAssigning(true);
      await assessmentsAPI.assign(currentAssignAssessment.id, {
        candidate_ids: selectedCandidateIds
      });
      addToast(`Assessment successfully assigned to ${selectedCandidateIds.length} candidate(s)!`, 'success');
      setShowAssignModal(false);
      fetchAssessments();
    } catch (err) {
      console.error('Failed to assign assessment:', err);
      addToast(err.response?.data?.detail || 'Failed to assign candidates.', 'error');
    } finally {
      setIsAssigning(false);
    }
  };

  // Open Results View
  const handleOpenResults = async (assessment) => {
    setResultsAssessment(assessment);
    setResultFilter('all');
    setShowResultsModal(true);
    fetchResults(assessment.id, 'all');
  };

  const fetchResults = async (assessmentId, filter = 'all') => {
    try {
      setResultsLoading(true);
      const res = await assessmentsAPI.getResults(assessmentId, filter);
      setCandidateResults(res.data || []);
    } catch (err) {
      console.error('Failed to load candidate results:', err);
      addToast('Failed to load assessment results.', 'error');
    } finally {
      setResultsLoading(false);
    }
  };

  // Open Candidate Answer Review Modal
  const handleOpenAnswerReview = async (assignmentId) => {
    try {
      setReviewLoading(true);
      setShowReviewModal(true);
      const res = await assessmentsAPI.getCandidateReview(assignmentId);
      setReviewData(res.data);
    } catch (err) {
      console.error('Failed to load candidate answer review:', err);
      addToast('Failed to load candidate answer details.', 'error');
      setShowReviewModal(false);
    } finally {
      setReviewLoading(false);
    }
  };

  // Status Badge Helper
  const renderStatusBadge = (status) => {
    const map = {
      DRAFT: 'bg-slate/20 text-slate dark:text-ivory/60 border-slate/30',
      PUBLISHED: 'bg-success/20 text-success border-success/30',
      ASSIGNED: 'bg-primary/20 text-primary border-primary/30',
      STARTED: 'bg-warning/20 text-warning border-warning/30',
      SUBMITTED: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      PASSED: 'bg-success/20 text-success border-success/30',
      FAILED: 'bg-oxblood/30 text-rose border-rose/30',
      EXPIRED: 'bg-slate/30 text-slate-400 border-slate-500/30'
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase border ${
        map[status] || 'bg-white/10 text-ivory/70 border-white/20'
      }`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* ======================================================== */}
      {/* 0. RECRUITER SUB-NAVIGATION TABS */}
      {/* ======================================================== */}
      <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 overflow-x-auto pb-1">
        <button
          onClick={() => setSectionTab('assessments')}
          className={`flex items-center gap-2 py-3 px-5 text-xs font-mono font-bold uppercase tracking-wider rounded-t-2xl whitespace-nowrap transition-colors min-h-[44px] ${
            activeSectionTab === 'assessments'
              ? 'bg-oxblood text-ivory shadow-sm'
              : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory bg-slate/5 dark:bg-white/5'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Job MCQ Assessments</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/25 text-ivory">
            {assessments.length}
          </span>
        </button>

        <button
          onClick={() => setSectionTab('question_bank')}
          className={`flex items-center gap-2 py-3 px-5 text-xs font-mono font-bold uppercase tracking-wider rounded-t-2xl whitespace-nowrap transition-colors min-h-[44px] ${
            activeSectionTab === 'question_bank'
              ? 'bg-oxblood text-ivory shadow-sm'
              : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory bg-slate/5 dark:bg-white/5'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Central Question Bank & Custom Items</span>
        </button>

        <button
          onClick={() => setSectionTab('reviews')}
          className={`flex items-center gap-2 py-3 px-5 text-xs font-mono font-bold uppercase tracking-wider rounded-t-2xl whitespace-nowrap transition-colors min-h-[44px] ${
            activeSectionTab === 'reviews'
              ? 'bg-oxblood text-ivory shadow-sm'
              : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory bg-slate/5 dark:bg-white/5'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Candidate Reviews & Decisions</span>
        </button>
      </div>

      {/* ======================================================== */}
      {/* VIEW A: QUESTION BANK TAB */}
      {/* ======================================================== */}
      {activeSectionTab === 'question_bank' && (
        <RecruiterQuestionBankTab />
      )}

      {/* ======================================================== */}
      {/* VIEW B: JOB ASSESSMENTS LIST & WORKFLOWS */}
      {/* ======================================================== */}
      {activeSectionTab === 'assessments' && (
        <div className="space-y-6">
          {/* Top Header Card */}
          <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
              <div>
                <div className="flex items-center gap-2">
                  <span className="p-2 rounded-xl bg-oxblood/10 text-oxblood dark:text-rose">
                    <Award size={20} />
                  </span>
                  <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory">
                    First-Round MCQ Assessments
                  </h2>
                </div>
                <p className="text-xs font-mono text-slate/70 dark:text-ivory/60 mt-1">
                  Create, publish, and assign time-bound screening assessments to shortlisted candidates.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5">
                {/* Filter by Job */}
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  className="bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[44px]"
                >
                  <option value="">All Job Postings</option>
                  {internalJobs.map((job) => (
                    <option key={job.id} value={job.id} className="bg-charcoal text-ivory">
                      {job.title}
                    </option>
                  ))}
                </select>

                {/* Auto-Generate Button */}
                <button
                  type="button"
                  onClick={handleOpenAutoGenerate}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-oxblood hover:text-ivory text-charcoal dark:text-ivory text-xs font-mono font-bold uppercase tracking-wider transition-all border border-slate/20 dark:border-rose/20 min-h-[44px]"
                >
                  <Sparkles size={15} className="text-oxblood dark:text-rose" /> Auto-Generate
                </button>

                {/* Manual Assessment Button */}
                <button
                  type="button"
                  onClick={handleOpenCreate}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider transition-all shadow-md shadow-oxblood/20 min-h-[44px]"
                >
                  <Plus size={16} /> New Assessment
                </button>
              </div>
            </div>

            {/* Empty Jobs Warning if Recruiter has no active jobs */}
            {internalJobs.length === 0 && (
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs font-mono text-amber-600 dark:text-amber-400">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <p>
                  No active job postings found. Assessments must be attached to an existing job opening. Create a job listing under <strong>Manage Postings</strong> first.
                </p>
              </div>
            )}

            {/* Quick Stats Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/50">Total Created</p>
                <p className="text-2xl font-bold font-mono text-charcoal dark:text-ivory mt-1">
                  <AnimatedCounter value={assessments.length} />
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/50">Published</p>
                <p className="text-2xl font-bold font-mono text-success mt-1">
                  <AnimatedCounter value={assessments.filter((a) => a.status === 'PUBLISHED').length} />
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/50">Drafts</p>
                <p className="text-2xl font-bold font-mono text-oxblood dark:text-rose mt-1">
                  <AnimatedCounter value={assessments.filter((a) => a.status === 'DRAFT').length} />
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/50">Assigned Jobs</p>
                <p className="text-2xl font-bold font-mono text-charcoal dark:text-ivory mt-1">
                  <AnimatedCounter value={new Set(assessments.map((a) => a.job_id)).size} />
                </p>
              </div>
            </div>
          </div>

          {/* Assessments Grid / List */}
          {loading ? (
            <div className="min-h-[200px] flex items-center justify-center font-mono text-xs text-slate/60 dark:text-ivory/50">
              <div className="w-6 h-6 rounded-full border-2 border-oxblood/30 border-t-oxblood animate-spin mr-2" />
              Loading assessments...
            </div>
          ) : assessments.length === 0 ? (
            <div className="glass-card p-12 text-center rounded-3xl border border-dashed border-slate/20 dark:border-rose/20 space-y-3">
              <Award className="w-12 h-12 text-slate/40 dark:text-rose/40 mx-auto" />
              <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
                No Assessments Created Yet
              </h3>
              <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 max-w-md mx-auto">
                Design time-bound first-round MCQ screenings or automatically generate one using our centralized technical question bank.
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <button
                  onClick={handleOpenAutoGenerate}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 text-charcoal dark:text-ivory text-xs font-mono font-bold uppercase tracking-wider min-h-[44px]"
                >
                  <Sparkles size={15} className="text-oxblood" /> Auto-Generate Test
                </button>
                <button
                  onClick={handleOpenCreate}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase tracking-wider min-h-[44px]"
                >
                  <Plus size={16} /> Create First Assessment
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {assessments.map((asm) => (
                <motion.div
                  key={asm.id}
                  layout
                  className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-lg flex flex-col justify-between space-y-5"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-[10px] font-mono text-slate/60 dark:text-ivory/50 uppercase truncate max-w-[180px]">
                        {asm.job_title || 'Job Posting'}
                      </span>
                      {renderStatusBadge(asm.status)}
                    </div>

                    <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory leading-snug">
                      {asm.title}
                    </h3>

                    {asm.instructions && (
                      <p className="text-xs font-sans text-slate/70 dark:text-ivory/60 mt-2 line-clamp-2">
                        {asm.instructions}
                      </p>
                    )}

                    {/* Metrics Pill Grid */}
                    <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate/10 dark:border-white/5 text-center">
                      <div className="p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                        <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Questions</p>
                        <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory">{asm.question_count}</p>
                      </div>
                      <div className="p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                        <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Duration</p>
                        <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory">{asm.duration_minutes}m</p>
                      </div>
                      <div className="p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                        <p className="text-[9px] font-mono uppercase text-slate/50 dark:text-ivory/40">Pass / Total</p>
                        <p className="text-sm font-bold font-mono text-charcoal dark:text-ivory">
                          {asm.passing_marks} / {asm.total_marks}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-2 pt-2 border-t border-slate/10 dark:border-white/5">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePreview(asm.id)}
                        className="flex-1 py-2 px-3 rounded-xl bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-xs font-mono font-semibold text-charcoal dark:text-ivory flex items-center justify-center gap-1.5 min-h-[40px]"
                      >
                        <Eye size={14} /> Preview
                      </button>

                      {asm.status === 'DRAFT' && (
                        <button
                          onClick={() => handleOpenEdit(asm)}
                          className="py-2 px-3 rounded-xl bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-xs font-mono font-semibold text-charcoal dark:text-ivory flex items-center justify-center gap-1.5 min-h-[40px]"
                        >
                          <Edit3 size={14} /> Edit
                        </button>
                      )}
                    </div>

                    {asm.status === 'DRAFT' ? (
                      <button
                        onClick={() => handlePublish(asm.id)}
                        className="w-full py-2.5 px-4 rounded-xl bg-success/20 hover:bg-success/30 text-success border border-success/30 text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-2 min-h-[42px]"
                      >
                        <CheckCircle2 size={16} /> Publish Assessment
                      </button>
                    ) : (
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => handleOpenAssignModal(asm)}
                            className="py-2.5 px-3 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 min-h-[42px] shadow-sm shadow-oxblood/20"
                          >
                            <UserCheck size={14} /> Assign
                          </button>
                          <button
                            onClick={() => handleOpenResults(asm)}
                            className="py-2.5 px-3 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 min-h-[42px]"
                          >
                            <Award size={14} /> Results
                          </button>
                        </div>

                        {/* Analytics Telemetry Button */}
                        <button
                          type="button"
                          onClick={() => {
                            setAnalyticsAssessment(asm);
                            setShowAnalyticsModal(true);
                          }}
                          className="w-full py-2 px-3 rounded-xl bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-charcoal dark:text-ivory text-xs font-mono font-semibold flex items-center justify-center gap-1.5 min-h-[38px] border border-slate/15 dark:border-rose/15 transition-colors"
                        >
                          <BarChart3 size={14} className="text-oxblood dark:text-rose" /> Performance Analytics
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* VIEW C: RECRUITER REVIEWS & DECISIONS TAB */}
      {/* ======================================================== */}
      {activeSectionTab === 'reviews' && (
        <RecruiterReviewsTab jobs={internalJobs} assessments={assessments} />
      )}

      {/* ==================================================================== */}
      {/* MODAL 1: CREATE / EDIT ASSESSMENT BUILDER */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={editingAssessmentId ? 'Edit Draft Assessment' : 'Create First-Round Assessment'}
      >
        <form onSubmit={handleSaveAssessment} className="space-y-6 text-charcoal dark:text-ivory max-h-[75vh] overflow-y-auto pr-1">
          {/* Job Selection */}
          <div>
            <label className="block text-xs font-mono font-bold uppercase text-slate/70 dark:text-ivory/60 mb-1.5">
              Target Job Posting *
            </label>
            <select
              value={formData.job_id}
              disabled={Boolean(editingAssessmentId)}
              onChange={(e) => setFormData({ ...formData, job_id: e.target.value })}
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-4 py-2.5 text-xs font-mono text-charcoal dark:text-ivory min-h-[44px]"
            >
              <option value="">-- Select Target Job Opening --</option>
              {internalJobs.map((job) => (
                <option key={job.id} value={job.id} className="bg-charcoal text-ivory">
                  {job.title} ({job.location})
                </option>
              ))}
            </select>
          </div>

          {/* Assessment Title */}
          <div>
            <label className="block text-xs font-mono font-bold uppercase text-slate/70 dark:text-ivory/60 mb-1.5">
              Assessment Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="e.g. Core Python & System Design First-Round MCQ"
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm font-sans text-charcoal dark:text-ivory min-h-[44px]"
            />
          </div>

          {/* Instructions */}
          <div>
            <label className="block text-xs font-mono font-bold uppercase text-slate/70 dark:text-ivory/60 mb-1.5">
              Candidate Instructions
            </label>
            <textarea
              rows={2}
              value={formData.instructions}
              onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
              placeholder="Instructions displayed to shortlisted candidates before starting..."
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl p-3 text-xs font-sans text-charcoal dark:text-ivory"
            />
          </div>

          {/* Duration & Marks Configuration */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
                Duration (Minutes) *
              </label>
              <input
                type="number"
                min="1"
                max="180"
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value, 10) || 1 })}
                required
                className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[40px]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
                Total Marks (Auto)
              </label>
              <div className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono font-bold text-oxblood dark:text-rose min-h-[40px] flex items-center">
                {totalCalculatedMarks} Marks
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
                Passing Marks *
              </label>
              <input
                type="number"
                min="1"
                max={totalCalculatedMarks || 100}
                value={formData.passing_marks}
                onChange={(e) => setFormData({ ...formData, passing_marks: parseInt(e.target.value, 10) || 1 })}
                required
                className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[40px]"
              />
            </div>
          </div>

          {/* Randomization Security Toggles */}
          <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 space-y-3 font-mono">
            <div className="flex items-center gap-2">
              <Shuffle className="w-4 h-4 text-oxblood dark:text-rose" />
              <span className="text-xs font-bold uppercase tracking-wider text-charcoal dark:text-ivory">
                Intelligent Attempt Randomization
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white/5 border border-slate/10 hover:bg-white/10 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.randomize_questions || false}
                  onChange={(e) => setFormData({ ...formData, randomize_questions: e.target.checked })}
                  className="w-4 h-4 text-oxblood rounded cursor-pointer"
                />
                <div>
                  <p className="font-bold text-charcoal dark:text-ivory">Shuffle Questions</p>
                  <p className="text-[10px] text-slate/50">Each candidate gets a unique server sequence</p>
                </div>
              </label>

              <label className="flex items-center gap-2.5 p-3 rounded-xl bg-white/5 border border-slate/10 hover:bg-white/10 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.randomize_options || false}
                  onChange={(e) => setFormData({ ...formData, randomize_options: e.target.checked })}
                  className="w-4 h-4 text-oxblood rounded cursor-pointer"
                />
                <div>
                  <p className="font-bold text-charcoal dark:text-ivory">Shuffle Options (A-D)</p>
                  <p className="text-[10px] text-slate/50">Randomizes choices while mapping answers securely</p>
                </div>
              </label>
            </div>
          </div>

          {/* Questions Builder */}
          <div className="space-y-4 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-ivory/60">
                Assessment Questions ({formData.questions.length})
              </h4>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setBankSearch('');
                    setBankTech('');
                    setBankDifficulty('');
                    setSelectedBankQuestions([]);
                    fetchBankQuestionsForImport();
                    setBankPickerContext('manual_builder');
                    setShowAddFromBankModal(true);
                  }}
                  className="text-xs font-mono text-oxblood dark:text-rose hover:underline flex items-center gap-1 font-bold"
                >
                  <Database size={14} /> Add from Question Bank
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setUploadModalContext('manual_builder');
                    setShowUploadFileModal(true);
                  }}
                  className="text-xs font-mono text-oxblood dark:text-rose hover:underline flex items-center gap-1 font-bold"
                >
                  <Upload size={14} /> Upload Question File
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const m = window.prompt("Enter uniform marks per question (e.g. 1, 2, 5):", "1");
                    if (m !== null) handleApplyUniformMarks(m);
                  }}
                  className="text-xs font-mono text-slate/70 dark:text-ivory/70 hover:underline flex items-center gap-1"
                  title="Apply uniform marks across all questions"
                >
                  <Award size={14} /> Uniform Marks
                </button>
                <button
                  type="button"
                  onClick={handleAddQuestion}
                  className="text-xs font-mono text-slate/70 dark:text-ivory/70 hover:underline flex items-center gap-1"
                >
                  <Plus size={14} /> Add Blank Question
                </button>
              </div>
            </div>

            {formData.questions.map((q, qIdx) => (
              <div
                key={qIdx}
                className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 space-y-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-lg bg-white/10 text-[11px] font-mono font-bold text-charcoal dark:text-ivory">
                      Question #{qIdx + 1}
                    </span>
                    {q.bank_question_id && (
                      <span className="text-[10px] font-mono text-oxblood dark:text-rose bg-oxblood/10 px-2 py-0.5 rounded border border-oxblood/20">
                        Bank Linked
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-[10px] font-mono uppercase text-slate/50 dark:text-ivory/40">Marks:</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={q.marks}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10) || 1;
                        setFormData((prev) => {
                          const updated = [...prev.questions];
                          updated[qIdx] = { ...updated[qIdx], marks: val };
                          return { ...prev, questions: updated };
                        });
                      }}
                      className="w-16 bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-lg px-2 py-1 text-xs font-mono text-center"
                    />
                    {formData.questions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveQuestion(qIdx)}
                        className="text-slate/40 hover:text-rose p-1 transition-colors"
                        title="Remove question"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                </div>

                <input
                  type="text"
                  placeholder="Enter question prompt..."
                  value={q.question_text}
                  onChange={(e) => {
                    const text = e.target.value;
                    setFormData((prev) => {
                      const updated = [...prev.questions];
                      updated[qIdx] = { ...updated[qIdx], question_text: text };
                      return { ...prev, questions: updated };
                    });
                  }}
                  required
                  className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-xl p-3 text-xs font-sans text-charcoal dark:text-ivory min-h-[40px]"
                />

                {/* Options */}
                <div className="space-y-2 pl-2 border-l-2 border-oxblood/40">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-slate/50 dark:text-ivory/40">
                    Options (Select radio for the correct answer):
                  </p>
                  {q.options.map((opt, optIdx) => (
                    <div key={optIdx} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name={`correct_opt_${qIdx}`}
                        checked={opt.is_correct}
                        onChange={() => handleSetCorrectOption(qIdx, optIdx)}
                        className="w-4 h-4 text-oxblood focus:ring-oxblood cursor-pointer"
                        title="Mark as correct answer"
                      />
                      <span className="w-5 text-xs font-mono font-bold text-oxblood dark:text-rose">
                        {opt.option_key}.
                      </span>
                      <input
                        type="text"
                        placeholder={`Option ${opt.option_key} text...`}
                        value={opt.option_text}
                        onChange={(e) => {
                          const val = e.target.value;
                          setFormData((prev) => {
                            const updated = [...prev.questions];
                            const opts = [...updated[qIdx].options];
                            opts[optIdx] = { ...opts[optIdx], option_text: val };
                            updated[qIdx] = { ...updated[qIdx], options: opts };
                            return { ...prev, questions: updated };
                          });
                        }}
                        required
                        className="flex-1 bg-white/10 dark:bg-charcoal border border-slate/20 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs font-sans min-h-[36px]"
                      />
                      {q.options.length > 2 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveOption(qIdx, optIdx)}
                          className="text-slate/40 hover:text-rose p-1"
                        >
                          <X size={14} />
                        </button>
                      )}
                    </div>
                  ))}

                  {q.options.length < 5 && (
                    <button
                      type="button"
                      onClick={() => handleAddOption(qIdx)}
                      className="text-[11px] font-mono text-slate/60 dark:text-ivory/50 hover:text-charcoal dark:hover:text-ivory flex items-center gap-1 mt-1 pt-1"
                    >
                      <Plus size={12} /> Add Option
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Modal Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate/15 dark:border-white/10">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs font-mono uppercase tracking-wider min-h-[44px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider shadow-md shadow-oxblood/20 min-h-[44px]"
            >
              {editingAssessmentId ? 'Save Changes' : 'Create Draft'}
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 1B: ADD QUESTIONS FROM QUESTION BANK MODAL */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showAddFromBankModal}
        onClose={() => setShowAddFromBankModal(false)}
        title="Add Questions from Question Bank"
        subtitle="Import predefined technical questions directly into this assessment snapshot"
      >
        <div className="space-y-4 text-charcoal dark:text-ivory font-mono text-xs max-h-[75vh] overflow-y-auto pr-1">
          {/* Filter Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input
              type="text"
              placeholder="Search bank questions..."
              value={bankSearch}
              onChange={(e) => setBankSearch(e.target.value)}
              className="bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[38px]"
            />
            <select
              value={bankTech}
              onChange={(e) => setBankTech(e.target.value)}
              className="bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[38px]"
            >
              <option value="">All Technologies</option>
              {(techMetadata.technologies || []).map((t) => {
                const val = typeof t === 'string' ? t : t.technology || String(t);
                return (
                  <option key={val} value={val} className="bg-charcoal text-ivory">{val}</option>
                );
              })}
            </select>
            <div className="flex gap-2">
              <select
                value={bankDifficulty}
                onChange={(e) => setBankDifficulty(e.target.value)}
                className="flex-1 bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[38px]"
              >
                <option value="">All Difficulties</option>
                <option value="BEGINNER" className="bg-charcoal text-ivory">Beginner</option>
                <option value="INTERMEDIATE" className="bg-charcoal text-ivory">Intermediate</option>
                <option value="ADVANCED" className="bg-charcoal text-ivory">Advanced</option>
              </select>
              <button
                type="button"
                onClick={fetchBankQuestionsForImport}
                className="px-3 py-2 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase min-h-[38px]"
              >
                Filter
              </button>
            </div>
          </div>

          {/* List of Questions */}
          {loadingBankQuestions ? (
            <div className="py-12 text-center text-slate/50">Loading questions from bank...</div>
          ) : bankQuestions.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-slate/5 text-slate/50">
              No matching questions found in bank.
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto border border-slate/15 rounded-2xl p-2 bg-black/10">
              {bankQuestions.map((bq) => {
                const isSelected = selectedBankQuestions.some((q) => q.id === bq.id);
                const isAlreadyInAssessment = formData.questions.some(
                  (q) => q.bank_question_id === bq.id || (q.question_text || '').trim().toLowerCase() === bq.question_text.trim().toLowerCase()
                );
                return (
                  <div
                    key={bq.id}
                    onClick={() => {
                      if (isAlreadyInAssessment) return;
                      setSelectedBankQuestions((prev) =>
                        isSelected ? prev.filter((q) => q.id !== bq.id) : [...prev, bq]
                      );
                    }}
                    className={`p-3 rounded-xl border flex items-start gap-3 transition-colors ${
                      isAlreadyInAssessment
                        ? 'bg-slate/5 border-slate/10 opacity-60 cursor-not-allowed'
                        : isSelected
                        ? 'bg-oxblood/15 border-oxblood text-ivory cursor-pointer'
                        : 'bg-white/5 border-slate/10 hover:bg-white/10 text-slate/70 dark:text-ivory/70 cursor-pointer'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected || isAlreadyInAssessment}
                      disabled={isAlreadyInAssessment}
                      onChange={() => {}}
                      className="w-4 h-4 text-oxblood rounded cursor-pointer mt-0.5"
                    />
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between items-center text-[10px]">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-oxblood dark:text-rose">{bq.technology} &bull; {bq.topic}</span>
                          {isAlreadyInAssessment && (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold text-[9px]">
                              Already Added
                            </span>
                          )}
                        </div>
                        <span className="uppercase">{bq.difficulty} &bull; {bq.marks}m</span>
                      </div>
                      <p className="font-sans text-xs leading-snug">{bq.question_text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex justify-between items-center pt-3 border-t border-slate/15">
            <span className="text-xs">
              Selected: <strong>{selectedBankQuestions.length}</strong> questions
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowAddFromBankModal(false)}
                className="px-4 py-2 rounded-xl bg-slate/10 text-xs uppercase min-h-[40px]"
              >
                {bankPickerContext === 'auto_generate' ? 'Return to Generator' : 'Cancel'}
              </button>
              <button
                type="button"
                onClick={handleConfirmImportFromBank}
                disabled={selectedBankQuestions.length === 0}
                className="px-5 py-2 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase min-h-[40px] disabled:opacity-40"
              >
                {bankPickerContext === 'auto_generate' ? 'Import to Builder' : 'Import Questions'} ({selectedBankQuestions.length})
              </button>
            </div>
          </div>
        </div>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 1C: AUTO-GENERATE ASSESSMENT MODAL */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showAutoGenerateModal}
        onClose={() => setShowAutoGenerateModal(false)}
        title="Auto-Generate Technical Assessment"
        subtitle="Sample intelligent questions directly from the centralized Question Bank"
      >
        <form onSubmit={handleAutoGenerateSubmit} className="space-y-5 text-charcoal dark:text-ivory font-mono text-xs max-h-[75vh] overflow-y-auto pr-1">
          {/* Target Job */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
              Target Job Posting *
            </label>
            <select
              value={autoGenForm.job_id}
              onChange={(e) => {
                const jId = e.target.value;
                const targetJob = internalJobs.find((j) => j.id === jId);
                setAutoGenForm({
                  ...autoGenForm,
                  job_id: jId,
                  title: `${targetJob?.title || 'Technical'} Screening Assessment`
                });
              }}
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
            >
              <option value="">-- Select Target Job Opening --</option>
              {internalJobs.map((job) => (
                <option key={job.id} value={job.id} className="bg-charcoal text-ivory">
                  {job.title} ({job.location})
                </option>
              ))}
            </select>
          </div>

          {/* Assessment Title */}
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
              Assessment Title *
            </label>
            <input
              type="text"
              value={autoGenForm.title}
              onChange={(e) => setAutoGenForm({ ...autoGenForm, title: e.target.value })}
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs font-sans min-h-[40px]"
            />
          </div>

          {/* Technology & Topic */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
                Technology / Subject *
              </label>
              <select
                value={autoGenForm.technology}
                onChange={(e) => {
                  const nextTech = e.target.value;
                  const availTopics = techMetadata.topics_by_technology[nextTech] || [];
                  setAutoGenForm({
                    ...autoGenForm,
                    technology: nextTech,
                    topic: availTopics[0] || ''
                  });
                }}
                required
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
              >
                {(techMetadata.technologies.length > 0 ? techMetadata.technologies : ['Python', 'JavaScript', 'React', 'SQL', 'DSA', 'Java']).map((t) => {
                  const val = typeof t === 'string' ? t : t.technology || String(t);
                  return (
                    <option key={val} value={val} className="bg-charcoal text-ivory">{val}</option>
                  );
                })}
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
                Topic (Optional)
              </label>
              <select
                value={autoGenForm.topic}
                onChange={(e) => setAutoGenForm({ ...autoGenForm, topic: e.target.value })}
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
              >
                <option value="">All Topics in {autoGenForm.technology}</option>
                {(techMetadata.topics_by_technology[autoGenForm.technology] || []).map((tp) => (
                  <option key={tp} value={tp} className="bg-charcoal text-ivory">{tp}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Question Bank Availability Indicator */}
          {loadingAvailability ? (
            <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 text-slate/50 flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-oxblood dark:text-rose" />
              <span>Checking question availability in Question Bank...</span>
            </div>
          ) : availability ? (
            <div className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-1.5">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2 font-bold text-xs text-charcoal dark:text-ivory">
                  <Database className="w-4 h-4 text-oxblood dark:text-rose" />
                  <span>
                    Question Bank: <strong className="text-oxblood dark:text-rose">{availability.total_available}</strong> available in {autoGenForm.technology} {autoGenForm.topic ? `(${autoGenForm.topic})` : '(All Topics)'}
                  </span>
                </div>
                <div className="flex gap-2 text-[10px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-500/20">
                    Beg: {availability.by_difficulty?.BEGINNER || 0}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 font-bold border border-amber-500/20">
                    Int: {availability.by_difficulty?.INTERMEDIATE || 0}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-600 dark:text-rose-400 font-bold border border-rose-500/20">
                    Adv: {availability.by_difficulty?.ADVANCED || 0}
                  </span>
                </div>
              </div>
              {availability.total_available < autoGenForm.total_questions && (
                <div className="p-4 rounded-2xl bg-oxblood/10 border border-oxblood/30 space-y-3 mt-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-xs text-oxblood dark:text-rose flex items-center gap-1.5">
                      <AlertTriangle size={15} /> Insufficient Questions in Question Bank
                    </span>
                    <span className="px-2 py-0.5 rounded bg-oxblood/20 text-oxblood dark:text-rose text-[10px] font-bold">
                      Shortage Detected
                    </span>
                  </div>

                  {/* Required / Available / Missing Grid */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2.5 rounded-xl bg-slate/10 dark:bg-black/30 border border-slate/15 dark:border-white/10">
                      <p className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/50">Required</p>
                      <p className="text-base font-bold text-charcoal dark:text-ivory">{autoGenForm.total_questions}</p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate/10 dark:bg-black/30 border border-slate/15 dark:border-white/10">
                      <p className="text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/50">Available</p>
                      <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">{availability.total_available}</p>
                    </div>
                    <div className="p-2.5 rounded-xl bg-oxblood/20 border border-oxblood/40">
                      <p className="text-[10px] uppercase font-bold text-oxblood dark:text-rose">Missing</p>
                      <p className="text-base font-bold text-oxblood dark:text-rose">
                        {Math.max(0, autoGenForm.total_questions - availability.total_available)}
                      </p>
                    </div>
                  </div>

                  <p className="text-[11px] font-sans text-slate/70 dark:text-ivory/70 leading-snug">
                    The Question Bank does not yet have enough approved questions for <strong>{autoGenForm.technology}</strong> {autoGenForm.topic ? `(${autoGenForm.topic})` : '(All Topics)'}.
                    Upload an exam or question file to immediately enrich the bank, or browse existing questions to adjust criteria.
                  </p>

                  {/* Actions: Upload Question File & Browse Question Bank */}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setUploadModalContext('auto_generate');
                        setShowUploadFileModal(true);
                      }}
                      className="flex-1 min-w-[150px] px-3.5 py-2.5 rounded-xl bg-oxblood text-ivory hover:bg-oxblood/90 font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-sm min-h-[40px]"
                    >
                      <Upload size={14} /> Upload Question File
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setBankTech(autoGenForm.technology);
                        setBankSearch('');
                        setBankDifficulty('');
                        setSelectedBankQuestions([]);
                        fetchBankQuestionsForImport();
                        setBankPickerContext('auto_generate');
                        setShowAddFromBankModal(true);
                      }}
                      className="flex-1 min-w-[150px] px-3.5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/20 text-charcoal dark:text-ivory font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 border border-slate/20 min-h-[40px]"
                    >
                      <Database size={14} /> Browse Question Bank
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* Question Count Presets & Custom Input */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="block text-[10px] uppercase font-bold text-slate/50">
                Number of Questions *
              </label>
              <span className="text-[10px] text-slate/50">Quick Presets: 5 &bull; 10 &bull; 15 &bull; 20 &bull; 25 &bull; 30</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {[5, 10, 15, 20, 25, 30].map((presetCount) => {
                const isSelected = autoGenForm.total_questions === presetCount;
                const isTooHigh = availability && presetCount > availability.total_available;
                return (
                  <button
                    key={presetCount}
                    type="button"
                    onClick={() => {
                      const marksPerQ = autoGenForm.uniform_marks_enabled ? (autoGenForm.marks_per_question || 1) : 1;
                      setAutoGenForm({
                        ...autoGenForm,
                        total_questions: presetCount,
                        passing_marks: Math.max(1, Math.round(presetCount * marksPerQ * 0.6))
                      });
                    }}
                    disabled={isTooHigh}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
                      isSelected
                        ? 'bg-oxblood text-ivory shadow-sm'
                        : isTooHigh
                        ? 'bg-slate/5 text-slate/30 border border-slate/10 cursor-not-allowed'
                        : 'bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory'
                    }`}
                  >
                    {presetCount} Questions
                  </button>
                );
              })}
              <div className="flex items-center gap-1.5 ml-auto">
                <span className="text-[10px] text-slate/50">Custom:</span>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={autoGenForm.total_questions}
                  onChange={(e) => {
                    const val = Math.max(1, parseInt(e.target.value, 10) || 1);
                    const marksPerQ = autoGenForm.uniform_marks_enabled ? (autoGenForm.marks_per_question || 1) : 1;
                    setAutoGenForm({
                      ...autoGenForm,
                      total_questions: val,
                      passing_marks: Math.max(1, Math.round(val * marksPerQ * 0.6))
                    });
                  }}
                  className="w-16 bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-lg px-2 py-1 text-xs text-center font-bold"
                />
              </div>
            </div>
          </div>

          {/* Duration & Marks Configuration */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
                Duration (Minutes) *
              </label>
              <input
                type="number"
                min="5"
                max="180"
                value={autoGenForm.duration_minutes}
                onChange={(e) => setAutoGenForm({ ...autoGenForm, duration_minutes: parseInt(e.target.value, 10) || 30 })}
                required
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
                Marks Per Question *
              </label>
              <select
                value={autoGenForm.marks_per_question}
                onChange={(e) => {
                  const m = parseInt(e.target.value, 10) || 1;
                  setAutoGenForm({
                    ...autoGenForm,
                    marks_per_question: m,
                    passing_marks: Math.max(1, Math.round(autoGenForm.total_questions * m * 0.6))
                  });
                }}
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
              >
                <option value="1" className="bg-charcoal text-ivory">1 Mark (Default Uniform)</option>
                <option value="2" className="bg-charcoal text-ivory">2 Marks</option>
                <option value="3" className="bg-charcoal text-ivory">3 Marks</option>
                <option value="5" className="bg-charcoal text-ivory">5 Marks</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] uppercase font-bold text-slate/50">
                  Target Passing Marks *
                </label>
                <span className="text-[9px] text-oxblood dark:text-rose font-bold">
                  Total: {autoGenForm.total_questions * (autoGenForm.marks_per_question || 1)}m
                </span>
              </div>
              <input
                type="number"
                min="1"
                max={autoGenForm.total_questions * (autoGenForm.marks_per_question || 1)}
                value={autoGenForm.passing_marks}
                onChange={(e) => setAutoGenForm({ ...autoGenForm, passing_marks: parseInt(e.target.value, 10) || 1 })}
                required
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs min-h-[40px]"
              />
            </div>
          </div>

          {/* Difficulty Distribution with Presets */}
          <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px] font-bold">
              <div className="flex items-center gap-2 flex-wrap">
                <span>Difficulty Distribution (%):</span>
                <div className="flex gap-1.5 text-[9px]">
                  <button
                    type="button"
                    onClick={() => setAutoGenForm({ ...autoGenForm, beginner_pct: 40, intermediate_pct: 40, advanced_pct: 20 })}
                    className="px-2 py-0.5 rounded bg-slate/10 dark:bg-white/10 hover:bg-slate/20"
                  >
                    Balanced (40/40/20)
                  </button>
                  <button
                    type="button"
                    onClick={() => setAutoGenForm({ ...autoGenForm, beginner_pct: 60, intermediate_pct: 30, advanced_pct: 10 })}
                    className="px-2 py-0.5 rounded bg-slate/10 dark:bg-white/10 hover:bg-slate/20"
                  >
                    Foundational (60/30/10)
                  </button>
                  <button
                    type="button"
                    onClick={() => setAutoGenForm({ ...autoGenForm, beginner_pct: 20, intermediate_pct: 40, advanced_pct: 40 })}
                    className="px-2 py-0.5 rounded bg-slate/10 dark:bg-white/10 hover:bg-slate/20"
                  >
                    Challenging (20/40/40)
                  </button>
                </div>
              </div>
              <span className={
                (Number(autoGenForm.beginner_pct) + Number(autoGenForm.intermediate_pct) + Number(autoGenForm.advanced_pct)) === 100
                  ? 'text-success' : 'text-rose'
              }>
                Total: {Number(autoGenForm.beginner_pct) + Number(autoGenForm.intermediate_pct) + Number(autoGenForm.advanced_pct)}% / 100%
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <label className="block text-[9px] uppercase text-slate/50">Beginner %</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={autoGenForm.beginner_pct}
                  onChange={(e) => setAutoGenForm({ ...autoGenForm, beginner_pct: parseInt(e.target.value, 10) || 0 })}
                  className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg p-1.5 text-center"
                />
              </div>

              <div>
                <label className="block text-[9px] uppercase text-slate/50">Intermediate %</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={autoGenForm.intermediate_pct}
                  onChange={(e) => setAutoGenForm({ ...autoGenForm, intermediate_pct: parseInt(e.target.value, 10) || 0 })}
                  className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg p-1.5 text-center"
                />
              </div>

              <div>
                <label className="block text-[9px] uppercase text-slate/50">Advanced %</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={autoGenForm.advanced_pct}
                  onChange={(e) => setAutoGenForm({ ...autoGenForm, advanced_pct: parseInt(e.target.value, 10) || 0 })}
                  className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg p-1.5 text-center"
                />
              </div>
            </div>
          </div>

          {/* Randomization toggles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <label className="flex items-center gap-2 p-2.5 rounded-xl bg-white/5 border border-slate/10 cursor-pointer">
              <input
                type="checkbox"
                checked={autoGenForm.randomize_questions}
                onChange={(e) => setAutoGenForm({ ...autoGenForm, randomize_questions: e.target.checked })}
                className="w-4 h-4 text-oxblood rounded cursor-pointer"
              />
              <div>
                <p className="font-bold text-charcoal dark:text-ivory">Shuffle Questions</p>
                <p className="text-[10px] text-slate/50">Individualized order per attempt</p>
              </div>
            </label>

            <label className="flex items-center gap-2 p-2.5 rounded-xl bg-white/5 border border-slate/10 cursor-pointer">
              <input
                type="checkbox"
                checked={autoGenForm.randomize_options}
                onChange={(e) => setAutoGenForm({ ...autoGenForm, randomize_options: e.target.checked })}
                className="w-4 h-4 text-oxblood rounded cursor-pointer"
              />
              <div>
                <p className="font-bold text-charcoal dark:text-ivory">Shuffle Options (A-D)</p>
                <p className="text-[10px] text-slate/50">Permutes choice positions</p>
              </div>
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate/15">
            <button
              type="button"
              onClick={() => setShowAutoGenerateModal(false)}
              className="px-4 py-2 rounded-xl bg-slate/10 text-xs uppercase min-h-[40px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={autoGenLoading || (availability && availability.total_available < autoGenForm.total_questions)}
              title={
                availability && availability.total_available < autoGenForm.total_questions
                  ? `Cannot generate assessment: missing ${Math.max(0, autoGenForm.total_questions - availability.total_available)} question(s). Upload question file or browse bank.`
                  : 'Generate Assessment'
              }
              className="px-5 py-2 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase min-h-[40px] flex items-center gap-1.5 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {autoGenLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Sampling Bank...
                </>
              ) : (
                <>
                  <Sparkles size={14} /> Generate Draft Assessment
                </>
              )}
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 2: ASSESSMENT PREVIEW */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showPreviewModal}
        onClose={() => setShowPreviewModal(false)}
        title="Assessment Preview"
      >
        {previewData && (
          <div className="space-y-6 text-charcoal dark:text-ivory">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-mono text-slate/60 dark:text-ivory/50 uppercase">
                  {previewData.job_title}
                </span>
                {renderStatusBadge(previewData.status)}
              </div>
              <h3 className="text-xl font-display font-bold">{previewData.title}</h3>
              {previewData.instructions && (
                <p className="text-xs font-mono text-slate/70 dark:text-ivory/60 mt-1">
                  {previewData.instructions}
                </p>
              )}
            </div>

            <div className="flex gap-4 p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 text-xs font-mono">
              <span><strong>Duration:</strong> {previewData.duration_minutes} min</span>
              <span><strong>Total:</strong> {previewData.total_marks} marks</span>
              <span><strong>Passing:</strong> {previewData.passing_marks} marks</span>
            </div>

            <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
              {previewData.questions?.map((q, idx) => (
                <div key={q.id} className="p-4 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="font-bold">Q{idx + 1}. {q.question_text}</span>
                    <span className="text-oxblood dark:text-rose font-bold">{q.marks} Mark(s)</span>
                  </div>
                  <div className="space-y-1 pl-4">
                    {q.options.map((opt) => (
                      <div
                        key={opt.id}
                        className={`p-2 rounded-lg text-xs font-sans flex items-center justify-between ${
                          opt.is_correct
                            ? 'bg-success/15 border border-success/30 text-success font-semibold'
                            : 'text-slate/70 dark:text-ivory/70'
                        }`}
                      >
                        <span>{opt.option_key}. {opt.option_text}</span>
                        {opt.is_correct && (
                          <span className="text-[10px] font-mono uppercase bg-success/20 px-2 py-0.5 rounded">
                            Correct Answer
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate/15 dark:border-white/10">
              <button
                onClick={() => setShowPreviewModal(false)}
                className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase tracking-wider min-h-[44px]"
              >
                Close Preview
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 3: ASSIGN TO SHORTLISTED CANDIDATES */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        title="Assign Assessment to Shortlisted Candidates"
      >
        <div className="space-y-5 text-charcoal dark:text-ivory">
          <div>
            <p className="text-xs font-mono text-slate/70 dark:text-ivory/60">
              Only candidates with <span className="font-bold text-oxblood dark:text-rose">SHORTLISTED</span> status for{' '}
              <span className="font-semibold text-charcoal dark:text-ivory">{currentAssignAssessment?.job_title}</span> can be assigned.
            </p>
          </div>

          {shortlistedCandidates.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-slate/5 dark:bg-white/5 border border-dashed border-slate/20 dark:border-white/10 space-y-2">
              <Users className="w-8 h-8 text-slate/40 dark:text-ivory/40 mx-auto" />
              <p className="text-xs font-mono text-slate/60 dark:text-ivory/50">
                No shortlisted candidates found for this job opening.
              </p>
              <p className="text-[11px] font-mono text-slate/40 dark:text-ivory/40">
                Go to the Candidate Pipeline tab to shortlist applicants first.
              </p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[45vh] overflow-y-auto pr-1">
              {shortlistedCandidates.map((cand) => {
                const isSelected = selectedCandidateIds.includes(cand.candidate_id);
                return (
                  <div
                    key={cand.candidate_id}
                    onClick={() => !cand.is_assigned && handleToggleCandidateSelect(cand.candidate_id)}
                    className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                      cand.is_assigned
                        ? 'opacity-60 bg-slate/5 dark:bg-white/5 border-slate/10 dark:border-white/5 cursor-not-allowed'
                        : isSelected
                        ? 'bg-oxblood/15 border-oxblood cursor-pointer'
                        : 'bg-white/5 border-slate/10 dark:border-white/10 hover:bg-white/10 cursor-pointer'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        disabled={cand.is_assigned}
                        checked={isSelected || cand.is_assigned}
                        onChange={() => {}}
                        className="w-4 h-4 text-oxblood rounded cursor-pointer"
                      />
                      <div>
                        <p className="text-xs font-bold text-charcoal dark:text-ivory">{cand.candidate_name}</p>
                        <p className="text-[11px] font-mono text-slate/50 dark:text-ivory/40">{cand.candidate_email}</p>
                      </div>
                    </div>

                    <div>
                      {cand.is_assigned ? (
                        <span className="text-[10px] font-mono text-success flex items-center gap-1 font-semibold">
                          <Check size={12} /> Already Assigned ({cand.assignment_status})
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono text-slate/50 dark:text-ivory/40 uppercase">
                          Ready to Assign
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex justify-between items-center pt-3 border-t border-slate/15 dark:border-white/10">
            <span className="text-xs font-mono text-slate/60 dark:text-ivory/50">
              Selected: <strong className="text-charcoal dark:text-ivory">{selectedCandidateIds.length}</strong> candidate(s)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase tracking-wider min-h-[44px]"
              >
                Cancel
              </button>
              <button
                onClick={handleAssignCandidatesSubmit}
                disabled={isAssigning || selectedCandidateIds.length === 0}
                className="px-5 py-2 rounded-xl bg-oxblood hover:bg-oxblood/80 disabled:opacity-40 disabled:cursor-not-allowed text-ivory text-xs font-mono font-bold uppercase tracking-wider shadow-md shadow-oxblood/20 min-h-[44px]"
              >
                {isAssigning ? 'Assigning...' : 'Confirm Assignment'}
              </button>
            </div>
          </div>
        </div>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 4: ASSESSMENT RESULTS & CANDIDATE SCORES */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showResultsModal}
        onClose={() => setShowResultsModal(false)}
        title={`Results — ${resultsAssessment?.title || 'Assessment'}`}
      >
        <div className="space-y-5 text-charcoal dark:text-ivory">
          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {['all', 'assigned', 'in_progress', 'passed', 'failed', 'expired'].map((f) => (
              <button
                key={f}
                onClick={() => {
                  setResultFilter(f);
                  fetchResults(resultsAssessment.id, f);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold uppercase tracking-wider transition-all min-h-[36px] ${
                  resultFilter === f
                    ? 'bg-oxblood text-ivory'
                    : 'bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-slate/70 dark:text-ivory/60'
                }`}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Results Table */}
          {resultsLoading ? (
            <div className="min-h-[150px] flex items-center justify-center font-mono text-xs">
              Loading candidates...
            </div>
          ) : candidateResults.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-slate/5 dark:bg-white/5 border border-dashed border-slate/20 dark:border-white/10">
              <p className="text-xs font-mono text-slate/50 dark:text-ivory/40">
                No candidate records match the selected filter.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
              {candidateResults.map((rec) => (
                <div
                  key={rec.id}
                  className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-bold text-charcoal dark:text-ivory">{rec.candidate_name}</p>
                      {renderStatusBadge(rec.status)}
                    </div>
                    <p className="text-[11px] font-mono text-slate/50 dark:text-ivory/40">{rec.candidate_email}</p>
                    <p className="text-[10px] font-mono text-slate/40 dark:text-ivory/30 mt-0.5">
                      Assigned: {new Date(rec.assigned_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    {rec.is_completed ? (
                      <div className="text-right font-mono">
                        <p className={`text-sm font-bold ${rec.result === 'PASSED' ? 'text-success' : 'text-rose'}`}>
                          {rec.marks_obtained} / {rec.total_marks} ({rec.percentage}%)
                        </p>
                        <p className="text-[10px] uppercase text-slate/50 dark:text-ivory/40">
                          {rec.result}
                        </p>
                      </div>
                    ) : (
                      <span className="text-xs font-mono text-slate/40 dark:text-ivory/40 italic">
                        {rec.has_started ? 'In Progress' : 'Not Started'}
                      </span>
                    )}

                    {rec.has_started && (
                      <button
                        onClick={() => handleOpenAnswerReview(rec.id)}
                        className="px-3 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-xs font-mono font-semibold flex items-center gap-1 min-h-[36px]"
                      >
                        <Eye size={13} /> Answers
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end pt-3 border-t border-slate/15 dark:border-white/10">
            <button
              onClick={() => setShowResultsModal(false)}
              className="px-5 py-2 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase tracking-wider min-h-[44px]"
            >
              Close
            </button>
          </div>
        </div>
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 5: DETAILED CANDIDATE ANSWER INSPECTION */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        title={`Candidate Submission — ${reviewData?.candidate_name || 'Review'}`}
      >
        {reviewLoading ? (
          <div className="p-8 text-center font-mono text-xs">Loading answers...</div>
        ) : reviewData ? (
          <div className="space-y-5 text-charcoal dark:text-ivory">
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold">{reviewData.candidate_name}</h4>
                <p className="text-xs font-mono text-slate/50 dark:text-ivory/40">{reviewData.candidate_email}</p>
              </div>
              <div className="text-right font-mono">
                <p className={`text-base font-bold ${reviewData.result === 'PASSED' ? 'text-success' : 'text-rose'}`}>
                  {reviewData.marks_obtained} / {reviewData.total_marks} ({reviewData.percentage}%)
                </p>
                <span className={`text-[10px] font-bold uppercase ${reviewData.result === 'PASSED' ? 'text-success' : 'text-rose'}`}>
                  {reviewData.result}
                </span>
              </div>
            </div>

            <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
              {reviewData.answers?.map((ans, idx) => (
                <div
                  key={ans.question_id}
                  className={`p-4 rounded-xl border space-y-2 ${
                    ans.is_correct
                      ? 'bg-success/5 border-success/20'
                      : 'bg-oxblood/5 border-rose/20'
                  }`}
                >
                  <div className="flex justify-between items-start text-xs font-mono">
                    <span className="font-bold">Q{idx + 1}. {ans.question_text}</span>
                    <span className={`font-bold ${ans.is_correct ? 'text-success' : 'text-rose'}`}>
                      {ans.marks_awarded} / {ans.marks} Marks
                    </span>
                  </div>

                  <div className="space-y-1.5 pl-3 pt-1">
                    {ans.options?.map((opt) => {
                      const isSelected = ans.selected_option_id === opt.id;
                      const isCorrect = opt.id === ans.correct_option_id;

                      let badgeClass = 'text-slate/70 dark:text-ivory/70';
                      if (isCorrect) badgeClass = 'bg-success/20 text-success border border-success/30 font-semibold';
                      else if (isSelected && !isCorrect) badgeClass = 'bg-oxblood/30 text-rose border border-rose/30 font-semibold';

                      return (
                        <div
                          key={opt.id}
                          className={`p-2 rounded-lg text-xs font-sans flex items-center justify-between ${badgeClass}`}
                        >
                          <span>{opt.option_key}. {opt.option_text}</span>
                          <span className="text-[10px] font-mono uppercase">
                            {isCorrect && isSelected && '✓ Correct & Selected'}
                            {isCorrect && !isSelected && '✓ Correct Answer'}
                            {!isCorrect && isSelected && '✗ Candidate Answer'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate/15 dark:border-white/10">
              <button
                onClick={() => setShowReviewModal(false)}
                className="px-5 py-2 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase tracking-wider min-h-[44px]"
              >
                Close Review
              </button>
            </div>
          </div>
        ) : null}
      </GlassModal>

      {/* ==================================================================== */}
      {/* MODAL 6: RECRUITER ASSESSMENT PERFORMANCE ANALYTICS */}
      {/* ==================================================================== */}
      <AssessmentAnalyticsModal
        isOpen={showAnalyticsModal}
        onClose={() => {
          setShowAnalyticsModal(false);
          setAnalyticsAssessment(null);
        }}
        assessmentId={analyticsAssessment?.id}
        assessmentTitle={analyticsAssessment?.title}
      />

      {/* ==================================================================== */}
      {/* MODAL 7: INLINE QUESTION FILE UPLOADER & EXTRACTION PREVIEW */}
      {/* ==================================================================== */}
      <InlineQuestionUploadModal
        isOpen={showUploadFileModal}
        onClose={() => setShowUploadFileModal(false)}
        technologyHint={uploadModalContext === 'auto_generate' ? autoGenForm.technology : (bankTech || 'Python')}
        topicHint={uploadModalContext === 'auto_generate' ? autoGenForm.topic : ''}
        onSuccess={handleUploadSuccess}
      />
    </div>
  );
};

export default RecruiterAssessmentsSection;
