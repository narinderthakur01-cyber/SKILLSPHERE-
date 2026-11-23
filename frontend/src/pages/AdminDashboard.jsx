import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { adminAPI, jobsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  PageTransitionWrapper,
  StaggerContainer,
  StaggerItem,
  AnimatedCounter,
  LiquidSpotlightCard,
  GlassModal,
  SkeletonShimmer,
  useToast,
} from '../components/MotionComponents';
import {
  ShieldCheck, Users, Briefcase, FileText, CheckCircle2,
  XCircle, AlertTriangle, RefreshCw, Activity, Check, ArrowUpRight,
  Search, Filter, Shield, UserCheck, Building2, Eye, Clock,
  UserPlus, SlidersHorizontal, Trash2, ExternalLink, Lock, Unlock,
  Info, X, Sparkles, ChevronRight, BarChart3, PieChart, Database,
  LifeBuoy
} from 'lucide-react';
import { AdminQuestionBankTab } from '../components/AdminQuestionBankTab';
import { AdminProctoringTab } from '../components/AdminProctoringTab';
import { AdminSupportTicketsTab } from '../components/AdminSupportTicketsTab';

export const AdminDashboard = () => {
  const { user: currentAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'analytics';
  const { addToast } = useToast();

  // Core Data States
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);

  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(true);

  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);

  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Filter States
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('ALL');
  const [userStatusFilter, setUserStatusFilter] = useState('ALL');

  const [jobSearch, setJobSearch] = useState('');
  const [jobStatusFilter, setJobStatusFilter] = useState('ALL');

  // Modal States
  const [inspectUser, setInspectUser] = useState(null);
  const [userToToggle, setUserToToggle] = useState(null);
  const [inspectJob, setInspectJob] = useState(null);
  const [jobToModerate, setJobToModerate] = useState(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditActionFilter, setAuditActionFilter] = useState('ALL');
  const [selectedAuditLog, setSelectedAuditLog] = useState(null);
  const [showAuditModal, setShowAuditModal] = useState(false);

  // Support Ticket Telemetry Metrics
  const [ticketMetrics, setTicketMetrics] = useState(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const setTab = (tabName) => {
    setSearchParams({ tab: tabName });
  };

  const fetchAllData = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchAnalytics(),
      fetchUsers(),
      fetchJobs(),
      fetchAuditLogs(),
      fetchTicketMetrics()
    ]);
    setRefreshing(false);
  };

  const fetchTicketMetrics = async () => {
    try {
      const res = await adminAPI.getTicketMetrics();
      if (res.data) {
        setTicketMetrics(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch support ticket metrics:", err);
    }
  };

  const fetchAuditLogs = async (actionType = auditActionFilter) => {
    try {
      setAuditLoading(true);
      const params = {};
      if (actionType && actionType !== 'ALL') {
        params.action_type = actionType;
      }
      const res = await adminAPI.getAuditLogs(params);
      setAuditLogs(res.data || []);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    } finally {
      setAuditLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setLoadingAnalytics(true);
      const res = await adminAPI.getAnalytics();
      setAnalytics(res.data);
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
      addToast({
        title: 'Analytics Sync Error',
        message: 'Could not fetch real-time telemetry from PostgreSQL cluster.',
        type: 'error',
      });
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setUsersLoading(true);
      const res = await adminAPI.getUsers();
      setUsers(res.data || []);
    } catch (err) {
      console.error('Failed to load users:', err);
      addToast({
        title: 'Users Sync Error',
        message: 'Unable to retrieve user directory.',
        type: 'error',
      });
    } finally {
      setUsersLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      setJobsLoading(true);
      const res = await adminAPI.getJobs();
      setJobs(res.data || []);
    } catch (err) {
      console.error('Failed to load jobs:', err);
      addToast({
        title: 'Jobs Sync Error',
        message: 'Unable to retrieve job postings.',
        type: 'error',
      });
    } finally {
      setJobsLoading(false);
    }
  };

  // User Status Toggle with Optimistic Feedback
  const handleConfirmToggleUser = async () => {
    if (!userToToggle) return;
    const { user: targetUser, nextActive } = userToToggle;
    setActionLoading(true);

    try {
      await adminAPI.toggleUserStatus(targetUser.id, nextActive);
      // Optimistic state update
      setUsers((prev) =>
        prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: nextActive } : u))
      );
      addToast({
        title: nextActive ? 'User Activated' : 'User Deactivated',
        message: `${targetUser.name || targetUser.email} has been ${
          nextActive ? 'activated' : 'deactivated'
        }.`,
        type: 'success',
      });
      setUserToToggle(null);
      // Refresh analytics in background
      fetchAnalytics();
    } catch (err) {
      console.error('Failed to update user status:', err);
      addToast({
        title: 'Status Update Failed',
        message: err.response?.data?.detail || 'An error occurred while updating the user.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Job Moderation with Optimistic Feedback
  const handleConfirmModerateJob = async () => {
    if (!jobToModerate) return;
    const { job: targetJob, nextStatus } = jobToModerate;
    setActionLoading(true);

    try {
      await adminAPI.moderateJob(targetJob.id, nextStatus);
      setJobs((prev) =>
        prev.map((j) => (j.id === targetJob.id ? { ...j, status: nextStatus } : j))
      );
      addToast({
        title: 'Listing Moderated',
        message: `Job "${targetJob.title}" status is now ${nextStatus}.`,
        type: 'success',
      });
      setJobToModerate(null);
      fetchAnalytics();
    } catch (err) {
      console.error('Failed to moderate job:', err);
      addToast({
        title: 'Moderation Error',
        message: err.response?.data?.detail || 'Could not update job status.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Filtered Users computation
  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const q = userSearch.toLowerCase().trim();
      const matchesSearch =
        !q ||
        (u.name && u.name.toLowerCase().includes(q)) ||
        (u.email && u.email.toLowerCase().includes(q)) ||
        (u.id && u.id.toLowerCase().includes(q));

      const matchesRole =
        userRoleFilter === 'ALL' || u.role?.toUpperCase() === userRoleFilter.toUpperCase();

      const matchesStatus =
        userStatusFilter === 'ALL' ||
        (userStatusFilter === 'ACTIVE' && u.is_active) ||
        (userStatusFilter === 'INACTIVE' && !u.is_active);

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, userSearch, userRoleFilter, userStatusFilter]);

  // Filtered Jobs computation
  const filteredJobs = useMemo(() => {
    return jobs.filter((j) => {
      const q = jobSearch.toLowerCase().trim();
      const companyName = j.company?.company_name || '';
      const matchesSearch =
        !q ||
        j.title?.toLowerCase().includes(q) ||
        companyName.toLowerCase().includes(q) ||
        j.location?.toLowerCase().includes(q) ||
        j.department?.toLowerCase().includes(q);

      const matchesStatus =
        jobStatusFilter === 'ALL' || j.status?.toUpperCase() === jobStatusFilter.toUpperCase();

      return matchesSearch && matchesStatus;
    });
  }, [jobs, jobSearch, jobStatusFilter]);

  // Platform User Composition Stats
  const userComposition = useMemo(() => {
    const total = users.length || 1;
    const candidates = users.filter((u) => u.role === 'JOB_SEEKER').length;
    const recruiters = users.filter((u) => u.role === 'RECRUITER').length;
    const admins = users.filter((u) => u.role === 'ADMIN').length;

    return {
      total: users.length,
      candidates,
      candidatePct: Math.round((candidates / total) * 100),
      recruiters,
      recruiterPct: Math.round((recruiters / total) * 100),
      admins,
      adminPct: Math.round((admins / total) * 100),
    };
  }, [users]);

  // Unified Chronological Activity Stream
  const activityStream = useMemo(() => {
    const events = [];

    users.forEach((u) => {
      if (u.created_at) {
        events.push({
          id: `user-${u.id}`,
          type: 'USER_REGISTERED',
          title: `New ${u.role === 'JOB_SEEKER' ? 'Candidate' : u.role === 'RECRUITER' ? 'Recruiter' : 'Admin'} Onboarded`,
          description: `${u.name || u.email} registered on the platform`,
          timestamp: new Date(u.created_at),
          role: u.role,
          badge: u.role,
          isUser: true,
        });
      }
    });

    jobs.forEach((j) => {
      if (j.created_at) {
        events.push({
          id: `job-${j.id}`,
          type: 'JOB_CREATED',
          title: 'Opening Published',
          description: `"${j.title}" by ${j.company?.company_name || 'Enterprise'}`,
          timestamp: new Date(j.created_at),
          status: j.status,
          isJob: true,
        });
      }
    });

    return events.sort((a, b) => b.timestamp - a.timestamp).slice(0, 15);
  }, [users, jobs]);

  // Pipeline conversion metric
  const hiringConversion = useMemo(() => {
    if (!analytics || !analytics.total_applications) return 0;
    const selected = analytics.applications_by_status?.SELECTED || 0;
    return Math.round((selected / analytics.total_applications) * 100);
  }, [analytics]);

  return (
    <PageTransitionWrapper>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="max-w-7xl mx-auto space-y-8">
          
          {/* ======================================================== */}
          {/* 1. COMMAND CENTER EXECUTIVE HEADER */}
          {/* ======================================================== */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-2xl relative overflow-hidden">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-oxblood/10 rounded-full blur-3xl pointer-events-none transform translate-x-20 -translate-y-20" />
            
            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-oxblood/15 text-oxblood dark:text-rose border border-oxblood/30">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h1 className="font-display text-2xl sm:text-3xl font-extrabold tracking-tight text-charcoal dark:text-ivory">
                        Governance & Tenancy Command Center
                      </h1>
                      <span className="badge-oxblood font-mono text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                        SUPER ADMIN
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-slate/75 dark:text-ivory/70 mt-1 leading-relaxed">
                      Real-time enterprise control plane: user identity verification, job posting compliance, and pipeline analytics.
                    </p>
                  </div>
                </div>

                {/* System Telemetry Chips */}
                <div className="flex flex-wrap items-center gap-2.5 mt-4 text-[11px] font-mono">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    Engine 100% Operational
                  </span>
                  <span className="px-3 py-1 rounded-full bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 border border-slate/15 dark:border-rose/15">
                    Database: PostgreSQL 18
                  </span>
                  <span className="px-3 py-1 rounded-full bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 border border-slate/15 dark:border-rose/15">
                    RBAC: JWT Active
                  </span>
                  <span className="px-3 py-1 rounded-full bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20">
                    Admin: {currentAdmin?.email || 'admin@skillsphere.local'}
                  </span>
                </div>
              </div>

              {/* Action Controls */}
              <div className="flex items-center gap-3 self-start lg:self-center">
                <button
                  onClick={fetchAllData}
                  disabled={refreshing}
                  className="btn-secondary px-4 py-2.5 text-xs font-mono font-bold rounded-xl flex items-center gap-2 min-h-[44px]"
                  title="Synchronize cluster state"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-oxblood' : ''}`} />
                  <span>{refreshing ? 'Syncing...' : 'Sync Cluster'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* 2. TAB NAVIGATION WITH ANIMATED PILL */}
          {/* ======================================================== */}
          <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 overflow-x-auto pb-1 scrollbar-none">
            {[
              { id: 'analytics', label: 'Platform Intelligence', icon: Activity, count: null },
              { id: 'tickets', label: 'Support Tickets', icon: LifeBuoy, count: ticketMetrics ? (ticketMetrics.open + ticketMetrics.in_progress) : null },
              { id: 'users', label: 'User Governance', icon: Users, count: users.length },
              { id: 'jobs', label: 'Job Moderation', icon: Briefcase, count: jobs.length },
              { id: 'activity', label: 'System Event Stream', icon: Clock, count: activityStream.length },
              { id: 'audit', label: 'Audit Logs & Governance', icon: ShieldCheck, count: auditLogs.length },
              { id: 'question_bank', label: 'Question Bank & Import', icon: Database, count: null },
              { id: 'proctoring', label: 'Assessment Proctoring', icon: Eye, count: null },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setTab(tab.id)}
                  className={`relative flex items-center gap-2 py-3 px-5 text-xs font-mono font-bold uppercase tracking-wider rounded-t-2xl whitespace-nowrap transition-colors duration-200 min-h-[44px] ${
                    isActive
                      ? 'text-ivory'
                      : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                  }`}
                >
                  {isActive && (
                    <motion.span
                      layoutId="adminTabPill"
                      className="absolute inset-0 bg-oxblood rounded-t-2xl shadow-sm"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                    {tab.count !== null && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
                        isActive ? 'bg-black/25 text-ivory' : 'bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-ivory/60'
                      }`}>
                        {tab.count}
                      </span>
                    )}
                  </span>
                </button>
              );
            })}
          </div>

          {/* ======================================================== */}
          {/* TAB 1: PLATFORM INTELLIGENCE & ANALYTICS */}
          {/* ======================================================== */}
          {activeTab === 'analytics' && (
            <div className="space-y-8">
              {/* KPI Spotlight Cards */}
              <StaggerContainer className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 font-mono">
                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
                    <div className="flex items-center justify-between text-slate/70 dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Total Users</span>
                      <Users className="w-4 h-4 opacity-70" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.total_users || 0} />}
                    </div>
                    <span className="text-[10px] text-slate/60 dark:text-ivory/50 mt-1">Platform-wide</span>
                  </LiquidSpotlightCard>
                </StaggerItem>

                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
                    <div className="flex items-center justify-between text-slate/70 dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Job Seekers</span>
                      <UserCheck className="w-4 h-4 opacity-70 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.total_candidates || 0} />}
                    </div>
                    <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-bold mt-1">
                      {userComposition.candidatePct}% of network
                    </span>
                  </LiquidSpotlightCard>
                </StaggerItem>

                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
                    <div className="flex items-center justify-between text-slate/70 dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Recruiters</span>
                      <Building2 className="w-4 h-4 opacity-70 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.total_recruiters || 0} />}
                    </div>
                    <span className="text-[10px] text-amber-700 dark:text-amber-400 font-bold mt-1">
                      {userComposition.recruiterPct}% of network
                    </span>
                  </LiquidSpotlightCard>
                </StaggerItem>

                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
                    <div className="flex items-center justify-between text-slate/70 dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Total Postings</span>
                      <Briefcase className="w-4 h-4 opacity-70" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.total_jobs || 0} />}
                    </div>
                    <span className="text-[10px] text-slate/60 dark:text-ivory/50 mt-1">All tenants</span>
                  </LiquidSpotlightCard>
                </StaggerItem>

                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
                    <div className="flex items-center justify-between text-slate/70 dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Active Postings</span>
                      <CheckCircle2 className="w-4 h-4 opacity-70 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-charcoal dark:text-ivory mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.active_jobs || 0} />}
                    </div>
                    <span className="text-[10px] text-slate/60 dark:text-ivory/50 mt-1">Open for intake</span>
                  </LiquidSpotlightCard>
                </StaggerItem>

                <StaggerItem>
                  <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-oxblood/40 dark:border-oxblood/50 ring-1 ring-oxblood/30 h-full flex flex-col justify-between bg-oxblood/5">
                    <div className="flex items-center justify-between text-oxblood dark:text-rose">
                      <span className="text-[10px] font-bold uppercase tracking-wider">Applications</span>
                      <FileText className="w-4 h-4 opacity-80" />
                    </div>
                    <div className="text-2xl sm:text-3xl font-extrabold text-oxblood dark:text-rose mt-2">
                      {loadingAnalytics ? <SkeletonShimmer height="h-8" /> : <AnimatedCounter value={analytics?.total_applications || 0} />}
                    </div>
                    <span className="text-[10px] text-oxblood dark:text-rose font-bold mt-1">
                      {hiringConversion}% hired rate
                    </span>
                  </LiquidSpotlightCard>
                </StaggerItem>
              </StaggerContainer>

              {/* Advanced Visual Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Visual Chart 1: SVG Donut User Composition */}
                <div className="lg:col-span-5 glass-card p-6 sm:p-7 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-slate/10 dark:border-rose/10">
                      <div>
                        <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                          <PieChart className="w-4 h-4 text-oxblood" />
                          User Role Breakdown
                        </h3>
                        <p className="text-xs text-slate/70 dark:text-ivory/60 mt-0.5">
                          Active accounts partitioned by security role
                        </p>
                      </div>
                      <span className="badge-slate font-mono text-[10px] font-bold px-2 py-0.5 rounded-full">
                        {users.length} Total
                      </span>
                    </div>

                    {/* Interactive Animated Donut SVG */}
                    <div className="py-6 flex flex-col items-center justify-center">
                      <div className="relative w-44 h-44 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
                          {/* Background Ring */}
                          <circle
                            cx="80"
                            cy="80"
                            r="65"
                            className="stroke-slate/10 dark:stroke-white/10"
                            strokeWidth="18"
                            fill="transparent"
                          />
                          {/* Candidate Segment (#829B88) */}
                          <motion.circle
                            cx="80"
                            cy="80"
                            r="65"
                            stroke="#829B88"
                            strokeWidth="18"
                            fill="transparent"
                            strokeDasharray={2 * Math.PI * 65}
                            initial={{ strokeDashoffset: 2 * Math.PI * 65 }}
                            animate={{
                              strokeDashoffset:
                                2 * Math.PI * 65 -
                                (2 * Math.PI * 65 * (userComposition.candidates / (users.length || 1))),
                            }}
                            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                            strokeLinecap="round"
                          />
                          {/* Recruiter Segment (#C49A62) */}
                          <motion.circle
                            cx="80"
                            cy="80"
                            r="45"
                            stroke="#C49A62"
                            strokeWidth="12"
                            fill="transparent"
                            strokeDasharray={2 * Math.PI * 45}
                            initial={{ strokeDashoffset: 2 * Math.PI * 45 }}
                            animate={{
                              strokeDashoffset:
                                2 * Math.PI * 45 -
                                (2 * Math.PI * 45 * (userComposition.recruiters / (users.length || 1))),
                            }}
                            transition={{ duration: 1.2, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
                            strokeLinecap="round"
                          />
                        </svg>

                        {/* Center Metric Label */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-center font-mono">
                          <span className="text-2xl font-extrabold text-charcoal dark:text-ivory">
                            {users.length}
                          </span>
                          <span className="text-[10px] text-slate/70 dark:text-rose uppercase tracking-wider font-bold">
                            Accounts
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Role Legend Details */}
                  <div className="space-y-2 pt-2 border-t border-slate/10 dark:border-rose/10 font-mono text-xs">
                    <div className="flex items-center justify-between p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-[#829B88]" />
                        <span className="font-bold text-charcoal dark:text-ivory">Candidates</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold">{userComposition.candidates}</span>
                        <span className="text-[10px] text-slate/60 dark:text-ivory/50">({userComposition.candidatePct}%)</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-[#C49A62]" />
                        <span className="font-bold text-charcoal dark:text-ivory">Recruiters</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold">{userComposition.recruiters}</span>
                        <span className="text-[10px] text-slate/60 dark:text-ivory/50">({userComposition.recruiterPct}%)</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-2 rounded-xl bg-slate/5 dark:bg-white/5">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-oxblood" />
                        <span className="font-bold text-charcoal dark:text-ivory">Super Admins</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold">{userComposition.admins}</span>
                        <span className="text-[10px] text-slate/60 dark:text-ivory/50">({userComposition.adminPct}%)</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Visual Chart 2: Pipeline Distribution Funnel */}
                <div className="lg:col-span-7 glass-card p-6 sm:p-7 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-slate/10 dark:border-rose/10">
                      <div>
                        <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-oxblood" />
                          Platform Application Funnel
                        </h3>
                        <p className="text-xs text-slate/70 dark:text-ivory/60 mt-0.5">
                          Status distribution across all active job openings
                        </p>
                      </div>
                      <span className="badge-selected font-mono text-[10px] font-bold px-2 py-0.5 rounded-full">
                        {analytics?.total_applications || 0} Total Apps
                      </span>
                    </div>

                    {/* Interactive Funnel Distribution Bars */}
                    <div className="py-6 space-y-3.5">
                      {analytics?.applications_by_status &&
                        Object.entries(analytics.applications_by_status).map(([statusKey, count]) => {
                          const maxCount = Math.max(
                            ...Object.values(analytics.applications_by_status),
                            1
                          );
                          const pct = Math.round((count / (analytics.total_applications || 1)) * 100);
                          const barWidthPct = Math.max(Math.round((count / maxCount) * 100), count > 0 ? 8 : 2);

                          let barColor = 'bg-slate/30 dark:bg-white/20';
                          let badgeStyle = 'text-slate/70 dark:text-ivory/70';
                          if (statusKey === 'SELECTED') {
                            barColor = 'bg-[#829B88]';
                            badgeStyle = 'text-[#829B88] font-bold';
                          } else if (statusKey === 'UNDER_REVIEW' || statusKey === 'SHORTLISTED') {
                            barColor = 'bg-[#C49A62]';
                            badgeStyle = 'text-[#C49A62] font-bold';
                          } else if (statusKey === 'REJECTED') {
                            barColor = 'bg-oxblood';
                            badgeStyle = 'text-oxblood dark:text-rose font-bold';
                          }

                          return (
                            <div key={statusKey} className="group">
                              <div className="flex items-center justify-between text-xs font-mono mb-1">
                                <span className="font-bold text-charcoal dark:text-ivory flex items-center gap-1.5">
                                  {statusKey.replace('_', ' ')}
                                  {statusKey === 'SELECTED' && (
                                    <span className="badge-selected text-[9px] px-1.5 py-0 rounded">HIRED</span>
                                  )}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className={badgeStyle}>{count}</span>
                                  <span className="text-[10px] text-slate/60 dark:text-ivory/50">
                                    ({pct}%)
                                  </span>
                                </div>
                              </div>
                              <div className="h-3 w-full bg-slate/10 dark:bg-white/5 rounded-full overflow-hidden p-0.5">
                                <motion.div
                                  className={`h-full rounded-full ${barColor}`}
                                  initial={{ width: 0 }}
                                  animate={{ width: `${barWidthPct}%` }}
                                  transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                                />
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Summary Metric Footer */}
                  <div className="pt-4 border-t border-slate/10 dark:border-rose/10 grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono text-xs">
                    <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5">
                      <span className="text-[10px] text-slate/60 dark:text-rose uppercase font-bold">Placement Rate</span>
                      <p className="text-lg font-extrabold text-[#829B88] mt-0.5">{hiringConversion}%</p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5">
                      <span className="text-[10px] text-slate/60 dark:text-rose uppercase font-bold">Seeker / Recruiter</span>
                      <p className="text-lg font-extrabold text-charcoal dark:text-ivory mt-0.5">
                        {userComposition.recruiters > 0
                          ? (userComposition.candidates / userComposition.recruiters).toFixed(1)
                          : userComposition.candidates}:1
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 col-span-2 sm:col-span-1">
                      <span className="text-[10px] text-slate/60 dark:text-rose uppercase font-bold">Active Listings</span>
                      <p className="text-lg font-extrabold text-oxblood dark:text-rose mt-0.5">
                        {analytics?.active_jobs || 0} / {analytics?.total_jobs || 0}
                      </p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: USER GOVERNANCE & RBAC */}
          {/* ======================================================== */}
          {activeTab === 'users' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              
              {/* Header & Controls Bar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate/10 dark:border-rose/10">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Users className="w-5 h-5 text-oxblood" />
                    Platform User Directory
                  </h3>
                  <p className="text-xs text-slate/75 dark:text-ivory/70 mt-0.5">
                    Governed accounts, security roles, and active credential controls
                  </p>
                </div>

                {/* Filter Pills */}
                <div className="flex flex-wrap items-center gap-2">
                  {['ALL', 'JOB_SEEKER', 'RECRUITER', 'ADMIN'].map((role) => (
                    <button
                      key={role}
                      onClick={() => setUserRoleFilter(role)}
                      className={`text-[11px] font-mono font-bold uppercase px-3 py-1.5 rounded-xl transition min-h-[44px] sm:min-h-0 flex items-center ${
                        userRoleFilter === role
                          ? 'bg-oxblood text-ivory shadow-sm'
                          : 'bg-slate/5 dark:bg-white/5 text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                      }`}
                    >
                      {role === 'JOB_SEEKER' ? 'Candidates' : role === 'RECRUITER' ? 'Recruiters' : role === 'ADMIN' ? 'Admins' : 'All Roles'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Search & Status Filters */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                <div className="sm:col-span-8 relative">
                  <Search className="w-4 h-4 text-slate/50 dark:text-ivory/40 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    placeholder="Search by full name, email, or user ID..."
                    className="glass-input pl-10 pr-4 py-2.5 w-full text-xs"
                  />
                  {userSearch && (
                    <button
                      onClick={() => setUserSearch('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate/40 hover:text-charcoal dark:hover:text-ivory"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="sm:col-span-4">
                  <select
                    value={userStatusFilter}
                    onChange={(e) => setUserStatusFilter(e.target.value)}
                    className="glass-input w-full text-xs py-2.5 font-mono"
                  >
                    <option value="ALL">All Account Statuses</option>
                    <option value="ACTIVE">Active Accounts Only</option>
                    <option value="INACTIVE">Deactivated Accounts Only</option>
                  </select>
                </div>
              </div>

              {/* User Count Summary */}
              <div className="text-xs font-mono text-slate/60 dark:text-ivory/50">
                Displaying <span className="font-bold text-charcoal dark:text-ivory">{filteredUsers.length}</span> of {users.length} registered accounts
              </div>

              {/* Desktop Table View (>= 768px) */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-mono font-bold uppercase tracking-wider text-[11px]">
                      <th className="py-3.5 px-4 rounded-l-xl">User & Identity</th>
                      <th className="py-3.5 px-4">Role Assigned</th>
                      <th className="py-3.5 px-4">Registration</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-right rounded-r-xl">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium font-mono">
                    {usersLoading ? (
                      <tr>
                        <td colSpan="5" className="py-8 text-center text-slate/60">
                          <SkeletonShimmer height="h-6" className="max-w-md mx-auto" />
                        </td>
                      </tr>
                    ) : filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-slate/60 dark:text-ivory/50">
                          <Users className="w-8 h-8 mx-auto mb-2 opacity-40" />
                          No users matching search filters.
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => {
                        const isSelf = currentAdmin?.id === u.id;
                        const isAdmin = u.role === 'ADMIN';

                        return (
                          <tr key={u.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4 font-sans">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-oxblood/15 text-oxblood dark:text-rose font-mono font-bold text-xs flex items-center justify-center border border-oxblood/20">
                                  {(u.name || u.email || 'U').slice(0, 2).toUpperCase()}
                                </div>
                                <div>
                                  <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">
                                    {u.name || 'Unnamed User'}
                                  </p>
                                  <p className="font-mono text-slate/70 dark:text-ivory/60 text-[11px]">
                                    {u.email}
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="py-4 px-4">
                              <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                                u.role === 'JOB_SEEKER'
                                  ? 'badge-selected'
                                  : u.role === 'RECRUITER'
                                  ? 'badge-rose'
                                  : 'badge-oxblood'
                              }`}>
                                {u.role === 'JOB_SEEKER' ? 'Candidate' : u.role}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-slate/70 dark:text-ivory/60 text-[11px]">
                              {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                            <td className="py-4 px-4">
                              <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                                u.is_active ? 'badge-selected' : 'bg-red-500/15 text-red-500 border border-red-500/30'
                              }`}>
                                {u.is_active ? 'Active' : 'Deactivated'}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-right space-x-2">
                              {/* Inspect Dossier */}
                              <button
                                onClick={() => setInspectUser(u)}
                                className="btn-secondary px-3.5 py-2 rounded-xl text-xs font-mono font-bold inline-flex items-center gap-1.5 min-h-[40px]"
                                title="Inspect user dossier"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                <span>Inspect</span>
                              </button>

                              {/* Toggle Status (Protected) */}
                              {!isAdmin && !isSelf && (
                                <button
                                  onClick={() =>
                                    setUserToToggle({ user: u, nextActive: !u.is_active })
                                  }
                                  className={`text-xs font-bold px-3.5 py-2 rounded-xl border transition inline-flex items-center gap-1.5 min-h-[40px] ${
                                    u.is_active
                                      ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30 hover:bg-red-500/20'
                                      : 'badge-selected hover:opacity-80'
                                  }`}
                                >
                                  {u.is_active ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                                  <span>{u.is_active ? 'Deactivate' : 'Activate'}</span>
                                </button>
                              )}
                              {(isAdmin || isSelf) && (
                                <span className="text-[10px] text-slate/50 dark:text-ivory/40 italic font-mono px-2">
                                  Protected
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>

              {/* Mobile Stacked Card View (< 768px) */}
              <div className="md:hidden space-y-4">
                {usersLoading ? (
                  <SkeletonShimmer height="h-24" />
                ) : filteredUsers.length === 0 ? (
                  <div className="py-8 text-center text-slate/60 text-xs">No users matching filter criteria.</div>
                ) : (
                  filteredUsers.map((u) => {
                    const isSelf = currentAdmin?.id === u.id;
                    const isAdmin = u.role === 'ADMIN';

                    return (
                      <div
                        key={u.id}
                        className="p-4 rounded-2xl bg-white/60 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full bg-oxblood/15 text-oxblood dark:text-rose font-mono font-bold text-xs flex items-center justify-center">
                              {(u.name || u.email || 'U').slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">
                                {u.name || 'Unnamed User'}
                              </p>
                              <p className="font-mono text-slate/70 dark:text-ivory/60 text-[11px]">
                                {u.email}
                              </p>
                            </div>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            u.is_active ? 'badge-selected' : 'bg-red-500/15 text-red-500'
                          }`}>
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] font-mono text-slate/70 dark:text-ivory/60 pt-2 border-t border-slate/10 dark:border-rose/10">
                          <span>Role: <strong>{u.role}</strong></span>
                          <span>Joined: {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}</span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 pt-2">
                          <button
                            onClick={() => setInspectUser(u)}
                            className="btn-secondary py-2.5 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 min-h-[44px]"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Inspect</span>
                          </button>

                          {!isAdmin && !isSelf ? (
                            <button
                              onClick={() =>
                                setUserToToggle({ user: u, nextActive: !u.is_active })
                              }
                              className={`py-2.5 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 min-h-[44px] ${
                                u.is_active
                                  ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30'
                                  : 'badge-selected'
                              }`}
                            >
                              {u.is_active ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                              <span>{u.is_active ? 'Deactivate' : 'Activate'}</span>
                            </button>
                          ) : (
                            <div className="flex items-center justify-center text-[10px] text-slate/50 font-mono italic">
                              Protected Admin
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: JOB MODERATION & COMPLIANCE */}
          {/* ======================================================== */}
          {activeTab === 'jobs' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              
              {/* Header Bar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate/10 dark:border-rose/10">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Briefcase className="w-5 h-5 text-oxblood" />
                    Job Moderation & Compliance
                  </h3>
                  <p className="text-xs text-slate/75 dark:text-ivory/70 mt-0.5">
                    Review published listings, verify company postings, and moderate status
                  </p>
                </div>

                {/* Status Segmented Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  {['ALL', 'ACTIVE', 'CLOSED', 'DRAFT'].map((st) => (
                    <button
                      key={st}
                      onClick={() => setJobStatusFilter(st)}
                      className={`text-[11px] font-mono font-bold uppercase px-3 py-1.5 rounded-xl transition min-h-[44px] sm:min-h-0 flex items-center ${
                        jobStatusFilter === st
                          ? 'bg-oxblood text-ivory shadow-sm'
                          : 'bg-slate/5 dark:bg-white/5 text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Search Bar */}
              <div className="relative">
                <Search className="w-4 h-4 text-slate/50 dark:text-ivory/40 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={jobSearch}
                  onChange={(e) => setJobSearch(e.target.value)}
                  placeholder="Filter by job title, company name, department, or location..."
                  className="glass-input pl-10 pr-4 py-2.5 w-full text-xs"
                />
              </div>

              {/* Jobs Table (>= 768px) */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-mono font-bold uppercase tracking-wider text-[11px]">
                      <th className="py-3.5 px-4 rounded-l-xl">Role & Company</th>
                      <th className="py-3.5 px-4">Location & Type</th>
                      <th className="py-3.5 px-4">Compensation</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-right rounded-r-xl">Moderation Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium font-mono">
                    {jobsLoading ? (
                      <tr>
                        <td colSpan="5" className="py-8 text-center">
                          <SkeletonShimmer height="h-6" className="max-w-md mx-auto" />
                        </td>
                      </tr>
                    ) : filteredJobs.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-slate/60 dark:text-ivory/50">
                          <Briefcase className="w-8 h-8 mx-auto mb-2 opacity-40" />
                          No job postings matching filter criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredJobs.map((j) => (
                        <tr key={j.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                          <td className="py-4 px-4 font-sans">
                            <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">
                              {j.title}
                            </p>
                            <p className="font-mono text-slate/70 dark:text-ivory/60 text-[11px]">
                              {j.company?.company_name || 'Enterprise Partner'}
                            </p>
                          </td>
                          <td className="py-4 px-4 text-slate/80 dark:text-ivory/75 text-[11px]">
                            {j.job_type} • {j.location}
                          </td>
                          <td className="py-4 px-4 font-mono text-[11px] text-slate/80 dark:text-ivory/75">
                            {j.salary_min && j.salary_max
                              ? `$${(j.salary_min / 1000).toFixed(0)}k - $${(j.salary_max / 1000).toFixed(0)}k`
                              : 'Competitive'}
                          </td>
                          <td className="py-4 px-4">
                            <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                              j.status === 'ACTIVE'
                                ? 'badge-selected'
                                : j.status === 'CLOSED'
                                ? 'bg-slate/15 text-slate/80 dark:text-ivory/60'
                                : 'badge-rose'
                            }`}>
                              {j.status}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-right space-x-2">
                            <button
                              onClick={() => setInspectJob(j)}
                              className="btn-secondary px-3.5 py-2 rounded-xl text-xs font-mono font-bold inline-flex items-center gap-1.5 min-h-[40px]"
                              title="Inspect full posting"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>Preview</span>
                            </button>

                            {j.status !== 'ACTIVE' ? (
                              <button
                                onClick={() =>
                                  setJobToModerate({ job: j, nextStatus: 'ACTIVE' })
                                }
                                className="text-xs font-bold badge-selected px-3.5 py-2 rounded-xl transition inline-flex items-center gap-1.5 min-h-[40px]"
                              >
                                <Check className="w-3.5 h-3.5" />
                                <span>Approve</span>
                              </button>
                            ) : (
                              <button
                                onClick={() =>
                                  setJobToModerate({ job: j, nextStatus: 'CLOSED' })
                                }
                                className="text-xs font-bold text-red-600 dark:text-red-400 bg-red-500/10 px-3.5 py-2 rounded-xl border border-red-500/30 hover:bg-red-500/20 transition inline-flex items-center gap-1.5 min-h-[40px]"
                              >
                                <XCircle className="w-3.5 h-3.5" />
                                <span>Close / Suspend</span>
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Mobile Jobs Card List (< 768px) */}
              <div className="md:hidden space-y-4">
                {jobsLoading ? (
                  <SkeletonShimmer height="h-24" />
                ) : filteredJobs.length === 0 ? (
                  <div className="py-8 text-center text-slate/60 text-xs">No jobs found.</div>
                ) : (
                  filteredJobs.map((j) => (
                    <div
                      key={j.id}
                      className="p-4 rounded-2xl bg-white/60 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-display font-bold text-charcoal dark:text-ivory text-sm">
                            {j.title}
                          </p>
                          <p className="font-mono text-slate/70 dark:text-ivory/60 text-[11px]">
                            {j.company?.company_name || 'Enterprise'}
                          </p>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          j.status === 'ACTIVE' ? 'badge-selected' : 'badge-slate'
                        }`}>
                          {j.status}
                        </span>
                      </div>

                      <div className="text-[11px] font-mono text-slate/70 dark:text-ivory/60">
                        {j.job_type} • {j.location}
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate/10 dark:border-rose/10">
                        <button
                          onClick={() => setInspectJob(j)}
                          className="btn-secondary py-2.5 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 min-h-[44px]"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Preview</span>
                        </button>

                        {j.status !== 'ACTIVE' ? (
                          <button
                            onClick={() =>
                              setJobToModerate({ job: j, nextStatus: 'ACTIVE' })
                            }
                            className="badge-selected py-2.5 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 min-h-[44px]"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                        ) : (
                          <button
                            onClick={() =>
                              setJobToModerate({ job: j, nextStatus: 'CLOSED' })
                            }
                            className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30 py-2.5 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-1.5 min-h-[44px]"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Close</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 4: SYSTEM EVENT STREAM */}
          {/* ======================================================== */}
          {activeTab === 'activity' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate/10 dark:border-rose/10">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <Clock className="w-5 h-5 text-oxblood" />
                    Chronological Platform Audit Trail
                  </h3>
                  <p className="text-xs text-slate/75 dark:text-ivory/70 mt-0.5">
                    Real-time transaction log of identity registrations and catalog operations
                  </p>
                </div>
                <span className="badge-oxblood font-mono text-[10px] font-bold px-2.5 py-0.5 rounded-full">
                  PostgreSQL Real-Time Feed
                </span>
              </div>

              {/* Event Stream List */}
              <div className="space-y-4">
                {activityStream.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className="p-4 rounded-2xl bg-white/50 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex items-start gap-4 hover:border-oxblood/30 transition"
                  >
                    <div className="p-2.5 rounded-xl bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20 shrink-0">
                      {event.isUser ? <UserPlus className="w-4 h-4" /> : <Briefcase className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h4 className="font-display font-bold text-charcoal dark:text-ivory text-sm">
                          {event.title}
                        </h4>
                        <span className="text-[11px] font-mono text-slate/60 dark:text-ivory/50">
                          {event.timestamp.toLocaleDateString()} at{' '}
                          {event.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-xs text-slate/80 dark:text-ivory/70 mt-1">
                        {event.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 5: IMMUTABLE AUDIT LOGS & PLATFORM GOVERNANCE */}
          {/* ======================================================== */}
          {activeTab === 'audit' && (
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6 font-mono">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
                <div>
                  <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Immutable Platform Audit Logs</span>
                  </h3>
                  <p className="text-xs text-slate/70 dark:text-ivory/65 font-normal">
                    Cryptographically tamper-evident event log recording all moderation actions, state changes, and scheduler operations.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={auditActionFilter}
                    onChange={(e) => {
                      setAuditActionFilter(e.target.value);
                      fetchAuditLogs(e.target.value);
                    }}
                    className="glass-input text-xs min-h-[44px]"
                  >
                    <option value="ALL">All Action Types</option>
                    <option value="APPLICATION_STATUS_CHANGE">Application Status Changes</option>
                    <option value="JOB_CREATE">Job Creations</option>
                    <option value="JOB_MODERATE">Job Moderations</option>
                    <option value="USER_STATUS_CHANGE">User Access Toggles</option>
                    <option value="INTERVIEW_SCHEDULE">Interview Schedules</option>
                  </select>

                  <button
                    onClick={() => fetchAuditLogs(auditActionFilter)}
                    className="px-3 py-2 rounded-xl border border-slate/15 dark:border-rose/15 hover:border-oxblood text-slate/70 dark:text-ivory/70 hover:text-oxblood transition min-h-[44px] flex items-center gap-1.5 text-xs font-bold"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>

              {auditLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((n) => <div key={n} className="h-16 glass-card rounded-2xl animate-pulse"></div>)}
                </div>
              ) : auditLogs.length === 0 ? (
                <div className="text-center py-14 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
                  <Shield className="w-10 h-10 text-slate/30 dark:text-ivory/30 mx-auto mb-2" />
                  <p className="font-display text-sm font-bold text-charcoal dark:text-ivory">No audit logs found for filter.</p>
                  <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1">Platform events will be recorded here automatically.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate/15 dark:border-rose/15 bg-slate/10 dark:bg-white/5 text-slate/80 dark:text-ivory/70 font-bold uppercase tracking-wider text-[11px]">
                        <th className="py-3.5 px-4 rounded-l-xl">Timestamp</th>
                        <th className="py-3.5 px-4">Action Type</th>
                        <th className="py-3.5 px-4">Actor</th>
                        <th className="py-3.5 px-4">Target Entity</th>
                        <th className="py-3.5 px-4">Summary</th>
                        <th className="py-3.5 px-4 text-right rounded-r-xl">Metadata</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate/10 dark:divide-white/5 font-medium">
                      {auditLogs.map((log) => {
                        return (
                          <tr key={log.id} className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4 text-slate/70 dark:text-ivory/60 text-[11px] whitespace-nowrap">
                              {new Date(log.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                            </td>
                            <td className="py-4 px-4 whitespace-nowrap">
                              <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase ${
                                log.action_type === 'APPLICATION_STATUS_CHANGE' ? 'badge-oxblood' :
                                log.action_type === 'JOB_MODERATE' ? 'badge-amber' :
                                log.action_type === 'USER_STATUS_CHANGE' ? 'badge-rose' :
                                log.action_type === 'INTERVIEW_SCHEDULE' ? 'badge-selected' : 'badge-slate'
                              }`}>
                                {log.action_type?.replace(/_/g, ' ')}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-charcoal dark:text-ivory font-bold">
                              {log.actor?.name || log.actor?.email || (log.actor_id ? `User #${log.actor_id.slice(0, 8)}` : 'System')}
                            </td>
                            <td className="py-4 px-4 text-slate/60 dark:text-ivory/50">
                              {log.target_entity_type} {log.target_entity_id ? `#${log.target_entity_id.slice(0, 8)}` : ''}
                            </td>
                            <td className="py-4 px-4 max-w-xs truncate text-slate/80 dark:text-ivory/70 text-[11px]">
                              {typeof log.details === 'object'
                                ? JSON.stringify(log.details)
                                : String(log.details || 'Event recorded')}
                            </td>
                            <td className="py-4 px-4 text-right">
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedAuditLog(log);
                                  setShowAuditModal(true);
                                }}
                                className="px-3 py-1.5 rounded-lg border border-slate/20 dark:border-rose/20 text-xs font-bold hover:border-oxblood text-charcoal dark:text-ivory inline-flex items-center gap-1 min-h-[32px]"
                              >
                                <Eye className="w-3 h-3" />
                                <span>Inspect JSON</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 6: QUESTION BANK & BULK IMPORT */}
          {/* ======================================================== */}
          {activeTab === 'question_bank' && (
            <AdminQuestionBankTab />
          )}

          {/* ======================================================== */}
          {/* TAB 7: ASSESSMENT PROCTORING & SURVEILLANCE */}
          {/* ======================================================== */}
          {activeTab === 'proctoring' && (
            <AdminProctoringTab />
          )}

          {/* ======================================================== */}
          {/* TAB 8: SUPPORT TICKETS & INQUIRY TRIAGE */}
          {/* ======================================================== */}
          {activeTab === 'tickets' && (
            <AdminSupportTicketsTab adminList={users.filter((u) => u.role === 'ADMIN')} />
          )}

        </div>
      </div>

      {/* ======================================================== */}
      {/* MODAL 1: USER DOSSIER INSPECTION */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(inspectUser)}
        onClose={() => setInspectUser(null)}
        title="Account Identity Dossier"
        subtitle={`System ID: ${inspectUser?.id || ''}`}
      >
        {inspectUser && (
          <div className="space-y-5 font-mono text-xs">
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-slate/60 dark:text-rose font-bold uppercase">Account Name</span>
                <span className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                  {inspectUser.name || 'Unnamed User'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate/60 dark:text-rose font-bold uppercase">Email Address</span>
                <span className="text-charcoal dark:text-ivory font-bold">{inspectUser.email}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate/60 dark:text-rose font-bold uppercase">Security Role</span>
                <span className="badge-oxblood px-2 py-0.5 rounded-full font-bold">
                  {inspectUser.role}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate/60 dark:text-rose font-bold uppercase">Current Status</span>
                <span className={`px-2 py-0.5 rounded-full font-bold ${
                  inspectUser.is_active ? 'badge-selected' : 'bg-red-500/15 text-red-500'
                }`}>
                  {inspectUser.is_active ? 'Active' : 'Deactivated'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate/60 dark:text-rose font-bold uppercase">Registered On</span>
                <span className="text-slate/70 dark:text-ivory/70">
                  {inspectUser.created_at ? new Date(inspectUser.created_at).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose flex items-start gap-2.5">
              <Shield className="w-4 h-4 shrink-0 mt-0.5" />
              <p className="text-[11px] leading-relaxed">
                Platform identity governance enforced via JWT token invalidation on status change.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setInspectUser(null)}
                className="btn-secondary px-5 py-2.5 rounded-xl font-bold min-h-[44px]"
              >
                Close Dossier
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 2: USER STATUS CONFIRMATION DIALOG */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(userToToggle)}
        onClose={() => !actionLoading && setUserToToggle(null)}
        title={userToToggle?.nextActive ? 'Activate User Account?' : 'Deactivate User Account?'}
        subtitle={`Target: ${userToToggle?.user?.name || userToToggle?.user?.email}`}
      >
        {userToToggle && (
          <div className="space-y-5 text-xs font-sans">
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm">
                  {userToToggle.nextActive
                    ? 'Reactivate Account Access'
                    : 'Revoke Platform Authentication'}
                </p>
                <p className="text-xs mt-1 leading-relaxed opacity-90">
                  {userToToggle.nextActive
                    ? 'The user will immediately regain access to log in and interact with SkillSphere.'
                    : 'The user will be immediately barred from logging in or making authenticated API requests until reactivated.'}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setUserToToggle(null)}
                disabled={actionLoading}
                className="btn-secondary px-4 py-2.5 rounded-xl font-mono font-bold min-h-[44px]"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmToggleUser}
                disabled={actionLoading}
                className={`px-5 py-2.5 rounded-xl font-mono font-bold text-ivory min-h-[44px] transition ${
                  userToToggle.nextActive
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {actionLoading
                  ? 'Updating...'
                  : userToToggle.nextActive
                  ? 'Confirm Activation'
                  : 'Confirm Deactivation'}
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 3: JOB DETAILS PREVIEW */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(inspectJob)}
        onClose={() => setInspectJob(null)}
        title={inspectJob?.title || 'Job Opening'}
        subtitle={`${inspectJob?.company?.company_name || 'Enterprise'} • ${inspectJob?.location || 'Remote'}`}
      >
        {inspectJob && (
          <div className="space-y-4 text-xs font-sans">
            <div className="flex flex-wrap items-center gap-2 font-mono">
              <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                inspectJob.status === 'ACTIVE' ? 'badge-selected' : 'badge-slate'
              }`}>
                {inspectJob.status}
              </span>
              <span className="badge-slate text-[10px] px-2.5 py-0.5 rounded-full font-bold">
                {inspectJob.job_type}
              </span>
              <span className="badge-rose text-[10px] px-2.5 py-0.5 rounded-full font-bold">
                {inspectJob.salary_min && inspectJob.salary_max
                  ? `$${(inspectJob.salary_min / 1000).toFixed(0)}k - $${(inspectJob.salary_max / 1000).toFixed(0)}k / year`
                  : 'Competitive'}
              </span>
            </div>

            <div>
              <h4 className="font-display font-bold text-charcoal dark:text-ivory text-sm mb-1">
                Role Description
              </h4>
              <p className="text-slate/80 dark:text-ivory/70 whitespace-pre-line leading-relaxed p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-rose/10">
                {inspectJob.description || 'No description provided.'}
              </p>
            </div>

            {inspectJob.required_skills && inspectJob.required_skills.length > 0 && (
              <div>
                <h4 className="font-display font-bold text-charcoal dark:text-ivory text-sm mb-1.5">
                  Target Required Skills
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {inspectJob.required_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20 font-mono text-[11px]"
                    >
                      {typeof skill === 'string' ? skill : skill.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end pt-3">
              <button
                onClick={() => setInspectJob(null)}
                className="btn-secondary px-5 py-2.5 rounded-xl font-mono font-bold min-h-[44px]"
              >
                Close Preview
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 4: JOB MODERATION CONFIRMATION */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(jobToModerate)}
        onClose={() => !actionLoading && setJobToModerate(null)}
        title={jobToModerate?.nextStatus === 'ACTIVE' ? 'Approve Job Posting?' : 'Close Job Posting?'}
        subtitle={jobToModerate?.job?.title}
      >
        {jobToModerate && (
          <div className="space-y-5 text-xs font-sans">
            <p className="text-slate/80 dark:text-ivory/70 leading-relaxed">
              {jobToModerate.nextStatus === 'ACTIVE'
                ? 'This listing will become immediately visible in the Candidate Job Discovery feed for applicants to view and apply.'
                : 'This listing will be closed to new candidate applications. Existing applications will be preserved for review.'}
            </p>

            <div className="flex items-center justify-end gap-3 pt-2 font-mono">
              <button
                onClick={() => setJobToModerate(null)}
                disabled={actionLoading}
                className="btn-secondary px-4 py-2.5 rounded-xl font-bold min-h-[44px]"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmModerateJob}
                disabled={actionLoading}
                className="btn-oxblood px-5 py-2.5 rounded-xl font-bold min-h-[44px]"
              >
                {actionLoading ? 'Updating...' : `Confirm ${jobToModerate.nextStatus}`}
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* AUDIT LOG JSON INSPECTOR MODAL */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showAuditModal}
        onClose={() => setShowAuditModal(false)}
        title="Audit Log Event Telemetry"
      >
        {selectedAuditLog && (
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-1">
              <p><span className="text-slate/50">Event ID:</span> <span className="font-bold text-charcoal dark:text-ivory">{selectedAuditLog.id}</span></p>
              <p><span className="text-slate/50">Action Type:</span> <span className="font-bold text-oxblood dark:text-rose">{selectedAuditLog.action_type}</span></p>
              <p><span className="text-slate/50">Actor ID:</span> <span className="text-charcoal dark:text-ivory">{selectedAuditLog.actor_id || 'System'}</span></p>
              <p><span className="text-slate/50">Timestamp:</span> <span className="text-charcoal dark:text-ivory">{new Date(selectedAuditLog.created_at).toISOString()}</span></p>
            </div>

            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate/60 mb-1">Raw JSON Metadata Payload</p>
              <pre className="p-4 rounded-xl bg-black/80 text-emerald-400 text-[11px] overflow-x-auto max-h-60 leading-relaxed border border-slate/20">
                {JSON.stringify(selectedAuditLog.details, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowAuditModal(false)}
                className="px-5 py-2 rounded-xl btn-oxblood text-xs font-bold min-h-[38px]"
              >
                Close Inspector
              </button>
            </div>
          </div>
        )}
      </GlassModal>

    </PageTransitionWrapper>
  );
};
