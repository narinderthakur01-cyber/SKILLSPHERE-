import React, { useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';

/**
 * SkillSphere Unified Atmospheric Background
 * Integrates:
 * 1. Inspira UI Wavy Background (React + HTML5 Canvas adaptation)
 * 2. Liquid-Nitrogen Cryogenic Silver-Cyan Vapor Streams
 * 3. Thermal-Gradient Oxblood & Dusty Rose Ambient Glow
 *
 * GPU-accelerated, responsive, pointer-events-none, strictly behind content (-z-10).
 * Honors prefers-reduced-motion.
 *
 * Theme Architecture:
 * - Dark Theme: Deep Obsidian Charcoal (#0C0B0E) + Screen-blended Oxblood & Nitrogen streams.
 * - Light Theme: Warm Clean Ivory (#EFE9E3) + Multiply-blended Steel Silver, Cool Cryo Frost,
 *   and Muted Oxblood ribbons for rich visibility without washing out.
 */
export const AnimatedBackground = () => {
  const canvasRef = useRef(null);
  const { isDark } = useTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = 0;
    let height = 0;
    let t = 0;

    // Check prefers-reduced-motion
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReducedMotion = mediaQuery.matches;

    // Handle high-DPI crisp rendering
    const handleResize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    // Wave color palettes for Inspira UI Wavy Background
    // Dark Palette: Preserved Obsidian Charcoal × Oxblood × Liquid Nitrogen Cyan
    const darkWaveColors = [
      'rgba(145, 79, 81, 0.40)',   // Muted Oxblood
      'rgba(88, 36, 39, 0.48)',    // Deep Burgundy
      'rgba(197, 164, 155, 0.28)', // Dusty Rose
      'rgba(184, 216, 235, 0.35)', // Liquid Nitrogen Silver-Cyan
      'rgba(215, 230, 242, 0.22)', // Icy Metallic Platinum
    ];

    // Light Palette: High-clarity subtle metallic, cool steel grey, muted oxblood, and icy frost
    const lightWaveColors = [
      'rgba(145, 79, 81, 0.55)',   // Muted Oxblood Ribbon
      'rgba(95, 115, 135, 0.48)',  // Cool Steel / Subtle Silver
      'rgba(175, 125, 130, 0.46)', // Warm Dusty Rose
      'rgba(70, 125, 155, 0.42)',  // Cryogenic Cool Frost
      'rgba(125, 138, 150, 0.40)', // Neutral Metallic Slate
    ];

    // Smooth sinusoidal multi-frequency wave calculation (Inspira / Aceternity style)
    const drawWave = (color, index, total, time) => {
      ctx.beginPath();
      ctx.lineWidth = isDark ? 1.8 : 2.2;
      ctx.strokeStyle = color;

      const baseHeight = height * (0.52 + (index * 0.055) - (total * 0.025));
      const freq = 0.0016 + (index * 0.0004);
      const amp1 = 36 + (index * 8);
      const amp2 = 22 + (index * 5);
      const speed = time * (0.0009 + (index * 0.00025));

      for (let x = 0; x <= width; x += 6) {
        const y =
          baseHeight +
          Math.sin(x * freq + speed) * amp1 +
          Math.cos(x * (freq * 0.65) + speed * 1.3) * amp2;

        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const colors = isDark ? darkWaveColors : lightWaveColors;
      colors.forEach((col, idx) => {
        drawWave(col, idx, colors.length, t);
      });

      if (!prefersReducedMotion) {
        t += 1;
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [isDark]);

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden transition-colors duration-700 select-none"
    >
      {/* =================================================================== */}
      {/* DARK THEME: Obsidian Charcoal Canvas with Nitrogen & Thermal       */}
      {/* =================================================================== */}
      <div className="dark:block hidden absolute inset-0">
        <div className="absolute inset-0 bg-[#0C0B0E] opacity-98" />

        {/* 1. Thermal Core Layer: Deep Oxblood Heat (Top Left) */}
        <div
          className="thermal-wave-1 absolute -top-[20%] -left-[15%] w-[75vw] h-[75vw] rounded-full blur-[135px] opacity-[0.32] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 45% 45%, #914F51 0%, #582427 45%, transparent 70%)'
          }}
        />

        {/* 2. Liquid Nitrogen Stream 1: Cryogenic Silver-Cyan Vapor (Top Right Flow) */}
        <div
          className="nitrogen-stream-1 absolute -top-[10%] right-[5%] w-[70vw] h-[70vw] rounded-full blur-[130px] opacity-[0.26] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 50% 45%, rgba(184, 216, 235, 0.95) 0%, rgba(120, 168, 196, 0.5) 40%, rgba(45, 70, 88, 0.25) 65%, transparent 75%)'
          }}
        />

        {/* 3. Thermal Layer: Deep Slate Structural Resonance (Center-Right Drift) */}
        <div
          className="thermal-wave-2 absolute top-[25%] -right-[15%] w-[70vw] h-[70vw] rounded-full blur-[140px] opacity-[0.36]"
          style={{
            background: 'radial-gradient(circle at 55% 50%, #373034 0%, #201F22 50%, transparent 75%)'
          }}
        />

        {/* 4. Liquid Nitrogen Stream 2: Icy Platinum Sublimation Cloud (Bottom Left Flow) */}
        <div
          className="nitrogen-stream-2 absolute bottom-[5%] -left-[10%] w-[65vw] h-[65vw] rounded-full blur-[125px] opacity-[0.24] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 50% 50%, rgba(198, 222, 235, 0.9) 0%, rgba(138, 178, 200, 0.45) 45%, transparent 70%)'
          }}
        />

        {/* 5. Thermal Layer: Warm Rose Luminescence (Bottom Center Drift) */}
        <div
          className="thermal-wave-3 absolute -bottom-[20%] left-[25%] w-[62vw] h-[62vw] rounded-full blur-[120px] opacity-[0.22] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 50% 50%, #C5A49B 0%, #8A4648 40%, transparent 70%)'
          }}
        />

        {/* 6. Liquid Nitrogen Vapor Aura (Breathing Center Pulse) */}
        <div
          className="nitrogen-vapor absolute top-[35%] left-[30%] w-[55vw] h-[55vw] rounded-full blur-[145px] opacity-[0.20] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle, rgba(175, 210, 228, 0.65) 0%, rgba(95, 140, 168, 0.3) 45%, transparent 68%)'
          }}
        />
      </div>

      {/* =================================================================== */}
      {/* LIGHT THEME: Warm Ivory Canvas with Metallic Frost & Thermal Bloom  */}
      {/* =================================================================== */}
      <div className="dark:hidden block absolute inset-0">
        <div className="absolute inset-0 bg-[#EFE9E3]" />

        {/* 1. Thermal Oxblood Core (Top Left Warmth) */}
        <div
          className="thermal-wave-1 absolute -top-[18%] -left-[12%] w-[72vw] h-[72vw] rounded-full blur-[130px] opacity-[0.28] mix-blend-multiply"
          style={{
            background: 'radial-gradient(circle at 45% 45%, #C5A49B 0%, #D4A5A8 40%, rgba(145, 79, 81, 0.35) 65%, transparent 75%)'
          }}
        />

        {/* 2. Liquid Nitrogen Cryogenic Mist (Top Right Cool Silver-Cyan Flow) */}
        <div
          className="nitrogen-stream-1 absolute -top-[10%] right-[0%] w-[68vw] h-[68vw] rounded-full blur-[125px] opacity-[0.32] mix-blend-multiply"
          style={{
            background: 'radial-gradient(circle at 50% 45%, rgba(140, 185, 210, 0.8) 0%, rgba(175, 205, 222, 0.5) 40%, rgba(200, 220, 230, 0.2) 65%, transparent 75%)'
          }}
        />

        {/* 3. Thermal Layer: Muted Oxblood Structural Warmth (Middle Right Drift) */}
        <div
          className="thermal-wave-2 absolute top-[28%] -right-[15%] w-[66vw] h-[66vw] rounded-full blur-[135px] opacity-[0.25] mix-blend-multiply"
          style={{
            background: 'radial-gradient(circle at 50% 50%, #914F51 0%, #B87679 40%, transparent 70%)'
          }}
        />

        {/* 4. Liquid Nitrogen Stream 2: Silver Vapor Sublimation (Bottom Left Flow) */}
        <div
          className="nitrogen-stream-2 absolute bottom-[2%] -left-[10%] w-[64vw] h-[64vw] rounded-full blur-[125px] opacity-[0.28] mix-blend-multiply"
          style={{
            background: 'radial-gradient(circle, rgba(160, 195, 215, 0.75) 0%, rgba(195, 215, 225, 0.4) 45%, transparent 70%)'
          }}
        />

        {/* 5. Ambient Center Vapor Aura */}
        <div
          className="nitrogen-vapor absolute top-[35%] left-[28%] w-[52vw] h-[52vw] rounded-full blur-[140px] opacity-[0.20] mix-blend-multiply"
          style={{
            background: 'radial-gradient(circle, rgba(170, 190, 205, 0.6) 0%, rgba(205, 180, 185, 0.3) 50%, transparent 70%)'
          }}
        />
      </div>

      {/* =================================================================== */}
      {/* INSPIRA UI WAVY BACKGROUND CANVAS LAYER                              */}
      {/* Dark: mix-blend-screen; Light: mix-blend-multiply for clear waves    */}
      {/* =================================================================== */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none opacity-85 dark:opacity-75 dark:mix-blend-screen mix-blend-multiply transition-opacity duration-500"
      />
    </div>
  );
};
