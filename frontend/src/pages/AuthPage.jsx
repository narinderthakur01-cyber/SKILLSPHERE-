import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import {
  Briefcase, User, Mail, Lock, AlertCircle, ArrowRight,
  ShieldCheck, Eye, EyeOff, Sparkles, Volume2, VolumeX,
  CheckCircle2, Terminal, Cpu, Database, Award, Zap
} from 'lucide-react';

export const AuthPage = () => {
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'login';
  const initialRole = searchParams.get('role') || 'JOB_SEEKER';

  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  const [role, setRole] = useState(initialRole);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [capsLockActive, setCapsLockActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isUnverifiedError, setIsUnverifiedError] = useState(false);
  const [success, setSuccess] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [activeQuickDemo, setActiveQuickDemo] = useState(null);

  // Tilt and spotlight coordinates
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  // Web Audio API context singleton
  const audioCtxRef = useRef(null);

  const getAudioContext = () => {
    if (!audioCtxRef.current) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        audioCtxRef.current = new AudioCtx();
      }
    }
    if (audioCtxRef.current && audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  };

  // Synthesize procedural audio: Keystroke click
  const playKeySound = (len) => {
    if (!audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const baseFreq = 950 + Math.min(len * 40, 650);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(baseFreq, ctx.currentTime);
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.05);
    } catch {
      // AudioContext unavailable or restricted
    }
  };

  // Synthesize procedural audio: Action / Toggle drop
  const playActionSound = () => {
    if (!audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(480, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(240, ctx.currentTime + 0.09);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.09);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.09);
    } catch {
      // AudioContext unavailable
    }
  };

  // Synthesize procedural audio: Security Breach / Error
  const playErrorSound = () => {
    if (!audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();
      osc1.type = 'sawtooth';
      osc2.type = 'sawtooth';
      osc1.frequency.setValueAtTime(105, ctx.currentTime);
      osc2.frequency.setValueAtTime(112, ctx.currentTime);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.28);
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);
      osc1.start();
      osc2.start();
      osc1.stop(ctx.currentTime + 0.28);
      osc2.stop(ctx.currentTime + 0.28);
    } catch {
      // AudioContext unavailable
    }
  };

  // Synthesize procedural audio: Access Authorized / 5-Note Arpeggio
  const playSuccessSound = () => {
    if (!audioEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51]; // C5, E5, G5, C6, E6
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.07);
        gain.gain.setValueAtTime(0.09, ctx.currentTime + idx * 0.07);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + idx * 0.07 + 0.24);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + idx * 0.07);
        osc.stop(ctx.currentTime + idx * 0.07 + 0.24);
      });
    } catch {
      // AudioContext unavailable
    }
  };

  // Dynamic Password Entropy Calculation
  const entropyScore = useMemo(() => {
    if (!password) return 0;
    let score = 0;
    if (password.length >= 8) score += 30;
    if (password.length >= 12) score += 20;
    if (/[0-9]/.test(password)) score += 20;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 15;
    if (/[^A-Za-z0-9]/.test(password)) score += 15;
    return Math.min(score, 100);
  }, [password]);

  const entropyLabel = useMemo(() => {
    if (entropyScore === 0) return { label: 'EMPTY', color: 'var(--text-secondary)' };
    if (entropyScore < 50) return { label: 'LOW ENTROPY', color: 'var(--crimson-alert)' };
    if (entropyScore < 80) return { label: 'MEDIUM CIPHER', color: '#C49A62' };
    return { label: 'HIGH ENTROPY', color: 'var(--neon-emerald)' };
  }, [entropyScore]);

  // Pointer position & perspective tilt tracking
  const handleMouseMove = (e) => {
    const x = e.clientX;
    const y = e.clientY;
    setMousePos({ x, y });

    if (window.innerWidth >= 860 && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width - 0.5;
      const relY = (e.clientY - rect.top) / rect.height - 0.5;
      setTilt({
        x: relY * -7, // Rotate X
        y: relX * 7,  // Rotate Y
      });
    }
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
  };

  const handleKeyDown = (e) => {
    setCapsLockActive(e.getModifierState && e.getModifierState('CapsLock'));
    setIsTyping(true);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 600);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError('');
    setIsUnverifiedError(false);
    setLoading(true);

    try {
      if (isLogin) {
        const res = await authAPI.login({ email, password });
        login(res.data.access_token, res.data.user);
        playSuccessSound();
        setSuccess(true);
        setTimeout(() => redirectUser(res.data.user.role), 650);
      } else {
        await authAPI.register({
          name,
          email,
          password,
          role,
        });
        playSuccessSound();
        // Unverified candidate and recruiter accounts must verify email before accessing workspace
        navigate(`/verify-email-pending?email=${encodeURIComponent(email)}&role=${encodeURIComponent(role)}`);
      }
    } catch (err) {
      console.error("Auth error:", err);
      playErrorSound();
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : 'Security authorization rejected. Verify credentials.';
      setError(msg);
      if (status === 403 && (msg.toLowerCase().includes('verification') || msg.toLowerCase().includes('verify'))) {
        setIsUnverifiedError(true);
      } else {
        setIsUnverifiedError(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const from = location.state?.from
    ? (typeof location.state.from === 'string'
        ? location.state.from
        : `${location.state.from.pathname || ''}${location.state.from.search || ''}`)
    : null;

  const redirectUser = (userRole) => {
    if (from && from !== '/auth' && from !== '/') {
      navigate(from, { replace: true });
      return;
    }
    if (userRole === 'JOB_SEEKER') navigate('/dashboard');
    else if (userRole === 'RECRUITER') navigate('/recruiter');
    else if (userRole === 'ADMIN') navigate('/admin');
    else navigate('/');
  };

  // Quick Demo Access Trigger
  const triggerQuickDemo = async (demoRole, demoEmail, demoPass) => {
    playActionSound();
    setActiveQuickDemo(demoRole);
    setEmail(demoEmail);
    setPassword(demoPass);
    setIsLogin(true);
    setError('');
    setLoading(true);

    try {
      const res = await authAPI.login({ email: demoEmail, password: demoPass });
      login(res.data.access_token, res.data.user);
      playSuccessSound();
      setSuccess(true);
      setTimeout(() => redirectUser(res.data.user.role), 650);
    } catch (err) {
      console.error("Quick demo login failed:", err);
      playErrorSound();
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : `Authentication failed for ${demoRole}.`);
    } finally {
      setLoading(false);
      setActiveQuickDemo(null);
    }
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`obsidian-viewport ${isTyping ? 'is-typing' : ''} ${error ? 'is-error' : ''} ${success ? 'is-success' : ''}`}
      style={{
        '--mouse-x': `${mousePos.x}px`,
        '--mouse-y': `${mousePos.y}px`,
      }}
    >
      {/* 1. EMBEDDED DASHBOARD DESIGN SYSTEM & KEYFRAME ENGINE */}
      <style>{`
        :root {
          /* Exact Dashboard Obsidian Charcoal × Oxblood Token System */
          --core-surface: #1B1A1B;
          --glass-base: rgba(55, 48, 52, 0.62);
          --glass-blur: blur(28px);
          --border-stroke: rgba(197, 164, 155, 0.16);
          --border-stroke-bright: rgba(197, 164, 155, 0.35);
          --accent-primary: #914F51;
          --accent-hover: #A55B5D;
          --accent-secondary: #C5A49B;
          --neon-emerald: #829B88;
          --crimson-alert: #B76565;
          --text-primary: #EFE9E3;
          --text-secondary: #C5A49B;
          --text-muted: rgba(239, 233, 227, 0.65);
        }

        .obsidian-viewport {
          min-height: 100dvh;
          width: 100%;
          background-color: var(--core-surface);
          color: var(--text-primary);
          position: relative;
          overflow-x: hidden;
          overflow-y: auto;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2.5rem 1rem;
          font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* 2. MULTI-LAYERED AMBIENT BACKGROUND ENGINE (Dashboard Oxblood & Slate) */
        .bg-layer-ribbons {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 1;
          overflow: hidden;
        }

        .ribbon-beam {
          position: absolute;
          border-radius: 50%;
          filter: blur(110px);
          opacity: 0.26;
          transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .ribbon-1 {
          width: 580px;
          height: 580px;
          background: radial-gradient(circle, #914F51 0%, rgba(145, 79, 81, 0) 70%);
          top: -120px;
          left: -80px;
          animation: floatBeam1 24s infinite ease-in-out alternate;
        }

        .ribbon-2 {
          width: 640px;
          height: 640px;
          background: radial-gradient(circle, #373034 0%, rgba(55, 48, 52, 0) 70%);
          bottom: -150px;
          right: -100px;
          animation: floatBeam2 28s infinite ease-in-out alternate;
        }

        .ribbon-3 {
          width: 480px;
          height: 480px;
          background: radial-gradient(circle, #C5A49B 0%, rgba(197, 164, 155, 0) 70%);
          top: 38%;
          left: 45%;
          animation: floatBeam3 32s infinite ease-in-out alternate;
        }

        .is-typing .ribbon-beam {
          animation-duration: 9s !important;
          opacity: 0.36 !important;
        }

        @keyframes floatBeam1 {
          0% { transform: translate(0, 0) scale(1); }
          100% { transform: translate(110px, 90px) scale(1.15); }
        }
        @keyframes floatBeam2 {
          0% { transform: translate(0, 0) scale(1); }
          100% { transform: translate(-130px, -80px) scale(1.18); }
        }
        @keyframes floatBeam3 {
          0% { transform: translate(0, 0) scale(1); }
          100% { transform: translate(-90px, 110px) scale(0.92); }
        }

        /* Coordinate Matrix Grid */
        .bg-matrix-grid {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 2;
          background-image: 
            linear-gradient(to right, rgba(197, 164, 155, 0.045) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(197, 164, 155, 0.045) 1px, transparent 1px);
          background-size: 50px 50px;
          mask-image: radial-gradient(ellipse 65% 65% at 50% 50%, #000 30%, transparent 80%);
          -webkit-mask-image: radial-gradient(ellipse 65% 65% at 50% 50%, #000 30%, transparent 80%);
        }

        /* Revolving Conic Atmospheric Wave */
        .bg-conic-wave {
          position: fixed;
          width: 1400px;
          height: 1400px;
          left: calc(50% - 700px);
          top: calc(50% - 700px);
          pointer-events: none;
          z-index: 2;
          opacity: 0.05;
          background: conic-gradient(from 0deg, transparent 0deg, #914F51 70deg, transparent 140deg, #373034 220deg, transparent 360deg);
          animation: rotateConic 70s linear infinite;
        }

        @keyframes rotateConic {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* Caustic Vignette */
        .bg-caustic-vignette {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 3;
          background: radial-gradient(circle at 50% 50%, transparent 40%, rgba(27, 26, 27, 0.88) 90%);
        }

        /* Specular Dynamic Cursor Spotlight (Oxblood / Rose Tint) */
        .cursor-spotlight {
          position: fixed;
          width: 320px;
          height: 320px;
          border-radius: 50%;
          pointer-events: none;
          z-index: 4;
          background: radial-gradient(circle, rgba(145, 79, 81, 0.16) 0%, transparent 70%);
          transform: translate(calc(var(--mouse-x, -500px) - 160px), calc(var(--mouse-y, -500px) - 160px));
          transition: transform 0.08s linear;
        }

        /* 3. CORE TWO-COLUMN MONOLITH ARCHITECTURE */
        .auth-monolith-container {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 1140px;
          display: grid;
          grid-template-columns: 1fr;
          gap: 2rem;
          transform-style: preserve-3d;
          transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @media (min-width: 960px) {
          .auth-monolith-container {
            grid-template-columns: 1.05fr 1fr;
            gap: 2.75rem;
            align-items: center;
          }
        }

        /* Dashboard Charcoal Titanium Glass Card Surface */
        .titanium-glass-card {
          background: var(--glass-base);
          backdrop-filter: blur(28px);
          -webkit-backdrop-filter: blur(28px);
          border: 1px solid var(--border-stroke);
          box-shadow: 
            0 24px 60px -12px rgba(0, 0, 0, 0.65),
            0 0 0 1px rgba(239, 233, 227, 0.06) inset;
          border-radius: 28px;
          position: relative;
          overflow: hidden;
          transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }

        .titanium-glass-card:hover {
          border-color: var(--border-stroke-bright);
        }

        /* Left Brand Monolith */
        .brand-monolith {
          padding: 2.5rem;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }

        /* Orbital Dashboard Logo */
        .orbital-logo-wrapper {
          position: relative;
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .orbital-ring {
          position: absolute;
          inset: 0;
          border: 1.5px dashed rgba(145, 79, 81, 0.55);
          border-radius: 50%;
          animation: orbitRotate 18s linear infinite;
        }

        .orbital-ring-outer {
          position: absolute;
          inset: -6px;
          border: 1px solid rgba(197, 164, 155, 0.15);
          border-radius: 50%;
        }

        .orbital-diamond {
          width: 28px;
          height: 28px;
          background: linear-gradient(135deg, #914F51 0%, #C5A49B 100%);
          transform: rotate(45deg);
          box-shadow: 0 0 20px rgba(145, 79, 81, 0.45);
          border-radius: 6px;
        }

        @keyframes orbitRotate {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* Dual-Stroke Dashboard Inputs */
        .dual-stroke-field {
          position: relative;
          background: rgba(55, 48, 52, 0.35);
          border: 1px solid var(--border-stroke);
          border-radius: 14px;
          padding: 0.75rem 1rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          transition: all 0.25s ease;
        }

        .dual-stroke-field:focus-within {
          border-color: rgba(145, 79, 81, 0.6);
          background: rgba(55, 48, 52, 0.5);
          box-shadow: 0 0 0 1px rgba(145, 79, 81, 0.3);
        }

        .dual-stroke-field::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 12%;
          right: 12%;
          height: 1.5px;
          background: linear-gradient(90deg, transparent, #914F51, #C5A49B, transparent);
          opacity: 0;
          transform: scaleX(0.6);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .dual-stroke-field:focus-within::after {
          opacity: 1;
          left: 6%;
          right: 6%;
          transform: scaleX(1);
        }

        .dual-stroke-input {
          flex: 1;
          background: transparent;
          border: none;
          color: var(--text-primary);
          font-size: 0.875rem;
          outline: none;
        }

        .dual-stroke-input::placeholder {
          color: rgba(239, 233, 227, 0.4);
          font-size: 0.8125rem;
        }

        /* Segmented Entropy Bar */
        .entropy-segment-track {
          display: flex;
          gap: 4px;
          height: 3px;
          margin-top: 6px;
          border-radius: 2px;
          overflow: hidden;
        }

        .entropy-segment {
          flex: 1;
          background: rgba(239, 233, 227, 0.1);
          border-radius: 2px;
          transition: background-color 0.3s ease;
        }

        /* Reactive Classes */
        .is-error .titanium-glass-card {
          animation: glitchShake 0.42s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
          border-color: var(--crimson-alert) !important;
          box-shadow: 0 0 35px rgba(183, 101, 101, 0.35) !important;
        }

        @keyframes glitchShake {
          10%, 90% { transform: translate3d(-2px, 0, 0); }
          20%, 80% { transform: translate3d(3px, 0, 0); }
          30%, 50%, 70% { transform: translate3d(-3px, 0, 0); }
          40%, 60% { transform: translate3d(3px, 0, 0); }
        }

        .is-success .auth-monolith-container {
          filter: drop-shadow(0 0 45px rgba(130, 155, 136, 0.45));
          transform: scale(0.985);
          transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* Quick Demo Access Bar */
        .demo-pill-btn {
          background: rgba(55, 48, 52, 0.4);
          border: 1px solid var(--border-stroke);
          color: var(--text-secondary);
          border-radius: 12px;
          padding: 0.6rem 0.85rem;
          min-height: 44px;
          font-size: 0.75rem;
          font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .demo-pill-btn:hover {
          background: rgba(145, 79, 81, 0.22);
          border-color: var(--accent-primary);
          color: var(--text-primary);
          transform: translateY(-1.5px);
        }

        .demo-pill-btn:active {
          transform: scale(0.97);
        }

        /* Primary Action Button (Oxblood) */
        .btn-auth-primary {
          background: #914F51;
          color: #EFE9E3;
          border: 1px solid rgba(239, 233, 227, 0.18);
          box-shadow: 0 4px 16px -1px rgba(145, 79, 81, 0.4), inset 0 1px 0 0 rgba(239, 233, 227, 0.25);
          transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .btn-auth-primary:hover {
          background: #A55B5D;
          transform: translateY(-1px);
          box-shadow: 0 8px 24px -2px rgba(145, 79, 81, 0.55), inset 0 1px 0 0 rgba(239, 233, 227, 0.35);
        }

        .btn-auth-primary:active {
          transform: translateY(0);
        }
      `}</style>

      {/* 2. BACKGROUND MULTI-LAYER ENGINE */}
      <div className="bg-layer-ribbons">
        <div className="ribbon-beam ribbon-1"></div>
        <div className="ribbon-beam ribbon-2"></div>
        <div className="ribbon-beam ribbon-3"></div>
      </div>
      <div className="bg-matrix-grid"></div>
      <div className="bg-conic-wave"></div>
      <div className="bg-caustic-vignette"></div>
      <div className="cursor-spotlight"></div>

      {/* 3. MAIN SPLIT-CONTAINER MONOLITH */}
      <div
        ref={containerRef}
        className="auth-monolith-container"
        style={{
          transform: `perspective(1400px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        }}
      >
        
        {/* ======================================================== */}
        {/* LEFT BRAND MONOLITH */}
        {/* ======================================================== */}
        <div className="titanium-glass-card brand-monolith hidden md:flex min-h-[580px]">
          <div>
            {/* Orbital Dashboard Logo */}
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3.5">
                <div className="orbital-logo-wrapper">
                  <div className="orbital-ring-outer"></div>
                  <div className="orbital-ring"></div>
                  <div className="orbital-diamond"></div>
                </div>
                <div>
                  <span className="font-bold text-xl tracking-tight text-[#EFE9E3] block font-display">
                    Skill<span className="text-[#914F51]">Sphere</span>
                  </span>
                  <span className="text-[10px] font-mono tracking-widest text-[#C5A49B] uppercase block">
                    Autonomous Talent Matrix
                  </span>
                </div>
              </div>

              {/* Procedural Audio Mute/Unmute Toggle */}
              <button
                type="button"
                onClick={() => { setAudioEnabled(!audioEnabled); playActionSound(); }}
                className="p-2 rounded-xl border border-[rgba(197,164,155,0.18)] bg-[rgba(55,48,52,0.4)] text-[#C5A49B] hover:text-[#EFE9E3] hover:border-[#914F51] transition"
                title={audioEnabled ? "Synthesized Sound FX: Active" : "Synthesized Sound FX: Muted"}
              >
                {audioEnabled ? <Volume2 className="w-4 h-4 text-[#914F51]" /> : <VolumeX className="w-4 h-4" />}
              </button>
            </div>

            {/* Headline and Value Proposition (Dashboard Typography) */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(145,79,81,0.18)] border border-[rgba(145,79,81,0.35)] text-[11px] font-mono text-[#EFE9E3] uppercase tracking-wider">
                <span className="w-2 h-2 rounded-full bg-[#829B88] animate-pulse"></span>
                <span>CRYPTOGRAPHIC TALENT IDENTIFIER</span>
              </div>

              <h1 className="text-3xl font-extrabold text-[#EFE9E3] tracking-tight leading-snug font-display">
                Precision Neural Matching. <br />
                <span className="bg-gradient-to-r from-[#914F51] via-[#C5A49B] to-[#829B88] bg-clip-text text-transparent">
                  Deterministic Calibration.
                </span>
              </h1>

              <p className="text-sm text-[#C5A49B] leading-relaxed font-normal">
                SkillSphere delivers dual-engine OCR skill decomposition, verified graph telemetry, and tenancy-enforced matching with zero algorithmic opacity.
              </p>
            </div>

            {/* Feature Pills */}
            <div className="grid grid-cols-2 gap-3 mt-8 text-xs font-mono">
              <div className="p-3 rounded-2xl bg-[rgba(55,48,52,0.35)] border border-[rgba(197,164,155,0.14)]">
                <div className="flex items-center gap-2 text-[#C5A49B] font-bold mb-1">
                  <Cpu className="w-3.5 h-3.5 text-[#914F51]" />
                  <span>Dual OCR Parse</span>
                </div>
                <p className="text-[11px] text-[rgba(239,233,227,0.65)]">PyMuPDF + Tesseract coordinate extraction</p>
              </div>

              <div className="p-3 rounded-2xl bg-[rgba(55,48,52,0.35)] border border-[rgba(197,164,155,0.14)]">
                <div className="flex items-center gap-2 text-[#829B88] font-bold mb-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#829B88]" />
                  <span>Deterministic Math</span>
                </div>
                <p className="text-[11px] text-[rgba(239,233,227,0.65)]">Explainable skill-gap telemetry</p>
              </div>
            </div>
          </div>

          {/* Animated Dynamic Metric Counters */}
          <div className="pt-8 border-t border-[rgba(197,164,155,0.15)] grid grid-cols-3 gap-3 text-center font-mono">
            <div>
              <p className="text-xl font-extrabold text-[#EFE9E3]">50K+</p>
              <p className="text-[10px] text-[#C5A49B] uppercase tracking-wider mt-0.5">Verified Talents</p>
            </div>
            <div>
              <p className="text-xl font-extrabold text-[#914F51]">99.9%</p>
              <p className="text-[10px] text-[#C5A49B] uppercase tracking-wider mt-0.5">Match Precision</p>
            </div>
            <div>
              <p className="text-xl font-extrabold text-[#829B88]">24/7</p>
              <p className="text-[10px] text-[#C5A49B] uppercase tracking-wider mt-0.5">Active Relays</p>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT GLASS COMMAND CAPSULE */}
        {/* ======================================================== */}
        <div className="titanium-glass-card p-6 sm:p-8">
          
          {/* Mobile Logo Header */}
          <div className="md:hidden flex items-center justify-between mb-6 pb-4 border-b border-[rgba(197,164,155,0.15)]">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#914F51] text-[#EFE9E3] font-black flex items-center justify-center text-xs">
                S
              </div>
              <span className="font-bold text-lg text-[#EFE9E3] font-display">SkillSphere</span>
            </div>
            <button
              type="button"
              onClick={() => { setAudioEnabled(!audioEnabled); playActionSound(); }}
              className="p-1.5 rounded-lg border border-[rgba(197,164,155,0.18)] text-[#C5A49B]"
            >
              {audioEnabled ? <Volume2 className="w-3.5 h-3.5 text-[#914F51]" /> : <VolumeX className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Mode Switcher: Sign In vs Register */}
          <div className="flex bg-[rgba(55,48,52,0.45)] p-1 rounded-2xl mb-6 border border-[rgba(197,164,155,0.15)] font-mono text-xs">
            <button
              type="button"
              onClick={() => { setIsLogin(true); setError(''); setIsUnverifiedError(false); playActionSound(); }}
              className={`flex-1 min-h-[44px] py-2.5 rounded-xl uppercase tracking-wider font-bold transition flex items-center justify-center ${
                isLogin
                  ? 'bg-[#914F51] text-[#EFE9E3] shadow-md'
                  : 'text-[#C5A49B] hover:text-[#EFE9E3]'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsLogin(false); setError(''); setIsUnverifiedError(false); playActionSound(); }}
              className={`flex-1 min-h-[44px] py-2.5 rounded-xl uppercase tracking-wider font-bold transition flex items-center justify-center ${
                !isLogin
                  ? 'bg-[#914F51] text-[#EFE9E3] shadow-md'
                  : 'text-[#C5A49B] hover:text-[#EFE9E3]'
              }`}
            >
              Register
            </button>
          </div>

          {/* RESTORED QUICK DEMO ACCESS SECTION (DEVELOPMENT MODE ONLY) */}
          {import.meta.env.DEV && (
            <div className="mb-6 p-3.5 rounded-2xl bg-[rgba(55,48,52,0.3)] border border-[rgba(197,164,155,0.15)] font-mono">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#C5A49B] flex items-center gap-1.5">
                  <Zap className="w-3 h-3 text-[#914F51]" />
                  <span>Quick Demo Access (Dev Mode)</span>
                </span>
                <span className="text-[9px] text-[rgba(239,233,227,0.5)]">1-Click Login</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => triggerQuickDemo('Candidate', 'alex@example.com', '12345678')}
                  className="demo-pill-btn justify-center"
                  title="Login as Alex Morgan (Candidate, 2 SELECTED applications)"
                >
                  <User className="w-3 h-3 text-[#C5A49B]" />
                  <span>Candidate</span>
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => triggerQuickDemo('Recruiter', 'recruiter@technova.com', 'Recruiter123!')}
                  className="demo-pill-btn justify-center"
                  title="Login as TechNova Recruiter"
                >
                  <Briefcase className="w-3 h-3 text-[#829B88]" />
                  <span>Recruiter</span>
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => triggerQuickDemo('Administrator', 'admin@skillsphere.local', 'Admin123!')}
                  className="demo-pill-btn justify-center"
                  title="Login as System Super Administrator"
                >
                  <ShieldCheck className="w-3 h-3 text-[#914F51]" />
                  <span>Admin</span>
                </button>
              </div>
            </div>
          )}

          {/* Error and Success Notices with AnimatePresence */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                key="error-notice"
                initial={{ opacity: 0, y: -8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.2 }}
                className="mb-4 p-3 bg-[rgba(183,101,101,0.18)] border border-[rgba(183,101,101,0.4)] rounded-xl text-[#fca5a5] text-xs font-mono"
              >
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#f87171] mt-0.5" />
                  <span>{error}</span>
                </div>
                {isUnverifiedError && (
                  <div className="mt-2.5 pt-2 border-t border-[rgba(183,101,101,0.3)] flex items-center justify-between">
                    <span className="text-[11px] text-[#C5A49B]">Verification required:</span>
                    <Link
                      to={`/verify-email-pending?email=${encodeURIComponent(email)}`}
                      className="text-[11px] font-bold text-[#EFE9E3] hover:text-[#C5A49B] underline transition inline-flex items-center gap-1"
                    >
                      Resend Verification Email →
                    </Link>
                  </div>
                )}
              </motion.div>
            )}
            {success && (
              <motion.div
                key="success-notice"
                initial={{ opacity: 0, y: -8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.2 }}
                className="mb-4 p-3 bg-[rgba(130,155,136,0.18)] border border-[rgba(130,155,136,0.4)] rounded-xl text-[#a7f3d0] text-xs font-mono flex items-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4 shrink-0 text-[#829B88]" />
                <span>Identity Verified. Initializing Workspace...</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* FORM FIELDS */}
          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* Registration Role Switcher with Animated Height Transition */}
            <AnimatePresence mode="popLayout" initial={false}>
              {!isLogin && (
                <motion.div
                  key="register-block"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                  className="space-y-4 overflow-hidden"
                >
                  <div>
                    <label className="block text-[11px] font-mono font-bold text-[#C5A49B] uppercase tracking-wider mb-2">
                      Classify Identity:
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => { setRole('JOB_SEEKER'); playActionSound(); }}
                        className={`p-3 min-h-[48px] rounded-2xl border text-left transition ${
                          role === 'JOB_SEEKER'
                            ? 'border-[#914F51] bg-[rgba(145,79,81,0.2)] text-[#EFE9E3] shadow-sm'
                            : 'border-[rgba(197,164,155,0.15)] bg-[rgba(55,48,52,0.3)] text-[#C5A49B] hover:border-[rgba(197,164,155,0.3)]'
                        }`}
                      >
                        <User className={`w-4 h-4 mb-1.5 ${role === 'JOB_SEEKER' ? 'text-[#914F51]' : 'text-[#C5A49B]'}`} />
                        <p className="text-xs font-bold text-[#EFE9E3]">Talent</p>
                        <p className="text-[10px] text-[#C5A49B]">Applicant Node</p>
                      </button>

                      <button
                        type="button"
                        onClick={() => { setRole('RECRUITER'); playActionSound(); }}
                        className={`p-3 min-h-[48px] rounded-2xl border text-left transition ${
                          role === 'RECRUITER'
                            ? 'border-[#914F51] bg-[rgba(145,79,81,0.2)] text-[#EFE9E3] shadow-sm'
                            : 'border-[rgba(197,164,155,0.15)] bg-[rgba(55,48,52,0.3)] text-[#C5A49B] hover:border-[rgba(197,164,155,0.3)]'
                        }`}
                      >
                        <Briefcase className={`w-4 h-4 mb-1.5 ${role === 'RECRUITER' ? 'text-[#914F51]' : 'text-[#C5A49B]'}`} />
                        <p className="text-xs font-bold text-[#EFE9E3]">Enterprise</p>
                        <p className="text-[10px] text-[#C5A49B]">Recruiter Node</p>
                      </button>
                    </div>
                  </div>

                  {/* Legal Name */}
                  <div>
                    <label className="block text-[11px] font-mono font-bold text-[#C5A49B] uppercase tracking-wider mb-1.5">
                      Full Legal Name
                    </label>
                    <div className="dual-stroke-field">
                      <User className="w-4 h-4 text-[#C5A49B] shrink-0" />
                      <input
                        type="text"
                        required
                        placeholder="e.g. Alex Morgan"
                        value={name}
                        onChange={(e) => { setName(e.target.value); playKeySound(e.target.value.length); }}
                        onKeyDown={handleKeyDown}
                        className="dual-stroke-input"
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Email Field */}
            <div>
              <label className="block text-[11px] font-mono font-bold text-[#C5A49B] uppercase tracking-wider mb-1.5">
                Work or Personal Coordinates
              </label>
              <div className="dual-stroke-field">
                <Mail className="w-4 h-4 text-[#C5A49B] shrink-0" />
                <input
                  type="email"
                  required
                  placeholder="name@domain.com"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); playKeySound(e.target.value.length); }}
                  onKeyDown={handleKeyDown}
                  className="dual-stroke-input"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-[11px] font-mono font-bold text-[#C5A49B] uppercase tracking-wider">
                  Access Cipher
                </label>
                {capsLockActive && (
                  <span className="text-[10px] font-mono text-[#C49A62] flex items-center gap-1">
                    <span>⚠ CAPS LOCK ON</span>
                  </span>
                )}
              </div>

              <div className="dual-stroke-field">
                <Lock className="w-4 h-4 text-[#C5A49B] shrink-0" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); playKeySound(e.target.value.length); }}
                  onKeyDown={handleKeyDown}
                  className="dual-stroke-input font-mono"
                />
                <button
                  type="button"
                  onClick={() => { setShowPassword(!showPassword); playActionSound(); }}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-[#C5A49B] hover:text-[#EFE9E3] hover:bg-white/5 transition"
                  title={showPassword ? "Hide password" : "Show password"}
                  aria-label={showPassword ? "Hide password cipher" : "Reveal password cipher"}
                >
                  <AnimatePresence mode="wait" initial={false}>
                    <motion.div
                      key={showPassword ? 'eye-off' : 'eye'}
                      initial={{ opacity: 0, rotate: -45, scale: 0.8 }}
                      animate={{ opacity: 1, rotate: 0, scale: 1 }}
                      exit={{ opacity: 0, rotate: 45, scale: 0.8 }}
                      transition={{ duration: 0.16 }}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </motion.div>
                  </AnimatePresence>
                </button>
              </div>

              {/* Password Entropy Segmented Meter */}
              {password && (
                <div className="mt-2 font-mono">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-[#C5A49B]">ENTROPY CALIBRATION:</span>
                    <span style={{ color: entropyLabel.color }} className="font-bold">
                      {entropyLabel.label}
                    </span>
                  </div>
                  <div className="entropy-segment-track">
                    <div
                      className="entropy-segment"
                      style={{
                        backgroundColor: entropyScore > 0 ? (entropyScore < 50 ? 'var(--crimson-alert)' : entropyScore < 80 ? '#C49A62' : 'var(--neon-emerald)') : undefined,
                      }}
                    ></div>
                    <div
                      className="entropy-segment"
                      style={{
                        backgroundColor: entropyScore >= 50 ? (entropyScore < 80 ? '#C49A62' : 'var(--neon-emerald)') : undefined,
                      }}
                    ></div>
                    <div
                      className="entropy-segment"
                      style={{
                        backgroundColor: entropyScore >= 80 ? 'var(--neon-emerald)' : undefined,
                      }}
                    ></div>
                  </div>
                </div>
              )}
            </div>

            {/* Remember Session Toggle & Forgot Password Link */}
            <div className="flex items-center justify-between pt-1 text-xs font-mono text-[#C5A49B]">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-[rgba(197,164,155,0.25)] bg-[rgba(55,48,52,0.5)] text-[#914F51] focus:ring-0"
                />
                <span>Persistent Session</span>
              </label>
              {isLogin ? (
                <Link
                  to="/forgot-password"
                  className="text-[11px] text-[#C5A49B] hover:text-[#EFE9E3] hover:underline transition"
                >
                  Forgot Password?
                </Link>
              ) : (
                <span className="text-[10px] text-[#C5A49B]">256-bit AES</span>
              )}
            </div>

            {/* Primary Action Button (Oxblood) */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 min-h-[48px] py-3.5 px-4 rounded-xl font-bold font-mono text-xs uppercase tracking-wider btn-auth-primary flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-[#EFE9E3]/30 border-t-[#EFE9E3] rounded-full animate-spin"></div>
              ) : (
                <>
                  <span>{isLogin ? 'Authenticate Workspace' : 'Initialize Account'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Bottom Telemetry Strip */}
          <div className="mt-6 pt-5 border-t border-[rgba(197,164,155,0.15)] flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-[#C5A49B]">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#829B88] animate-ping"></span>
              <span>GATEWAY: 127.0.0.1:8000 [ACTIVE]</span>
            </span>
            <span>AUTH: JWT HS256</span>
            <span className="text-[#EFE9E3]">TALENT GRAPH: READY</span>
          </div>
        </div>

      </div>
    </div>
  );
};
