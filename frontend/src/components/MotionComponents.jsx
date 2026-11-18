import React, { useEffect, useState, useRef, createContext, useContext } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';

// Register GSAP ScrollTrigger plugin once safely on client side
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export { gsap, ScrollTrigger, useGSAP };

/**
 * Universal Reduced Motion Hook
 */
export const usePrefersReducedMotion = () => {
  return useReducedMotion() ?? false;
};

/**
 * PageTransitionWrapper (with backward-compatible PageTransition alias)
 * Hardware-accelerated exit and entrance coordinates with AnimatePresence
 */
export const PageTransitionWrapper = ({ children, className = '' }) => {
  const shouldReduceMotion = usePrefersReducedMotion();

  const variants = {
    initial: shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 12 },
    animate: shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 },
    exit: shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 },
  };

  return (
    <motion.div
      variants={variants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{
        duration: shouldReduceMotion ? 0.1 : 0.32,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
};
export const PageTransition = PageTransitionWrapper;

/**
 * StaggerContainer & StaggerItem
 * Coordinated list & grid animation utilizing Framer Motion's layout engine
 */
export const StaggerContainer = ({
  children,
  staggerDelay = 0.05,
  delayChildren = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = usePrefersReducedMotion();

  const containerVariants = {
    hidden: { opacity: shouldReduceMotion ? 1 : 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : staggerDelay,
        delayChildren: shouldReduceMotion ? 0 : delayChildren,
      },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem = ({ children, className = '', ...props }) => {
  const shouldReduceMotion = usePrefersReducedMotion();

  const itemVariants = {
    hidden: shouldReduceMotion
      ? { opacity: 0 }
      : { opacity: 0, y: 14, scale: 0.98 },
    visible: shouldReduceMotion
      ? { opacity: 1 }
      : {
          opacity: 1,
          y: 0,
          scale: 1,
          transition: {
            duration: 0.38,
            ease: [0.16, 1, 0.3, 1],
          },
        },
  };

  return (
    <motion.div
      variants={itemVariants}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

/**
 * Animated Numerical Counter
 * Transitions numbers smoothly from 0 to value using requestAnimationFrame
 */
export const AnimatedCounter = ({
  value,
  duration = 1200,
  prefix = '',
  suffix = '',
  autoStart = true
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const endValue = Number(value) || 0;
  const shouldReduceMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion) {
      setDisplayValue(endValue);
      return;
    }
    if (!autoStart) return;

    let startTimestamp = null;
    const startValue = 0;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      // Ease out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(startValue + (endValue - startValue) * easedProgress);
      setDisplayValue(current);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        setDisplayValue(endValue);
      }
    };

    const animFrame = window.requestAnimationFrame(step);
    return () => window.cancelAnimationFrame(animFrame);
  }, [value, duration, autoStart, shouldReduceMotion, endValue]);

  return (
    <span>
      {prefix}
      {displayValue}
      {suffix}
    </span>
  );
};

/**
 * Transform-based Progress Bar
 * Uses transform: scaleX() and transformOrigin: left to prevent expensive layout recalculations
 */
export const AnimatedProgressBar = ({
  progress = 0,
  height = 'h-2',
  color = 'bg-oxblood',
  bgColor = 'bg-slate/10 dark:bg-rose/10',
  className = ''
}) => {
  const shouldReduceMotion = usePrefersReducedMotion();
  const validProgress = Math.min(Math.max(progress || 0, 0), 100) / 100;

  return (
    <div className={`w-full ${height} ${bgColor} rounded-full overflow-hidden relative ${className}`}>
      <motion.div
        className={`h-full ${color} rounded-full origin-left`}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: validProgress }}
        transition={{
          duration: shouldReduceMotion ? 0.1 : 0.8,
          ease: [0.16, 1, 0.3, 1],
        }}
      />
    </div>
  );
};

/**
 * Animated SVG Progress Ring
 * Renders stroke-dashoffset transition for compatibility match score and completeness
 */
export const AnimatedProgressRing = ({
  percentage = 0,
  size = 72,
  strokeWidth = 6,
  color = '#914F51',
  bgColor = 'rgba(197, 164, 155, 0.15)',
  children
}) => {
  const shouldReduceMotion = usePrefersReducedMotion();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const validPercentage = Math.min(Math.max(percentage || 0, 0), 100);
  const strokeDashoffset = circumference - (validPercentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={bgColor}
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: shouldReduceMotion ? strokeDashoffset : circumference }}
          animate={{ strokeDashoffset }}
          transition={{
            duration: shouldReduceMotion ? 0.1 : 1.2,
            ease: [0.16, 1, 0.3, 1]
          }}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        {children || (
          <span className="font-mono font-bold text-xs">
            {validPercentage}%
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * GPU-Accelerated Skeleton Shimmer
 * Transforms an overlay gradient to signal loading states without layout shifts
 */
export const SkeletonShimmer = ({ className = '', height = 'h-5', rounded = 'rounded-xl' }) => {
  return (
    <div
      className={`relative overflow-hidden bg-slate/10 dark:bg-white/5 ${height} ${rounded} ${className}`}
      aria-hidden="true"
    >
      <motion.div
        className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 dark:via-white/5 to-transparent"
        animate={{ translateX: ['100%', '-100%'] }}
        transition={{
          repeat: Infinity,
          duration: 1.6,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
};

/**
 * StatusTransitionBadge
 * Smooth morphing status badge with spring physics
 */
export const StatusTransitionBadge = ({ status, className = '', children }) => {
  return (
    <motion.span
      layout
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 28 }}
      className={`inline-flex items-center gap-1.5 ${className}`}
    >
      {children || status}
    </motion.span>
  );
};

/**
 * Spring-based Liquid Glass Modal
 */
export const AnimatedModal = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'max-w-2xl'
}) => {
  const shouldReduceMotion = usePrefersReducedMotion();

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
          {/* Backdrop Blur Layer */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-charcoal/80 dark:bg-black/85 backdrop-blur-md"
          />

          {/* Modal Surface */}
          <motion.div
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.94, y: 16 }}
            animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 10 }}
            transition={{ type: 'spring', damping: 28, stiffness: 340 }}
            className={`relative w-full ${maxWidth} glass-surface-elevated rounded-3xl p-6 sm:p-8 border border-slate/15 dark:border-rose/20 shadow-2xl z-10 max-h-[90vh] overflow-y-auto`}
            role="dialog"
            aria-modal="true"
          >
            <button
              onClick={onClose}
              className="absolute top-5 right-5 p-2 rounded-full text-charcoal/60 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory hover:bg-slate/10 dark:hover:bg-white/10 transition"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>

            {title && (
              <div className="pr-10 mb-5">
                <h3 className="font-display text-xl sm:text-2xl font-bold text-charcoal dark:text-ivory">
                  {title}
                </h3>
                {subtitle && (
                  <p className="text-xs text-slate/70 dark:text-ivory/60 mt-1">{subtitle}</p>
                )}
              </div>
            )}

            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
export const GlassModal = AnimatedModal;

/**
 * Slide-in Animated Drawer
 * Responsive drawer from right or bottom with backdrop blur
 */
export const AnimatedDrawer = ({
  isOpen,
  onClose,
  title,
  children,
  side = 'right'
}) => {
  const isRight = side === 'right';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-charcoal/80 dark:bg-black/85 backdrop-blur-sm"
          />

          <motion.div
            initial={isRight ? { x: '100%' } : { y: '100%' }}
            animate={isRight ? { x: 0 } : { y: 0 }}
            exit={isRight ? { x: '100%' } : { y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 350 }}
            className={`relative z-10 ${
              isRight ? 'h-full w-full max-w-md border-l' : 'w-full max-h-[85vh] border-t rounded-t-3xl'
            } glass-surface-elevated border-slate/15 dark:border-rose/20 p-6 overflow-y-auto shadow-2xl`}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate/10 dark:border-rose/10 mb-4">
              <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">{title}</h3>
              <button
                onClick={onClose}
                className="p-1.5 rounded-xl hover:bg-slate/10 dark:hover:bg-white/10 text-charcoal/60 dark:text-ivory/60 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

/**
 * LiquidSpotlightCard
 * Cursor-following radial caustic highlight on desktop with hover lift
 */
export const LiquidSpotlightCard = ({
  children,
  className = '',
  onClick,
  ...props
}) => {
  const cardRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const shouldReduceMotion = usePrefersReducedMotion();

  const handleMouseMove = (e) => {
    if (!cardRef.current || shouldReduceMotion) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const handleMouseLeave = () => {
    setMousePos({ x: -1000, y: -1000 });
  };

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      whileHover={shouldReduceMotion ? {} : { y: -3 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className={`relative glass-card overflow-hidden ${className}`}
      {...props}
    >
      {/* Specular dynamic spotlight layer */}
      <div
        className="pointer-events-none absolute -inset-px transition-opacity duration-300 opacity-0 group-hover:opacity-100 dark:block hidden"
        style={{
          opacity: mousePos.x > 0 ? 0.35 : 0,
          background: `radial-gradient(320px circle at ${mousePos.x}px ${mousePos.y}px, rgba(145, 79, 81, 0.35), transparent 70%)`,
        }}
      />
      <div
        className="pointer-events-none absolute -inset-px transition-opacity duration-300 opacity-0 group-hover:opacity-100 dark:hidden block"
        style={{
          opacity: mousePos.x > 0 ? 0.25 : 0,
          background: `radial-gradient(280px circle at ${mousePos.x}px ${mousePos.y}px, rgba(145, 79, 81, 0.18), transparent 70%)`,
        }}
      />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
};

/**
 * MagneticButton
 * Subtle pointer magnetic pull for desktop primary actions; disabled on touch
 */
export const MagneticButton = ({
  children,
  className = '',
  onClick,
  strength = 14,
  ...props
}) => {
  const btnRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const shouldReduceMotion = usePrefersReducedMotion();

  const handleMouseMove = (e) => {
    if (!btnRef.current || shouldReduceMotion) return;
    const { clientX, clientY } = e;
    const { left, top, width, height } = btnRef.current.getBoundingClientRect();
    const x = ((clientX - (left + width / 2)) / (width / 2)) * strength;
    const y = ((clientY - (top + height / 2)) / (height / 2)) * strength;
    setPosition({ x, y });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.button
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      animate={shouldReduceMotion ? { x: 0, y: 0 } : { x: position.x, y: position.y }}
      transition={{ type: 'spring', stiffness: 220, damping: 18 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.96 }}
      className={className}
      {...props}
    >
      {children}
    </motion.button>
  );
};

/**
 * ToastNotification Manager & Hook
 */
const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (messageOrObj, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random();
    let text = messageOrObj;
    let toastType = type;
    if (typeof messageOrObj === 'object' && messageOrObj !== null) {
      text = messageOrObj.title || messageOrObj.message || String(messageOrObj);
      toastType = messageOrObj.type || type;
    }
    setToasts((prev) => [...prev, { id, message: String(text), type: toastType }]);
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 15, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 350, damping: 28 }}
              className={`pointer-events-auto p-4 rounded-2xl border shadow-xl flex items-center gap-3 backdrop-blur-xl ${
                toast.type === 'success'
                  ? 'bg-success-50/90 dark:bg-charcoal/90 text-charcoal dark:text-ivory border-success/40'
                  : toast.type === 'error'
                  ? 'bg-danger-50/90 dark:bg-charcoal/90 text-charcoal dark:text-ivory border-danger/40'
                  : 'bg-warmivory/90 dark:bg-charcoal/90 text-charcoal dark:text-ivory border-slate/20 dark:border-rose/20'
              }`}
            >
              {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-success shrink-0" />}
              {toast.type === 'error' && <AlertCircle className="w-4 h-4 text-danger shrink-0" />}
              {toast.type === 'info' && <Info className="w-4 h-4 text-oxblood dark:text-rose shrink-0" />}
              <span className="text-xs font-medium flex-1">{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 text-slate/50 dark:text-rose/50"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    return {
      addToast: (msg) => console.log('Toast:', msg),
    };
  }
  return context;
};
