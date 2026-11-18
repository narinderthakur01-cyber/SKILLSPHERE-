import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { jobsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  LiquidSpotlightCard,
  MagneticButton,
  SkeletonShimmer,
  usePrefersReducedMotion,
  gsap,
  ScrollTrigger,
  useGSAP
} from '../components/MotionComponents';
import {
  Search, MapPin, Briefcase, ArrowRight, ArrowUpRight,
  CheckCircle2, ShieldCheck, Compass, Target,
  FileText, Layers, Award, Code, Check, Clock
} from 'lucide-react';
import { LandingBackground } from '../components/landing/LandingBackground';
import { FeatureCardsSection } from '../components/landing/FeatureCardsSection';
import { ApplicationJourneySection } from '../components/landing/ApplicationJourneySection';

export const LandingPage = () => {
  const { user, role } = useAuth();
  const navigate = useNavigate();
  const landingRef = useRef(null);
  const activeStageRef = useRef(0);
  const shouldReduceMotion = usePrefersReducedMotion();

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeStoryStage, setActiveStoryStage] = useState(0);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await jobsAPI.list({ page_size: 6 });
      setJobs(res.data.items || []);
    } catch (err) {
      console.error("Error loading preview jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (user && role === 'JOB_SEEKER') {
      navigate(`/dashboard?tab=jobs&keyword=${encodeURIComponent(query)}`);
    } else {
      navigate(`/auth?mode=register&role=JOB_SEEKER`);
    }
  };

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: shouldReduceMotion ? 'auto' : 'smooth' });
    }
  };

  // ============================================================================
  // GSAP SCROLLTRIGGER & HERO TIMELINE ANIMATIONS
  // Restores original motion punch while fixing sticky/pinning scroll collisions
  // ============================================================================
  useGSAP(() => {
    if (shouldReduceMotion) return;

    // 1. Hero Entrance Reveal Timeline
    const heroTl = gsap.timeline({ defaults: { ease: "power3.out" } });
    heroTl
      .fromTo(
        ".hero-masked-line",
        { yPercent: 120, opacity: 0 },
        { yPercent: 0, opacity: 1, duration: 0.85, stagger: 0.16 }
      )
      .fromTo(".hero-subtitle", { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.65 }, "-=0.35")
      .fromTo(".hero-search-console", { opacity: 0, y: 22, scale: 0.98 }, { opacity: 1, y: 0, scale: 1, duration: 0.65 }, "-=0.3")
      .fromTo(".hero-cta-btn", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.12 }, "-=0.35");

    // 2. Subtle Parallax on Background Layer while scrolling past Hero
    gsap.to(".hero-parallax-layer", {
      yPercent: -12,
      ease: "none",
      scrollTrigger: {
        trigger: ".hero-section",
        start: "top top",
        end: "bottom top",
        scrub: true,
      },
    });

    // 3. Desktop Pinned Storytelling Motion (>= 1024px)
    // Fixes previous collision: NO position: sticky on children; cards stacked in deck;
    // Throttled state updates to prevent re-render thrashing during scroll.
    const mm = gsap.matchMedia();
    mm.add("(min-width: 1024px)", () => {
      const cards = gsap.utils.toArray(".story-deck-card");
      if (cards.length >= 3) {
        // Initial setup for cards 1 and 2
        gsap.set(cards[1], { opacity: 0, y: 50, scale: 0.95, pointerEvents: "none" });
        gsap.set(cards[2], { opacity: 0, y: 50, scale: 0.95, pointerEvents: "none" });

        const storyTimeline = gsap.timeline({
          scrollTrigger: {
            trigger: ".storytelling-section",
            start: "top 16%",
            end: "+=1200",
            pin: true,
            pinSpacing: true,
            anticipatePin: 1,
            scrub: 0.7,
            onUpdate: (self) => {
              const p = self.progress;
              const newStage = p < 0.35 ? 0 : p < 0.7 ? 1 : 2;
              if (newStage !== activeStageRef.current) {
                activeStageRef.current = newStage;
                setActiveStoryStage(newStage);
              }
            },
          },
        });

        storyTimeline
          // Stage 0 -> Stage 1
          .to(cards[0], { opacity: 0, y: -35, scale: 0.95, duration: 0.8, pointerEvents: "none" }, 0.2)
          .to(cards[1], { opacity: 1, y: 0, scale: 1, duration: 0.8, pointerEvents: "auto" }, 0.35)
          // Stage 1 -> Stage 2
          .to(cards[1], { opacity: 0, y: -35, scale: 0.95, duration: 0.8, pointerEvents: "none" }, 1.2)
          .to(cards[2], { opacity: 1, y: 0, scale: 1, duration: 0.8, pointerEvents: "auto" }, 1.35);
      }
    });

    return () => {
      mm.revert();
    };
  }, { scope: landingRef, dependencies: [shouldReduceMotion] });

  const storyStages = [
    {
      step: '01',
      title: 'Transparent Skill Alignment',
      tag: 'Clear Capability Overlap',
      description:
        'Review direct skill intersections and identify growth areas with full visibility into how your qualifications match role requirements.',
      highlights: ['Direct Competency Overlap', 'Strengths Highlighted', 'Actionable Guidance'],
    },
    {
      step: '02',
      title: 'Structured Evaluations',
      tag: 'Fair & Objective Review',
      description:
        'Engage with standardized evaluations designed to showcase your practical problem-solving ability in a fair, consistent environment.',
      highlights: ['Standardized Question Sets', 'Objective Scoring', 'Equal Opportunity Baseline'],
    },
    {
      step: '03',
      title: 'Verified Decision Pipeline',
      tag: 'Direct Communication',
      description:
        'Move through each hiring phase with transparent status updates, timely recruiter decisions, and direct interview scheduling.',
      highlights: ['Real-Time Status Updates', 'Direct Recruiter Review', 'Seamless Scheduling'],
    },
  ];

  return (
    <div ref={landingRef} className="min-h-screen flex flex-col font-sans transition-colors duration-300 overflow-x-hidden relative">
      
      {/* ======================================================== */}
      {/* HERO SECTION — CENTRALLY ALIGNED WITH MASKED TYPOGRAPHY   */}
      {/* ======================================================== */}
      <section className="hero-section relative pt-20 sm:pt-28 lg:pt-36 pb-24 sm:pb-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Continuous Moving Burgundy/Rose Gradient Mesh & Light Trails */}
        <div className="hero-parallax-layer absolute inset-0 -z-10 pointer-events-none">
          <LandingBackground />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          
          {/* MASKED EDITORIAL TYPOGRAPHY REVEAL */}
          <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-charcoal dark:text-ivory leading-[1.08]">
            <span className="block overflow-hidden pb-1">
              <span className="hero-masked-line inline-block">
                Precision Matching.
              </span>
            </span>
            <span className="block overflow-hidden mt-1 sm:mt-2">
              <span className="hero-masked-line inline-block text-oxblood dark:text-rose">
                Transparent Hiring.
              </span>
            </span>
          </h1>

          {/* SUPPORTING TEXT WITH ENTRANCE FADE & SLIDE */}
          <p className="hero-subtitle mt-6 sm:mt-8 text-base sm:text-lg lg:text-xl text-slate/80 dark:text-ivory/75 max-w-2xl mx-auto font-normal leading-relaxed">
            Discover opportunities. Connect with talent. Move forward with clarity.
          </p>

          {/* INTEGRATED REFINED SEARCH BAR */}
          <form
            onSubmit={handleSearch}
            className="hero-search-console mt-10 sm:mt-12 max-w-2xl mx-auto glass-card p-2 sm:p-2.5 rounded-2xl sm:rounded-full border border-slate/15 dark:border-rose/20 shadow-xl flex flex-col sm:flex-row items-center gap-2 backdrop-blur-2xl"
          >
            <div className="flex items-center flex-1 w-full px-4 py-2 min-h-[46px]">
              <Search className="w-4 h-4 text-oxblood dark:text-rose mr-3 shrink-0" />
              <input
                type="text"
                placeholder="Search by job title, skills or location"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full text-xs sm:text-sm bg-transparent focus:outline-none text-charcoal dark:text-ivory placeholder:text-slate/40 dark:placeholder:text-ivory/35 font-medium"
              />
            </div>

            <MagneticButton
              type="submit"
              className="w-full sm:w-auto px-7 py-3 btn-oxblood font-display font-semibold text-xs sm:text-sm rounded-xl sm:rounded-full transition shrink-0 flex items-center justify-center gap-2 shadow-md min-h-[46px]"
            >
              <span>Search</span>
              <ArrowRight className="w-4 h-4" />
            </MagneticButton>
          </form>

          {/* PRIMARY & SECONDARY CTA BUTTONS WITH MAGNETIC INTERACTIONS */}
          <div className="hero-cta-group mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <MagneticButton
              type="button"
              onClick={() => scrollToSection('featured-opportunities')}
              className="hero-cta-btn w-full sm:w-auto px-7 py-3.5 btn-oxblood font-display font-semibold text-xs sm:text-sm rounded-xl sm:rounded-full flex items-center justify-center gap-2 shadow-md hover:scale-[1.02] transition"
            >
              <span>Explore Opportunities</span>
              <ArrowRight className="w-4 h-4" />
            </MagneticButton>

            <MagneticButton
              type="button"
              onClick={() => scrollToSection('discover-section')}
              className="hero-cta-btn w-full sm:w-auto px-7 py-3.5 btn-secondary font-display font-semibold text-xs sm:text-sm rounded-xl sm:rounded-full flex items-center justify-center gap-2 transition"
            >
              <span>Discover SkillSphere</span>
            </MagneticButton>
          </div>

        </div>
      </section>

      {/* ======================================================== */}
      {/* SECTION 1: FEATURE CARDS — YOUR PROFILE, ALL IN ONE PLACE*/}
      {/* ======================================================== */}
      <div id="discover-section">
        <FeatureCardsSection />
      </div>

      {/* ======================================================== */}
      {/* SECTION 2: GSAP STORYTELLING — FIND THE RIGHT MATCH      */}
      {/* Pinned smoothly on desktop (>=1024px); natural stack on mobile */}
      {/* ======================================================== */}
      <section className="storytelling-section py-20 sm:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full border-t border-slate/10 dark:border-rose/10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
          
          {/* Left Column: Narrative & Interactive Stage Indicators */}
          <div className="lg:col-span-5 flex flex-col justify-center">
            <span className="font-mono text-xs uppercase tracking-wider text-oxblood dark:text-rose font-semibold mb-2">
              DISCOVERY & MATCHING
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-charcoal dark:text-ivory tracking-tight leading-tight">
              Find the right match
            </h2>
            <p className="text-sm sm:text-base text-slate/80 dark:text-ivory/70 mt-3 font-normal leading-relaxed">
              Explore opportunities based on your skills and see how your experience aligns with what employers are looking for.
            </p>

            {/* Stage Progress Indicators (Desktop Interactive) */}
            <div className="hidden lg:flex flex-col gap-3 mt-8 pt-6 border-t border-slate/15 dark:border-rose/15 font-mono text-xs">
              {storyStages.map((stage, idx) => (
                <div
                  key={stage.step}
                  className={`flex items-center gap-3 p-3.5 rounded-2xl transition-all duration-300 ${
                    activeStoryStage === idx
                      ? 'bg-oxblood/15 dark:bg-rose/10 border border-oxblood/40 dark:border-rose/30 text-charcoal dark:text-ivory font-bold shadow-xs'
                      : 'text-slate/60 dark:text-ivory/50 border border-transparent'
                  }`}
                >
                  <span
                    className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-colors ${
                      activeStoryStage === idx
                        ? 'bg-oxblood text-ivory'
                        : 'bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-ivory/60'
                    }`}
                  >
                    {stage.step}
                  </span>
                  <div className="flex flex-col">
                    <span className="text-xs font-medium">{stage.title}</span>
                    <span className="text-[10px] opacity-70 font-normal">{stage.tag}</span>
                  </div>
                  {activeStoryStage === idx && (
                    <span className="ml-auto w-2 h-2 rounded-full bg-oxblood animate-pulse" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Story Cards Deck */}
          {/* On Desktop: Positioned inside a fixed-height deck for smooth scrub morphing */}
          {/* On Mobile/Tablet: Stacked vertically with natural scrolling */}
          <div className="lg:col-span-7 relative min-h-[420px] sm:min-h-[460px]">
            
            {/* STAGE 01 CARD: SKILL ALIGNMENT */}
            <div className="story-deck-card lg:absolute lg:inset-0 glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col justify-between transition-all duration-300 mb-6 lg:mb-0">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate/10 dark:border-rose/10 mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-oxblood text-ivory flex items-center justify-center font-mono font-bold text-sm shadow-xs">
                      01
                    </div>
                    <div>
                      <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">Transparent Skill Alignment</h3>
                      <p className="text-[11px] font-mono text-oxblood dark:text-rose font-medium">Clear Capability Overlap</p>
                    </div>
                  </div>
                  <span className="badge-selected text-[10px] font-mono px-2.5 py-1 rounded-full uppercase font-bold">
                    ALIGNMENT
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-slate/80 dark:text-ivory/70 leading-relaxed font-normal">
                  Review direct skill intersections and identify growth areas with full visibility into how your qualifications match role requirements, helping you focus on the right opportunities.
                </p>

                {/* Visual Alignment Mock */}
                <div className="mt-5 p-4 rounded-2xl bg-charcoal/95 text-ivory font-mono text-[11px] border border-white/10 shadow-inner">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-3 text-rose">
                    <span className="flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5" />
                      <span>CAPABILITY_ALIGNMENT</span>
                    </span>
                    <span className="text-emerald-400 font-bold">MUTUAL FIT</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px]">
                    <div className="p-2 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
                      ✓ Core Match: React, TypeScript, APIs
                    </div>
                    <div className="p-2 rounded-lg bg-oxblood/20 border border-oxblood/40 text-rose">
                      • Growth Focus: Cloud Infrastructure
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-oxblood dark:text-rose font-medium">
                <span>Direct Overlap Analysis</span>
                <span className="text-slate/60 dark:text-ivory/50">Informed Career Decisions</span>
              </div>
            </div>

            {/* STAGE 02 CARD: STRUCTURED EVALUATIONS */}
            <div className="story-deck-card lg:absolute lg:inset-0 glass-card p-6 sm:p-8 rounded-3xl border border-oxblood/30 dark:border-rose/30 shadow-xl flex flex-col justify-between transition-all duration-300 mb-6 lg:mb-0">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate/10 dark:border-rose/10 mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-oxblood text-ivory flex items-center justify-center font-mono font-bold text-sm shadow-xs">
                      02
                    </div>
                    <div>
                      <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">Structured Evaluations</h3>
                      <p className="text-[11px] font-mono text-oxblood dark:text-rose font-medium">Fair & Objective Review</p>
                    </div>
                  </div>
                  <span className="badge-oxblood text-[10px] font-mono px-2.5 py-1 rounded-full uppercase font-bold">
                    EVALUATION
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-slate/80 dark:text-ivory/70 leading-relaxed font-normal">
                  Engage with standardized evaluations designed to showcase your practical problem-solving ability in a fair, consistent environment, giving employers an objective baseline.
                </p>

                {/* Visual Assessment Progress Mock */}
                <div className="mt-5 p-4 rounded-2xl bg-charcoal/95 text-ivory font-mono text-[11px] border border-white/10 shadow-inner">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-3 text-rose">
                    <span className="flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5" />
                      <span>ASSESSMENT_SCORECARD</span>
                    </span>
                    <span className="text-emerald-400 font-bold">OBJECTIVE</span>
                  </div>
                  <div className="space-y-1.5 text-[10px] text-warmivory/80">
                    <p>• Role-Relevant Question Sets: Complete</p>
                    <p>• Practical Engineering Knowledge: Validated</p>
                    <p>• Fair Baseline Evaluation: Verified</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-oxblood dark:text-rose font-medium">
                <span>Equal Opportunity Baseline</span>
                <span className="text-slate/60 dark:text-ivory/50">Merit-First Hiring</span>
              </div>
            </div>

            {/* STAGE 03 CARD: VERIFIED DECISION PIPELINE */}
            <div className="story-deck-card lg:absolute lg:inset-0 glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col justify-between transition-all duration-300">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate/10 dark:border-rose/10 mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-oxblood text-ivory flex items-center justify-center font-mono font-bold text-sm shadow-xs">
                      03
                    </div>
                    <div>
                      <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">Verified Decision Pipeline</h3>
                      <p className="text-[11px] font-mono text-oxblood dark:text-rose font-medium">Direct Communication</p>
                    </div>
                  </div>
                  <span className="badge-selected text-[10px] font-mono px-2.5 py-1 rounded-full uppercase font-bold">
                    DECISION
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-slate/80 dark:text-ivory/70 leading-relaxed font-normal">
                  Move through each hiring phase with transparent status updates, timely recruiter decisions, and direct interview scheduling without unnecessary intermediaries.
                </p>

                {/* Visual Pipeline States */}
                <div className="mt-5 p-4 rounded-2xl bg-charcoal/95 text-ivory font-mono text-[11px] border border-white/10 shadow-inner">
                  <div className="flex items-center gap-1.5 text-rose pb-2 border-b border-white/10 mb-3">
                    <Clock className="w-3.5 h-3.5" />
                    <span>LIFECYCLE_PROGRESS</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="px-2 py-1 rounded-md bg-white/10 text-ivory">APPLIED</span>
                    <span className="text-oxblood">→</span>
                    <span className="px-2 py-1 rounded-md bg-white/10 text-ivory">ASSESSMENT</span>
                    <span className="text-oxblood">→</span>
                    <span className="px-2 py-1 rounded-md bg-rose/20 text-rose font-bold">UNDER_REVIEW</span>
                    <span className="text-oxblood">→</span>
                    <span className="px-2 py-1 rounded-md bg-emerald-500/20 text-emerald-300 font-bold">DECISION</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-oxblood dark:text-rose font-medium">
                <span>Timely Feedback</span>
                <span className="text-slate/60 dark:text-ivory/50">Clear Next Steps</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ======================================================== */}
      {/* SECTION 3: APPLICATION JOURNEY TIMELINE                  */}
      {/* ======================================================== */}
      <ApplicationJourneySection />

      {/* ======================================================== */}
      {/* SECTION 4: FEATURED OPPORTUNITIES                        */}
      {/* Real API data with refined cards & safe fallbacks        */}
      {/* ======================================================== */}
      <section
        id="featured-opportunities"
        className="py-20 sm:py-28 border-t border-slate/15 dark:border-rose/15 bg-slate/5 dark:bg-slate/20 relative"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mb-12">
            <div>
              <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-charcoal dark:text-ivory">
                Opportunities worth exploring
              </h2>
              <p className="mt-2 text-xs sm:text-sm text-slate/75 dark:text-ivory/70">
                Discover roles, explore new possibilities and take the next step in your career.
              </p>
            </div>
            <Link
              to={user && role === 'JOB_SEEKER' ? "/dashboard?tab=jobs" : "/auth"}
              className="text-xs font-mono font-bold text-oxblood dark:text-rose hover:underline flex items-center gap-1.5 transition underline-offset-4 min-h-[44px]"
            >
              <span>View all open roles</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((n) => (
                <div key={n} className="p-6 glass-card rounded-2xl border border-slate/15 dark:border-rose/15 h-60 flex flex-col justify-between">
                  <div>
                    <SkeletonShimmer height="h-4" className="w-1/3 mb-3" />
                    <SkeletonShimmer height="h-6" className="w-3/4 mb-4" />
                    <SkeletonShimmer height="h-4" className="w-1/2 mb-5" />
                    <div className="flex gap-2">
                      <SkeletonShimmer height="h-6" className="w-16" />
                      <SkeletonShimmer height="h-6" className="w-20" />
                      <SkeletonShimmer height="h-6" className="w-14" />
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate/10 dark:border-rose/10 flex justify-between items-center">
                    <SkeletonShimmer height="h-5" className="w-24" />
                    <SkeletonShimmer height="h-8" className="w-20 rounded-xl" />
                  </div>
                </div>
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-16 glass-card rounded-2xl p-8 max-w-xl mx-auto border border-slate/15 dark:border-rose/15 shadow-sm">
              <Briefcase className="w-10 h-10 text-slate/40 dark:text-ivory/40 mx-auto mb-3" />
              <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory">
                No active openings published right now
              </h3>
              <p className="text-xs text-slate/60 dark:text-ivory/60 mt-1 max-w-sm mx-auto">
                New roles are added regularly. Create your profile to stay notified when matching positions open.
              </p>
              <Link
                to="/auth?mode=register&role=JOB_SEEKER"
                className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 btn-oxblood font-display text-xs font-semibold rounded-xl"
              >
                <span>Create your profile</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job) => (
                <LiquidSpotlightCard
                  key={job.id}
                  className="p-6 sm:p-7 rounded-2xl flex flex-col justify-between border border-slate/15 dark:border-rose/15 shadow-sm group hover:border-oxblood/40 dark:hover:border-rose/30 transition-all duration-300"
                >
                  <div>
                    {/* Company & Job Type */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <span className="font-mono text-[10px] font-bold text-oxblood dark:text-rose uppercase tracking-wider block truncate">
                          {job.company?.company_name || "Verified Employer"}
                        </span>
                        <h3 className="font-display font-bold text-charcoal dark:text-ivory text-base sm:text-lg mt-1 leading-snug group-hover:text-oxblood dark:group-hover:text-rose transition-colors duration-200 truncate">
                          {job.title}
                        </h3>
                      </div>
                      {job.job_type && (
                        <span className="badge-slate text-[10px] uppercase font-mono font-bold px-2.5 py-1 rounded-full shrink-0">
                          {job.job_type.replace('_', ' ')}
                        </span>
                      )}
                    </div>

                    {/* Location & Experience */}
                    <div className="mt-3 flex items-center gap-2 text-xs font-mono text-slate/70 dark:text-ivory/70">
                      <span className="flex items-center gap-1 truncate">
                        <MapPin className="w-3.5 h-3.5 text-oxblood dark:text-rose shrink-0" />
                        <span className="truncate">{job.location || 'Location upon inquiry'}</span>
                      </span>
                      {job.experience_min !== undefined && job.experience_max !== undefined && (
                        <>
                          <span>•</span>
                          <span className="shrink-0">{job.experience_min} - {job.experience_max} yrs</span>
                        </>
                      )}
                    </div>

                    {/* Skill Tags */}
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-1.5">
                        {job.required_skills.slice(0, 4).map((sk, idx) => (
                          <span
                            key={idx}
                            className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate/10 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-charcoal dark:text-ivory font-medium"
                          >
                            {sk}
                          </span>
                        ))}
                        {job.required_skills.length > 4 && (
                          <span className="text-[11px] font-mono text-slate/60 dark:text-ivory/40 px-1 py-0.5">
                            +{job.required_skills.length - 4} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Footer: Compensation & Apply Button */}
                  <div className="mt-6 pt-4 border-t border-slate/15 dark:border-rose/15 flex justify-between items-center">
                    <div>
                      <span className="block text-[10px] font-mono uppercase text-slate/60 dark:text-ivory/40 font-medium">
                        Compensation
                      </span>
                      <span className="font-mono text-xs sm:text-sm font-bold text-charcoal dark:text-ivory">
                        {job.salary_min && job.salary_max
                          ? `₹${(job.salary_min/100000).toFixed(1)}L - ₹${(job.salary_max/100000).toFixed(1)}L`
                          : "Competitive"}
                      </span>
                    </div>
                    <Link
                      to={user && role === 'JOB_SEEKER' ? `/dashboard?tab=jobs&jobId=${job.id}` : "/auth"}
                      className="px-4 py-2.5 btn-secondary font-display font-semibold text-xs rounded-xl flex items-center gap-1.5 transition min-h-[44px] group-hover:border-oxblood/40"
                    >
                      <span>Apply</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </LiquidSpotlightCard>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ======================================================== */}
      {/* REFINED EDITORIAL FOOTER                                 */}
      {/* ======================================================== */}
      <footer className="mt-auto border-t border-slate/15 dark:border-rose/15 bg-charcoal text-ivory py-12 px-4 sm:px-6 lg:px-8 font-mono text-xs">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-oxblood text-ivory flex items-center justify-center font-display font-black text-xs">
              S
            </div>
            <span className="font-display font-bold text-sm tracking-tight text-ivory">SkillSphere</span>
          </div>

          <p className="text-ivory/60 text-center md:text-left">
            © 2026 SkillSphere. All rights reserved.
          </p>

          <div className="flex items-center gap-5 text-ivory/60">
            <span className="hover:text-ivory transition cursor-pointer">Security</span>
            <span className="hover:text-ivory transition cursor-pointer">Terms</span>
            <span className="hover:text-ivory transition cursor-pointer">Privacy</span>
          </div>
        </div>
      </footer>

    </div>
  );
};
