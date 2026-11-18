import React from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Compass,
  Target,
  Layers
} from 'lucide-react';
import { LiquidSpotlightCard, usePrefersReducedMotion } from '../MotionComponents';

/**
 * FeatureCardsSection
 * Section 1: "Your profile, all in one place"
 * Four clear, consistent cards representing the candidate journey:
 * 1. Build your profile
 * 2. Discover opportunities
 * 3. Understand skill matches
 * 4. Track your applications
 */
export const FeatureCardsSection = () => {
  const shouldReduceMotion = usePrefersReducedMotion();

  const features = [
    {
      id: 'profile',
      icon: FileText,
      title: 'Build your profile',
      description:
        'Consolidate your experience, skills and qualifications into one organised profile ready for review.',
    },
    {
      id: 'opportunities',
      icon: Compass,
      title: 'Discover opportunities',
      description:
        'Explore relevant open positions tailored to your specific capabilities, domain experience and career aspirations.',
    },
    {
      id: 'matches',
      icon: Target,
      title: 'Understand skill matches',
      description:
        'See clearly how your background aligns with role requirements, making mutual fit transparent and straightforward.',
    },
    {
      id: 'tracking',
      icon: Layers,
      title: 'Track your applications',
      description:
        'Keep track of your applications, assessment steps and hiring updates without losing sight of your next step.',
    },
  ];

  const containerVariants = {
    hidden: { opacity: shouldReduceMotion ? 1 : 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 18 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
    },
  };

  return (
    <section className="py-20 sm:py-28 relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Section Header */}
      <div className="text-center max-w-2xl mx-auto mb-14 sm:mb-16">
        <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-charcoal dark:text-ivory tracking-tight">
          Your profile, all in one place
        </h2>
        <p className="mt-3 text-sm sm:text-base text-slate/75 dark:text-ivory/70 font-normal leading-relaxed">
          Bring your experience, skills and qualifications together in one organised profile.
        </p>
      </div>

      {/* Four Feature Cards */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-40px' }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <motion.div key={feature.id} variants={itemVariants} className="h-full">
              <LiquidSpotlightCard className="p-6 sm:p-7 rounded-2xl h-full flex flex-col justify-between border border-slate/15 dark:border-rose/15 shadow-sm hover:border-oxblood/40 dark:hover:border-rose/30 transition-all duration-300">
                <div>
                  {/* Subtle Icon Surface */}
                  <div className="w-11 h-11 rounded-xl bg-oxblood/10 dark:bg-rose/10 text-oxblood dark:text-rose flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-105">
                    <Icon className="w-5 h-5" />
                  </div>

                  {/* Title & Description */}
                  <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory leading-snug">
                    {feature.title}
                  </h3>
                  <p className="mt-2.5 text-xs sm:text-sm text-slate/75 dark:text-ivory/70 leading-relaxed font-normal">
                    {feature.description}
                  </p>
                </div>
              </LiquidSpotlightCard>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
};
