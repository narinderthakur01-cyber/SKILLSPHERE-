import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { notificationsAPI } from '../services/api';
import {
  Briefcase, User, LogOut, Menu, X, ShieldCheck, Sun, Moon,
  FileText, Users, Building, Layers, Sparkles, Bell, Bookmark,
  Calendar, MessageSquare, History, CheckCheck, Clock, LifeBuoy,
  Terminal, Award, Video, Film, Upload, Activity, Database, Eye,
  BarChart3, Bot, ChevronRight, ArrowRight, Sparkle
} from 'lucide-react';
import axios from 'axios';

/**
 * SkillSphere Immersive Full-Screen Navigation & Topbar
 * Inspired by 21st.dev (@hyperiux/components/immersive-full-screen-nav)
 * and Watermelon UI (Agndex Dashboard architecture)
 *
 * Features:
 * - 3-bar hamburger navigation trigger visible across all breakpoints
 * - Circular clip-path expansion reveal from the hamburger trigger coordinates
 * - Staggered category and link reveal animations
 * - Complete role coverage: Candidate (12 tabs), Recruiter (10 tabs), Admin (8 tabs) + Assistant
 * - Esc key closing, scroll locking (body & html), backdrop dismiss
 * - Zero permanent vertical sidebars: 100% full-width dashboard content area
 * - Preserves deep link URL query params and active tab states
 */
export const Navbar = () => {
  const { user, role, logout } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const notifRef = useRef(null);

  // Close immersive menu and notifications on route/search change
  useEffect(() => {
    setDrawerOpen(false);
    setNotifOpen(false);
  }, [location.pathname, location.search]);

  // Lock body & html scroll when immersive nav is open
  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, [drawerOpen]);

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

  // Close drawer & notifications on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setDrawerOpen(false);
        setNotifOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
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

  // Backend health heartbeat check
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
    setDrawerOpen(false);
  };

  // Role-specific navigation groups containing ALL dashboard destinations
  const getNavigationGroups = () => {
    const search = location.search;

    if (!user) {
      return [
        {
          title: 'Explore SkillSphere',
          tagline: 'AI-Native Technical Hiring & Candidate Passport',
          items: [
            { path: '/', label: 'Platform Overview', desc: 'Experience the AI-native workspace', icon: Layers, active: location.pathname === '/' },
            { path: '/auth', label: 'Sign In', desc: 'Access your candidate or recruiter dashboard', icon: User, active: location.pathname === '/auth' && !search.includes('mode=register') },
            { path: '/auth?mode=register', label: 'Create Account', desc: 'Join as a Candidate or Hiring Team', icon: Sparkles, active: location.pathname === '/auth' && search.includes('mode=register') },
          ]
        }
      ];
    }

    if (role === 'JOB_SEEKER') {
      return [
        {
          title: 'Career & Applications',
          tagline: 'Curated roles & application tracking',
          items: [
            {
              path: '/dashboard?tab=jobs',
              label: 'Browse Jobs',
              desc: 'AI-matched job opportunities',
              icon: Briefcase,
              active: location.pathname === '/dashboard' && (!search || search.includes('tab=jobs')),
            },
            {
              path: '/dashboard?tab=saved',
              label: 'Saved Jobs',
              desc: 'Bookmarked postings for later',
              icon: Bookmark,
              active: location.pathname === '/dashboard' && search.includes('tab=saved'),
            },
            {
              path: '/dashboard?tab=applications',
              label: 'My Applications',
              desc: 'Active hiring pipeline stages',
              icon: FileText,
              active: location.pathname === '/dashboard' && search.includes('tab=applications'),
            },
            {
              path: '/dashboard?tab=profile',
              label: 'Candidate Passport',
              desc: 'Skill verification & profile telemetry',
              icon: User,
              active: location.pathname === '/dashboard' && search.includes('tab=profile'),
            },
          ]
        },
        {
          title: 'Assessments & Technical',
          tagline: 'Skill verification & interactive evaluations',
          items: [
            {
              path: '/dashboard?tab=assessments',
              label: 'First-Round Assessments',
              desc: 'Automated MCQ & coding tests',
              icon: Award,
              active: location.pathname === '/dashboard' && search.includes('tab=assessments'),
            },
            {
              path: '/dashboard?tab=video-assessments',
              label: 'Video Assessments',
              desc: 'Asynchronous prompt responses',
              icon: Video,
              active: location.pathname === '/dashboard' && search.includes('tab=video-assessments'),
            },
            {
              path: '/dashboard?tab=practice',
              label: 'Tech Practice & Drills',
              desc: 'Self-guided technical sandbox',
              icon: Terminal,
              active: location.pathname === '/dashboard' && search.includes('tab=practice'),
            },
            {
              path: '/dashboard?tab=media',
              label: 'My Media Library',
              desc: 'Recorded answers & code submissions',
              icon: Film,
              active: location.pathname === '/dashboard' && search.includes('tab=media'),
            },
            {
              path: '/dashboard?tab=interviews',
              label: 'Live WebRTC Interviews',
              desc: 'Real-time video & collaborative room',
              icon: Calendar,
              active: location.pathname === '/dashboard' && search.includes('tab=interviews'),
            },
          ]
        },
        {
          title: 'Intelligence & Support',
          tagline: 'AI resume analysis & real-time messaging',
          items: [
            {
              path: '/dashboard?tab=resumes',
              label: 'OCR & AI Intel',
              desc: 'Automated resume parsing & score',
              icon: Upload,
              active: location.pathname === '/dashboard' && search.includes('tab=resumes'),
            },
            {
              path: '/dashboard?tab=messages',
              label: 'Direct Messaging',
              desc: 'Chat directly with recruiters',
              icon: MessageSquare,
              active: location.pathname === '/dashboard' && search.includes('tab=messages'),
            },
            {
              path: '/dashboard?tab=tickets',
              label: 'Support Tickets',
              desc: 'Human agent escalation & help',
              icon: LifeBuoy,
              active: location.pathname === '/dashboard' && search.includes('tab=tickets'),
            },
            {
              path: '/assistant',
              label: 'SkillSphere Assistant',
              desc: 'AI copilot & conversational career advisor',
              icon: Bot,
              active: location.pathname === '/assistant',
            },
          ]
        }
      ];
    }

    if (role === 'RECRUITER') {
      return [
        {
          title: 'Hiring & Postings',
          tagline: 'Manage pipelines & published listings',
          items: [
            {
              path: '/recruiter?tab=jobs',
              label: 'Manage Openings',
              desc: 'Create and publish job listings',
              icon: Briefcase,
              active: location.pathname === '/recruiter' && (!search || search.includes('tab=jobs')),
            },
            {
              path: '/recruiter?tab=pipeline',
              label: 'Pipeline (Kanban)',
              desc: 'Drag-and-drop applicant tracker',
              icon: Users,
              active: location.pathname === '/recruiter' && search.includes('tab=pipeline'),
            },
            {
              path: '/recruiter?tab=company',
              label: 'Company Profile',
              desc: 'Branding, benefits & organization',
              icon: Building,
              active: location.pathname === '/recruiter' && search.includes('tab=company'),
            },
          ]
        },
        {
          title: 'Interviews & Evaluations',
          tagline: 'Proctored assessments & live meetings',
          items: [
            {
              path: '/recruiter?tab=assessments',
              label: 'First-Round Assessments',
              desc: 'Evaluate candidate test scores',
              icon: Award,
              active: location.pathname === '/recruiter' && search.includes('tab=assessments'),
            },
            {
              path: '/recruiter?tab=video-assessments',
              label: 'Video Assessments',
              desc: 'Review recorded candidate answers',
              icon: Video,
              active: location.pathname === '/recruiter' && search.includes('tab=video-assessments'),
            },
            {
              path: '/recruiter?tab=interviews',
              label: 'Live WebRTC Interviews',
              desc: 'Conduct face-to-face evaluations',
              icon: Calendar,
              active: location.pathname === '/recruiter' && search.includes('tab=interviews'),
            },
            {
              path: '/recruiter?tab=media',
              label: 'Media Library',
              desc: 'Review submissions & recordings',
              icon: Film,
              active: location.pathname === '/recruiter' && search.includes('tab=media'),
            },
          ]
        },
        {
          title: 'Analytics & Support',
          tagline: 'Hiring metrics & communication',
          items: [
            {
              path: '/recruiter?tab=analytics',
              label: 'Recruitment Analytics',
              desc: 'Funnel throughput & conversion rates',
              icon: BarChart3,
              active: location.pathname === '/recruiter' && search.includes('tab=analytics'),
            },
            {
              path: '/recruiter?tab=messages',
              label: 'Direct Messaging',
              desc: 'Direct communication with applicants',
              icon: MessageSquare,
              active: location.pathname === '/recruiter' && search.includes('tab=messages'),
            },
            {
              path: '/recruiter?tab=tickets',
              label: 'Support Tickets',
              desc: 'Help desk & platform inquiries',
              icon: LifeBuoy,
              active: location.pathname === '/recruiter' && search.includes('tab=tickets'),
            },
            {
              path: '/assistant',
              label: 'SkillSphere Assistant',
              desc: 'AI copilot for job descriptions & evaluations',
              icon: Bot,
              active: location.pathname === '/assistant',
            },
          ]
        }
      ];
    }

    if (role === 'ADMIN') {
      return [
        {
          title: 'Platform Intelligence & Users',
          tagline: 'System overview & account management',
          items: [
            {
              path: '/admin?tab=analytics',
              label: 'Platform Intelligence',
              desc: 'Global throughput & system telemetry',
              icon: Activity,
              active: location.pathname === '/admin' && (!search || search.includes('tab=analytics')),
            },
            {
              path: '/admin?tab=users',
              label: 'User Governance',
              desc: 'Manage roles, permissions & statuses',
              icon: Users,
              active: location.pathname === '/admin' && search.includes('tab=users'),
            },
            {
              path: '/admin?tab=jobs',
              label: 'Job Moderation',
              desc: 'Content safety & quality control',
              icon: Briefcase,
              active: location.pathname === '/admin' && search.includes('tab=jobs'),
            },
          ]
        },
        {
          title: 'Security, Proctoring & Logs',
          tagline: 'Fraud prevention & system audits',
          items: [
            {
              path: '/admin?tab=activity',
              label: 'System Event Stream',
              desc: 'Live operational logging',
              icon: Clock,
              active: location.pathname === '/admin' && search.includes('tab=activity'),
            },
            {
              path: '/admin?tab=audit',
              label: 'Audit Logs & Governance',
              desc: 'Immutable security & admin changes',
              icon: ShieldCheck,
              active: location.pathname === '/admin' && search.includes('tab=audit'),
            },
            {
              path: '/admin?tab=proctoring',
              label: 'Assessment Proctoring',
              desc: 'AI anti-cheating & behavioral flags',
              icon: Eye,
              active: location.pathname === '/admin' && search.includes('tab=proctoring'),
            },
          ]
        },
        {
          title: 'Questions, Tickets & Assistant',
          tagline: 'Item banking & user escalations',
          items: [
            {
              path: '/admin?tab=question_bank',
              label: 'Question Bank & Import',
              desc: 'Curate technical assessment items',
              icon: Database,
              active: location.pathname === '/admin' && search.includes('tab=question_bank'),
            },
            {
              path: '/admin?tab=tickets',
              label: 'Support Tickets (Handoff)',
              desc: 'Live human agent resolution queue',
              icon: LifeBuoy,
              active: location.pathname === '/admin' && search.includes('tab=tickets'),
            },
            {
              path: '/assistant',
              label: 'SkillSphere Assistant',
              desc: 'AI system copilot & governance tools',
              icon: Bot,
              active: location.pathname === '/assistant',
            },
          ]
        }
      ];
    }

    return [];
  };

  const navGroups = getNavigationGroups();

  // Get current page section context for Topbar breadcrumb
  const getCurrentSectionTitle = () => {
    if (!user) return 'Overview';
    if (role === 'JOB_SEEKER') return 'Candidate Workspace';
    if (role === 'RECRUITER') return 'Recruiter Command Center';
    if (role === 'ADMIN') return 'Platform Governance';
    return 'Dashboard';
  };

  // 21st.dev Immersive Reveal Animation Variants
  const overlayVariants = {
    closed: {
      clipPath: 'circle(0% at 36px 36px)',
      opacity: 0,
      transition: {
        duration: 0.45,
        ease: [0.77, 0, 0.175, 1],
      },
    },
    open: {
      clipPath: 'circle(150% at 36px 36px)',
      opacity: 1,
      transition: {
        duration: 0.65,
        ease: [0.77, 0, 0.175, 1],
        when: 'beforeChildren',
        staggerChildren: 0.06,
      },
    },
  };

  const itemGroupVariants = {
    closed: { opacity: 0, y: 16 },
    open: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, ease: 'easeOut' },
    },
  };

  return (
    <>
      {/* ===================================================================== */}
      {/* WATERMELON-INSPIRED TOPBAR                                            */}
      {/* Minimalist, spacious, unified across all screen sizes                  */}
      {/* ===================================================================== */}
      <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-ivory/90 dark:bg-[#131115]/90 border-b border-slate-200/50 dark:border-white/10 transition-colors duration-300">
        <div className="w-full max-w-[1520px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 sm:h-20">

            {/* Left: 3-Bar Hamburger Trigger & Brand Context */}
            <div className="flex items-center gap-3 sm:gap-4">
              {/* Universal 3-Bar Hamburger Button */}
              <button
                type="button"
                onClick={() => setDrawerOpen(true)}
                aria-label="Open Navigation Menu"
                title="Navigation Menu (Esc to close)"
                className="w-11 h-11 rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white/60 dark:bg-white/5 hover:border-oxblood/40 dark:hover:border-rose/40 hover:bg-slate-100/80 dark:hover:bg-white/10 text-charcoal dark:text-ivory transition-all flex flex-col items-center justify-center gap-1.5 min-h-[44px] min-w-[44px] shadow-xs active:scale-95 group cursor-pointer"
              >
                <span className="w-5 h-0.5 rounded-full bg-charcoal dark:bg-ivory group-hover:bg-oxblood dark:group-hover:bg-rose transition-all group-hover:w-6" />
                <span className="w-5 h-0.5 rounded-full bg-charcoal dark:bg-ivory group-hover:bg-oxblood dark:group-hover:bg-rose transition-all" />
                <span className="w-5 h-0.5 rounded-full bg-charcoal dark:bg-ivory group-hover:bg-oxblood dark:group-hover:bg-rose transition-all group-hover:w-4" />
              </button>

              {/* Brand Logo & Editorial Title */}
              <Link to="/" className="flex items-center gap-2.5 group">
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-charcoal dark:bg-ivory text-ivory dark:text-charcoal flex items-center justify-center font-display font-black text-lg transition-transform duration-300 group-hover:scale-105 shadow-md ring-1 ring-oxblood/30">
                  <span className="text-oxblood dark:text-oxblood font-extrabold">S</span>
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="font-display font-bold text-base sm:text-lg tracking-tight text-charcoal dark:text-ivory leading-none">
                      Skill<span className="text-oxblood">Sphere</span>
                    </span>
                    <span className="hidden sm:inline-block text-slate-300 dark:text-white/20 font-mono text-xs">/</span>
                    <span className="hidden sm:inline-block text-xs font-mono font-semibold text-slate-600 dark:text-rose/90 tracking-wide">
                      {getCurrentSectionTitle()}
                    </span>
                  </div>
                  <span className="text-[9px] font-mono tracking-widest text-slate-500 dark:text-rose/70 uppercase mt-0.5">
                    ATS & Intelligence
                  </span>
                </div>
              </Link>

              {/* System Active Telemetry Badge */}
              {backendHealthy && (
                <div className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full badge-success text-[10px] font-mono font-medium tracking-wide">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#829B88] animate-pulse" />
                  <span>SYSTEM ACTIVE</span>
                </div>
              )}
            </div>

            {/* Right: Quick Controls (Theme Toggle, Notifications, User) */}
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Notification Bell with Badge & Dropdown */}
              {user && (
                <div className="relative" ref={notifRef}>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.92 }}
                    onClick={() => setNotifOpen(!notifOpen)}
                    aria-label="View notifications"
                    title="Notifications"
                    className="relative w-11 h-11 rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white/60 dark:bg-white/5 text-charcoal dark:text-ivory hover:border-oxblood/40 transition shadow-xs flex items-center justify-center min-h-[44px] min-w-[44px]"
                  >
                    <Bell className="w-4 h-4 text-charcoal/80 dark:text-ivory/80" />
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 w-5 h-5 bg-oxblood text-white text-[10px] font-mono font-bold rounded-full flex items-center justify-center shadow-sm">
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
                        className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl border border-slate-200 dark:border-white/15 bg-white/95 dark:bg-[#18161B]/95 backdrop-blur-2xl shadow-2xl p-4 z-50 text-xs font-sans"
                      >
                        <div className="flex items-center justify-between pb-3 border-b border-slate-200/60 dark:border-white/10 mb-2">
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
                              <span>Mark read</span>
                            </button>
                          )}
                        </div>

                        <div className="max-h-72 overflow-y-auto space-y-1.5 scrollbar-thin">
                          {notifications.length === 0 ? (
                            <div className="text-center py-6 text-slate-400 dark:text-rose/60 font-mono">
                              No notifications yet
                            </div>
                          ) : (
                            notifications.map((n) => (
                              <div
                                key={n.id}
                                onClick={() => handleNotificationClick(n)}
                                className={`p-3 rounded-xl transition cursor-pointer flex items-start gap-2.5 ${
                                  n.is_read
                                    ? 'bg-transparent hover:bg-slate-100/60 dark:hover:bg-white/5 opacity-70'
                                    : 'bg-oxblood/5 dark:bg-rose/10 border border-oxblood/10 hover:bg-oxblood/10'
                                }`}
                              >
                                <div className="mt-0.5 shrink-0">
                                  {!n.is_read && <span className="w-2 h-2 rounded-full bg-oxblood inline-block" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-bold text-charcoal dark:text-ivory leading-tight truncate">
                                    {n.title}
                                  </p>
                                  <p className="text-slate-600 dark:text-slate-300 text-[11px] mt-0.5 leading-snug line-clamp-2">
                                    {n.message}
                                  </p>
                                  <span className="text-[9px] font-mono text-slate-400 mt-1 block">
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
              <button
                onClick={toggleTheme}
                aria-label="Toggle visual theme"
                className="w-11 h-11 rounded-2xl border border-slate-200/80 dark:border-white/10 bg-white/60 dark:bg-white/5 text-charcoal dark:text-ivory hover:border-oxblood/40 transition shadow-xs flex items-center justify-center min-h-[44px] min-w-[44px]"
              >
                {isDark ? <Sun className="w-4 h-4 text-rose" /> : <Moon className="w-4 h-4 text-oxblood" />}
              </button>

              {/* User Profile Action */}
              {user ? (
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200/60 dark:border-white/10">
                  <div className="hidden md:block text-right">
                    <span className="font-display font-semibold text-xs text-charcoal dark:text-ivory block leading-tight">
                      {user.name}
                    </span>
                    <span className="text-[10px] font-mono text-oxblood dark:text-rose font-medium block">
                      {user.role}
                    </span>
                  </div>
                  <button
                    onClick={() => setDrawerOpen(true)}
                    title="Open Navigation Menu"
                    className="w-11 h-11 rounded-2xl bg-gradient-to-br from-oxblood to-oxblood-600 text-white font-mono font-bold text-xs flex items-center justify-center shadow-md liquid-metal-pill cursor-pointer"
                  >
                    {user.name?.[0]?.toUpperCase() || 'U'}
                  </button>
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

          </div>
        </div>
      </header>

      {/* ===================================================================== */}
      {/* 21ST.DEV IMMERSIVE FULL SCREEN NAVIGATION OVERLAY                     */}
      {/* Circular clip-path expansion, editorial grid, role-specific tabs       */}
      {/* ===================================================================== */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            initial="closed"
            animate="open"
            exit="closed"
            variants={overlayVariants}
            className={`fixed inset-0 z-50 flex flex-col justify-between backdrop-blur-3xl overflow-hidden w-full max-w-full overflow-x-hidden ${
              isDark ? 'bg-[#0B0A0D]/98 text-white' : 'bg-[#FAF6F2]/98 text-charcoal'
            }`}
            role="dialog"
            aria-modal="true"
            aria-label="SkillSphere Immersive Navigation"
          >
            {/* Ambient lighting behind nav */}
            <div
              className="absolute inset-0 pointer-events-none opacity-40"
              style={{
                backgroundImage: isDark
                  ? 'radial-gradient(circle at 15% 15%, rgba(145, 79, 81, 0.25) 0%, transparent 45%), radial-gradient(circle at 85% 75%, rgba(64, 180, 220, 0.12) 0%, transparent 45%)'
                  : 'radial-gradient(circle at 15% 15%, rgba(145, 79, 81, 0.14) 0%, transparent 45%), radial-gradient(circle at 85% 75%, rgba(80, 140, 180, 0.10) 0%, transparent 45%)'
              }}
            />

            {/* Immersive Top Bar: Brand, Role Badge & Escape Action */}
            <div className={`relative z-10 w-full max-w-[1520px] mx-auto px-4 sm:px-6 lg:px-8 pt-4 sm:pt-6 pb-3 sm:pb-4 flex items-center justify-between border-b gap-2 ${
              isDark ? 'border-white/10' : 'border-slate-300/80'
            }`}>
              <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-oxblood text-white flex items-center justify-center font-display font-black text-lg sm:text-xl shadow-lg ring-1 ring-white/20 shrink-0">
                  <span>S</span>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 sm:gap-2">
                    <span className={`font-display font-bold text-base sm:text-lg tracking-tight truncate ${
                      isDark ? 'text-white' : 'text-charcoal'
                    }`}>
                      Skill<span className="text-oxblood dark:text-rose">Sphere</span>
                    </span>
                    <span className={`hidden sm:inline-block font-mono text-xs ${isDark ? 'text-white/20' : 'text-slate-400'}`}>/</span>
                    <span className="hidden sm:inline-block text-xs font-mono font-semibold text-oxblood dark:text-rose uppercase tracking-wider truncate">
                      {user ? `${user.role} Navigation` : 'Navigation'}
                    </span>
                  </div>
                  <p className={`hidden sm:block text-[10px] font-mono mt-0.5 truncate ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Select a section or press <kbd className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${isDark ? 'bg-white/10 text-white/90 border border-white/15' : 'bg-slate-200 text-charcoal border border-slate-300'}`}>ESC</kbd> to return
                  </p>
                </div>
              </div>

              {/* Close Button & ESC pill */}
              <div className="flex items-center gap-2 shrink-0">
                <span className={`hidden md:inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-[10px] font-mono ${
                  isDark ? 'border-white/10 bg-white/5 text-slate-400' : 'border-slate-300 bg-white/70 text-slate-600'
                }`}>
                  <span>ESC to close</span>
                </span>
                <button
                  type="button"
                  onClick={() => setDrawerOpen(false)}
                  aria-label="Close navigation"
                  className={`w-10 h-10 sm:w-11 sm:h-11 rounded-2xl border transition-all flex items-center justify-center cursor-pointer min-h-[44px] min-w-[44px] active:scale-95 group ${
                    isDark
                      ? 'border-white/15 bg-white/5 hover:bg-white/15 hover:border-white/30 text-white'
                      : 'border-slate-300 bg-white/80 hover:bg-slate-100 hover:border-slate-400 text-charcoal shadow-xs'
                  }`}
                >
                  <X className={`w-5 h-5 transition-transform group-hover:rotate-90 ${isDark ? 'text-slate-300 group-hover:text-white' : 'text-charcoal'}`} />
                </button>
              </div>
            </div>

            {/* Main Navigation Matrix: Editorial Multi-Column Layout */}
            <div className="relative z-10 flex-1 overflow-y-auto w-full max-w-[1520px] mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8 scrollbar-thin overflow-x-hidden">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 w-full">
                {navGroups.map((group, gIdx) => (
                  <motion.div
                    key={gIdx}
                    variants={itemGroupVariants}
                    className={`flex flex-col space-y-3 p-4 sm:p-6 rounded-3xl border transition-all backdrop-blur-xl shadow-xl w-full min-w-0 ${
                      isDark
                        ? 'bg-white/[0.03] border-white/10 hover:border-white/20'
                        : 'bg-white/90 border-slate-200/90 shadow-md hover:border-slate-300'
                    }`}
                  >
                    {/* Category Header */}
                    <div className={`border-b pb-3 ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-oxblood dark:text-rose">
                          {group.title}
                        </span>
                        <span className={`text-[10px] font-mono ${isDark ? 'text-slate-500' : 'text-slate-600'}`}>
                          {String(group.items.length).padStart(2, '0')}
                        </span>
                      </div>
                      {group.tagline && (
                        <p className={`text-[11px] mt-1 leading-snug ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                          {group.tagline}
                        </p>
                      )}
                    </div>

                    {/* Links Grid */}
                    <div className="space-y-1.5 pt-1">
                      {group.items.map((item) => {
                        const Icon = item.icon;
                        const isActive = item.active;

                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setDrawerOpen(false)}
                            className={`group relative flex items-start gap-3 p-2.5 sm:p-3 rounded-2xl transition-all duration-200 cursor-pointer min-h-[48px] ${
                              isActive
                                ? 'bg-oxblood text-white shadow-lg liquid-metal-pill border border-white/20'
                                : isDark
                                  ? 'text-slate-300 hover:text-white hover:bg-white/[0.07] border border-transparent hover:border-white/10'
                                  : 'text-charcoal hover:text-oxblood hover:bg-slate-100/80 border border-transparent hover:border-slate-200'
                            }`}
                          >
                            <div className={`mt-0.5 p-2 rounded-xl shrink-0 transition-colors ${
                              isActive
                                ? 'bg-white/20 text-white'
                                : isDark
                                  ? 'bg-white/5 text-slate-400 group-hover:text-rose group-hover:bg-white/10'
                                  : 'bg-slate-100 text-slate-600 group-hover:text-oxblood group-hover:bg-slate-200/80'
                            }`}>
                              <Icon className="w-4 h-4" />
                            </div>

                            <div className="flex-1 min-w-0 pr-2 sm:pr-4">
                              <div className="flex items-center gap-2">
                                <span className={`font-display font-bold text-xs sm:text-sm tracking-tight leading-tight group-hover:translate-x-0.5 transition-transform truncate ${
                                  isActive ? 'text-white' : isDark ? 'text-white' : 'text-charcoal'
                                }`}>
                                  {item.label}
                                </span>
                                {isActive && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse shrink-0" />
                                )}
                              </div>
                              {item.desc && (
                                <p className={`text-[11px] mt-0.5 leading-snug line-clamp-1 ${
                                  isActive
                                    ? 'text-white/80'
                                    : isDark
                                      ? 'text-slate-400 group-hover:text-slate-300'
                                      : 'text-slate-600 group-hover:text-slate-700'
                                }`}>
                                  {item.desc}
                                </p>
                              )}
                            </div>

                            <ArrowRight className={`w-4 h-4 mt-2 shrink-0 transition-all ${
                              isActive
                                ? 'text-white translate-x-0'
                                : 'opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 text-oxblood dark:text-rose'
                            }`} />
                          </Link>
                        );
                      })}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Immersive Footer: User Identity, Theme, Logout */}
            <div className={`relative z-10 w-full max-w-[1520px] mx-auto px-4 sm:px-6 lg:px-8 py-3.5 sm:py-5 border-t backdrop-blur-xl ${
              isDark ? 'border-white/10 bg-black/40 text-white' : 'border-slate-300/80 bg-white/85 text-charcoal'
            }`}>
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4 w-full">
                {user ? (
                  <>
                    <div className="flex items-center gap-2.5 sm:gap-3 w-full sm:w-auto min-w-0">
                      <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-gradient-to-br from-oxblood to-oxblood-600 text-white font-mono font-bold text-xs sm:text-sm flex items-center justify-center shadow-md shrink-0">
                        {user.name?.[0]?.toUpperCase() || 'U'}
                      </div>
                      <div className="min-w-0 flex-1 sm:flex-initial">
                        <p className={`font-display font-bold text-xs sm:text-sm truncate ${
                          isDark ? 'text-white' : 'text-charcoal'
                        }`}>
                          {user.name}
                        </p>
                        <p className="font-mono text-[11px] sm:text-xs text-oxblood dark:text-rose truncate">
                          {user.email || user.role} • <span className={`uppercase text-[9px] sm:text-[10px] ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{user.role}</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-2.5 w-full sm:w-auto justify-between sm:justify-end">
                      <button
                        onClick={toggleTheme}
                        aria-label="Toggle theme"
                        className={`flex-1 sm:flex-initial px-3 py-2 rounded-xl border text-xs font-mono transition flex items-center justify-center gap-2 min-h-[44px] ${
                          isDark
                            ? 'border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white'
                            : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-100 text-charcoal shadow-xs'
                        }`}
                      >
                        {isDark ? <Sun className="w-4 h-4 text-rose" /> : <Moon className="w-4 h-4 text-oxblood" />}
                        <span>{isDark ? 'Light' : 'Dark'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={handleLogout}
                        className="flex-1 sm:flex-initial px-4 py-2 rounded-xl border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-300 hover:text-red-700 dark:hover:text-white font-mono text-xs font-bold transition flex items-center justify-center gap-2 min-h-[44px]"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-2">
                    <span className={`text-[11px] font-mono text-center sm:text-left ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                      Sign in or create an account to unlock your personalized workspace.
                    </span>
                    <div className="flex items-center gap-2 w-full sm:w-auto justify-center">
                      <Link
                        to="/auth"
                        onClick={() => setDrawerOpen(false)}
                        className={`flex-1 sm:flex-initial px-4 py-2 rounded-xl border text-xs font-mono font-bold uppercase min-h-[44px] flex items-center justify-center ${
                          isDark
                            ? 'border-white/20 bg-white/5 text-white'
                            : 'border-slate-300 bg-white text-charcoal shadow-xs'
                        }`}
                      >
                        Sign In
                      </Link>
                      <Link
                        to="/auth?mode=register"
                        onClick={() => setDrawerOpen(false)}
                        className="flex-1 sm:flex-initial px-4 py-2 btn-oxblood rounded-xl text-xs font-mono font-bold uppercase min-h-[44px] flex items-center justify-center"
                      >
                        Sign Up
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
