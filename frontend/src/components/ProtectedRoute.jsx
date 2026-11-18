import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, role, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin"></div>
          <p className="text-sm font-medium text-slate-500">Loading SkillSphere...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  // Enforce email verification for candidates and recruiters (ADMIN exempt)
  if (role !== 'ADMIN' && user.email_verified === false) {
    return <Navigate to={`/verify-email-pending?email=${encodeURIComponent(user.email || '')}`} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    // If logged in but unauthorized for this specific role route, redirect to their home
    if (role === 'JOB_SEEKER') return <Navigate to="/dashboard" replace />;
    if (role === 'RECRUITER') return <Navigate to="/recruiter" replace />;
    if (role === 'ADMIN') return <Navigate to="/admin" replace />;
    return <Navigate to="/" replace />;
  }

  return children;
};
