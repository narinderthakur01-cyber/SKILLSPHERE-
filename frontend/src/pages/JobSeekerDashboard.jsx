import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { resumeAPI, jobsAPI, applicationAPI, savedJobsAPI, interviewsAPI, messagesAPI, practiceAPI, assessmentsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  PageTransition,
  GlassModal,
  AnimatedProgressRing,
  AnimatedCounter,
  LiquidSpotlightCard,
  MagneticButton,
  StaggerContainer,
  StaggerItem,
  useToast,
  usePrefersReducedMotion
} from '../components/MotionComponents';
import {
  Briefcase, FileText, CheckCircle2, AlertCircle, Clock, MapPin, Building,
  Upload, Sparkles, X, Plus, Search, Filter, ArrowUpRight, Award, ChevronRight,
  RefreshCw, Check, AlertTriangle, UserCheck, Download, ExternalLink, Calendar,
  GraduationCap, Layers, ArrowRight, ShieldCheck, Trash2, Eye, HelpCircle,
  Bookmark, BookmarkCheck, MessageSquare, Send, CheckCheck, Video, PhoneCall, Star,
  Terminal, Cpu, Code, Zap, Play, Lightbulb, Film, LifeBuoy
} from 'lucide-react';
import { CandidateAssessmentsSection } from '../components/CandidateAssessmentsSection';
import { CandidateVideoAssessmentsSection } from '../components/CandidateVideoAssessmentsSection';
import { CandidateMediaLibrarySection } from '../components/CandidateMediaLibrarySection';
import { UserSupportTicketsTab } from '../components/UserSupportTicketsTab';

export const JobSeekerDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const shouldReduceMotion = usePrefersReducedMotion();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'jobs';

  // Jobs state
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [keyword, setKeyword] = useState(searchParams.get('keyword') || '');
  const [location, setLocation] = useState(searchParams.get('location') || '');
  const [jobType, setJobType] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [selectedJob, setSelectedJob] = useState(null);

  // Resume & OCR state
  const [resumes, setResumes] = useState([]);
  const [profile, setProfile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStage, setUploadStage] = useState('idle'); // 'idle' | 'uploading' | 'ocr_parsing' | 'extracting_graph' | 'complete'
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');

  // Editable Profile Form state
  const [formName, setFormName] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formTitle, setFormTitle] = useState('');
  const [formLocation, setFormLocation] = useState('');
  const [formBio, setFormBio] = useState('');
  const [formSkills, setFormSkills] = useState([]);
  const [formEducation, setFormEducation] = useState([]);
  const [formExperience, setFormExperience] = useState([]);
  const [formTotalYearsExp, setFormTotalYearsExp] = useState(0);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Matching Analysis state
  const [matchAnalysis, setMatchAnalysis] = useState(null);
  const [analyzingMatch, setAnalyzingMatch] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [analyzedJobTitle, setAnalyzedJobTitle] = useState('');

  // Application submission state
  const [applications, setApplications] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState('');
  const [applySuccess, setApplySuccess] = useState('');
  const [showApplyModal, setShowApplyModal] = useState(false);

  // Saved Jobs state
  const [savedJobs, setSavedJobs] = useState([]);
  const [savedJobIds, setSavedJobIds] = useState(new Set());
  const [savedLoading, setSavedLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);

  // Interviews state
  const [myInterviews, setMyInterviews] = useState([]);
  const [interviewsLoading, setInterviewsLoading] = useState(false);
  const [prepInterview, setPrepInterview] = useState(null);
  const [prepConsentGranted, setPrepConsentGranted] = useState(false);
  const [deviceTestActive, setDeviceTestActive] = useState(false);
  const [deviceTestPassed, setDeviceTestPassed] = useState(false);
  const prepVideoRef = useRef(null);
  const [prepStream, setPrepStream] = useState(null);

  // Messaging state
  const [conversations, setConversations] = useState([]);
  const [activePartner, setActivePartner] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [messageText, setMessageText] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  // AI Resume Intelligence state
  const [qualityFeedback, setQualityFeedback] = useState(null);
  const [qualityLoading, setQualityLoading] = useState(false);

  // Technical Practice state
  const [practiceTechs, setPracticeTechs] = useState([]);
  const [practiceLoading, setPracticeLoading] = useState(false);
  const [selectedTech, setSelectedTech] = useState(null);
  const [practiceBatch, setPracticeBatch] = useState(1);
  const [practiceQuestions, setPracticeQuestions] = useState([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [attemptResult, setAttemptResult] = useState(null);
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [showingHint, setShowingHint] = useState(false);
  const [newManualTechInput, setNewManualTechInput] = useState('');
  const [addingManualTech, setAddingManualTech] = useState(false);
  const [practiceAnalytics, setPracticeAnalytics] = useState(null);
  const [generatingMore, setGeneratingMore] = useState(false);
  const [detectingResumeTech, setDetectingResumeTech] = useState(false);
  const [batchCompleted, setBatchCompleted] = useState(false);

  useEffect(() => {
    fetchResumes();
    fetchProfile();
    fetchApplications();
    fetchJobs();
    fetchSavedJobs();
    fetchRecommendations();
    fetchInterviews();
    fetchConversations();
    fetchQualityFeedback();
    fetchPracticeTechs();
    fetchPracticeAnalytics();
  }, []);

  useEffect(() => {
    if (activePartner) {
      fetchThread(activePartner.partner_id || activePartner.id);
    }
  }, [activePartner]);

  const fetchPracticeTechs = async () => {
    try {
      setPracticeLoading(true);
      const res = await practiceAPI.getTechnologies();
      setPracticeTechs(res.data || []);
    } catch (err) {
      console.error("Failed to fetch practice technologies:", err);
    } finally {
      setPracticeLoading(false);
    }
  };

  const fetchPracticeAnalytics = async () => {
    try {
      const res = await practiceAPI.getAnalytics();
      setPracticeAnalytics(res.data || null);
    } catch (err) {
      console.error("Failed to load practice analytics:", err);
    }
  };

  const fetchPracticeQuestions = async (techName, batch = 1) => {
    try {
      setQuestionsLoading(true);
      setAttemptResult(null);
      setSelectedAnswer('');
      setShowingHint(false);
      setBatchCompleted(false);
      setCurrentQIndex(0);
      const res = await practiceAPI.getQuestions(techName, batch);
      setPracticeQuestions(res.data || []);
    } catch (err) {
      console.error("Failed to load questions:", err);
      addToast({ title: "Failed to load practice questions", type: "error" });
    } finally {
      setQuestionsLoading(false);
    }
  };

  const handleSelectTech = (tech) => {
    setSelectedTech(tech);
    setPracticeBatch(1);
    fetchPracticeQuestions(tech.technology_name, 1);
  };

  const handleSubmitAttempt = async () => {
    if (!selectedAnswer.trim() || !practiceQuestions[currentQIndex]) return;
    try {
      setSubmittingAnswer(true);
      const q = practiceQuestions[currentQIndex];
      const res = await practiceAPI.submitAttempt(q.id, {
        candidate_answer: selectedAnswer.trim(),
        time_spent_seconds: 30,
        hints_used: showingHint ? 1 : 0
      });
      setAttemptResult(res.data);
      if (res.data.is_correct) {
        addToast({ title: "Correct Answer! +10 Points", type: "success" });
      } else {
        addToast({ title: "Incorrect. Review the explanation below.", type: "warning" });
      }
      fetchPracticeAnalytics();
    } catch (err) {
      console.error("Attempt submission failed:", err);
      addToast({ title: "Failed to record answer", type: "error" });
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQIndex < practiceQuestions.length - 1) {
      setCurrentQIndex(prev => prev + 1);
      setSelectedAnswer('');
      setAttemptResult(null);
      setShowingHint(false);
    } else {
      setBatchCompleted(true);
    }
  };

  const handleNextBatch = () => {
    const nextB = practiceBatch + 1;
    setPracticeBatch(nextB);
    fetchPracticeQuestions(selectedTech.technology_name, nextB);
  };

  const handleGenerateMoreQuestions = async () => {
    if (!selectedTech) return;
    try {
      setGeneratingMore(true);
      const res = await practiceAPI.generateMoreQuestions(selectedTech.technology_name);
      addToast({ title: "Generated 10 additional non-duplicate questions!", type: "success" });
      setPracticeBatch(prev => prev + 1);
      setPracticeQuestions(res.data || []);
      setCurrentQIndex(0);
      setSelectedAnswer('');
      setAttemptResult(null);
      setShowingHint(false);
      setBatchCompleted(false);
      fetchPracticeAnalytics();
    } catch (err) {
      console.error("Failed to generate more questions:", err);
      addToast({ title: "Failed to generate questions", type: "error" });
    } finally {
      setGeneratingMore(false);
    }
  };

  const handleAddManualTech = async (e) => {
    e.preventDefault();
    if (!newManualTechInput.trim()) return;
    try {
      setAddingManualTech(true);
      await practiceAPI.addTechnology({
        technology_name: newManualTechInput.trim(),
        category: 'LANGUAGE',
        proficiency_level: 'INTERMEDIATE'
      });
      addToast({ title: `Added ${newManualTechInput.trim()} to practice roadmap!`, type: "success" });
      setNewManualTechInput('');
      fetchPracticeTechs();
    } catch (err) {
      console.error("Failed to add technology:", err);
      addToast({ title: "Failed to add technology", type: "error" });
    } finally {
      setAddingManualTech(false);
    }
  };

  const handleRemovePracticeTech = async (techName) => {
    try {
      await practiceAPI.removeTechnology(techName);
      addToast({ title: `Removed ${techName}`, type: "info" });
      if (selectedTech?.technology_name === techName) {
        setSelectedTech(null);
      }
      fetchPracticeTechs();
      fetchPracticeAnalytics();
    } catch (err) {
      console.error("Failed to remove technology:", err);
    }
  };

  const handleSyncResumeTechnologies = async () => {
    try {
      setDetectingResumeTech(true);
      const res = await practiceAPI.detectFromResume();
      setPracticeTechs(res.data || []);
      addToast({ title: `Synchronized ${res.data?.length || 0} technologies from your resume!`, type: "success" });
      fetchPracticeAnalytics();
    } catch (err) {
      console.error("Failed to sync resume technologies:", err);
      addToast({ title: "Sync failed. Ensure a resume has been uploaded.", type: "error" });
    } finally {
      setDetectingResumeTech(false);
    }
  };

  const fetchSavedJobs = async () => {
    try {
      setSavedLoading(true);
      const res = await savedJobsAPI.list();
      setSavedJobs(res.data || []);
      setSavedJobIds(new Set((res.data || []).map(sj => sj.job_id || sj.id)));
    } catch (err) {
      console.error("Failed to load saved jobs:", err);
    } finally {
      setSavedLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      setRecsLoading(true);
      const res = await savedJobsAPI.getRecommendations();
      setRecommendations(res.data || []);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
    } finally {
      setRecsLoading(false);
    }
  };

  const toggleSaveJob = async (jobId) => {
    const isSaved = savedJobIds.has(jobId);
    const nextSavedIds = new Set(savedJobIds);
    if (isSaved) {
      nextSavedIds.delete(jobId);
      setSavedJobIds(nextSavedIds);
      setSavedJobs(prev => prev.filter(j => (j.job_id || j.id) !== jobId));
      try {
        await savedJobsAPI.unsave(jobId);
        addToast("Job removed from saved bookmarks", "info");
      } catch (err) {
        fetchSavedJobs();
        addToast("Failed to remove saved job", "error");
      }
    } else {
      nextSavedIds.add(jobId);
      setSavedJobIds(nextSavedIds);
      try {
        await savedJobsAPI.save(jobId);
        addToast("Job bookmarked successfully!", "success");
        fetchSavedJobs();
      } catch (err) {
        fetchSavedJobs();
        addToast("Failed to save job", "error");
      }
    }
  };

  const fetchInterviews = async () => {
    try {
      setInterviewsLoading(true);
      const res = await interviewsAPI.getMy();
      setMyInterviews(res.data || []);
    } catch (err) {
      console.error("Failed to load interviews:", err);
    } finally {
      setInterviewsLoading(false);
    }
  };

  const handleOpenPrepModal = (inv) => {
    setPrepInterview(inv);
    setPrepConsentGranted(false);
    setDeviceTestActive(false);
    setDeviceTestPassed(false);
  };

  useEffect(() => {
    if (prepVideoRef.current && prepStream) {
      prepVideoRef.current.srcObject = prepStream;
    }
  }, [prepStream, deviceTestActive]);

  useEffect(() => {
    return () => {
      if (prepStream) {
        prepStream.getTracks().forEach(t => t.stop());
      }
    };
  }, [prepStream]);

  const handleStartDeviceTest = async () => {
    try {
      setDeviceTestActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setPrepStream(stream);
      if (prepVideoRef.current) {
        prepVideoRef.current.srcObject = stream;
      }
      setDeviceTestPassed(true);
      addToast("Camera and microphone verified successfully!", "success");
    } catch (err) {
      console.warn("Device check notice:", err);
      setDeviceTestPassed(true);
      addToast("Proceeding with available audio/video permissions.", "info");
    }
  };

  const handleClosePrepModal = () => {
    if (prepStream) {
      prepStream.getTracks().forEach(t => t.stop());
      setPrepStream(null);
    }
    setPrepInterview(null);
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

  const fetchQualityFeedback = async () => {
    try {
      setQualityLoading(true);
      const res = await resumeAPI.getQualityFeedback();
      setQualityFeedback(res.data);
    } catch (err) {
      console.error("Failed to fetch quality feedback:", err);
    } finally {
      setQualityLoading(false);
    }
  };

  const setTab = (tabName) => {
    setSearchParams({ tab: tabName });
  };

  const fetchJobs = async () => {
    try {
      setJobsLoading(true);
      const params = {};
      if (keyword) params.keyword = keyword;
      if (location) params.location = location;
      if (jobType) params.job_type = jobType;
      const res = await jobsAPI.list(params);
      setJobs(res.data.items || []);
    } catch (err) {
      console.error("Failed to load jobs:", err);
      addToast("Failed to fetch active job openings.", "error");
    } finally {
      setJobsLoading(false);
    }
  };

  const fetchResumes = async () => {
    try {
      const res = await resumeAPI.getMyResumes();
      setResumes(res.data || []);
      if (res.data.length > 0 && !selectedResumeId) {
        setSelectedResumeId(res.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load resumes:", err);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await resumeAPI.getProfile();
      setProfile(res.data);
      setFormName(res.data.name || '');
      setFormPhone(res.data.phone || '');
      setFormTitle(res.data.title || '');
      setFormLocation(res.data.location || '');
      setFormBio(res.data.bio || '');
      setFormSkills(res.data.skills || []);
      setFormEducation(res.data.education || []);
      setFormExperience(res.data.experience || []);
      setFormTotalYearsExp(res.data.total_years_exp || 0);
    } catch (err) {
      console.error("Failed to load profile:", err);
    }
  };

  const fetchApplications = async () => {
    try {
      const res = await applicationAPI.getMyApplications();
      setApplications(res.data || []);
    } catch (err) {
      console.error("Failed to load applications:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // File validation: Size <= 10MB
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File exceeds the 10MB size limit. Please upload a smaller PDF or image.");
      return;
    }

    setUploading(true);
    setUploadStage('uploading');
    setUploadError('');
    setUploadSuccess('');

    // Simulated progress stage timing while API executes
    const stage1 = setTimeout(() => setUploadStage('ocr_parsing'), 800);
    const stage2 = setTimeout(() => setUploadStage('extracting_graph'), 1800);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await resumeAPI.upload(formData);
      setUploadStage('complete');
      setUploadSuccess(`Resume '${file.name}' parsed successfully with dual OCR extraction! Review verified skills below.`);
      addToast("Resume parsed with dual OCR extraction!", "success");
      fetchResumes();
      fetchProfile();
    } catch (err) {
      console.error("Resume upload error:", err);
      const detail = err.response?.data?.detail;
      setUploadError(typeof detail === 'string' ? detail : "Failed to parse resume file.");
      addToast("Failed to parse resume file.", "error");
      setUploadStage('idle');
    } finally {
      clearTimeout(stage1);
      clearTimeout(stage2);
      setUploading(false);
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setSaveMessage('');
    try {
      const payload = {
        name: formName,
        phone: formPhone,
        title: formTitle,
        location: formLocation,
        bio: formBio,
        skills: formSkills,
        education: formEducation,
        experience: formExperience,
        total_years_exp: parseFloat(formTotalYearsExp) || 0.0,
      };
      await resumeAPI.updateProfile(payload);
      setSaveMessage("Profile and verified skills saved successfully!");
      addToast("Candidate passport profile saved!", "success");
      fetchProfile();
    } catch (err) {
      console.error("Save profile error:", err);
      addToast("Failed to save profile changes.", "error");
    } finally {
      setSavingProfile(false);
    }
  };

  const updateExperience = (index, field, value) => {
    const updated = [...formExperience];
    updated[index] = { ...updated[index], [field]: value };
    setFormExperience(updated);
  };

  const addExperienceItem = () => {
    setFormExperience([...formExperience, { title: '', company: '', duration: '', description: '' }]);
  };

  const removeExperienceItem = (index) => {
    setFormExperience(formExperience.filter((_, i) => i !== index));
  };

  const updateEducation = (index, field, value) => {
    const updated = [...formEducation];
    updated[index] = { ...updated[index], [field]: value };
    setFormEducation(updated);
  };

  const addEducationItem = () => {
    setFormEducation([...formEducation, { degree: '', institution: '', year: '', grade: '' }]);
  };

  const removeEducationItem = (index) => {
    setFormEducation(formEducation.filter((_, i) => i !== index));
  };

  const addSkill = () => {
    if (newSkillInput.trim() && !formSkills.includes(newSkillInput.trim())) {
      setFormSkills([...formSkills, newSkillInput.trim()]);
      setNewSkillInput('');
    }
  };

  const removeSkill = (skillToRemove) => {
    setFormSkills(formSkills.filter(s => s !== skillToRemove));
  };

  const handleAnalyzeMatch = async (job) => {
    if (resumes.length === 0) {
      addToast("Please upload a resume first in 'My Resumes & OCR'.", "info");
      setTab('resumes');
      return;
    }
    setAnalyzingMatch(true);
    setMatchAnalysis(null);
    setAnalyzedJobTitle(job.title);
    setShowMatchModal(true);

    try {
      const resumeId = selectedResumeId || resumes[0].id;
      const res = await resumeAPI.analyze({
        resume_id: resumeId,
        job_id: job.id
      });
      setMatchAnalysis(res.data);
    } catch (err) {
      console.error("Match analysis error:", err);
      addToast("Could not calculate skill match telemetry.", "error");
      setShowMatchModal(false);
    } finally {
      setAnalyzingMatch(false);
    }
  };

  const openApplyModal = (job) => {
    setSelectedJob(job);
    setApplyError('');
    setApplySuccess('');
    setShowApplyModal(true);
  };

  const handleApplyToJob = async () => {
    if (!selectedResumeId) {
      setApplyError("Please select an attached resume to submit your application.");
      return;
    }
    setApplying(true);
    setApplyError('');
    setApplySuccess('');

    try {
      await applicationAPI.apply(selectedJob.id, {
        resume_id: selectedResumeId,
        cover_letter: coverLetter
      });
      setApplySuccess("Application submitted successfully! Track real-time status in 'My Applications'.");
      addToast(`Applied successfully to ${selectedJob.title}!`, "success");
      fetchApplications();
      setTimeout(() => {
        setShowApplyModal(false);
        setCoverLetter('');
      }, 1200);
    } catch (err) {
      console.error("Application error:", err);
      const detail = err.response?.data?.detail;
      setApplyError(typeof detail === 'string' ? detail : "Failed to submit application.");
      addToast(typeof detail === 'string' ? detail : "Application submission failed.", "error");
    } finally {
      setApplying(false);
    }
  };

  const handleWithdraw = async (applicationId) => {
    if (!window.confirm("Are you sure you want to withdraw this application? You can reapply later if the job opening remains active.")) return;
    try {
      await applicationAPI.withdraw(applicationId);
      addToast("Application withdrawn successfully.", "info");
      fetchApplications();
    } catch (err) {
      alert(err.response?.data?.detail || "Could not withdraw application.");
    }
  };

  const isAlreadyApplied = (jobId) => {
    return applications.some(app => app.job_id === jobId && app.status !== 'WITHDRAWN');
  };

  // Profile completeness score
  const completeness = useMemo(() => {
    let score = 0;
    if (profile?.name || user?.name) score += 15;
    if (profile?.title) score += 15;
    if (profile?.bio) score += 15;
    if (profile?.skills?.length > 0) score += 25;
    if (profile?.experience?.length > 0) score += 15;
    if (resumes.length > 0) score += 15;
    return Math.min(score, 100);
  }, [profile, user, resumes]);

  // Filtered & Sorted Jobs
  const processedJobs = useMemo(() => {
    let result = [...jobs];
    if (sortBy === 'salary_high') {
      result.sort((a, b) => (b.salary_max || 0) - (a.salary_max || 0));
    } else if (sortBy === 'exp_low') {
      result.sort((a, b) => (a.experience_min || 0) - (b.experience_min || 0));
    }
    return result;
  }, [jobs, sortBy]);

  // Application counts by status
  const selectedCount = applications.filter(a => a.status === 'SELECTED').length;
  const inProgressCount = applications.filter(a => ['APPLIED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEW'].includes(a.status)).length;

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
      case 'INTERVIEW':
        return (
          <span className="badge-oxblood font-mono text-[11px] font-bold px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#914F51]"></span>
            <span>INTERVIEW SCHEDULED</span>
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="badge-slate font-mono text-[11px] font-medium px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate/40 dark:bg-ivory/40"></span>
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
            <span>NOT SELECTED</span>
          </span>
        );
      case 'WITHDRAWN':
        return (
          <span className="opacity-50 font-mono text-[11px] font-medium px-3 py-1 rounded-full inline-flex items-center gap-1.5">
            <span>WITHDRAWN</span>
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
          {/* WORKSPACE EDITORIAL HEADER & METRICS GRID */}
          {/* ======================================================== */}
          <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-slate/15 dark:border-rose/15">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-tight text-charcoal dark:text-ivory">
                    Candidate Workspace
                  </h1>
                  <span className="badge-selected font-mono text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                    VERIFIED PROFILE
                  </span>
                </div>
                <p className="text-sm text-slate/80 dark:text-ivory/70 mt-1 font-normal leading-relaxed">
                  Welcome back, <span className="font-semibold text-charcoal dark:text-ivory">{profile?.name || user?.name}</span>. Explore compatible openings, review OCR extraction, and track applications.
                </p>
              </div>

              {/* Progress Ring & Profile Telemetry */}
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <AnimatedProgressRing percentage={completeness} size={54} strokeWidth={5} color="#914F51" />
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate/60 dark:text-rose">Profile Score</p>
                    <p className="text-xs font-mono font-bold text-charcoal dark:text-ivory">{completeness}% Complete</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 pl-4 border-l border-slate/15 dark:border-rose/15">
                  <div className="text-right">
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate/60 dark:text-rose">Verified Skills</p>
                    <p className="text-sm font-mono font-bold text-charcoal dark:text-ivory">
                      {profile?.skills?.length || 0} Detected
                    </p>
                  </div>
                  <div className="w-11 h-11 rounded-2xl bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal font-mono font-bold flex items-center justify-center text-sm shadow-sm ring-1 ring-oxblood/30">
                    {profile?.skills?.length || 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Metrics Bar with Animated Counters */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 text-center font-mono">
              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                  <AnimatedCounter value={applications.length} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Submitted Apps</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-success">
                  <AnimatedCounter value={selectedCount} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Offers / Selected</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-oxblood dark:text-rose">
                  <AnimatedCounter value={inProgressCount} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Under Review</p>
              </div>

              <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                  <AnimatedCounter value={jobs.length} />
                </p>
                <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Active Roles</p>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* TAB NAVIGATION WITH ANIMATED PILL */}
          {/* ======================================================== */}
          <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 overflow-x-auto pb-1 scrollbar-none" role="tablist">
            {[
              { id: 'jobs', label: `Browse Jobs (${jobs.length})`, icon: Search },
              { id: 'saved', label: `Saved Jobs (${savedJobs.length})`, icon: Bookmark },
              { id: 'assessments', label: 'First-Round Assessments', icon: Award },
              { id: 'video-assessments', label: 'Video Assessments', icon: Video },
              { id: 'media', label: 'My Media', icon: Film },
              { id: 'interviews', label: `Interviews (${myInterviews.length})`, icon: Calendar },
              { id: 'messages', label: 'Messages', icon: MessageSquare },
              { id: 'practice', label: `Tech Practice (${practiceTechs.length})`, icon: Terminal },
              { id: 'resumes', label: `Resumes & AI Intel (${resumes.length})`, icon: Upload },
              { id: 'applications', label: `Applications (${applications.length})`, icon: Briefcase },
              { id: 'tickets', label: 'Support Tickets', icon: LifeBuoy },
              { id: 'profile', label: 'Candidate Passport', icon: UserCheck }
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
                      layoutId="candidateTabPill"
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
          {/* TAB 1: BROWSE JOBS & EXPLAINABLE MATCH */}
          {/* ======================================================== */}
          {activeTab === 'jobs' && (
            <div className="space-y-6">
              
              {/* Filter and Search Bar */}
              <div className="glass-card p-4 sm:p-5 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-md flex flex-col md:flex-row gap-3 items-center">
                <div className="flex-1 w-full flex items-center px-4 py-2 bg-white/50 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 min-h-[44px]">
                  <Search className="w-4 h-4 text-slate/40 dark:text-rose/50 mr-2.5 shrink-0" />
                  <input
                    type="text"
                    placeholder="Search by title, technology, role..."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') fetchJobs(); }}
                    className="w-full text-xs bg-transparent focus:outline-none text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 font-medium"
                  />
                </div>

                <div className="w-full md:w-48 flex items-center px-4 py-2 bg-white/50 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 min-h-[44px]">
                  <MapPin className="w-4 h-4 text-slate/40 dark:text-rose/50 mr-2.5 shrink-0" />
                  <input
                    type="text"
                    placeholder="Location / Remote..."
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') fetchJobs(); }}
                    className="w-full text-xs bg-transparent focus:outline-none text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 font-medium"
                  />
                </div>

                <select
                  value={jobType}
                  onChange={(e) => setJobType(e.target.value)}
                  className="w-full md:w-40 min-h-[44px] glass-input text-xs"
                >
                  <option value="">All Job Types</option>
                  <option value="FULL_TIME">Full Time</option>
                  <option value="PART_TIME">Part Time</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="REMOTE">Remote</option>
                  <option value="INTERNSHIP">Internship</option>
                </select>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full md:w-44 min-h-[44px] glass-input text-xs"
                >
                  <option value="newest">Sort: Newest First</option>
                  <option value="salary_high">Sort: Salary (High to Low)</option>
                  <option value="exp_low">Sort: Experience (Entry First)</option>
                </select>

                <button
                  onClick={fetchJobs}
                  className="w-full md:w-auto px-5 py-2.5 min-h-[44px] btn-oxblood text-xs font-mono font-bold uppercase rounded-xl transition flex items-center justify-center gap-1.5"
                >
                  <Filter className="w-3.5 h-3.5" />
                  <span>Filter</span>
                </button>
              </div>

              {/* Job Cards Grid */}
              {jobsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3, 4, 5, 6].map((n) => (
                    <div key={n} className="h-56 glass-card rounded-3xl animate-pulse"></div>
                  ))}
                </div>
              ) : processedJobs.length === 0 ? (
                <div className="text-center py-16 glass-card rounded-3xl p-8 border border-slate/15 dark:border-rose/15">
                  <Briefcase className="w-12 h-12 text-slate/30 dark:text-ivory/30 mx-auto mb-3" />
                  <p className="font-display text-base font-bold text-charcoal dark:text-ivory">No job openings found matching your criteria.</p>
                  <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">Try adjusting your keyword, location, or employment type filter.</p>
                </div>
              ) : (
                <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {processedJobs.map((job) => {
                    const alreadyApplied = isAlreadyApplied(job.id);
                    return (
                      <StaggerItem key={job.id}>
                        <LiquidSpotlightCard className="p-6 rounded-3xl flex flex-col justify-between border border-slate/15 dark:border-rose/15 shadow-md h-full">
                          <div>
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <span className="font-mono text-[10px] font-semibold text-oxblood dark:text-rose uppercase tracking-wider block">
                                  {job.company?.company_name || "Featured Employer"}
                                </span>
                                <h3 className="font-display font-bold text-charcoal dark:text-ivory text-base sm:text-lg mt-0.5 leading-snug">
                                  {job.title}
                                </h3>
                              </div>
                              <div className="flex items-center gap-1.5 shrink-0">
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); toggleSaveJob(job.id); }}
                                  className="p-1.5 rounded-lg border border-slate/15 dark:border-rose/15 hover:border-oxblood/40 text-slate/60 dark:text-ivory/60 hover:text-oxblood transition min-h-[32px] min-w-[32px] flex items-center justify-center"
                                  title={savedJobIds.has(job.id) ? "Remove bookmark" : "Save job"}
                                >
                                  {savedJobIds.has(job.id) ? (
                                    <BookmarkCheck className="w-4 h-4 text-oxblood dark:text-rose fill-oxblood/20" />
                                  ) : (
                                    <Bookmark className="w-4 h-4" />
                                  )}
                                </button>
                                <span className="badge-slate text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded-full shrink-0">
                                  {job.job_type.replace('_', ' ')}
                                </span>
                              </div>
                            </div>

                            <div className="mt-3 flex items-center gap-2 text-xs font-mono text-slate/70 dark:text-ivory/60">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3.5 h-3.5 text-slate/50 dark:text-ivory/40" />
                                <span>{job.location}</span>
                              </span>
                              <span>•</span>
                              <span>{job.experience_min} - {job.experience_max} yrs</span>
                            </div>

                            {/* Required Skills Chips */}
                            <div className="mt-4 flex flex-wrap gap-1.5">
                              {job.required_skills?.slice(0, 4).map((sk, idx) => (
                                <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory font-medium">
                                  {sk}
                                </span>
                              ))}
                              {job.required_skills?.length > 4 && (
                                <span className="text-[11px] font-mono text-slate/60 dark:text-ivory/40 px-1 py-0.5">
                                  +{job.required_skills.length - 4} more
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15">
                            <div className="flex justify-between items-center mb-3">
                              <div>
                                <span className="block text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/40">Compensation</span>
                                <span className="font-mono text-xs font-bold text-charcoal dark:text-ivory">
                                  {job.salary_min && job.salary_max
                                    ? `₹${(job.salary_min/100000).toFixed(1)}L - ₹${(job.salary_max/100000).toFixed(1)}L`
                                    : "Competitive"}
                                </span>
                              </div>

                              {alreadyApplied && (
                                <span className="badge-selected text-[10px] font-mono font-bold px-2.5 py-1 rounded-full flex items-center gap-1">
                                  <Check className="w-3 h-3" />
                                  <span>APPLIED</span>
                                </span>
                              )}
                            </div>

                            <div className="flex gap-2">
                              <button
                                onClick={() => handleAnalyzeMatch(job)}
                                className="flex-1 min-h-[44px] py-2 px-3 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory hover:border-oxblood/40 font-mono text-xs font-bold transition flex items-center justify-center gap-1"
                                title="Run deterministic skill overlap analysis"
                              >
                                <Sparkles className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                                <span>Analyze Match</span>
                              </button>

                              {!alreadyApplied ? (
                                <button
                                  onClick={() => openApplyModal(job)}
                                  className="min-h-[44px] px-5 py-2 btn-oxblood font-display font-semibold text-xs rounded-xl transition flex items-center justify-center gap-1 shadow-xs"
                                >
                                  <span>Apply</span>
                                  <ArrowUpRight className="w-3.5 h-3.5" />
                                </button>
                              ) : (
                                <button
                                  onClick={() => setTab('applications')}
                                  className="min-h-[44px] px-3.5 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-slate/60 dark:text-ivory/60 font-mono text-xs hover:text-charcoal dark:hover:text-ivory transition"
                                >
                                  View
                                </button>
                              )}
                            </div>
                          </div>
                        </LiquidSpotlightCard>
                      </StaggerItem>
                    );
                  })}
                </StaggerContainer>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: SAVED JOBS & AI RECOMMENDATIONS */}
          {/* ======================================================== */}
          {activeTab === 'saved' && (
            <div className="space-y-8">
              {/* Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Bookmark className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Saved Opportunities ({savedJobs.length})</span>
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Curated roles you have bookmarked for priority application and tracking.
                  </p>
                </div>
                <button
                  onClick={fetchSavedJobs}
                  className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
              </div>

              {savedLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((n) => (
                    <div key={n} className="h-56 glass-card rounded-3xl animate-pulse"></div>
                  ))}
                </div>
              ) : savedJobs.length === 0 ? (
                <div className="text-center py-12 glass-card rounded-3xl p-8 border border-slate/15 dark:border-rose/15">
                  <Bookmark className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">No jobs bookmarked yet.</p>
                  <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">Browse open roles and click the bookmark icon to save opportunities here.</p>
                  <button
                    onClick={() => setTab('jobs')}
                    className="mt-4 btn-oxblood px-5 py-2 rounded-xl text-xs font-display font-semibold inline-flex items-center gap-1.5 min-h-[44px]"
                  >
                    <span>Browse Open Positions</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {savedJobs.map((item) => {
                    const job = item.job || item;
                    const jobId = item.job_id || item.id;
                    const alreadyApplied = isAlreadyApplied(jobId);
                    return (
                      <StaggerItem key={jobId}>
                        <LiquidSpotlightCard className="p-6 rounded-3xl flex flex-col justify-between border border-slate/15 dark:border-rose/15 shadow-md h-full">
                          <div>
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <span className="font-mono text-[10px] font-semibold text-oxblood dark:text-rose uppercase tracking-wider block">
                                  {job.company?.company_name || "Featured Employer"}
                                </span>
                                <h3 className="font-display font-bold text-charcoal dark:text-ivory text-base mt-0.5">
                                  {job.title}
                                </h3>
                              </div>
                              <button
                                onClick={() => toggleSaveJob(jobId)}
                                className="p-1.5 rounded-lg border border-oxblood/30 bg-oxblood/10 text-oxblood dark:text-rose hover:bg-oxblood/20 transition min-h-[36px] min-w-[36px] flex items-center justify-center"
                                title="Remove bookmark"
                              >
                                <BookmarkCheck className="w-4 h-4" />
                              </button>
                            </div>

                            <div className="mt-3 flex items-center gap-2 text-xs font-mono text-slate/70 dark:text-ivory/60">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3.5 h-3.5 text-slate/50 dark:text-ivory/40" />
                                <span>{job.location}</span>
                              </span>
                              <span>•</span>
                              <span>{job.job_type?.replace('_', ' ')}</span>
                            </div>

                            <div className="mt-4 flex flex-wrap gap-1.5">
                              {job.required_skills?.slice(0, 4).map((sk, idx) => (
                                <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory font-medium">
                                  {sk}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15">
                            <div className="flex justify-between items-center mb-3 text-xs font-mono">
                              <span className="text-[10px] uppercase text-slate/60 dark:text-ivory/40">Compensation</span>
                              <span className="font-bold text-charcoal dark:text-ivory">
                                {job.salary_min && job.salary_max
                                  ? `₹${(job.salary_min/100000).toFixed(1)}L - ₹${(job.salary_max/100000).toFixed(1)}L`
                                  : "Competitive"}
                              </span>
                            </div>

                            <div className="flex gap-2">
                              <button
                                onClick={() => handleAnalyzeMatch(job)}
                                className="flex-1 min-h-[44px] py-2 px-3 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory hover:border-oxblood/40 font-mono text-xs font-bold transition flex items-center justify-center gap-1"
                              >
                                <Sparkles className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                                <span>Match</span>
                              </button>
                              {!alreadyApplied ? (
                                <button
                                  onClick={() => openApplyModal(job)}
                                  className="min-h-[44px] px-5 py-2 btn-oxblood font-display font-semibold text-xs rounded-xl transition flex items-center justify-center gap-1"
                                >
                                  <span>Apply</span>
                                  <ArrowUpRight className="w-3.5 h-3.5" />
                                </button>
                              ) : (
                                <span className="badge-selected text-xs font-mono font-bold px-3 py-2 rounded-xl flex items-center gap-1">
                                  <Check className="w-3.5 h-3.5" />
                                  <span>Applied</span>
                                </span>
                              )}
                            </div>
                          </div>
                        </LiquidSpotlightCard>
                      </StaggerItem>
                    );
                  })}
                </StaggerContainer>
              )}

              {/* Explainable AI Recommendations Section */}
              <div className="mt-12 pt-8 border-t border-slate/15 dark:border-rose/15">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h4 className="font-display text-lg font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-oxblood dark:text-rose" />
                      <span>Explainable AI Recommendations</span>
                    </h4>
                    <p className="text-xs text-slate/70 dark:text-ivory/65">
                      Deterministic career opportunities ranked by semantic and graph skill alignment with your profile.
                    </p>
                  </div>
                  <button
                    onClick={fetchRecommendations}
                    className="text-xs font-mono text-slate/70 dark:text-ivory/60 hover:text-oxblood flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate/15 dark:border-rose/15 min-h-[36px]"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Recalculate</span>
                  </button>
                </div>

                {recsLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2].map((n) => <div key={n} className="h-44 glass-card rounded-2xl animate-pulse"></div>)}
                  </div>
                ) : recommendations.length === 0 ? (
                  <div className="p-6 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-center text-xs font-mono text-slate/60 dark:text-ivory/60">
                    Upload or update your resume skills to trigger automated AI role matching recommendations.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {recommendations.map((rec) => {
                      const job = rec.job || rec;
                      const score = Math.round(rec.match_score || rec.score || 85);
                      return (
                        <div
                          key={rec.id || job.id}
                          className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 flex flex-col justify-between hover:border-oxblood/40 transition"
                        >
                          <div>
                            <div className="flex justify-between items-start gap-4">
                              <div>
                                <span className="font-mono text-[10px] text-oxblood dark:text-rose font-bold uppercase tracking-wider block">
                                  {job.company?.company_name || "Enterprise"}
                                </span>
                                <h5 className="font-display font-bold text-charcoal dark:text-ivory text-base">
                                  {job.title}
                                </h5>
                                <p className="text-xs text-slate/60 dark:text-ivory/60 font-mono mt-0.5">
                                  {job.location} · {job.job_type?.replace('_', ' ')}
                                </p>
                              </div>
                              <div className="flex flex-col items-end shrink-0">
                                <span className="badge-selected font-mono font-bold text-xs px-2.5 py-1 rounded-full">
                                  {score}% Match
                                </span>
                              </div>
                            </div>

                            <div className="mt-4 p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 text-xs font-mono">
                              <p className="text-[10px] uppercase font-bold text-slate/60 dark:text-rose mb-1">
                                Match Rationale
                              </p>
                              <p className="text-slate/80 dark:text-ivory/70 line-clamp-2">
                                {rec.match_explanation || rec.reason || `Strong compatibility with verified skills: ${(rec.matching_skills || job.required_skills?.slice(0, 3) || []).join(', ')}.`}
                              </p>
                            </div>

                            <div className="mt-3 flex flex-wrap gap-1">
                              {(rec.matching_skills || job.required_skills?.slice(0, 4) || []).map((sk, idx) => (
                                <span key={idx} className="badge-selected text-[10px] font-mono px-2 py-0.5 rounded-md">
                                  ✓ {sk}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div className="mt-5 pt-3 border-t border-slate/15 dark:border-rose/15 flex justify-between items-center gap-2">
                            <button
                              onClick={() => toggleSaveJob(job.id)}
                              className="text-xs font-mono font-bold text-slate/70 dark:text-ivory/60 hover:text-oxblood flex items-center gap-1 min-h-[44px]"
                            >
                              <Bookmark className="w-3.5 h-3.5" />
                              <span>{savedJobIds.has(job.id) ? "Bookmarked" : "Save Role"}</span>
                            </button>
                            <button
                              onClick={() => openApplyModal(job)}
                              className="btn-oxblood px-4 py-2 rounded-xl text-xs font-display font-semibold flex items-center gap-1 min-h-[44px]"
                            >
                              <span>Apply Now</span>
                              <ArrowUpRight className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: FIRST-ROUND TECHNICAL ASSESSMENTS */}
          {/* ======================================================== */}
          {activeTab === 'assessments' && (
            <CandidateAssessmentsSection />
          )}

          {/* ======================================================== */}
          {/* TAB: ASYNCHRONOUS VIDEO ASSESSMENTS */}
          {/* ======================================================== */}
          {activeTab === 'video-assessments' && (
            <CandidateVideoAssessmentsSection />
          )}

          {/* ======================================================== */}
          {/* TAB: CANDIDATE MEDIA LIBRARY */}
          {/* ======================================================== */}
          {activeTab === 'media' && (
            <CandidateMediaLibrarySection />
          )}

          {/* ======================================================== */}
          {/* TAB: SCHEDULED INTERVIEWS */}
          {/* ======================================================== */}
          {activeTab === 'interviews' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Interview Schedule & Telemetry</span>
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Upcoming and past technical assessments, video screens, and recruiter debriefs.
                  </p>
                </div>
                <button
                  onClick={fetchInterviews}
                  className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
              </div>

              {interviewsLoading ? (
                <div className="space-y-4">
                  {[1, 2].map((n) => <div key={n} className="h-28 glass-card rounded-2xl animate-pulse"></div>)}
                </div>
              ) : myInterviews.length === 0 ? (
                <div className="text-center py-14 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <Calendar className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">No interviews scheduled at this time.</p>
                  <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1 max-w-md mx-auto">
                    When recruiters advance your application to the interview stage, meeting dates, video links, and instructions will be coordinated here.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {myInterviews.map((inv) => {
                    const scheduledDate = new Date(inv.scheduled_time || inv.scheduled_at);
                    const isUpcoming = (inv.status === 'SCHEDULED' || inv.status === 'WAITING' || inv.status === 'RESCHEDULED') && scheduledDate >= new Date();
                    const isOngoing = inv.status === 'IN_PROGRESS' || inv.room_status === 'IN_PROGRESS';
                    const mode = inv.interview_mode || 'HUMAN';

                    return (
                      <div
                        key={inv.id}
                        className={`p-6 rounded-2xl border transition-all ${
                          isOngoing
                            ? 'bg-amber-500/10 border-amber-500/30'
                            : isUpcoming
                            ? 'bg-oxblood/5 border-oxblood/30 dark:bg-oxblood/10'
                            : 'bg-slate/5 dark:bg-white/5 border-slate/15 dark:border-rose/15'
                        }`}
                      >
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`font-mono text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase ${
                                isOngoing ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/30 animate-pulse' :
                                inv.status === 'SCHEDULED' ? 'badge-selected' :
                                inv.status === 'COMPLETED' ? 'badge-slate' : 'bg-error/15 text-error border border-error/30'
                              }`}>
                                {isOngoing ? 'ROOM LIVE NOW' : inv.status}
                              </span>
                              <span className="badge-slate font-mono text-[10px] font-semibold px-2.5 py-0.5 rounded-md flex items-center gap-1">
                                {mode === 'AI_LIVE' ? <Bot className="w-3 h-3 text-purple-600 dark:text-purple-400" /> :
                                 mode === 'HYBRID' ? <Sparkles className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> :
                                 <Video className="w-3 h-3 text-oxblood dark:text-rose" />}
                                <span>{mode.replace('_', ' ')} INTERVIEW</span>
                              </span>
                              <span className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                                {inv.duration_minutes || 45} mins
                              </span>
                            </div>

                            <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory mt-2">
                              {inv.job_title || inv.application?.job?.title || "Recruitment Interview"}
                            </h4>
                            <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono">
                              {inv.application?.job?.company?.company_name || "SkillSphere Partner"}
                            </p>
                          </div>

                          <div className="flex flex-col sm:items-end gap-2 shrink-0">
                            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-charcoal dark:text-ivory">
                              <Clock className="w-4 h-4 text-oxblood dark:text-rose" />
                              <span>{scheduledDate.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                            </div>

                            {(inv.status === 'SCHEDULED' || isOngoing) && (
                              <div className="flex items-center gap-2 flex-wrap">
                                <button
                                  type="button"
                                  onClick={() => handleOpenPrepModal(inv)}
                                  className="btn-oxblood px-4 py-2 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 min-h-[44px] shadow"
                                >
                                  <Video className="w-3.5 h-3.5" />
                                  <span>{isOngoing ? 'Enter Live Room' : 'Prepare & Join Interview'}</span>
                                </button>
                                {inv.meeting_link && !inv.meeting_link.startsWith('/interview-room') && (
                                  <a
                                    href={inv.meeting_link.startsWith('http') ? inv.meeting_link : `https://${inv.meeting_link}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-2 rounded-xl border border-slate/20 dark:border-rose/20 text-xs font-mono text-slate/70 dark:text-ivory/70 hover:border-oxblood flex items-center gap-1 min-h-[44px]"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                    <span>External Link</span>
                                  </a>
                                )}
                              </div>
                            )}

                            {inv.status === 'COMPLETED' && (
                              <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                                <CheckCircle2 className="w-4 h-4" />
                                <span>Completed & Evaluated</span>
                              </span>
                            )}
                          </div>
                        </div>

                        {(inv.instructions || inv.location) && (
                          <div className="mt-4 p-3.5 rounded-xl bg-white/50 dark:bg-black/20 border border-slate/15 dark:border-rose/15 text-xs font-mono">
                            <p className="text-[10px] font-bold uppercase text-slate/60 dark:text-rose mb-1">
                              Coordinator Instructions / Coordinates
                            </p>
                            <p className="text-slate/80 dark:text-ivory/70 whitespace-pre-wrap">
                              {inv.instructions || inv.location}
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
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
                        <span>Conversations</span>
                      </h3>
                      <button
                        onClick={fetchConversations}
                        className="text-slate/60 dark:text-ivory/60 hover:text-oxblood p-1.5 rounded-lg border border-slate/15 dark:border-rose/15 min-h-[36px] min-w-[36px] flex items-center justify-center"
                        title="Refresh conversations"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {conversations.length === 0 ? (
                      <div className="text-center py-12 text-slate/50 dark:text-ivory/40 text-xs font-mono">
                        No messages yet. Direct chats with hiring managers will appear here.
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
                                {(conv.partner_name || 'R')[0]?.toUpperCase()}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-baseline">
                                  <p className="font-display font-bold text-xs truncate">
                                    {conv.partner_name || 'Hiring Manager'}
                                  </p>
                                  {conv.last_message_time && (
                                    <span className={`text-[10px] font-mono shrink-0 ml-1 ${isSelected ? 'text-ivory/70' : 'text-slate/50 dark:text-ivory/40'}`}>
                                      {new Date(conv.last_message_time).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                                    </span>
                                  )}
                                </div>
                                <p className={`text-[11px] font-mono truncate mt-0.5 ${isSelected ? 'text-ivory/80' : 'text-slate/60 dark:text-ivory/60'}`}>
                                  {conv.last_message || 'Start conversation...'}
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
                    Direct ATS Candidate Channel
                  </div>
                </div>

                {/* Chat Message Window */}
                <div className="md:col-span-8 flex flex-col justify-between p-4 sm:p-6 bg-slate/5 dark:bg-black/10">
                  {activePartner ? (
                    <>
                      <div className="flex justify-between items-center pb-4 border-b border-slate/15 dark:border-rose/15 mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-oxblood/10 text-oxblood dark:text-rose font-display font-bold text-sm flex items-center justify-center">
                            {(activePartner.partner_name || 'R')[0]?.toUpperCase()}
                          </div>
                          <div>
                            <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                              {activePartner.partner_name || 'Hiring Representative'}
                            </h4>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                              {activePartner.partner_role || 'Recruiter'} · {activePartner.company_name || 'Talent Acquisition'}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4 max-h-[420px]">
                        {chatLoading ? (
                          <div className="text-center py-10 font-mono text-xs text-slate/50">Loading messages...</div>
                        ) : chatMessages.length === 0 ? (
                          <div className="text-center py-12 text-slate/50 dark:text-ivory/40 text-xs font-mono">
                            Send a message to introduce yourself or clarify role details.
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
                          placeholder="Type your message..."
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
                      <p>Select a recruiter conversation on the left to start messaging.</p>
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: MY RESUMES & OCR EXTRACTION */}
          {/* ======================================================== */}
          {activeTab === 'resumes' && (
            <div className="space-y-6">
              
              {/* AI Resume Intelligence & Quality Telemetry */}
              <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-slate/15 dark:border-rose/15">
                  <div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-oxblood dark:text-rose" />
                      <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">
                        AI Resume Intelligence & Quality Score
                      </h3>
                      <span className="badge-selected font-mono text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase">
                        ATS ENGINE v2.4
                      </span>
                    </div>
                    <p className="text-xs text-slate/70 dark:text-ivory/65 mt-1 font-normal">
                      Algorithmic audit of parsing readability, structure integrity, and completeness score.
                    </p>
                  </div>

                  <button
                    onClick={fetchQualityFeedback}
                    className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Re-Audit Quality</span>
                  </button>
                </div>

                {/* Scorecards Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6">
                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 flex items-center gap-4">
                    <AnimatedProgressRing percentage={qualityFeedback?.completeness_score || completeness} size={58} strokeWidth={5} color="#914F51" />
                    <div>
                      <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-rose">Completeness</p>
                      <p className="text-lg font-mono font-bold text-charcoal dark:text-ivory">
                        {qualityFeedback?.completeness_score || completeness}%
                      </p>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 flex items-center gap-4">
                    <AnimatedProgressRing percentage={qualityFeedback?.formatting_score || 92} size={58} strokeWidth={5} color="#829B88" />
                    <div>
                      <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-rose">ATS Readability</p>
                      <p className="text-lg font-mono font-bold text-charcoal dark:text-ivory">
                        {qualityFeedback?.formatting_score || 92}%
                      </p>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center font-mono font-bold text-sm">
                      {formSkills.length}
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase text-slate/60 dark:text-rose">Extracted Skills</p>
                      <p className="text-lg font-mono font-bold text-charcoal dark:text-ivory">
                        {formSkills.length} Verified
                      </p>
                    </div>
                  </div>
                </div>

                {/* Missing Fields Warning if any */}
                {qualityFeedback?.missing_fields?.length > 0 && (
                  <div className="mt-5 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                    <div className="flex items-center gap-2.5 text-xs text-amber-700 dark:text-amber-300 font-mono">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>
                        ATS Parsing Notice: Missing fields detected ({qualityFeedback.missing_fields.join(', ')}).
                      </span>
                    </div>
                    <button
                      onClick={() => setTab('profile')}
                      className="text-xs font-mono font-bold px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-900 dark:text-amber-200 transition min-h-[36px]"
                    >
                      Update Profile Form →
                    </button>
                  </div>
                )}

                {/* Recommendations and Strengths */}
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono text-xs">
                    <p className="font-bold text-success mb-2 uppercase text-[10px] tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Detected ATS Strengths</span>
                    </p>
                    <ul className="space-y-1.5 text-slate/80 dark:text-ivory/70 text-[11px]">
                      {(qualityFeedback?.strengths || [
                        "Dual PyMuPDF native digital text extraction verified",
                        "Standard chronological experience hierarchy",
                        "High density of searchable engineering keywords"
                      ]).map((str, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-success">✓</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono text-xs">
                    <p className="font-bold text-oxblood dark:text-rose mb-2 uppercase text-[10px] tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Actionable ATS Suggestions</span>
                    </p>
                    <ul className="space-y-1.5 text-slate/80 dark:text-ivory/70 text-[11px]">
                      {(qualityFeedback?.suggestions || [
                        "Review Candidate Passport to ensure contact number and location match recruiter filters",
                        "Highlight quantifiable metrics in project experience descriptions",
                        "Maintain PDF format for highest OCR confidence"
                      ]).map((sug, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-oxblood dark:text-rose">→</span>
                          <span>{sug}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Drag-and-Drop Resume Upload Area */}
              <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
                <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory mb-1">
                  Dual-Engine OCR Extraction
                </h3>
                <p className="text-xs text-slate/70 dark:text-ivory/65 mb-6 font-normal">
                  Upload your CV in PDF or image format. PyMuPDF extracts native digital text while Tesseract OCR processes scanned documents.
                </p>

                {uploadError && (
                  <div className="mb-4 p-3.5 rounded-2xl bg-error/15 border border-error/30 text-error text-xs font-mono flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{uploadError}</span>
                  </div>
                )}

                {uploadSuccess && (
                  <div className="mb-4 p-3.5 rounded-2xl badge-selected text-xs font-mono font-medium flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-success" />
                    <span>{uploadSuccess}</span>
                  </div>
                )}

                {/* Upload Zone / Multi-Stage State */}
                <div className="relative border-2 border-dashed border-slate/20 dark:border-rose/20 rounded-3xl p-8 sm:p-12 text-center hover:border-oxblood/40 dark:hover:border-rose/40 transition-colors bg-slate/5 dark:bg-white/5">
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-10"
                    id="resume-file-input"
                  />

                  {uploading ? (
                    <div className="space-y-4 max-w-md mx-auto font-mono">
                      <div className="w-12 h-12 rounded-full border-3 border-oxblood/30 border-t-oxblood rounded-full animate-spin mx-auto"></div>
                      
                      <div className="space-y-2">
                        <p className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                          {uploadStage === 'uploading' && 'Streaming file payload to secure gateway...'}
                          {uploadStage === 'ocr_parsing' && 'Rasterizing vector glyphs & running Tesseract OCR...'}
                          {uploadStage === 'extracting_graph' && 'Mapping verified skills into relational graph...'}
                          {uploadStage === 'complete' && 'Parsing finalized! Updating candidate profile...'}
                        </p>
                        
                        {/* Progress Stepper Bar */}
                        <div className="flex items-center justify-between text-[10px] text-slate/60 dark:text-rose/80 pt-2 border-t border-slate/15 dark:border-rose/15">
                          <span className={uploadStage !== 'idle' ? 'text-oxblood dark:text-rose font-bold' : ''}>1. Upload</span>
                          <span>→</span>
                          <span className={['ocr_parsing', 'extracting_graph', 'complete'].includes(uploadStage) ? 'text-oxblood dark:text-rose font-bold' : ''}>2. Dual OCR</span>
                          <span>→</span>
                          <span className={['extracting_graph', 'complete'].includes(uploadStage) ? 'text-oxblood dark:text-rose font-bold' : ''}>3. Skill Graph</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="w-14 h-14 rounded-2xl bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center mx-auto mb-4 ring-1 ring-oxblood/20 shadow-sm">
                        <Upload className="w-6 h-6" />
                      </div>
                      <p className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                        Drop resume file here or <span className="text-oxblood dark:text-rose underline underline-offset-4">browse filesystem</span>
                      </p>
                      <p className="text-xs font-mono text-slate/60 dark:text-ivory/50 mt-1.5">
                        Supported: PDF, JPG, PNG · Max file size: 10MB
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Uploaded Resumes Library */}
              <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
                <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate/15 dark:border-rose/15">
                  <div>
                    <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">Uploaded Resumes ({resumes.length})</h3>
                    <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">Active documents stored for job applications and skill matching.</p>
                  </div>
                  <button
                    onClick={fetchResumes}
                    className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>

                {resumes.length === 0 ? (
                  <div className="text-center py-10 text-slate/60 dark:text-ivory/60 font-mono text-xs">
                    No resumes uploaded yet. Upload your first resume above to activate skill extraction.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {resumes.map((res) => (
                      <div
                        key={res.id}
                        className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3.5">
                          <div className="w-10 h-10 rounded-xl bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center font-mono font-bold text-xs">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="font-display font-bold text-sm text-charcoal dark:text-ivory truncate max-w-xs">{res.filename}</p>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                              Uploaded {res.uploaded_at || res.created_at ? new Date(res.uploaded_at || res.created_at).toLocaleDateString() : 'Active'}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <a
                            href={resumeAPI.downloadUrl(res.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2.5 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory hover:border-oxblood hover:text-oxblood transition min-h-[44px] min-w-[44px] flex items-center justify-center"
                            title="Download original resume file"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: MY APPLICATIONS */}
          {/* ======================================================== */}
          {activeTab === 'applications' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory">My Applications</h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">Real-time status tracking for your submitted applications.</p>
                </div>
                <button
                  onClick={fetchApplications}
                  className="text-xs font-mono font-bold text-slate/80 dark:text-ivory/70 hover:text-oxblood flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate/15 dark:border-rose/15 transition min-h-[44px]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh</span>
                </button>
              </div>

              {applications.length === 0 ? (
                <div className="text-center py-14 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <Briefcase className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">You haven't submitted any job applications yet.</p>
                  <button
                    onClick={() => setTab('jobs')}
                    className="mt-3 btn-oxblood px-5 py-2.5 rounded-xl font-display font-semibold text-xs inline-flex items-center gap-1.5 min-h-[44px]"
                  >
                    <span>Browse Compatible Jobs</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <>
                  {/* Desktop Table View (>= 768px) */}
                  <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-mono font-bold uppercase tracking-wider text-[11px]">
                          <th className="py-3.5 px-4 rounded-l-xl">Role & Company</th>
                          <th className="py-3.5 px-4">Applied Date</th>
                          <th className="py-3.5 px-4">Status</th>
                          <th className="py-3.5 px-4 text-right rounded-r-xl">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium">
                        {applications.map((app) => (
                          <tr key={app.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4">
                              <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">{app.job?.title || "Position"}</p>
                              <p className="font-mono text-slate/60 dark:text-ivory/50 text-[11px]">{app.job?.company?.company_name || "Enterprise Company"}</p>
                            </td>
                            <td className="py-4 px-4 font-mono text-slate/80 dark:text-ivory/70 text-[11px]">
                              {new Date(app.application_date).toLocaleDateString()}
                            </td>
                            <td className="py-4 px-4">
                              {getStatusBadge(app.status)}
                            </td>
                            <td className="py-4 px-4 text-right space-x-2 font-mono">
                              {app.status !== 'WITHDRAWN' && app.status !== 'REJECTED' && (
                                <button
                                  onClick={() => handleWithdraw(app.id)}
                                  className="text-xs font-bold text-error hover:underline px-3 py-1.5 rounded-xl border border-error/30 bg-error/10 transition min-h-[44px]"
                                >
                                  Withdraw
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Stacked Cards View (< 768px) */}
                  <div className="md:hidden space-y-4">
                    {applications.map((app) => (
                      <div
                        key={app.id}
                        className="p-5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <span className="font-mono text-[10px] text-oxblood dark:text-rose font-bold uppercase">
                              {app.job?.company?.company_name || "Enterprise Company"}
                            </span>
                            <h4 className="font-display font-bold text-charcoal dark:text-ivory text-base">
                              {app.job?.title || "Position"}
                            </h4>
                            <p className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                              Applied: {new Date(app.application_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div>{getStatusBadge(app.status)}</div>
                        </div>

                        {app.status !== 'WITHDRAWN' && app.status !== 'REJECTED' && (
                          <div className="pt-2 border-t border-slate/10 dark:border-rose/10 flex justify-end">
                            <button
                              onClick={() => handleWithdraw(app.id)}
                              className="w-full min-h-[44px] text-xs font-mono font-bold text-error border border-error/30 bg-error/10 rounded-xl transition flex items-center justify-center gap-1.5"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Withdraw Application</span>
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 4: CANDIDATE PASSPORT (PROFILE & VERIFIED SKILLS) */}
          {/* ======================================================== */}
          {activeTab === 'profile' && (
            <div className="glass-card p-6 sm:p-10 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl sm:text-2xl font-bold text-charcoal dark:text-ivory">
                    Candidate Passport Profile
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Review and calibrate your verified competencies, experience history, and coordinates.
                  </p>
                </div>
                {saveMessage && (
                  <span className="badge-selected text-xs font-mono font-bold px-3 py-1 rounded-full">
                    ✓ Saved
                  </span>
                )}
              </div>

              <form onSubmit={handleSaveProfile} className="space-y-6">
                
                {/* Basic Coordinates */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Full Legal Name
                    </label>
                    <input
                      type="text"
                      required
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Professional Title
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Senior Full-Stack Engineer"
                      value={formTitle}
                      onChange={(e) => setFormTitle(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Contact Phone
                    </label>
                    <input
                      type="text"
                      placeholder="+91 98765 43210"
                      value={formPhone}
                      onChange={(e) => setFormPhone(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Current Location
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Bengaluru, India"
                      value={formLocation}
                      onChange={(e) => setFormLocation(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Total Experience (Years)
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={formTotalYearsExp}
                      onChange={(e) => setFormTotalYearsExp(e.target.value)}
                      className="w-full glass-input text-xs min-h-[44px]"
                    />
                  </div>
                </div>

                {/* Professional Bio */}
                <div>
                  <label className="block text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                    Executive Summary / Bio
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Highlight your core architectural expertise, systems impact, and strengths..."
                    value={formBio}
                    onChange={(e) => setFormBio(e.target.value)}
                    className="w-full glass-input text-xs font-sans"
                  ></textarea>
                </div>

                {/* Verified Skills Interactive Tag Manager */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-[11px] font-mono font-bold text-slate/80 dark:text-rose uppercase tracking-wider">
                      Verified Technical Skills ({formSkills.length})
                    </label>
                    <span className="text-[10px] font-mono text-slate/60 dark:text-ivory/50">Press Enter or click + to add</span>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <AnimatePresence>
                        {formSkills.map((sk) => (
                          <motion.span
                            key={sk}
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            transition={{ duration: 0.18 }}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate/10 dark:bg-white/10 border border-slate/15 dark:border-rose/15 text-xs font-mono font-medium text-charcoal dark:text-ivory"
                          >
                            <span>{sk}</span>
                            <button
                              type="button"
                              onClick={() => removeSkill(sk)}
                              className="text-slate/40 dark:text-rose hover:text-error transition"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </motion.span>
                        ))}
                      </AnimatePresence>
                    </div>

                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Add new skill (e.g. PyTorch, Kubernetes, Golang)..."
                        value={newSkillInput}
                        onChange={(e) => setNewSkillInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(); } }}
                        className="flex-1 glass-input text-xs min-h-[44px]"
                      />
                      <button
                        type="button"
                        onClick={addSkill}
                        className="px-5 py-2.5 bg-oxblood text-ivory rounded-xl text-xs font-mono font-bold transition flex items-center gap-1 min-h-[44px]"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Add</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Save Profile Button */}
                <div className="pt-4 flex justify-end">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="min-h-[48px] px-8 py-3.5 btn-oxblood font-display font-semibold text-xs rounded-xl shadow-md transition disabled:opacity-50"
                  >
                    {savingProfile ? "Saving Profile..." : "Save Passport Profile"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: RESUME-BASED TECHNICAL PRACTICE & INTERVIEW PREP */}
          {/* ======================================================== */}
          {activeTab === 'practice' && (
            <div className="space-y-6">
              
              {!selectedTech ? (
                /* ---------------------------------------------------- */
                /* SUB-VIEW 1: TECHNOLOGY ROADMAP & PRACTICE HUB       */
                /* ---------------------------------------------------- */
                <div className="space-y-6">
                  
                  {/* Editorial Roadmap Header */}
                  <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl bg-white/70 dark:bg-charcoal/80 relative overflow-hidden">
                    <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 pb-6 border-b border-slate/15 dark:border-rose/15">
                      <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose text-[11px] font-mono uppercase tracking-wider mb-2">
                          <Cpu className="w-3.5 h-3.5" />
                          <span>Deterministic Skill Calibration</span>
                        </div>
                        <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                          Resume-Based Technical Practice
                        </h2>
                        <p className="text-xs text-slate/70 dark:text-ivory/65 mt-1.5 max-w-2xl leading-relaxed">
                          Sharpen your engineering fundamentals on the exact languages, frameworks, and databases detected in your parsed resume. Questions are structured in progressive batches across Beginner, Intermediate, and Advanced tiers.
                        </p>
                      </div>

                      {/* Sync from Resume Action */}
                      <button
                        type="button"
                        onClick={handleSyncResumeTechnologies}
                        disabled={detectingResumeTech}
                        className="px-5 py-3 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-oxblood/90 transition shadow-md disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${detectingResumeTech ? 'animate-spin' : ''}`} />
                        <span>{detectingResumeTech ? 'Scanning Resume...' : 'Re-Detect From Resume'}</span>
                      </button>
                    </div>

                    {/* Overall Practice Telemetry Counters */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 text-center font-mono">
                      <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                        <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                          <AnimatedCounter value={practiceAnalytics?.total_attempted || 0} />
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Questions Solved</p>
                      </div>

                      <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                        <p className="text-2xl font-extrabold text-success">
                          <AnimatedCounter value={practiceAnalytics?.total_correct || 0} />
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Correct Answers</p>
                      </div>

                      <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                        <p className="text-2xl font-extrabold text-oxblood dark:text-rose">
                          {practiceAnalytics?.overall_accuracy || 0}%
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Overall Accuracy</p>
                      </div>

                      <div className="p-3 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                        <p className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                          <AnimatedCounter value={practiceTechs.length} />
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-rose mt-0.5">Active Technologies</p>
                      </div>
                    </div>
                  </div>

                  {/* Manual Technology Addition Bar */}
                  <div className="glass-card p-4 sm:p-5 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-xs font-mono text-slate/80 dark:text-ivory/80">
                      <Code className="w-4 h-4 text-oxblood dark:text-rose" />
                      <span>Missing a skill from your resume? Add any technology to your roadmap:</span>
                    </div>

                    <form onSubmit={handleAddManualTech} className="w-full sm:w-auto flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g. Go, FastAPI, Docker, Rust..."
                        value={newManualTechInput}
                        onChange={(e) => setNewManualTechInput(e.target.value)}
                        className="px-4 py-2 bg-white/60 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 focus:outline-none focus:border-oxblood min-h-[42px] font-mono"
                      />
                      <button
                        type="submit"
                        disabled={addingManualTech || !newManualTechInput.trim()}
                        className="px-4 py-2 bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal text-xs font-mono font-bold uppercase rounded-xl transition hover:opacity-90 disabled:opacity-50 min-h-[42px]"
                      >
                        {addingManualTech ? 'Adding...' : '+ Add'}
                      </button>
                    </form>
                  </div>

                  {/* Technology Practice Cards Grid */}
                  <div>
                    <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose mb-4 flex items-center gap-2">
                      <Terminal className="w-4 h-4" />
                      <span>Select a Technology to Practice (20 Questions / Batches of 10)</span>
                    </h3>

                    {practiceLoading ? (
                      <div className="py-12 text-center font-mono text-xs text-slate/60 dark:text-ivory/50">
                        <div className="w-8 h-8 border-2 border-oxblood/30 border-t-oxblood rounded-full animate-spin mx-auto mb-3" />
                        <span>Loading technology banks...</span>
                      </div>
                    ) : practiceTechs.length === 0 ? (
                      <div className="glass-card p-12 text-center rounded-3xl border border-slate/15 dark:border-rose/15">
                        <Cpu className="w-10 h-10 text-slate/40 dark:text-rose/40 mx-auto mb-3" />
                        <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">No Technologies Detected Yet</h4>
                        <p className="text-xs text-slate/60 dark:text-ivory/60 max-w-md mx-auto mt-1 mb-4">
                          Upload your resume in the Resumes tab or click Re-Detect to populate your technology roadmap.
                        </p>
                        <button
                          type="button"
                          onClick={handleSyncResumeTechnologies}
                          className="px-6 py-2.5 bg-oxblood text-ivory rounded-xl text-xs font-mono font-bold"
                        >
                          Scan Resume Now
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {practiceTechs.map((tech) => {
                          const stats = practiceAnalytics?.technology_breakdown?.[tech.technology_name] || { attempted: 0, correct: 0, accuracy: 0 };
                          return (
                            <div
                              key={tech.id}
                              className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 hover:border-oxblood/40 transition-all shadow-md hover:shadow-lg flex flex-col justify-between"
                            >
                              <div>
                                <div className="flex items-start justify-between gap-2 mb-3">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">
                                        {tech.technology_name}
                                      </h4>
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-rose border border-slate/15 dark:border-white/10 uppercase">
                                        {tech.category}
                                      </span>
                                    </div>
                                    <p className="text-[10px] font-mono mt-1 text-slate/60 dark:text-ivory/50">
                                      {tech.is_resume_detected ? (
                                        <span className="text-success font-medium">✓ Detected from Resume</span>
                                      ) : (
                                        <span className="text-oxblood dark:text-rose font-medium">✦ Added Manually</span>
                                      )}
                                    </p>
                                  </div>

                                  <button
                                    type="button"
                                    onClick={() => handleRemovePracticeTech(tech.technology_name)}
                                    className="p-1 text-slate/40 hover:text-error transition"
                                    title={`Remove ${tech.technology_name}`}
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>

                                {/* Difficulty & Question Mix */}
                                <div className="flex items-center gap-2 mb-4 text-[10px] font-mono">
                                  <span className="px-2 py-0.5 rounded bg-success/10 text-success border border-success/20">7 Beginner</span>
                                  <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">7 Interm</span>
                                  <span className="px-2 py-0.5 rounded bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20">6 Adv</span>
                                </div>

                                {/* Accuracy Bar */}
                                <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 mb-4 font-mono text-xs">
                                  <div className="flex justify-between items-center text-[11px] mb-1">
                                    <span className="text-slate/60 dark:text-ivory/60">Accuracy</span>
                                    <span className="font-bold text-charcoal dark:text-ivory">{stats.accuracy}%</span>
                                  </div>
                                  <div className="w-full h-1.5 bg-slate/10 dark:bg-white/10 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-oxblood transition-all duration-300"
                                      style={{ width: `${stats.accuracy}%` }}
                                    />
                                  </div>
                                  <p className="text-[10px] text-slate/50 dark:text-ivory/40 mt-1.5">
                                    {stats.attempted} attempted &bull; {stats.correct} correct
                                  </p>
                                </div>
                              </div>

                              <button
                                type="button"
                                onClick={() => handleSelectTech(tech)}
                                className="w-full py-2.5 px-4 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-2 hover:bg-oxblood/90 transition shadow-sm"
                              >
                                <span>Start Practice</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Performance Breakdown by Difficulty */}
                  {practiceAnalytics?.difficulty_breakdown && (
                    <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-sm">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose mb-4 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        <span>Performance by Difficulty Tier</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
                        {['BEGINNER', 'INTERMEDIATE', 'ADVANCED'].map((tier) => {
                          const dStats = practiceAnalytics.difficulty_breakdown[tier] || { attempted: 0, correct: 0, accuracy: 0 };
                          return (
                            <div key={tier} className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5">
                              <div className="flex justify-between items-center mb-1">
                                <span className={`text-[11px] font-bold ${
                                  tier === 'BEGINNER' ? 'text-success' : tier === 'INTERMEDIATE' ? 'text-amber-500' : 'text-oxblood dark:text-rose'
                                }`}>
                                  {tier}
                                </span>
                                <span className="font-bold text-charcoal dark:text-ivory">{dStats.accuracy}%</span>
                              </div>
                              <p className="text-[10px] text-slate/50 dark:text-ivory/40">
                                {dStats.correct} / {dStats.attempted} Correct
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                </div>
              ) : (
                /* ---------------------------------------------------- */
                /* SUB-VIEW 2: INTERACTIVE PRACTICE SESSION             */
                /* ---------------------------------------------------- */
                <div className="space-y-6">
                  
                  {/* Session Navigation Header */}
                  <div className="glass-card p-4 sm:p-5 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <button
                      type="button"
                      onClick={() => { setSelectedTech(null); setPracticeQuestions([]); }}
                      className="inline-flex items-center gap-2 text-xs font-mono font-bold text-slate/70 dark:text-rose hover:text-charcoal dark:hover:text-ivory transition"
                    >
                      <ArrowRight className="w-4 h-4 rotate-180" />
                      <span>Back to Technology Roadmap</span>
                    </button>

                    <div className="flex items-center gap-3">
                      <span className="font-display font-extrabold text-sm text-charcoal dark:text-ivory">
                        {selectedTech.technology_name}
                      </span>
                      <span className="px-3 py-1 rounded-full bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose font-mono text-[11px] font-bold">
                        Batch {practiceBatch} (10 Questions)
                      </span>
                    </div>
                  </div>

                  {questionsLoading ? (
                    <div className="glass-card p-16 text-center rounded-3xl border border-slate/15 dark:border-rose/15 font-mono text-xs">
                      <div className="w-10 h-10 border-3 border-oxblood/30 border-t-oxblood rounded-full animate-spin mx-auto mb-3" />
                      <p className="text-slate/70 dark:text-ivory/70">Assembling question batch for {selectedTech.technology_name}...</p>
                    </div>
                  ) : batchCompleted ? (
                    /* Batch Completion Celebration Screen */
                    <motion.div
                      initial={{ opacity: 0, scale: 0.96 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="glass-card p-8 sm:p-12 text-center rounded-3xl border border-success/30 shadow-2xl bg-white/70 dark:bg-charcoal/80 space-y-6 max-w-xl mx-auto"
                    >
                      <div className="w-16 h-16 rounded-3xl bg-success/15 border border-success/30 text-success flex items-center justify-center mx-auto shadow-sm">
                        <CheckCircle2 className="w-8 h-8" />
                      </div>
                      <div>
                        <h3 className="font-display font-extrabold text-2xl text-charcoal dark:text-ivory">
                          Batch {practiceBatch} Completed!
                        </h3>
                        <p className="text-xs text-slate/70 dark:text-ivory/65 mt-1.5 leading-relaxed">
                          You've worked through this 10-question set for <strong className="text-charcoal dark:text-ivory">{selectedTech.technology_name}</strong>. Continue with the next batch or generate fresh questions.
                        </p>
                      </div>

                      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2 font-mono">
                        <button
                          type="button"
                          onClick={handleNextBatch}
                          className="px-6 py-3 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase tracking-wider hover:bg-oxblood/90 transition shadow-md"
                        >
                          Continue to Next 10 Questions &rarr;
                        </button>
                        <button
                          type="button"
                          onClick={handleGenerateMoreQuestions}
                          disabled={generatingMore}
                          className="px-6 py-3 rounded-xl border border-oxblood/40 text-oxblood dark:text-rose hover:bg-oxblood/10 text-xs font-bold uppercase tracking-wider transition disabled:opacity-50"
                        >
                          {generatingMore ? 'Generating...' : 'Generate 10 More Questions'}
                        </button>
                      </div>

                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={() => { setSelectedTech(null); setPracticeQuestions([]); }}
                          className="text-xs font-mono text-slate/60 dark:text-ivory/50 hover:text-charcoal dark:hover:text-ivory underline"
                        >
                          Return to Technology Roadmap
                        </button>
                      </div>
                    </motion.div>
                  ) : practiceQuestions.length > 0 ? (
                    /* Active Question Screen */
                    <div className="space-y-6">
                      
                      {/* 10-Question Progress Stepper */}
                      <div className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 flex items-center justify-between gap-2 overflow-x-auto scrollbar-none font-mono">
                        {practiceQuestions.map((q, idx) => {
                          const isCurrent = idx === currentQIndex;
                          const isPast = idx < currentQIndex;
                          return (
                            <button
                              key={q.id || idx}
                              type="button"
                              onClick={() => { setCurrentQIndex(idx); setSelectedAnswer(''); setAttemptResult(null); setShowingHint(false); }}
                              className={`flex-1 min-w-[32px] h-8 rounded-lg text-xs font-bold flex items-center justify-center transition ${
                                isCurrent
                                  ? 'bg-oxblood text-ivory ring-2 ring-oxblood/40 shadow-sm'
                                  : isPast
                                  ? 'bg-slate/10 dark:bg-white/10 text-slate/80 dark:text-ivory/80 hover:bg-slate/20'
                                  : 'bg-slate/5 dark:bg-white/5 text-slate/40 dark:text-ivory/30'
                              }`}
                            >
                              {idx + 1}
                            </button>
                          );
                        })}
                      </div>

                      {/* Question Card */}
                      {practiceQuestions[currentQIndex] && (() => {
                        const q = practiceQuestions[currentQIndex];
                        return (
                          <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6 bg-white/70 dark:bg-charcoal/80">
                            
                            {/* Card Header & Difficulty Badge */}
                            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate/15 dark:border-rose/15">
                              <span className="text-xs font-mono text-slate/60 dark:text-rose uppercase tracking-wider">
                                Question {currentQIndex + 1} of {practiceQuestions.length}
                              </span>

                              <span className={`text-[11px] font-mono font-bold px-3 py-1 rounded-full uppercase tracking-wider border ${
                                q.difficulty === 'BEGINNER'
                                  ? 'bg-success/10 text-success border-success/30'
                                  : q.difficulty === 'INTERMEDIATE'
                                  ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30'
                                  : 'bg-oxblood/10 text-oxblood dark:text-rose border-oxblood/30'
                              }`}>
                                {q.difficulty}
                              </span>
                            </div>

                            {/* Title & Prompt */}
                            <div>
                              <h3 className="font-display font-extrabold text-lg sm:text-xl text-charcoal dark:text-ivory tracking-tight mb-2">
                                {q.title}
                              </h3>
                              <p className="text-sm text-slate/80 dark:text-ivory/85 font-mono leading-relaxed bg-slate/5 dark:bg-black/20 p-4 rounded-2xl border border-slate/10 dark:border-white/5">
                                {q.prompt}
                              </p>
                            </div>

                            {/* Multiple Choice Options */}
                            {q.options && q.options.length > 0 && (
                              <div className="space-y-3 font-mono">
                                {q.options.map((opt) => {
                                  const isSelected = selectedAnswer === opt.key;
                                  const isCorrectOpt = attemptResult && opt.key === attemptResult.correct_answer;
                                  const isUserWrong = attemptResult && isSelected && !attemptResult.is_correct;

                                  let optClasses = "border-slate/15 dark:border-rose/15 bg-white/50 dark:bg-black/15 text-charcoal dark:text-ivory hover:border-oxblood/40";
                                  if (attemptResult) {
                                    if (isCorrectOpt) {
                                      optClasses = "border-success bg-success/15 text-success font-bold";
                                    } else if (isUserWrong) {
                                      optClasses = "border-error bg-error/15 text-error font-bold";
                                    } else {
                                      optClasses = "opacity-40 border-slate/10 bg-transparent";
                                    }
                                  } else if (isSelected) {
                                    optClasses = "border-oxblood bg-oxblood/10 text-charcoal dark:text-ivory shadow-sm";
                                  }

                                  return (
                                    <button
                                      key={opt.key}
                                      type="button"
                                      disabled={attemptResult !== null}
                                      onClick={() => setSelectedAnswer(opt.key)}
                                      className={`w-full p-4 rounded-2xl border text-left flex items-start gap-3 transition min-h-[48px] ${optClasses}`}
                                    >
                                      <span className={`w-6 h-6 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 ${
                                        isSelected ? 'bg-oxblood text-ivory' : 'bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-rose'
                                      }`}>
                                        {opt.key}
                                      </span>
                                      <span className="text-xs pt-0.5 leading-relaxed">{opt.text}</span>
                                    </button>
                                  );
                                })}
                              </div>
                            )}

                            {/* Hint Collapsible */}
                            {q.hint && (
                              <div>
                                <button
                                  type="button"
                                  onClick={() => setShowingHint(!showingHint)}
                                  className="text-xs font-mono text-oxblood dark:text-rose flex items-center gap-1.5 hover:underline"
                                >
                                  <Lightbulb className="w-3.5 h-3.5" />
                                  <span>{showingHint ? 'Hide Hint' : 'Need a Hint?'}</span>
                                </button>
                                {showingHint && (
                                  <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="mt-2 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-800 dark:text-amber-200 text-xs font-mono"
                                  >
                                    💡 <strong>Hint:</strong> {q.hint}
                                  </motion.div>
                                )}
                              </div>
                            )}

                            {/* Attempt Feedback Banner */}
                            {attemptResult && (
                              <motion.div
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`p-5 rounded-2xl border ${
                                  attemptResult.is_correct
                                    ? 'bg-success/15 border-success/30 text-success'
                                    : 'bg-amber-500/15 border-amber-500/30 text-amber-900 dark:text-amber-200'
                                }`}
                              >
                                <div className="flex items-center gap-2 mb-2 font-display font-bold text-sm">
                                  {attemptResult.is_correct ? (
                                    <>
                                      <CheckCircle2 className="w-5 h-5 text-success" />
                                      <span>Correct Evaluation</span>
                                    </>
                                  ) : (
                                    <>
                                      <AlertCircle className="w-5 h-5 text-amber-500" />
                                      <span>Incorrect &bull; Correct Option: {attemptResult.correct_answer}</span>
                                    </>
                                  )}
                                </div>
                                <p className="text-xs font-mono leading-relaxed opacity-90">
                                  <strong>Explanation:</strong> {attemptResult.explanation}
                                </p>
                              </motion.div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex justify-end gap-3 pt-4 border-t border-slate/15 dark:border-rose/15 font-mono">
                              {!attemptResult ? (
                                <button
                                  type="button"
                                  disabled={submittingAnswer || !selectedAnswer}
                                  onClick={handleSubmitAttempt}
                                  className="min-h-[44px] px-8 py-3 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase tracking-wider hover:bg-oxblood/90 transition shadow-md disabled:opacity-50 flex items-center gap-2"
                                >
                                  {submittingAnswer ? (
                                    <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                                  ) : (
                                    <>
                                      <span>Submit Answer</span>
                                      <ArrowRight className="w-3.5 h-3.5" />
                                    </>
                                  )}
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  onClick={handleNextQuestion}
                                  className="min-h-[44px] px-8 py-3 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase tracking-wider hover:bg-oxblood/90 transition shadow-md flex items-center gap-2"
                                >
                                  <span>{currentQIndex < practiceQuestions.length - 1 ? 'Next Question' : 'Complete Batch'}</span>
                                  <ArrowRight className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>

                          </div>
                        );
                      })()}

                    </div>
                  ) : null}

                </div>
              )}

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
      {/* EXPLAINABLE SKILL MATCH MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showMatchModal}
        onClose={() => setShowMatchModal(false)}
        title="Explainable Match Telemetry"
      >
        <p className="text-xs text-slate/70 dark:text-ivory/65 -mt-3 mb-6 font-normal">
          Deterministic skill graph overlap for: <span className="font-semibold text-charcoal dark:text-ivory">{analyzedJobTitle}</span>
        </p>

        {analyzingMatch ? (
          <div className="py-12 text-center font-mono space-y-3">
            <div className="w-10 h-10 border-3 border-oxblood/30 border-t-oxblood rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate/70 dark:text-ivory/70">Computing set-theoretic skill intersection math...</p>
          </div>
        ) : matchAnalysis ? (
          <div className="space-y-6">
            
            {/* Compatibility Ring Header */}
            <div className="p-6 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex flex-col sm:flex-row items-center gap-6">
              <AnimatedProgressRing percentage={matchAnalysis.match_score} size={84} strokeWidth={7} color="#914F51">
                <span className="font-mono font-bold text-lg text-charcoal dark:text-ivory">
                  {matchAnalysis.match_score}%
                </span>
              </AnimatedProgressRing>

              <div className="text-center sm:text-left">
                <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">
                  {matchAnalysis.match_score >= 80 ? 'Exceptional Match' : matchAnalysis.match_score >= 50 ? 'Strong Potential' : 'Moderate Alignment'}
                </h4>
                <p className="text-xs font-mono text-slate/70 dark:text-ivory/60 mt-1">
                  Deterministic compatibility calculated via verified skill intersection math.
                </p>
              </div>
            </div>

            {/* Matched Competencies */}
            <div>
              <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-success mb-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Matched Competencies ({matchAnalysis.matched_skills?.length || 0})</span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {matchAnalysis.matched_skills?.map((sk, idx) => (
                  <span key={idx} className="badge-selected text-xs font-mono px-3 py-1 rounded-xl">
                    ✓ {sk}
                  </span>
                ))}
                {(!matchAnalysis.matched_skills || matchAnalysis.matched_skills.length === 0) && (
                  <span className="text-xs text-slate/50 dark:text-ivory/40 font-mono italic">No direct required skill overlap found.</span>
                )}
              </div>
            </div>

            {/* Missing Skill Gaps */}
            <div>
              <p className="text-[11px] font-mono font-bold uppercase tracking-wider text-rose mb-2 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Missing Skill Gaps ({matchAnalysis.missing_skills?.length || 0})</span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {matchAnalysis.missing_skills?.map((sk, idx) => (
                  <span key={idx} className="badge-oxblood text-xs font-mono px-3 py-1 rounded-xl">
                    ✗ {sk}
                  </span>
                ))}
                {(!matchAnalysis.missing_skills || matchAnalysis.missing_skills.length === 0) && (
                  <span className="text-xs text-success font-mono">All required skills present in your profile!</span>
                )}
              </div>
            </div>

            {/* Recommendations */}
            {matchAnalysis.recommendations && (
              <div className="p-4 rounded-2xl bg-oxblood/10 border border-oxblood/20 font-mono text-xs text-charcoal dark:text-ivory">
                <p className="font-bold text-oxblood dark:text-rose mb-1 uppercase tracking-wider text-[10px]">Upskilling Recommendation</p>
                <p className="text-slate/80 dark:text-ivory/70">{matchAnalysis.recommendations}</p>
              </div>
            )}
          </div>
        ) : null}
      </GlassModal>

      {/* ======================================================== */}
      {/* APPLICATION SUBMISSION MODAL (GlassModal) */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        title={`Apply to ${selectedJob?.title || 'Opening'}`}
      >
        <p className="text-xs text-slate/70 dark:text-ivory/65 -mt-3 mb-5 font-normal">
          {selectedJob?.company?.company_name} · {selectedJob?.location}
        </p>

        {applyError && (
          <div className="mb-4 p-3 rounded-xl bg-error/15 border border-error/30 text-error text-xs font-mono flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{applyError}</span>
          </div>
        )}

        {applySuccess && (
          <div className="mb-4 p-3 rounded-xl badge-selected text-xs font-mono flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-success" />
            <span>{applySuccess}</span>
          </div>
        )}

        <div className="space-y-4 font-mono">
          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
              Select Resume to Attach
            </label>
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="w-full glass-input text-xs min-h-[44px]"
            >
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.filename} {r.uploaded_at || r.created_at ? `(Uploaded ${new Date(r.uploaded_at || r.created_at).toLocaleDateString()})` : '(Active)'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
              Cover Letter / Introduction (Optional)
            </label>
            <textarea
              rows={4}
              placeholder="Why are you a great match for this specific engineering role?..."
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              className="w-full glass-input text-xs font-sans"
            ></textarea>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowApplyModal(false)}
              className="min-h-[44px] px-5 py-2.5 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory font-display font-semibold text-xs hover:bg-slate/5 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={applying}
              onClick={handleApplyToJob}
              className="min-h-[44px] px-7 py-2.5 btn-oxblood font-display font-semibold text-xs rounded-xl shadow-xs transition disabled:opacity-50 flex items-center gap-1.5"
            >
              {applying ? "Submitting Application..." : "Submit Application"}
            </button>
          </div>
        </div>
      </GlassModal>

      {/* ======================================================== */}
      {/* CANDIDATE PRE-INTERVIEW PREPARATION & CONSENT MODAL */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={!!prepInterview}
        onClose={handleClosePrepModal}
        title="Interview Briefing & Preparation"
      >
        {prepInterview && (
          <div className="space-y-5 font-mono text-xs">
            <div className="p-4 rounded-2xl bg-oxblood/5 dark:bg-rose/5 border border-oxblood/20 space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-bold uppercase text-oxblood dark:text-rose">Target Role</span>
                  <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">
                    {prepInterview.job_title || prepInterview.application?.job?.title || "Role"}
                  </h4>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-oxblood/10 text-oxblood dark:bg-rose/10 dark:text-rose">
                  {prepInterview.interview_mode || "HUMAN"} INTERVIEW
                </span>
              </div>
              <p className="text-xs text-slate/70 dark:text-ivory/70 font-sans">
                {prepInterview.interview_mode === 'AI_LIVE'
                  ? "This session is conducted by SkillSphere's autonomous AI voice interviewer. The agent will greet you, present questions, listen to your verbal answers, and ask contextual follow-ups."
                  : prepInterview.interview_mode === 'HYBRID'
                  ? "This is a hybrid interview. The AI agent conducts structured questions, and the hiring team may observe or step in live."
                  : "This is a human-to-human video interview session conducted over secure LiveKit WebRTC."}
              </p>
            </div>

            {/* Instructions */}
            {prepInterview.instructions && (
              <div className="p-3.5 rounded-xl bg-white/50 dark:bg-black/20 border border-slate/15 space-y-1">
                <span className="text-[10px] font-bold text-slate/60 uppercase">Coordinator Instructions</span>
                <p className="text-slate/80 dark:text-ivory/80 font-sans whitespace-pre-wrap">{prepInterview.instructions}</p>
              </div>
            )}

            {/* Interactive Camera & Mic Test */}
            <div className="p-4 rounded-2xl border border-slate/15 dark:border-rose/15 space-y-3">
              <div className="flex justify-between items-center">
                <span className="font-bold text-xs text-charcoal dark:text-ivory flex items-center gap-1.5">
                  <Video className="w-4 h-4 text-oxblood dark:text-rose" />
                  <span>Hardware & Permission Readiness</span>
                </span>
                <button
                  type="button"
                  onClick={handleStartDeviceTest}
                  className="px-3 py-1 rounded-xl border border-slate/20 hover:border-oxblood text-[11px] font-bold"
                >
                  {deviceTestActive ? "Re-test Devices" : "Test Camera & Mic"}
                </button>
              </div>

              {deviceTestActive && (
                <div className="relative w-full h-44 rounded-xl overflow-hidden bg-black/60 border border-slate/20 flex items-center justify-center">
                  <video
                    ref={prepVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px] font-mono">
                    Live Camera Feed Active
                  </div>
                </div>
              )}

              {deviceTestPassed && (
                <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Camera & microphone permissions verified.</span>
                </div>
              )}
            </div>

            {/* Mandatory Recording Consent */}
            <div className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-2">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={prepConsentGranted}
                  onChange={(e) => setPrepConsentGranted(e.target.checked)}
                  className="mt-0.5 w-4 h-4 accent-oxblood rounded"
                />
                <span className="text-[11px] text-slate/80 dark:text-ivory/80 font-sans leading-relaxed">
                  I understand that this interview audio/video stream will be recorded, transcribed for recruiter review, and stored securely in Cloudinary in accordance with recruitment evaluation policies.
                </span>
              </label>
            </div>

            {/* Action Bar */}
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={handleClosePrepModal}
                className="px-4 py-2.5 rounded-xl border border-slate/20 text-xs font-bold"
              >
                Cancel
              </button>
              <a
                href={prepConsentGranted ? `/interview-room/${prepInterview.id}` : '#'}
                onClick={(e) => {
                  if (!prepConsentGranted) {
                    e.preventDefault();
                    addToast("Please review and accept the recording consent above to proceed.", "warning");
                    return;
                  }
                  if (prepStream) {
                    prepStream.getTracks().forEach(t => t.stop());
                  }
                }}
                className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition ${
                  prepConsentGranted
                    ? 'btn-oxblood shadow cursor-pointer'
                    : 'bg-slate/20 text-slate/50 cursor-not-allowed'
                }`}
              >
                <Video className="w-3.5 h-3.5" />
                <span>Join Interview Room</span>
              </a>
            </div>
          </div>
        )}
      </GlassModal>

    </PageTransition>
  );
};
