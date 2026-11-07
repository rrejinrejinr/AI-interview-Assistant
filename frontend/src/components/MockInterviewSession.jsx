import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Send,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  Camera,
  CheckCircle2,
  Lock,
  Maximize2,
  XCircle,
  LogOut,
  Sparkles
} from 'lucide-react';
import { submitMockAnswerApi, rejectMockInterviewApi, completeMockInterviewApi, exitMockInterviewApi } from '../services/api';

const NO_FACE_WARNING_THRESHOLD_SEC = 5;
const NO_FACE_TERMINATION_THRESHOLD_SEC = 15;
const MULTIPLE_FACE_TERMINATION_THRESHOLD_SEC = 8;
const PHONE_WARNING_THRESHOLD_SEC = 3;
const PHONE_TERMINATION_THRESHOLD_SEC = 10;

const loadCocoSsdScript = () => {
  return new Promise((resolve) => {
    if (window.cocoSsd) return resolve(window.cocoSsd);
    if (!window.tf) {
      const tfScript = document.createElement('script');
      tfScript.src = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.10.0/dist/tf.min.js';
      tfScript.crossOrigin = 'anonymous';
      tfScript.onload = () => {
        const cocoScript = document.createElement('script');
        cocoScript.src = 'https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.3/dist/coco-ssd.min.js';
        cocoScript.crossOrigin = 'anonymous';
        cocoScript.onload = () => resolve(window.cocoSsd);
        cocoScript.onerror = () => resolve(null);
        document.head.appendChild(cocoScript);
      };
      tfScript.onerror = () => resolve(null);
      document.head.appendChild(tfScript);
    } else {
      const cocoScript = document.createElement('script');
      cocoScript.src = 'https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.3/dist/coco-ssd.min.js';
      cocoScript.crossOrigin = 'anonymous';
      cocoScript.onload = () => resolve(window.cocoSsd);
      cocoScript.onerror = () => resolve(null);
      document.head.appendChild(cocoScript);
    }
  });
};

const loadMediaPipeScript = () => {
  return new Promise((resolve) => {
    if (window.FaceDetection) return resolve(window.FaceDetection);
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/face_detection.js';
    script.crossOrigin = 'anonymous';
    script.onload = () => resolve(window.FaceDetection);
    script.onerror = () => resolve(null);
    document.head.appendChild(script);
  });
};

const getFrameBrightness = (video) => {
  try {
    if (!video || video.readyState < 2 || video.videoWidth === 0) return 0;
    const canvas = document.createElement('canvas');
    canvas.width = 32;
    canvas.height = 24;
    const ctx = canvas.getContext('2d');
    if (!ctx) return 128;
    ctx.drawImage(video, 0, 0, 32, 24);
    const imgData = ctx.getImageData(0, 0, 32, 24).data;
    let totalLuma = 0;
    for (let i = 0; i < imgData.length; i += 4) {
      totalLuma += (0.299 * imgData[i] + 0.587 * imgData[i + 1] + 0.114 * imgData[i + 2]);
    }
    return totalLuma / (imgData.length / 4);
  } catch (e) {
    return 128;
  }
};

export default function MockInterviewSession({
  session,
  onInterviewComplete,
  onInterviewRejected,
  onExitSession
}) {
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentEval, setCurrentEval] = useState(null);
  const [answeredMap, setAnsweredMap] = useState({});

  // Exit Modal State
  const [showExitModal, setShowExitModal] = useState(false);
  const [exiting, setExiting] = useState(false);

  // Integrity Monitoring State (Face & Phone Detection)
  const [faceCount, setFaceCount] = useState(0);
  const [cameraError, setCameraError] = useState(null);
  const [cameraBlocked, setCameraBlocked] = useState(false);
  const [noFaceDuration, setNoFaceDuration] = useState(0);
  const [multiFaceDuration, setMultiFaceDuration] = useState(0);
  const [phoneDetected, setPhoneDetected] = useState(false);
  const [phoneDuration, setPhoneDuration] = useState(0);
  const [integrityWarning, setIntegrityWarning] = useState(null);
  const [rejectedInfo, setRejectedInfo] = useState(null);

  // Refs
  const videoRef = useRef(null);
  const streamRef = useRef(session.mediaStream || null);
  const recognitionRef = useRef(null);
  const detectorRef = useRef(null);
  const cocoModelRef = useRef(null);
  const monitorIntervalRef = useRef(null);

  const questions = session.questions || [];
  const currentQuestion = questions[currentQIndex] || null;
  const isLastQuestion = currentQIndex === questions.length - 1;

  // Initialize MediaStream, Face Detection & Phone Object Detection
  useEffect(() => {
    let isMounted = true;

    async function setupLiveMonitoring() {
      try {
        if (!streamRef.current) {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({
              video: { width: { ideal: 480 }, height: { ideal: 360 }, facingMode: 'user' },
              audio: true
            });
            if (!isMounted) {
              stream.getTracks().forEach((t) => t.stop());
              return;
            }
            streamRef.current = stream;
          } catch (camErr) {
            if (!isMounted) return;
            const errMsg = camErr.name === 'NotAllowedError'
              ? 'Camera permission denied. Please allow camera access in your browser to continue.'
              : 'Camera hardware is unavailable or blocked.';
            setCameraError(errMsg);
            setFaceCount(0);
            return;
          }
        }

        if (videoRef.current && streamRef.current) {
          videoRef.current.srcObject = streamRef.current;
          await videoRef.current.play().catch(() => {});
        }

        // Initialize MediaPipe Face Detection
        const FaceDetectorClass = await loadMediaPipeScript();
        if (FaceDetectorClass && isMounted) {
          const faceDetection = new FaceDetectorClass({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`
          });
          faceDetection.setOptions({ model: 'short', minDetectionConfidence: 0.5 });
          faceDetection.onResults((results) => {
            if (!isMounted) return;
            const count = results.detections ? results.detections.length : 0;
            setFaceCount(count);
          });
          detectorRef.current = faceDetection;
        }

        // Initialize COCO-SSD Phone Detection
        loadCocoSsdScript().then(async (coco) => {
          if (coco && isMounted) {
            try {
              const model = await coco.load();
              if (isMounted) cocoModelRef.current = model;
            } catch (e) {
              console.warn('COCO-SSD load warning:', e);
            }
          }
        });

        // Monitoring Heartbeat loop (every 500ms)
        monitorIntervalRef.current = setInterval(async () => {
          if (!isMounted || rejectedInfo) return;

          if (videoRef.current && videoRef.current.readyState >= 2) {
            // Check frame brightness (detect covered or black camera)
            const brightness = getFrameBrightness(videoRef.current);
            if (brightness < 12) {
              if (isMounted) {
                setCameraBlocked(true);
                setFaceCount(0);
              }
              return;
            } else {
              if (isMounted && cameraBlocked) setCameraBlocked(false);
            }

            // Send to MediaPipe
            if (detectorRef.current) {
              try {
                await detectorRef.current.send({ image: videoRef.current });
              } catch (e) {
                if (isMounted) setFaceCount(0);
              }
            }
            // Send to COCO-SSD for phone detection (uniform threshold 0.50)
            if (cocoModelRef.current) {
              try {
                const predictions = await cocoModelRef.current.detect(videoRef.current);
                const hasPhone = predictions && predictions.some(p => p.class === 'cell phone' && p.score >= 0.50);
                if (isMounted) setPhoneDetected(hasPhone);
              } catch (e) {}
            }
          } else {
            if (isMounted) setFaceCount(0);
          }
        }, 500);
      } catch (err) {
        console.error('Live Camera Monitoring Error:', err);
        setCameraError('Camera stream stopped or camera hardware became unavailable.');
        setFaceCount(0);
      }
    }

    setupLiveMonitoring();

    return () => {
      isMounted = false;
      if (monitorIntervalRef.current) clearInterval(monitorIntervalRef.current);
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (e) {}
        detectorRef.current = null;
      }
      if (streamRef.current) {
        try {
          streamRef.current.getTracks().forEach((t) => t.stop());
        } catch (e) {}
        streamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [rejectedInfo]);

  // Face & Phone Presence Threshold Evaluation (Runs every 1s)
  useEffect(() => {
    if (rejectedInfo) return;

    const timer = setInterval(() => {
      // 1. Check Phone Detection Condition
      if (phoneDetected) {
        setPhoneDuration((prev) => {
          const next = prev + 1;
          if (next >= PHONE_TERMINATION_THRESHOLD_SEC) {
            handleTriggerRejection('Unauthorized mobile phone or handheld electronic device detected during mock interview.');
          } else if (next >= PHONE_WARNING_THRESHOLD_SEC) {
            setIntegrityWarning(`Interview Integrity Warning: Mobile phone detected in camera frame. Remove it immediately (${PHONE_TERMINATION_THRESHOLD_SEC - next}s remaining before rejection).`);
          }
          return next;
        });
      } else {
        setPhoneDuration(0);
      }

      // 2. Check No Face Condition
      if (faceCount === 0) {
        setNoFaceDuration((prev) => {
          const next = prev + 1;
          if (next >= NO_FACE_TERMINATION_THRESHOLD_SEC) {
            handleTriggerRejection('Face was not continuously present in the camera frame for more than 15 seconds.');
          } else if (next >= NO_FACE_WARNING_THRESHOLD_SEC) {
            setIntegrityWarning(`Interview Integrity Warning: No candidate detected. Return to frame within ${NO_FACE_TERMINATION_THRESHOLD_SEC - next} seconds.`);
          }
          return next;
        });
      } else {
        setNoFaceDuration(0);
      }

      // 3. Check Multiple Faces Condition
      if (faceCount > 1) {
        setMultiFaceDuration((prev) => {
          const next = prev + 1;
          if (next >= MULTIPLE_FACE_TERMINATION_THRESHOLD_SEC) {
            handleTriggerRejection('Multiple faces were detected in the camera frame for a sustained period.');
          } else {
            setIntegrityWarning(`Interview Integrity Warning: Multiple faces detected (${faceCount}). Ensure you are alone in the frame.`);
          }
          return next;
        });
      } else {
        setMultiFaceDuration(0);
      }

      // Clear warning if all conditions are normal
      if (faceCount === 1 && !phoneDetected) {
        setIntegrityWarning(null);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [faceCount, phoneDetected, rejectedInfo]);

  const baseTextRef = useRef('');

  // Web Speech API initialization
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = 0; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      const base = baseTextRef.current ? baseTextRef.current.trim() + ' ' : '';
      const full = (base + finalTranscript + interimTranscript).trim();
      setUserAnswer(full);
    };

    recognition.onerror = (e) => {
      console.warn('Speech Recognition Error:', e.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (e) {}
    };
  }, []);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Voice input is not supported in this browser. Please type your answer.');
      return;
    }

    if (isRecording) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      setIsRecording(false);
      baseTextRef.current = userAnswer.trim();
    } else {
      try {
        baseTextRef.current = userAnswer.trim();
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
    }
  };

  // Malpractice / Integrity Rejection Handler
  const handleTriggerRejection = async (reason) => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }

    if (document.fullscreenElement && document.exitFullscreen) {
      try {
        await document.exitFullscreen();
      } catch (e) {}
    }

    try {
      const res = await rejectMockInterviewApi(session.session_id, reason);
      const rejData = {
        session_id: session.session_id,
        reason: reason,
        questions_completed: Object.keys(answeredMap).length,
        total_questions: questions.length,
        timestamp: new Date().toISOString(),
        email_dispatched: res.email_dispatched
      };
      setRejectedInfo(rejData);
      if (onInterviewRejected) {
        onInterviewRejected(rejData);
      }
    } catch (err) {
      console.error('Rejection API error:', err);
      setRejectedInfo({
        session_id: session.session_id,
        reason: reason,
        questions_completed: Object.keys(answeredMap).length,
        total_questions: questions.length,
        timestamp: new Date().toISOString()
      });
    }
  };

  // Candidate Manual Exit Handler (NOT MALPRACTICE, NO EMAIL)
  const handleConfirmExit = async () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }

    if (document.fullscreenElement && document.exitFullscreen) {
      try {
        await document.exitFullscreen();
      } catch (e) {}
    }

    setExiting(true);
    try {
      await exitMockInterviewApi(session.session_id);
    } catch (err) {
      console.error('Exit Mock Interview API error:', err);
    } finally {
      setExiting(false);
      setShowExitModal(false);
      if (onExitSession) {
        onExitSession();
      }
    }
  };

  const handleSaveCurrentAnswer = async (ansText) => {
    const textToSave = ansText !== undefined ? ansText : userAnswer;
    if (!textToSave.trim() || !currentQuestion) return;

    setAnsweredMap((prev) => ({
      ...prev,
      [currentQuestion.id]: textToSave.trim()
    }));

    try {
      await submitMockAnswerApi(
        session.session_id,
        currentQuestion.id,
        textToSave.trim()
      );
    } catch (err) {
      console.error('Save Answer Error:', err);
    }
  };

  const handleNextQuestion = async () => {
    if (submitting) return;

    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      setIsRecording(false);
    }

    if (isLastQuestion) {
      await handleCompleteInterview();
      return;
    }

    setSubmitting(true);
    try {
      if (userAnswer.trim()) {
        await handleSaveCurrentAnswer(userAnswer);
      }

      const nextIdx = currentQIndex + 1;
      setCurrentQIndex(nextIdx);
      const nextQ = questions[nextIdx];
      const savedAns = answeredMap[nextQ?.id] || '';
      setUserAnswer(savedAns);
      baseTextRef.current = savedAns;
    } finally {
      setSubmitting(false);
    }
  };

  const handlePrevQuestion = async () => {
    if (submitting || currentQIndex === 0) return;

    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      setIsRecording(false);
    }

    setSubmitting(true);
    try {
      if (userAnswer.trim()) {
        await handleSaveCurrentAnswer(userAnswer);
      }

      const prevIdx = currentQIndex - 1;
      setCurrentQIndex(prevIdx);
      const prevQ = questions[prevIdx];
      const savedAns = answeredMap[prevQ?.id] || '';
      setUserAnswer(savedAns);
      baseTextRef.current = savedAns;
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteInterview = async () => {
    setSubmitting(true);
    try {
      if (userAnswer.trim()) {
        await handleSaveCurrentAnswer(userAnswer);
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (document.fullscreenElement && document.exitFullscreen) {
        try {
          await document.exitFullscreen();
        } catch (e) {}
      }

      const report = await completeMockInterviewApi(session.session_id);
      if (onInterviewComplete) {
        onInterviewComplete(report);
      }
    } catch (err) {
      console.error('Complete Mock Interview Error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Rejection View
  if (rejectedInfo) {
    return (
      <div className="ai-card" style={{ maxWidth: '650px', margin: '40px auto', border: '2px solid #ef4444' }}>
        <div style={{ textAlign: 'center', padding: '20px 10px' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px'
          }}>
            <XCircle size={32} color="#ef4444" />
          </div>

          <h2 style={{ fontSize: '19px', fontWeight: '800', color: '#ef4444', marginBottom: '8px' }}>
            Mock Interview Terminated
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', maxWidth: '480px', margin: '0 auto 20px' }}>
            Your mock interview session has been terminated because the interview integrity requirements were not satisfied.
          </p>

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            borderRadius: '10px',
            padding: '16px',
            textAlign: 'left',
            marginBottom: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)' }}>REASON FOR TERMINATION:</div>
            <div style={{ fontSize: '13.5px', fontWeight: '800', color: 'var(--text-primary)' }}>{rejectedInfo.reason}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Questions Completed: {rejectedInfo.questions_completed} / {rejectedInfo.total_questions}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Session ID: #{rejectedInfo.session_id}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--primary)', marginTop: '4px' }}>
              A formal integrity event notification has been dispatched to your registered email address.
            </div>
          </div>

          <button
            type="button"
            onClick={onExitSession}
            className="btn-primary"
            style={{ width: '100%', padding: '12px' }}
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const answeredCount = Object.keys(answeredMap).length;
  const progressPercent = Math.round((answeredCount / questions.length) * 100);
  const formattedIndexStr = String(currentQIndex + 1).padStart(2, '0');
  const formattedTotalStr = String(questions.length).padStart(2, '0');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Integrity Warning Floating Alert */}
      {integrityWarning && (
        <div style={{
          background: '#fef2f2',
          border: '1.5px solid #ef4444',
          color: '#991b1b',
          borderRadius: '10px',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontWeight: '700',
          fontSize: '13px',
          boxShadow: '0 4px 12px rgba(239, 68, 68, 0.15)'
        }}>
          <AlertTriangle size={20} color="#dc2626" style={{ flexShrink: 0 }} />
          <span>{integrityWarning}</span>
        </div>
      )}

      {/* Top Header Card */}
      <div className="ai-card" style={{ padding: '14px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-primary" style={{ fontWeight: '800' }}>
                Question {formattedIndexStr} / {formattedTotalStr}
              </span>
              <span className="badge badge-neutral">
                Difficulty: {session.difficulty || 'Medium'}
              </span>
              <span className="badge badge-neutral">
                Category: {currentQuestion?.category || 'Technical'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px' }}>
              <div style={{ width: '220px', height: '6px', background: 'var(--border-light)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${progressPercent}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.3s' }} />
              </div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)' }}>
                {answeredCount} / {questions.length} Answered ({progressPercent}%)
              </span>
            </div>
          </div>

          {/* Exit Interview Button */}
          <button
            type="button"
            onClick={() => setShowExitModal(true)}
            className="btn-secondary"
            style={{
              padding: '8px 14px',
              fontSize: '12.5px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--danger)',
              borderColor: 'var(--border-light)'
            }}
          >
            <LogOut size={14} />
            <span>Exit Interview</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Question & Answer (Left) + Camera & Proctoring (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: '16px', alignItems: 'start' }}>
        {/* Left Area: Question & Answer Card */}
        <div className="ai-card">
          {/* Question Text */}
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            borderRadius: '12px',
            padding: '18px 20px',
            marginBottom: '18px'
          }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Question #{currentQIndex + 1}
            </span>
            <h3 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px', lineHeight: '1.45' }}>
              {currentQuestion?.question_text || currentQuestion?.question}
            </h3>
          </div>

          {/* Answer Input Area */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label" style={{ margin: 0 }}>Your Answer</label>
              <button
                type="button"
                onClick={toggleRecording}
                className={isRecording ? 'btn-danger' : 'btn-secondary'}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  borderRadius: '8px'
                }}
              >
                {isRecording ? <MicOff size={14} /> : <Mic size={14} />}
                <span>{isRecording ? 'Stop Speaking' : 'Start Speaking'}</span>
              </button>
            </div>

            <textarea
              rows={6}
              placeholder="Type your technical response here, or click 'Start Speaking' to dictate using your microphone..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              disabled={submitting}
              className="form-textarea"
              style={{ fontSize: '13.5px', lineHeight: '1.5' }}
            />

            {/* Action Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginTop: '6px' }}>
              <button
                type="button"
                onClick={handlePrevQuestion}
                disabled={currentQIndex === 0 || submitting}
                className="btn-secondary"
                style={{ padding: '10px 18px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <span>Previous</span>
              </button>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={handleNextQuestion}
                  disabled={submitting}
                  className="btn-primary"
                  style={{
                    background: isLastQuestion ? 'var(--success)' : 'var(--primary)',
                    borderColor: isLastQuestion ? 'var(--success)' : 'var(--primary)',
                    padding: '10px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontWeight: '800'
                  }}
                >
                  <span>
                    {submitting
                      ? (isLastQuestion ? 'Submitting & Evaluating 30 Questions...' : 'Saving Answer...')
                      : isLastQuestion
                      ? `Submit & Complete Mock Interview (${questions.length}/${questions.length})`
                      : 'Next Question'}
                  </span>
                  {!submitting && <ArrowRight size={15} />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Area: Camera Feed & Proctoring Status Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="ai-card" style={{ padding: '14px' }}>
            <div style={{
              fontSize: '11.5px',
              fontWeight: '800',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <Camera size={13} className="text-primary" />
              <span>Camera Monitor</span>
            </div>

            <div style={{
              position: 'relative',
              width: '100%',
              aspectRatio: '4/3',
              borderRadius: '8px',
              overflow: 'hidden',
              background: '#0f172a',
              border: (faceCount === 1 && !phoneDetected && !cameraBlocked && !cameraError) ? '2px solid var(--success)' : '2px solid #ef4444'
            }}>
              <video
                ref={videoRef}
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
              />
              {(cameraError || cameraBlocked) && (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'rgba(15, 23, 42, 0.88)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '16px',
                  textAlign: 'center',
                  color: 'white',
                  gap: '8px'
                }}>
                  <AlertCircle size={28} color="#ef4444" />
                  <span style={{ fontSize: '12px', fontWeight: '700' }}>
                    {cameraError || 'Camera is blocked or covered'}
                  </span>
                </div>
              )}
            </div>

            <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Face Status:</span>
                <span style={{
                  fontWeight: '800',
                  color: (faceCount === 1 && !cameraBlocked && !cameraError) ? 'var(--success)' : '#ef4444'
                }}>
                  {cameraError
                    ? 'Unavailable'
                    : cameraBlocked
                    ? 'Camera Covered'
                    : faceCount === 1
                    ? 'Candidate in frame'
                    : faceCount > 1
                    ? 'Multiple Faces'
                    : 'Face not detected'}
                </span>
              </div>

              {/* Helpful Instruction Banner */}
              {faceCount === 0 && !cameraError && !cameraBlocked && (
                <div style={{
                  marginTop: '4px',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  color: '#ef4444',
                  fontSize: '11px',
                  lineHeight: '1.4'
                }}>
                  Please position your face clearly inside the camera frame.
                </div>
              )}

              {faceCount === 1 && !cameraError && !cameraBlocked && (
                <div style={{
                  marginTop: '4px',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  background: 'rgba(34, 197, 94, 0.1)',
                  border: '1px solid rgba(34, 197, 94, 0.25)',
                  color: 'var(--success)',
                  fontSize: '11px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <CheckCircle2 size={12} />
                  <span>Face detected</span>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Device Status:</span>
                <span style={{ fontWeight: '800', color: !phoneDetected ? 'var(--success)' : '#ef4444' }}>
                  {!phoneDetected ? 'Clean' : 'Phone Detected!'}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Interview Status:</span>
                <span style={{ fontWeight: '800', color: 'var(--primary)' }}>In Progress</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* EXIT CONFIRMATION MODAL */}
      {showExitModal && (
        <div
          className="ai-modal-backdrop"
          onClick={() => setShowExitModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(15, 23, 42, 0.72)',
            backdropFilter: 'blur(5px)',
            WebkitBackdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
            padding: '16px',
            boxSizing: 'border-box'
          }}
        >
          <div
            className="ai-modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--bg-surface, #ffffff)',
              color: 'var(--text-primary)',
              borderRadius: '16px',
              border: '1px solid var(--border-light)',
              padding: '30px 24px',
              width: '100%',
              maxWidth: '460px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
              margin: 'auto',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: '52px',
                height: '52px',
                borderRadius: '50%',
                background: 'var(--primary-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '14px'
              }}>
                <LogOut size={26} className="text-primary" />
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '8px', color: 'var(--text-primary)' }}>
                Exit Mock Interview?
              </h3>

              <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: '0 0 24px', maxWidth: '380px' }}>
                You have not completed this interview. Your current progress will be saved.
              </p>

              <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={() => setShowExitModal(false)}
                  className="btn-secondary"
                  style={{ flex: 1, padding: '11px', fontWeight: '700', fontSize: '13.5px' }}
                >
                  Continue Interview
                </button>
                <button
                  type="button"
                  onClick={handleConfirmExit}
                  disabled={exiting}
                  className="btn-danger"
                  style={{ flex: 1, padding: '11px', fontWeight: '700', fontSize: '13.5px' }}
                >
                  {exiting ? 'Exiting...' : 'Exit Interview'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
