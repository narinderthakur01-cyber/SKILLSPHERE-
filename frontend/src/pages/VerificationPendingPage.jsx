import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, RefreshCw, ShieldAlert, Sparkles, Clock } from 'lucide-react';
import { authAPI } from '../services/api';
import { PageTransition } from '../components/MotionComponents';

/**
 * Mask an email address for privacy (e.g. j***e@domain.com)
 */
function maskEmail(email) {
  if (!email || !email.includes('@')) return email || '';
  const [local, domain] = email.split('@');
  if (local.length <= 2) {
    return `${local[0]}*@${domain}`;
  }
  return `${local[0]}${'*'.repeat(Math.max(local.length - 2, 3))}${local[local.length - 1]}@${domain}`;
}

export const VerificationPendingPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const initialEmail = searchParams.get('email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [isEditingEmail, setIsEditingEmail] = useState(!initialEmail);

  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(60); // 60s initial cooldown after registration
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Handle cooldown countdown
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleResend = async (e) => {
    if (e) e.preventDefault();
    if (!email || !email.trim()) {
      setErrorMsg('Please specify a valid email address.');
      return;
    }
    if (cooldown > 0) return;

    setLoading(true);
    setStatusMsg('');
    setErrorMsg('');

    try {
      const res = await authAPI.resendVerification(email.trim());
      setStatusMsg(res.data?.message || 'A fresh verification email has been dispatched. Please check your inbox.');
      setCooldown(60);
      setIsEditingEmail(false);
    } catch (err) {
      if (err.response?.status === 429) {
        const detail = err.response?.data?.detail;
        setErrorMsg(typeof detail === 'string' ? detail : 'Too many requests. Please wait before requesting another link.');
        setCooldown(60);
      } else {
        const detail = err.response?.data?.detail;
        setErrorMsg(typeof detail === 'string' ? detail : 'Unable to dispatch verification email. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="w-full max-w-md space-y-6">

          {/* Titanium Glass Monolith Card */}
          <div className="glass-card p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-2xl relative overflow-hidden bg-white/75 dark:bg-charcoal/85 backdrop-blur-xl">

            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 -mr-16 -mt-16 w-52 h-52 rounded-full bg-oxblood/10 blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-40 h-40 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

            {/* Header Icon */}
            <div className="text-center mb-6">
              <motion.div
                initial={{ scale: 0.8, rotate: -8 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 260, damping: 20 }}
                className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-oxblood/10 border border-oxblood/25 text-oxblood dark:text-rose mb-4 shadow-inner relative"
              >
                <Mail className="w-8 h-8" />
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-oxblood animate-ping opacity-75" />
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-oxblood" />
              </motion.div>

              <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                Verify Your Email
              </h2>
              <p className="text-xs text-slate/70 dark:text-ivory/60 mt-2 font-normal leading-relaxed">
                We sent a single-use cryptographic verification link to your registered inbox.
              </p>
            </div>

            {/* Target Email Display / Editor */}
            <div className="mb-6 p-4 rounded-2xl bg-charcoal/5 dark:bg-black/25 border border-slate/15 dark:border-rose/15 font-mono text-center">
              <div className="text-[10px] uppercase tracking-wider text-slate/60 dark:text-ivory/50 mb-1 flex items-center justify-center gap-1.5">
                <Clock className="w-3 h-3 text-oxblood dark:text-rose" />
                <span>Link Expires in 30 Minutes</span>
              </div>

              {!isEditingEmail && email ? (
                <div>
                  <p className="text-sm font-bold text-charcoal dark:text-ivory tracking-tight break-all">
                    {maskEmail(email)}
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsEditingEmail(true)}
                    className="mt-2 text-[11px] text-oxblood dark:text-rose hover:underline font-mono"
                  >
                    Change or re-enter email
                  </button>
                </div>
              ) : (
                <div className="mt-2 space-y-2">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter account email"
                    className="w-full px-3 py-2 text-xs bg-white dark:bg-charcoal/60 rounded-xl border border-slate/20 dark:border-rose/20 text-charcoal dark:text-ivory placeholder:text-slate/40 focus:outline-none focus:border-oxblood dark:focus:border-rose"
                  />
                  {initialEmail && (
                    <button
                      type="button"
                      onClick={() => { setEmail(initialEmail); setIsEditingEmail(false); }}
                      className="text-[10px] text-slate/50 dark:text-ivory/40 hover:underline"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Status & Error Alerts */}
            <AnimatePresence mode="wait">
              {statusMsg && (
                <motion.div
                  key="status-msg"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="mb-5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400 text-xs font-mono flex items-start gap-2"
                >
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{statusMsg}</span>
                </motion.div>
              )}

              {errorMsg && (
                <motion.div
                  key="error-msg"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="mb-5 p-3 rounded-xl bg-error/10 border border-error/25 text-error text-xs font-mono flex items-start gap-2"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Instruction Checklist */}
            <div className="mb-6 space-y-2 text-xs text-slate/75 dark:text-ivory/70 font-sans">
              <div className="flex items-start gap-2.5">
                <span className="w-4 h-4 rounded-full bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5">1</span>
                <p>Open your email client and locate the message from <strong>SkillSphere Security</strong>.</p>
              </div>
              <div className="flex items-start gap-2.5">
                <span className="w-4 h-4 rounded-full bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5">2</span>
                <p>Click the <strong>"Verify Email Address"</strong> button within 30 minutes.</p>
              </div>
              <div className="flex items-start gap-2.5">
                <span className="w-4 h-4 rounded-full bg-oxblood/10 text-oxblood dark:text-rose flex items-center justify-center text-[10px] font-mono font-bold shrink-0 mt-0.5">3</span>
                <p>Don't see it? Check your <strong>Spam / Junk</strong> folder or click Resend below.</p>
              </div>
            </div>

            {/* Resend Action Form */}
            <form onSubmit={handleResend} className="space-y-4 font-mono">
              <button
                type="submit"
                disabled={loading || cooldown > 0}
                className="w-full min-h-[48px] py-3 px-4 rounded-xl font-bold text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                ) : cooldown > 0 ? (
                  <span className="flex items-center gap-2 text-[11px]">
                    <Clock className="w-3.5 h-3.5" />
                    Resend link in {cooldown}s
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5" />
                    Resend Verification Email
                  </span>
                )}
              </button>
            </form>

            {/* Back to Login Footer */}
            <div className="mt-8 pt-5 border-t border-slate/15 dark:border-rose/15 flex items-center justify-between text-xs font-mono">
              <Link
                to="/auth?mode=login"
                className="inline-flex items-center gap-1.5 text-slate/70 dark:text-ivory/60 hover:text-oxblood dark:hover:text-rose transition"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Sign In</span>
              </Link>

              <Link
                to="/auth?mode=register"
                className="text-slate/60 dark:text-ivory/50 hover:text-charcoal dark:hover:text-ivory transition text-[11px]"
              >
                Create new account
              </Link>
            </div>

          </div>

          {/* Security Telemetry Badge */}
          <div className="text-center text-[10px] font-mono text-slate/50 dark:text-ivory/40 tracking-wider">
            <span>SHA-256 SIGNED • 30-MINUTE EXPIRY • ANTI-ENUMERATION GUARD</span>
          </div>

        </div>
      </div>
    </PageTransition>
  );
};
