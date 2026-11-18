import React from 'react';
import { motion } from 'framer-motion';
import {
  Send,
  ClipboardCheck,
  Search,
  CheckCircle2
} from 'lucide-react';
import { usePrefersReducedMotion } from '../MotionComponents';

/**
 * ApplicationJourneySection
 * Section 3: "Every application, in one place"
 * Illustrative workflow: Applied → Assessment → Under Review → Decision.
 * Horizontal layout on desktop; vertical timeline on mobile.
 */
export const ApplicationJourneySection = () => {
  const shouldReduceMotion = usePrefersReducedMotion();

  const journeySteps = [
    {
      step: '01',
      title: 'Applied',
      icon: Send,
      description:
        'Submit your qualifications directly to open roles with your up-to-date profile.',
    },
    {
      step: '02',
      title: 'Assessment',
      icon: ClipboardCheck,
      description:
        'Complete any relevant role-based evaluations or skill reviews requested by the hiring team.',
    },
    {
      step: '03',
      title: 'Under Review',
      icon: Search,
      description:
        'Employers review your background, evaluate competency alignment, and consider team fit.',
    },
    {
      step: '04',
      title: 'Decision',
      icon: CheckCircle2,
      description:
        'Receive clear status updates, interview invitations, and timely feedback on your candidacy.',
    },
  ];

  return (
    <section className="py-20 sm:py-28 relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate/10 dark:border-rose/10">
      {/* Section Header */}
      <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-20">
        <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-charcoal dark:text-ivory tracking-tight">
          Every application, in one place
        </h2>
        <p className="mt-3 text-sm sm:text-base text-slate/75 dark:text-ivory/70 font-normal leading-relaxed">
          Keep track of your applications, assessments and hiring updates without losing sight of your next step.
        </p>
      </div>

      {/* ======================================================== */}
      {/* DESKTOP TIMELINE (>= 1024px)                             */}
      {/* ======================================================== */}
      <div className="hidden lg:block relative">
        {/* Track Line */}
        <div className="absolute top-[38px] left-[10%] right-[10%] h-[2px] bg-slate/15 dark:bg-rose/15 -z-10" />

        {/* Animated Progress Beam */}
        <motion.div
          className="absolute top-[38px] left-[10%] h-[2px] bg-gradient-to-r from-oxblood via-dustyrose to-oxblood origin-left -z-10"
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true, margin: '-40px' }}
          transition={{ duration: shouldReduceMotion ? 0.1 : 1.1, ease: [0.16, 1, 0.3, 1] }}
          style={{ width: '80%' }}
        />

        <div className="grid grid-cols-4 gap-6">
          {journeySteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.step}
                initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ duration: 0.5, delay: shouldReduceMotion ? 0 : idx * 0.12 }}
                className="flex flex-col items-center text-center"
              >
                {/* Numbered Step Circle */}
                <div className="w-18 h-18 rounded-2xl glass-surface-elevated border border-oxblood/30 dark:border-rose/25 flex items-center justify-center shadow-md mb-6 relative group transition-transform duration-300 hover:scale-105">
                  <div className="w-9 h-9 rounded-xl bg-oxblood text-ivory flex items-center justify-center font-display font-bold text-xs shadow-xs">
                    {step.step}
                  </div>
                </div>

                {/* Step Card */}
                <div className="w-full glass-card p-5 sm:p-6 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm text-left hover:border-oxblood/35 dark:hover:border-rose/25 transition-all duration-300">
                  <div className="flex items-center gap-2 mb-2 text-oxblood dark:text-rose">
                    <Icon className="w-4 h-4" />
                    <h3 className="font-display text-base font-bold text-charcoal dark:text-ivory">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-xs text-slate/75 dark:text-ivory/70 leading-relaxed font-normal">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* ======================================================== */}
      {/* MOBILE / TABLET VERTICAL TIMELINE (< 1024px)             */}
      {/* ======================================================== */}
      <div className="lg:hidden relative pl-6 sm:pl-8 space-y-6">
        {/* Continuous Connecting Line */}
        <div className="absolute left-[18px] sm:left-[22px] top-4 bottom-4 w-[2px] bg-gradient-to-b from-oxblood via-dustyrose to-slate/20" />

        {journeySteps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <motion.div
              key={step.step}
              initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, x: -14 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-30px' }}
              transition={{ duration: 0.4, delay: shouldReduceMotion ? 0 : idx * 0.08 }}
              className="relative pl-6 sm:pl-8"
            >
              {/* Node Indicator */}
              <div className="absolute -left-[18px] sm:-left-[22px] top-1 w-9 h-9 rounded-xl bg-oxblood text-ivory flex items-center justify-center font-display font-bold text-xs shadow-md border-2 border-white dark:border-charcoal">
                {step.step}
              </div>

              {/* Card Container */}
              <div className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm">
                <div className="flex items-center gap-2 mb-1.5 text-oxblood dark:text-rose">
                  <Icon className="w-4 h-4" />
                  <h3 className="font-display text-base font-bold text-charcoal dark:text-ivory">
                    {step.title}
                  </h3>
                </div>
                <p className="text-xs sm:text-sm text-slate/75 dark:text-ivory/70 leading-relaxed font-normal">
                  {step.description}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Subtle Illustrative Workflow Note */}
      <p className="mt-12 text-center font-mono text-[11px] text-slate/50 dark:text-ivory/40">
        Illustrative hiring workflow. Specific stages may vary according to employer and role requirements.
      </p>
    </section>
  );
};
