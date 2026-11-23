import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LifeBuoy, Search, Filter, RefreshCw, MessageSquare, Shield,
  AlertTriangle, CheckCircle2, Clock, User, Check, X, Send,
  Lock, ChevronRight, Tag, AlertCircle, FileText, ChevronLeft,
  ChevronDown, UserCheck, Sparkles, SlidersHorizontal, Zap, Radio, Activity
} from 'lucide-react';
import { adminAPI } from '../services/api';
import { LiveChatPanel } from './LiveChatPanel';
import {
  StaggerContainer,
  StaggerItem,
  LiquidSpotlightCard,
  GlassModal,
  useToast
} from './MotionComponents';

// Category Display Helpers
const CATEGORY_META = {
  RESUME_OCR: { label: 'Resume & OCR', color: 'badge-rose' },
  LIVEKIT_VIDEO: { label: 'LiveKit WebRTC', color: 'badge-selected' },
  PROCTORING_MCQ: { label: 'Proctoring & MCQ', color: 'bg-purple-500/15 text-purple-400 border border-purple-500/30' },
  ACCOUNT_AUTH: { label: 'Account & Auth', color: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
  GENERAL: { label: 'General Support', color: 'badge-slate' },
};

// Priority Display Helpers
const PRIORITY_META = {
  LOW: { label: 'Low', badge: 'bg-slate/15 text-slate-400 border border-slate/30' },
  MEDIUM: { label: 'Medium', badge: 'bg-blue-500/15 text-blue-400 border border-blue-500/30' },
  HIGH: { label: 'High', badge: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
  URGENT: { label: 'Urgent', badge: 'bg-red-500/15 text-red-400 border border-red-500/30 animate-pulse' },
};

// Status Display Helpers
const STATUS_META = {
  OPEN: { label: 'Open', badge: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' },
  IN_PROGRESS: { label: 'In Progress', badge: 'bg-blue-500/15 text-blue-400 border border-blue-500/30' },
  WAITING_USER: { label: 'Waiting User', badge: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
  RESOLVED: { label: 'Resolved', badge: 'bg-teal-500/15 text-teal-400 border border-teal-500/30' },
  CLOSED: { label: 'Closed', badge: 'bg-slate/20 text-slate/60 border border-slate/30' },
};

// Valid Lifecycle Transitions State Machine (mirroring backend)
const VALID_TRANSITIONS = {
  OPEN: ['IN_PROGRESS', 'WAITING_USER', 'RESOLVED', 'CLOSED'],
  IN_PROGRESS: ['WAITING_USER', 'RESOLVED', 'CLOSED'],
  WAITING_USER: ['IN_PROGRESS', 'RESOLVED', 'CLOSED'],
  RESOLVED: ['OPEN', 'IN_PROGRESS', 'CLOSED'],
  CLOSED: ['OPEN'],
};

export const AdminSupportTicketsTab = ({ adminList = [] }) => {
  const { addToast } = useToast();

  // Metrics state
  const [metrics, setMetrics] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    waiting_user: 0,
    resolved: 0,
    closed: 0,
    urgent: 0,
    high: 0,
    urgent_or_high: 0,
  });
  const [loadingMetrics, setLoadingMetrics] = useState(true);

  // Tickets list state
  const [tickets, setTickets] = useState([]);
  const [totalTickets, setTotalTickets] = useState(0);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters & Pagination
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Detail Drawer State
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Reply / Internal Note Form State
  const [replyMessage, setReplyMessage] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [sendingReply, setSendingReply] = useState(false);

  // Confirmation Modals State
  const [statusConfirmTarget, setStatusConfirmTarget] = useState(null); // { status, notes }
  const [actionLoading, setActionLoading] = useState(false);

  // Assignment & Priority update state in drawer
  const [selectedAdminId, setSelectedAdminId] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');

  // Stage 7 Administrator Availability & Presence State
  const [availability, setAvailability] = useState({
    is_available: false,
    max_active_chats: 3,
    active_chats_count: 0,
    last_heartbeat_at: null,
    is_active_presence: false,
  });
  const [updatingAvail, setUpdatingAvail] = useState(false);

  // Fetch admin availability and presence
  const fetchAvailability = useCallback(async () => {
    try {
      const res = await adminAPI.getAvailability();
      if (res.data) setAvailability(res.data);
    } catch (e) {
      console.warn('Failed to load admin availability', e);
    }
  }, []);

  // Heartbeat presence: send every 30 seconds when marked available
  useEffect(() => {
    fetchAvailability();
  }, [fetchAvailability]);

  useEffect(() => {
    let timer = null;
    if (availability.is_available) {
      timer = setInterval(async () => {
        try {
          const res = await adminAPI.sendHeartbeat();
          if (res.data) setAvailability(res.data);
        } catch (e) {
          console.warn('Heartbeat error', e);
        }
      }, 30000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [availability.is_available]);

  // Toggle live support availability
  const handleToggleAvailability = async () => {
    try {
      setUpdatingAvail(true);
      const nextStatus = !availability.is_available;
      const res = await adminAPI.updateAvailability({
        is_available: nextStatus,
        max_active_chats: availability.max_active_chats || 3,
      });
      setAvailability(res.data);
      addToast({
        title: nextStatus ? 'Live Support Online' : 'Live Support Offline',
        message: nextStatus
          ? 'You are now marked available for incoming live chat handoffs.'
          : 'You are now offline. Live chat handoffs will be queued.',
        type: nextStatus ? 'success' : 'info',
      });
    } catch (err) {
      console.error('Failed to toggle availability:', err);
    } finally {
      setUpdatingAvail(false);
    }
  };

  // Accept incoming live handoff
  const handleAcceptHandoff = async (ticketId) => {
    try {
      setActionLoading(true);
      const res = await adminAPI.acceptHandoff(ticketId);
      addToast({
        title: 'Handoff Accepted',
        message: 'You have joined the live chat session.',
        type: 'success',
      });
      setTicketDetail(res.data);
      fetchTickets();
      fetchMetrics();
      fetchAvailability();
    } catch (err) {
      console.error('Failed to accept handoff:', err);
      addToast({
        title: 'Handoff Error',
        message: err.response?.data?.detail || 'Could not accept live chat handoff.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // 1. Fetch Metrics
  const fetchMetrics = useCallback(async () => {
    try {
      setLoadingMetrics(true);
      const res = await adminAPI.getTicketMetrics();
      if (res.data) {
        setMetrics(res.data);
      }
    } catch (err) {
      console.error('Failed to load ticket metrics:', err);
      // Non-fatal, metrics will reflect defaults
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  // 2. Fetch Tickets with Filtering & Pagination
  const fetchTickets = useCallback(async () => {
    try {
      setLoadingTickets(true);
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (priorityFilter !== 'ALL') params.priority = priorityFilter;
      if (categoryFilter !== 'ALL') params.category = categoryFilter;
      if (searchTerm.trim()) params.search = searchTerm.trim();

      const res = await adminAPI.getTickets(params);
      setTickets(res.data?.tickets || []);
      setTotalTickets(res.data?.total || 0);
    } catch (err) {
      console.error('Failed to load support tickets:', err);
      addToast({
        title: 'Sync Error',
        message: 'Could not fetch support tickets from server.',
        type: 'error',
      });
    } finally {
      setLoadingTickets(false);
      setRefreshing(false);
    }
  }, [page, statusFilter, priorityFilter, categoryFilter, searchTerm, addToast]);

  // Initial and reactive load
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const handleRefreshAll = async () => {
    setRefreshing(true);
    await Promise.all([fetchMetrics(), fetchTickets()]);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTickets();
  };

  // 3. Open Detail Drawer & Fetch Full Details (including internal notes)
  const handleOpenDetail = async (ticketId) => {
    setSelectedTicketId(ticketId);
    try {
      setLoadingDetail(true);
      const res = await adminAPI.getTicketDetail(ticketId);
      setTicketDetail(res.data);
      setSelectedAdminId(res.data.assigned_admin_id || '');
      setSelectedPriority(res.data.priority || 'MEDIUM');
      setReplyMessage('');
      setIsInternalNote(false);
    } catch (err) {
      console.error('Failed to load ticket detail:', err);
      addToast({
        title: 'Error',
        message: 'Could not fetch ticket details.',
        type: 'error',
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedTicketId(null);
    setTicketDetail(null);
  };

  // 4. Send Public Reply or Internal Note
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() || !ticketDetail) return;

    try {
      setSendingReply(true);
      await adminAPI.sendTicketMessage(ticketDetail.id, replyMessage.trim(), isInternalNote);
      addToast({
        title: isInternalNote ? 'Internal Note Logged' : 'Public Reply Sent',
        message: isInternalNote
          ? 'Internal investigation note saved (visible to admins only).'
          : 'Public reply sent to ticket author.',
        type: 'success',
      });
      setReplyMessage('');
      // Reload ticket detail and refresh lists
      const res = await adminAPI.getTicketDetail(ticketDetail.id);
      setTicketDetail(res.data);
      fetchTickets();
      fetchMetrics();
    } catch (err) {
      console.error('Failed to send ticket message:', err);
      addToast({
        title: 'Message Error',
        message: err.response?.data?.detail || 'Could not send message.',
        type: 'error',
      });
    } finally {
      setSendingReply(false);
    }
  };

  // 5. Initiate Status Change (with confirmation modal for critical statuses)
  const handleRequestStatusChange = (newStatus) => {
    if (!ticketDetail || newStatus === ticketDetail.status) return;

    // Critical transitions: prompt confirmation modal
    if (newStatus === 'RESOLVED' || newStatus === 'CLOSED') {
      setStatusConfirmTarget({
        status: newStatus,
        notes: '',
      });
    } else {
      // Direct transition for OPEN, IN_PROGRESS, WAITING_USER
      executeStatusUpdate(newStatus, '');
    }
  };

  const executeStatusUpdate = async (newStatus, notes = '') => {
    if (!ticketDetail) return;
    try {
      setActionLoading(true);
      const res = await adminAPI.updateTicketStatus(ticketDetail.id, newStatus, notes);
      setTicketDetail(res.data);
      setStatusConfirmTarget(null);
      addToast({
        title: 'Status Updated',
        message: `Ticket moved to ${newStatus}.`,
        type: 'success',
      });
      fetchTickets();
      fetchMetrics();
    } catch (err) {
      console.error('Failed to update ticket status:', err);
      addToast({
        title: 'Status Error',
        message: err.response?.data?.detail || 'Status transition rejected.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // 6. Assign Admin
  const handleAssignAdmin = async (adminId) => {
    if (!ticketDetail) return;
    try {
      setActionLoading(true);
      const res = await adminAPI.assignTicket(ticketDetail.id, adminId || null);
      setTicketDetail(res.data);
      setSelectedAdminId(adminId || '');
      addToast({
        title: 'Assignment Updated',
        message: adminId ? 'Ticket assigned to administrator.' : 'Ticket unassigned.',
        type: 'success',
      });
      fetchTickets();
    } catch (err) {
      console.error('Failed to assign ticket:', err);
      addToast({
        title: 'Assignment Error',
        message: err.response?.data?.detail || 'Could not update assignment.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // 7. Update Priority
  const handlePriorityChange = async (newPriority) => {
    if (!ticketDetail || newPriority === ticketDetail.priority) return;
    try {
      setActionLoading(true);
      const res = await adminAPI.updateTicketPriority(ticketDetail.id, newPriority);
      setTicketDetail(res.data);
      setSelectedPriority(newPriority);
      addToast({
        title: 'Priority Updated',
        message: `Ticket priority set to ${newPriority}.`,
        type: 'success',
      });
      fetchTickets();
      fetchMetrics();
    } catch (err) {
      console.error('Failed to update priority:', err);
      addToast({
        title: 'Priority Error',
        message: err.response?.data?.detail || 'Could not update priority.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Allowed transitions for currently inspected ticket
  const allowedStatusTargets = useMemo(() => {
    if (!ticketDetail) return [];
    return VALID_TRANSITIONS[ticketDetail.status] || [];
  }, [ticketDetail]);

  const totalPages = Math.ceil(totalTickets / pageSize) || 1;

  return (
    <div className="space-y-8 font-sans">
      {/* ======================================================== */}
      {/* 1. TOP HEADER & TELEMETRY KPI SPOTLIGHT CARDS */}
      {/* ======================================================== */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-display font-extrabold text-charcoal dark:text-ivory flex items-center gap-2.5">
            <LifeBuoy className="w-6 h-6 text-oxblood dark:text-rose" />
            Support Ticket Management
          </h2>
          <p className="text-xs text-slate/70 dark:text-ivory/60 mt-1">
            Real-time candidate and recruiter inquiry triage, lifecycle transitions, and private audit trails.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Stage 7 Live Support Presence Toggle */}
          <div className="flex items-center gap-2 p-1.5 px-3 rounded-xl bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono text-xs">
            <button
              onClick={handleToggleAvailability}
              disabled={updatingAvail}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold transition ${
                availability.is_available
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate/20 text-slate/60 hover:text-slate/80'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${availability.is_available ? 'bg-emerald-500 animate-pulse' : 'bg-slate/40'}`} />
              <span>{availability.is_available ? 'Live Support: ONLINE' : 'Live Support: OFFLINE'}</span>
            </button>

            <span className="text-[11px] text-slate/50">
              Active: {availability.active_chats_count}/{availability.max_active_chats}
            </span>
          </div>

          <button
            onClick={handleRefreshAll}
            disabled={refreshing}
            className="btn-secondary px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 shrink-0 min-h-[38px]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* KPI Spotlight Cards */}
      <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 font-mono">
        {/* Total */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate/70 dark:text-rose">Total</span>
            <div className="text-2xl font-extrabold text-charcoal dark:text-ivory mt-1">
              {loadingMetrics ? '—' : metrics.total}
            </div>
            <span className="text-[10px] text-slate/50">All Records</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* Open */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-emerald-500/25 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-500">Open</span>
            <div className="text-2xl font-extrabold text-emerald-500 mt-1">
              {loadingMetrics ? '—' : metrics.open}
            </div>
            <span className="text-[10px] text-slate/50">Awaiting Triage</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* In Progress */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-blue-500/25 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">In Progress</span>
            <div className="text-2xl font-extrabold text-blue-400 mt-1">
              {loadingMetrics ? '—' : metrics.in_progress}
            </div>
            <span className="text-[10px] text-slate/50">Investigating</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* Waiting User */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-amber-500/25 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Waiting User</span>
            <div className="text-2xl font-extrabold text-amber-400 mt-1">
              {loadingMetrics ? '—' : metrics.waiting_user}
            </div>
            <span className="text-[10px] text-slate/50">Pending Reply</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* Resolved */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-teal-500/25 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400">Resolved</span>
            <div className="text-2xl font-extrabold text-teal-400 mt-1">
              {loadingMetrics ? '—' : metrics.resolved}
            </div>
            <span className="text-[10px] text-slate/50">Addressed</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* Closed */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate/60">Closed</span>
            <div className="text-2xl font-extrabold text-slate/60 mt-1">
              {loadingMetrics ? '—' : metrics.closed}
            </div>
            <span className="text-[10px] text-slate/50">Archived</span>
          </LiquidSpotlightCard>
        </StaggerItem>

        {/* Urgent / High */}
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-4 rounded-2xl border border-red-500/30 h-full flex flex-col justify-between bg-red-500/5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Priority
            </span>
            <div className="text-2xl font-extrabold text-red-400 mt-1">
              {loadingMetrics ? '—' : metrics.urgent_or_high}
            </div>
            <span className="text-[10px] text-slate/50">Urgent & High</span>
          </LiquidSpotlightCard>
        </StaggerItem>
      </StaggerContainer>

      {/* ======================================================== */}
      {/* 2. SEARCH & ADVANCED MULTI-CRITERIA FILTERS */}
      {/* ======================================================== */}
      <div className="glass-card p-4 sm:p-5 rounded-2xl border border-slate/15 dark:border-rose/15 space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate/50" />
            <input
              type="text"
              placeholder="Search by ticket number (e.g. TICK-2026-0001) or subject..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder-slate/40 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => { setSearchTerm(''); setPage(1); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate/40 hover:text-slate/70"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            type="submit"
            className="btn-oxblood px-5 py-2.5 rounded-xl text-xs font-mono font-bold shrink-0 min-h-[42px]"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-1 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate/60 dark:text-rose/80 font-bold">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory text-xs focus:outline-none focus:border-oxblood dark:focus:border-rose"
          >
            <option value="ALL">Status: All</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="WAITING_USER">Waiting User</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory text-xs focus:outline-none focus:border-oxblood dark:focus:border-rose"
          >
            <option value="ALL">Priority: All</option>
            <option value="URGENT">Urgent</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory text-xs focus:outline-none focus:border-oxblood dark:focus:border-rose"
          >
            <option value="ALL">Category: All</option>
            <option value="RESUME_OCR">Resume & OCR</option>
            <option value="LIVEKIT_VIDEO">LiveKit Video/WebRTC</option>
            <option value="PROCTORING_MCQ">Proctoring & MCQ</option>
            <option value="ACCOUNT_AUTH">Account & Auth</option>
            <option value="GENERAL">General Support</option>
          </select>

          {(statusFilter !== 'ALL' || priorityFilter !== 'ALL' || categoryFilter !== 'ALL' || searchTerm) && (
            <button
              onClick={() => {
                setStatusFilter('ALL');
                setPriorityFilter('ALL');
                setCategoryFilter('ALL');
                setSearchTerm('');
                setPage(1);
              }}
              className="text-oxblood dark:text-rose hover:underline text-[11px] font-bold"
            >
              Reset Filters
            </button>
          )}

          <div className="ml-auto text-slate/50 text-[11px]">
            Showing {tickets.length} of {totalTickets} tickets
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 3. TICKET QUEUE DATA TABLE */}
      {/* ======================================================== */}
      <div className="glass-card rounded-2xl border border-slate/15 dark:border-rose/15 overflow-hidden">
        {loadingTickets ? (
          <div className="p-12 text-center font-mono text-xs text-slate/60 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-oxblood dark:text-rose" />
            <p>Querying support ticket telemetry...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-400/80 mx-auto" />
            <h4 className="font-display font-bold text-charcoal dark:text-ivory text-sm">
              No Support Tickets Found
            </h4>
            <p className="text-xs text-slate/60 max-w-sm mx-auto">
              No tickets matched the current filter criteria or queue is completely clear.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate/5 dark:bg-white/5 border-b border-slate/15 dark:border-rose/15 font-mono text-[11px] uppercase tracking-wider text-slate/70 dark:text-rose/80">
                <tr>
                  <th className="py-3.5 px-4 font-bold">Ticket #</th>
                  <th className="py-3.5 px-4 font-bold">Subject</th>
                  <th className="py-3.5 px-4 font-bold">Category</th>
                  <th className="py-3.5 px-4 font-bold">Priority</th>
                  <th className="py-3.5 px-4 font-bold">Status</th>
                  <th className="py-3.5 px-4 font-bold">User</th>
                  <th className="py-3.5 px-4 font-bold">Created</th>
                  <th className="py-3.5 px-4 font-bold">Assigned</th>
                  <th className="py-3.5 px-4 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate/10 dark:divide-rose/10 font-sans">
                {tickets.map((t) => {
                  const catMeta = CATEGORY_META[t.category] || CATEGORY_META.GENERAL;
                  const priMeta = PRIORITY_META[t.priority] || PRIORITY_META.MEDIUM;
                  const statMeta = STATUS_META[t.status] || STATUS_META.OPEN;

                  return (
                    <tr
                      key={t.id}
                      onClick={() => handleOpenDetail(t.id)}
                      className="hover:bg-slate/5 dark:hover:bg-white/5 transition cursor-pointer group"
                    >
                      {/* Ticket Number */}
                      <td className="py-3.5 px-4 font-mono font-bold text-oxblood dark:text-rose whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span>{t.ticket_number}</span>
                          {t.is_live_chat && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse">
                              LIVE
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Subject */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <p className="font-bold text-charcoal dark:text-ivory truncate group-hover:text-oxblood dark:group-hover:text-rose transition">
                          {t.subject}
                        </p>
                        <p className="text-[11px] text-slate/50 truncate font-mono">
                          {t.message_count} {t.message_count === 1 ? 'message' : 'messages'}
                        </p>
                      </td>

                      {/* Category */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${catMeta.color}`}>
                          {catMeta.label}
                        </span>
                      </td>

                      {/* Priority */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${priMeta.badge}`}>
                          {priMeta.label}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono font-bold ${statMeta.badge}`}>
                          {statMeta.label}
                        </span>
                      </td>

                      {/* User */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <p className="font-bold text-charcoal dark:text-ivory text-xs">
                          {t.user_name || 'User'}
                        </p>
                        <p className="text-[10px] text-slate/50 font-mono">
                          {t.user_role} • {t.user_email || `ID: ${t.user_id.slice(0, 8)}`}
                        </p>
                      </td>

                      {/* Created */}
                      <td className="py-3.5 px-4 whitespace-nowrap font-mono text-[11px] text-slate/60 dark:text-ivory/60">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>

                      {/* Assigned Admin */}
                      <td className="py-3.5 px-4 whitespace-nowrap font-mono text-[11px]">
                        {t.assigned_admin_name ? (
                          <span className="flex items-center gap-1.5 text-oxblood dark:text-rose font-bold">
                            <UserCheck className="w-3.5 h-3.5" />
                            {t.assigned_admin_name}
                          </span>
                        ) : (
                          <span className="text-slate/40 italic">Unassigned</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          {t.is_live_chat && !t.assigned_admin_id && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAcceptHandoff(t.id);
                              }}
                              className="px-2.5 py-1 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 text-[10px] font-mono font-bold flex items-center gap-1 transition"
                            >
                              <Zap className="w-3 h-3" />
                              <span>Accept Live</span>
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDetail(t.id);
                            }}
                            className="p-1.5 rounded-lg bg-slate/10 dark:bg-white/10 group-hover:bg-oxblood group-hover:text-ivory transition"
                          >
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate/15 dark:border-rose/15 flex items-center justify-between font-mono text-xs">
            <span className="text-slate/50">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn-secondary px-3 py-1.5 rounded-lg text-xs disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="btn-secondary px-3 py-1.5 rounded-lg text-xs disabled:opacity-40"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ======================================================== */}
      {/* 4. TICKET DETAIL MODAL / DRAWER */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(selectedTicketId)}
        onClose={handleCloseDetail}
        title={ticketDetail ? `${ticketDetail.ticket_number} — ${ticketDetail.subject}` : 'Ticket Details'}
        subtitle={ticketDetail ? `${CATEGORY_META[ticketDetail.category]?.label || ticketDetail.category} • Submitted by ${ticketDetail.user_name || ticketDetail.user_email || 'User'}` : ''}
      >
        {loadingDetail ? (
          <div className="p-12 text-center font-mono text-xs text-slate/60 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-oxblood dark:text-rose" />
            <p>Loading conversation thread and telemetry audit logs...</p>
          </div>
        ) : ticketDetail ? (
          <div className="space-y-6 text-xs font-sans max-h-[75vh] overflow-y-auto pr-1">
            {/* Ticket Metadata Banner */}
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3 font-mono">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  {/* Status Badge */}
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${STATUS_META[ticketDetail.status]?.badge || 'badge-slate'}`}>
                    {STATUS_META[ticketDetail.status]?.label || ticketDetail.status}
                  </span>
                  {/* Priority Badge */}
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${PRIORITY_META[ticketDetail.priority]?.badge || 'badge-slate'}`}>
                    Priority: {PRIORITY_META[ticketDetail.priority]?.label || ticketDetail.priority}
                  </span>
                  {/* Category Badge */}
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${CATEGORY_META[ticketDetail.category]?.color || 'badge-slate'}`}>
                    {CATEGORY_META[ticketDetail.category]?.label || ticketDetail.category}
                  </span>
                </div>

                <span className="text-[11px] text-slate/50">
                  Created {new Date(ticketDetail.created_at).toLocaleString()}
                </span>
              </div>

              {/* Description */}
              <div className="pt-2 border-t border-slate/10 dark:border-rose/10 font-sans">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate/50 font-bold block mb-1">
                  Issue Description
                </span>
                <p className="text-slate/85 dark:text-ivory/80 leading-relaxed whitespace-pre-line bg-black/10 dark:bg-black/30 p-3 rounded-xl border border-slate/10">
                  {ticketDetail.description}
                </p>
              </div>

              {/* Administrative Controls Bar: Status, Priority, Assignment */}
              <div className="pt-3 border-t border-slate/10 dark:border-rose/10 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Status Transition Control */}
                <div>
                  <label className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate/60 block mb-1">
                    Transition Lifecycle State
                  </label>
                  <select
                    value={ticketDetail.status}
                    onChange={(e) => handleRequestStatusChange(e.target.value)}
                    disabled={actionLoading || allowedStatusTargets.length === 0}
                    className="w-full px-2.5 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 border border-slate/20 text-xs font-mono font-bold text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose disabled:opacity-50"
                  >
                    <option value={ticketDetail.status}>Current: {ticketDetail.status}</option>
                    {allowedStatusTargets.map((target) => (
                      <option key={target} value={target}>Move to → {target}</option>
                    ))}
                  </select>
                </div>

                {/* Priority Urgency Control */}
                <div>
                  <label className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate/60 block mb-1">
                    Urgency Priority
                  </label>
                  <select
                    value={selectedPriority}
                    onChange={(e) => handlePriorityChange(e.target.value)}
                    disabled={actionLoading}
                    className="w-full px-2.5 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 border border-slate/20 text-xs font-mono font-bold text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose disabled:opacity-50"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>

                {/* Assign Admin Control */}
                <div>
                  <label className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate/60 block mb-1">
                    Assigned Admin
                  </label>
                  <select
                    value={selectedAdminId}
                    onChange={(e) => handleAssignAdmin(e.target.value)}
                    disabled={actionLoading}
                    className="w-full px-2.5 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 border border-slate/20 text-xs font-mono font-bold text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose disabled:opacity-50"
                  >
                    <option value="">Unassigned</option>
                    {adminList.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name || a.email}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Stage 7 Live Handoff Acceptance Banner */}
            {ticketDetail.is_live_chat && !ticketDetail.assigned_admin_id && (
              <div className="p-3.5 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-bold">
                  <Radio className="w-4 h-4 animate-pulse" />
                  <span>Live Handoff Requested: User is waiting for an agent to connect.</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleAcceptHandoff(ticketDetail.id)}
                  disabled={actionLoading}
                  className="btn-oxblood px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shrink-0"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Accept Live Handoff</span>
                </button>
              </div>
            )}

            {/* Stage 7 Real-Time WebSocket Panel or Standard Conversation Thread */}
            {ticketDetail.is_live_chat ? (
              <div className="space-y-3">
                <LiveChatPanel
                  ticketId={ticketDetail.id}
                  ticketNumber={ticketDetail.ticket_number}
                  isLiveChat={true}
                  isAdmin={true}
                  ticketStatus={ticketDetail.status}
                  initialMessages={ticketDetail.messages || []}
                  onSessionEnded={() => {
                    handleOpenDetail(ticketDetail.id);
                    fetchTickets();
                    fetchMetrics();
                    fetchAvailability();
                  }}
                  onMessageSent={() => {
                    fetchTickets();
                    fetchMetrics();
                  }}
                />
              </div>
            ) : (
              <>
                {/* Conversation Thread */}
            <div className="space-y-3">
              <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory flex items-center justify-between">
                <span>Conversation Thread & Investigation Notes</span>
                <span className="text-[11px] font-mono text-slate/50">
                  {ticketDetail.messages?.length || 0} entries
                </span>
              </h4>

              <div className="space-y-3">
                {ticketDetail.messages && ticketDetail.messages.length > 0 ? (
                  ticketDetail.messages.map((m) => {
                    const isInternal = m.is_internal;
                    const isAdmin = m.sender_role === 'ADMIN';

                    return (
                      <div
                        key={m.id}
                        className={`p-3.5 rounded-2xl border transition ${
                          isInternal
                            ? 'bg-amber-500/10 border-amber-500/30 text-charcoal dark:text-ivory ml-4'
                            : isAdmin
                            ? 'bg-oxblood/10 border-oxblood/20 text-charcoal dark:text-ivory ml-4'
                            : 'bg-slate/5 dark:bg-white/5 border-slate/15 dark:border-rose/15 mr-4'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5 text-[11px] font-mono">
                          <div className="flex items-center gap-2">
                            {isInternal ? (
                              <span className="flex items-center gap-1 text-amber-500 font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-[10px]">
                                <Lock className="w-3 h-3" /> INTERNAL NOTE (ADMINS ONLY)
                              </span>
                            ) : (
                              <span className={`font-bold ${isAdmin ? 'text-oxblood dark:text-rose' : 'text-slate/70 dark:text-ivory/70'}`}>
                                {m.sender_name || 'User'} ({m.sender_role})
                              </span>
                            )}
                          </div>
                          <span className="text-slate/50 text-[10px]">
                            {new Date(m.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs leading-relaxed whitespace-pre-line font-sans">
                          {m.message}
                        </p>
                      </div>
                    );
                  })
                ) : (
                  <p className="p-4 text-center text-slate/50 font-mono text-xs">
                    No replies yet.
                  </p>
                )}
              </div>
            </div>

            {/* Audit Trail Section */}
            {ticketDetail.audit_logs && ticketDetail.audit_logs.length > 0 && (
              <div className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 font-mono text-[11px] space-y-2">
                <span className="font-bold uppercase tracking-wider text-slate/50 block">
                  Audit Log History ({ticketDetail.audit_logs.length} events)
                </span>
                <div className="max-h-32 overflow-y-auto space-y-1 pr-1 text-[10px]">
                  {ticketDetail.audit_logs.map((a) => (
                    <div key={a.id} className="flex items-start justify-between border-b border-slate/5 py-1">
                      <span className="text-slate/70 dark:text-rose">
                        [{a.action}] {a.old_status && a.new_status ? `${a.old_status} → ${a.new_status}` : ''}
                      </span>
                      <span className="text-slate/40">
                        {new Date(a.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reply / Internal Note Input Form */}
            <form onSubmit={handleSendMessage} className="space-y-3 pt-2 border-t border-slate/15 dark:border-rose/15">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-charcoal dark:text-ivory font-display">
                  Post Administrative Response
                </span>

                {/* Internal Note Toggle */}
                <label className="flex items-center gap-2 cursor-pointer font-mono text-[11px]">
                  <input
                    type="checkbox"
                    checked={isInternalNote}
                    onChange={(e) => setIsInternalNote(e.target.checked)}
                    className="rounded border-slate/30 text-oxblood focus:ring-oxblood"
                  />
                  <span className={`font-bold flex items-center gap-1 ${isInternalNote ? 'text-amber-500' : 'text-slate/60 dark:text-ivory/60'}`}>
                    <Lock className="w-3 h-3" />
                    Internal Note (Private)
                  </span>
                </label>
              </div>

              <textarea
                rows={3}
                placeholder={
                  isInternalNote
                    ? 'Write an internal investigation note (visible only to administrators)...'
                    : 'Write a public response to the user...'
                }
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                disabled={sendingReply}
                className={`w-full p-3 rounded-xl border text-xs focus:outline-none transition ${
                  isInternalNote
                    ? 'bg-amber-500/5 border-amber-500/30 text-charcoal dark:text-ivory focus:border-amber-500'
                    : 'bg-slate/5 dark:bg-white/5 border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory focus:border-oxblood dark:focus:border-rose'
                }`}
              />

              <div className="flex items-center justify-between font-mono">
                <span className="text-[10px] text-slate/50">
                  {isInternalNote ? 'Confidential • Never exposed to user' : 'Public • User will be notified'}
                </span>

                <button
                  type="submit"
                  disabled={sendingReply || !replyMessage.trim()}
                  className={`px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 min-h-[38px] transition ${
                    isInternalNote
                      ? 'bg-amber-600 hover:bg-amber-700 text-ivory disabled:opacity-50'
                      : 'btn-oxblood disabled:opacity-50'
                  }`}
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{sendingReply ? 'Posting...' : isInternalNote ? 'Save Internal Note' : 'Send Public Reply'}</span>
                </button>
              </div>
            </form>
          </>
        )}
          </div>
        ) : null}
      </GlassModal>

      {/* ======================================================== */}
      {/* 5. STATUS TRANSITION CONFIRMATION MODAL */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(statusConfirmTarget)}
        onClose={() => !actionLoading && setStatusConfirmTarget(null)}
        title={statusConfirmTarget?.status === 'CLOSED' ? 'Close Support Ticket?' : 'Mark Ticket Resolved?'}
        subtitle={ticketDetail?.ticket_number}
      >
        {statusConfirmTarget && (
          <div className="space-y-4 text-xs font-sans">
            <div className={`p-4 rounded-2xl border flex items-start gap-3 ${
              statusConfirmTarget.status === 'CLOSED'
                ? 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-300'
                : 'bg-teal-500/10 border-teal-500/20 text-teal-700 dark:text-teal-300'
            }`}>
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-sm">
                  {statusConfirmTarget.status === 'CLOSED' ? 'Final Ticket Closure' : 'Resolve Ticket Issue'}
                </p>
                <p className="text-xs mt-1 leading-relaxed opacity-90">
                  {statusConfirmTarget.status === 'CLOSED'
                    ? 'Closing this ticket marks it as completely finalized. Regular users will not be able to post further replies unless an admin reopens it.'
                    : 'Marking this ticket as resolved indicates that the technical inquiry or troubleshooting problem has been addressed.'}
                </p>
              </div>
            </div>

            <div>
              <label className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate/60 block mb-1">
                Resolution Notes (Optional)
              </label>
              <textarea
                rows={2}
                placeholder="Brief explanation for this status change..."
                value={statusConfirmTarget.notes}
                onChange={(e) => setStatusConfirmTarget({ ...statusConfirmTarget, notes: e.target.value })}
                className="w-full p-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 text-xs text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 font-mono">
              <button
                type="button"
                onClick={() => setStatusConfirmTarget(null)}
                disabled={actionLoading}
                className="btn-secondary px-4 py-2 rounded-xl text-xs font-bold min-h-[38px]"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={() => executeStatusUpdate(statusConfirmTarget.status, statusConfirmTarget.notes)}
                disabled={actionLoading}
                className={`px-5 py-2 rounded-xl text-xs font-bold text-ivory min-h-[38px] transition ${
                  statusConfirmTarget.status === 'CLOSED'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-teal-600 hover:bg-teal-700'
                }`}
              >
                {actionLoading ? 'Updating...' : `Confirm ${statusConfirmTarget.status}`}
              </button>
            </div>
          </div>
        )}
      </GlassModal>
    </div>
  );
};
