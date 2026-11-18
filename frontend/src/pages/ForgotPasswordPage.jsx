import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import { authAPI } from '../services/api';
import { PageTransition } from '../components/MotionComponents';

export const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [resendSuccess, setResendSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setError('');
    setResendSuccess('');

    try {
      await authAPI.forgotPassword(email.trim());
      setSubmitted(true);
    } catch (err) {
      if (err.response && err.response.status === 429) {
        setError('Too many reset attempts. Please wait a few minutes before trying again.');
      } else {
        // Anti-enumeration: Even on network error, keep user safe
        setSubmitted(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    setResendSuccess('');

    try {
      await authAPI.resendResetEmail(email.trim());
      setResendSuccess('A fresh reset link has been dispatched to your inbox.');
    } catch (err) {
      if (err.response && err.response.status === 429) {
        setError('Rate limit reached. Please wait 15 minutes before requesting another email.');
      } else {
        setResendSuccess('A fresh reset link has been dispatched to your inbox.');
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="w-full max-w-md space-y-6">
          
          {/* Card Container */}
          <div className="glass-card p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-2xl relative overflow-hidden bg-white/70 dark:bg-charcoal/80 backdrop-blur-xl">
            
            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 rounded-full bg-oxblood/10 blur-3xl pointer-events-none" />

            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose mb-4 shadow-sm">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                Reset Account Password
              </h2>
              <p className="text-xs text-slate/70 dark:text-ivory/60 mt-1.5 font-normal leading-relaxed">
                Enter your registered email address and we'll send you a single-use cryptographic reset link.
              </p>
            </div>

            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="mb-6 p-3.5 rounded-xl bg-error/10 border border-error/25 text-error text-xs font-mono flex items-center gap-2.5"
                >
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {!submitted ? (
              /* Request Form */
              <form onSubmit={handleSubmit} className="space-y-5 font-mono">
                <div>
                  <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-2">
                    Registered Email Address
                  </label>
                  <div className="relative flex items-center">
                    <Mail className="absolute left-3.5 w-4 h-4 text-slate/40 dark:text-rose/50" />
                    <input
                      type="email"
                      required
                      placeholder="name@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 bg-white/60 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full min-h-[48px] py-3.5 px-4 rounded-xl font-bold font-mono text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Send Password Reset Link</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            ) : (
              /* Generic Success Screen (Anti-Enumeration Guard) */
              <motion.div
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="space-y-6 text-center"
              >
                <div className="p-4 rounded-2xl bg-success/10 border border-success/25 text-success">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-mono font-bold text-xs">Reset Dispatch Queued</span>
                  </div>
                  <p className="text-[11px] text-slate/80 dark:text-ivory/80 leading-relaxed font-sans">
                    If an active account exists for <strong className="font-mono text-charcoal dark:text-ivory">{email}</strong>, a secure reset link valid for <strong>15 minutes</strong> has been sent to your inbox.
                  </p>
                </div>

                {resendSuccess && (
                  <p className="text-[11px] text-success font-mono">
                    ✓ {resendSuccess}
                  </p>
                )}

                <div className="space-y-3 font-mono">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={resending}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider text-oxblood dark:text-rose border border-oxblood/30 hover:bg-oxblood/10 transition disabled:opacity-50"
                  >
                    {resending ? 'Dispatched...' : 'Resend Reset Email'}
                  </button>

                  <button
                    type="button"
                    onClick={() => { setSubmitted(false); setEmail(''); }}
                    className="text-[11px] text-slate/60 dark:text-ivory/50 hover:text-charcoal dark:hover:text-ivory transition"
                  >
                    Try a different email address
                  </button>
                </div>
              </motion.div>
            )}

            {/* Back to Login Footer */}
            <div className="mt-8 pt-5 border-t border-slate/15 dark:border-rose/15 text-center">
              <Link
                to="/auth"
                className="inline-flex items-center gap-2 text-xs font-mono text-slate/70 dark:text-ivory/60 hover:text-oxblood dark:hover:text-rose transition"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Authentication Gateway</span>
              </Link>
            </div>

          </div>

          {/* Security Telemetry Badge */}
          <div className="text-center text-[10px] font-mono text-slate/50 dark:text-ivory/40">
            <span>PROTECTED BY 256-BIT CRYPTOGRAPHIC RESET TOKENS</span>
          </div>

        </div>
      </div>
    </PageTransition>
  );
};
