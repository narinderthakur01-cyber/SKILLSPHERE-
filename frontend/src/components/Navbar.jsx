import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { notificationsAPI } from '../services/api';
import {
  Briefcase, User, LogOut, Menu, X, ShieldCheck, Sun, Moon,
  FileText, Users, Building, Layers, Sparkles, Bell, Bookmark,
  Calendar, MessageSquare, History, CheckCheck, Clock
} from 'lucide-react';
import axios from 'axios';

export const Navbar = () => {
  const { user, role, logout } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const notifRef = useRef(null);

  // Close mobile menu & notifications on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setNotifOpen(false);
  }, [location.pathname, location.search]);

  // Click outside to close notification dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch notifications for authenticated user
  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const res = await notificationsAPI.list();
      setNotifications(res.data || []);
    } catch {
      // Ignore background notification fetch errors
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 20000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await notificationsAPI.markRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch (e) {
        console.error(e);
      }
    }
    setNotifOpen(false);
    if (notif.link) {
      navigate(notif.link);
    }
  };

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setMobileMenuOpen(false);
        setNotifOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await axios.get('/health', { timeout: 3000 });
        if (isMounted && res.data?.status === 'healthy') {
          setBackendHealthy(true);
        } else if (isMounted) {
          setBackendHealthy(false);
        }
      } catch {
        if (isMounted) setBackendHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
    setMobileMenuOpen(false);
  };

  const getNavItems = () => {
    if (!user) {
      return [{ path: '/', label: 'Overview', active: location.pathname === '/' }];
    }
    if (role === 'JOB_SEEKER') {
      const search = location.search;
      return [
        {
          path: '/dashboard?tab=jobs',
          label: 'Browse Jobs',
          active: location.pathname === '/dashboard' && (!search || search.includes('tab=jobs')),
        },
        {
          path: '/dashboard?tab=saved',
          label: 'Saved Jobs',
          active: location.pathname === '/dashboard' && search.includes('tab=saved'),
        },
        {
          path: '/dashboard?tab=applications',
          label: 'Applications',
          active: location.pathname === '/dashboard' && search.includes('tab=applications'),
        },
        {
          path: '/dashboard?tab=assessments',
          label: 'Assessments',
          active: location.pathname === '/dashboard' && search.includes('tab=assessments'),
        },
        {
          path: '/dashboard?tab=interviews',
          label: 'Interviews',
          active: location.pathname === '/dashboard' && search.includes('tab=interviews'),
        },
        {
          path: '/dashboard?tab=messages',
          label: 'Messages',
          active: location.pathname === '/dashboard' && search.includes('tab=messages'),
        },
        {
          path: '/dashboard?tab=resumes',
          label: 'OCR & Intelligence',
          active: location.pathname === '/dashboard' && search.includes('tab=resumes'),
        },
        {
          path: '/assistant',
          label: 'Assistant',
          active: location.pathname === '/assistant',
        },
      ];
    }
    if (role === 'RECRUITER') {
      const search = location.search;
      return [
        {
          path: '/recruiter?tab=jobs',
          label: 'Openings',
          active: location.pathname === '/recruiter' && (!search || search.includes('tab=jobs')),
        },
        {
          path: '/recruiter?tab=pipeline',
          label: 'Pipeline (Kanban)',
          active: location.pathname === '/recruiter' && search.includes('tab=pipeline'),
        },
        {
          path: '/recruiter?tab=assessments',
          label: 'Assessments',
          active: location.pathname === '/recruiter' && search.includes('tab=assessments'),
        },
        {
          path: '/recruiter?tab=interviews',
          label: 'Interviews',
          active: location.pathname === '/recruiter' && search.includes('tab=interviews'),
        },
        {
          path: '/recruiter?tab=messages',
          label: 'Messages',
          active: location.pathname === '/recruiter' && search.includes('tab=messages'),
        },
        {
          path: '/recruiter?tab=company',
          label: 'Company',
          active: location.pathname === '/recruiter' && search.includes('tab=company'),
        },
        {
          path: '/assistant',
          label: 'Assistant',
          active: location.pathname === '/assistant',
        },
      ];
    }
    if (role === 'ADMIN') {
      const search = location.search;
      return [
        {
          path: '/admin?tab=analytics',
          label: 'Intelligence',
          active: location.pathname === '/admin' && (!search || search.includes('tab=analytics')),
        },
        {
          path: '/admin?tab=users',
          label: 'Users',
          active: location.pathname === '/admin' && search.includes('tab=users'),
        },
        {
          path: '/admin?tab=jobs',
          label: 'Moderation',
          active: location.pathname === '/admin' && search.includes('tab=jobs'),
        },
        {
          path: '/admin?tab=audit',
          label: 'Audit Logs',
          active: location.pathname === '/admin' && search.includes('tab=audit'),
        },
        {
          path: '/admin?tab=question_bank',
          label: 'Question Bank',
          active: location.pathname === '/admin' && search.includes('tab=question_bank'),
        },
        {
          path: '/assistant',
          label: 'Assistant',
          active: location.pathname === '/assistant',
        },
      ];
    }
    return [];
  };

  const navItems = getNavItems();

  return (
    <header className="sticky top-0 z-40 w-full transition-colors duration-300 backdrop-blur-xl bg-ivory/85 dark:bg-charcoal/85 border-b border-slate/10 dark:border-rose/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 sm:h-20">
          
          {/* Brand Logo & Live Engine Status */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal flex items-center justify-center font-display font-black text-lg transition-transform duration-300 group-hover:scale-105 shadow-md ring-1 ring-oxblood/30">
                <span className="text-oxblood dark:text-oxblood font-extrabold">S</span>
              </div>
              <div className="flex flex-col">
                <span className="font-display font-bold text-lg sm:text-xl tracking-tight text-charcoal dark:text-ivory">
                  Skill<span className="text-oxblood">Sphere</span>
                </span>
                <span className="text-[9px] font-mono tracking-widest text-slate/70 dark:text-rose/80 uppercase -mt-0.5">
                  ATS & Intelligence
                </span>
              </div>
            </Link>

            {/* Live Health Badge */}
            {backendHealthy && (
              <div className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-success text-[10px] font-mono font-medium tracking-wide">
                <span className="w-1.5 h-1.5 rounded-full bg-[#829B88] animate-pulse"></span>
                <span>SYSTEM ACTIVE</span>
              </div>
            )}
          </div>

          {/* Desktop Navigation Links with Animated Indicator */}
          <nav className="hidden lg:flex items-center gap-1 p-1 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5" aria-label="Main Navigation">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-3.5 py-2 rounded-xl text-xs font-mono font-semibold uppercase tracking-wider transition-colors duration-200 ${
                  item.active
                    ? 'text-ivory'
                    : 'text-slate/80 dark:text-ivory/70 hover:text-oxblood dark:hover:text-rose'
                }`}
              >
                {item.active && (
                  <motion.span
                    layoutId="navbarActiveIndicator"
                    className="absolute inset-0 rounded-xl bg-oxblood shadow-sm"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Desktop Controls: Notifications, Theme Toggle, User Profile */}
          <div className="hidden md:flex items-center gap-2.5">
            {/* Notification Bell with Badge & Dropdown */}
            {user && (
              <div className="relative" ref={notifRef}>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.92 }}
                  onClick={() => setNotifOpen(!notifOpen)}
                  aria-label="View notifications"
                  title="Notifications"
                  className="relative w-10 h-10 rounded-xl border border-slate/15 dark:border-rose/20 bg-white/60 dark:bg-slate/40 text-charcoal dark:text-ivory hover:border-oxblood/40 transition shadow-xs flex items-center justify-center min-h-[44px] min-w-[44px]"
                >
                  <Bell className="w-4 h-4 text-charcoal/80 dark:text-ivory/80" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-oxblood text-ivory text-[10px] font-mono font-bold rounded-full flex items-center justify-center shadow-sm">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </motion.button>

                {/* Notification Dropdown Panel */}
                <AnimatePresence>
                  {notifOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.96 }}
                      transition={{ duration: 0.2 }}
                      className="absolute right-0 mt-2 w-80 sm:w-96 glass-surface-elevated rounded-2xl border border-slate/15 dark:border-rose/20 shadow-2xl p-4 z-50 text-xs font-sans"
                    >
                      <div className="flex items-center justify-between pb-3 border-b border-slate/10 dark:border-rose/10 mb-2">
                        <div className="flex items-center gap-2">
                          <Bell className="w-4 h-4 text-oxblood" />
                          <span className="font-display font-bold text-sm text-charcoal dark:text-ivory">
                            Notifications
                          </span>
                          {unreadCount > 0 && (
                            <span className="badge-oxblood text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">
                              {unreadCount} new
                            </span>
                          )}
                        </div>
                        {unreadCount > 0 && (
                          <button
                            onClick={handleMarkAllRead}
                            className="text-[11px] font-mono font-bold text-oxblood dark:text-rose hover:underline flex items-center gap-1"
                          >
                            <CheckCheck className="w-3.5 h-3.5" />
                            <span>Mark all read</span>
                          </button>
                        )}
                      </div>

                      <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
                        {notifications.length === 0 ? (
                          <div className="py-8 text-center text-slate/50 dark:text-ivory/50 font-mono text-xs">
                            No notifications yet.
                          </div>
                        ) : (
                          notifications.slice(0, 10).map((n) => (
                            <div
                              key={n.id}
                              onClick={() => handleNotificationClick(n)}
                              className={`p-3 rounded-xl cursor-pointer transition flex items-start gap-2.5 ${
                                !n.is_read
                                  ? 'bg-oxblood/10 border border-oxblood/20'
                                  : 'hover:bg-slate/5 dark:hover:bg-white/5'
                              }`}
                            >
                              <div className="w-2 h-2 rounded-full bg-oxblood shrink-0 mt-1.5 opacity-80" />
                              <div className="flex-1 min-w-0">
                                <p className="font-display font-bold text-xs text-charcoal dark:text-ivory leading-tight">
                                  {n.title}
                                </p>
                                <p className="text-[11px] text-slate/75 dark:text-ivory/70 mt-0.5 line-clamp-2">
                                  {n.message}
                                </p>
                                <span className="text-[9px] font-mono text-slate/50 dark:text-ivory/50 mt-1 block">
                                  {new Date(n.created_at).toLocaleDateString()} at{' '}
                                  {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Theme Toggle Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.92 }}
              onClick={toggleTheme}
              aria-label="Toggle visual theme"
              title={isDark ? "Switch to light theme" : "Switch to dark theme"}
              className="w-10 h-10 rounded-xl border border-slate/15 dark:border-rose/20 bg-white/60 dark:bg-slate/40 text-charcoal dark:text-ivory hover:border-oxblood/40 transition shadow-xs flex items-center justify-center shrink-0 min-h-[44px] min-w-[44px]"
            >
              {isDark ? (
                <Sun className="w-4 h-4 text-rose" />
              ) : (
                <Moon className="w-4 h-4 text-oxblood" />
              )}
            </motion.button>

            {user ? (
              <div className="flex items-center gap-2.5 pl-2.5 border-l border-slate/15 dark:border-rose/15">
                <div className="text-right">
                  <span className="font-display font-semibold text-xs text-charcoal dark:text-ivory block leading-tight">
                    {user.name}
                  </span>
                  <span className="text-[10px] font-mono text-oxblood dark:text-rose font-medium block">
                    {user.role}
                  </span>
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleLogout}
                  title="Sign out"
                  className="w-10 h-10 rounded-xl border border-slate/15 dark:border-rose/20 bg-white/40 dark:bg-slate/40 text-slate/70 dark:text-ivory/70 hover:text-red-500 hover:border-red-500/30 transition flex items-center justify-center shrink-0 min-h-[44px] min-w-[44px]"
                >
                  <LogOut className="w-4 h-4" />
                </motion.button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/auth"
                  className="px-4 py-2 text-xs font-mono font-bold uppercase tracking-wider text-charcoal dark:text-ivory hover:text-oxblood transition min-h-[44px] flex items-center"
                >
                  Sign In
                </Link>
                <Link
                  to="/auth?mode=register"
                  className="px-4 py-2 btn-oxblood text-xs font-mono font-bold uppercase tracking-wider rounded-xl shadow-xs min-h-[44px] flex items-center"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Actions: Theme Toggle, Notifications & Menu Toggle (>= 44px) */}
          <div className="flex items-center gap-2 md:hidden">
            {user && (
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative w-11 h-11 rounded-xl border border-slate/15 dark:border-rose/20 flex items-center justify-center min-h-[44px] min-w-[44px]"
                aria-label="Notifications"
              >
                <Bell className="w-4 h-4 text-charcoal dark:text-ivory" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-oxblood" />
                )}
              </button>
            )}

            <button
              onClick={toggleTheme}
              aria-label="Toggle visual theme"
              className="w-11 h-11 rounded-xl border border-slate/15 dark:border-rose/20 flex items-center justify-center min-h-[44px] min-w-[44px]"
            >
              {isDark ? <Sun className="w-4 h-4 text-rose" /> : <Moon className="w-4 h-4 text-oxblood" />}
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              className="w-11 h-11 rounded-xl border border-slate/15 dark:border-rose/20 bg-slate/5 dark:bg-white/5 flex items-center justify-center text-charcoal dark:text-ivory min-h-[44px] min-w-[44px]"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-slate/10 dark:border-rose/10 bg-ivory/95 dark:bg-charcoal/95 backdrop-blur-2xl px-4 py-5 space-y-3"
          >
            {user && (
              <div className="p-3.5 rounded-2xl bg-oxblood/10 border border-oxblood/20 flex items-center justify-between">
                <div>
                  <p className="font-display font-bold text-sm text-charcoal dark:text-ivory">{user.name}</p>
                  <p className="font-mono text-[11px] text-oxblood dark:text-rose">{user.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-xs font-mono font-bold text-red-500 rounded-xl hover:bg-red-500/10 min-h-[44px] min-w-[44px] flex items-center justify-center"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}

            <div className="space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block py-3 px-4 rounded-xl text-xs font-mono font-bold uppercase tracking-wider min-h-[44px] flex items-center ${
                    item.active
                      ? 'bg-oxblood text-ivory shadow-xs'
                      : 'text-charcoal/80 dark:text-ivory/80 hover:bg-slate/10 dark:hover:bg-white/10'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            {!user && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate/10 dark:border-rose/10">
                <Link
                  to="/auth"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-3 text-center btn-secondary rounded-xl text-xs font-mono font-bold uppercase min-h-[44px] flex items-center justify-center"
                >
                  Sign In
                </Link>
                <Link
                  to="/auth?mode=register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-3 text-center btn-oxblood rounded-xl text-xs font-mono font-bold uppercase min-h-[44px] flex items-center justify-center"
                >
                  Get Started
                </Link>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};
