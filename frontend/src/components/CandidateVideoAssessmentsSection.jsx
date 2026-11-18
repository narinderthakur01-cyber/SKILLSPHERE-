import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Video, Clock, CheckCircle2, ChevronRight, AlertCircle,
  Shield, Play, RefreshCw, FileText
} from 'lucide-react';
import { videoAssessmentsAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const CandidateVideoAssessmentsSection = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchMyVideoAssessments = async () => {
    setLoading(true);
    try {
      const res = await videoAssessmentsAPI.getMyAssessments();
      setAssessments(res.data);
    } catch (err) {
      addToast({
        title: "Load Error",
        message: err.response?.data?.detail || "Could not retrieve video assessments.",
        type: "error"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyVideoAssessments();
  }, []);

  return (
    <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-6">
      <div className="flex justify-between items-center pb-4 border-b border-slate/15 dark:border-rose/15">
        <div>
          <h3 className="font-display text-xl font-bold text-charcoal dark:text-ivory flex items-center gap-2">
            <Video className="w-5 h-5 text-oxblood dark:text-rose" />
            <span>Asynchronous Video Assessments</span>
          </h3>
          <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono mt-1">
            Timed video responses &bull; Record answers directly in browser &bull; Evaluated privately by recruiter
          </p>
        </div>

        <button
          onClick={fetchMyVideoAssessments}
          className="p-2 rounded-xl border border-slate/15 dark:border-rose/15 text-slate/70 dark:text-ivory/70 hover:text-oxblood transition"
          title="Refresh assessments"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((n) => <div key={n} className="h-32 glass-card rounded-2xl animate-pulse" />)}
        </div>
      ) : assessments.length === 0 ? (
        <div className="text-center py-16 rounded-3xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
          <Video className="w-12 h-12 text-slate/30 dark:text-ivory/30 mx-auto mb-3" />
          <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory">No Video Assessments Assigned</h3>
          <p className="text-xs text-slate/60 dark:text-ivory/60 font-mono mt-1 max-w-sm mx-auto">
            When recruiters invite you to complete a video screening round, instructions and prompts will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {assessments.map((a) => {
            const isCompleted = a.status === 'COMPLETED';
            return (
              <div
                key={a.id}
                className={`p-6 rounded-2xl border transition-all ${
                  isCompleted
                    ? 'bg-slate/5 dark:bg-white/5 border-slate/15 dark:border-rose/15'
                    : 'bg-oxblood/5 border-oxblood/30 dark:bg-oxblood/10 shadow-sm'
                }`}
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-mono text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase ${
                        isCompleted ? 'badge-slate' : 'badge-selected'
                      }`}>
                        {a.status}
                      </span>
                      <span className="badge-slate font-mono text-[10px] px-2 py-0.5 rounded">
                        {a.total_questions} Questions
                      </span>
                      {isCompleted && (
                        <span className="text-[10px] font-mono uppercase font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                          {a.review_status}
                        </span>
                      )}
                    </div>

                    <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory mt-2">
                      {a.title}
                    </h4>
                    <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono">
                      Role: {a.job_title}
                    </p>
                  </div>

                  <div className="flex flex-col sm:items-end gap-2 shrink-0">
                    <div className="flex items-center gap-1.5 text-xs font-mono text-slate/60 dark:text-ivory/50">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Assigned {new Date(a.assigned_at).toLocaleDateString()}</span>
                    </div>

                    {!isCompleted ? (
                      <button
                        onClick={() => navigate(`/video-assessment/${a.id}`)}
                        className="btn-oxblood px-4 py-2 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 shadow"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>{a.status === 'IN_PROGRESS' ? 'Resume Assessment' : 'Start Video Assessment'}</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Submitted & Under Review</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
