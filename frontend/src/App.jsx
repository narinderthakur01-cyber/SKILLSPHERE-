import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider, PageTransitionWrapper } from './components/MotionComponents';
import { Navbar } from './components/Navbar';
import { AnimatedBackground } from './components/AnimatedBackground';
import { ProtectedRoute } from './components/ProtectedRoute';

// Route-level code splitting via React.lazy
const LandingPage = React.lazy(() =>
  import('./pages/LandingPage').then((m) => ({ default: m.LandingPage }))
);
const AuthPage = React.lazy(() =>
  import('./pages/AuthPage').then((m) => ({ default: m.AuthPage }))
);
const ForgotPasswordPage = React.lazy(() =>
  import('./pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage }))
);
const ResetPasswordPage = React.lazy(() =>
  import('./pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage }))
);
const VerificationPendingPage = React.lazy(() =>
  import('./pages/VerificationPendingPage').then((m) => ({ default: m.VerificationPendingPage }))
);
const VerifyEmailPage = React.lazy(() =>
  import('./pages/VerifyEmailPage').then((m) => ({ default: m.VerifyEmailPage }))
);
const JobSeekerDashboard = React.lazy(() =>
  import('./pages/JobSeekerDashboard').then((m) => ({ default: m.JobSeekerDashboard }))
);
const CandidateAssessmentTestPage = React.lazy(() =>
  import('./pages/CandidateAssessmentTestPage').then((m) => ({ default: m.CandidateAssessmentTestPage }))
);
const RecruiterDashboard = React.lazy(() =>
  import('./pages/RecruiterDashboard').then((m) => ({ default: m.RecruiterDashboard }))
);
const AdminDashboard = React.lazy(() =>
  import('./pages/AdminDashboard').then((m) => ({ default: m.AdminDashboard }))
);
const VideoInterviewRoomPage = React.lazy(() =>
  import('./pages/VideoInterviewRoomPage').then((m) => ({ default: m.VideoInterviewRoomPage }))
);
const CandidateVideoAssessmentPage = React.lazy(() =>
  import('./pages/CandidateVideoAssessmentPage').then((m) => ({ default: m.CandidateVideoAssessmentPage }))
);
const AssistantPage = React.lazy(() =>
  import('./pages/AssistantPage').then((m) => ({ default: m.AssistantPage }))
);
import { ChatWidget } from './components/chatbot/ChatWidget';

/**
 * Editorial Branded Route Fallback
 * Prevents layout shifts while code-split chunks hydrate
 */
const RouteFallback = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center font-mono text-xs">
    <div className="w-8 h-8 rounded-full border-2 border-oxblood/30 border-t-oxblood animate-spin mb-3" />
    <span className="text-slate/60 dark:text-ivory/50 uppercase tracking-wider text-[10px]">
      Loading View...
    </span>
  </div>
);

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <Suspense fallback={<RouteFallback />}>
        <Routes location={location} key={location.pathname}>
          {/* Public Routes */}
          <Route
            path="/"
            element={
              <PageTransitionWrapper key="landing-route">
                <LandingPage />
              </PageTransitionWrapper>
            }
          />
          <Route
            path="/auth"
            element={
              <PageTransitionWrapper key="auth-route">
                <AuthPage />
              </PageTransitionWrapper>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <PageTransitionWrapper key="forgot-password-route">
                <ForgotPasswordPage />
              </PageTransitionWrapper>
            }
          />
          <Route
            path="/reset-password"
            element={
              <PageTransitionWrapper key="reset-password-route">
                <ResetPasswordPage />
              </PageTransitionWrapper>
            }
          />
          <Route
            path="/verify-email-pending"
            element={
              <PageTransitionWrapper key="verify-email-pending-route">
                <VerificationPendingPage />
              </PageTransitionWrapper>
            }
          />
          <Route
            path="/verify-email"
            element={
              <PageTransitionWrapper key="verify-email-route">
                <VerifyEmailPage />
              </PageTransitionWrapper>
            }
          />

          {/* Protected Job Seeker Dashboard */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={['JOB_SEEKER']}>
                <PageTransitionWrapper key="dashboard-route">
                  <JobSeekerDashboard />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/assessment/:assignmentId"
            element={
              <ProtectedRoute allowedRoles={['JOB_SEEKER']}>
                <PageTransitionWrapper key="assessment-test-route">
                  <CandidateAssessmentTestPage />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/video-assessment/:assignmentId"
            element={
              <ProtectedRoute allowedRoles={['JOB_SEEKER', 'ADMIN']}>
                <PageTransitionWrapper key="video-assessment-route">
                  <CandidateVideoAssessmentPage />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/interview-room/:interviewId"
            element={
              <ProtectedRoute allowedRoles={['JOB_SEEKER', 'RECRUITER', 'ADMIN']}>
                <PageTransitionWrapper key="interview-room-route">
                  <VideoInterviewRoomPage />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />

          {/* Protected Recruiter Dashboard */}
          <Route
            path="/recruiter"
            element={
              <ProtectedRoute allowedRoles={['RECRUITER']}>
                <PageTransitionWrapper key="recruiter-route">
                  <RecruiterDashboard />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />

          {/* Protected Admin Dashboard */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <PageTransitionWrapper key="admin-route">
                  <AdminDashboard />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />

          {/* Protected Assistant Portal */}
          <Route
            path="/assistant"
            element={
              <ProtectedRoute allowedRoles={['JOB_SEEKER', 'RECRUITER', 'ADMIN']}>
                <PageTransitionWrapper key="assistant-route">
                  <AssistantPage />
                </PageTransitionWrapper>
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AnimatePresence>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <div className="min-h-screen flex flex-col font-sans relative selection:bg-oxblood/30 selection:text-charcoal dark:selection:text-ivory">
              <AnimatedBackground />
              <Navbar />
              <main className="flex-1">
                <AnimatedRoutes />
              </main>
              <ChatWidget />
            </div>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
