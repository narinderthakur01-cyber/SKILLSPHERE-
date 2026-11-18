import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Clock, ShieldAlert, ArrowRight, ArrowLeft, RefreshCw, Mail, Sparkles } from 'lucide-react';
import { authAPI } from '../services/api';
import { PageTransition } from '../components/MotionComponents';

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  // Status: 'verifying' | 'success' | 'expired' | 'invalid' | 'missing'
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resendFeedback, setResendFeedback] = useState('');
  const [resendError, setResendError] = useState('');

  const hasFiredRef = useRef(false);

  // Cooldown countdown
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const interval = setInterval(() => {
      setResendCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [resendCooldown]);

  // Execute verification on mount
  useEffect(() => {
    let isCancelled = false;

    if (!token || !token.trim()) {
      setStatus('missing');
      setMessage('No verification token detected in the URL query parameters.');
      return;
    }

    if (hasFiredRef.current) return;
    hasFiredRef.current = true;

    const verify = async () => {
      try {
        const res = await authAPI.verifyEmail(token.trim());
        if (!isCancelled) {
          setStatus('success');
          setMessage(res.data?.message || 'Email successfully verified.');
        }
      } catch (err) {
        if (!isCancelled) {
          const detail = err.response?.data?.detail || '';
          const detailStr = typeof detail === 'string' ? detail.toLowerCase() : '';
          if (detailStr.includes('expired')) {
            setStatus('expired');
            setMessage(typeof detail === 'string' ? detail : 'This verification link has expired. Verification links are valid for 30 minutes.');
          } else {
            setStatus('invalid');
            setMessage(typeof detail === 'string' ? detail : 'This verification link is invalid or has already been used.');
          }
        }
      }
    };

    verify();

    return () => {
      isCancelled = true;
    };
  }, [token]);

  const handleResend = async (e) => {
    if (e) e.preventDefault();
    if (!resendEmail || !resendEmail.trim()) {
      setResendError('Please enter your account email.');
      return;
    }
    if (resendCooldown > 0) return;

    setResending(true);
    setResendFeedback('');
    setResendError('');

    try {
      const res = await authAPI.resendVerification(resendEmail.trim());
      setResendFeedback(res.data?.message || 'A fresh verification email has been dispatched. Please check your inbox.');
      setResendCooldown(60);
    } catch (err) {
      if (err.response?.status === 429) {
        const detail = err.response?.data?.detail;
        setResendError(typeof detail === 'string' ? detail : 'Rate limit reached. Please wait a moment before requesting another link.');
        setResendCooldown(60);
      } else {
        const detail = err.response?.data?.detail;
        setResendError(typeof detail === 'string' ? detail : 'Failed to send verification link. Please check the email and try again.');
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="w-full max-w-md space-y-6">

          {/* Monolith Glass Card */}
          <div className="glass-card p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-2xl relative overflow-hidden bg-white/75 dark:bg-charcoal/85 backdrop-blur-xl">

            {/* Ambient Lighting */}
            <div className="absolute top-0 right-0 -mr-16 -mt-16 w-52 h-52 rounded-full bg-oxblood/10 blur-3xl pointer-events-none" />
            {status === 'success' && (
              <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-44 h-44 rounded-full bg-emerald-500/15 blur-3xl pointer-events-none" />
            )}

            {/* 1. STATE: VERIFYING */}
            {status === 'verifying' && (
              <div className="text-center py-6 space-y-4 font-mono">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-oxblood/10 border border-oxblood/20 flex items-center justify-center">
                  <div className="w-7 h-7 border-3 border-oxblood/30 border-t-oxblood rounded-full animate-spin" />
                </div>
                <div>
                  <h2 className="text-xl font-display font-bold text-charcoal dark:text-ivory">
                    Authenticating Verification Token
                  </h2>
                  <p className="text-xs text-slate/60 dark:text-ivory/50 mt-1 font-sans">
                    Validating SHA-256 cryptographic signature and expiry...
                  </p>
                </div>
              </div>
            )}

            {/* 2. STATE: SUCCESS */}
            {status === 'success' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="text-center space-y-5"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400 mb-1">
                  <CheckCircle2 className="w-9 h-9" />
                </div>

                <div>
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-2">
                    <Sparkles className="w-3 h-3" />
                    <span>Identity Cryptographically Verified</span>
                  </div>
                  <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                    Email Verified!
                  </h2>
                  <p className="text-xs text-slate/70 dark:text-ivory/60 mt-2 font-sans leading-relaxed">
                    {message || 'Your SkillSphere account is fully authenticated and unlocked. A welcome confirmation has been dispatched.'}
                  </p>
                </div>

                <div className="pt-2">
                  <Link
                    to="/auth?mode=login"
                    className="w-full min-h-[48px] py-3.5 px-4 rounded-xl font-bold font-mono text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition shadow-md"
                  >
                    <span>Proceed to Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </motion.div>
            )}

            {/* 3. STATE: EXPIRED */}
            {status === 'expired' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="text-center space-y-5"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/25 text-amber-600 dark:text-amber-400 mb-1">
                  <Clock className="w-8 h-8" />
                </div>

                <div>
                  <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                    Verification Link Expired
                  </h2>
                  <p className="text-xs text-slate/70 dark:text-ivory/60 mt-2 font-sans leading-relaxed">
                    {message || 'Security verification links are valid for 30 minutes. Enter your email below to receive a fresh single-use link.'}
                  </p>
                </div>

                {/* Resend Form */}
                <form onSubmit={handleResend} className="space-y-3 font-mono text-left pt-2">
                  <div className="relative flex items-center">
                    <Mail className="absolute left-3.5 w-4 h-4 text-slate/40 dark:text-rose/50" />
                    <input
                      type="email"
                      required
                      placeholder="account@company.com"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-white/70 dark:bg-black/25 rounded-xl border border-slate/20 dark:border-rose/20 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                    />
                  </div>

                  {resendFeedback && (
                    <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">
                      ✓ {resendFeedback}
                    </p>
                  )}
                  {resendError && (
                    <p className="text-[11px] text-error font-mono">
                      ⚠ {resendError}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={resending || resendCooldown > 0}
                    className="w-full min-h-[44px] py-2.5 px-4 rounded-xl font-bold text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition disabled:opacity-50"
                  >
                    {resending ? (
                      <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                    ) : resendCooldown > 0 ? (
                      <span>Resend available in {resendCooldown}s</span>
                    ) : (
                      <span className="flex items-center gap-1.5">
                        <RefreshCw className="w-3.5 h-3.5" />
                        Send Fresh Verification Link
                      </span>
                    )}
                  </button>
                </form>

                <div className="pt-2 border-t border-slate/15 dark:border-rose/15">
                  <Link
                    to="/auth?mode=login"
                    className="inline-flex items-center gap-1.5 text-xs font-mono text-slate/70 dark:text-ivory/60 hover:text-oxblood dark:hover:text-rose transition"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Return to Sign In</span>
                  </Link>
                </div>
              </motion.div>
            )}

            {/* 4. STATE: INVALID / MISSING */}
            {(status === 'invalid' || status === 'missing') && (
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="text-center space-y-5"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-error/10 border border-error/25 text-error mb-1">
                  <ShieldAlert className="w-8 h-8" />
                </div>

                <div>
                  <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                    {status === 'missing' ? 'Verification Token Missing' : 'Invalid or Used Link'}
                  </h2>
                  <p className="text-xs text-slate/70 dark:text-ivory/60 mt-2 font-sans leading-relaxed">
                    {message || 'This verification link is invalid, malformed, or has already been used. If your account is verified, you can sign in directly.'}
                  </p>
                </div>

                {/* Resend Form */}
                <form onSubmit={handleResend} className="space-y-3 font-mono text-left pt-2">
                  <label className="block text-[10px] uppercase font-bold text-slate/60 dark:text-ivory/50">
                    Need a fresh verification link?
                  </label>
                  <div className="relative flex items-center">
                    <Mail className="absolute left-3.5 w-4 h-4 text-slate/40 dark:text-rose/50" />
                    <input
                      type="email"
                      required
                      placeholder="Enter registered email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-white/70 dark:bg-black/25 rounded-xl border border-slate/20 dark:border-rose/20 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                    />
                  </div>

                  {resendFeedback && (
                    <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono">
                      ✓ {resendFeedback}
                    </p>
                  )}
                  {resendError && (
                    <p className="text-[11px] text-error font-mono">
                      ⚠ {resendError}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={resending || resendCooldown > 0}
                    className="w-full min-h-[44px] py-2.5 px-4 rounded-xl font-bold text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition disabled:opacity-50"
                  >
                    {resending ? (
                      <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                    ) : resendCooldown > 0 ? (
                      <span>Resend available in {resendCooldown}s</span>
                    ) : (
                      <span className="flex items-center gap-1.5">
                        <RefreshCw className="w-3.5 h-3.5" />
                        Disptach Verification Link
                      </span>
                    )}
                  </button>
                </form>

                <div className="pt-2 border-t border-slate/15 dark:border-rose/15 flex items-center justify-between text-xs font-mono">
                  <Link
                    to="/auth?mode=login"
                    className="inline-flex items-center gap-1.5 text-slate/70 dark:text-ivory/60 hover:text-oxblood dark:hover:text-rose transition"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </Link>

                  <Link
                    to="/auth?mode=register"
                    className="text-slate/60 dark:text-ivory/50 hover:text-charcoal dark:hover:text-ivory transition text-[11px]"
                  >
                    Create new account
                  </Link>
                </div>
              </motion.div>
            )}

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
