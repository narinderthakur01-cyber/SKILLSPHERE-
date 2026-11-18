import React, { useEffect, useRef } from 'react';
import { usePrefersReducedMotion } from '../MotionComponents';

/**
 * LandingBackground
 * Combines an animated gradient mesh, flowing abstract light trails,
 * fine grain texture, and subtle desktop pointer parallax.
 * Strictly respects prefers-reduced-motion with an elegant static fallback.
 */
export const LandingBackground = () => {
  const shouldReduceMotion = usePrefersReducedMotion();
  const parallaxRef = useRef(null);
  const targetOffset = useRef({ x: 0, y: 0 });
  const currentOffset = useRef({ x: 0, y: 0 });
  const rafId = useRef(null);

  useEffect(() => {
    if (shouldReduceMotion) return;

    // Skip on touch-first devices for battery and rendering efficiency
    if (typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches) {
      return;
    }

    const handlePointerMove = (e) => {
      const { innerWidth, innerHeight } = window;
      // Very restrained normalized offset between -10px and +10px
      const x = ((e.clientX / innerWidth) - 0.5) * 20;
      const y = ((e.clientY / innerHeight) - 0.5) * 20;
      targetOffset.current = { x, y };
    };

    const animateParallax = () => {
      // Smooth lerp damping without triggering React re-renders
      currentOffset.current.x += (targetOffset.current.x - currentOffset.current.x) * 0.04;
      currentOffset.current.y += (targetOffset.current.y - currentOffset.current.y) * 0.04;

      if (parallaxRef.current) {
        parallaxRef.current.style.transform = `translate3d(${currentOffset.current.x.toFixed(2)}px, ${currentOffset.current.y.toFixed(2)}px, 0)`;
      }
      rafId.current = requestAnimationFrame(animateParallax);
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    rafId.current = requestAnimationFrame(animateParallax);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [shouldReduceMotion]);

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 overflow-hidden select-none"
    >
      {/* Parallax Container */}
      <div
        ref={parallaxRef}
        className="absolute inset-0 w-full h-full will-change-transform"
      >
        {/* ======================================================== */}
        {/* LAYER A: ANIMATED GRADIENT MESH FORMS                    */}
        {/* Deep Charcoal, Oxblood, Burgundy, Muted Rose, Crimson     */}
        {/* ======================================================== */}

        {/* Gradient Form 1: Deep Oxblood & Burgundy (Top Left) */}
        <div
          className={`absolute -top-[15%] -left-[10%] w-[700px] h-[700px] sm:w-[900px] sm:h-[900px] rounded-full blur-[150px] opacity-40 dark:opacity-35 ${
            shouldReduceMotion ? '' : 'landing-mesh-1'
          }`}
          style={{
            background: 'radial-gradient(circle at 45% 45%, #914F51 0%, #643233 48%, transparent 72%)',
          }}
        />

        {/* Gradient Form 2: Muted Rose & Crimson (Top Right) */}
        <div
          className={`absolute top-[5%] -right-[15%] w-[620px] h-[620px] sm:w-[820px] sm:h-[820px] rounded-full blur-[160px] opacity-35 dark:opacity-25 ${
            shouldReduceMotion ? '' : 'landing-mesh-2'
          }`}
          style={{
            background: 'radial-gradient(circle at 50% 50%, #C5A49B 0%, #BA7476 42%, transparent 70%)',
          }}
        />

        {/* Gradient Form 3: Soft Crimson Highlight (Center Low) */}
        <div
          className={`absolute top-[45%] left-[20%] w-[580px] h-[580px] sm:w-[760px] sm:h-[760px] rounded-full blur-[150px] opacity-30 dark:opacity-20 ${
            shouldReduceMotion ? '' : 'landing-mesh-3'
          }`}
          style={{
            background: 'radial-gradient(circle at 45% 45%, #A55B5D 0%, #7B3F41 55%, transparent 72%)',
          }}
        />

        {/* Gradient Form 4: Deep Charcoal & Burgundy Base (Bottom Right) */}
        <div
          className={`absolute -bottom-[12%] right-[5%] w-[540px] h-[540px] sm:w-[700px] sm:h-[700px] rounded-full blur-[160px] opacity-30 dark:opacity-20 ${
            shouldReduceMotion ? '' : 'landing-mesh-4'
          }`}
          style={{
            background: 'radial-gradient(circle at 50% 50%, #373034 0%, #4E2627 50%, transparent 70%)',
          }}
        />

        {/* ======================================================== */}
        {/* LAYER B: FLOWING ABSTRACT LIGHT TRAILS (PERIMETER ONLY)   */}
        {/* ======================================================== */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 1440 900"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="xMidYMid slice"
        >
          <defs>
            {/* Trail 1 Gradient */}
            <linearGradient id="trailGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#914F51" stopOpacity="0" />
              <stop offset="35%" stopColor="#914F51" stopOpacity="0.6" />
              <stop offset="65%" stopColor="#C5A49B" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#914F51" stopOpacity="0" />
            </linearGradient>

            {/* Trail 2 Gradient */}
            <linearGradient id="trailGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#C5A49B" stopOpacity="0" />
              <stop offset="40%" stopColor="#BA7476" stopOpacity="0.5" />
              <stop offset="70%" stopColor="#914F51" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#373034" stopOpacity="0" />
            </linearGradient>

            {/* Trail 3 Gradient */}
            <linearGradient id="trailGrad3" x1="0%" y1="50%" x2="100%" y2="50%">
              <stop offset="0%" stopColor="#643233" stopOpacity="0" />
              <stop offset="50%" stopColor="#914F51" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#C5A49B" stopOpacity="0" />
            </linearGradient>

            <filter id="trailGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Curved Trail 1: Top-Left Outer Sweep */}
          <path
            d="M -80 320 C 180 140, 420 380, 680 180"
            stroke="url(#trailGrad1)"
            strokeWidth="2.5"
            strokeLinecap="round"
            filter="url(#trailGlow)"
            className={shouldReduceMotion ? 'opacity-30' : 'landing-trail-path-1'}
          />

          {/* Curved Trail 2: Top-Right Outer Arch */}
          <path
            d="M 850 120 C 1100 280, 1260 140, 1520 360"
            stroke="url(#trailGrad2)"
            strokeWidth="2"
            strokeLinecap="round"
            filter="url(#trailGlow)"
            className={shouldReduceMotion ? 'opacity-30' : 'landing-trail-path-2'}
          />

          {/* Curved Trail 3: Lower Perimeter Sweep */}
          <path
            d="M 60 760 C 420 620, 880 780, 1380 640"
            stroke="url(#trailGrad3)"
            strokeWidth="2"
            strokeLinecap="round"
            filter="url(#trailGlow)"
            className={shouldReduceMotion ? 'opacity-25' : 'landing-trail-path-3'}
          />
        </svg>

        {/* Ambient Vignette Overlay for Depth */}
        <div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-warmivory/40 dark:to-charcoal/50 pointer-events-none"
        />
      </div>

      {/* ======================================================== */}
      {/* LAYER C: SUBTLE TACTILE GRAIN TEXTURE                    */}
      {/* ======================================================== */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.028] dark:opacity-[0.038] mix-blend-overlay pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="landing-fine-grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#landing-fine-grain)" />
      </svg>
    </div>
  );
};
