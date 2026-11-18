import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  Clock, CheckCircle, AlertTriangle, ChevronLeft, ChevronRight,
  ShieldCheck, HelpCircle, FileText, Send, ArrowLeft, Award, XCircle,
  Camera, CameraOff, Video, Eye, EyeOff, ShieldAlert, Maximize2,
  Minimize2, RefreshCw, UserCheck, CheckSquare, Square, Info
} from 'lucide-react';
import { assessmentsAPI, proctoringAPI, mediaAPI } from '../services/api';
import { useToast } from '../components/MotionComponents';
import { faceDetector } from '../utils/faceDetection';

export const CandidateAssessmentTestPage = () => {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Workflow Steps: 'PRE_CHECK' -> 'TESTING'
  const [currentStep, setCurrentStep] = useState('PRE_CHECK');
  const [instructions, setInstructions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Proctoring & Camera Hardware States
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraStatus, setCameraStatus] = useState('IDLE'); // 'IDLE', 'REQUESTING', 'CONNECTED', 'ERROR', 'INTERRUPTED'
  const [cameraError, setCameraError] = useState(null);
  const [candidateConsent, setCandidateConsent] = useState(false);
  const [proctoringSession, setProctoringSession] = useState(null);
  const [facePresenceStatus, setFacePresenceStatus] = useState('VISIBLE'); // 'VISIBLE', 'ABSENT', 'MULTIPLE'
  const [isCameraMinimized, setIsCameraMinimized] = useState(false);
  const [isCameraInterrupted, setIsCameraInterrupted] = useState(false);
  const [activeWarningModal, setActiveWarningModal] = useState(null);

  // Video Element Refs
  const previewVideoRef = useRef(null);
  const floatingVideoRef = useRef(null);

  // Browser MediaRecorder Session Recording
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const recordedVideoBlobRef = useRef(null);
  const [recordingUploadStatus, setRecordingUploadStatus] = useState('IDLE'); // 'IDLE', 'UPLOADING', 'COMPLETED', 'ERROR'
  const [uploadProgress, setUploadProgress] = useState(0);
  const [recordingDurationSeconds, setRecordingDurationSeconds] = useState(0);
  const recordingTimerRef = useRef(null);

  // Cooldown and Grace Period Refs
  const lastLoggedEventRef = useRef({ type: null, time: 0 });
  const faceAbsentCountRef = useRef(0);
  const blurStartRef = useRef(null);
  const streamRef = useRef(null);
  streamRef.current = cameraStream;

  // Attempt & Questions Data
  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({}); // question_id -> option_id
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);

  // Timer state
  const [secondsLeft, setSecondsLeft] = useState(0);
  const timerRef = useRef(null);
  const autoSaveTimerRef = useRef(null);
  const faceMonitorTimerRef = useRef(null);
  const answersRef = useRef(selectedAnswers);
  answersRef.current = selectedAnswers;

  // Format seconds to mm:ss
  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // --------------------------------------------------------------------------
  // Camera Hardware Initialization
  // --------------------------------------------------------------------------
  const startCamera = async () => {
    try {
      setCameraStatus('REQUESTING');
      setCameraError(null);

      // Clean up previous stream if any
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }

      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user',
          },
          audio: true,
        });
      } catch (audioErr) {
        console.warn('Microphone unavailable or denied, falling back to video only:', audioErr);
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user',
          },
          audio: false,
        });
      }

      setCameraStream(stream);
      setCameraStatus('CONNECTED');
      setIsCameraInterrupted(false);

      // Attach stream to active preview video element
      if (previewVideoRef.current) {
        previewVideoRef.current.srcObject = stream;
      }
      if (floatingVideoRef.current) {
        floatingVideoRef.current.srcObject = stream;
      }

      // Listen for stream disconnection / track end
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.onended = () => {
          handleCameraInterrupted();
        };
      }
    } catch (err) {
      console.error('Camera connection error:', err);
      let friendlyError = 'Unable to access your webcam.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        friendlyError = 'Camera permission was denied. Please allow camera access in your browser site settings.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        friendlyError = 'No webcam was detected on this device. Please connect a working camera.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        friendlyError = 'Your camera is currently in use by another application. Please close other video software.';
      }
      setCameraStatus('ERROR');
      setCameraError(friendlyError);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
  };

  // Ensure stream stays bound to video elements when transitioning steps
  useEffect(() => {
    if (cameraStream) {
      if (previewVideoRef.current && previewVideoRef.current.srcObject !== cameraStream) {
        previewVideoRef.current.srcObject = cameraStream;
      }
      if (floatingVideoRef.current && floatingVideoRef.current.srcObject !== cameraStream) {
        floatingVideoRef.current.srcObject = cameraStream;
      }
    }
  }, [cameraStream, currentStep]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      stopCamera();
      if (timerRef.current) clearInterval(timerRef.current);
      if (autoSaveTimerRef.current) clearInterval(autoSaveTimerRef.current);
      if (faceMonitorTimerRef.current) clearInterval(faceMonitorTimerRef.current);
    };
  }, []);

  // --------------------------------------------------------------------------
  // Initial Assessment Check
  // --------------------------------------------------------------------------
  const loadInitialStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Check if attempt already finalized
      try {
        const resResult = await assessmentsAPI.getResult(assignmentId);
        if (
          resResult?.data &&
          (resResult.data.submitted_at ||
            resResult.data.is_completed ||
            ['SUBMITTED', 'ACCEPTED', 'REJECTED', 'MOVED_TO_INTERVIEW', 'ON_HOLD'].includes(resResult.data.review_status))
        ) {
          setSubmissionResult(resResult.data);
          setLoading(false);
          return;
        }
      } catch {
        // Not completed yet, proceed to instructions
      }

      // Fetch pre-assessment instructions
      const resInst = await assessmentsAPI.getInstructions(assignmentId);
      setInstructions(resInst.data);

      // If attempt is already started, we still enforce camera check before resuming
      setCurrentStep('PRE_CHECK');
    } catch (err) {
      console.error('Failed to load assessment instructions:', err);
      const errMsg = err.response?.data?.detail || 'Failed to retrieve assessment details.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }, [assignmentId]);

  useEffect(() => {
    loadInitialStatus();
  }, [loadInitialStatus]);

  // --------------------------------------------------------------------------
  // Start or Resume Proctored Assessment
  // --------------------------------------------------------------------------
  const handleBeginAssessment = async () => {
    if (cameraStatus !== 'CONNECTED' || !cameraStream) {
      addToast('Please connect and verify your webcam first.', 'error');
      return;
    }
    if (!candidateConsent) {
      addToast('Please confirm your consent to proctored monitoring.', 'info');
      return;
    }

    try {
      setLoading(true);
      // 1. Start or resume attempt in assessment engine
      const resAttempt = await assessmentsAPI.startAttempt(assignmentId);
      const attemptData = resAttempt.data;
      setAttempt(attemptData);
      setQuestions(attemptData.questions || []);
      setSelectedAnswers(attemptData.saved_answers || {});
      setSecondsLeft(attemptData.remaining_seconds);

      // 2. Initialize proctoring telemetry session
      const resProctor = await proctoringAPI.startSession({
        attempt_id: attemptData.attempt_id,
        camera_permission_granted: true,
      });
      setProctoringSession(resProctor.data);

      setCurrentStep('TESTING');
      addToast('Proctored session initiated. Webcam and focus monitoring active.', 'success');
    } catch (err) {
      console.error('Failed to begin proctored assessment:', err);
      const errMsg = err.response?.data?.detail || 'Could not start assessment session.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------------------------------
  // Proctoring Event Recording Dispatcher
  // --------------------------------------------------------------------------
  const dispatchProctoringEvent = async (eventType, durationSeconds = 0, severity = 'LOW', details = {}) => {
    if (!proctoringSession?.id) return;

    // Throttle duplicate logging of same event type within 18 seconds
    const now = Date.now();
    const lastEvent = lastLoggedEventRef.current;
    if (lastEvent.type === eventType && (now - lastEvent.time) < 18000) {
      return;
    }
    lastLoggedEventRef.current = { type: eventType, time: now };

    try {
      const res = await proctoringAPI.recordEvent(proctoringSession.id, {
        event_type: eventType,
        duration_seconds: durationSeconds,
        severity: severity,
        details_json: details,
      });

      const updatedSession = res.data;
      setProctoringSession(updatedSession);

      // Trigger warning notification modal
      const warningCount = updatedSession.total_warning_count;
      let modalTitle = `Security Notice: Warning ${warningCount} of 3`;
      let modalMsg = 'An integrity deviation was detected. Please keep your face clearly in frame and remain focused on this test.';

      if (eventType === 'TAB_SWITCH' || eventType === 'WINDOW_BLUR') {
        modalTitle = `Tab Switch Detected (Warning ${warningCount}/3)`;
        modalMsg = `Focus was lost for ${durationSeconds.toFixed(1)}s. Navigating away from the assessment window is strictly supervised.`;
      } else if (eventType === 'FACE_NOT_DETECTED') {
        modalTitle = `Face Absent from Camera (Warning ${warningCount}/3)`;
        modalMsg = 'Your face was not detected in the camera frame for more than 4 seconds. Please ensure your camera angle is centered.';
      } else if (eventType === 'MULTIPLE_FACES_DETECTED') {
        modalTitle = `Multiple Faces Detected (Warning ${warningCount}/3)`;
        modalMsg = 'Multiple people were identified in your camera feed. SkillSphere assessments must be taken individually.';
      } else if (eventType === 'CAMERA_INTERRUPTED') {
        modalTitle = `Camera Feed Disconnected (Warning ${warningCount}/3)`;
        modalMsg = 'The webcam stream was interrupted. Reconnect your camera immediately to resume answering.';
      }

      if (warningCount >= 3) {
        modalTitle = 'Final Security Warning: Administrative Review Triggered';
        modalMsg = 'You have accrued 3 or more surveillance warnings. Your session telemetry has been flagged for recruiter and administrative inspection.';
      }

      setActiveWarningModal({
        type: eventType,
        title: modalTitle,
        message: modalMsg,
        count: warningCount,
      });
    } catch (err) {
      console.error('Failed to record proctoring telemetry:', err);
    }
  };

  // --------------------------------------------------------------------------
  // Camera Interruption & Restoration
  // --------------------------------------------------------------------------
  const handleCameraInterrupted = () => {
    setIsCameraInterrupted(true);
    setCameraStatus('INTERRUPTED');
    dispatchProctoringEvent('CAMERA_INTERRUPTED', 0, 'HIGH', { reason: 'Stream stopped or track ended' });
  };

  const handleReconnectCamera = async () => {
    await startCamera();
    if (cameraStatus === 'CONNECTED') {
      setIsCameraInterrupted(false);
      dispatchProctoringEvent('CAMERA_RESTORED', 0, 'LOW', { reason: 'Camera stream manually restored' });
      addToast('Webcam feed restored successfully', 'success');
    }
  };

  // --------------------------------------------------------------------------
  // Tab-Switch & Window Focus Detection
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (currentStep !== 'TESTING' || !proctoringSession?.id || submissionResult) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        blurStartRef.current = Date.now();
      } else {
        if (blurStartRef.current) {
          const elapsedSec = (Date.now() - blurStartRef.current) / 1000;
          blurStartRef.current = null;
          if (elapsedSec >= 1.0) {
            dispatchProctoringEvent('TAB_SWITCH', elapsedSec, 'HIGH', {
              duration_seconds: elapsedSec,
              trigger: 'visibilitychange',
            });
          }
        }
      }
    };

    const handleWindowBlur = () => {
      if (!blurStartRef.current) {
        blurStartRef.current = Date.now();
      }
    };

    const handleWindowFocus = () => {
      if (blurStartRef.current) {
        const elapsedSec = (Date.now() - blurStartRef.current) / 1000;
        blurStartRef.current = null;
        if (elapsedSec >= 1.2) {
          dispatchProctoringEvent('WINDOW_BLUR', elapsedSec, 'HIGH', {
            duration_seconds: elapsedSec,
            trigger: 'window_blur',
          });
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [currentStep, proctoringSession, submissionResult]);

  // --------------------------------------------------------------------------
  // Client-Side Face Presence Monitoring Loop
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (currentStep !== 'TESTING' || !proctoringSession?.id || isCameraInterrupted || submissionResult) {
      if (faceMonitorTimerRef.current) clearInterval(faceMonitorTimerRef.current);
      return;
    }

    faceMonitorTimerRef.current = setInterval(async () => {
      const videoEl = floatingVideoRef.current || previewVideoRef.current;
      if (!videoEl || videoEl.readyState < 2) return;

      const detection = await faceDetector.detect(videoEl);
      setFacePresenceStatus(detection.status);

      if (detection.status === 'ABSENT') {
        faceAbsentCountRef.current += 1;
        // Grace period: require 3 consecutive absent samples (approx 5.4 seconds)
        if (faceAbsentCountRef.current >= 3) {
          dispatchProctoringEvent('FACE_NOT_DETECTED', 5.4, 'MEDIUM', {
            confidence: detection.confidence,
          });
        }
      } else if (detection.status === 'MULTIPLE') {
        faceAbsentCountRef.current = 0;
        dispatchProctoringEvent('MULTIPLE_FACES_DETECTED', 0, 'HIGH', {
          face_count: detection.faceCount,
        });
      } else {
        // Face visible & verified
        faceAbsentCountRef.current = 0;
      }
    }, 1800);

    return () => {
      if (faceMonitorTimerRef.current) clearInterval(faceMonitorTimerRef.current);
    };
  }, [currentStep, proctoringSession, isCameraInterrupted, submissionResult]);

  // --------------------------------------------------------------------------
  // Server-Synced Countdown Timer
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (currentStep !== 'TESTING' || loading || !attempt || submissionResult) return;

    if (secondsLeft <= 0) {
      handleAutoSubmit();
      return;
    }

    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [currentStep, loading, attempt, secondsLeft, submissionResult]);

  // --------------------------------------------------------------------------
  // Periodic Background Answer Saver
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (currentStep !== 'TESTING' || !attempt?.attempt_id || submissionResult) return;

    autoSaveTimerRef.current = setInterval(() => {
      persistAnswersToServer(false);
    }, 12000);

    return () => clearInterval(autoSaveTimerRef.current);
  }, [currentStep, attempt, submissionResult]);

  // Save answers to server
  const persistAnswersToServer = async (showFeedback = false) => {
    if (!attempt?.attempt_id || submissionResult) return;
    const current = answersRef.current;
    const answerPayload = Object.entries(current).map(([qId, optId]) => ({
      question_id: qId,
      selected_option_id: optId,
    }));

    if (answerPayload.length === 0) return;

    try {
      setIsSaving(true);
      await assessmentsAPI.saveAnswers(attempt.attempt_id, answerPayload);
      if (showFeedback) {
        addToast('Progress saved securely', 'success');
      }
    } catch (err) {
      console.error('Failed to auto-save answers:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Option selection
  const handleSelectOption = (questionId, optionId) => {
    if (isCameraInterrupted) {
      addToast('Please restore your camera feed before selecting answers.', 'error');
      return;
    }
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  // --------------------------------------------------------------------------
  // MediaRecorder Session Recording Lifecycle
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (currentStep === 'TESTING' && cameraStream && !mediaRecorderRef.current) {
      try {
        const mimeTypes = [
          'video/webm;codecs=vp9,opus',
          'video/webm;codecs=vp8,opus',
          'video/webm',
          'video/mp4'
        ];
        let chosenMime = '';
        if (window.MediaRecorder) {
          for (const mime of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mime)) {
              chosenMime = mime;
              break;
            }
          }
        }

        recordedChunksRef.current = [];
        const recorder = new MediaRecorder(cameraStream, chosenMime ? { mimeType: chosenMime } : undefined);
        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            recordedChunksRef.current.push(e.data);
          }
        };
        recorder.start(1000);
        mediaRecorderRef.current = recorder;

        recordingTimerRef.current = setInterval(() => {
          setRecordingDurationSeconds((prev) => prev + 1);
        }, 1000);
      } catch (err) {
        console.warn('Session MediaRecorder failed to start:', err);
      }
    }

    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, [currentStep, cameraStream]);

  const stopSessionRecording = () => {
    return new Promise((resolve) => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === 'inactive') {
        const blob = recordedChunksRef.current.length > 0
          ? new Blob(recordedChunksRef.current, { type: 'video/webm' })
          : null;
        resolve(blob);
        return;
      }

      recorder.onstop = () => {
        const mime = recorder.mimeType || 'video/webm';
        const blob = new Blob(recordedChunksRef.current, { type: mime });
        resolve(blob);
      };

      try {
        recorder.stop();
      } catch (e) {
        const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
        resolve(blob);
      }
    });
  };

  const uploadSessionRecording = async (blob, attemptId) => {
    if (!blob || blob.size === 0 || !attemptId) return;
    setRecordingUploadStatus('UPLOADING');
    setUploadProgress(12);

    try {
      const sigRes = await mediaAPI.getUploadSignature({
        folder_key: 'assessments',
        resource_type: 'video'
      });
      const { signature, timestamp, api_key, upload_url, folder } = sigRes.data;

      const formData = new FormData();
      formData.append('file', blob, `session_attempt_${attemptId}.webm`);
      formData.append('api_key', api_key);
      formData.append('timestamp', timestamp);
      formData.append('signature', signature);
      formData.append('folder', folder);

      setUploadProgress(40);
      let uploadResult;
      try {
        const directUpload = await axios.post(upload_url, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const pct = Math.round((progressEvent.loaded * 50) / progressEvent.total) + 40;
              setUploadProgress(Math.min(92, pct));
            }
          }
        });
        uploadResult = directUpload.data;
      } catch (directErr) {
        console.warn('Direct Cloudinary upload failed, using server upload fallback:', directErr);
        const fallbackRes = await mediaAPI.uploadDirect(formData);
        uploadResult = fallbackRes.data;
      }

      setUploadProgress(95);
      await assessmentsAPI.saveSessionRecording(attemptId, {
        public_id: uploadResult.public_id,
        asset_id: uploadResult.asset_id || uploadResult.public_id,
        secure_url: uploadResult.secure_url || uploadResult.url,
        playback_url: uploadResult.playback_url || uploadResult.secure_url,
        duration_seconds: uploadResult.duration || recordingDurationSeconds,
        file_size_bytes: uploadResult.bytes || blob.size,
        file_format: uploadResult.format || 'webm',
        original_filename: `session_attempt_${attemptId}.webm`,
        resource_type: 'video'
      });

      setUploadProgress(100);
      setRecordingUploadStatus('COMPLETED');
      addToast('Proctoring session video securely uploaded and archived.', 'success');
    } catch (uploadErr) {
      console.error('Failed to upload session recording:', uploadErr);
      setRecordingUploadStatus('ERROR');
      addToast('Failed to upload session video recording. Please retry using the button below.', 'error');
    }
  };

  // Auto-submit when timer expires
  const handleAutoSubmit = async () => {
    if (isSubmitting || submissionResult) return;
    setIsSubmitting(true);
    try {
      addToast('Time has expired! Automatically submitting your answers...', 'info');
      await persistAnswersToServer(false);
      if (proctoringSession?.id) {
        await proctoringAPI.endSession(proctoringSession.id).catch(() => null);
      }
      const videoBlob = await stopSessionRecording();
      recordedVideoBlobRef.current = videoBlob;
      stopCamera();

      const res = await assessmentsAPI.submitAttempt(attempt.attempt_id);
      setSubmissionResult(res.data);
      addToast('Assessment submitted successfully! Your responses are now under review.', 'success');

      if (videoBlob) {
        uploadSessionRecording(videoBlob, attempt.attempt_id);
      }
    } catch (err) {
      console.error('Error during auto-submission:', err);
      const resResult = await assessmentsAPI.getResult(assignmentId).catch(() => null);
      if (resResult?.data) {
        setSubmissionResult(resResult.data);
      } else {
        setError(err.response?.data?.detail || 'Auto-submission completed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Manual submit action
  const handleManualSubmit = async () => {
    setShowConfirmModal(false);
    setIsSubmitting(true);
    try {
      await persistAnswersToServer(false);
      if (proctoringSession?.id) {
        await proctoringAPI.endSession(proctoringSession.id).catch(() => null);
      }
      const videoBlob = await stopSessionRecording();
      recordedVideoBlobRef.current = videoBlob;
      stopCamera();

      const res = await assessmentsAPI.submitAttempt(attempt.attempt_id);
      setSubmissionResult(res.data);
      addToast('Assessment submitted successfully! Your responses are now under review.', 'success');

      if (videoBlob) {
        uploadSessionRecording(videoBlob, attempt.attempt_id);
      }
    } catch (err) {
      console.error('Failed to submit assessment:', err);
      addToast(err.response?.data?.detail || 'Submission failed.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const answeredCount = Object.keys(selectedAnswers).filter((k) => selectedAnswers[k]).length;
  const totalCount = questions.length;
  const currentQuestion = questions[currentIndex];

  // --------------------------------------------------------------------------
  // Loading State
  // --------------------------------------------------------------------------
  if (loading) {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex flex-col items-center justify-center p-6 font-mono">
        <div className="w-12 h-12 rounded-full border-3 border-oxblood/30 border-t-oxblood animate-spin mb-4" />
        <p className="text-sm tracking-wider uppercase text-ivory/70">Connecting to Proctored Assessment Engine...</p>
        <p className="text-xs text-ivory/40 mt-1">Calibrating telemetry and server timer</p>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Submission Confirmation View (Privacy Preserved - Recruiter Controlled)
  // --------------------------------------------------------------------------
  if (submissionResult) {
    const formattedSubmittedAt = submissionResult.submitted_at
      ? new Date(submissionResult.submitted_at).toLocaleString('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      : new Date().toLocaleString('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short',
        });

    const isReviewed = submissionResult.final_decision && submissionResult.final_decision !== 'PENDING_REVIEW';

    return (
      <div className="min-h-screen bg-charcoal text-ivory py-12 px-4 sm:px-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-2xl glass-card bg-charcoal/90 border border-slate/20 dark:border-rose/20 rounded-3xl p-8 sm:p-10 shadow-2xl text-center space-y-8"
        >
          <div className="flex justify-center">
            <div className="w-20 h-20 rounded-full bg-emerald-500/15 border-2 border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <CheckCircle size={44} />
            </div>
          </div>

          <div>
            <span className="inline-block px-3 py-1 text-xs font-mono font-bold tracking-widest rounded-full uppercase mb-3 bg-oxblood/30 text-rose border border-rose/30">
              {submissionResult.review_status ? submissionResult.review_status.replace('_', ' ') : 'PENDING REVIEW'}
            </span>
            <h1 className="text-3xl sm:text-4xl font-display font-extrabold text-ivory">
              {submissionResult.assessment_title || 'Round 1 Assessment'}
            </h1>
            <p className="text-sm font-mono text-ivory/60 mt-1">
              Position: <span className="text-ivory font-semibold">{submissionResult.job_title || 'Role'}</span>
            </p>
          </div>

          {/* Submission Details Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
              <Clock className="w-5 h-5 text-rose shrink-0" />
              <div>
                <p className="text-[10px] font-mono uppercase text-ivory/50">Submitted At</p>
                <p className="text-sm font-mono font-medium text-ivory mt-0.5">
                  {formattedSubmittedAt}
                </p>
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
              <div>
                <p className="text-[10px] font-mono uppercase text-ivory/50">Submission Integrity</p>
                <p className="text-sm font-mono font-medium text-ivory mt-0.5">
                  Verified & Securely Recorded
                </p>
              </div>
            </div>
          </div>

          {/* Cloudinary Session Recording Status & Retry Bar */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-left">
            <div className="flex items-center gap-3">
              <Video className="w-5 h-5 text-oxblood dark:text-rose shrink-0" />
              <div>
                <p className="text-[10px] font-mono uppercase text-ivory/50">Proctoring Video Recording</p>
                <p className="text-xs sm:text-sm font-mono font-medium text-ivory mt-0.5">
                  {recordingUploadStatus === 'COMPLETED' && 'Archived in Secure Storage'}
                  {recordingUploadStatus === 'UPLOADING' && `Uploading to Cloud Storage (${uploadProgress}%)`}
                  {recordingUploadStatus === 'ERROR' && 'Upload Interrupted'}
                  {recordingUploadStatus === 'IDLE' && 'Proctoring Video Captured'}
                </p>
              </div>
            </div>

            {recordingUploadStatus === 'UPLOADING' && (
              <div className="w-full sm:w-36 bg-white/10 h-2 rounded-full overflow-hidden">
                <div className="bg-oxblood h-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </div>
            )}

            {recordingUploadStatus === 'COMPLETED' && (
              <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Completed
              </span>
            )}

            {recordingUploadStatus === 'ERROR' && recordedVideoBlobRef.current && (
              <button
                onClick={() => uploadSessionRecording(recordedVideoBlobRef.current, attempt?.attempt_id)}
                className="px-3 py-1.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 transition"
              >
                <RefreshCw size={12} /> Retry Upload Recording
              </button>
            )}
          </div>

          {/* Official Candidate Confirmation Notice */}
          <div className="p-6 rounded-2xl bg-oxblood/10 border border-rose/25 text-left space-y-3">
            <div className="flex items-center gap-2.5 text-rose">
              <Info className="w-5 h-5 shrink-0" />
              <p className="text-sm font-semibold font-mono uppercase tracking-wider">
                Submission Recorded & Under Review
              </p>
            </div>
            <p className="text-xs sm:text-sm font-sans text-ivory/80 leading-relaxed">
              Thank you for completing your assessment! Your responses have been successfully submitted and your assessment is now under review. The recruitment team will evaluate your performance and notify you about the next stage of the recruitment process. Your assessment activity may be reviewed according to the monitoring policy explained before the assessment. You can safely leave this page. Your submission has been recorded.
            </p>
          </div>

          {/* If recruiter has made a decision that is candidate-visible */}
          {isReviewed && submissionResult.status_message && (
            <div className="p-5 rounded-2xl bg-white/5 border border-white/15 text-left">
              <p className="text-xs font-mono uppercase text-rose font-bold mb-1">
                {submissionResult.status_headline || 'Recruitment Status Update'}
              </p>
              <p className="text-xs sm:text-sm text-ivory/90 leading-relaxed font-sans">
                {submissionResult.status_message}
              </p>
            </div>
          )}

          <div className="pt-2">
            <button
              onClick={() => navigate('/dashboard?tab=assessments')}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-oxblood text-ivory hover:bg-oxblood/80 font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-oxblood/20 min-h-[44px]"
            >
              <ArrowLeft size={16} /> Return to Assessments
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // Error State
  // --------------------------------------------------------------------------
  if (error) {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex items-center justify-center p-6">
        <div className="max-w-md w-full glass-card p-8 rounded-3xl border border-rose/30 text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-rose mx-auto" />
          <h2 className="text-xl font-display font-bold text-ivory">Assessment Access Alert</h2>
          <p className="text-sm font-mono text-ivory/70">{error}</p>
          <button
            onClick={() => navigate('/dashboard?tab=assessments')}
            className="mt-4 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-mono uppercase tracking-wider text-ivory min-h-[44px]"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // STEP 0: PRE-ASSESSMENT CAMERA & PROCTORING PERMISSION SCREEN
  // --------------------------------------------------------------------------
  if (currentStep === 'PRE_CHECK') {
    return (
      <div className="min-h-screen bg-charcoal text-ivory py-10 px-4 sm:px-6 flex items-center justify-center font-sans">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-3xl glass-card bg-charcoal/90 border border-slate/20 dark:border-rose/20 rounded-3xl p-6 sm:p-10 shadow-2xl space-y-8"
        >
          {/* Header */}
          <div className="border-b border-white/10 pb-6">
            <div className="flex items-center gap-2.5 text-xs font-mono text-oxblood dark:text-rose uppercase font-bold tracking-widest mb-2">
              <ShieldCheck size={16} />
              <span>SkillSphere Supervision &bull; Step 1 of 2</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-display font-extrabold text-ivory">
              Proctored Assessment Verification
            </h1>
            <p className="text-xs sm:text-sm font-mono text-ivory/60 mt-1">
              Assessment: <span className="text-ivory font-semibold">{instructions?.title || 'First-Round Assessment'}</span> &bull; Position: <span className="text-ivory font-semibold">{instructions?.job_title || 'Software Role'}</span>
            </p>
          </div>

          {/* Assessment Specifications Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-[10px] font-mono uppercase text-ivory/40">Duration</p>
              <p className="text-lg font-bold font-mono text-ivory mt-0.5">{instructions?.duration_minutes || 30} Mins</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-[10px] font-mono uppercase text-ivory/40">Questions</p>
              <p className="text-lg font-bold font-mono text-ivory mt-0.5">{instructions?.question_count || 0}</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-[10px] font-mono uppercase text-ivory/40">Total Marks</p>
              <p className="text-lg font-bold font-mono text-ivory mt-0.5">{instructions?.total_marks || 0}</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-[10px] font-mono uppercase text-ivory/40">Passing Mark</p>
              <p className="text-lg font-bold font-mono text-ivory mt-0.5">{instructions?.passing_marks || 0}</p>
            </div>
          </div>

          {/* Interactive Webcam Test Area */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            {/* Webcam Preview Window */}
            <div className="md:col-span-6 relative aspect-video bg-black/60 rounded-2xl overflow-hidden border border-white/15 flex items-center justify-center">
              <video
                ref={previewVideoRef}
                autoPlay
                playsInline
                muted
                className={`w-full h-full object-cover transform -scale-x-100 ${cameraStatus === 'CONNECTED' ? 'block' : 'hidden'}`}
              />
              {cameraStatus !== 'CONNECTED' && (
                <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
                  <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-ivory/40">
                    <Camera size={24} />
                  </div>
                  <p className="text-xs font-mono text-ivory/60">Webcam Inactive</p>
                  <p className="text-[11px] font-mono text-ivory/40">Click below to test your camera connection</p>
                </div>
              )}

              {/* Status Pill Badge */}
              <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/75 backdrop-blur-md text-[10px] font-mono">
                <span className={`w-2 h-2 rounded-full ${
                  cameraStatus === 'CONNECTED' ? 'bg-success animate-pulse' : cameraStatus === 'ERROR' ? 'bg-rose' : 'bg-white/40'
                }`} />
                <span className={cameraStatus === 'CONNECTED' ? 'text-success' : 'text-ivory/70'}>
                  {cameraStatus === 'CONNECTED' ? 'Camera Calibrated' : cameraStatus === 'REQUESTING' ? 'Requesting Access...' : 'Camera Off'}
                </span>
              </div>
            </div>

            {/* Camera Control & Rules */}
            <div className="md:col-span-6 space-y-4">
              <div className="space-y-2 text-xs font-mono text-ivory/80 leading-relaxed">
                <p className="flex items-start gap-2">
                  <span className="text-oxblood font-bold">&bull;</span>
                  <span><strong>Webcam Verification:</strong> Face presence is periodically verified in your browser. Strictly zero image or video files are stored.</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-oxblood font-bold">&bull;</span>
                  <span><strong>Tab Switch Monitoring:</strong> Navigating away from this window triggers security alerts and records focus-loss duration.</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-oxblood font-bold">&bull;</span>
                  <span><strong>Three-Warning Threshold:</strong> Reaching 3 infractions flags your assessment for manual recruiter and admin review.</span>
                </p>
              </div>

              {cameraStatus !== 'CONNECTED' ? (
                <button
                  onClick={startCamera}
                  disabled={cameraStatus === 'REQUESTING'}
                  className="w-full py-3 px-4 rounded-xl bg-white/10 hover:bg-white/15 text-ivory font-mono text-xs uppercase font-bold tracking-wider flex items-center justify-center gap-2 border border-white/10 transition-all min-h-[44px]"
                >
                  <Camera size={16} />
                  <span>{cameraStatus === 'REQUESTING' ? 'Connecting to Webcam...' : 'Connect & Test Camera'}</span>
                </button>
              ) : (
                <div className="p-3 rounded-xl bg-success/15 border border-success/30 text-success text-xs font-mono flex items-center gap-2">
                  <CheckCircle size={16} className="shrink-0" />
                  <span>Camera connected! Keep your face centered during the test.</span>
                </div>
              )}

              {cameraError && (
                <div className="p-3 rounded-xl bg-oxblood/20 border border-rose/30 text-rose text-xs font-mono space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <AlertTriangle size={14} /> Hardware Access Notice
                  </p>
                  <p className="text-[11px] leading-relaxed opacity-90">{cameraError}</p>
                </div>
              )}
            </div>
          </div>

          {/* Accommodation Notice */}
          <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-start gap-3">
            <Info className="w-4 h-4 text-ivory/60 mt-0.5 shrink-0" />
            <div className="text-[11px] font-mono text-ivory/60 leading-relaxed">
              <strong className="text-ivory/80">Disability & Hardware Accommodation Notice:</strong> If you experience technical limitations, lack hardware access, or require specific testing accommodations, please notify the hiring team or administrator before starting.
            </div>
          </div>

          {/* Consent Checkbox */}
          <div
            onClick={() => setCandidateConsent(!candidateConsent)}
            className="flex items-start gap-3 p-3.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 cursor-pointer transition-colors"
          >
            <div className="mt-0.5 text-oxblood dark:text-rose shrink-0">
              {candidateConsent ? <CheckSquare size={18} /> : <Square size={18} className="text-ivory/40" />}
            </div>
            <label className="text-xs font-mono text-ivory/80 cursor-pointer select-none leading-relaxed">
              I acknowledge and agree that this assessment is proctored with local face presence verification and tab-switch supervision, and confirm I am the registered candidate.
            </label>
          </div>

          {/* Action Footer */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              onClick={() => navigate('/dashboard?tab=assessments')}
              className="py-3 px-6 rounded-xl bg-white/10 hover:bg-white/15 text-ivory font-mono text-xs uppercase tracking-wider min-h-[44px] transition-colors"
            >
              Return Later
            </button>
            <button
              onClick={handleBeginAssessment}
              disabled={cameraStatus !== 'CONNECTED' || !candidateConsent}
              className="flex-1 py-3 px-6 rounded-xl bg-oxblood hover:bg-oxblood/85 disabled:opacity-30 disabled:cursor-not-allowed text-ivory font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-oxblood/20 min-h-[44px] flex items-center justify-center gap-2"
            >
              <ShieldCheck size={16} />
              <span>Begin Proctored Assessment</span>
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // STEP 1: ACTIVE TEST INTERFACE WITH CONTINUOUS PROCTORING SUPERVISION
  // --------------------------------------------------------------------------
  const isTimeCritical = secondsLeft < 180; // less than 3 minutes
  const warningCount = proctoringSession?.total_warning_count || 0;

  return (
    <div className="min-h-screen bg-charcoal text-ivory flex flex-col font-sans relative">
      {/* Top Test Header */}
      <header className="sticky top-0 z-30 bg-charcoal/95 backdrop-blur-md border-b border-slate/15 dark:border-rose/15 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-oxblood text-ivory font-black flex items-center justify-center text-sm shadow">
            S
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-display font-bold text-ivory truncate max-w-[180px] sm:max-w-sm">
              {attempt?.assessment_title || instructions?.title || 'First-Round Assessment'}
            </h1>
            <div className="flex items-center gap-2 text-[10px] font-mono text-ivory/50">
              <span>Proctored Session</span>
              <span>&bull;</span>
              <span className={`font-bold ${warningCount > 0 ? (warningCount >= 3 ? 'text-rose' : 'text-amber-400') : 'text-success'}`}>
                {warningCount === 0 ? '0 Warnings (Clean)' : `${warningCount} Warning${warningCount > 1 ? 's' : ''}`}
              </span>
            </div>
          </div>
        </div>

        {/* Center: Countdown Timer */}
        <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full border font-mono font-bold text-xs sm:text-sm tracking-wider transition-colors ${
          isTimeCritical
            ? 'bg-rose/20 text-rose border-rose animate-pulse'
            : 'bg-white/5 text-ivory border-white/10'
        }`}>
          <Clock size={16} className={isTimeCritical ? 'text-rose' : 'text-oxblood'} />
          <span>{formatTime(secondsLeft)}</span>
        </div>

        {/* Right: Submit Action */}
        <div className="flex items-center gap-3">
          {isSaving && (
            <span className="hidden sm:inline-block text-[10px] font-mono text-ivory/40">
              Saving...
            </span>
          )}
          <button
            onClick={() => setShowConfirmModal(true)}
            disabled={isSubmitting || isCameraInterrupted}
            className="px-4 sm:px-5 py-2 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-md shadow-oxblood/20 min-h-[44px] flex items-center gap-1.5"
          >
            <Send size={14} />
            <span className="hidden sm:inline">Submit Test</span>
            <span className="sm:hidden">Submit</span>
          </button>
        </div>
      </header>

      {/* Floating Proctoring Camera Badge (Fixed Bottom-Right) */}
      <div className="fixed bottom-4 right-4 z-40 select-none">
        <motion.div
          layout
          className={`glass-card bg-charcoal/95 border ${
            isCameraInterrupted
              ? 'border-rose shadow-rose/20'
              : facePresenceStatus === 'ABSENT'
              ? 'border-amber-400 shadow-amber-400/20'
              : 'border-oxblood/40'
          } rounded-2xl overflow-hidden shadow-2xl transition-all`}
        >
          {/* Header Bar */}
          <div className="px-3 py-1.5 bg-black/60 flex items-center justify-between gap-3 text-[10px] font-mono">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${
                isCameraInterrupted
                  ? 'bg-rose animate-ping'
                  : facePresenceStatus === 'VISIBLE'
                  ? 'bg-success animate-pulse'
                  : 'bg-amber-400 animate-ping'
              }`} />
              <span className="font-bold text-ivory/90">
                {isCameraInterrupted
                  ? 'Camera Dropped'
                  : facePresenceStatus === 'VISIBLE'
                  ? 'Face Verified'
                  : facePresenceStatus === 'MULTIPLE'
                  ? 'Multiple Faces'
                  : 'Face Absent'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-[9px] text-rose font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-rose animate-ping inline-block" />
                <span>REC {formatTime(recordingDurationSeconds)}</span>
              </div>

              <button
                onClick={() => setIsCameraMinimized(!isCameraMinimized)}
                className="text-ivory/50 hover:text-ivory transition-colors"
                title={isCameraMinimized ? 'Expand Camera' : 'Minimize'}
              >
                {isCameraMinimized ? <Maximize2 size={12} /> : <Minimize2 size={12} />}
              </button>
            </div>
          </div>

          {/* Video Feed */}
          {!isCameraMinimized && (
            <div className="w-36 h-28 sm:w-44 sm:h-32 bg-black relative">
              <video
                ref={floatingVideoRef}
                autoPlay
                playsInline
                muted
                className={`w-full h-full object-cover transform -scale-x-100 ${isCameraInterrupted ? 'opacity-20' : 'opacity-90'}`}
              />
              {isCameraInterrupted && (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-2 text-center bg-black/80">
                  <CameraOff size={20} className="text-rose mb-1" />
                  <p className="text-[9px] font-mono text-rose font-bold">Interrupted</p>
                  <button
                    onClick={handleReconnectCamera}
                    className="mt-1 px-2 py-0.5 rounded bg-oxblood text-[8px] font-mono uppercase text-ivory"
                  >
                    Reconnect
                  </button>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </div>

      {/* Main Test Workspace */}
      <div className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left / Center: Question Panel */}
        <main className="lg:col-span-8 space-y-6">
          {currentQuestion && (
            <div className="glass-card bg-charcoal/80 border border-slate/15 dark:border-rose/15 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
              {/* Question Meta Header */}
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <span className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono font-bold text-ivory/80 uppercase">
                  Question {currentIndex + 1} of {totalCount}
                </span>
                <span className="text-xs font-mono text-oxblood dark:text-rose font-bold">
                  {currentQuestion.marks} Mark{currentQuestion.marks > 1 ? 's' : ''}
                </span>
              </div>

              {/* Question Text */}
              <div className="text-lg sm:text-xl font-medium text-ivory leading-relaxed font-sans">
                {currentQuestion.question_text}
              </div>

              {/* Options List */}
              <div className="space-y-3 pt-2">
                {currentQuestion.options.map((opt) => {
                  const isSelected = selectedAnswers[currentQuestion.id] === opt.id;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => handleSelectOption(currentQuestion.id, opt.id)}
                      disabled={isCameraInterrupted}
                      className={`w-full text-left p-4 sm:p-4.5 rounded-2xl border transition-all duration-150 flex items-start gap-3.5 min-h-[48px] ${
                        isSelected
                          ? 'bg-oxblood/25 border-oxblood text-ivory shadow-md shadow-oxblood/10'
                          : 'bg-white/5 border-white/10 hover:bg-white/10 text-ivory/80 hover:text-ivory'
                      } ${isCameraInterrupted ? 'opacity-40 cursor-not-allowed' : ''}`}
                    >
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 text-xs font-mono font-bold transition-colors ${
                        isSelected
                          ? 'border-oxblood bg-oxblood text-ivory'
                          : 'border-ivory/40 text-ivory/60'
                      }`}>
                        {opt.option_key}
                      </div>
                      <span className="text-sm sm:text-base font-sans leading-snug">
                        {opt.option_text}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Question Navigation Controls */}
              <div className="flex items-center justify-between pt-6 border-t border-white/10">
                <button
                  onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                  disabled={currentIndex === 0 || isCameraInterrupted}
                  className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-xs uppercase tracking-wider flex items-center gap-1.5 min-h-[44px]"
                >
                  <ChevronLeft size={16} /> Previous
                </button>

                <button
                  onClick={() => persistAnswersToServer(true)}
                  disabled={isCameraInterrupted}
                  className="text-xs font-mono text-ivory/40 hover:text-ivory/70 transition-colors"
                >
                  Save Progress
                </button>

                <button
                  onClick={() => setCurrentIndex((prev) => Math.min(totalCount - 1, prev + 1))}
                  disabled={currentIndex === totalCount - 1 || isCameraInterrupted}
                  className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed font-mono text-xs uppercase tracking-wider flex items-center gap-1.5 min-h-[44px]"
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </main>

        {/* Right: Question Navigation Matrix & Summary */}
        <aside className="lg:col-span-4 space-y-6">
          <div className="glass-card bg-charcoal/80 border border-slate/15 dark:border-rose/15 rounded-3xl p-6 shadow-xl space-y-5">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-ivory/60">
              Question Navigator
            </h3>

            {/* Answered Progress Stats */}
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="flex items-center gap-1.5 text-success">
                <span className="w-2.5 h-2.5 rounded-full bg-success" />
                {answeredCount} Answered
              </span>
              <span className="flex items-center gap-1.5 text-ivory/40">
                <span className="w-2.5 h-2.5 rounded-full bg-white/20" />
                {totalCount - answeredCount} Pending
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-oxblood h-full transition-all duration-300"
                style={{ width: `${(answeredCount / (totalCount || 1)) * 100}%` }}
              />
            </div>

            {/* Matrix Grid */}
            <div className="grid grid-cols-5 gap-2 pt-2">
              {questions.map((q, idx) => {
                const isAns = Boolean(selectedAnswers[q.id]);
                const isCurr = idx === currentIndex;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(idx)}
                    disabled={isCameraInterrupted}
                    className={`h-11 rounded-xl text-xs font-mono font-bold transition-all flex items-center justify-center ${
                      isCurr
                        ? 'border-2 border-ivory scale-105 shadow-md'
                        : 'border border-transparent'
                    } ${
                      isAns
                        ? 'bg-oxblood text-ivory'
                        : 'bg-white/5 hover:bg-white/10 text-ivory/50'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            {/* Supervision Safeguard Notice */}
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 text-[11px] font-mono text-ivory/50 leading-relaxed space-y-1">
              <p className="flex items-center gap-1 text-ivory/80 font-bold mb-1">
                <ShieldCheck size={14} className="text-oxblood" /> Proctoring Active
              </p>
              <p>&bull; Live webcam presence monitored continuously.</p>
              <p>&bull; Tab-switch & focus deviation recorded.</p>
              <p>&bull; Answers auto-submit when the countdown expires.</p>
            </div>
          </div>
        </aside>
      </div>

      {/* Confirmation Modal Before Manual Submit */}
      <AnimatePresence>
        {showConfirmModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal/80 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md glass-card bg-charcoal border border-slate/20 dark:border-rose/20 rounded-3xl p-6 sm:p-8 space-y-5 shadow-2xl"
            >
              <div className="w-12 h-12 rounded-full bg-oxblood/20 text-rose flex items-center justify-center mx-auto">
                <HelpCircle size={28} />
              </div>
              <div className="text-center">
                <h3 className="text-xl font-display font-bold text-ivory">Ready to Submit?</h3>
                <p className="text-xs font-mono text-ivory/60 mt-1">
                  You have answered <span className="text-ivory font-bold">{answeredCount}</span> of{' '}
                  <span className="text-ivory font-bold">{totalCount}</span> questions.
                </p>
                {answeredCount < totalCount && (
                  <p className="text-xs font-mono text-rose mt-2">
                    Notice: {totalCount - answeredCount} question(s) remain unanswered!
                  </p>
                )}
                <p className="text-[11px] font-mono text-ivory/40 mt-3">
                  Once submitted, your answers will be permanently evaluated and cannot be changed.
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-ivory text-xs font-mono uppercase tracking-wider min-h-[44px]"
                >
                  Continue Test
                </button>
                <button
                  onClick={handleManualSubmit}
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory font-bold text-xs font-mono uppercase tracking-wider shadow-lg shadow-oxblood/20 min-h-[44px]"
                >
                  {isSubmitting ? 'Evaluating...' : 'Confirm Submit'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Proctoring Warning Notification Modal */}
      <AnimatePresence>
        {activeWarningModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md glass-card bg-charcoal border-2 border-rose/50 rounded-3xl p-6 sm:p-8 space-y-5 shadow-2xl"
            >
              <div className="w-14 h-14 rounded-full bg-oxblood/30 border border-rose text-rose flex items-center justify-center mx-auto animate-pulse">
                <ShieldAlert size={32} />
              </div>

              <div className="text-center space-y-2">
                <span className="inline-block px-3 py-1 text-[10px] font-mono font-bold uppercase tracking-widest bg-rose/20 text-rose border border-rose/30 rounded-full">
                  Security Warning Triggered
                </span>
                <h3 className="text-lg sm:text-xl font-display font-bold text-ivory">
                  {activeWarningModal.title}
                </h3>
                <p className="text-xs font-mono text-ivory/80 leading-relaxed">
                  {activeWarningModal.message}
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 text-[11px] font-mono text-ivory/50 space-y-1">
                <p>&bull; Remaining Time continues to decrement normally.</p>
                <p>&bull; All selected answers are preserved securely.</p>
                <p>&bull; Repeated infractions are permanently stored for administrative review.</p>
              </div>

              <button
                onClick={() => setActiveWarningModal(null)}
                className="w-full py-3 rounded-xl bg-oxblood hover:bg-oxblood/85 text-ivory font-mono font-bold text-xs uppercase tracking-wider shadow-lg shadow-oxblood/20 min-h-[44px] transition-all"
              >
                I Understand &amp; Resume Test
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CandidateAssessmentTestPage;
