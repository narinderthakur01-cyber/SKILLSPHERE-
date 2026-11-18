import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Eye, ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2,
  XCircle, Clock, Search, Filter, RefreshCw, User, Briefcase,
  Award, FileText, ChevronRight, Check, X, Camera, CameraOff,
  Maximize2, Activity, Info
} from 'lucide-react';
import { proctoringAPI } from '../services/api';
import {
  StaggerContainer,
  StaggerItem,
  LiquidSpotlightCard,
  GlassModal,
  useToast
} from './MotionComponents';

export const AdminProctoringTab = () => {
  const { addToast } = useToast();

  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  // Deep Modal Inspection State
  const [selectedSession, setSelectedSession] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [sessionReviewNotes, setSessionReviewNotes] = useState('');
  const [sessionReviewStatus, setSessionReviewStatus] = useState('FLAGGED');
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch sessions from backend
  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      const params = { filter };
      if (search.trim()) {
        params.search = search.trim();
      }
      const res = await proctoringAPI.getSessions(params);
      setSessions(res.data?.items || []);
    } catch (err) {
      console.error('Failed to load proctoring sessions:', err);
      addToast({
        title: 'Proctoring Sync Error',
        message: 'Could not fetch proctoring sessions from telemetry service.',
        type: 'error',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter, search, addToast]);

  useEffect(() => {
    fetchSessions();
  }, [filter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchSessions();
  };

  // Inspect session detail & full event timeline
  const handleOpenDetail = async (sessionId) => {
    try {
      setDetailLoading(true);
      const res = await proctoringAPI.getSessionDetail(sessionId);
      const detail = res.data;
      setSelectedSession(detail);
      setSessionReviewStatus(detail.monitoring_status === 'FLAGGED' ? 'COMPLETED' : 'FLAGGED');
      setSessionReviewNotes('');
    } catch (err) {
      console.error('Failed to load session details:', err);
      addToast({
        title: 'Telemetry Error',
        message: 'Could not fetch deep session timeline.',
        type: 'error',
      });
    } finally {
      setDetailLoading(false);
    }
  };

  // Inline event review action
  const handleReviewEvent = async (eventId, newStatus) => {
    try {
      setActionLoading(true);
      const res = await proctoringAPI.reviewEvent(eventId, {
        reviewed_status: newStatus,
        admin_notes: `Marked ${newStatus} by Administrator`,
      });

      // Update local timeline event
      setSelectedSession((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          events: prev.events.map((e) => (e.id === eventId ? res.data : e)),
        };
      });

      addToast({
        title: 'Event Reviewed',
        message: `Security event updated to ${newStatus}.`,
        type: 'success',
      });
    } catch (err) {
      console.error('Failed to review event:', err);
      addToast({
        title: 'Review Error',
        message: 'Could not update event status.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Session-level status review action
  const handleReviewSession = async () => {
    if (!selectedSession) return;
    try {
      setActionLoading(true);
      const res = await proctoringAPI.reviewSession(selectedSession.id, {
        monitoring_status: sessionReviewStatus,
        admin_notes: sessionReviewNotes.trim() || undefined,
      });

      setSelectedSession(res.data);
      // Refresh session in list
      setSessions((prev) =>
        prev.map((s) => (s.id === res.data.id ? res.data : s))
      );

      addToast({
        title: 'Session Resolved',
        message: `Proctoring session updated to ${sessionReviewStatus}.`,
        type: 'success',
      });
    } catch (err) {
      console.error('Failed to update session review:', err);
      addToast({
        title: 'Resolution Error',
        message: 'Could not apply session resolution.',
        type: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Telemetry Aggregates
  const totalSessionsCount = sessions.length;
  const flaggedCount = sessions.filter(
    (s) => s.monitoring_status === 'FLAGGED' || s.total_warning_count >= 3
  ).length;
  const totalTabSwitches = sessions.reduce((acc, s) => acc + (s.tab_switch_count || 0), 0);
  const totalFaceAnomalies = sessions.reduce(
    (acc, s) => acc + (s.face_not_detected_count || 0) + (s.multiple_faces_count || 0),
    0
  );

  return (
    <div className="space-y-8 font-sans">
      {/* 1. TOP TELEMETRY KPI SPOTLIGHT CARDS */}
      <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate/70 dark:text-rose">
              <span className="text-[10px] font-bold uppercase tracking-wider">Proctored Sessions</span>
              <Eye className="w-4 h-4 text-oxblood dark:text-rose" />
            </div>
            <div className="mt-4">
              <span className="text-3xl font-display font-extrabold text-charcoal dark:text-ivory">
                {totalSessionsCount}
              </span>
              <p className="text-[10px] text-slate/50 dark:text-ivory/40 mt-1">Total recorded attempts</p>
            </div>
          </LiquidSpotlightCard>
        </StaggerItem>

        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate/70 dark:text-rose">
              <span className="text-[10px] font-bold uppercase tracking-wider">Requires Review</span>
              <ShieldAlert className="w-4 h-4 text-rose animate-pulse" />
            </div>
            <div className="mt-4">
              <span className={`text-3xl font-display font-extrabold ${flaggedCount > 0 ? 'text-rose' : 'text-charcoal dark:text-ivory'}`}>
                {flaggedCount}
              </span>
              <p className="text-[10px] text-slate/50 dark:text-ivory/40 mt-1">3+ warnings or flagged</p>
            </div>
          </LiquidSpotlightCard>
        </StaggerItem>

        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate/70 dark:text-rose">
              <span className="text-[10px] font-bold uppercase tracking-wider">Tab-Switch Deviations</span>
              <Clock className="w-4 h-4 text-amber-500" />
            </div>
            <div className="mt-4">
              <span className="text-3xl font-display font-extrabold text-charcoal dark:text-ivory">
                {totalTabSwitches}
              </span>
              <p className="text-[10px] text-slate/50 dark:text-ivory/40 mt-1">Focus loss events</p>
            </div>
          </LiquidSpotlightCard>
        </StaggerItem>

        <StaggerItem>
          <LiquidSpotlightCard className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 h-full flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate/70 dark:text-rose">
              <span className="text-[10px] font-bold uppercase tracking-wider">Face Anomalies</span>
              <Activity className="w-4 h-4 text-oxblood" />
            </div>
            <div className="mt-4">
              <span className="text-3xl font-display font-extrabold text-charcoal dark:text-ivory">
                {totalFaceAnomalies}
              </span>
              <p className="text-[10px] text-slate/50 dark:text-ivory/40 mt-1">Absent or multiple faces</p>
            </div>
          </LiquidSpotlightCard>
        </StaggerItem>
      </StaggerContainer>

      {/* 2. FILTER & SEARCH CONTROL TOOLBAR */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 font-mono text-xs">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate/40 dark:text-ivory/40" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search candidate name, email, job title, assessment..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory focus:outline-none focus:border-oxblood text-xs"
          />
        </form>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {[
            { id: 'ALL', label: 'All Sessions' },
            { id: 'NORMAL', label: 'Clean (0)' },
            { id: 'WARNINGS', label: 'Warnings (1-2)' },
            { id: 'REQUIRES_REVIEW', label: 'Flagged (3+)' },
            { id: 'COMPLETED', label: 'Completed' },
          ].map((pill) => {
            const isSelected = filter === pill.id;
            return (
              <button
                key={pill.id}
                onClick={() => setFilter(pill.id)}
                className={`px-3 py-1.5 rounded-xl font-bold uppercase tracking-wider transition-colors whitespace-nowrap min-h-[36px] ${
                  isSelected
                    ? 'bg-oxblood text-ivory shadow-sm'
                    : 'bg-slate/5 dark:bg-white/5 text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
                }`}
              >
                {pill.label}
              </button>
            );
          })}

          <button
            onClick={() => {
              setRefreshing(true);
              fetchSessions();
            }}
            disabled={refreshing}
            className="p-2 rounded-xl bg-slate/5 dark:bg-white/5 text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory border border-slate/15 dark:border-rose/15 min-h-[36px]"
            title="Refresh Sessions"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-oxblood' : ''}`} />
          </button>
        </div>
      </div>

      {/* 3. PROCTORING SESSIONS TABLE */}
      <div className="glass-card rounded-2xl border border-slate/15 dark:border-rose/15 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center font-mono">
            <div className="w-8 h-8 rounded-full border-2 border-oxblood/30 border-t-oxblood animate-spin mx-auto mb-3" />
            <p className="text-xs uppercase tracking-wider text-slate/60 dark:text-ivory/60">
              Querying Proctoring Telemetry Cluster...
            </p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center font-mono space-y-3">
            <Eye className="w-10 h-10 text-slate/30 dark:text-ivory/20 mx-auto" />
            <p className="text-sm font-bold text-charcoal dark:text-ivory">No Proctoring Sessions Found</p>
            <p className="text-xs text-slate/50 dark:text-ivory/40">
              No attempts match the active filter criteria.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate/5 dark:bg-white/5 border-b border-slate/15 dark:border-rose/15 text-[10px] text-slate/50 dark:text-ivory/50 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Candidate &amp; Role</th>
                  <th className="py-3 px-4">Assessment</th>
                  <th className="py-3 px-4">Integrity Status</th>
                  <th className="py-3 px-4">Telemetry Breakdown</th>
                  <th className="py-3 px-4">Test Result</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate/10 dark:divide-white/5">
                {sessions.map((s) => {
                  const isFlagged = s.monitoring_status === 'FLAGGED' || s.total_warning_count >= 3;
                  const hasWarnings = s.total_warning_count > 0 && !isFlagged;

                  return (
                    <tr
                      key={s.id}
                      className="hover:bg-slate/5 dark:hover:bg-white/5 transition-colors"
                    >
                      {/* Candidate & Role */}
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-slate/10 dark:bg-white/10 flex items-center justify-center text-charcoal dark:text-ivory font-bold shrink-0">
                            {s.candidate_name?.charAt(0) || 'C'}
                          </div>
                          <div>
                            <p className="font-bold text-charcoal dark:text-ivory text-sm leading-snug">
                              {s.candidate_name}
                            </p>
                            <p className="text-[11px] text-slate/50 dark:text-ivory/50">
                              {s.candidate_email}
                            </p>
                            <p className="text-[10px] text-oxblood dark:text-rose font-semibold mt-0.5">
                              {s.job_title}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Assessment Title */}
                      <td className="py-4 px-4">
                        <span className="font-semibold text-charcoal dark:text-ivory block">
                          {s.assessment_title}
                        </span>
                        <span className="text-[10px] text-slate/50 dark:text-ivory/40">
                          {new Date(s.started_at).toLocaleDateString()} at{' '}
                          {new Date(s.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </td>

                      {/* Integrity Status Badge */}
                      <td className="py-4 px-4">
                        <div className="space-y-1">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-bold text-[10px] uppercase tracking-wider ${
                              isFlagged
                                ? 'bg-rose/20 text-rose border border-rose/30'
                                : hasWarnings
                                ? 'bg-amber-400/20 text-amber-500 border border-amber-400/30'
                                : 'bg-success/20 text-success border border-success/30'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isFlagged ? 'bg-rose' : hasWarnings ? 'bg-amber-400' : 'bg-success'
                              }`}
                            />
                            {isFlagged
                              ? `Flagged (${s.total_warning_count})`
                              : hasWarnings
                              ? `Warning (${s.total_warning_count})`
                              : 'Clean (0)'}
                          </span>
                          <span className="text-[10px] text-slate/50 dark:text-ivory/50 block font-normal">
                            Status: <strong className="uppercase">{s.monitoring_status}</strong>
                          </span>
                        </div>
                      </td>

                      {/* Telemetry Breakdown Chips */}
                      <td className="py-4 px-4">
                        <div className="flex flex-wrap gap-1.5 text-[10px]">
                          <span className="px-2 py-0.5 rounded bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-slate/70 dark:text-ivory/70">
                            Tab Switches: <strong className="text-charcoal dark:text-ivory">{s.tab_switch_count}</strong>
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 text-slate/70 dark:text-ivory/70">
                            Face Absent: <strong className="text-charcoal dark:text-ivory">{s.face_not_detected_count}</strong>
                          </span>
                          {s.multiple_faces_count > 0 && (
                            <span className="px-2 py-0.5 rounded bg-rose/10 border border-rose/20 text-rose font-bold">
                              Multiple Faces: {s.multiple_faces_count}
                            </span>
                          )}
                          {s.camera_interruption_count > 0 && (
                            <span className="px-2 py-0.5 rounded bg-amber-400/10 border border-amber-400/20 text-amber-500">
                              Cam Drops: {s.camera_interruption_count}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Test Result */}
                      <td className="py-4 px-4">
                        {s.result ? (
                          <div>
                            <span
                              className={`inline-block px-2 py-0.5 rounded-full font-bold text-[10px] uppercase ${
                                s.result === 'PASSED'
                                  ? 'bg-success/20 text-success'
                                  : 'bg-rose/20 text-rose'
                              }`}
                            >
                              {s.result}
                            </span>
                            <p className="text-[11px] text-charcoal dark:text-ivory font-bold mt-1">
                              {s.score} / {s.total_marks} ({s.percentage}%)
                            </p>
                          </div>
                        ) : (
                          <span className="text-slate/40 dark:text-ivory/40 text-[11px]">
                            In Progress
                          </span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-4 px-4 text-right">
                        <button
                          onClick={() => handleOpenDetail(s.id)}
                          className="px-3 py-1.5 rounded-xl bg-oxblood text-ivory hover:bg-oxblood/85 text-[11px] font-bold uppercase tracking-wider transition-all shadow-sm flex items-center gap-1.5 ml-auto min-h-[32px]"
                        >
                          <span>Inspect</span>
                          <ChevronRight size={14} />
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

      {/* 4. MODAL: DETAILED TELEMETRY TIMELINE & REVIEW */}
      <GlassModal
        isOpen={Boolean(selectedSession)}
        onClose={() => setSelectedSession(null)}
        title="Proctoring Telemetry Timeline & Governance"
        subtitle={`Session ID: ${selectedSession?.id || ''}`}
      >
        {selectedSession && (
          <div className="space-y-6 font-mono text-xs">
            {/* Candidate & Assessment Overview Box */}
            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-slate/50 dark:text-ivory/50 uppercase">Candidate</p>
                <p className="font-bold text-sm text-charcoal dark:text-ivory mt-0.5">
                  {selectedSession.candidate_name}
                </p>
                <p className="text-xs text-slate/60 dark:text-ivory/60">{selectedSession.candidate_email}</p>
                <p className="text-xs text-oxblood dark:text-rose font-semibold mt-1">
                  Job: {selectedSession.job_title}
                </p>
              </div>

              <div>
                <p className="text-[10px] text-slate/50 dark:text-ivory/50 uppercase">Assessment Metrics</p>
                <p className="font-bold text-charcoal dark:text-ivory mt-0.5">
                  {selectedSession.assessment_title}
                </p>
                <div className="flex items-center gap-3 mt-1.5 text-xs">
                  <span>
                    Score: <strong>{selectedSession.score ?? 'N/A'} / {selectedSession.total_marks ?? 'N/A'}</strong>
                  </span>
                  <span>
                    Percentage: <strong>{selectedSession.percentage ? `${selectedSession.percentage}%` : 'N/A'}</strong>
                  </span>
                  {selectedSession.result && (
                    <span
                      className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                        selectedSession.result === 'PASSED'
                          ? 'bg-success/20 text-success'
                          : 'bg-rose/20 text-rose'
                      }`}
                    >
                      {selectedSession.result}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Event Timeline */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-bold text-charcoal dark:text-ivory uppercase text-xs tracking-wider flex items-center gap-2">
                  <Clock size={14} className="text-oxblood" />
                  <span>Chronological Security Event Stream ({selectedSession.events?.length || 0})</span>
                </h4>
                <span className="text-[10px] text-slate/50 dark:text-ivory/50">
                  Zero video/image storage enforced
                </span>
              </div>

              {(!selectedSession.events || selectedSession.events.length === 0) ? (
                <div className="p-8 text-center bg-slate/5 dark:bg-white/5 rounded-2xl border border-slate/15 dark:border-rose/15 text-slate/50 dark:text-ivory/50">
                  <CheckCircle2 className="w-8 h-8 text-success mx-auto mb-2" />
                  <p className="font-bold text-charcoal dark:text-ivory">Clean Session — Zero Infractions</p>
                  <p className="text-[11px] mt-0.5">No face absences, multi-face events, or tab switches were detected.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-72 overflow-y-auto pr-2 scrollbar-thin">
                  {selectedSession.events.map((evt, idx) => {
                    const isTab = evt.event_type === 'TAB_SWITCH' || evt.event_type === 'WINDOW_BLUR';
                    const isFace = evt.event_type === 'FACE_NOT_DETECTED' || evt.event_type === 'MULTIPLE_FACES_DETECTED';
                    const isCam = evt.event_type === 'CAMERA_INTERRUPTED' || evt.event_type === 'CAMERA_RESTORED';

                    return (
                      <div
                        key={evt.id || idx}
                        className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 flex items-start justify-between gap-3"
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg mt-0.5 ${
                            evt.severity === 'HIGH'
                              ? 'bg-rose/20 text-rose'
                              : 'bg-amber-400/20 text-amber-500'
                          }`}>
                            {isCam ? <CameraOff size={16} /> : isTab ? <Clock size={16} /> : <Eye size={16} />}
                          </div>

                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-charcoal dark:text-ivory">
                                {evt.event_type.replace(/_/g, ' ')}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                                evt.severity === 'HIGH' ? 'bg-rose/20 text-rose' : 'bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-ivory/70'
                              }`}>
                                {evt.severity}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                                evt.reviewed_status === 'REVIEWED'
                                  ? 'bg-success/20 text-success'
                                  : evt.reviewed_status === 'DISMISSED'
                                  ? 'bg-slate/20 text-slate/60 dark:text-ivory/60'
                                  : 'bg-amber-400/20 text-amber-500'
                              }`}>
                                {evt.reviewed_status}
                              </span>
                            </div>

                            <p className="text-[11px] text-slate/60 dark:text-ivory/60 mt-1">
                              Timestamp: {new Date(evt.event_timestamp).toLocaleTimeString()} &bull;{' '}
                              {evt.duration_seconds > 0 && `Duration: ${evt.duration_seconds.toFixed(1)}s away`}
                            </p>

                            {evt.admin_notes && (
                              <p className="text-[10px] text-oxblood dark:text-rose mt-1 italic">
                                Note: {evt.admin_notes}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Event Review Action */}
                        {evt.reviewed_status === 'PENDING' && (
                          <div className="flex items-center gap-1.5 shrink-0">
                            <button
                              onClick={() => handleReviewEvent(evt.id, 'REVIEWED')}
                              disabled={actionLoading}
                              className="p-1.5 rounded-lg bg-success/20 text-success hover:bg-success/30 transition-colors"
                              title="Mark Reviewed / Confirmed"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              onClick={() => handleReviewEvent(evt.id, 'DISMISSED')}
                              disabled={actionLoading}
                              className="p-1.5 rounded-lg bg-slate/10 dark:bg-white/10 text-slate/60 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory transition-colors"
                              title="Dismiss / False Positive"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Session Resolution Form */}
            <div className="p-4 rounded-2xl bg-oxblood/10 border border-rose/30 space-y-3">
              <h4 className="font-bold text-charcoal dark:text-ivory uppercase text-xs tracking-wider">
                Session Governance Resolution
              </h4>
              <p className="text-[11px] text-slate/60 dark:text-ivory/70 leading-relaxed">
                Adjudicate this assessment session. You can confirm the infraction as FLAGGED or clear/approve it as COMPLETED for recruiter consideration.
              </p>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="sessionStatus"
                    value="COMPLETED"
                    checked={sessionReviewStatus === 'COMPLETED'}
                    onChange={() => setSessionReviewStatus('COMPLETED')}
                    className="accent-oxblood"
                  />
                  <span className="text-xs font-bold text-charcoal dark:text-ivory">Approved / Cleared (COMPLETED)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="sessionStatus"
                    value="FLAGGED"
                    checked={sessionReviewStatus === 'FLAGGED'}
                    onChange={() => setSessionReviewStatus('FLAGGED')}
                    className="accent-oxblood"
                  />
                  <span className="text-xs font-bold text-rose">Confirm Breach (FLAGGED)</span>
                </label>
              </div>

              <textarea
                value={sessionReviewNotes}
                onChange={(e) => setSessionReviewNotes(e.target.value)}
                placeholder="Enter administrative review notes or justification..."
                rows={2}
                className="w-full p-2.5 rounded-xl bg-slate/5 dark:bg-black/30 border border-slate/15 dark:border-rose/20 text-charcoal dark:text-ivory text-xs focus:outline-none focus:border-oxblood resize-none"
              />

              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => setSelectedSession(null)}
                  className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory text-xs uppercase tracking-wider"
                >
                  Close
                </button>
                <button
                  onClick={handleReviewSession}
                  disabled={actionLoading}
                  className="px-5 py-2 rounded-xl bg-oxblood hover:bg-oxblood/85 text-ivory font-bold text-xs uppercase tracking-wider shadow-md shadow-oxblood/20 flex items-center gap-2"
                >
                  <ShieldCheck size={14} />
                  <span>{actionLoading ? 'Saving...' : 'Submit Resolution'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </GlassModal>
    </div>
  );
};
