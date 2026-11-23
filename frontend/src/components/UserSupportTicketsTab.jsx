import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LifeBuoy, Search, Filter, RefreshCw, MessageSquare, Plus,
  CheckCircle2, Clock, Check, X, Send, AlertCircle, AlertTriangle,
  ChevronRight, ChevronLeft, Tag, FileText, User, Zap, PhoneCall
} from 'lucide-react';
import { supportTicketsAPI } from '../services/api';
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
  WAITING_USER: { label: 'Waiting on You', badge: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
  RESOLVED: { label: 'Resolved', badge: 'bg-teal-500/15 text-teal-400 border border-teal-500/30' },
  CLOSED: { label: 'Closed', badge: 'bg-slate/20 text-slate/60 border border-slate/30' },
};

export const UserSupportTicketsTab = ({ preSelectedTicketId = null, onSelectTicket = null }) => {
  const { addToast } = useToast();

  const [tickets, setTickets] = useState([]);
  const [totalTickets, setTotalTickets] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Selected Ticket Detail State
  const [selectedTicketId, setSelectedTicketId] = useState(preSelectedTicketId);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);
  const [requestingLive, setRequestingLive] = useState(false);

  // Create Ticket Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSubject, setNewSubject] = useState('');
  const [newCategory, setNewCategory] = useState('GENERAL');
  const [newPriority, setNewPriority] = useState('MEDIUM');
  const [newDescription, setNewDescription] = useState('');
  const [creatingTicket, setCreatingTicket] = useState(false);

  // 1. Fetch User Tickets
  const fetchMyTickets = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      };
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      const res = await supportTicketsAPI.getMyTickets(params);
      let list = res.data?.tickets || [];
      if (searchTerm.trim()) {
        const q = searchTerm.trim().toLowerCase();
        list = list.filter(
          (t) =>
            t.ticket_number?.toLowerCase().includes(q) ||
            t.subject?.toLowerCase().includes(q)
        );
      }
      setTickets(list);
      setTotalTickets(res.data?.total || list.length);
    } catch (err) {
      console.error('Failed to load tickets:', err);
      addToast({
        title: 'Error',
        message: 'Could not load your support tickets.',
        type: 'error',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [page, statusFilter, searchTerm, addToast]);

  useEffect(() => {
    fetchMyTickets();
  }, [fetchMyTickets]);

  // Open detail if preselected
  useEffect(() => {
    if (preSelectedTicketId) {
      handleOpenDetail(preSelectedTicketId);
    }
  }, [preSelectedTicketId]);

  // 2. Open Ticket Detail
  const handleOpenDetail = async (ticketId) => {
    setSelectedTicketId(ticketId);
    if (onSelectTicket) onSelectTicket(ticketId);
    try {
      setLoadingDetail(true);
      const res = await supportTicketsAPI.getMyTicketDetail(ticketId);
      setTicketDetail(res.data);
      setReplyText('');
    } catch (err) {
      console.error('Failed to load ticket detail:', err);
      addToast({
        title: 'Error',
        message: 'Could not load ticket detail.',
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

  // 3. Post Reply
  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || !ticketDetail || sendingReply) return;

    try {
      setSendingReply(true);
      await supportTicketsAPI.replyMyTicket(ticketDetail.id, replyText.trim());
      addToast({
        title: 'Reply Sent',
        message: 'Your reply has been sent to our support team.',
        type: 'success',
      });
      setReplyText('');
      // Reload ticket detail
      const res = await supportTicketsAPI.getMyTicketDetail(ticketDetail.id);
      setTicketDetail(res.data);
      fetchMyTickets();
    } catch (err) {
      console.error('Failed to send reply:', err);
      addToast({
        title: 'Reply Error',
        message: err.response?.data?.detail || 'Could not send reply.',
        type: 'error',
      });
    } finally {
      setSendingReply(false);
    }
  };

  const handleRequestLiveAgent = async () => {
    if (!ticketDetail || requestingLive) return;
    try {
      setRequestingLive(true);
      const res = await supportTicketsAPI.requestLiveHandoff(ticketDetail.id, 'User requested real-time live support');
      addToast({
        title: 'Live Handoff Requested',
        message: res.data?.message || 'Connected to live support queue.',
        type: 'success',
      });
      // Refresh detail to get is_live_chat = true
      const detailRes = await supportTicketsAPI.getMyTicketDetail(ticketDetail.id);
      setTicketDetail(detailRes.data);
      fetchMyTickets();
    } catch (err) {
      console.error('Failed to request live handoff:', err);
      addToast({
        title: 'Live Chat Error',
        message: err.response?.data?.detail || 'Could not initiate live chat handoff.',
        type: 'error',
      });
    } finally {
      setRequestingLive(false);
    }
  };

  // 4. Create New Ticket
  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!newSubject.trim() || !newDescription.trim() || creatingTicket) return;

    try {
      setCreatingTicket(true);
      const payload = {
        subject: newSubject.trim(),
        description: newDescription.trim(),
        category: newCategory,
        priority: newPriority,
      };
      const res = await supportTicketsAPI.create(payload);
      addToast({
        title: 'Ticket Created',
        message: `Your support ticket ${res.data?.ticket_number || ''} has been registered!`,
        type: 'success',
      });
      setShowCreateModal(false);
      setNewSubject('');
      setNewDescription('');
      setNewCategory('GENERAL');
      setNewPriority('MEDIUM');
      fetchMyTickets();
      if (res.data?.id) {
        handleOpenDetail(res.data.id);
      }
    } catch (err) {
      console.error('Failed to create ticket:', err);
      addToast({
        title: 'Creation Failed',
        message: err.response?.data?.detail || 'Could not create support ticket.',
        type: 'error',
      });
    } finally {
      setCreatingTicket(false);
    }
  };

  const totalPages = Math.ceil(totalTickets / pageSize) || 1;

  return (
    <div className="space-y-6 font-sans">
      {/* Header and Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-display font-extrabold text-charcoal dark:text-ivory flex items-center gap-2.5">
            <LifeBuoy className="w-6 h-6 text-oxblood dark:text-rose" />
            My Support Tickets
          </h2>
          <p className="text-xs text-slate/70 dark:text-ivory/60 mt-1">
            Track inquiries, view administrator responses, and reply to open technical support tickets.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              setRefreshing(true);
              fetchMyTickets();
            }}
            disabled={refreshing}
            className="btn-secondary px-3.5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 shrink-0 min-h-[38px]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-oxblood px-4 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 shrink-0 min-h-[38px]"
          >
            <Plus className="w-4 h-4" />
            <span>New Ticket</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative flex-1 w-full sm:w-auto">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate/50" />
          <input
            type="text"
            placeholder="Search tickets by number (e.g. TICK-2026-0001) or subject..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder-slate/40 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end text-xs font-mono">
          <div className="flex items-center gap-1.5 text-slate/60">
            <Filter className="w-3.5 h-3.5" />
            <span>Status:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory text-xs focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="WAITING_USER">Waiting on You</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Tickets List */}
      <div className="glass-card rounded-2xl border border-slate/15 dark:border-rose/15 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center font-mono text-xs text-slate/60 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-oxblood dark:text-rose" />
            <p>Loading your support tickets...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-400/80 mx-auto" />
            <h4 className="font-display font-bold text-charcoal dark:text-ivory text-sm">
              No Tickets Found
            </h4>
            <p className="text-xs text-slate/60 max-w-sm mx-auto">
              You do not have any support tickets matching the selected filter.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-oxblood px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 mt-2"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Support Ticket</span>
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate/10 dark:divide-rose/10">
            {tickets.map((t) => {
              const catMeta = CATEGORY_META[t.category] || CATEGORY_META.GENERAL;
              const priMeta = PRIORITY_META[t.priority] || PRIORITY_META.MEDIUM;
              const statMeta = STATUS_META[t.status] || STATUS_META.OPEN;

              return (
                <div
                  key={t.id}
                  onClick={() => handleOpenDetail(t.id)}
                  className="p-4 sm:p-5 hover:bg-slate/5 dark:hover:bg-white/5 transition cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-oxblood dark:text-rose">
                        {t.ticket_number}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${statMeta.badge}`}>
                        {statMeta.label}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${catMeta.color}`}>
                        {catMeta.label}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${priMeta.badge}`}>
                        {priMeta.label}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-charcoal dark:text-ivory group-hover:text-oxblood dark:group-hover:text-rose transition truncate">
                      {t.subject}
                    </h3>

                    <p className="text-[11px] text-slate/50 font-mono flex items-center gap-2">
                      <span>Created {new Date(t.created_at).toLocaleDateString()}</span>
                      <span>•</span>
                      <span>{t.message_count} {t.message_count === 1 ? 'message' : 'messages'}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDetail(t.id);
                      }}
                      className="px-3.5 py-1.5 rounded-xl bg-slate/10 dark:bg-white/10 group-hover:bg-oxblood group-hover:text-ivory text-xs font-mono font-bold transition flex items-center gap-1"
                    >
                      <span>View</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
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
      {/* TICKET DETAIL DRAWER / MODAL */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(selectedTicketId)}
        onClose={handleCloseDetail}
        title={ticketDetail ? `${ticketDetail.ticket_number} — ${ticketDetail.subject}` : 'Support Ticket'}
        subtitle={ticketDetail ? `${CATEGORY_META[ticketDetail.category]?.label || ticketDetail.category} • Submitted ${new Date(ticketDetail.created_at).toLocaleDateString()}` : ''}
      >
        {loadingDetail ? (
          <div className="p-12 text-center font-mono text-xs text-slate/60 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-oxblood dark:text-rose" />
            <p>Loading ticket conversation...</p>
          </div>
        ) : ticketDetail ? (
          <div className="space-y-6 text-xs font-sans max-h-[75vh] overflow-y-auto pr-1">
            {/* Meta Card */}
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 space-y-3 font-mono">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${STATUS_META[ticketDetail.status]?.badge || 'badge-slate'}`}>
                    Status: {STATUS_META[ticketDetail.status]?.label || ticketDetail.status}
                  </span>
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${PRIORITY_META[ticketDetail.priority]?.badge || 'badge-slate'}`}>
                    Priority: {PRIORITY_META[ticketDetail.priority]?.label || ticketDetail.priority}
                  </span>
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${CATEGORY_META[ticketDetail.category]?.color || 'badge-slate'}`}>
                    {CATEGORY_META[ticketDetail.category]?.label || ticketDetail.category}
                  </span>
                </div>

                <span className="text-[11px] text-slate/50">
                  Last Updated: {new Date(ticketDetail.updated_at).toLocaleString()}
                </span>
              </div>

              {/* Description */}
              <div className="pt-2 border-t border-slate/10 dark:border-rose/10 font-sans">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate/50 font-bold block mb-1">
                  Problem Description
                </span>
                <p className="text-slate/85 dark:text-ivory/80 leading-relaxed whitespace-pre-line bg-black/10 dark:bg-black/30 p-3 rounded-xl border border-slate/10">
                  {ticketDetail.description}
                </p>
              </div>

              {/* Stage 7 Live Chat Controls */}
              <div className="pt-2 border-t border-slate/10 dark:border-rose/10 flex items-center justify-between font-sans">
                {ticketDetail.is_live_chat ? (
                  <div className="flex items-center gap-2 text-emerald-400 font-mono text-[11px] font-bold">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Real-Time Live Chat Active</span>
                  </div>
                ) : ticketDetail.status !== 'CLOSED' ? (
                  <button
                    type="button"
                    onClick={handleRequestLiveAgent}
                    disabled={requestingLive}
                    className="px-3.5 py-1.5 rounded-xl bg-oxblood/15 hover:bg-oxblood/25 text-oxblood dark:text-rose border border-oxblood/30 text-xs font-mono font-bold flex items-center gap-1.5 transition"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    <span>{requestingLive ? 'Requesting Live Agent...' : 'Connect to Live Human Agent'}</span>
                  </button>
                ) : null}
              </div>
            </div>

            {/* Conversation Thread or Real-Time WebSocket Panel */}
            {ticketDetail.is_live_chat ? (
              <div className="space-y-3">
                <LiveChatPanel
                  ticketId={ticketDetail.id}
                  ticketNumber={ticketDetail.ticket_number}
                  isLiveChat={true}
                  isAdmin={false}
                  ticketStatus={ticketDetail.status}
                  initialMessages={ticketDetail.messages || []}
                  onSessionEnded={() => {
                    handleOpenDetail(ticketDetail.id);
                    fetchMyTickets();
                  }}
                  onMessageSent={() => fetchMyTickets()}
                />
              </div>
            ) : (
              <>
                {/* Conversation Thread */}
                <div className="space-y-3">
                  <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory flex items-center justify-between">
                    <span>Conversation Thread</span>
                    <span className="text-[11px] font-mono text-slate/50">
                      {ticketDetail.messages?.length || 0} messages
                    </span>
                  </h4>

                  <div className="space-y-3">
                    {ticketDetail.messages && ticketDetail.messages.length > 0 ? (
                      ticketDetail.messages.map((m) => {
                        const isAdmin = m.sender_role === 'ADMIN';

                        return (
                          <div
                            key={m.id}
                            className={`p-3.5 rounded-2xl border transition ${
                              isAdmin
                                ? 'bg-oxblood/10 border-oxblood/20 text-charcoal dark:text-ivory ml-4'
                                : 'bg-slate/5 dark:bg-white/5 border-slate/15 dark:border-rose/15 mr-4'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5 text-[11px] font-mono">
                              <span className={`font-bold ${isAdmin ? 'text-oxblood dark:text-rose' : 'text-slate/70 dark:text-ivory/70'}`}>
                                {isAdmin ? 'Support Engineer (Admin)' : `${m.sender_name || 'You'} (Author)`}
                              </span>
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
                        No messages yet.
                      </p>
                    )}
                  </div>
                </div>

                {/* Reply Input Box */}
                {ticketDetail.status === 'CLOSED' ? (
                  <div className="p-3.5 rounded-xl bg-slate/10 dark:bg-white/5 border border-slate/20 text-center font-mono text-xs text-slate/60">
                    This support ticket is marked as CLOSED. New replies cannot be posted.
                  </div>
                ) : (
                  <form onSubmit={handleSendReply} className="space-y-3 pt-2 border-t border-slate/15 dark:border-rose/15">
                    <span className="font-bold text-charcoal dark:text-ivory font-display block">
                      Add a Reply
                    </span>

                    <textarea
                      rows={3}
                      placeholder="Provide additional details or respond to support engineers..."
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      disabled={sendingReply}
                      className="w-full p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory text-xs focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                    />

                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={sendingReply || !replyText.trim()}
                        className="btn-oxblood px-5 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 min-h-[38px] disabled:opacity-50"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>{sendingReply ? 'Sending...' : 'Send Reply'}</span>
                      </button>
                    </div>
                  </form>
                )}
              </>
            )}
          </div>
        ) : null}
      </GlassModal>

      {/* ======================================================== */}
      {/* CREATE TICKET MODAL */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showCreateModal}
        onClose={() => !creatingTicket && setShowCreateModal(false)}
        title="Submit New Support Ticket"
        subtitle="Our technical support team will review and respond to your inquiry."
      >
        <form onSubmit={handleCreateTicket} className="space-y-4 text-xs font-sans">
          {/* Subject */}
          <div>
            <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose block mb-1">
              Issue Subject *
            </label>
            <input
              type="text"
              required
              minLength={3}
              maxLength={200}
              placeholder="e.g. Resume OCR extraction error on PDF"
              value={newSubject}
              onChange={(e) => setNewSubject(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 text-xs text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Category */}
            <div>
              <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose block mb-1">
                Category *
              </label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 text-xs text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose"
              >
                <option value="GENERAL">General Support</option>
                <option value="RESUME_OCR">Resume & OCR Parsing</option>
                <option value="LIVEKIT_VIDEO">LiveKit Video / WebRTC</option>
                <option value="PROCTORING_MCQ">Proctoring & MCQ Assessment</option>
                <option value="ACCOUNT_AUTH">Account & Authentication</option>
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose block mb-1">
                Urgency Priority *
              </label>
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 text-xs text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate/70 dark:text-rose block mb-1">
              Detailed Description *
            </label>
            <textarea
              rows={4}
              required
              minLength={10}
              placeholder="Please describe the steps to reproduce the issue, error messages received, and any troubleshooting attempted..."
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 text-xs text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood dark:focus:border-rose"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 font-mono">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              disabled={creatingTicket}
              className="btn-secondary px-4 py-2 rounded-xl text-xs font-bold min-h-[38px]"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={creatingTicket || !newSubject.trim() || !newDescription.trim()}
              className="btn-oxblood px-5 py-2 rounded-xl text-xs font-bold min-h-[38px] disabled:opacity-50"
            >
              {creatingTicket ? 'Submitting...' : 'Submit Support Ticket'}
            </button>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
