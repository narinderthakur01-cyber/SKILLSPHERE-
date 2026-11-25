import React from 'react';

/**
 * SkillSphere Animated Thermal-Gradient Background
 * Organic, continuous multi-layer thermal atmospheric flow integrating
 * Obsidian Charcoal (#1B1A1B), Deep Slate (#373034), Oxblood (#914F51),
 * and Warm Dusty Rose (#C5A49B).
 *
 * GPU-accelerated via transform3d; fully behind content with pointer-events-none.
 */
export const AnimatedBackground = () => {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden transition-colors duration-700 select-none"
    >
      {/* =================================================================== */}
      {/* DARK THEME: Obsidian Charcoal Canvas with Visible Thermal Currents */}
      {/* =================================================================== */}
      <div className="dark:block hidden absolute inset-0">
        {/* Subtle noise/texture overlay for organic metallic grain */}
        <div className="absolute inset-0 bg-[#161517] opacity-95" />

        {/* Thermal Layer 1: Main Oxblood Thermal Core (Top Left Drift) */}
        <div
          className="thermal-wave-1 absolute -top-[20%] -left-[15%] w-[75vw] h-[75vw] rounded-full blur-[130px] opacity-[0.38] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 45% 45%, #914F51 0%, #643233 45%, transparent 70%)'
          }}
        />

        {/* Thermal Layer 2: Deep Slate Resonance Wave (Center-Right Drift) */}
        <div
          className="thermal-wave-2 absolute top-[20%] -right-[20%] w-[70vw] h-[70vw] rounded-full blur-[140px] opacity-[0.42]"
          style={{
            background: 'radial-gradient(circle at 55% 50%, #373034 0%, #252425 50%, transparent 75%)'
          }}
        />

        {/* Thermal Layer 3: Warm Rose Luminescence (Bottom Center Drift) */}
        <div
          className="thermal-wave-3 absolute -bottom-[20%] left-[15%] w-[65vw] h-[65vw] rounded-full blur-[120px] opacity-[0.24] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle at 50% 50%, #C5A49B 0%, #914F51 40%, transparent 70%)'
          }}
        />

        {/* Thermal Layer 4: Organic Thermal Pulse (Breathing Accent Core) */}
        <div
          className="thermal-pulse absolute top-[40%] left-[30%] w-[50vw] h-[50vw] rounded-full blur-[150px] opacity-[0.22] mix-blend-screen"
          style={{
            background: 'radial-gradient(circle, #BA7476 0%, #7B3F41 40%, transparent 65%)'
          }}
        />
      </div>

      {/* =================================================================== */}
      {/* LIGHT THEME: Warm Ivory Canvas with Soft Thermal Rose & Oxblood      */}
      {/* =================================================================== */}
      <div className="dark:hidden block absolute inset-0">
        <div className="absolute inset-0 bg-[#EFE9E3] opacity-95" />

        {/* Thermal Wave Light 1: Warm Rose Bloom (Top-Left) */}
        <div
          className="thermal-wave-1 absolute -top-[15%] -left-[10%] w-[68vw] h-[68vw] rounded-full blur-[120px] opacity-[0.18]"
          style={{
            background: 'radial-gradient(circle at 40% 40%, #C5A49B 0%, #E7C8C9 45%, transparent 70%)'
          }}
        />

        {/* Thermal Wave Light 2: Oxblood Warmth (Middle-Right) */}
        <div
          className="thermal-wave-2 absolute top-[30%] -right-[15%] w-[65vw] h-[65vw] rounded-full blur-[130px] opacity-[0.14]"
          style={{
            background: 'radial-gradient(circle at 50% 50%, #914F51 0%, #BA7476 40%, transparent 68%)'
          }}
        />

        {/* Thermal Wave Light 3: Deep Slate Subtle Ground (Bottom-Left) */}
        <div
          className="thermal-wave-3 absolute -bottom-[15%] left-[20%] w-[60vw] h-[60vw] rounded-full blur-[125px] opacity-[0.10]"
          style={{
            background: 'radial-gradient(circle, #373034 0%, #8A7F87 45%, transparent 70%)'
          }}
        />
      </div>
    </div>
  );
};
