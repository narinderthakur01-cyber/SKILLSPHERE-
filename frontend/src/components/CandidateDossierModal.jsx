import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User, FileText, CheckCircle2, Video, Calendar, Award,
  Sparkles, X, ExternalLink, Shield, Clock, Play
} from 'lucide-react';
import { interviewsAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const CandidateDossierModal = ({ candidateId, onClose }) => {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [dossier, setDossier] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, mcq, video, interviews

  useEffect(() => {
    let isMounted = true;
    async function fetchDossier() {
      try {
        const res = await interviewsAPI.getCandidateDossier(candidateId);
        if (!isMounted) return;
        setDossier(res.data);
      } catch (err) {
        addToast({
          title: "Dossier Error",
          message: err.response?.data?.detail || "Could not retrieve candidate dossier.",
          type: "error"
        });
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchDossier();
    return () => { isMounted = false; };
  }, [candidateId]);

  if (!candidateId) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="glass-card max-w-4xl w-full p-6 sm:p-8 rounded-3xl border border-oxblood/40 space-y-6 bg-[#141820] text-ivory max-h-[90vh] overflow-y-auto shadow-2xl"
      >
        {/* Header */}
        <div className="flex justify-between items-start pb-4 border-b border-ivory/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-oxblood/20 border border-oxblood/40 flex items-center justify-center text-oxblood dark:text-rose font-display text-xl font-bold">
              {dossier?.candidate?.name?.[0] || 'C'}
            </div>
            <div>
              <h3 className="font-display font-bold text-xl text-white">
                {dossier?.candidate?.name || 'Candidate Dossier'}
              </h3>
              <p className="text-xs font-mono text-ivory/60">
                {dossier?.candidate?.email} &bull; {dossier?.candidate?.experience_years || 0} Years Experience
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-ivory/60 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 border-b border-ivory/10 pb-2 text-xs font-mono">
          {[
            { id: 'overview', label: 'Candidate Profile & Resumes' },
            { id: 'mcq', label: `MCQ Assessments (${dossier?.mcq_assessments?.length || 0})` },
            { id: 'video', label: `Video Assessments (${dossier?.video_assessments?.length || 0})` },
            { id: 'interviews', label: `Interviews & Scorecards (${dossier?.interviews?.length || 0})` }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-3 py-1.5 rounded-xl transition ${
                activeTab === t.id
                  ? 'bg-oxblood text-white font-bold'
                  : 'text-ivory/60 hover:text-white hover:bg-ivory/5'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="py-16 text-center text-xs font-mono text-ivory/50">Loading dossier records...</div>
        ) : (
          <div className="space-y-4">
            {/* 1. Overview */}
            {activeTab === 'overview' && (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-black/40 border border-ivory/10 space-y-2">
                  <h4 className="font-mono text-xs uppercase font-bold text-oxblood dark:text-rose">Skills Inventory</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(dossier?.candidate?.skills || []).map((sk, idx) => (
                      <span key={idx} className="badge-slate font-mono text-xs px-2.5 py-0.5 rounded">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-black/40 border border-ivory/10 space-y-2">
                  <h4 className="font-mono text-xs uppercase font-bold text-oxblood dark:text-rose">Resumes</h4>
                  {dossier?.resumes?.length === 0 ? (
                    <p className="text-xs font-mono text-ivory/50">No resume files uploaded.</p>
                  ) : (
                    <div className="space-y-2">
                      {dossier?.resumes?.map((r) => (
                        <div key={r.id} className="p-3 rounded-xl bg-black/30 border border-ivory/10 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-oxblood dark:text-rose" />
                            <span className="font-mono text-xs text-white">{r.filename}</span>
                          </div>
                          {r.file_url && (
                            <a
                              href={r.file_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-mono text-oxblood dark:text-rose hover:underline flex items-center gap-1"
                            >
                              <span>View File</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 2. MCQ Assessments */}
            {activeTab === 'mcq' && (
              <div className="space-y-3">
                {dossier?.mcq_assessments?.length === 0 ? (
                  <p className="text-xs font-mono text-ivory/50 py-8 text-center">No MCQ assessments taken.</p>
                ) : (
                  dossier?.mcq_assessments?.map((mcq) => (
                    <div key={mcq.id} className="p-4 rounded-2xl bg-black/40 border border-ivory/10 flex items-center justify-between">
                      <div>
                        <h4 className="font-display font-bold text-sm text-white">{mcq.assessment_title}</h4>
                        <p className="text-xs font-mono text-ivory/60">
                          Status: {mcq.status} &bull; Review: {mcq.review_status}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="font-display text-lg font-bold text-oxblood dark:text-rose">
                          {mcq.score !== null ? `${mcq.score}%` : 'Pending'}
                        </span>
                        <span className="block font-mono text-[10px] text-ivory/50">
                          {mcq.passed ? 'PASSED' : 'UNDER REVIEW'}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* 3. Video Assessments */}
            {activeTab === 'video' && (
              <div className="space-y-4">
                {dossier?.video_assessments?.length === 0 ? (
                  <p className="text-xs font-mono text-ivory/50 py-8 text-center">No video assessments recorded.</p>
                ) : (
                  dossier?.video_assessments?.map((va) => (
                    <div key={va.id} className="p-4 rounded-2xl bg-black/40 border border-ivory/10 space-y-3">
                      <div className="flex justify-between items-center">
                        <h4 className="font-display font-bold text-sm text-white">{va.title}</h4>
                        <span className="badge-selected text-[10px] font-mono px-2 py-0.5 rounded">
                          {va.review_status}
                        </span>
                      </div>
                      <div className="space-y-2">
                        {va.responses?.map((resp, i) => (
                          <div key={i} className="p-3 rounded-xl bg-black/30 border border-ivory/10 flex items-center justify-between">
                            <span className="text-xs font-mono text-ivory/80 line-clamp-1">{resp.question}</span>
                            {resp.playback_url && (
                              <a
                                href={resp.playback_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-xs font-mono text-oxblood dark:text-rose hover:underline flex items-center gap-1"
                              >
                                <Play className="w-3.5 h-3.5" />
                                <span>Watch</span>
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* 4. Interviews & Scorecards */}
            {activeTab === 'interviews' && (
              <div className="space-y-4">
                {dossier?.interviews?.length === 0 ? (
                  <p className="text-xs font-mono text-ivory/50 py-8 text-center">No interviews scheduled.</p>
                ) : (
                  dossier?.interviews?.map((inv) => (
                    <div key={inv.id} className="p-5 rounded-2xl bg-black/40 border border-ivory/10 space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="badge-selected font-mono text-[10px] px-2 py-0.5 rounded">
                            {inv.round_title || `Round ${inv.round_number}`}
                          </span>
                          <p className="text-xs font-mono text-ivory/60 mt-1">
                            Scheduled: {new Date(inv.scheduled_time).toLocaleString()}
                          </p>
                        </div>
                        <span className="badge-slate font-mono text-[10px] px-2 py-0.5 rounded">
                          {inv.status}
                        </span>
                      </div>

                      {/* Scorecard Summary if present */}
                      {inv.scorecard && (
                        <div className="p-3 rounded-xl bg-oxblood/10 border border-oxblood/20 space-y-1 text-xs font-mono">
                          <div className="flex justify-between font-bold text-white">
                            <span>Scorecard Recommendation:</span>
                            <span className="text-emerald-400">{inv.scorecard.recommendation}</span>
                          </div>
                          <div className="flex justify-between text-ivory/70">
                            <span>Overall Score: {inv.scorecard.overall_score} / 5</span>
                            <span>Tech: {inv.scorecard.technical_score} | Comm: {inv.scorecard.communication_score}</span>
                          </div>
                        </div>
                      )}

                      {/* Recordings */}
                      {inv.recordings?.length > 0 && (
                        <div className="space-y-1">
                          <span className="font-mono text-[10px] text-ivory/60 uppercase">Recordings:</span>
                          {inv.recordings.map((rec) => (
                            <div key={rec.id} className="flex justify-between items-center text-xs font-mono">
                              <span>Status: {rec.status} ({Math.round(rec.duration_seconds || 0)}s)</span>
                              {rec.playback_url && (
                                <a
                                  href={rec.playback_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-oxblood dark:text-rose hover:underline flex items-center gap-1"
                                >
                                  <Play className="w-3 h-3" />
                                  <span>Signed Playback</span>
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
};
