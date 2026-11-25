import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, MessageSquare, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ChatWindow } from './ChatWindow';

export const ChatWidget = () => {
  const { user, role } = useAuth();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  // Suppress chatbot on unauthenticated views and distraction-sensitive routes
  if (!user) return null;

  const currentPath = location.pathname;
  const isHiddenRoute = (
    currentPath === '/' ||
    currentPath.startsWith('/auth') ||
    currentPath.startsWith('/forgot-password') ||
    currentPath.startsWith('/reset-password') ||
    currentPath.startsWith('/verify-email') ||
    currentPath.startsWith('/assessment/') ||
    currentPath.startsWith('/video-assessment/') ||
    currentPath.startsWith('/interview-room/') ||
    currentPath === '/assistant' // Hide floating widget on the dedicated Assistant page itself
  );

  if (isHiddenRoute) return null;

  return (
    <div className="fixed bottom-5 right-5 z-40 print:hidden">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 350 }}
            className="mb-3 origin-bottom-right"
          >
            <ChatWindow onClose={() => setIsOpen(false)} isFullPage={false} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Toggle Button */}
      <motion.button
        type="button"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-14 h-14 rounded-full bg-gradient-to-br from-oxblood to-oxblood-600 text-white shadow-xl hover:shadow-2xl flex items-center justify-center transition-all duration-200 border-2 border-white/30 dark:border-white/20 group focus:outline-none focus:ring-4 focus:ring-oxblood/40 liquid-metal-pill"
        title={isOpen ? 'Close Assistant' : 'Open SkillSphere Assistant'}
        aria-label="Toggle SkillSphere Assistant"
      >
        <AnimatePresence mode="wait" initial={false}>
          {isOpen ? (
            <motion.div
              key="close-icon"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <X className="w-6 h-6" />
            </motion.div>
          ) : (
            <motion.div
              key="bot-icon"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="relative"
            >
              <Bot className="w-6 h-6" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-oxblood animate-pulse" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
};
