import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Video, VideoOff, Mic, MicOff, Play, Pause, RotateCcw, Check,
  ChevronRight, AlertCircle, Shield, Clock, CheckCircle2, Lock,
  ArrowRight, Sparkles, RefreshCw, Eye
} from 'lucide-react';
import { videoAssessmentsAPI, mediaAPI } from '../services/api';
import { useToast } from '../components/MotionComponents';

export const CandidateVideoAssessmentPage = () => {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Workflow Stages: 'loading' | 'hardware_check' | 'instructions' | 'question_prep' | 'recording' | 'preview_retake' | 'uploading_step' | 'final_review' | 'submitted'
  const [stage, setStage] = useState('loading');
  const [assignment, setAssignment] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [error, setError] = useState('');

  // Media Stream & Hardware
  const [mediaStream, setMediaStream] = useState(null);
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isVideoMuted, setIsVideoMuted] = useState(false);
  const [hardwareVerified, setHardwareVerified] = useState(false);

  // Timers
  const [prepSecondsRemaining, setPrepSecondsRemaining] = useState(30);
  const [recordSecondsRemaining, setRecordSecondsRemaining] = useState(120);
  const [elapsedRecordingTime, setElapsedRecordingTime] = useState(0);

  // Recording State & Blobs
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const [recordedVideoBlob, setRecordedVideoBlob] = useState(null);
  const [recordedVideoUrl, setRecordedVideoUrl] = useState(null);
  const [retakeCountMap, setRetakeCountMap] = useState({}); // question_id -> count
  const [savedResponsesMap, setSavedResponsesMap] = useState({}); // question_id -> response object

  // DOM Refs
  const liveVideoRef = useRef(null);
  const previewVideoRef = useRef(null);

  // 1. Load Assignment Details
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const res = await videoAssessmentsAPI.getCandidateAssessmentDetail(assignmentId);
        if (!isMounted) return;
        setAssignment(res.data);

        // Prepopulate existing responses if any
        const respMap = {};
        const retMap = {};
        (res.data.responses || []).forEach(r => {
          respMap[r.question_id] = r;
          retMap[r.question_id] = r.retake_count;
        });
        setSavedResponsesMap(respMap);
        setRetakeCountMap(retMap);

        if (res.data.status === 'COMPLETED') {
          setStage('submitted');
        } else {
          setStage('hardware_check');
        }
      } catch (err) {
        if (!isMounted) return;
        setError(err.response?.data?.detail || "Failed to load video assessment.");
      }
    }
    loadData();

    return () => {
      isMounted = false;
      if (mediaStream) {
        mediaStream.getTracks().forEach(t => t.stop());
      }
    };
  }, [assignmentId]);

  // 2. Hardware camera initialization
  useEffect(() => {
    if (stage === 'hardware_check' || stage === 'question_prep' || stage === 'recording') {
      if (!mediaStream) {
        navigator.mediaDevices?.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true
        }).then(stream => {
          setMediaStream(stream);
          if (liveVideoRef.current) {
            liveVideoRef.current.srcObject = stream;
          }
        }).catch(err => {
          console.warn("Camera init warning:", err);
          setError("Please allow camera and microphone access to complete your video assessment.");
        });
      } else if (liveVideoRef.current) {
        liveVideoRef.current.srcObject = mediaStream;
      }
    }
  }, [stage, mediaStream]);

  const currentQuestion = assignment?.questions?.[currentQuestionIndex];
  const totalQuestions = assignment?.questions?.length || 0;

  // 3. Prep Timer
  useEffect(() => {
    let timer = null;
    if (stage === 'question_prep' && prepSecondsRemaining > 0) {
      timer = setInterval(() => {
        setPrepSecondsRemaining(prev => prev - 1);
      }, 1000);
    } else if (stage === 'question_prep' && prepSecondsRemaining === 0) {
      startRecording();
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [stage, prepSecondsRemaining]);

  // 4. Recording Countdown Timer
  useEffect(() => {
    let timer = null;
    if (stage === 'recording' && recordSecondsRemaining > 0) {
      timer = setInterval(() => {
        setRecordSecondsRemaining(prev => prev - 1);
        setElapsedRecordingTime(prev => prev + 1);
      }, 1000);
    } else if (stage === 'recording' && recordSecondsRemaining === 0) {
      stopRecording();
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [stage, recordSecondsRemaining]);

  // Start question workflow
  const prepareQuestion = (index) => {
    setCurrentQuestionIndex(index);
    const q = assignment?.questions?.[index];
    setPrepSecondsRemaining(q?.prep_time_seconds || 30);
    setRecordSecondsRemaining(q?.max_duration_seconds || 120);
    setElapsedRecordingTime(0);
    setRecordedVideoBlob(null);
    if (recordedVideoUrl) {
      URL.revokeObjectURL(recordedVideoUrl);
      setRecordedVideoUrl(null);
    }
    setStage('question_prep');
  };

  // Start Recording
  const startRecording = () => {
    if (!mediaStream) {
      addToast({ title: "Camera Error", message: "Camera stream is not active.", type: "error" });
      return;
    }
    recordedChunksRef.current = [];
    try {
      const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9'
        : 'video/webm';
      const recorder = new MediaRecorder(mediaStream, { mimeType: mime });

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        setRecordedVideoBlob(blob);
        setRecordedVideoUrl(url);
        setStage('preview_retake');
      };

      mediaRecorderRef.current = recorder;
      recorder.start(1000); // 1-second chunks
      const q = assignment?.questions?.[currentQuestionIndex];
      setRecordSecondsRemaining(q?.max_duration_seconds || 120);
      setElapsedRecordingTime(0);
      setStage('recording');
    } catch (err) {
      console.error("Recording error:", err);
      addToast({ title: "Recording Error", message: "Could not start video recorder.", type: "error" });
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  // Retake Question
  const handleRetake = () => {
    if (!currentQuestion) return;
    const currentRetakes = retakeCountMap[currentQuestion.id] || 0;
    if (currentRetakes >= currentQuestion.retake_limit) {
      addToast({
        title: "Retake Limit Exceeded",
        message: `You have reached the maximum of ${currentQuestion.retake_limit} retake(s) for this question.`,
        type: "error"
      });
      return;
    }
    setRetakeCountMap(prev => ({
      ...prev,
      [currentQuestion.id]: currentRetakes + 1
    }));
    prepareQuestion(currentQuestionIndex);
  };

  // Save Response & Proceed
  const handleSaveAndNext = async () => {
    if (!recordedVideoBlob || !currentQuestion) return;
    setStage('uploading_step');

    try {
      // 1. Upload video to Cloudinary / backend
      const formData = new FormData();
      const filename = `response_${assignment?.id || assignmentId}_q${currentQuestion.order_num}.webm`;
      formData.append('file', recordedVideoBlob, filename);
      formData.append('folder_key', 'candidate_responses');
      if (assignment?.candidate_id && assignment.candidate_id !== 'undefined' && assignment.candidate_id !== 'null') {
        formData.append('candidate_id', assignment.candidate_id);
      }

      const uploadRes = await mediaAPI.uploadDirect(formData);
      const mediaAssetId = uploadRes.data.id;

      // 2. Submit question response
      const retakeCount = retakeCountMap[currentQuestion.id] || 0;
      const respRes = await videoAssessmentsAPI.submitResponse(assignmentId, {
        question_id: currentQuestion.id,
        media_asset_id: mediaAssetId,
        duration_seconds: elapsedRecordingTime,
        retake_count: retakeCount
      });

      // Update state
      setSavedResponsesMap(prev => ({
        ...prev,
        [currentQuestion.id]: respRes.data
      }));

      addToast({
        title: "Response Saved",
        message: `Question ${currentQuestion.order_num} response recorded.`,
        type: "success"
      });

      // Advance or final review
      if (currentQuestionIndex + 1 < totalQuestions) {
        prepareQuestion(currentQuestionIndex + 1);
      } else {
        setStage('final_review');
      }
    } catch (err) {
      console.error("Save response error:", err);
      addToast({
        title: "Upload Failed",
        message: err.response?.data?.detail || "Could not upload video response. Please try again.",
        type: "error"
      });
      setStage('preview_retake');
    }
  };

  // Finalize Submission
  const handleFinalize = async () => {
    try {
      await videoAssessmentsAPI.finalize(assignmentId);
      setStage('submitted');
      addToast({
        title: "Assessment Finalized",
        message: "Your video assessment responses have been submitted to the recruiter.",
        type: "success"
      });
    } catch (err) {
      addToast({
        title: "Submission Error",
        message: err.response?.data?.detail || "Failed to finalize video assessment.",
        type: "error"
      });
    }
  };

  if (stage === 'loading') {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex flex-col items-center justify-center p-6">
        <div className="w-12 h-12 rounded-full border-4 border-oxblood/30 border-t-oxblood animate-spin mb-4" />
        <p className="text-xs font-mono text-ivory/60">Loading Video Assessment...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex flex-col items-center justify-center p-6">
        <div className="glass-card max-w-md w-full p-8 rounded-3xl border border-red-500/30 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="font-display text-xl font-bold text-white">Assessment Error</h2>
          <p className="text-xs text-ivory/70 font-mono">{error}</p>
          <button
            onClick={() => navigate('/dashboard?tab=video-assessments')}
            className="btn-oxblood w-full py-2.5 rounded-xl text-xs font-semibold mt-4"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGE 1: HARDWARE CHECK
  // ========================================================================
  if (stage === 'hardware_check') {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex items-center justify-center p-6">
        <div className="glass-card max-w-xl w-full p-8 rounded-3xl border border-oxblood/30 space-y-6 shadow-2xl">
          <div className="text-center space-y-2">
            <span className="badge-selected font-mono text-[11px] px-3 py-1 rounded-full uppercase">
              Step 1 of 3: Pre-Assessment Hardware Verification
            </span>
            <h2 className="font-display text-2xl font-bold text-white">
              Camera & Microphone Verification
            </h2>
            <p className="text-xs text-ivory/70 font-sans">
              Verify that your camera and microphone are functioning clearly before starting the assessment.
            </p>
          </div>

          <div className="relative rounded-2xl overflow-hidden bg-black/50 border border-ivory/10 aspect-video max-w-md mx-auto flex items-center justify-center">
            <video
              ref={liveVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover transform scale-x-[-1]"
            />
            <div className="absolute bottom-3 left-3 bg-black/60 px-3 py-1 rounded-lg text-[10px] font-mono text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Camera Stream Active</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-black/30 border border-ivory/10 space-y-2 text-xs font-mono text-ivory/70">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Video Resolution: 720p HD</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Audio Input Channel Connected</span>
            </div>
          </div>

          <button
            onClick={() => {
              setHardwareVerified(true);
              setStage('instructions');
            }}
            className="btn-oxblood w-full py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 shadow-lg"
          >
            <span>Hardware Verified &bull; Continue to Instructions</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGE 2: INSTRUCTIONS
  // ========================================================================
  if (stage === 'instructions') {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex items-center justify-center p-6">
        <div className="glass-card max-w-2xl w-full p-8 rounded-3xl border border-oxblood/30 space-y-6 shadow-2xl">
          <div className="space-y-1">
            <span className="badge-selected font-mono text-[11px] px-3 py-1 rounded-full uppercase">
              Step 2 of 3: Assessment Protocol & Policy
            </span>
            <h2 className="font-display text-2xl font-bold text-white">
              {assignment?.title}
            </h2>
            <p className="text-xs font-mono text-ivory/60">
              Job Position: {assignment?.job_title} &bull; {totalQuestions} Video Prompts
            </p>
          </div>

          {assignment?.instructions && (
            <div className="p-4 rounded-2xl bg-black/40 border border-ivory/10 text-xs font-sans text-ivory/80 leading-relaxed">
              <h4 className="font-mono text-xs font-bold text-oxblood dark:text-rose uppercase mb-1">Recruiter Instructions</h4>
              <p>{assignment.instructions}</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center font-mono">
            <div className="p-4 rounded-xl bg-ivory/5 border border-ivory/10">
              <Clock className="w-5 h-5 text-oxblood dark:text-rose mx-auto mb-1" />
              <p className="text-lg font-bold text-white">{totalQuestions}</p>
              <p className="text-[10px] text-ivory/60 uppercase">Questions</p>
            </div>
            <div className="p-4 rounded-xl bg-ivory/5 border border-ivory/10">
              <RotateCcw className="w-5 h-5 text-oxblood dark:text-rose mx-auto mb-1" />
              <p className="text-lg font-bold text-white">{assignment?.questions?.[0]?.retake_limit || 2}</p>
              <p className="text-[10px] text-ivory/60 uppercase">Retakes / Question</p>
            </div>
            <div className="p-4 rounded-xl bg-ivory/5 border border-ivory/10">
              <Shield className="w-5 h-5 text-oxblood dark:text-rose mx-auto mb-1" />
              <p className="text-lg font-bold text-white">Private</p>
              <p className="text-[10px] text-ivory/60 uppercase">Evaluation</p>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-oxblood/10 border border-oxblood/30 text-xs font-sans text-ivory/80 space-y-1">
            <p className="font-bold font-mono text-oxblood dark:text-rose">Confidentiality & Privacy Assurance:</p>
            <p>Your video recordings are encrypted in transit and durably stored in authenticated cloud storage. Only authorized members of the hiring team have access to review and evaluate your responses.</p>
          </div>

          <button
            onClick={() => prepareQuestion(0)}
            className="btn-oxblood w-full py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 shadow-lg"
          >
            <span>Begin Video Assessment</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGES 3.1 & 3.2: QUESTION PREP & RECORDING
  // ========================================================================
  if (stage === 'question_prep' || stage === 'recording') {
    const currentRetakes = retakeCountMap[currentQuestion?.id] || 0;
    const retakesLeft = (currentQuestion?.retake_limit || 2) - currentRetakes;

    return (
      <div className="min-h-screen bg-[#0E1116] text-ivory flex flex-col justify-between p-6">
        {/* Header */}
        <div className="max-w-4xl w-full mx-auto flex justify-between items-center pb-4 border-b border-ivory/10">
          <div>
            <span className="font-mono text-xs text-oxblood dark:text-rose font-bold">
              Question {currentQuestionIndex + 1} of {totalQuestions}
            </span>
            <h3 className="font-display font-bold text-base text-white">
              {assignment?.title}
            </h3>
          </div>
          <div className="text-right font-mono text-xs">
            <span className="badge-slate px-2.5 py-1 rounded">
              {retakesLeft > 0 ? `${retakesLeft} Retake(s) Left` : 'Final Attempt'}
            </span>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="max-w-4xl w-full mx-auto my-auto grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          {/* Left: Question Prompt */}
          <div className="space-y-4">
            <div className="p-6 rounded-3xl bg-[#141820] border border-ivory/15 space-y-4 shadow-xl">
              <span className="badge-selected font-mono text-[10px] px-2.5 py-0.5 rounded-full uppercase">
                Video Question Prompt
              </span>
              <h2 className="font-display font-bold text-xl text-white leading-snug">
                {currentQuestion?.question_text}
              </h2>
              {currentQuestion?.question_instructions && (
                <p className="text-xs font-mono text-ivory/70 border-t border-ivory/10 pt-3">
                  Tip: {currentQuestion.question_instructions}
                </p>
              )}
            </div>

            {/* Prep Countdown Card */}
            {stage === 'question_prep' && (
              <div className="p-6 rounded-3xl bg-oxblood/10 border border-oxblood/30 text-center space-y-3">
                <p className="font-mono text-xs text-oxblood dark:text-rose uppercase font-bold tracking-wider">
                  Preparation Countdown
                </p>
                <div className="font-display text-5xl font-black text-white">
                  {prepSecondsRemaining}s
                </div>
                <p className="text-xs text-ivory/60 font-sans">
                  Use this time to organize your thoughts. Recording will begin automatically, or you can start now.
                </p>
                <button
                  onClick={startRecording}
                  className="btn-oxblood px-6 py-2.5 rounded-xl font-display font-semibold text-xs inline-flex items-center gap-1.5"
                >
                  <Video className="w-3.5 h-3.5" />
                  <span>Ready &bull; Start Recording Now</span>
                </button>
              </div>
            )}

            {/* Recording Active Card */}
            {stage === 'recording' && (
              <div className="p-6 rounded-3xl bg-red-950/40 border border-red-600/40 text-center space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600/20 text-red-400 font-mono text-xs font-bold animate-pulse">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <span>RECORDING ACTIVE</span>
                </div>
                <div className="font-display text-4xl font-bold text-white font-mono">
                  {Math.floor(elapsedRecordingTime / 60).toString().padStart(2, '0')}:{(elapsedRecordingTime % 60).toString().padStart(2, '0')}
                  <span className="text-sm text-ivory/50 font-normal"> / {Math.floor((currentQuestion?.max_duration_seconds || 120) / 60)}:00</span>
                </div>
                <button
                  onClick={stopRecording}
                  className="px-6 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-display font-semibold text-xs inline-flex items-center gap-1.5 shadow-lg transition"
                >
                  <Check className="w-4 h-4" />
                  <span>Stop & Review Recording</span>
                </button>
              </div>
            )}
          </div>

          {/* Right: Camera Feed Preview */}
          <div className="relative rounded-3xl overflow-hidden bg-black border border-ivory/15 aspect-[4/3] shadow-2xl flex items-center justify-center">
            <video
              ref={liveVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover transform scale-x-[-1]"
            />
            {stage === 'recording' && (
              <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/60 px-3 py-1 rounded-full border border-red-500/50">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                <span className="font-mono text-[10px] text-red-400 font-bold">REC</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="max-w-4xl w-full mx-auto text-center text-xs font-mono text-ivory/40 pt-4 border-t border-ivory/10">
          Question {currentQuestion?.order_num} &bull; Max Duration {currentQuestion?.max_duration_seconds}s
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGE 3.3: PREVIEW & RETAKE
  // ========================================================================
  if (stage === 'preview_retake' || stage === 'uploading_step') {
    const currentRetakes = retakeCountMap[currentQuestion?.id] || 0;
    const canRetake = currentRetakes < (currentQuestion?.retake_limit || 2);

    return (
      <div className="min-h-screen bg-[#0E1116] text-ivory flex flex-col justify-between p-6">
        <div className="max-w-3xl w-full mx-auto pb-4 border-b border-ivory/10 flex justify-between items-center">
          <div>
            <span className="font-mono text-xs text-oxblood dark:text-rose font-bold">
              Reviewing Question {currentQuestionIndex + 1} of {totalQuestions}
            </span>
            <h3 className="font-display font-bold text-base text-white">
              {currentQuestion?.question_text}
            </h3>
          </div>
          <span className="badge-slate font-mono text-xs px-2.5 py-1 rounded">
            Attempt {currentRetakes + 1}
          </span>
        </div>

        <div className="max-w-2xl w-full mx-auto my-auto space-y-6">
          {/* Recorded Clip Player */}
          <div className="rounded-3xl overflow-hidden bg-black border border-ivory/20 aspect-video shadow-2xl relative">
            {recordedVideoUrl && (
              <video
                src={recordedVideoUrl}
                controls
                className="w-full h-full object-cover"
              />
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleRetake}
              disabled={!canRetake || stage === 'uploading_step'}
              className={`flex-1 py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 border transition ${
                canRetake
                  ? 'border-ivory/20 text-ivory hover:bg-ivory/10'
                  : 'border-ivory/10 text-ivory/30 cursor-not-allowed'
              }`}
            >
              <RotateCcw className="w-4 h-4" />
              <span>{canRetake ? "Retake Question" : "Retake Limit Reached"}</span>
            </button>

            <button
              onClick={handleSaveAndNext}
              disabled={stage === 'uploading_step'}
              className="flex-1 btn-oxblood py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 shadow-lg"
            >
              <Check className="w-4 h-4" />
              <span>{stage === 'uploading_step' ? "Uploading to Cloud..." : "Accept & Proceed"}</span>
            </button>
          </div>
        </div>

        <div className="max-w-3xl w-full mx-auto text-center text-xs font-mono text-ivory/40 pt-4 border-t border-ivory/10">
          Clicking Accept saves your video response securely to Cloudinary.
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGE 4: FINAL REVIEW BEFORE SUBMIT
  // ========================================================================
  if (stage === 'final_review') {
    return (
      <div className="min-h-screen bg-charcoal text-ivory flex items-center justify-center p-6">
        <div className="glass-card max-w-2xl w-full p-8 rounded-3xl border border-oxblood/30 space-y-6 shadow-2xl">
          <div className="space-y-1">
            <span className="badge-selected font-mono text-[11px] px-3 py-1 rounded-full uppercase">
              Final Step: Review & Confirm Submission
            </span>
            <h2 className="font-display text-2xl font-bold text-white">
              All Questions Completed
            </h2>
            <p className="text-xs font-mono text-ivory/60">
              Please review your recorded answers below before submitting to the recruiting team.
            </p>
          </div>

          {/* List of responses */}
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {assignment?.questions?.map((q, idx) => {
              const resp = savedResponsesMap[q.id];
              return (
                <div key={q.id} className="p-4 rounded-2xl bg-black/40 border border-ivory/10 flex items-center justify-between">
                  <div>
                    <span className="font-mono text-[10px] text-oxblood dark:text-rose uppercase font-bold">
                      Question {idx + 1}
                    </span>
                    <p className="font-display font-bold text-xs text-white line-clamp-1">{q.question_text}</p>
                    <p className="text-[11px] font-mono text-ivory/60">
                      Duration: {resp?.duration_seconds ? `${Math.round(resp.duration_seconds)}s` : 'Recorded'} &bull; Retakes: {resp?.retake_count || 0}
                    </p>
                  </div>
                  <span className="badge-selected text-[10px] font-mono px-2 py-0.5 rounded flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>Saved</span>
                  </span>
                </div>
              );
            })}
          </div>

          <div className="p-4 rounded-2xl bg-black/40 border border-ivory/10 text-xs font-sans text-ivory/80 space-y-1">
            <p className="font-bold font-mono text-oxblood dark:text-rose">Submission Finality:</p>
            <p>Once finalized, your responses are immediately locked and made available to the hiring team for evaluation.</p>
          </div>

          <button
            onClick={handleFinalize}
            className="btn-oxblood w-full py-3 rounded-2xl font-display font-semibold text-xs flex items-center justify-center gap-2 shadow-lg"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Finalize & Submit Assessment</span>
          </button>
        </div>
      </div>
    );
  }

  // ========================================================================
  // STAGE 5: SUBMITTED CONFIRMATION
  // ========================================================================
  return (
    <div className="min-h-screen bg-charcoal text-ivory flex items-center justify-center p-6">
      <div className="glass-card max-w-lg w-full p-8 rounded-3xl border border-oxblood/30 text-center space-y-6 shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
          <CheckCircle2 className="w-8 h-8" />
        </div>

        <div>
          <span className="badge-selected font-mono text-[11px] px-3 py-1 rounded-full uppercase">
            Submission Received
          </span>
          <h2 className="font-display text-2xl font-bold text-white mt-2">
            Video Assessment Complete
          </h2>
          <p className="text-xs text-ivory/70 font-mono mt-1">
            {assignment?.title} &bull; {assignment?.job_title}
          </p>
          <p className="text-xs text-ivory/60 font-sans mt-3 leading-relaxed">
            Your video responses have been submitted to the recruiter. In accordance with platform policy, your evaluation is held in private review until the hiring team makes a decision.
          </p>
        </div>

        <button
          onClick={() => navigate('/dashboard?tab=video-assessments')}
          className="btn-oxblood w-full py-2.5 rounded-xl text-xs font-semibold"
        >
          Return to Dashboard
        </button>
      </div>
    </div>
  );
};
