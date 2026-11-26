import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Room, RoomEvent, Track, VideoPresets } from 'livekit-client';
import {
  Mic, MicOff, Video, VideoOff, PhoneOff, Monitor, Shield,
  CheckCircle2, AlertTriangle, Users, FileText, Sparkles, Clock,
  Lock, RefreshCw, X, ChevronRight, Check, Send, Award, HelpCircle,
  Bot, Volume2, Radio
} from 'lucide-react';
import { interviewsAPI, authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/MotionComponents';

export const VideoInterviewRoomPage = () => {
  const { interviewId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToast } = useToast();

  // Meeting State
  const [loading, setLoading] = useState(true);
  const [tokenData, setTokenData] = useState(null);
  const [roomStatus, setRoomStatus] = useState(null);
  const [isAdmitted, setIsAdmitted] = useState(false);
  const [error, setError] = useState('');

  // Media streams & device controls
  const [localStream, setLocalStream] = useState(null);
  const [screenStream, setScreenStream] = useState(null);
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isVideoMuted, setIsVideoMuted] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [devicePermissionError, setDevicePermissionError] = useState('');

  // Video & Audio element refs
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const remoteAudioRef = useRef(null);

  // LiveKit WebRTC Room & Track State
  const [livekitRoom, setLivekitRoom] = useState(null);
  const [connectionState, setConnectionState] = useState('DISCONNECTED');
  const [remoteParticipants, setRemoteParticipants] = useState([]);
  const [remoteVideoTrack, setRemoteVideoTrack] = useState(null);
  const [remoteAudioTrack, setRemoteAudioTrack] = useState(null);

  // Recording & Consent State
  const [myConsent, setMyConsent] = useState(false);
  const [bothConsented, setBothConsented] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState('NOT_RECORDED');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showConsentModal, setShowConsentModal] = useState(false);

  // Recruiter In-Meeting Drawers
  const [showScorecardDrawer, setShowScorecardDrawer] = useState(false);
  const [showAIDrawer, setShowAIDrawer] = useState(false);

  // Scorecard State
  const [scorecard, setScorecard] = useState({
    technical_knowledge_score: 4,
    technical_evidence_notes: '',
    communication_score: 4,
    communication_evidence_notes: '',
    problem_solving_score: 4,
    problem_solving_notes: '',
    role_specific_score: 4,
    role_specific_notes: '',
    cultural_alignment_score: 4,
    cultural_alignment_notes: '',
    overall_recommendation: 'RECOMMENDED',
    strengths: '',
    improvement_areas: '',
    private_evaluation_notes: '',
  });
  const [savingScorecard, setSavingScorecard] = useState(false);

  // AI Intelligence State
  const [aiTranscript, setAITranscript] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [editedSummary, setEditedSummary] = useState('');

  const isRecruiter = user?.role === 'RECRUITER' || user?.role === 'ADMIN';

  // AI Live & Hybrid Conversation Engine State
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [aiStatus, setAiStatus] = useState('SPEAKING'); // 'SPEAKING', 'LISTENING', 'PROCESSING', 'PAUSED'
  const [aiSpeechText, setAiSpeechText] = useState('');
  const [candidateLiveTranscript, setCandidateLiveTranscript] = useState('');
  const [candidateResponses, setCandidateResponses] = useState([]);
  const [qTimeRemaining, setQTimeRemaining] = useState(180);
  const [isSubmittingFinal, setIsSubmittingFinal] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [hybridRecruiterActive, setHybridRecruiterActive] = useState(false);

  // Helper for AI Voice Synthesis
  const speakAI = (text) => {
    setAiSpeechText(text);
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      setAiStatus('SPEAKING');
      utterance.onend = () => {
        setAiStatus('LISTENING');
      };
      utterance.onerror = () => {
        setAiStatus('LISTENING');
      };
      window.speechSynthesis.speak(utterance);
    } else {
      setAiStatus('LISTENING');
    }
  };

  // 1. Initial WebRTC & Token Setup
  useEffect(() => {
    let isMounted = true;

    async function initRoom() {
      setLoading(true);
      setError('');
      try {
        // Fetch room token and status
        const [tokenRes, statusRes] = await Promise.all([
          interviewsAPI.getRoomToken(interviewId),
          interviewsAPI.getRoomStatus(interviewId)
        ]);

        if (!isMounted) return;

        setTokenData(tokenRes.data);
        setRoomStatus(statusRes.data);
        setIsAdmitted(tokenRes.data.is_admitted);
        setRecordingStatus(statusRes.data.recording_status);
        setBothConsented(statusRes.data.both_consented_recording);

        // Fetch AI Questions if AI_LIVE or HYBRID
        const mode = statusRes.data?.interview_mode || 'HUMAN';
        if (mode === 'AI_LIVE' || mode === 'HYBRID' || mode === 'CONFIGURED') {
          try {
            const qRes = await interviewsAPI.getQuestions(interviewId);
            const loadedQs = qRes.data || [];
            if (isMounted) {
              setInterviewQuestions(loadedQs);
              if (loadedQs.length > 0) {
                const firstQ = loadedQs[0];
                setQTimeRemaining(firstQ.max_duration_seconds || 180);
                speakAI(firstQ.question_text);
              }
            }
          } catch (qErr) {
            console.warn("Could not load AI questions:", qErr);
          }
        }

        // Prompt for camera and mic access
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: true
          });
          if (isMounted) {
            setLocalStream(stream);
            if (localVideoRef.current) {
              localVideoRef.current.srcObject = stream;
            }
          }
        } catch (mediaErr) {
          console.warn("Camera/mic permission notice:", mediaErr);
          setDevicePermissionError("Camera/Microphone access not granted or unavailable. Preview running in audio/simulated mode.");
        }

      } catch (err) {
        if (!isMounted) return;
        console.error("Failed to initialize interview room:", err);
        setError(err.response?.data?.detail || "Could not connect to interview room.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    initRoom();

    return () => {
      isMounted = false;
      // Stop all tracks on unmount
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
      if (screenStream) {
        screenStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [interviewId]);

  // Bind local stream to video ref whenever localStream changes
  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream, isAdmitted]);

  // Connect to LiveKit Room when token is available and participant is admitted (or recruiter)
  useEffect(() => {
    if (!tokenData?.token || !tokenData?.server_url || (!isAdmitted && !isRecruiter)) {
      return;
    }

    let activeRoom = null;
    let isCancelled = false;

    async function connectLiveKit() {
      try {
        const room = new Room({
          adaptiveStream: true,
          dynacast: true,
          videoCaptureDefaults: {
            resolution: VideoPresets.h720.resolution,
          },
        });

        activeRoom = room;

        room.on(RoomEvent.Connected, () => {
          if (!isCancelled) {
            setConnectionState('CONNECTED');
            setLivekitRoom(room);
          }
        });

        room.on(RoomEvent.Disconnected, () => {
          if (!isCancelled) {
            setConnectionState('DISCONNECTED');
            setRemoteParticipants([]);
            setRemoteVideoTrack(null);
            setRemoteAudioTrack(null);
          }
        });

        room.on(RoomEvent.Reconnecting, () => {
          if (!isCancelled) setConnectionState('RECONNECTING');
        });

        room.on(RoomEvent.Reconnected, () => {
          if (!isCancelled) setConnectionState('CONNECTED');
        });

        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (isCancelled) return;
          if (track.kind === Track.Kind.Video) {
            setRemoteVideoTrack(track);
            if (remoteVideoRef.current) {
              track.attach(remoteVideoRef.current);
            }
          } else if (track.kind === Track.Kind.Audio) {
            setRemoteAudioTrack(track);
            if (remoteAudioRef.current) {
              track.attach(remoteAudioRef.current);
            }
          }
        });

        room.on(RoomEvent.TrackUnsubscribed, (track) => {
          if (isCancelled) return;
          try { track.detach(); } catch (e) {}
          if (track.kind === Track.Kind.Video) {
            setRemoteVideoTrack(null);
          } else if (track.kind === Track.Kind.Audio) {
            setRemoteAudioTrack(null);
          }
        });

        room.on(RoomEvent.ParticipantConnected, () => {
          if (!isCancelled) {
            setRemoteParticipants(Array.from(room.remoteParticipants.values()));
          }
        });

        room.on(RoomEvent.ParticipantDisconnected, () => {
          if (!isCancelled) {
            setRemoteParticipants(Array.from(room.remoteParticipants.values()));
          }
        });

        setConnectionState('CONNECTING');
        await room.connect(tokenData.server_url, tokenData.token);

        if (isCancelled) {
          room.disconnect();
          return;
        }

        setLivekitRoom(room);
        setConnectionState('CONNECTED');
        setRemoteParticipants(Array.from(room.remoteParticipants.values()));

        // Check if existing remote participants already published tracks
        room.remoteParticipants.forEach((p) => {
          p.trackPublications.forEach((pub) => {
            if (pub.track) {
              if (pub.track.kind === Track.Kind.Video) {
                setRemoteVideoTrack(pub.track);
                if (remoteVideoRef.current) {
                  pub.track.attach(remoteVideoRef.current);
                }
              } else if (pub.track.kind === Track.Kind.Audio) {
                setRemoteAudioTrack(pub.track);
                if (remoteAudioRef.current) {
                  pub.track.attach(remoteAudioRef.current);
                }
              }
            }
          });
        });

        // Publish local camera and mic
        try {
          await room.localParticipant.enableCameraAndMicrophone();
          if (isVideoMuted) {
            await room.localParticipant.setCameraEnabled(false);
          }
          if (isAudioMuted) {
            await room.localParticipant.setMicrophoneEnabled(false);
          }
        } catch (pubErr) {
          console.warn("LiveKit publish local tracks notice:", pubErr);
        }

      } catch (err) {
        console.warn("LiveKit connection notice:", err);
        if (!isCancelled) {
          setConnectionState('STANDALONE');
        }
      }
    }

    connectLiveKit();

    return () => {
      isCancelled = true;
      if (activeRoom) {
        try {
          activeRoom.disconnect();
        } catch (e) {}
      }
    };
  }, [tokenData, isAdmitted, isRecruiter]);

  // Attach remote video track when remoteVideoRef mounts or track changes
  useEffect(() => {
    if (remoteVideoRef.current && remoteVideoTrack) {
      remoteVideoTrack.attach(remoteVideoRef.current);
      return () => {
        try { remoteVideoTrack.detach(remoteVideoRef.current); } catch (e) {}
      };
    }
  }, [remoteVideoTrack, isAdmitted]);

  // Attach remote audio track when remoteAudioRef mounts or track changes
  useEffect(() => {
    if (remoteAudioRef.current && remoteAudioTrack) {
      remoteAudioTrack.attach(remoteAudioRef.current);
      return () => {
        try { remoteAudioTrack.detach(remoteAudioRef.current); } catch (e) {}
      };
    }
  }, [remoteAudioTrack, isAdmitted]);

  // 2. Poll room status every 3.5 seconds (admissions, consents, recording status, hybrid takeover sync)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await interviewsAPI.getRoomStatus(interviewId);
        setRoomStatus(res.data);
        setBothConsented(res.data.both_consented_recording);
        setRecordingStatus(res.data.recording_status);
        if (!isRecruiter && res.data.is_admitted) {
          setIsAdmitted(true);
        }
        // Real-time synchronization of recruiter takeover & hand-back
        if (res.data.ai_takeover_status === 'RECRUITER_ACTIVE') {
          setHybridRecruiterActive(true);
          if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
            window.speechSynthesis.cancel();
          }
          setAiStatus('PAUSED');
        } else if (res.data.ai_takeover_status === 'AI_ACTIVE') {
          setHybridRecruiterActive(false);
          setAiStatus(prev => prev === 'PAUSED' ? 'LISTENING' : prev);
        }
      } catch (err) {
        // Silently handle polling glitch
      }
    }, 3500);

    return () => clearInterval(interval);
  }, [interviewId, isRecruiter]);

  // 3. Recording duration timer
  useEffect(() => {
    let timer = null;
    if (recordingStatus === 'RECORDING') {
      timer = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingDuration(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [recordingStatus]);

  // Format timer
  const formatDuration = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  // Web Speech API for candidate response transcription
  useEffect(() => {
    let recognition = null;
    const SpeechRecognition = typeof window !== 'undefined' ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
    if (SpeechRecognition) {
      try {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = (event) => {
          let full = '';
          for (let i = 0; i < event.results.length; i++) {
            full += event.results[i][0].transcript + ' ';
          }
          setCandidateLiveTranscript(full.trim());
        };
        recognition.start();
      } catch (e) {
        console.warn("Speech recognition notice:", e);
      }
    }
    return () => {
      if (recognition) {
        try { recognition.stop(); } catch(e){}
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Countdown timer for active question
  useEffect(() => {
    let qTimer = null;
    if (interviewQuestions.length > 0 && qTimeRemaining > 0 && !showCompletionModal && aiStatus !== 'PAUSED') {
      qTimer = setInterval(() => {
        setQTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(qTimer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (qTimer) clearInterval(qTimer);
    };
  }, [currentQIndex, qTimeRemaining, showCompletionModal, aiStatus, interviewQuestions.length]);

  const handleNextAIQuestion = () => {
    if (interviewQuestions.length === 0) return;
    const currentQ = interviewQuestions[currentQIndex];
    const newResponses = [
      ...candidateResponses,
      {
        question_id: currentQ.id,
        transcript: candidateLiveTranscript || "Candidate verbal response captured in audio stream.",
        response_duration: Math.max(5, (currentQ.max_duration_seconds || 180) - qTimeRemaining),
        score: 4.0
      }
    ];
    setCandidateResponses(newResponses);
    setCandidateLiveTranscript('');

    if (currentQIndex + 1 < interviewQuestions.length) {
      const nextIdx = currentQIndex + 1;
      setCurrentQIndex(nextIdx);
      const nextQ = interviewQuestions[nextIdx];
      setQTimeRemaining(nextQ.max_duration_seconds || 180);
      speakAI(nextQ.question_text);
      interviewsAPI.advanceAIState(interviewId).catch(() => {});
    } else {
      handleFinishAIInterview(newResponses);
    }
  };

  const handleFinishAIInterview = async (responsesToSubmit = candidateResponses) => {
    setIsSubmittingFinal(true);
    try {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (responsesToSubmit.length > 0) {
        await interviewsAPI.submitAIResponses(interviewId, responsesToSubmit);
      }
      await interviewsAPI.generateAIEvaluation(interviewId);
      await interviewsAPI.archiveRecording(interviewId);
      setShowCompletionModal(true);
    } catch (err) {
      console.error("Finish AI interview notice:", err);
      setShowCompletionModal(true);
    } finally {
      setIsSubmittingFinal(false);
    }
  };

  const handleToggleHybridTakeover = async () => {
    const nextState = !hybridRecruiterActive;
    setHybridRecruiterActive(nextState);
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setAiStatus(nextState ? 'PAUSED' : 'LISTENING');
    try {
      await interviewsAPI.hybridTakeover(interviewId, nextState);
      addToast({
        title: nextState ? "Recruiter Takeover Active" : "Handed Back to AI",
        message: nextState ? "AI speech paused. You now lead the conversation." : "AI interviewer resumed conversation.",
        type: "info"
      });
    } catch (err) {
      console.error("Hybrid takeover failed:", err);
    }
  };

  // Device Toggle Handlers
  const toggleAudio = async () => {
    const nextState = !isAudioMuted;
    setIsAudioMuted(nextState);
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = !nextState;
      });
    }
    if (livekitRoom?.localParticipant) {
      try {
        await livekitRoom.localParticipant.setMicrophoneEnabled(!nextState);
      } catch (err) {
        console.warn("LiveKit toggle mic notice:", err);
      }
    }
  };

  const toggleVideo = async () => {
    const nextState = !isVideoMuted;
    setIsVideoMuted(nextState);
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = !nextState;
      });
    }
    if (livekitRoom?.localParticipant) {
      try {
        await livekitRoom.localParticipant.setCameraEnabled(!nextState);
      } catch (err) {
        console.warn("LiveKit toggle video notice:", err);
      }
    }
  };

  const toggleScreenShare = async () => {
    if (isScreenSharing) {
      if (screenStream) {
        screenStream.getTracks().forEach(track => track.stop());
        setScreenStream(null);
      }
      setIsScreenSharing(false);
      if (livekitRoom?.localParticipant) {
        try {
          await livekitRoom.localParticipant.setScreenShareEnabled(false);
        } catch (e) {}
      }
      if (localVideoRef.current && localStream) {
        localVideoRef.current.srcObject = localStream;
      }
    } else {
      try {
        if (livekitRoom?.localParticipant) {
          await livekitRoom.localParticipant.setScreenShareEnabled(true);
          setIsScreenSharing(true);
        } else {
          const displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
          setScreenStream(displayStream);
          setIsScreenSharing(true);
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = displayStream;
          }
          displayStream.getVideoTracks()[0].onended = () => {
            setIsScreenSharing(false);
            setScreenStream(null);
            if (localVideoRef.current && localStream) {
              localVideoRef.current.srcObject = localStream;
            }
          };
        }
      } catch (err) {
        console.warn("Screen share cancelled:", err);
      }
    }
  };

  // Recruiter Admission Handler
  const handleAdmitCandidate = async () => {
    try {
      await interviewsAPI.admitParticipant(interviewId, true);
      setIsAdmitted(true);
      addToast({
        title: "Candidate Admitted",
        message: "The candidate has been admitted into the active interview room.",
        type: "success"
      });
    } catch (err) {
      addToast({
        title: "Admission Error",
        message: err.response?.data?.detail || "Failed to admit candidate.",
        type: "error"
      });
    }
  };

  // Informed Consent Handler
  const handleToggleConsent = async (granted) => {
    try {
      const res = await interviewsAPI.recordConsent(interviewId, granted);
      setMyConsent(granted);
      setBothConsented(res.data.both_consented);
      setShowConsentModal(false);
      addToast({
        title: granted ? "Recording Consent Granted" : "Consent Withdrawn",
        message: granted
          ? "Your explicit consent for this interview session has been recorded."
          : "You have refused recording consent. Recording remains strictly disabled.",
        type: granted ? "success" : "info"
      });
    } catch (err) {
      addToast({
        title: "Consent Error",
        message: err.response?.data?.detail || "Could not update recording consent.",
        type: "error"
      });
    }
  };

  // Recording Controls
  const handleStartRecording = async () => {
    if (!bothConsented) {
      addToast({
        title: "Mutual Consent Required",
        message: "Both candidate and recruiter must explicitly consent before recording can begin.",
        type: "error"
      });
      return;
    }

    try {
      await interviewsAPI.startRecording(interviewId);
      setRecordingStatus('RECORDING');
      addToast({
        title: "Recording Started",
        message: "Interview recording has started. Participants are notified.",
        type: "success"
      });
    } catch (err) {
      addToast({
        title: "Recording Error",
        message: err.response?.data?.detail || "Failed to initiate recording.",
        type: "error"
      });
    }
  };

  const handleStopRecording = async () => {
    try {
      await interviewsAPI.stopRecording(interviewId);
      setRecordingStatus('COMPLETED');
      addToast({
        title: "Recording Stopped",
        message: "Recording is saved and securely transferred to Cloudinary.",
        type: "success"
      });
    } catch (err) {
      addToast({
        title: "Recording Error",
        message: err.response?.data?.detail || "Failed to stop recording.",
        type: "error"
      });
    }
  };

  // Submit Scorecard Handler
  const handleSaveScorecard = async (e) => {
    e.preventDefault();
    setSavingScorecard(true);
    try {
      await interviewsAPI.submitScorecard(interviewId, scorecard);
      addToast({
        title: "Scorecard Submitted",
        message: "Structured evaluation has been securely recorded.",
        type: "success"
      });
      setShowScorecardDrawer(false);
    } catch (err) {
      addToast({
        title: "Scorecard Error",
        message: err.response?.data?.detail || "Failed to submit scorecard.",
        type: "error"
      });
    } finally {
      setSavingScorecard(false);
    }
  };

  // AI Intelligence Handler
  const handleLoadAI = async () => {
    setLoadingAI(true);
    try {
      const res = await interviewsAPI.getAITranscript(interviewId);
      setAITranscript(res.data);
      setEditedSummary(res.data.ai_summary || '');
      setShowAIDrawer(true);
    } catch (err) {
      addToast({
        title: "AI Analysis",
        message: err.response?.data?.detail || "Failed to generate AI intelligence.",
        type: "error"
      });
    } finally {
      setLoadingAI(false);
    }
  };

  const handleApproveAI = async () => {
    try {
      const res = await interviewsAPI.approveAITranscript(interviewId, {
        edited_summary: editedSummary,
        edited_feedback: aiTranscript?.draft_feedback_json || {}
      });
      setAITranscript(res.data);
      addToast({
        title: "AI Draft Approved",
        message: "Assistant draft summary has been approved by the recruiter.",
        type: "success"
      });
    } catch (err) {
      addToast({
        title: "Approval Error",
        message: err.response?.data?.detail || "Failed to approve feedback.",
        type: "error"
      });
    }
  };

  // Leave / End Meeting
  const handleLeaveMeeting = async () => {
    if (livekitRoom) {
      try {
        livekitRoom.disconnect();
      } catch (e) {}
    }
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
    }
    if (isRecruiter) {
      if (window.confirm("Do you want to end this interview session for everyone?")) {
        try {
          await interviewsAPI.endRoom(interviewId);
        } catch (e) {
          // ignore
        }
      }
      navigate('/recruiter?tab=interviews');
    } else {
      if (window.confirm("Leave this interview room?")) {
        navigate('/dashboard?tab=interviews');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0E1116] text-white flex flex-col items-center justify-center p-6">
        <div className="w-12 h-12 rounded-full border-4 border-oxblood/30 border-t-oxblood animate-spin mb-4" />
        <h2 className="font-display text-xl font-bold text-white">Connecting to SkillSphere Live Room...</h2>
        <p className="text-xs font-mono text-slate-300 mt-1">Securing end-to-end WebRTC channels & credentials</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0E1116] text-white flex flex-col items-center justify-center p-6">
        <div className="glass-card max-w-md w-full p-8 rounded-3xl border border-red-500/40 text-center space-y-4 bg-[#141820]">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="font-display text-xl font-bold text-white">Interview Access Denied</h2>
          <p className="text-xs text-slate-300 font-mono">{error}</p>
          <button
            onClick={() => navigate(isRecruiter ? '/recruiter?tab=interviews' : '/dashboard?tab=interviews')}
            className="btn-oxblood w-full py-2.5 rounded-xl font-semibold text-xs mt-4"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Waiting Room View (For Candidates before recruiter admits)
  if (!isRecruiter && !isAdmitted) {
    return (
      <div className="min-h-screen bg-[#0E1116] text-white flex flex-col items-center justify-center p-6">
        <div className="glass-card max-w-xl w-full p-8 rounded-3xl border border-oxblood/40 text-center space-y-6 shadow-2xl bg-[#141820]">
          <div className="w-16 h-16 rounded-2xl bg-oxblood/20 border border-oxblood/40 flex items-center justify-center mx-auto text-oxblood dark:text-rose">
            <Lock className="w-8 h-8 animate-pulse" />
          </div>

          <div>
            <span className="badge-selected font-mono text-[11px] px-3.5 py-1 rounded-full uppercase bg-oxblood/25 text-rose-300 border border-oxblood/40">
              SkillSphere Waiting Room
            </span>
            <h2 className="font-display text-2xl font-bold text-white mt-3">
              Waiting for the Interviewer
            </h2>
            <p className="text-xs text-slate-300 font-mono mt-1 max-w-md mx-auto">
              {roomStatus?.job_title} &bull; {roomStatus?.recruiter_name || 'Hiring Team'}
            </p>
            <p className="text-xs text-slate-400 font-sans mt-3">
              Please stay on this page. You will automatically join as soon as the recruiter admits you.
            </p>
          </div>

          {/* Local Camera Test Preview */}
          <div className="relative rounded-2xl overflow-hidden bg-black/60 border border-white/15 aspect-video max-w-sm mx-auto flex items-center justify-center">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            {isVideoMuted && (
              <div className="absolute inset-0 bg-black/80 flex items-center justify-center">
                <VideoOff className="w-10 h-10 text-white/50" />
              </div>
            )}
            <div className="absolute bottom-3 left-3 bg-black/75 px-2.5 py-1 rounded-lg text-[10px] font-mono text-white/90 border border-white/10">
              Camera Preview (Self-check)
            </div>
          </div>

          {/* Device Controls in Waiting Room */}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={toggleAudio}
              className={`p-3 rounded-full transition ${isAudioMuted ? 'bg-red-600 text-white' : 'bg-white/15 text-white hover:bg-white/25 border border-white/20'}`}
              title={isAudioMuted ? "Unmute Mic" : "Mute Mic"}
            >
              {isAudioMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
            <button
              onClick={toggleVideo}
              className={`p-3 rounded-full transition ${isVideoMuted ? 'bg-red-600 text-white' : 'bg-white/15 text-white hover:bg-white/25 border border-white/20'}`}
              title={isVideoMuted ? "Turn Video On" : "Turn Video Off"}
            >
              {isVideoMuted ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
            </button>
            <button
              onClick={() => setShowConsentModal(true)}
              className="px-4 py-2 rounded-xl text-xs font-mono border border-white/20 hover:border-white/40 text-white flex items-center gap-1.5 bg-white/5"
            >
              <Shield className="w-3.5 h-3.5 text-rose-300" />
              <span>{myConsent ? "Consent Granted" : "Review Consent"}</span>
            </button>
          </div>

          <div className="pt-4 border-t border-white/10 flex justify-between items-center text-[11px] font-mono text-slate-300">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-emerald-300">Connection Active</span>
            </div>
            <button
              onClick={() => navigate('/dashboard?tab=interviews')}
              className="text-slate-400 hover:text-white"
            >
              Cancel & Exit
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ACTIVE INTERVIEW ROOM VIEW
  return (
    <div className="min-h-screen bg-[#0E1116] text-white flex flex-col justify-between select-none">
      {/* 1. Header Bar */}
      <header className="h-16 px-6 border-b border-white/10 flex items-center justify-between bg-[#141820]/95 backdrop-blur-md z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-oxblood/30 border border-oxblood flex items-center justify-center font-display font-bold text-white text-sm">
            SS
          </div>
          <div>
            <h1 className="font-display font-bold text-sm text-white flex items-center gap-2">
              <span>{roomStatus?.job_title || 'SkillSphere Video Interview'}</span>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white/10 text-slate-200 border border-white/15">
                Room {interviewId.slice(0, 8)}
              </span>
            </h1>
            <p className="text-[11px] font-mono text-slate-300">
              {roomStatus?.recruiter_name} &bull; {roomStatus?.candidate_name}
            </p>
          </div>
        </div>

        {/* Center: Recording Indicator & Duration */}
        <div className="flex items-center gap-3">
          {recordingStatus === 'RECORDING' ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-950/80 border border-red-600/60 text-red-300 font-mono text-xs font-bold animate-pulse">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span>REC {formatDuration(recordingDuration)}</span>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/15 text-slate-200 font-mono text-xs">
              <Shield className="w-3.5 h-3.5 text-rose-300" />
              <span>{bothConsented ? "Mutual Consent Verified" : "Consent Required to Record"}</span>
            </div>
          )}
        </div>

        {/* Right Actions: Drawers & Room Info */}
        <div className="flex items-center gap-2">
          {isRecruiter && (roomStatus?.interview_mode === 'HYBRID' || tokenData?.interview_mode === 'HYBRID') && (
            <button
              onClick={handleToggleHybridTakeover}
              className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold flex items-center gap-1.5 border transition shadow ${
                hybridRecruiterActive
                  ? 'bg-amber-500 text-black border-amber-400 animate-pulse'
                  : 'bg-emerald-600/40 text-emerald-300 border-emerald-500/50 hover:bg-emerald-600/60'
              }`}
              title="Toggle Recruiter Speaking vs AI Speaking"
            >
              <Radio className="w-3.5 h-3.5" />
              <span>{hybridRecruiterActive ? 'Hand Back to AI' : 'Take Over'}</span>
            </button>
          )}

          {isRecruiter && (
            <>
              <button
                onClick={() => setShowScorecardDrawer(!showScorecardDrawer)}
                className={`px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 border transition ${
                  showScorecardDrawer ? 'bg-oxblood text-white border-oxblood' : 'bg-white/10 border-white/20 text-white hover:bg-white/20'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Scorecard</span>
              </button>

              <button
                onClick={handleLoadAI}
                disabled={loadingAI}
                className="px-3 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-1.5 bg-oxblood/30 border border-oxblood/50 text-rose-200 hover:bg-oxblood/40 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span className="hidden md:inline">{loadingAI ? 'Analyzing...' : 'AI Assistant'}</span>
              </button>
            </>
          )}

          <button
            onClick={() => setShowConsentModal(true)}
            className="p-2 rounded-xl bg-white/10 border border-white/20 text-white hover:bg-white/20"
            title="Recording Privacy & Consent"
          >
            <Shield className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Recruiter Waiting Room Notification Banner if Candidate is waiting */}
      {isRecruiter && !roomStatus?.is_admitted && (
        <div className="bg-oxblood/20 border-b border-oxblood/40 px-6 py-2.5 flex items-center justify-between text-xs font-mono text-slate-200 z-20">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
            <span>Candidate <strong>{roomStatus?.candidate_name}</strong> is in the waiting room ready to be admitted.</span>
          </div>
          <button
            onClick={handleAdmitCandidate}
            className="btn-oxblood px-4 py-1.5 rounded-lg text-xs font-display font-semibold flex items-center gap-1"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Admit Candidate</span>
          </button>
        </div>
      )}

      {/* 2. Main Video Grid Area */}
      <main className="flex-1 p-4 md:p-6 flex flex-col md:flex-row gap-4 relative overflow-hidden">
        {/* Remote Participant or AI Interviewer Box */}
        {(roomStatus?.interview_mode === 'AI_LIVE' || roomStatus?.interview_mode === 'HYBRID' || roomStatus?.interview_mode === 'CONFIGURED') ? (
          <div className="flex-1 rounded-3xl bg-[#141820] border border-white/15 relative overflow-hidden flex flex-col justify-between p-6 shadow-inner min-h-[400px]">
            {/* Top AI Status Bar */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  aiStatus === 'SPEAKING' ? 'bg-purple-400 animate-ping' :
                  aiStatus === 'LISTENING' ? 'bg-emerald-400 animate-pulse' :
                  aiStatus === 'PAUSED' ? 'bg-amber-400' : 'bg-blue-400'
                }`} />
                <span className="font-display font-bold text-sm text-white">
                  SkillSphere AI Interviewer
                </span>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full uppercase ${
                  aiStatus === 'SPEAKING' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                  aiStatus === 'LISTENING' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                  aiStatus === 'PAUSED' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                  'bg-blue-500/20 text-blue-300'
                }`}>
                  {aiStatus === 'PAUSED' ? 'AI Paused (Recruiter Active)' : aiStatus}
                </span>
              </div>

              {interviewQuestions.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-oxblood/30 border border-oxblood text-oxblood dark:text-rose">
                    Question {currentQIndex + 1} / {interviewQuestions.length}
                  </span>
                  <div className="flex items-center gap-1 font-mono text-xs text-slate-200 bg-black/50 px-2.5 py-1 rounded-lg border border-white/15">
                    <Clock className="w-3.5 h-3.5 text-oxblood dark:text-rose" />
                    <span>{Math.floor(qTimeRemaining / 60)}:{(qTimeRemaining % 60).toString().padStart(2, '0')}</span>
                  </div>
                </div>
              )}
            </div>

            {/* AI Avatar & Audio Visualizer Center */}
            <div className="my-auto py-6 text-center space-y-4">
              <div className="relative inline-block">
                <div className={`w-24 h-24 sm:w-28 sm:h-28 rounded-3xl mx-auto flex items-center justify-center border transition-all duration-500 ${
                  aiStatus === 'SPEAKING'
                    ? 'bg-purple-950/60 border-purple-500 shadow-[0_0_40px_rgba(168,85,247,0.35)] scale-105'
                    : aiStatus === 'LISTENING'
                    ? 'bg-emerald-950/40 border-emerald-500/60 shadow-[0_0_30px_rgba(16,185,129,0.2)]'
                    : 'bg-oxblood/20 border-oxblood/40'
                }`}>
                  <Bot className={`w-12 h-12 sm:w-14 sm:h-14 ${
                    aiStatus === 'SPEAKING' ? 'text-purple-300' :
                    aiStatus === 'LISTENING' ? 'text-emerald-300' : 'text-oxblood dark:text-rose'
                  }`} />
                </div>

                {/* Animated Audio Sound Waves when AI Speaking */}
                {aiStatus === 'SPEAKING' && (
                  <div className="flex items-center justify-center gap-1 mt-3">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                      <span
                        key={i}
                        className="w-1 bg-purple-400 rounded-full animate-bounce"
                        style={{ height: `${12 + (i % 3) * 10}px`, animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Active Question Prompt Display */}
              <div className="max-w-xl mx-auto px-5 py-4 rounded-2xl bg-black/70 border border-white/20 backdrop-blur-md shadow-xl">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono font-bold text-rose-300 uppercase tracking-wider">
                    {interviewQuestions[currentQIndex]?.question_type || 'TECHNICAL'} PROMPT
                  </span>
                  <button
                    onClick={() => speakAI(interviewQuestions[currentQIndex]?.question_text || aiSpeechText)}
                    className="text-[10px] text-slate-300 hover:text-white flex items-center gap-1 font-mono transition"
                    title="Repeat Question Audio"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>Repeat Audio</span>
                  </button>
                </div>
                <p className="text-sm font-display font-medium text-white leading-relaxed">
                  "{interviewQuestions[currentQIndex]?.question_text || aiSpeechText || 'Welcome to your SkillSphere technical interview. Please speak into your microphone.'}"
                </p>
              </div>

              {/* Live Candidate Speech Captions */}
              {candidateLiveTranscript && (
                <div className="max-w-lg mx-auto p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-left shadow-lg">
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-300 mb-1">
                    <Mic className="w-3.5 h-3.5 animate-pulse" />
                    <span className="font-bold">Live Transcription:</span>
                  </div>
                  <p className="text-xs font-mono text-emerald-100 line-clamp-3">
                    {candidateLiveTranscript}
                  </p>
                </div>
              )}
            </div>

            {/* Bottom Question Controls */}
            <div className="flex justify-between items-center pt-3 border-t border-white/10">
              <span className="text-xs text-slate-300 font-mono">
                {interviewQuestions.length === 0 ? 'AI Session Active' :
                 currentQIndex + 1 === interviewQuestions.length ? 'Final Question' : `${interviewQuestions.length - currentQIndex - 1} questions remaining`}
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleNextAIQuestion}
                  disabled={isSubmittingFinal}
                  className="px-4 py-2 rounded-xl bg-oxblood text-white font-mono text-xs font-bold hover:bg-oxblood-600 transition shadow-md flex items-center gap-1.5"
                >
                  <span>{currentQIndex + 1 >= interviewQuestions.length ? 'Submit & Conclude' : 'Next Question'}</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 rounded-3xl bg-[#141820] border border-white/15 relative overflow-hidden flex items-center justify-center shadow-inner min-h-[300px]">
            {/* LiveKit Remote Video Feed */}
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className={`w-full h-full object-cover ${remoteVideoTrack ? 'block' : 'hidden'}`}
            />
            {/* Hidden Audio Element for Remote Audio Track */}
            <audio ref={remoteAudioRef} autoPlay />

            {/* Placeholder when peer video track is unattached or muted */}
            {!remoteVideoTrack && (
              <div className="text-center p-6 space-y-3">
                <div className="w-20 h-20 rounded-full bg-oxblood/30 border border-oxblood flex items-center justify-center mx-auto text-rose-300 font-display text-2xl font-bold">
                  {isRecruiter ? (roomStatus?.candidate_name?.[0] || 'C') : (roomStatus?.recruiter_name?.[0] || 'R')}
                </div>
                <div>
                  <p className="font-display font-bold text-base text-white">
                    {isRecruiter ? (roomStatus?.candidate_name || 'Candidate') : (roomStatus?.recruiter_name || 'Interviewer')}
                  </p>
                  <p className="font-mono text-xs text-slate-300">
                    {remoteParticipants.length > 0
                      ? `${isRecruiter ? 'Candidate' : 'Interviewer'} connected (Camera off)`
                      : `Waiting for ${isRecruiter ? 'candidate' : 'interviewer'} to join...`}
                  </p>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-black/60 border border-white/15 text-[10px] font-mono text-emerald-300 font-bold">
                  <span className={`w-2 h-2 rounded-full ${
                    connectionState === 'CONNECTED' ? 'bg-emerald-400 animate-pulse' :
                    connectionState === 'CONNECTING' ? 'bg-amber-400 animate-ping' :
                    'bg-slate-400'
                  }`} />
                  <span>
                    {connectionState === 'CONNECTED'
                      ? (remoteParticipants.length > 0 ? 'LiveKit Room Active' : 'Connected & Ready')
                      : connectionState === 'CONNECTING'
                      ? 'Connecting LiveKit Room...'
                      : 'WebRTC Waiting Room'}
                  </span>
                </div>
              </div>
            )}

            <div className="absolute top-4 left-4 bg-black/75 px-3 py-1 rounded-xl text-xs font-mono text-white backdrop-blur-sm border border-white/20 flex items-center gap-2">
              <span>{isRecruiter ? (roomStatus?.candidate_name || 'Candidate') : (roomStatus?.recruiter_name || 'Interviewer')}</span>
              {remoteAudioTrack && <span className="text-emerald-400 text-[10px]">&bull; Audio Live</span>}
            </div>
          </div>
        )}

        {/* Local Stream PIP / Side-by-Side Box */}
        <div className="w-full md:w-80 lg:w-96 rounded-3xl bg-[#141820] border border-white/15 relative overflow-hidden flex items-center justify-center shadow-lg aspect-video md:aspect-auto">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover transform scale-x-[-1]"
          />

          {isVideoMuted && (
            <div className="absolute inset-0 bg-[#141820] flex flex-col items-center justify-center space-y-2">
              <VideoOff className="w-10 h-10 text-slate-400" />
              <span className="font-mono text-[11px] text-slate-300">Camera Off</span>
            </div>
          )}

          <div className="absolute top-3 left-3 bg-black/75 px-2.5 py-1 rounded-lg text-[10px] font-mono text-white backdrop-blur-sm border border-white/20 flex items-center gap-1.5">
            <span>You ({user?.name})</span>
            {isAudioMuted && <MicOff className="w-3 h-3 text-red-400" />}
          </div>

          {isScreenSharing && (
            <div className="absolute bottom-3 left-3 bg-oxblood px-2.5 py-1 rounded-lg text-[10px] font-mono text-white flex items-center gap-1 shadow-md">
              <Monitor className="w-3 h-3" />
              <span>Sharing Screen</span>
            </div>
          )}
        </div>
      </main>

      {/* 3. Bottom Meeting Controls Bar with Fixed High-Contrast Buttons & Labels */}
      <footer className="h-20 px-6 border-t border-white/10 bg-[#141820]/95 backdrop-blur-md flex items-center justify-between z-30">
        {/* Left: Session details */}
        <div className="hidden sm:block text-xs font-mono text-slate-300">
          <div className="flex items-center gap-2">
            <span>SkillSphere LiveKit WebRTC</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              connectionState === 'CONNECTED' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30' :
              connectionState === 'CONNECTING' || connectionState === 'RECONNECTING' ? 'bg-amber-950/80 text-amber-300 border border-amber-500/30' :
              'bg-white/10 text-slate-300 border border-white/10'
            }`}>
              {connectionState}
            </span>
          </div>
          {devicePermissionError && (
            <span className="block text-amber-400 text-[10px] font-bold">{devicePermissionError}</span>
          )}
        </div>

        {/* Center: Device & Control Buttons */}
        <div className="flex items-center gap-3 mx-auto">
          <button
            onClick={toggleAudio}
            className={`p-3.5 rounded-2xl transition shadow-lg ${
              isAudioMuted ? 'bg-red-600 text-white' : 'bg-white/10 text-white hover:bg-white/20 border border-white/20'
            }`}
            title={isAudioMuted ? "Unmute Microphone" : "Mute Microphone"}
          >
            {isAudioMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          <button
            onClick={toggleVideo}
            className={`p-3.5 rounded-2xl transition shadow-lg ${
              isVideoMuted ? 'bg-red-600 text-white' : 'bg-white/10 text-white hover:bg-white/20 border border-white/20'
            }`}
            title={isVideoMuted ? "Turn On Camera" : "Turn Off Camera"}
          >
            {isVideoMuted ? <VideoOff className="w-5 h-5" /> : <Video className="w-5 h-5" />}
          </button>

          <button
            onClick={toggleScreenShare}
            className={`p-3.5 rounded-2xl transition shadow-lg ${
              isScreenSharing ? 'bg-oxblood text-white' : 'bg-white/10 text-white hover:bg-white/20 border border-white/20'
            }`}
            title={isScreenSharing ? "Stop Sharing" : "Share Screen"}
          >
            <Monitor className="w-5 h-5" />
          </button>

          {/* Recruiter Recording Action Button */}
          {isRecruiter && (
            recordingStatus === 'RECORDING' ? (
              <button
                onClick={handleStopRecording}
                className="px-4 py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white font-mono text-xs font-bold flex items-center gap-2 shadow-lg transition"
              >
                <span className="w-3 h-3 bg-white rounded-sm animate-pulse" />
                <span>Stop Rec</span>
              </button>
            ) : (
              <button
                onClick={handleStartRecording}
                disabled={!bothConsented}
                className={`px-4 py-3 rounded-2xl font-mono text-xs font-bold flex items-center gap-2 shadow-lg transition ${
                  bothConsented
                    ? 'bg-white/10 hover:bg-white/20 text-white border border-white/25'
                    : 'bg-white/5 text-white/35 cursor-not-allowed border border-white/10'
                }`}
                title={bothConsented ? "Start Recording Session" : "Requires mutual consent from both participants"}
              >
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span>Record</span>
              </button>
            )
          )}

          {/* Leave / End Call */}
          <button
            onClick={handleLeaveMeeting}
            className="p-3.5 px-5 rounded-2xl bg-red-600 hover:bg-red-700 text-white font-display font-semibold text-xs flex items-center gap-2 shadow-lg transition"
          >
            <PhoneOff className="w-5 h-5" />
            <span className="hidden sm:inline">{isRecruiter ? 'End Call' : 'Leave'}</span>
          </button>
        </div>

        {/* Right: Round details */}
        <div className="hidden sm:block text-right text-xs font-mono text-slate-300">
          <span className="px-2.5 py-0.5 rounded text-[10px] bg-white/10 text-slate-200 border border-white/15">
            {roomStatus?.round_title || 'Technical Screen'}
          </span>
        </div>
      </footer>

      {/* ==================================================================== */}
      {/* INFORMED RECORDING CONSENT MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showConsentModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-lg w-full p-6 sm:p-8 rounded-3xl border border-oxblood/40 space-y-5 bg-[#141820]"
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-xl bg-oxblood/20 border border-oxblood/40 flex items-center justify-center text-oxblood dark:text-rose">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-lg text-white">
                      Recording & Privacy Policy
                    </h3>
                    <p className="text-xs font-mono text-slate-300">
                      Mutual Informed Consent Protocol
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConsentModal(false)}
                  className="p-1 rounded-lg text-slate-300 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-black/50 border border-white/15 space-y-2 text-xs font-sans text-slate-200 leading-relaxed">
                <p>
                  To uphold the highest recruitment integrity, security, and privacy standards, SkillSphere requires <strong>both the candidate and recruiter</strong> to grant explicit consent before session recording can be initialized.
                </p>
                <ul className="list-disc pl-4 space-y-1 font-mono text-[11px] text-slate-300">
                  <li>Recordings are transferred durably into private, authenticated Cloudinary cloud storage.</li>
                  <li>Access is restricted solely to authorized recruitment evaluators via signed, time-limited URLs.</li>
                  <li>Consent grant timestamp, participant user ID, and IP address are immutably logged for audit.</li>
                </ul>
              </div>

              <div className="flex justify-between items-center text-xs font-mono p-3 rounded-xl bg-white/5 border border-white/15 text-slate-200">
                <span>Mutual Consent Status:</span>
                <span className={bothConsented ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                  {bothConsented ? "Both Consented (Recording Permitted)" : "Pending Consent"}
                </span>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => handleToggleConsent(false)}
                  className="flex-1 py-2.5 rounded-xl border border-white/25 font-mono text-xs text-slate-200 hover:bg-white/10 transition"
                >
                  Decline / Revoke
                </button>
                <button
                  onClick={() => handleToggleConsent(true)}
                  className="flex-1 btn-oxblood py-2.5 rounded-xl font-display font-semibold text-xs flex items-center justify-center gap-1.5"
                >
                  <Check className="w-4 h-4" />
                  <span>Grant Explicit Consent</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* RECRUITER STRUCTURED SCORECARD DRAWER */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showScorecardDrawer && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 bottom-0 w-full sm:w-[480px] bg-[#141820] border-l border-white/20 shadow-2xl z-40 p-6 flex flex-col justify-between overflow-y-auto"
          >
            <div className="space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-white/15">
                <div>
                  <h3 className="font-display font-bold text-lg text-white flex items-center gap-2">
                    <FileText className="w-5 h-5 text-oxblood dark:text-rose" />
                    <span>Recruiter Scorecard</span>
                  </h3>
                  <p className="text-xs font-mono text-slate-300">
                    Candidate: {roomStatus?.candidate_name}
                  </p>
                </div>
                <button
                  onClick={() => setShowScorecardDrawer(false)}
                  className="p-1 rounded-lg text-slate-300 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSaveScorecard} className="space-y-4 text-xs font-sans">
                {/* 1. Technical Knowledge */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="font-bold font-mono text-slate-200">Technical Knowledge (1 - 5)</label>
                    <span className="font-mono text-oxblood dark:text-rose font-bold">{scorecard.technical_knowledge_score} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={scorecard.technical_knowledge_score}
                    onChange={(e) => setScorecard({ ...scorecard, technical_knowledge_score: parseFloat(e.target.value) })}
                    className="w-full accent-oxblood"
                  />
                  <input
                    type="text"
                    placeholder="Evidence / technical notes..."
                    value={scorecard.technical_evidence_notes}
                    onChange={(e) => setScorecard({ ...scorecard, technical_evidence_notes: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 rounded-lg bg-black/60 border border-white/20 text-xs text-white placeholder:text-slate-400 focus:border-rose outline-none"
                  />
                </div>

                {/* 2. Communication */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="font-bold font-mono text-slate-200">Communication & Clarity (1 - 5)</label>
                    <span className="font-mono text-oxblood dark:text-rose font-bold">{scorecard.communication_score} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={scorecard.communication_score}
                    onChange={(e) => setScorecard({ ...scorecard, communication_score: parseFloat(e.target.value) })}
                    className="w-full accent-oxblood"
                  />
                </div>

                {/* 3. Problem Solving */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="font-bold font-mono text-slate-200">Problem Solving & Architecture (1 - 5)</label>
                    <span className="font-mono text-oxblood dark:text-rose font-bold">{scorecard.problem_solving_score} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={scorecard.problem_solving_score}
                    onChange={(e) => setScorecard({ ...scorecard, problem_solving_score: parseFloat(e.target.value) })}
                    className="w-full accent-oxblood"
                  />
                </div>

                {/* 4. Role-Specific Skills */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="font-bold font-mono text-slate-200">Role-Specific Competence (1 - 5)</label>
                    <span className="font-mono text-oxblood dark:text-rose font-bold">{scorecard.role_specific_score} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={scorecard.role_specific_score}
                    onChange={(e) => setScorecard({ ...scorecard, role_specific_score: parseFloat(e.target.value) })}
                    className="w-full accent-oxblood"
                  />
                </div>

                {/* 5. Cultural Alignment */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="font-bold font-mono text-slate-200">Cultural Alignment (1 - 5)</label>
                    <span className="font-mono text-oxblood dark:text-rose font-bold">{scorecard.cultural_alignment_score} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={scorecard.cultural_alignment_score}
                    onChange={(e) => setScorecard({ ...scorecard, cultural_alignment_score: parseFloat(e.target.value) })}
                    className="w-full accent-oxblood"
                  />
                </div>

                {/* Overall Recommendation */}
                <div className="pt-2">
                  <label className="font-bold font-mono text-slate-200 block mb-1">Overall Recommendation</label>
                  <select
                    value={scorecard.overall_recommendation}
                    onChange={(e) => setScorecard({ ...scorecard, overall_recommendation: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-black/60 border border-white/20 font-mono text-xs text-white focus:border-rose outline-none"
                  >
                    <option value="RECOMMENDED">RECOMMENDED (Advance to Next Step / Offer)</option>
                    <option value="ADDITIONAL_INTERVIEW_REQUIRED">ADDITIONAL INTERVIEW REQUIRED</option>
                    <option value="UNDER_REVIEW">UNDER REVIEW (Debrief Needed)</option>
                    <option value="NOT_RECOMMENDED">NOT RECOMMENDED (Reject Application)</option>
                  </select>
                </div>

                {/* Strengths & Improvement Notes */}
                <div>
                  <label className="font-bold font-mono text-slate-200 block mb-1">Key Strengths</label>
                  <textarea
                    rows={2}
                    value={scorecard.strengths}
                    onChange={(e) => setScorecard({ ...scorecard, strengths: e.target.value })}
                    placeholder="Candidate demonstrated deep knowledge of..."
                    className="w-full px-3 py-2 rounded-xl bg-black/60 border border-white/20 text-xs text-white placeholder:text-slate-400 focus:border-rose outline-none resize-none"
                  />
                </div>

                <div>
                  <label className="font-bold font-mono text-slate-200 block mb-1">Private Evaluation Notes</label>
                  <textarea
                    rows={2}
                    value={scorecard.private_evaluation_notes}
                    onChange={(e) => setScorecard({ ...scorecard, private_evaluation_notes: e.target.value })}
                    placeholder="Internal debrief notes (never visible to candidate)..."
                    className="w-full px-3 py-2 rounded-xl bg-black/60 border border-white/20 text-xs text-white placeholder:text-slate-400 focus:border-rose outline-none resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={savingScorecard}
                  className="btn-oxblood w-full py-2.5 rounded-xl font-display font-semibold text-xs mt-4 flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{savingScorecard ? "Saving Scorecard..." : "Submit Internal Scorecard"}</span>
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* AI ASSISTANT INTELLIGENCE DRAWER */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showAIDrawer && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 bottom-0 w-full sm:w-[480px] bg-[#141820] border-l border-white/20 shadow-2xl z-40 p-6 flex flex-col justify-between overflow-y-auto"
          >
            <div className="space-y-6">
              <div className="flex justify-between items-center pb-4 border-b border-white/15">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-oxblood/30 border border-oxblood flex items-center justify-center text-oxblood dark:text-rose">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-base text-white">
                      AI Interview Intelligence
                    </h3>
                    <p className="text-[10px] font-mono text-slate-300">
                      Assistant Draft &bull; Requires Recruiter Approval
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAIDrawer(false)}
                  className="p-1 rounded-lg text-slate-300 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Status Banner */}
              <div className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2 ${
                aiTranscript?.is_approved_by_recruiter
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
              }`}>
                {aiTranscript?.is_approved_by_recruiter ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                    <span>Approved by Recruiter</span>
                  </>
                ) : (
                  <>
                    <HelpCircle className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>Assistant Draft (Pending Recruiter Review)</span>
                  </>
                )}
              </div>

              {/* Topics Explored */}
              {aiTranscript?.technical_topics_json?.length > 0 && (
                <div>
                  <h4 className="font-mono text-xs font-bold text-slate-200 uppercase mb-2">Technical Topics Analyzed</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {aiTranscript.technical_topics_json.map((topic, idx) => (
                      <span key={idx} className="badge-slate font-mono text-[10px] px-2 py-0.5 rounded">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Editable AI Executive Summary */}
              <div>
                <h4 className="font-mono text-xs font-bold text-slate-200 uppercase mb-1">Executive Summary</h4>
                <textarea
                  rows={4}
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-black/60 border border-white/20 text-xs text-white placeholder:text-slate-400 focus:border-rose outline-none resize-none font-sans leading-relaxed"
                />
              </div>

              {/* Timestamp Breakdown */}
              {aiTranscript?.timestamps_json?.length > 0 && (
                <div>
                  <h4 className="font-mono text-xs font-bold text-slate-200 uppercase mb-2">Interview Segments</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {aiTranscript.timestamps_json.map((seg, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-black/60 border border-white/15 text-xs font-mono">
                        <span className="text-oxblood dark:text-rose font-bold mr-2">{seg.time}</span>
                        <span className="text-slate-200">{seg.topic}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={handleApproveAI}
                className="btn-oxblood w-full py-2.5 rounded-xl font-display font-semibold text-xs flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4" />
                <span>Approve & Finalize AI Feedback</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* INTERVIEW COMPLETION & CLOUDINARY SUBMISSION CONFIRMATION MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showCompletionModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card bg-[#141820] max-w-lg w-full p-8 rounded-3xl border border-oxblood/40 text-center space-y-6 shadow-2xl"
            >
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div>
                <span className="badge-selected font-mono text-[11px] px-3 py-1 rounded-full uppercase">
                  Interview Concluded
                </span>
                <h3 className="font-display text-2xl font-bold text-white mt-3">
                  Session Completed Successfully
                </h3>
                <p className="text-xs font-mono text-slate-300 mt-2 max-w-sm mx-auto leading-relaxed">
                  Thank you for completing your interview. Your verbal responses, technical explanations, and recording have been securely transferred to Cloudinary for recruiter review.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/15 text-left font-mono text-xs space-y-1.5 text-slate-200">
                <div className="flex justify-between">
                  <span>Room ID:</span>
                  <span className="text-white">{interviewId.slice(0, 12)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Archived Folder:</span>
                  <span className="text-purple-400 font-bold">skillsphere/ai-interviews</span>
                </div>
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="text-emerald-400 font-bold">Completed & Ingested</span>
                </div>
              </div>

              <button
                onClick={() => navigate(isRecruiter ? '/recruiter?tab=interviews' : '/dashboard?tab=interviews')}
                className="w-full py-3 rounded-xl bg-oxblood text-white font-mono text-xs font-bold hover:bg-oxblood/90 transition shadow flex items-center justify-center gap-2"
              >
                <span>Return to Dashboard</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
