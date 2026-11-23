import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { recruiterAPI, jobsAPI, applicationAPI, resumeAPI, interviewsAPI, evaluationsAPI, messagesAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  PageTransition,
  GlassModal,
  AnimatedCounter,
  AnimatedProgressRing,
  LiquidSpotlightCard,
  MagneticButton,
  StaggerContainer,
  StaggerItem,
  useToast,
  usePrefersReducedMotion
} from '../components/MotionComponents';
import {
  Briefcase, Users, Plus, Building, FileText, CheckCircle2,
  X, Filter, MapPin, RefreshCw, AlertCircle, Eye, ExternalLink,
  Download, ArrowUpRight, Check, Award, Search, Phone, Mail,
  Calendar, Trash2, ArrowRight, MessageSquare, Send, Star, Columns,
  List, Sparkles, SlidersHorizontal, UserCheck, Video, PhoneCall,
  History, CheckCheck, BarChart3, HelpCircle, Clock, ChevronRight, Film, LifeBuoy
} from 'lucide-react';
import { RecruiterAssessmentsSection } from '../components/RecruiterAssessmentsSection';
import { RecruiterMediaLibraryTab } from '../components/RecruiterMediaLibraryTab';
import { RecruiterVideoAssessmentsTab } from '../components/RecruiterVideoAssessmentsTab';
import { RecruiterInterviewHubTab } from '../components/RecruiterInterviewHubTab';
import { CandidateDossierModal } from '../components/CandidateDossierModal';
import { UserSupportTicketsTab } from '../components/UserSupportTicketsTab';

const VALID_RECRUITER_TABS = ['jobs', 'pipeline', 'assessments', 'video-assessments', 'interviews', 'media', 'messages', 'analytics', 'company', 'tickets'];

export const RecruiterDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const shouldReduceMotion = usePrefersReducedMotion();
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get('tab');
  const activeTab = useMemo(() => {
    return VALID_RECRUITER_TABS.includes(rawTab) ? rawTab : 'jobs';
  }, [rawTab]);

  // Jobs state
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [showJobModal, setShowJobModal] = useState(false);
  const [jobSearch, setJobSearch] = useState('');

  // New Job Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [jobType, setJobType] = useState('FULL_TIME');
  const [postStatus, setPostStatus] = useState('ACTIVE');
  const [expMin, setExpMin] = useState(1);
  const [expMax, setExpMax] = useState(4);
  const [salMin, setSalMin] = useState(1000000);
  const [salMax, setSalMax] = useState(1800000);
  const [requiredSkills, setRequiredSkills] = useState([]);
  const [skillInput, setSkillInput] = useState('');
  const [creatingJob, setCreatingJob] = useState(false);
  const [jobFormError, setJobFormError] = useState('');

  // Applicants state
  const [applicants, setApplicants] = useState([]);
  const [applicantsLoading, setApplicantsLoading] = useState(false);
  const [filterJobId, setFilterJobId] = useState(searchParams.get('jobId') || '');
  const [filterStatus, setFilterStatus] = useState('');
  const [candidateSearch, setCandidateSearch] = useState('');
  const [selectedApplicant, setSelectedApplicant] = useState(null);
  const [showApplicantModal, setShowApplicantModal] = useState(false);
  const [dossierCandidateId, setDossierCandidateId] = useState(null);

  // Company state
  const [company, setCompany] = useState(null);
  const [companyName, setCompanyName] = useState('');
  const [companyDesc, setCompanyDesc] = useState('');
  const [companyWeb, setCompanyWeb] = useState('');
  const [companyLoc, setCompanyLoc] = useState('');
  const [companyEmail, setCompanyEmail] = useState('');
  const [companyLogo, setCompanyLogo] = useState('');
  const [savingCompany, setSavingCompany] = useState(false);
  const [companySuccess, setCompanySuccess] = useState('');

  // Pipeline View Mode ('kanban' | 'table')
  const [pipelineView, setPipelineView] = useState('kanban');

  // Recruiter Analytics state
  const [recruiterAnalytics, setRecruiterAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // Recruiter Interviews state
  const [recruiterInterviews, setRecruiterInterviews] = useState([]);
  const [interviewsLoading, setInterviewsLoading] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [schedDate, setSchedDate] = useState('');
  const [schedTime, setSchedTime] = useState('14:00');
  const [schedDuration, setSchedDuration] = useState(45);
  const [schedType, setSchedType] = useState('ONLINE');
  const [schedMode, setSchedMode] = useState('HUMAN'); // HUMAN, AI_LIVE, HYBRID, CONFIGURED
  const [schedLink, setSchedLink] = useState('');
  const [schedLocation, setSchedLocation] = useState('');
  const [schedInstructions, setSchedInstructions] = useState('');
  const [scheduling, setScheduling] = useState(false);
  const [schedDifficulty, setSchedDifficulty] = useState('INTERMEDIATE');
  const [schedVoice, setSchedVoice] = useState('alloy');
  const [schedAllowTakeover, setSchedAllowTakeover] = useState(true);
  const [schedRecordingConsent, setSchedRecordingConsent] = useState(true);
  const [schedQuestions, setSchedQuestions] = useState([]);
  const [schedGeneratingQuestions, setSchedGeneratingQuestions] = useState(false);
  const [schedNewQuestionText, setSchedNewQuestionText] = useState('');
  const [schedNewQuestionType, setSchedNewQuestionType] = useState('TECHNICAL');

  // Candidate Evaluation Scorecard state
  const [techRating, setTechRating] = useState(4);
  const [commRating, setCommRating] = useState(4);
  const [expRating, setExpRating] = useState(4);
  const [recommendation, setRecommendation] = useState('HIRE');
  const [evalFeedback, setEvalFeedback] = useState('');
  const [submittingEval, setSubmittingEval] = useState(false);
  const [candidateEvals, setCandidateEvals] = useState([]);

  // Candidate Comparison Matrix state
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [compareData, setCompareData] = useState([]);
  const [compareLoading, setCompareLoading] = useState(false);

  // Recruiter Private Notes & History state
  const [internalNotes, setInternalNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [statusHistory, setStatusHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Direct Candidate Messaging state
  const [conversations, setConversations] = useState([]);
  const [activePartner, setActivePartner] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [messageText, setMessageText] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchApplicants();
    fetchCompany();
    fetchRecruiterAnalytics();
    fetchRecruiterInterviews();
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedApplicant) {
      setInternalNotes(selectedApplicant.recruiter_notes || '');
      fetchApplicationHistory(selectedApplicant.id);
      fetchApplicationEvaluations(selectedApplicant.id);
    }
  }, [selectedApplicant]);

  useEffect(() => {
    if (activePartner) {
      fetchThread(activePartner.partner_id || activePartner.id);
    }
  }, [activePartner]);

  const fetchRecruiterAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const res = await recruiterAPI.getAnalytics();
      setRecruiterAnalytics(res.data);
    } catch (err) {
      console.error("Failed to load recruiter analytics:", err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchRecruiterInterviews = async () => {
    try {
      setInterviewsLoading(true);
      const res = await interviewsAPI.getMy();
      setRecruiterInterviews(res.data || []);
    } catch (err) {
      console.error("Failed to load recruiter interviews:", err);
    } finally {
      setInterviewsLoading(false);
    }
  };

  const fetchApplicationHistory = async (appId) => {
    try {
      setHistoryLoading(true);
      const res = await applicationAPI.getHistory(appId);
      setStatusHistory(res.data || []);
    } catch (err) {
      console.error("Failed to load application history:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const fetchApplicationEvaluations = async (appId) => {
    try {
      const res = await evaluationsAPI.getByApplication(appId);
      setCandidateEvals(res.data || []);
    } catch (err) {
      console.error("Failed to load candidate evaluations:", err);
    }
  };

  const handleSaveNotes = async () => {
    if (!selectedApplicant) return;
    setSavingNotes(true);
    try {
      await applicationAPI.updateNotes(selectedApplicant.id, internalNotes);
      addToast("Internal recruiter notes saved successfully!", "success");
      setSelectedApplicant(prev => ({ ...prev, recruiter_notes: internalNotes }));
      setApplicants(prev => prev.map(a => a.id === selectedApplicant.id ? { ...a, recruiter_notes: internalNotes } : a));
    } catch (err) {
      console.error("Failed to save notes:", err);
      addToast("Failed to save internal notes", "error");
    } finally {
      setSavingNotes(false);
    }
  };

  const handleSubmitEvaluation = async (e) => {
    if (e) e.preventDefault();
    if (!selectedApplicant) return;
    setSubmittingEval(true);
    try {
      await evaluationsAPI.submit({
        application_id: selectedApplicant.id,
        technical_rating: Number(techRating),
        communication_rating: Number(commRating),
        experience_rating: Number(expRating),
        overall_recommendation: recommendation,
        feedback: evalFeedback
      });
      addToast("Candidate evaluation scorecard submitted!", "success");
      fetchApplicationEvaluations(selectedApplicant.id);
      setEvalFeedback('');
    } catch (err) {
      console.error("Failed to submit evaluation:", err);
      addToast(err.response?.data?.detail || "Failed to submit evaluation", "error");
    } finally {
      setSubmittingEval(false);
    }
  };

  const handleOpenCompare = async (jobId) => {
    setShowCompareModal(true);
    setCompareLoading(true);
    try {
      const res = await evaluationsAPI.compareCandidates(jobId);
      setCompareData(res.data || []);
    } catch (err) {
      console.error("Failed to compare candidates:", err);
      addToast("Failed to fetch candidate comparison matrix", "error");
    } finally {
      setCompareLoading(false);
    }
  };

  const handleGenerateSchedQuestions = async () => {
    if (!selectedApplicant) return;
    setSchedGeneratingQuestions(true);
    try {
      const res = await interviewsAPI.generateAIQuestions({
        application_id: selectedApplicant.id,
        difficulty: schedDifficulty,
        question_count: 4,
        categories: ['TECHNICAL', 'PROBLEM_SOLVING', 'BEHAVIORAL', 'ROLE_SPECIFIC']
      });
      setSchedQuestions(res.data || []);
      addToast(`Generated ${res.data?.length || 0} tailored interview questions!`, "success");
    } catch (err) {
      console.error("Failed to generate questions:", err);
      addToast("Failed to generate AI questions", "error");
    } finally {
      setSchedGeneratingQuestions(false);
    }
  };

  const handleScheduleInterview = async (e) => {
    if (e) e.preventDefault();
    if (!selectedApplicant || !schedDate) {
      addToast("Please select interview date and time", "warning");
      return;
    }
    setScheduling(true);
    try {
      const scheduledAtIso = new Date(`${schedDate}T${schedTime || '14:00'}:00`).toISOString();
      await interviewsAPI.schedule({
        application_id: selectedApplicant.id,
        scheduled_time: scheduledAtIso,
        scheduled_at: scheduledAtIso,
        duration_minutes: Number(schedDuration),
        interview_type: schedType,
        interview_mode: schedMode,
        meeting_link: schedLink,
        location: schedLocation,
        instructions: schedInstructions,
        recording_enabled: schedRecordingConsent,
        voice: schedVoice,
        difficulty: schedDifficulty,
        allow_recruiter_takeover: schedAllowTakeover,
        questions: schedQuestions.length > 0 ? schedQuestions : undefined
      });
      addToast(`Interview scheduled with ${selectedApplicant.candidate?.name || 'Candidate'}!`, "success");
      setShowScheduleModal(false);
      setSchedQuestions([]);
      setSchedNewQuestionText('');
      fetchRecruiterInterviews();
      if (selectedApplicant.status !== 'INTERVIEW') {
        handleStatusChange(selectedApplicant.id, 'INTERVIEW');
      }
    } catch (err) {
      console.error("Failed to schedule interview:", err);
      addToast(err.response?.data?.detail || "Failed to schedule interview", "error");
    } finally {
      setScheduling(false);
    }
  };

  const [resendingEmailId, setResendingEmailId] = useState(null);

  const handleInterviewStatusChange = async (interviewId, newStatus) => {
    try {
      await interviewsAPI.update(interviewId, { status: newStatus });
      addToast(`Interview marked as ${newStatus}`, "success");
      fetchRecruiterInterviews();
    } catch (err) {
      console.error("Failed to update interview:", err);
      addToast("Failed to update interview status", "error");
    }
  };

  const handleResendInterviewEmail = async (interviewId) => {
    try {
      setResendingEmailId(interviewId);
      const res = await interviewsAPI.resendEmail(interviewId);
      addToast('Interview invitation email dispatched via Brevo!', 'success');
      setRecruiterInterviews((prev) =>
        prev.map((i) => (i.id === interviewId ? { ...i, ...res.data } : i))
      );
    } catch (err) {
      console.error('Failed to resend interview email:', err);
      addToast(err.response?.data?.detail || 'Failed to resend invitation email.', 'error');
    } finally {
      setResendingEmailId(null);
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await messagesAPI.getConversations();
      setConversations(res.data || []);
      if (res.data && res.data.length > 0 && !activePartner) {
        setActivePartner(res.data[0]);
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const fetchThread = async (partnerId) => {
    try {
      setChatLoading(true);
      const res = await messagesAPI.getThread(partnerId);
      setChatMessages(res.data || []);
    } catch (err) {
      console.error("Failed to load thread:", err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!messageText.trim() || !activePartner) return;
    const partnerId = activePartner.partner_id || activePartner.id;
    setSendingMessage(true);
    try {
      const res = await messagesAPI.send({
        receiver_id: partnerId,
        content: messageText.trim()
      });
      setChatMessages(prev => [...prev, res.data]);
      setMessageText('');
      fetchConversations();
    } catch (err) {
      console.error("Failed to send message:", err);
      addToast("Failed to send message", "error");
    } finally {
      setSendingMessage(false);
    }
  };

  const setTab = (tabName, extraParams = {}) => {
    const newParams = { tab: tabName, ...extraParams };
    setSearchParams(newParams);
  };

  const fetchJobs = async () => {
    try {
      setJobsLoading(true);
      const res = await recruiterAPI.getJobs();
      setJobs(res.data || []);
    } catch (err) {
      console.error("Failed to load recruiter jobs:", err);
      addToast("Failed to fetch recruiter job postings.", "error");
    } finally {
      setJobsLoading(false);
    }
  };

  const fetchApplicants = async (jobId = filterJobId, status = filterStatus) => {
    try {
      setApplicantsLoading(true);
      const params = {};
      if (jobId) params.job_id = jobId;
      if (status) params.status = status;
      const res = await recruiterAPI.getApplicants(params);
      setApplicants(res.data || []);
    } catch (err) {
      console.error("Failed to load applicants:", err);
      addToast("Failed to fetch candidate applications.", "error");
    } finally {
      setApplicantsLoading(false);
    }
  };

  const fetchCompany = async () => {
    try {
      const res = await recruiterAPI.getCompany();
      if (res.data) {
        setCompany(res.data);
        setCompanyName(res.data.company_name || '');
        setCompanyDesc(res.data.description || '');
        setCompanyWeb(res.data.website || '');
        setCompanyLoc(res.data.location || '');
        setCompanyEmail(res.data.contact_email || '');
        setCompanyLogo(res.data.logo_url || '');
      }
    } catch (err) {
      console.error("Failed to load company:", err);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setCreatingJob(true);
    setJobFormError('');

    const parsedExpMin = (expMin !== '' && !isNaN(parseFloat(expMin))) ? parseFloat(expMin) : 0.0;
    const parsedExpMax = (expMax !== '' && !isNaN(parseFloat(expMax))) ? parseFloat(expMax) : 0.0;
    const parsedSalMin = (salMin !== '' && !isNaN(parseFloat(salMin))) ? parseFloat(salMin) : null;
    const parsedSalMax = (salMax !== '' && !isNaN(parseFloat(salMax))) ? parseFloat(salMax) : null;

    if (parsedExpMin > parsedExpMax) {
      setJobFormError("Minimum experience cannot be greater than maximum experience.");
      setCreatingJob(false);
      return;
    }

    if (parsedSalMin !== null && parsedSalMax !== null && parsedSalMin > parsedSalMax) {
      setJobFormError("Minimum salary cannot be greater than maximum salary.");
      setCreatingJob(false);
      return;
    }

    try {
      await jobsAPI.create({
        title,
        description,
        location,
        job_type: jobType,
        experience_min: parsedExpMin,
        experience_max: parsedExpMax,
        salary_min: parsedSalMin,
        salary_max: parsedSalMax,
        status: postStatus,
        required_skills: requiredSkills,
      });

      setShowJobModal(false);
      resetJobForm();
      const actionMsg = postStatus === 'DRAFT' ? 'saved as draft' : 'published';
      addToast(`Job opening '${title}' ${actionMsg} successfully!`, "success");
      fetchJobs();
    } catch (err) {
      console.error("Job creation error:", err);
      const detail = err.response?.data?.detail;
      let errorMsg = "Failed to create job posting.";
      if (typeof detail === 'string') {
        errorMsg = detail;
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map(d => `${d.loc?.slice(1).join('.') || 'field'}: ${d.msg}`).join(' | ');
      }
      setJobFormError(errorMsg);
      addToast(errorMsg, "error");
    } finally {
      setCreatingJob(false);
    }
  };

  const handlePublishJob = async (jobId) => {
    try {
      await jobsAPI.update(jobId, { status: 'ACTIVE' });
      addToast("Job opening published successfully!", "success");
      fetchJobs();
    } catch (err) {
      console.error("Failed to publish job:", err);
      addToast(err.response?.data?.detail || "Failed to publish job opening.", "error");
    }
  };

  const handleReopenJob = async (jobId) => {
    try {
      await jobsAPI.update(jobId, { status: 'ACTIVE' });
      addToast("Job opening reopened and active!", "success");
      fetchJobs();
    } catch (err) {
      console.error("Failed to reopen job:", err);
      addToast(err.response?.data?.detail || "Failed to reopen job opening.", "error");
    }
  };

  const resetJobForm = () => {
    setTitle('');
    setDescription('');
    setLocation('');
    setJobType('FULL_TIME');
    setPostStatus('ACTIVE');
    setRequiredSkills([]);
    setSkillInput('');
    setExpMin(1);
    setExpMax(4);
    setSalMin(1000000);
    setSalMax(1800000);
    setJobFormError('');
  };

  const addJobSkill = () => {
    if (skillInput.trim() && !requiredSkills.includes(skillInput.trim())) {
      setRequiredSkills([...requiredSkills, skillInput.trim()]);
      setSkillInput('');
    }
  };

  const removeJobSkill = (skToRemove) => {
    setRequiredSkills(requiredSkills.filter(s => s !== skToRemove));
  };

  const handleStatusChange = async (applicationId, newStatus) => {
    // Optimistic status update
    const previousApplicants = [...applicants];
    setApplicants(prev =>
      prev.map(a => a.id === applicationId ? { ...a, status: newStatus } : a)
    );

    if (selectedApplicant && selectedApplicant.id === applicationId) {
      setSelectedApplicant(prev => ({ ...prev, status: newStatus }));
    }

    try {
      await applicationAPI.updateStatus(applicationId, newStatus);
      addToast(`Candidate status updated to ${newStatus.replace('_', ' ')}`, "success");
      fetchApplicants();
    } catch (err) {
      console.error("Status update error:", err);
      // Rollback optimistic update
      setApplicants(previousApplicants);
      addToast(err.response?.data?.detail || "Failed to update candidate status.", "error");
    }
  };

  const handleCloseJob = async (jobId) => {
    if (!window.confirm("Are you sure you want to close this job opening? Candidates will no longer be able to submit new applications.")) return;
    try {
      await jobsAPI.delete(jobId);
      addToast("Job opening closed successfully.", "info");
      fetchJobs();
    } catch (err) {
      addToast("Failed to close job opening.", "error");
    }
  };

  const handleSaveCompany = async (e) => {
    e.preventDefault();
    setSavingCompany(true);
    setCompanySuccess('');
    try {
      const res = await recruiterAPI.updateCompany({
        company_name: companyName,
        description: companyDesc,
        website: companyWeb,
        location: companyLoc,
        contact_email: companyEmail,
        logo_url: companyLogo,
      });
      setCompany(res.data);
      setCompanySuccess("Company branding profile saved successfully!");
      addToast("Company branding updated!", "success");
    } catch (err) {
      console.error("Company update error:", err);
      addToast("Failed to update company branding.", "error");
    } finally {
      setSavingCompany(false);
    }
  };

  const openApplicantModal = (applicant) => {
    setSelectedApplicant(applicant);
    setShowApplicantModal(true);
  };

  // Metrics calculations
  const activeJobsCount = jobs.filter(j => j.status === 'ACTIVE').length;
  const shortlistedCount = applicants.filter(a => ['SHORTLISTED', 'INTERVIEW'].includes(a.status)).length;
  const selectedCount = applicants.filter(a => a.status === 'SELECTED').length;

  // Filtered candidate list
  const filteredApplicants = useMemo(() => {
    let result = [...applicants];
    if (candidateSearch.trim()) {
      const q = candidateSearch.toLowerCase();
      result = result.filter(a =>
        a.candidate?.name?.toLowerCase().includes(q) ||
        a.candidate?.email?.toLowerCase().includes(q) ||
        a.job?.title?.toLowerCase().includes(q) ||
        a.candidate?.skills?.some(s => s.toLowerCase().includes(q))
      );
    }
    return result;
  }, [applicants, candidateSearch]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SELECTED':
        return (
          <span className="badge-selected font-mono text-[11px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5 shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-[#829B88] animate-pulse"></span>
            <span>SELECTED / OFFERED</span>
          </span>
        );
      case 'SHORTLISTED':
        return (
          <span className="badge-rose font-mono text-[11px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C5A49B]"></span>
            <span>SHORTLISTED</span>
          </span>
        );
      case 'SCREENING':
        return (
          <span className="badge-oxblood font-mono text-[11px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#914F51]"></span>
            <span>SCREENING</span>
          </span>
        );
      case 'INTERVIEW':
        return (
          <span className="badge-oxblood font-mono text-[11px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#914F51]"></span>
            <span>INTERVIEW</span>
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="badge-slate font-mono text-[11px] font-medium px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span>UNDER REVIEW</span>
          </span>
        );
      case 'APPLIED':
        return (
          <span className="badge-slate font-mono text-[11px] font-medium px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span>APPLIED</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="bg-error/15 text-error border border-error/30 font-mono text-[11px] font-medium px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span>REJECTED</span>
          </span>
        );
      default:
        return (
          <span className="badge-slate font-mono text-[11px] font-medium px-2.5 py-1 rounded-full">
            {status}
          </span>
        );
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="max-w-7xl mx-auto space-y-8">
          
          {/* ======================================================== */}
          {/* RECRUITER TALENT HUB HEADER & METRICS */}
          {/* ======================================================== */}
          <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 pb-6 border-b border-slate/15 dark:border-rose/15">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-tight text-charcoal dark:text-ivory">
                    Recruiter Talent Hub
                  </h1>
                  <span className="badge-oxblood font-mono text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                    VERIFIED EMPLOYER
                  </span>
                </div>
                <p className="text-sm text-slate/80 dark:text-ivory/70 mt-1 font-normal leading-relaxed">
                  Managing openings for <span className="font-semibold text-charcoal dark:text-ivory">{company?.company_name || "Company Profile"}</span>. Screen candidates, inspect verified skills, and review applicants.
                </p>
              </div>

              <MagneticButton
                onClick={() => { resetJobForm(); setShowJobModal(true); }}
                className="btn-oxblood px-5 py-3 font-display font-semibold text-xs rounded-xl shadow-md transition flex items-center gap-2 min-h-[44px]"
              >
                <Plus className="w-4 h-4 text-ivory" />
                <span>Post New Opening</span>
              </MagneticButton>
            </div>

            {/* Recruiter Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 text-center font-mono">
              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                  <AnimatedCounter value={activeJobsCount} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Published Roles</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                  <AnimatedCounter value={applicants.length} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Total Applicants</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-oxblood dark:text-rose">
                  <AnimatedCounter value={shortlistedCount} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Shortlisted / Interview</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-success">
                  <AnimatedCounter value={selectedCount} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Offers Extended</p>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* TAB NAVIGATION WITH ANIMATED PILL */}
          {/* ======================================================== */}
          <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 overflow-x-auto pb-1 scrollbar-none" role="tablist">
            {[
              { id: 'jobs', label: `Manage Postings (${jobs.length})`, icon: Briefcase },
              { id: 'pipeline', label: `Pipeline & Candidates (${applicants.length})`, icon: Users },
              { id: 'assessments', label: 'First-Round Assessments', icon: Award },
              { id: 'video-assessments', label: 'Video Assessments', icon: Video },
              { id: 'interviews', label: `Interviews (${recruiterInterviews.length})`, icon: Calendar },
              { id: 'media', label: 'Media Library', icon: Film },
              { id: 'messages', label: 'Messages', icon: MessageSquare },
              { id: 'analytics', label: 'Recruitment Analytics', icon: BarChart3 },
              { id: 'company', label: 'Company Profile', icon: Building },
              { id: 'tickets', label: 'Support Tickets', icon: LifeBuoy }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setTab(tab.id)}
                  role="tab"
                  aria-selected={isActive}
                  className={`relative min-h-[44px] flex items-center gap-2 py-3 px-5 text-xs font-mono font-bold uppercase tracking-wider rounded-t-2xl whitespace-nowrap transition-colors duration-200 ${
                    isActive
                      ? 'text-ivory'
                      : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                  }`}
                >
                  {isActive && (
                    <motion.span
                      layoutId="recruiterTabPill"
                      className="absolute inset-0 bg-oxblood rounded-t-2xl shadow-sm"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </span>
                </button>
              );
            })}
          </div>

          {/* ======================================================== */}
          {/* TAB 1: MANAGE JOB POSTINGS */}
          {/* ======================================================== */}
          {activeTab === 'jobs' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">Published Positions</h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">Track published roles, review required skills, or close fulfilled roles.</p>
                </div>
                <div className="flex gap-2 w-full sm:w-auto">
                  <button
                    onClick={fetchJobs}
                    className="min-h-[44px] text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl border border-slate/15 dark:border-rose/15 transition"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                  <button
                    onClick={() => { resetJobForm(); setShowJobModal(true); }}
                    className="min-h-[44px] btn-oxblood px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase transition flex items-center justify-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Post Opening</span>
                  </button>
                </div>
              </div>

              {jobs.length === 0 ? (
                <div className="text-center py-14 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <Briefcase className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">No job openings posted yet.</p>
                  <button
                    onClick={() => setShowJobModal(true)}
                    className="mt-3 btn-oxblood px-5 py-2.5 rounded-xl font-display font-semibold text-xs inline-flex items-center gap-1.5 min-h-[44px]"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create Opening</span>
                  </button>
                </div>
              ) : (
                <>
                  {/* Desktop Table View (>= 768px) */}
                  <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-mono font-bold uppercase tracking-wider text-[11px]">
                          <th className="py-3.5 px-4 rounded-l-xl">Role Title</th>
                          <th className="py-3.5 px-4">Type & Location</th>
                          <th className="py-3.5 px-4">Required Skills</th>
                          <th className="py-3.5 px-4">Status</th>
                          <th className="py-3.5 px-4 text-right rounded-r-xl">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium">
                        {jobs.map((job) => (
                          <tr key={job.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4">
                              <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">{job.title}</p>
                              <p className="font-mono text-slate/60 dark:text-ivory/50 text-[10px]">Created {new Date(job.created_at).toLocaleDateString()}</p>
                            </td>
                            <td className="py-4 px-4 font-mono text-slate/80 dark:text-ivory/70 text-[11px]">
                              <span className="font-bold text-charcoal dark:text-ivory">{job.job_type.replace('_', ' ')}</span>
                              <p className="text-slate/60 dark:text-ivory/50 text-[10px]">{job.location}</p>
                            </td>
                            <td className="py-4 px-4">
                              <div className="flex flex-wrap gap-1 max-w-xs font-mono">
                                {job.required_skills?.map((sk, idx) => (
                                  <span key={idx} className="bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory px-1.5 py-0.5 rounded-md text-[10px] font-medium">
                                    {sk}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="py-4 px-4">
                              <span className={`font-mono text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                                job.status === 'ACTIVE' ? 'badge-selected' : job.status === 'DRAFT' ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30' : 'badge-slate'
                              }`}>
                                {job.status}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-right space-x-2 font-mono">
                              <button
                                onClick={() => { setFilterJobId(job.id); setTab('pipeline', { jobId: job.id }); fetchApplicants(job.id, filterStatus); }}
                                className="min-h-[44px] text-xs font-bold text-charcoal dark:text-ivory hover:text-oxblood px-3.5 py-2 rounded-xl border border-slate/15 dark:border-rose/15 transition inline-flex items-center gap-1"
                              >
                                <span>Candidates</span>
                                <ArrowUpRight className="w-3.5 h-3.5" />
                              </button>
                              {job.status === 'DRAFT' && (
                                <button
                                  onClick={() => handlePublishJob(job.id)}
                                  className="min-h-[44px] text-xs font-bold text-success hover:underline px-3.5 py-2 rounded-xl border border-success/30 bg-success/10 transition"
                                >
                                  Publish
                                </button>
                              )}
                              {job.status === 'ACTIVE' && (
                                <button
                                  onClick={() => handleCloseJob(job.id)}
                                  className="min-h-[44px] text-xs font-bold text-error hover:underline px-3.5 py-2 rounded-xl border border-error/30 bg-error/10 transition"
                                >
                                  Close
                                </button>
                              )}
                              {job.status === 'CLOSED' && (
                                <button
                                  onClick={() => handleReopenJob(job.id)}
                                  className="min-h-[44px] text-xs font-bold text-slate/70 dark:text-ivory/70 hover:underline px-3.5 py-2 rounded-xl border border-slate/20 transition"
                                >
                                  Reopen
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Stacked View (< 768px) */}
                  <div className="md:hidden space-y-4">
                    {jobs.map((job) => (
                      <div
                        key={job.id}
                        className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <span className="font-mono text-[10px] text-oxblood dark:text-rose font-bold uppercase">
                              {job.job_type.replace('_', ' ')}
                            </span>
                            <h4 className="font-display font-bold text-charcoal dark:text-ivory text-base">
                              {job.title}
                            </h4>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                              {job.location} · Created {new Date(job.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            job.status === 'ACTIVE' ? 'badge-selected' : job.status === 'DRAFT' ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30' : 'badge-slate'
                          }`}>
                            {job.status}
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-1 font-mono">
                          {job.required_skills?.map((sk, idx) => (
                            <span key={idx} className="bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory px-2 py-0.5 rounded-md text-[10px]">
                              {sk}
                            </span>
                          ))}
                        </div>

                        <div className="pt-2 border-t border-slate/10 dark:border-rose/10 flex gap-2">
                          <button
                            onClick={() => { setFilterJobId(job.id); setTab('pipeline', { jobId: job.id }); fetchApplicants(job.id, filterStatus); }}
                            className="flex-1 min-h-[44px] text-xs font-mono font-bold text-charcoal dark:text-ivory border border-slate/20 dark:border-rose/20 rounded-xl transition flex items-center justify-center gap-1"
                          >
                            <span>Review Candidates</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </button>
                          {job.status === 'DRAFT' && (
                            <button
                              onClick={() => handlePublishJob(job.id)}
                              className="min-h-[44px] px-4 text-xs font-mono font-bold text-success border border-success/30 bg-success/10 rounded-xl transition"
                            >
                              Publish
                            </button>
                          )}
                          {job.status === 'ACTIVE' && (
                            <button
                              onClick={() => handleCloseJob(job.id)}
                              className="min-h-[44px] px-4 text-xs font-mono font-bold text-error border border-error/30 bg-error/10 rounded-xl transition"
                            >
                              Close
                            </button>
                          )}
                          {job.status === 'CLOSED' && (
                            <button
                              onClick={() => handleReopenJob(job.id)}
                              className="min-h-[44px] px-4 text-xs font-mono font-bold text-slate/70 border border-slate/30 rounded-xl transition"
                            >
                              Reopen
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: CANDIDATES PIPELINE & KANBAN BOARD */}
          {/* ======================================================== */}
          {activeTab === 'pipeline' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Users className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Recruitment Pipeline & Candidates</span>
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Visual ATS Kanban stages and candidate telemetry for agile hiring workflows.
                  </p>
                </div>

                {/* Filters, View Toggle, and Compare */}
                <div className="flex flex-wrap items-center gap-2 w-full md:w-auto font-mono">
                  {/* View Mode Switcher */}
                  <div className="flex bg-slate/10 dark:bg-white/5 p-1 rounded-xl border border-slate/15 dark:border-rose/15">
                    <button
                      type="button"
                      onClick={() => setPipelineView('kanban')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition ${
                        pipelineView === 'kanban'
                          ? 'bg-oxblood text-ivory shadow-xs'
                          : 'text-slate/60 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                      }`}
                    >
                      <Columns className="w-3.5 h-3.5" />
                      <span>Kanban</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setPipelineView('table')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition ${
                        pipelineView === 'table'
                          ? 'bg-oxblood text-ivory shadow-xs'
                          : 'text-slate/60 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                      }`}
                    >
                      <List className="w-3.5 h-3.5" />
                      <span>Table</span>
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleOpenCompare(filterJobId || (jobs[0]?.id))}
                    disabled={jobs.length === 0}
                    className="px-3.5 py-2 rounded-xl border border-oxblood/30 bg-oxblood/10 text-oxblood dark:text-rose hover:bg-oxblood/20 font-mono text-xs font-bold transition flex items-center gap-1.5 min-h-[44px]"
                    title="Compare all candidates side-by-side"
                  >
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                    <span>Compare Matrix</span>
                  </button>

                  <div className="flex items-center px-3 py-1.5 bg-white/50 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 min-h-[44px]">
                    <Search className="w-3.5 h-3.5 text-slate/40 dark:text-rose/50 mr-2" />
                    <input
                      type="text"
                      placeholder="Search candidates or skills..."
                      value={candidateSearch}
                      onChange={(e) => setCandidateSearch(e.target.value)}
                      className="text-xs bg-transparent focus:outline-none text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30"
                    />
                  </div>

                  <select
                    value={filterJobId}
                    onChange={(e) => { setFilterJobId(e.target.value); fetchApplicants(e.target.value, filterStatus); }}
                    className="glass-input text-xs min-h-[44px]"
                  >
                    <option value="">All Job Openings</option>
                    {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
                  </select>

                  <select
                    value={filterStatus}
                    onChange={(e) => { setFilterStatus(e.target.value); fetchApplicants(filterJobId, e.target.value); }}
                    className="glass-input text-xs min-h-[44px]"
                  >
                    <option value="">All Statuses</option>
                    <option value="APPLIED">Applied</option>
                    <option value="SCREENING">Screening</option>
                    <option value="SHORTLISTED">Shortlisted</option>
                    <option value="INTERVIEW">Interview</option>
                    <option value="SELECTED">Selected</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </div>
              </div>

              {filteredApplicants.length === 0 ? (
                <div className="text-center py-14 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <Users className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">No candidates found for current filters.</p>
                  <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">Select another job or status filter above.</p>
                </div>
              ) : pipelineView === 'kanban' ? (
                /* ======================================================== */
                /* VISUAL KANBAN PIPELINE BOARD */
                /* ======================================================== */
                <div className="overflow-x-auto pb-4 pt-1">
                  <div className="flex gap-4 min-w-[1100px] items-start">
                    {[
                      { id: 'APPLIED', label: 'Applied', color: 'border-t-slate/50' },
                      { id: 'SCREENING', label: 'Screening', color: 'border-t-oxblood' },
                      { id: 'SHORTLISTED', label: 'Shortlisted', color: 'border-t-rose' },
                      { id: 'INTERVIEW', label: 'Interview', color: 'border-t-amber-500' },
                      { id: 'SELECTED', label: 'Selected / Offer', color: 'border-t-success' },
                      { id: 'REJECTED', label: 'Not Selected', color: 'border-t-error' }
                    ].map((col) => {
                      const colApps = filteredApplicants.filter(a => a.status === col.id);
                      return (
                        <div
                          key={col.id}
                          className={`flex-1 min-w-[200px] rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 border-t-4 ${col.color} p-3 flex flex-col min-h-[500px]`}
                        >
                          {/* Column Header */}
                          <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate/10 dark:border-white/5">
                            <span className="font-mono text-xs font-bold uppercase tracking-wider text-charcoal dark:text-ivory">
                              {col.label}
                            </span>
                            <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate/15 dark:bg-white/10 text-charcoal dark:text-ivory">
                              {colApps.length}
                            </span>
                          </div>

                          {/* Candidate Cards Stream */}
                          <div className="space-y-3 flex-1 overflow-y-auto max-h-[600px] pr-1">
                            {colApps.map((app) => (
                              <div
                                key={app.id}
                                onClick={() => openApplicantModal(app)}
                                className="p-3.5 rounded-xl bg-white dark:bg-charcoal border border-slate/15 dark:border-rose/15 hover:border-oxblood/40 cursor-pointer shadow-xs transition hover:shadow-md space-y-2"
                              >
                                <div className="flex justify-between items-start gap-1.5">
                                  <div>
                                    <h5 className="font-display font-bold text-xs text-charcoal dark:text-ivory hover:text-oxblood leading-tight">
                                      {app.candidate?.name || "Candidate"}
                                    </h5>
                                    <p className="text-[10px] font-mono text-oxblood dark:text-rose truncate max-w-[130px] mt-0.5">
                                      {app.job?.title}
                                    </p>
                                  </div>
                                  {app.recruiter_notes && (
                                    <span className="p-1 rounded bg-oxblood/10 text-oxblood dark:text-rose" title="Internal notes recorded">
                                      <FileText className="w-3 h-3" />
                                    </span>
                                  )}
                                </div>

                                <div className="text-[10px] font-mono text-slate/50 dark:text-ivory/40 flex justify-between">
                                  <span>{app.candidate?.total_years_exp || 0} yrs exp</span>
                                  <span>{new Date(app.application_date).toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
                                </div>

                                <div className="flex flex-wrap gap-1 font-mono">
                                  {app.candidate?.skills?.slice(0, 3).map((sk, idx) => (
                                    <span key={idx} className="bg-slate/10 dark:bg-white/5 text-[9px] px-1.5 py-0.5 rounded border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory">
                                      {sk}
                                    </span>
                                  ))}
                                  {(app.candidate?.skills?.length || 0) > 3 && (
                                    <span className="text-[9px] text-slate/40">+{app.candidate.skills.length - 3}</span>
                                  )}
                                </div>

                                {/* Quick Stage Advancement */}
                                <div className="pt-2 border-t border-slate/10 dark:border-white/5 flex justify-between items-center" onClick={(e) => e.stopPropagation()}>
                                  <button
                                    onClick={() => openApplicantModal(app)}
                                    className="text-[10px] font-mono font-bold text-slate/60 dark:text-ivory/60 hover:text-oxblood flex items-center gap-0.5"
                                  >
                                    <Eye className="w-3 h-3" />
                                    <span>Review</span>
                                  </button>

                                  <div className="flex items-center gap-1">
                                    {col.id !== 'REJECTED' && col.id !== 'SELECTED' && (
                                      <button
                                        onClick={() => {
                                          const nextMap = {
                                            'APPLIED': 'SCREENING',
                                            'SCREENING': 'SHORTLISTED',
                                            'SHORTLISTED': 'INTERVIEW',
                                            'INTERVIEW': 'SELECTED'
                                          };
                                          handleStatusChange(app.id, nextMap[col.id]);
                                        }}
                                        className="px-2 py-0.5 rounded bg-oxblood/10 text-oxblood dark:text-rose hover:bg-oxblood hover:text-ivory text-[10px] font-mono font-bold transition flex items-center gap-0.5"
                                        title="Advance to next pipeline stage"
                                      >
                                        <span>Advance</span>
                                        <ChevronRight className="w-3 h-3" />
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}

                            {colApps.length === 0 && (
                              <div className="py-12 text-center text-[10px] font-mono text-slate/40 dark:text-ivory/30 italic">
                                No candidates in {col.label}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <>
                  {/* Desktop Table View (>= 768px) */}
                  <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-mono font-bold uppercase tracking-wider text-[11px]">
                          <th className="py-3.5 px-4 rounded-l-xl">Candidate</th>
                          <th className="py-3.5 px-4">Applied Position</th>
                          <th className="py-3.5 px-4">Contact Details</th>
                          <th className="py-3.5 px-4">Verified Skills</th>
                          <th className="py-3.5 px-4">Resume</th>
                          <th className="py-3.5 px-4 text-right rounded-r-xl">Status & Decision</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium">
                        {filteredApplicants.map((app) => (
                          <tr key={app.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4">
                              <button
                                onClick={() => openApplicantModal(app)}
                                className="text-left font-display font-bold text-charcoal dark:text-ivory text-sm hover:text-oxblood flex items-center gap-1.5 transition"
                              >
                                <span>{app.candidate?.name || "Candidate"}</span>
                                {app.status === 'SELECTED' && (
                                  <span className="badge-selected text-[9px] px-1.5 py-0 font-mono">SELECTED</span>
                                )}
                              </button>
                              <p className="font-mono text-slate/70 dark:text-ivory/60 text-[10px]">{app.candidate?.title || "Candidate"}</p>
                            </td>
                            <td className="py-4 px-4 font-mono">
                              <p className="font-bold text-charcoal dark:text-ivory text-xs">{app.job?.title}</p>
                              <p className="text-slate/60 dark:text-ivory/50 text-[10px]">{new Date(app.application_date).toLocaleDateString()}</p>
                            </td>
                            <td className="py-4 px-4 font-mono text-slate/80 dark:text-ivory/70 text-[11px]">
                              <p>{app.candidate?.email}</p>
                              <p className="text-slate/60 dark:text-ivory/50 text-[10px]">{app.candidate?.phone || "No phone"}</p>
                            </td>
                            <td className="py-4 px-4">
                              <div className="flex flex-wrap gap-1 max-w-xs font-mono">
                                {app.candidate?.skills?.slice(0, 4).map((sk, idx) => (
                                  <span key={idx} className="bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory px-1.5 py-0.5 rounded-md text-[10px] font-medium">
                                    {sk}
                                  </span>
                                ))}
                                {(app.candidate?.skills?.length || 0) > 4 && (
                                  <span className="text-[10px] text-slate/50 dark:text-ivory/40">+{app.candidate.skills.length - 4}</span>
                                )}
                              </div>
                            </td>
                            <td className="py-4 px-4 font-mono">
                              {app.resume_id ? (
                                <a
                                  href={resumeAPI.downloadUrl(app.resume_id)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="min-h-[44px] inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 hover:border-oxblood text-charcoal dark:text-ivory text-[11px] font-bold transition"
                                  title="Download & inspect applicant resume"
                                >
                                  <Download className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                                  <span>Resume</span>
                                </a>
                              ) : (
                                <span className="opacity-40 text-[11px]">N/A</span>
                              )}
                            </td>
                            <td className="py-4 px-4 text-right font-mono">
                              <select
                                value={app.status}
                                onChange={(e) => handleStatusChange(app.id, e.target.value)}
                                className={`text-xs border rounded-xl p-2.5 min-h-[44px] font-mono font-bold focus:outline-none transition ${
                                  app.status === 'SELECTED'
                                    ? 'badge-selected shadow-xs'
                                    : 'bg-white/70 dark:bg-charcoal/70 border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory'
                                }`}
                              >
                                <option value="APPLIED">APPLIED</option>
                                <option value="UNDER_REVIEW">UNDER REVIEW</option>
                                <option value="SHORTLISTED">SHORTLISTED</option>
                                <option value="INTERVIEW">INTERVIEW</option>
                                <option value="SELECTED">SELECTED / OFFERED</option>
                                <option value="REJECTED">REJECTED</option>
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Stacked View (< 768px) */}
                  <div className="md:hidden space-y-4">
                    {filteredApplicants.map((app) => (
                      <div
                        key={app.id}
                        className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <button
                              onClick={() => openApplicantModal(app)}
                              className="text-left font-display font-bold text-charcoal dark:text-ivory text-base hover:text-oxblood"
                            >
                              {app.candidate?.name || "Candidate"}
                            </button>
                            <p className="text-xs font-mono text-oxblood dark:text-rose font-semibold">{app.job?.title}</p>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">{app.candidate?.email}</p>
                          </div>
                          <div>
                            {getStatusBadge(app.status)}
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-1 font-mono">
                          {app.candidate?.skills?.slice(0, 5).map((sk, idx) => (
                            <span key={idx} className="bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory px-2 py-0.5 rounded-md text-[10px]">
                              {sk}
                            </span>
                          ))}
                        </div>

                        <div className="pt-2 border-t border-slate/10 dark:border-rose/10 flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            {app.resume_id && (
                              <a
                                href={resumeAPI.downloadUrl(app.resume_id)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 min-h-[44px] text-xs font-mono font-bold text-charcoal dark:text-ivory border border-slate/20 dark:border-rose/20 rounded-xl transition flex items-center justify-center gap-1.5"
                              >
                                <Download className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                                <span>Download CV</span>
                              </a>
                            )}
                            <button
                              onClick={() => openApplicantModal(app)}
                              className="flex-1 min-h-[44px] text-xs font-mono font-bold text-charcoal dark:text-ivory border border-slate/20 dark:border-rose/20 rounded-xl transition flex items-center justify-center gap-1.5"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>Inspect Profile</span>
                            </button>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-slate/60 dark:text-rose uppercase font-bold shrink-0">Status:</span>
                            <select
                              value={app.status}
                              onChange={(e) => handleStatusChange(app.id, e.target.value)}
                              className="flex-1 min-h-[44px] glass-input text-xs font-mono font-bold"
                            >
                              <option value="APPLIED">APPLIED</option>
                              <option value="UNDER_REVIEW">UNDER REVIEW</option>
                              <option value="SHORTLISTED">SHORTLISTED</option>
                              <option value="INTERVIEW">INTERVIEW</option>
                              <option value="SELECTED">SELECTED / OFFERED</option>
                              <option value="REJECTED">REJECTED</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITER FIRST-ROUND ASSESSMENTS */}
          {/* ======================================================== */}
          {activeTab === 'assessments' && (
            <RecruiterAssessmentsSection jobs={jobs} />
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITER VIDEO ASSESSMENTS */}
          {/* ======================================================== */}
          {activeTab === 'video-assessments' && (
            <RecruiterVideoAssessmentsTab jobs={jobs} />
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITER MEDIA LIBRARY */}
          {/* ======================================================== */}
          {activeTab === 'media' && (
            <RecruiterMediaLibraryTab />
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITER INTERVIEWS MANAGEMENT */}
          {/* ======================================================== */}
          {activeTab === 'interviews' && (
            <RecruiterInterviewHubTab
              interviews={recruiterInterviews}
              loading={interviewsLoading}
              onRefresh={fetchRecruiterInterviews}
              onOpenDossier={(candId) => setDossierCandidateId(candId)}
              jobs={jobs}
              applicants={applicants}
              onScheduleNewInterview={(applicant) => {
                if (applicant) setSelectedApplicant(applicant);
                setShowScheduleModal(true);
              }}
            />
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITER DIRECT MESSAGING */}
          {/* ======================================================== */}
          {activeTab === 'messages' && (
            <div className="glass-card rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-12 min-h-[600px]">
                
                {/* Conversations Sidebar */}
                <div className="md:col-span-4 border-r border-slate/15 dark:border-rose/15 p-4 sm:p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate/15 dark:border-rose/15">
                      <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-oxblood dark:text-rose" />
                        <span>Candidate Threads</span>
                      </h3>
                      <button
                        onClick={fetchConversations}
                        className="text-slate/60 dark:text-ivory/60 hover:text-oxblood p-1.5 rounded-lg border border-slate/15 dark:border-rose/15 min-h-[36px] min-w-[36px] flex items-center justify-center"
                        title="Refresh messages"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {conversations.length === 0 ? (
                      <div className="text-center py-12 text-slate/50 dark:text-ivory/40 text-xs font-mono">
                        No conversations yet. Open candidate profile in Pipeline to send direct message.
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        {conversations.map((conv) => {
                          const partnerId = conv.partner_id || conv.id;
                          const isSelected = activePartner && (activePartner.partner_id || activePartner.id) === partnerId;
                          return (
                            <button
                              key={partnerId}
                              onClick={() => setActivePartner(conv)}
                              className={`w-full text-left p-3 rounded-xl transition min-h-[48px] flex items-start gap-3 ${
                                isSelected
                                  ? 'bg-oxblood text-ivory shadow-xs'
                                  : 'hover:bg-slate/5 dark:hover:bg-white/5 text-charcoal dark:text-ivory'
                              }`}
                            >
                              <div className={`w-9 h-9 rounded-full flex items-center justify-center font-display font-bold text-xs shrink-0 ${
                                isSelected ? 'bg-white/20 text-ivory' : 'bg-oxblood/10 text-oxblood dark:text-rose'
                              }`}>
                                {(conv.partner_name || 'C')[0]?.toUpperCase()}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-baseline">
                                  <p className="font-display font-bold text-xs truncate">
                                    {conv.partner_name || 'Candidate'}
                                  </p>
                                  {conv.last_message_time && (
                                    <span className={`text-[10px] font-mono shrink-0 ml-1 ${isSelected ? 'text-ivory/70' : 'text-slate/50 dark:text-ivory/40'}`}>
                                      {new Date(conv.last_message_time).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                                    </span>
                                  )}
                                </div>
                                <p className={`text-[11px] font-mono truncate mt-0.5 ${isSelected ? 'text-ivory/80' : 'text-slate/60 dark:text-ivory/60'}`}>
                                  {conv.last_message || 'Start chat...'}
                                </p>
                              </div>
                              {conv.unread_count > 0 && !isSelected && (
                                <span className="w-5 h-5 rounded-full bg-oxblood text-ivory text-[10px] font-mono font-bold flex items-center justify-center shrink-0">
                                  {conv.unread_count}
                                </span>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <div className="pt-4 border-t border-slate/15 dark:border-rose/15 text-[11px] font-mono text-slate/50 dark:text-ivory/40 text-center">
                    Direct Recruiter-Candidate Channel
                  </div>
                </div>

                {/* Chat Message Window */}
                <div className="md:col-span-8 flex flex-col justify-between p-4 sm:p-6 bg-slate/5 dark:bg-black/10">
                  {activePartner ? (
                    <>
                      <div className="flex justify-between items-center pb-4 border-b border-slate/15 dark:border-rose/15 mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-oxblood/10 text-oxblood dark:text-rose font-display font-bold text-sm flex items-center justify-center">
                            {(activePartner.partner_name || 'C')[0]?.toUpperCase()}
                          </div>
                          <div>
                            <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                              {activePartner.partner_name || 'Candidate'}
                            </h4>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                              Direct Messaging Channel
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4 max-h-[420px]">
                        {chatLoading ? (
                          <div className="text-center py-10 font-mono text-xs text-slate/50">Loading messages...</div>
                        ) : chatMessages.length === 0 ? (
                          <div className="text-center py-12 text-slate/50 dark:text-ivory/40 text-xs font-mono">
                            Send a message to introduce next interview steps.
                          </div>
                        ) : (
                          chatMessages.map((msg) => {
                            const isMe = msg.sender_id === user?.id;
                            return (
                              <div
                                key={msg.id}
                                className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
                              >
                                <div
                                  className={`max-w-[78%] px-4 py-2.5 rounded-2xl text-xs ${
                                    isMe
                                      ? 'bg-oxblood text-ivory rounded-br-none'
                                      : 'bg-white dark:bg-charcoal text-charcoal dark:text-ivory border border-slate/15 dark:border-rose/15 rounded-bl-none shadow-xs'
                                  }`}
                                >
                                  <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                </div>
                                <span className="text-[10px] font-mono text-slate/50 dark:text-ivory/40 mt-1 px-1">
                                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                              </div>
                            );
                          })
                        )}
                      </div>

                      <form onSubmit={handleSendMessage} className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Type your message to candidate..."
                          value={messageText}
                          onChange={(e) => setMessageText(e.target.value)}
                          className="flex-1 glass-input text-xs min-h-[44px]"
                        />
                        <button
                          type="submit"
                          disabled={sendingMessage || !messageText.trim()}
                          className="btn-oxblood px-5 py-2.5 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 min-h-[44px] disabled:opacity-50"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Send</span>
                        </button>
                      </form>
                    </>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate/50 dark:text-ivory/40 font-mono text-xs">
                      <MessageSquare className="w-10 h-10 mb-2 opacity-40" />
                      <p>Select a candidate conversation on the left to start messaging.</p>
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: RECRUITMENT ANALYTICS */}
          {/* ======================================================== */}
          {activeTab === 'analytics' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-8 font-mono">
              <div className="flex justify-between items-center pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Recruitment Intelligence & Funnel Analytics</span>
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Real-time PostgreSQL aggregation of recruitment pipeline velocity, conversion rates, and time-to-hire.
                  </p>
                </div>
                <button
                  onClick={fetchRecruiterAnalytics}
                  className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
              </div>

              {/* Top Conversion Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <span className="text-[10px] uppercase text-slate/60 dark:text-rose font-bold block">Total Applications</span>
                  <p className="text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                    <AnimatedCounter value={recruiterAnalytics?.total_applications || applicants.length} />
                  </p>
                  <span className="text-[11px] text-slate/50 mt-1 block">In Active Funnel</span>
                </div>

                <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <span className="text-[10px] uppercase text-slate/60 dark:text-rose font-bold block">Screening Rate</span>
                  <p className="text-3xl font-extrabold text-oxblood dark:text-rose mt-2">
                    {Math.round(recruiterAnalytics?.screening_rate || 75)}%
                  </p>
                  <span className="text-[11px] text-slate/50 mt-1 block">Passed Initial OCR</span>
                </div>

                <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <span className="text-[10px] uppercase text-slate/60 dark:text-rose font-bold block">Interview Rate</span>
                  <p className="text-3xl font-extrabold text-amber-500 mt-2">
                    {Math.round(recruiterAnalytics?.interview_rate || 40)}%
                  </p>
                  <span className="text-[11px] text-slate/50 mt-1 block">Advanced to Interview</span>
                </div>

                <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <span className="text-[10px] uppercase text-slate/60 dark:text-rose font-bold block">Avg Time-to-Hire</span>
                  <p className="text-3xl font-extrabold text-success mt-2">
                    {recruiterAnalytics?.avg_days_to_hire || 14} <span className="text-sm font-normal">days</span>
                  </p>
                  <span className="text-[11px] text-slate/50 mt-1 block">Application to Selection</span>
                </div>
              </div>

              {/* Visual Funnel Stage Distribution */}
              <div className="p-6 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-4">
                <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory uppercase tracking-wider">
                  Pipeline Stage Volume Breakdown
                </h4>
                <div className="space-y-3">
                  {[
                    { label: 'APPLIED', count: applicants.filter(a => a.status === 'APPLIED').length, color: 'bg-slate/40' },
                    { label: 'SCREENING', count: applicants.filter(a => a.status === 'SCREENING').length, color: 'bg-oxblood' },
                    { label: 'SHORTLISTED', count: applicants.filter(a => a.status === 'SHORTLISTED').length, color: 'bg-rose' },
                    { label: 'INTERVIEW', count: applicants.filter(a => a.status === 'INTERVIEW').length, color: 'bg-amber-500' },
                    { label: 'SELECTED', count: applicants.filter(a => a.status === 'SELECTED').length, color: 'bg-success' },
                    { label: 'REJECTED', count: applicants.filter(a => a.status === 'REJECTED').length, color: 'bg-error' },
                  ].map((stage) => {
                    const total = Math.max(applicants.length, 1);
                    const pct = Math.round((stage.count / total) * 100);
                    return (
                      <div key={stage.label} className="space-y-1">
                        <div className="flex justify-between text-xs font-bold text-slate/80 dark:text-ivory/80">
                          <span>{stage.label}</span>
                          <span>{stage.count} candidates ({pct}%)</span>
                        </div>
                        <div className="h-3 w-full bg-slate/15 dark:bg-white/10 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                            className={`h-full rounded-full ${stage.color}`}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: COMPANY PROFILE */}
          {/* ======================================================== */}
          {activeTab === 'company' && (
            <div className="glass-card p-6 sm:p-10 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl max-w-2xl mx-auto">
              <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory mb-1">Company Profile & Employer Branding</h2>
              <p className="text-xs text-slate/70 dark:text-ivory/65 mb-6 font-normal">Candidate job cards and application details reflect this branding identity.</p>

              {companySuccess && (
                <div className="mb-5 p-3.5 rounded-2xl badge-selected text-xs font-mono font-medium flex items-center gap-2">
                  <Check className="w-4 h-4 text-success" />
                  <span>{companySuccess}</span>
                </div>
              )}

              <form onSubmit={handleSaveCompany} className="space-y-4 font-mono">
                <div>
                  <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                    Company Legal / Brand Name
                  </label>
                  <input
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full glass-input text-xs min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                    Company Mission & Overview
                  </label>
                  <textarea
                    rows={3}
                    value={companyDesc}
                    onChange={(e) => setCompanyDesc(e.target.value)}
                    className="w-full glass-input text-xs font-sans"
                  ></textarea>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                      Website URL
                    </label>
                    <input
                      type="url"
                      placeholder="https://example.com"
                      value={companyWeb}
                      onChange={(e) => setCompanyWeb(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                      Headquarters Location
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Bengaluru, India"
                      value={companyLoc}
                      onChange={(e) => setCompanyLoc(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                    Careers Contact Email
                  </label>
                  <input
                    type="email"
                    value={companyEmail}
                    onChange={(e) => setCompanyEmail(e.target.value)}
                    className="w-full glass-input text-xs min-h-[44px]"
                  />
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    type="submit"
                    disabled={savingCompany}
                    className="min-h-[48px] px-8 py-3.5 btn-oxblood font-display font-semibold text-xs rounded-xl shadow-xs transition disabled:opacity-50"
                  >
                    {savingCompany ? "Saving Profile..." : "Save Company Profile"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: SUPPORT TICKETS & ESCALATION TRACKING */}
          {/* ======================================================== */}
          {activeTab === 'tickets' && (
            <div className="space-y-6">
              <UserSupportTicketsTab />
            </div>
          )}

        </div>
      </div>

      {/* ======================================================== */}
      {/* POST JOB MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showJobModal}
        onClose={() => setShowJobModal(false)}
        title="Publish New Job Opening"
      >
        <p className="text-xs text-slate/70 dark:text-ivory/65 -mt-3 mb-5 font-normal">
          Define the role parameters and required skill tags for deterministic matching.
        </p>

        {jobFormError && (
          <div className="mb-4 p-3 rounded-xl bg-error/15 border border-error/30 text-error text-xs font-mono">
            {jobFormError}
          </div>
        )}

        <form onSubmit={handleCreateJob} className="space-y-4 font-mono">
          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Role Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Senior Full-Stack Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full glass-input text-xs min-h-[44px]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Location</label>
              <input
                type="text"
                required
                placeholder="e.g. Bengaluru, India or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Employment Type</label>
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              >
                <option value="FULL_TIME">Full Time</option>
                <option value="PART_TIME">Part Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="REMOTE">Remote</option>
                <option value="INTERNSHIP">Internship</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Min Exp (Yrs)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                value={expMin}
                onChange={(e) => setExpMin(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Max Exp (Yrs)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                value={expMax}
                onChange={(e) => setExpMax(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Min Salary (₹/yr)</label>
              <input
                type="number"
                value={salMin}
                onChange={(e) => setSalMin(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Max Salary (₹/yr)</label>
              <input
                type="number"
                value={salMax}
                onChange={(e) => setSalMax(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
          </div>

          {/* REQUIRED SKILLS INPUT */}
          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
              Required Technical Skills ({requiredSkills.length})
            </label>
            <div className="p-3.5 rounded-2xl bg-white/60 dark:bg-slate/40 border border-slate/15 dark:border-rose/15 mb-2">
              <div className="flex flex-wrap gap-1.5 mb-2">
                {requiredSkills.map((sk, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg badge-slate text-xs font-medium">
                    <span>{sk}</span>
                    <button
                      type="button"
                      onClick={() => removeJobSkill(sk)}
                      className="hover:text-oxblood transition ml-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                {requiredSkills.length === 0 && (
                  <span className="text-xs text-slate/40 dark:text-ivory/40 italic">No skills added. Add required skills below.</span>
                )}
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Python, FastAPI, Docker, PostgreSQL..."
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addJobSkill(); } }}
                  className="flex-1 glass-input text-xs min-h-[44px]"
                />
                <button
                  type="button"
                  onClick={addJobSkill}
                  className="px-4 py-2 bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal rounded-xl text-xs font-bold transition flex items-center gap-1 shadow-sm min-h-[44px]"
                >
                  <Plus className="w-3.5 h-3.5 text-rose dark:text-oxblood" />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Job Description & Responsibilities</label>
            <textarea
              rows={4}
              required
              placeholder="Outline day-to-day architectural responsibilities, requirements, and benefits..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full glass-input text-xs font-sans"
            ></textarea>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">Publication Lifecycle</label>
            <select
              value={postStatus}
              onChange={(e) => setPostStatus(e.target.value)}
              className="w-full glass-input text-xs min-h-[44px]"
            >
              <option value="ACTIVE">Publish Immediately (Active & Discoverable)</option>
              <option value="DRAFT">Save as Draft (Internal Only)</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowJobModal(false)}
              className="min-h-[44px] px-5 py-2.5 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory font-display font-semibold text-xs hover:bg-slate/5 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creatingJob}
              className="min-h-[44px] px-7 py-2.5 btn-oxblood font-display font-semibold text-xs rounded-xl shadow-xs transition disabled:opacity-50"
            >
              {creatingJob ? (postStatus === 'DRAFT' ? "Saving Draft..." : "Publishing Opening...") : (postStatus === 'DRAFT' ? "Save as Draft" : "Publish Job Opening")}
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ======================================================== */}
      {/* CANDIDATE INSPECTION MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showApplicantModal}
        onClose={() => setShowApplicantModal(false)}
        title="Candidate Profile & Telemetry"
      >
        {selectedApplicant && (
          <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h4 className="font-display font-bold text-lg text-charcoal dark:text-ivory">
                  {selectedApplicant.candidate?.name || "Candidate"}
                </h4>
                <p className="font-mono text-xs text-oxblood dark:text-rose">{selectedApplicant.candidate?.title || "Candidate"}</p>
                <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50 mt-1">
                  Applied for <span className="font-bold text-charcoal dark:text-ivory">{selectedApplicant.job?.title}</span> on {new Date(selectedApplicant.application_date).toLocaleDateString()}
                </p>
              </div>

              <div>
                {getStatusBadge(selectedApplicant.status)}
              </div>
            </div>

            {/* Contact Coordinates */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex items-center gap-2">
                <Mail className="w-4 h-4 text-oxblood dark:text-rose" />
                <span className="truncate">{selectedApplicant.candidate?.email || "No email"}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex items-center gap-2">
                <Phone className="w-4 h-4 text-oxblood dark:text-rose" />
                <span>{selectedApplicant.candidate?.phone || "No phone provided"}</span>
              </div>
            </div>

            {/* Verified Skills */}
            <div>
              <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/80 dark:text-rose mb-2">
                Verified Technical Skills ({selectedApplicant.candidate?.skills?.length || 0})
              </p>
              <div className="flex flex-wrap gap-1.5 font-mono">
                {selectedApplicant.candidate?.skills?.map((sk, idx) => (
                  <span key={idx} className="badge-slate text-xs px-2.5 py-1 rounded-xl">
                    {sk}
                  </span>
                ))}
                {(!selectedApplicant.candidate?.skills || selectedApplicant.candidate.skills.length === 0) && (
                  <span className="text-xs text-slate/50 dark:text-ivory/40 italic font-mono">No skills on record.</span>
                )}
              </div>
            </div>

            {/* Candidate Bio */}
            {selectedApplicant.candidate?.bio && (
              <div>
                <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/80 dark:text-rose mb-1">
                  Candidate Summary
                </p>
                <p className="text-xs text-slate/80 dark:text-ivory/70 leading-relaxed p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  {selectedApplicant.candidate.bio}
                </p>
              </div>
            )}

            {/* Candidate Cover Letter */}
            {selectedApplicant.cover_letter && (
              <div>
                <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/80 dark:text-rose mb-1">
                  Cover Letter / Application Note
                </p>
                <p className="text-xs text-slate/80 dark:text-ivory/70 leading-relaxed p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  {selectedApplicant.cover_letter}
                </p>
              </div>
            )}

            {/* Private Recruiter Internal Notes */}
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[11px] font-bold text-oxblood dark:text-rose uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Private Internal Notes (Recruiter Only)</span>
                </span>
                <button
                  type="button"
                  onClick={handleSaveNotes}
                  disabled={savingNotes}
                  className="px-3 py-1 rounded-lg btn-oxblood text-[10px] font-bold flex items-center gap-1 disabled:opacity-50 min-h-[32px]"
                >
                  <Check className="w-3 h-3" />
                  <span>{savingNotes ? "Saving..." : "Save Notes"}</span>
                </button>
              </div>
              <textarea
                rows={2}
                placeholder="Confidential interview thoughts, salary requirements, or hiring manager remarks..."
                value={internalNotes}
                onChange={(e) => setInternalNotes(e.target.value)}
                className="w-full glass-input text-xs font-sans"
              />
            </div>

            {/* Candidate Evaluation Scorecard Form */}
            <div className="p-5 rounded-2xl bg-white/60 dark:bg-black/20 border border-slate/15 dark:border-rose/15 space-y-4 font-mono">
              <div className="flex justify-between items-center pb-2 border-b border-slate/10 dark:border-white/5">
                <span className="text-xs font-bold text-charcoal dark:text-ivory uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-oxblood dark:text-rose" />
                  <span>Interview Evaluation Scorecard</span>
                </span>
                <span className="text-[10px] text-slate/50">Structured 1-5 Competency Scoring</span>
              </div>

              <form onSubmit={handleSubmitEvaluation} className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/70 dark:text-rose mb-1">
                      Technical: {techRating}/5
                    </label>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setTechRating(star)}
                          className={`p-1.5 rounded-lg border text-xs min-h-[32px] min-w-[32px] flex items-center justify-center transition ${
                            star <= techRating
                              ? 'bg-amber-500/20 border-amber-500/40 text-amber-500'
                              : 'border-slate/15 dark:border-white/10 text-slate/40'
                          }`}
                        >
                          <Star className="w-3.5 h-3.5 fill-current" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/70 dark:text-rose mb-1">
                      Communication: {commRating}/5
                    </label>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setCommRating(star)}
                          className={`p-1.5 rounded-lg border text-xs min-h-[32px] min-w-[32px] flex items-center justify-center transition ${
                            star <= commRating
                              ? 'bg-amber-500/20 border-amber-500/40 text-amber-500'
                              : 'border-slate/15 dark:border-white/10 text-slate/40'
                          }`}
                        >
                          <Star className="w-3.5 h-3.5 fill-current" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/70 dark:text-rose mb-1">
                      Domain Experience: {expRating}/5
                    </label>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setExpRating(star)}
                          className={`p-1.5 rounded-lg border text-xs min-h-[32px] min-w-[32px] flex items-center justify-center transition ${
                            star <= expRating
                              ? 'bg-amber-500/20 border-amber-500/40 text-amber-500'
                              : 'border-slate/15 dark:border-white/10 text-slate/40'
                          }`}
                        >
                          <Star className="w-3.5 h-3.5 fill-current" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/70 dark:text-rose mb-1">
                      Overall Recommendation
                    </label>
                    <select
                      value={recommendation}
                      onChange={(e) => setRecommendation(e.target.value)}
                      className="w-full glass-input text-xs min-h-[40px]"
                    >
                      <option value="STRONG_HIRE">STRONG HIRE</option>
                      <option value="HIRE">HIRE</option>
                      <option value="HOLD">HOLD / BACKUP</option>
                      <option value="NO_HIRE">NO HIRE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate/70 dark:text-rose mb-1">
                      Evaluation Feedback
                    </label>
                    <input
                      type="text"
                      placeholder="Candidate strengths and concerns..."
                      value={evalFeedback}
                      onChange={(e) => setEvalFeedback(e.target.value)}
                      className="w-full glass-input text-xs min-h-[40px] font-sans"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={submittingEval}
                    className="btn-oxblood px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 min-h-[38px] disabled:opacity-50"
                  >
                    <Award className="w-3.5 h-3.5" />
                    <span>{submittingEval ? "Submitting..." : "Submit Scorecard"}</span>
                  </button>
                </div>
              </form>

              {candidateEvals.length > 0 && (
                <div className="pt-3 border-t border-slate/10 dark:border-white/5 space-y-2">
                  <p className="text-[10px] font-bold text-slate/60 uppercase">Previous Scorecards ({candidateEvals.length})</p>
                  <div className="space-y-1.5">
                    {candidateEvals.map((ev) => (
                      <div key={ev.id} className="p-2.5 rounded-xl bg-slate/5 dark:bg-white/5 text-xs flex justify-between items-center">
                        <div>
                          <span className="font-bold text-charcoal dark:text-ivory mr-2">{ev.evaluator?.name || 'Recruiter'}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ev.overall_recommendation === 'STRONG_HIRE' ? 'badge-selected' :
                            ev.overall_recommendation === 'HIRE' ? 'badge-selected' :
                            ev.overall_recommendation === 'HOLD' ? 'badge-amber' : 'bg-error/15 text-error'
                          }`}>
                            {ev.overall_recommendation}
                          </span>
                          {ev.feedback && <p className="text-[11px] text-slate/70 dark:text-ivory/70 mt-1 font-sans">{ev.feedback}</p>}
                        </div>
                        <div className="text-right text-[11px] text-slate/50">
                          <span>Tech: {ev.technical_rating}/5 · Comm: {ev.communication_rating}/5</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Status History Audit Trail */}
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono space-y-2.5">
              <span className="text-[11px] font-bold text-charcoal dark:text-ivory uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                <span>Status Audit History</span>
              </span>

              {historyLoading ? (
                <div className="py-4 text-center text-xs text-slate/50">Loading transition audit trail...</div>
              ) : statusHistory.length === 0 ? (
                <p className="text-[11px] text-slate/50 italic">No previous status transitions recorded.</p>
              ) : (
                <div className="space-y-2">
                  {statusHistory.map((h) => (
                    <div key={h.id} className="text-[11px] flex items-center justify-between p-2 rounded-lg bg-white/40 dark:bg-black/20">
                      <div className="flex items-center gap-2">
                        <span className="opacity-60">{h.previous_status || 'INITIAL'}</span>
                        <span>→</span>
                        <span className="font-bold text-oxblood dark:text-rose">{h.new_status}</span>
                        {h.notes && <span className="text-slate/60 text-[10px] ml-2 font-sans">"{h.notes}"</span>}
                      </div>
                      <span className="text-[10px] text-slate/50">
                        {new Date(h.changed_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Actions & Decision Bar */}
            <div className="pt-4 border-t border-slate/15 dark:border-rose/15 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
              <div className="flex items-center gap-2 flex-wrap">
                {selectedApplicant.resume_id && (
                  <a
                    href={resumeAPI.downloadUrl(selectedApplicant.resume_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="min-h-[44px] px-3.5 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory hover:border-oxblood text-xs font-mono font-bold transition flex items-center gap-1.5"
                  >
                    <Download className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                    <span>CV</span>
                  </a>
                )}

                <button
                  type="button"
                  onClick={() => setShowScheduleModal(true)}
                  className="min-h-[44px] px-4 py-2 rounded-xl btn-oxblood text-xs font-mono font-bold transition flex items-center gap-1.5"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Schedule Interview</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleOpenCompare(selectedApplicant.job_id || selectedApplicant.job?.id)}
                  className="min-h-[44px] px-3.5 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory hover:border-oxblood text-xs font-mono font-bold transition flex items-center gap-1.5"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  <span>Compare</span>
                </button>
              </div>

              <div className="flex items-center gap-2 font-mono">
                <span className="text-xs font-bold text-slate/70 dark:text-rose">Status:</span>
                <select
                  value={selectedApplicant.status}
                  onChange={(e) => handleStatusChange(selectedApplicant.id, e.target.value)}
                  className="min-h-[44px] glass-input text-xs font-mono font-bold"
                >
                  <option value="APPLIED">APPLIED</option>
                  <option value="SCREENING">SCREENING</option>
                  <option value="SHORTLISTED">SHORTLISTED</option>
                  <option value="INTERVIEW">INTERVIEW</option>
                  <option value="SELECTED">SELECTED / OFFERED</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* SCHEDULE INTERVIEW MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        title={`Schedule Interview: ${selectedApplicant?.candidate?.name || 'Candidate'}`}
      >
        <p className="text-xs text-slate/70 dark:text-ivory/65 -mt-3 mb-5 font-normal font-mono">
          For Position: <span className="font-bold text-charcoal dark:text-ivory">{selectedApplicant?.job?.title}</span>
        </p>

        <form onSubmit={handleScheduleInterview} className="space-y-4 font-mono">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                Interview Date
              </label>
              <input
                type="date"
                required
                value={schedDate}
                onChange={(e) => setSchedDate(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                Time
              </label>
              <input
                type="time"
                required
                value={schedTime}
                onChange={(e) => setSchedTime(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                Interview Type
              </label>
              <select
                value={schedType}
                onChange={(e) => setSchedType(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              >
                <option value="ONLINE">ONLINE (Video Call)</option>
                <option value="PHONE">PHONE SCREEN</option>
                <option value="IN_PERSON">IN PERSON (On-site)</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
                Duration (Minutes)
              </label>
              <select
                value={schedDuration}
                onChange={(e) => setSchedDuration(e.target.value)}
                className="w-full glass-input text-xs min-h-[44px]"
              >
                <option value="30">30 Minutes</option>
                <option value="45">45 Minutes</option>
                <option value="60">60 Minutes</option>
                <option value="90">90 Minutes</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
              Interview Workflow & AI Engine
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {[
                { key: 'HUMAN', label: 'Human Live', desc: 'Direct WebRTC' },
                { key: 'AI_LIVE', label: 'AI Live', desc: 'Autonomous Agent' },
                { key: 'HYBRID', label: 'Hybrid AI', desc: 'Recruiter Takeover' },
                { key: 'CONFIGURED', label: 'Configured', desc: 'Custom Rubric' },
              ].map((opt) => (
                <div
                  key={opt.key}
                  onClick={() => setSchedMode(opt.key)}
                  className={`p-2 rounded-xl border text-center cursor-pointer transition ${
                    schedMode === opt.key
                      ? 'bg-oxblood/10 border-oxblood dark:border-rose text-charcoal dark:text-ivory'
                      : 'border-slate/20 hover:border-oxblood/40 text-slate/60 dark:text-ivory/60'
                  }`}
                >
                  <span className="block text-xs font-bold">{opt.label}</span>
                  <span className="text-[10px] opacity-75">{opt.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Live & Hybrid Mode Customizer */}
          {(schedMode === 'AI_LIVE' || schedMode === 'HYBRID' || schedMode === 'CONFIGURED') && (
            <div className="p-4 rounded-2xl bg-oxblood/5 dark:bg-rose/5 border border-oxblood/20 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-oxblood dark:text-rose uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  <span>AI Interview Protocol & Rubric</span>
                </span>
                <span className="text-[10px] font-mono text-slate/50">
                  {schedQuestions.length} Questions Configured
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 dark:text-ivory/70 mb-1">
                    Evaluation Difficulty
                  </label>
                  <select
                    value={schedDifficulty}
                    onChange={(e) => setSchedDifficulty(e.target.value)}
                    className="w-full glass-input text-xs min-h-[40px]"
                  >
                    <option value="ENTRY">Entry Level</option>
                    <option value="INTERMEDIATE">Intermediate Level</option>
                    <option value="SENIOR">Senior Level</option>
                    <option value="LEAD">Staff / Principal Lead</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 dark:text-ivory/70 mb-1">
                    AI Voice Profile
                  </label>
                  <select
                    value={schedVoice}
                    onChange={(e) => setSchedVoice(e.target.value)}
                    className="w-full glass-input text-xs min-h-[40px]"
                  >
                    <option value="alloy">Alloy (Balanced, Neutral)</option>
                    <option value="echo">Echo (Authoritative, Clear)</option>
                    <option value="fable">Fable (Warm, Conversational)</option>
                    <option value="onyx">Onyx (Deep, Executive)</option>
                    <option value="nova">Nova (Bright, Energetic)</option>
                    <option value="shimmer">Shimmer (Calm, Precise)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-slate/70 dark:text-ivory/70 mb-1">
                    Recording & Takeover
                  </label>
                  <div className="flex flex-col gap-1 text-[11px] pt-1">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={schedAllowTakeover}
                        onChange={(e) => setSchedAllowTakeover(e.target.checked)}
                        className="rounded accent-oxblood"
                      />
                      <span>Recruiter Takeover</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={schedRecordingConsent}
                        onChange={(e) => setSchedRecordingConsent(e.target.checked)}
                        className="rounded accent-oxblood"
                      />
                      <span>Mandatory Recording</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Questions Management */}
              <div className="space-y-2 pt-2 border-t border-slate/15 dark:border-rose/15">
                <div className="flex justify-between items-center">
                  <span className="text-[11px] font-bold text-charcoal dark:text-ivory">
                    Interview Question Set
                  </span>
                  <button
                    type="button"
                    onClick={handleGenerateSchedQuestions}
                    disabled={schedGeneratingQuestions}
                    className="px-3 py-1.5 rounded-xl bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose border border-oxblood/20 text-xs font-bold hover:bg-oxblood/20 transition flex items-center gap-1.5"
                  >
                    <Sparkles className={`w-3.5 h-3.5 ${schedGeneratingQuestions ? 'animate-spin' : ''}`} />
                    <span>{schedGeneratingQuestions ? "Generating..." : "Generate AI Questions"}</span>
                  </button>
                </div>

                {schedQuestions.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {schedQuestions.map((q, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-xl bg-white/70 dark:bg-black/30 border border-slate/15 dark:border-rose/15 text-xs flex justify-between items-start gap-2"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.5 rounded bg-slate/10 font-bold text-[10px]">
                              Q{idx + 1}
                            </span>
                            <span className="px-1.5 py-0.5 rounded bg-oxblood/10 text-oxblood dark:text-rose font-bold text-[10px]">
                              {q.question_type}
                            </span>
                            <span className="text-[10px] text-slate/50">
                              {q.max_duration_seconds || 180}s
                            </span>
                          </div>
                          <p className="text-slate/80 dark:text-ivory/80 font-sans">
                            {q.question_text}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSchedQuestions(schedQuestions.filter((_, i) => i !== idx))}
                          className="p-1 hover:text-error transition"
                          title="Remove Question"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate/50 font-sans py-2">
                    Click "Generate AI Questions" or add custom questions below to prime the AI interviewer.
                  </p>
                )}

                {/* Add Custom Question Row */}
                <div className="flex gap-2 pt-2">
                  <input
                    type="text"
                    placeholder="Add a custom technical or situational question..."
                    value={schedNewQuestionText}
                    onChange={(e) => setSchedNewQuestionText(e.target.value)}
                    className="flex-1 glass-input text-xs min-h-[38px]"
                  />
                  <select
                    value={schedNewQuestionType}
                    onChange={(e) => setSchedNewQuestionType(e.target.value)}
                    className="glass-input text-xs min-h-[38px] w-32"
                  >
                    <option value="TECHNICAL">Technical</option>
                    <option value="PROBLEM_SOLVING">Problem Solving</option>
                    <option value="BEHAVIORAL">Behavioral</option>
                    <option value="ROLE_SPECIFIC">Role Specific</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => {
                      if (!schedNewQuestionText.trim()) return;
                      setSchedQuestions([
                        ...schedQuestions,
                        {
                          sequence_number: schedQuestions.length + 1,
                          question_text: schedNewQuestionText.trim(),
                          question_type: schedNewQuestionType,
                          source: 'CUSTOM',
                          max_duration_seconds: 180
                        }
                      ]);
                      setSchedNewQuestionText('');
                    }}
                    className="px-3 py-1.5 rounded-xl border border-slate/20 text-xs font-bold hover:border-oxblood"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
              Meeting Video Link
            </label>
            <input
              type="text"
              placeholder="e.g. https://meet.google.com/xyz-abcd-efg"
              value={schedLink}
              onChange={(e) => setSchedLink(e.target.value)}
              className="w-full glass-input text-xs min-h-[44px]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
              Location Coordinates (If in-person)
            </label>
            <input
              type="text"
              placeholder="e.g. Conference Room 3B, Tech Park Campus"
              value={schedLocation}
              onChange={(e) => setSchedLocation(e.target.value)}
              className="w-full glass-input text-xs min-h-[44px]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1">
              Instructions for Candidate
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Please join 5 minutes early with your system architecture diagrams..."
              value={schedInstructions}
              onChange={(e) => setSchedInstructions(e.target.value)}
              className="w-full glass-input text-xs font-sans"
            />
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowScheduleModal(false)}
              className="min-h-[44px] px-5 py-2.5 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory text-xs font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={scheduling}
              className="min-h-[44px] px-6 py-2.5 btn-oxblood text-xs font-bold rounded-xl shadow-xs disabled:opacity-50 flex items-center gap-1.5"
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>{scheduling ? "Scheduling..." : "Confirm Schedule"}</span>
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ======================================================== */}
      {/* CANDIDATE COMPARISON MATRIX MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        title="Candidate Comparison Matrix"
      >
        <p className="text-xs text-slate/70 dark:text-ivory/65 -mt-3 mb-5 font-normal font-mono">
          Side-by-side technical evaluation, match telemetry, and recommendation matrix.
        </p>

        {compareLoading ? (
          <div className="py-12 text-center font-mono text-xs text-slate/50">
            Generating side-by-side candidate comparison matrix...
          </div>
        ) : compareData.length === 0 ? (
          <div className="py-12 text-center font-mono text-xs text-slate/50">
            No applicants found for this position to compare.
          </div>
        ) : (
          <div className="overflow-x-auto font-mono text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 uppercase text-[10px] font-bold">
                  <th className="py-3 px-3">Candidate</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Match</th>
                  <th className="py-3 px-3">Exp</th>
                  <th className="py-3 px-3">Matching Skills</th>
                  <th className="py-3 px-3">Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate/10 dark:divide-white/5">
                {compareData.map((cand) => (
                  <tr key={cand.application_id || cand.id} className="hover:bg-slate/5 dark:hover:bg-white/5">
                    <td className="py-3 px-3 font-bold text-charcoal dark:text-ivory">
                      {cand.candidate_name || cand.name}
                    </td>
                    <td className="py-3 px-3">
                      <span className="badge-slate text-[10px] px-2 py-0.5 rounded font-bold">
                        {cand.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="badge-selected text-[10px] px-2 py-0.5 rounded font-bold">
                        {Math.round(cand.match_score || 85)}%
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {cand.total_years_exp || 0} yrs
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(cand.matching_skills || []).slice(0, 3).map((sk, idx) => (
                          <span key={idx} className="bg-slate/10 dark:bg-white/5 text-[9px] px-1.5 py-0.5 rounded">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        cand.average_recommendation === 'STRONG_HIRE' ? 'badge-selected' :
                        cand.average_recommendation === 'HIRE' ? 'badge-selected' :
                        cand.average_recommendation === 'HOLD' ? 'badge-amber' : 'badge-slate'
                      }`}>
                        {cand.average_recommendation || 'PENDING'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassModal>

      {/* Centralized Candidate Dossier Modal */}
      {dossierCandidateId && (
        <CandidateDossierModal
          candidateId={dossierCandidateId}
          onClose={() => setDossierCandidateId(null)}
        />
      )}

    </PageTransition>
  );
};
