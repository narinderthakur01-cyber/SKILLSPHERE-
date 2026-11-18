import React, { useState, useMemo } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, Check } from 'lucide-react';
import { authAPI } from '../services/api';
import { PageTransition } from '../components/MotionComponents';

export const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  // Password entropy calculation
  const entropyScore = useMemo(() => {
    let score = 0;
    if (!newPassword) return 0;
    if (newPassword.length >= 8) score += 30;
    if (newPassword.length >= 12) score += 20;
    if (/[A-Z]/.test(newPassword)) score += 15;
    if (/[0-9]/.test(newPassword)) score += 15;
    if (/[^A-Za-z0-9]/.test(newPassword)) score += 20;
    return Math.min(score, 100);
  }, [newPassword]);

  const entropyLabel = useMemo(() => {
    if (entropyScore < 40) return { label: 'LOW ENTROPY', color: '#914F51' };
    if (entropyScore < 75) return { label: 'MODERATE CALIBRATION', color: '#C49A62' };
    return { label: 'CRYPTOGRAPHIC GRADE', color: '#829B88' };
  }, [entropyScore]);

  const passwordsMatch = newPassword && confirmPassword && newPassword === confirmPassword;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) {
      setError('Missing password reset token. Please request a new link.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match. Please verify your entries.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters in length.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await authAPI.resetPassword({
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setIsSuccess(true);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to reset password. The link may have expired.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
        <div className="w-full max-w-md space-y-6">
          
          <div className="glass-card p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-2xl relative overflow-hidden bg-white/70 dark:bg-charcoal/80 backdrop-blur-xl">
            
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose mb-4 shadow-sm">
                <Lock className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-display font-extrabold text-charcoal dark:text-ivory tracking-tight">
                Set New Access Password
              </h2>
              <p className="text-xs text-slate/70 dark:text-ivory/60 mt-1.5 font-normal leading-relaxed">
                Configure your new password credentials below to regain account access.
              </p>
            </div>

            {/* Missing Token Warning */}
            {!token && (
              <div className="mb-6 p-4 rounded-xl bg-error/10 border border-error/25 text-error text-xs font-mono">
                <p className="font-bold mb-1">Missing Security Token</p>
                <p className="text-[11px] leading-relaxed">
                  No valid reset token was detected in your URL. Please use the reset link sent to your email or request a new one.
                </p>
                <Link
                  to="/forgot-password"
                  className="mt-3 inline-block font-bold underline hover:opacity-80 transition"
                >
                  Request New Password Reset Link &rarr;
                </Link>
              </div>
            )}

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

            {!isSuccess ? (
              token && (
                <form onSubmit={handleSubmit} className="space-y-4 font-mono">
                  
                  {/* New Password Input */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      New Password Cipher
                    </label>
                    <div className="relative flex items-center">
                      <Lock className="absolute left-3.5 w-4 h-4 text-slate/40 dark:text-rose/50" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        required
                        placeholder="••••••••••••"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full pl-10 pr-11 py-3 bg-white/60 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 p-1 text-slate/40 dark:text-rose/50 hover:text-charcoal dark:hover:text-ivory transition"
                        title={showNewPassword ? 'Hide password' : 'Show password'}
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>

                    {/* Entropy Meter */}
                    {newPassword && (
                      <div className="mt-2 text-[10px]">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-slate/60 dark:text-ivory/50">STRENGTH:</span>
                          <span style={{ color: entropyLabel.color }} className="font-bold">
                            {entropyLabel.label}
                          </span>
                        </div>
                        <div className="w-full bg-slate/10 dark:bg-white/10 h-1 rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all duration-300"
                            style={{
                              width: `${entropyScore}%`,
                              backgroundColor: entropyLabel.color,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Confirm Password Input */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate/80 dark:text-rose uppercase tracking-wider mb-1.5">
                      Confirm New Password
                    </label>
                    <div className="relative flex items-center">
                      <Lock className="absolute left-3.5 w-4 h-4 text-slate/40 dark:text-rose/50" />
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        placeholder="••••••••••••"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full pl-10 pr-11 py-3 bg-white/60 dark:bg-black/20 rounded-xl border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/30 focus:outline-none focus:border-oxblood dark:focus:border-rose transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 p-1 text-slate/40 dark:text-rose/50 hover:text-charcoal dark:hover:text-ivory transition"
                        title={showConfirmPassword ? 'Hide password' : 'Show password'}
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {confirmPassword && (
                      <p className={`mt-1 text-[10px] flex items-center gap-1 ${passwordsMatch ? 'text-success' : 'text-error'}`}>
                        {passwordsMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
                      </p>
                    )}
                  </div>

                  {/* Requirements List */}
                  <div className="p-3 bg-slate/5 dark:bg-white/5 rounded-xl border border-slate/10 dark:border-white/5 space-y-1 text-[10px] text-slate/70 dark:text-ivory/60">
                    <p className={`flex items-center gap-1.5 ${newPassword.length >= 8 ? 'text-success' : ''}`}>
                      <Check className="w-3 h-3" /> Minimum 8 characters
                    </p>
                    <p className={`flex items-center gap-1.5 ${passwordsMatch ? 'text-success' : ''}`}>
                      <Check className="w-3 h-3" /> Password match confirmation
                    </p>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading || !passwordsMatch || newPassword.length < 8}
                    className="w-full mt-2 min-h-[48px] py-3.5 px-4 rounded-xl font-bold font-mono text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md"
                  >
                    {loading ? (
                      <div className="w-4 h-4 border-2 border-ivory/30 border-t-ivory rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Reset Password</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              )
            ) : (
              /* Success State */
              <motion.div
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="space-y-6 text-center"
              >
                <div className="p-5 rounded-2xl bg-success/10 border border-success/25 text-success">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-success" />
                  <h3 className="font-display font-bold text-sm text-charcoal dark:text-ivory mb-1">
                    Password Successfully Updated
                  </h3>
                  <p className="text-xs text-slate/80 dark:text-ivory/80 leading-relaxed font-sans">
                    Your password credentials have been updated securely. You may now authenticate with your new password.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => navigate('/auth')}
                  className="w-full min-h-[48px] py-3.5 px-4 rounded-xl font-bold font-mono text-xs uppercase tracking-wider btn-oxblood flex items-center justify-center gap-2 transition shadow-md"
                >
                  <span>Proceed to Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </motion.div>
            )}

            {/* Back to Login Footer */}
            {!isSuccess && (
              <div className="mt-8 pt-5 border-t border-slate/15 dark:border-rose/15 text-center">
                <Link
                  to="/auth"
                  className="inline-flex items-center gap-2 text-xs font-mono text-slate/70 dark:text-ivory/60 hover:text-oxblood dark:hover:text-rose transition"
                >
                  <span>Return to Sign In</span>
                </Link>
              </div>
            )}

          </div>

        </div>
      </div>
    </PageTransition>
  );
};
