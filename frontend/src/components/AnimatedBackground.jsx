import React from 'react';

/**
 * Obsidian Charcoal × Oxblood Ambient Background
 * Multiple subtle gradient layers with slow charcoal and deep slate movement,
 * and restrained oxblood atmospheric light transitions.
 * No landscapes, scenery, floating objects, or distracting decorations.
 */
export const AnimatedBackground = () => {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden transition-colors duration-700"
    >
      {/* Dark-First Theme: Obsidian Charcoal & Deep Slate with Oxblood Ambient Glow */}
      <div className="dark:block hidden absolute inset-0">
        {/* Layer 1: Charcoal / Deep Slate Base Drift */}
        <div
          className="ambient-shift-1 absolute -top-[15%] -left-[10%] w-[65vw] h-[65vw] rounded-full blur-[140px] opacity-[0.28]"
          style={{ background: 'radial-gradient(circle, #373034 0%, transparent 70%)' }}
        />

        {/* Layer 2: Restrained Oxblood Atmospheric Transition */}
        <div
          className="ambient-shift-2 absolute top-[30%] -right-[15%] w-[60vw] h-[60vw] rounded-full blur-[160px] opacity-[0.16]"
          style={{ background: 'radial-gradient(circle, #914F51 0%, transparent 65%)' }}
        />

        {/* Layer 3: Warm Dusty Rose / Deep Slate Low-Light Base */}
        <div
          className="ambient-shift-3 absolute -bottom-[10%] left-[20%] w-[55vw] h-[55vw] rounded-full blur-[150px] opacity-[0.14]"
          style={{ background: 'radial-gradient(circle, #373034 0%, #1B1A1B 75%)' }}
        />
      </div>

      {/* Light Theme: Warm Ivory Canvas with Subtle Slate & Rose Accents */}
      <div className="dark:hidden block absolute inset-0">
        <div
          className="ambient-shift-1 absolute -top-[10%] -left-[10%] w-[60vw] h-[60vw] rounded-full blur-[130px] opacity-[0.06]"
          style={{ background: 'radial-gradient(circle, #373034 0%, transparent 70%)' }}
        />
        <div
          className="ambient-shift-2 absolute top-[35%] -right-[10%] w-[60vw] h-[60vw] rounded-full blur-[140px] opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, #914F51 0%, transparent 65%)' }}
        />
        <div
          className="ambient-shift-3 absolute -bottom-[15%] left-[25%] w-[50vw] h-[50vw] rounded-full blur-[120px] opacity-[0.05]"
          style={{ background: 'radial-gradient(circle, #C5A49B 0%, transparent 70%)' }}
        />
      </div>
    </div>
  );
};