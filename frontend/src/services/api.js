import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api/v1` 
    : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('skillsphere_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401s
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('skillsphere_token');
      localStorage.removeItem('skillsphere_user');
      if (window.location.pathname !== '/' && window.location.pathname !== '/auth') {
        window.location.href = '/auth';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  resendResetEmail: (email) => api.post('/auth/resend-reset-email', { email }),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  verifyEmailGet: (token) => api.get('/auth/verify-email', { params: { token } }),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
  getVerificationStatus: (email) => api.get('/auth/verification-status', { params: { email } }),
};

export const resumeAPI = {
  upload: (formData) => api.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getProfile: () => api.get('/resume/profile'),
  updateProfile: (data) => api.put('/resume/profile', data),
  getMyResumes: () => api.get('/resume/my-resumes'),
  analyze: (data) => api.post('/resume/analyze', data),
  getQualityFeedback: (jobId) => api.post('/resume/quality-feedback', null, {
    params: jobId ? { job_id: jobId } : {}
  }),
  downloadUrl: (id) => `/api/v1/resume/${id}/download`,
};

export const jobsAPI = {
  list: (params) => api.get('/jobs', { params }),
  get: (id) => api.get(`/jobs/${id}`),
  create: (data) => api.post('/jobs', data),
  update: (id, data) => api.put(`/jobs/${id}`, data),
  delete: (id) => api.delete(`/jobs/${id}`),
};

export const savedJobsAPI = {
  list: () => api.get('/saved-jobs'),
  save: (jobId) => api.post(`/saved-jobs/${jobId}`),
  unsave: (jobId) => api.delete(`/saved-jobs/${jobId}`),
  getRecommendations: () => api.get('/jobs/recommendations'),
};

export const applicationAPI = {
  apply: (jobId, data) => api.post(`/jobs/${jobId}/apply`, data),
  getMyApplications: () => api.get('/applications'),
  withdraw: (applicationId) => api.put(`/applications/${applicationId}/withdraw`),
  updateStatus: (applicationId, status, notes) => api.put(`/applications/${applicationId}/status`, { status, notes }),
  updateNotes: (applicationId, notes) => api.put(`/applications/${applicationId}/notes`, { notes }),
  getHistory: (applicationId) => api.get(`/applications/${applicationId}/history`),
};

export const recruiterAPI = {
  getJobs: () => api.get('/recruiter/jobs'),
  getApplicants: (params) => api.get('/recruiter/applicants', { params }),
  getAnalytics: () => api.get('/recruiter/analytics'),
  getCompany: () => api.get('/recruiter/company'),
  updateCompany: (data) => api.put('/recruiter/company', data),
};

export const interviewsAPI = {
  schedule: (data) => api.post('/interviews', data),
  getMy: () => api.get('/interviews/my'),
  getByApplication: (appId) => api.get(`/interviews/application/${appId}`),
  update: (id, data) => api.put(`/interviews/${id}`, data),
  cancel: (id) => api.post(`/interviews/${id}/cancel`),
  resendEmail: (id) => api.post(`/interviews/${id}/resend-email`),
  getRoomToken: (interviewId) => api.post(`/interviews/${interviewId}/room-token`),
  getRoomStatus: (interviewId) => api.get(`/interviews/${interviewId}/room-status`),
  admitParticipant: (interviewId, admitted = true) => api.post(`/interviews/${interviewId}/admission`, null, { params: { admitted } }),
  startRoom: (interviewId) => api.post(`/interviews/${interviewId}/room-start`),
  endRoom: (interviewId) => api.post(`/interviews/${interviewId}/room-end`),
  recordConsent: (interviewId, consent_granted) => api.post(`/interviews/${interviewId}/consent`, { consent_granted }),
  startRecording: (interviewId) => api.post(`/interviews/${interviewId}/recording/start`),
  stopRecording: (interviewId) => api.post(`/interviews/${interviewId}/recording/stop`),
  retryRecording: (interviewId) => api.post(`/interviews/${interviewId}/recording/retry`),
  getRecordings: (interviewId) => api.get(`/interviews/${interviewId}/recordings`),
  submitScorecard: (interviewId, data) => api.post(`/interviews/${interviewId}/scorecard`, data),
  getScorecard: (interviewId) => api.get(`/interviews/${interviewId}/scorecard`),
  getAITranscript: (interviewId) => api.post(`/interviews/${interviewId}/ai-transcript`),
  approveAITranscript: (interviewId, data) => api.post(`/interviews/${interviewId}/ai-transcript/approve`, data),
  getCandidateDossier: (candidateId) => api.get(`/interviews/candidate/${candidateId}/dossier`),
  generateAIQuestions: (data) => api.post('/interviews/ai-questions/generate', data),
  configureAI: (interviewId, data) => api.post(`/interviews/${interviewId}/configure-ai`, data),
  getQuestions: (interviewId) => api.get(`/interviews/${interviewId}/questions`),
  updateQuestions: (interviewId, data) => api.put(`/interviews/${interviewId}/questions`, data),
  getAIState: (interviewId) => api.get(`/interviews/${interviewId}/ai-state`),
  advanceAIState: (interviewId) => api.post(`/interviews/${interviewId}/ai-state/advance`),
  hybridTakeover: (interviewId, takeover) => api.post(`/interviews/${interviewId}/hybrid/takeover`, { takeover }),
  submitAIResponses: (interviewId, data) => api.post(`/interviews/${interviewId}/ai-responses`, data),
  generateAIEvaluation: (interviewId) => api.post(`/interviews/${interviewId}/evaluation/generate`),
  getAIEvaluation: (interviewId) => api.get(`/interviews/${interviewId}/evaluation`),
  updateAIEvaluation: (interviewId, data) => api.put(`/interviews/${interviewId}/evaluation`, data),
  archiveRecording: (interviewId, recordingUrl) => api.post(`/interviews/${interviewId}/archive-recording`, null, { params: { recording_url: recordingUrl } }),
};

export const mediaAPI = {
  getUploadSignature: (data) => api.post('/media/signature', data),
  uploadDirect: (formData) => api.post('/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  list: (params) => api.get('/media', { params }),
  getSignedPlayback: (assetId) => api.get(`/media/${assetId}/playback`),
  delete: (assetId) => api.delete(`/media/${assetId}`),
};

export const videoAssessmentsAPI = {
  create: (data) => api.post('/video-assessments', data),
  publish: (id) => api.post(`/video-assessments/${id}/publish`),
  list: (params) => api.get('/video-assessments', { params }),
  get: (id) => api.get(`/video-assessments/${id}`),
  assign: (id, applicationIds) => api.post(`/video-assessments/${id}/assign`, { application_ids: applicationIds }),
  getAssignments: (id) => api.get(`/video-assessments/${id}/assignments`),
  getReviewDetails: (assignmentId) => api.get(`/video-assessments/assignments/${assignmentId}/review`),
  evaluate: (assignmentId, data) => api.post(`/video-assessments/assignments/${assignmentId}/evaluate`, data),
  getMyAssessments: () => api.get('/candidate/video-assessments'),
  getCandidateAssessmentDetail: (assignmentId) => api.get(`/candidate/video-assessments/${assignmentId}`),
  submitResponse: (assignmentId, data) => api.post(`/candidate/video-assessments/${assignmentId}/responses`, data),
  finalize: (assignmentId) => api.post(`/candidate/video-assessments/${assignmentId}/finalize`),
};

export const evaluationsAPI = {
  submit: (data) => api.post('/evaluations', data),
  getByApplication: (appId) => api.get(`/evaluations/application/${appId}`),
  compareCandidates: (jobId) => api.get(`/evaluations/compare/${jobId}`),
};

export const notificationsAPI = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
};

export const messagesAPI = {
  getConversations: () => api.get('/messages/conversations'),
  getThread: (partnerId) => api.get(`/messages/thread/${partnerId}`),
  send: (data) => api.post('/messages', data),
};

export const adminAPI = {
  getAnalytics: () => api.get('/admin/analytics'),
  getUsers: () => api.get('/admin/users'),
  toggleUserStatus: (userId, isActive) => api.put(`/admin/users/${userId}/status?is_active=${isActive}`),
  getJobs: () => api.get('/admin/jobs'),
  moderateJob: (jobId, newStatus) => api.put(`/admin/jobs/${jobId}/moderate?new_status=${newStatus}`),
  getAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
};

export const skillsAPI = {
  search: (query) => api.get('/skills', { params: { query } }),
};

export const practiceAPI = {
  getTechnologies: () => api.get('/practice/technologies'),
  addTechnology: (data) => api.post('/practice/technologies', data),
  removeTechnology: (techName) => api.delete(`/practice/technologies/${encodeURIComponent(techName)}`),
  detectFromResume: () => api.post('/practice/technologies/detect-from-resume'),
  getQuestions: (techName, batch = 1) => api.get(`/practice/technologies/${encodeURIComponent(techName)}/questions`, { params: { batch } }),
  generateMoreQuestions: (techName) => api.post(`/practice/technologies/${encodeURIComponent(techName)}/generate-more`),
  submitAttempt: (questionId, data) => api.post(`/practice/questions/${questionId}/attempt`, data),
  getAnalytics: () => api.get('/practice/analytics'),
};

export const assessmentsAPI = {
  // Recruiter
  create: (data) => api.post('/recruiter/assessments', data),
  listRecruiter: (jobId) => api.get('/recruiter/assessments', { params: jobId ? { job_id: jobId } : {} }),
  getDetails: (id) => api.get(`/recruiter/assessments/${id}`),
  updateDraft: (id, data) => api.put(`/recruiter/assessments/${id}`, data),
  publish: (id) => api.post(`/recruiter/assessments/${id}/publish`),
  getShortlistedCandidates: (id) => api.get(`/recruiter/assessments/${id}/shortlisted-candidates`),
  assign: (id, data) => api.post(`/recruiter/assessments/${id}/assign`, data),
  getAssignments: (id) => api.get(`/recruiter/assessments/${id}/assignments`),
  getResults: (id, filter = 'all') => api.get(`/recruiter/assessments/${id}/results`, { params: { filter_status: filter } }),
  getCandidateReview: (assignmentId) => api.get(`/recruiter/assessments/assignments/${assignmentId}/candidate-answers`),
  listReviews: (params) => api.get('/recruiter/assessments/reviews', { params }),
  getDetailedReview: (assignmentId) => api.get(`/recruiter/assessments/assignments/${assignmentId}/detailed-review`),
  adjustScore: (assignmentId, data) => api.post(`/recruiter/assessments/assignments/${assignmentId}/adjust-score`, data),
  makeDecision: (assignmentId, data) => api.post(`/recruiter/assessments/assignments/${assignmentId}/decision`, data),
  retryEmail: (assignmentId) => api.post(`/recruiter/assessments/assignments/${assignmentId}/retry-email`),
  getComparison: (assessmentId) => api.get(`/recruiter/assessments/${assessmentId}/comparison`),

  // Candidate
  listCandidate: () => api.get('/candidate/assessments'),
  getInstructions: (assignmentId) => api.get(`/candidate/assessments/${assignmentId}/instructions`),
  startAttempt: (assignmentId) => api.post(`/candidate/assessments/${assignmentId}/start`),
  getAttempt: (assignmentId) => api.get(`/candidate/assessments/${assignmentId}/attempt`),
  saveAnswers: (attemptId, answers) => api.post(`/candidate/assessments/attempts/${attemptId}/answers`, { answers }),
  submitAttempt: (attemptId) => api.post(`/candidate/assessments/attempts/${attemptId}/submit`),
  saveSessionRecording: (attemptId, data) => api.post(`/candidate/assessments/attempts/${attemptId}/session-recording`, data),
  getResult: (assignmentId) => api.get(`/candidate/assessments/${assignmentId}/result`),
};

export const questionBankAPI = {
  list: (params) => api.get('/question-bank/questions', { params }),
  get: (id) => api.get(`/question-bank/questions/${id}`),
  create: (data) => api.post('/question-bank/questions', data),
  update: (id, data) => api.put(`/question-bank/questions/${id}`, data),
  duplicate: (id) => api.post(`/question-bank/questions/${id}/duplicate`),
  archive: (id) => api.post(`/question-bank/questions/${id}/archive`),
  checkDuplicate: (arg, excludeId = null) => {
    const text = typeof arg === 'object' && arg !== null ? (arg.text || arg.question_text) : arg;
    const exId = typeof arg === 'object' && arg !== null ? (arg.exclude_id || excludeId) : excludeId;
    return api.post('/question-bank/check-duplicate', { question_text: text, exclude_id: exId });
  },
  getTechnologies: () => api.get('/question-bank/technologies'),
  checkAvailability: (technology, topic = null) => api.get('/question-bank/availability', { params: { technology, topic } }),
  sample: (data) => api.post('/question-bank/sample', data),
  autoGenerateAssessment: (data) => api.post('/question-bank/auto-generate-assessment', data),
  listCollections: () => api.get('/question-bank/collections'),
  createCollection: (data) => api.post('/question-bank/collections', data),
  getCollection: (id) => api.get(`/question-bank/collections/${id}`),
  bulkImport: (csvContent, commit = false) => api.post('/question-bank/bulk-import', { csv_content: csvContent, commit }),
  uploadAndExtract: (formData) => api.post('/question-bank/upload-extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  batchImport: (data) => api.post('/question-bank/batch-import', data),
  getAssessmentAnalytics: (assessmentId) => api.get(`/question-bank/assessments/${assessmentId}/analytics`),
};

export const proctoringAPI = {
  // Candidate Endpoints
  startSession: (data) => api.post('/proctoring/session/start', data),
  recordEvent: (sessionId, data) => api.post(`/proctoring/session/${sessionId}/event`, data),
  getMySession: (attemptId) => api.get(`/proctoring/session/my/${attemptId}`),
  endSession: (sessionId) => api.post(`/proctoring/session/${sessionId}/end`),

  // Admin Endpoints
  getSessions: (params) => api.get('/admin/proctoring/sessions', { params }),
  getSessionDetail: (sessionId) => api.get(`/admin/proctoring/sessions/${sessionId}`),
  reviewEvent: (eventId, data) => api.put(`/admin/proctoring/events/${eventId}/review`, data),
  reviewSession: (sessionId, data) => api.put(`/admin/proctoring/sessions/${sessionId}/review`, data),
};

export default api;
