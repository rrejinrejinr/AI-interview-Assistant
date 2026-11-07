import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ArrowLeft,
  Play,
  RefreshCw,
  AlertTriangle,
  Maximize2,
  UserCheck
} from 'lucide-react';
import { verifyMockInterviewPhotoApi } from '../services/api';

export default function MockInterviewVerification({ session, onBeginInterview, onCancel }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);

  const [cameraStatus, setCameraStatus] = useState('requesting'); // requesting | active | denied | error
  const [faceCount, setFaceCount] = useState(0);
  const [isFaceValid, setIsFaceValid] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [modelLoading, setModelLoading] = useState(true);
  const [startingInterview, setStartingInterview] = useState(false);

  const loadMediaPipeScript = () => {
    return new Promise((resolve, reject) => {
      if (window.FaceDetection) {
        return resolve();
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/face_detection.js';
      script.crossOrigin = 'anonymous';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Face Detection script.'));
      document.head.appendChild(script);
    });
  };

  useEffect(() => {
    let isMounted = true;

    async function initCameraAndDetector() {
      try {
        setCameraStatus('requesting');
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
          audio: true
        });

        if (!isMounted) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
        setCameraStatus('active');

        await loadMediaPipeScript();

        if (!isMounted) return;

        if (window.FaceDetection) {
          const faceDetection = new window.FaceDetection({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`
          });

          faceDetection.setOptions({
            model: 'short',
            minDetectionConfidence: 0.5
          });

          faceDetection.onResults((results) => {
            if (!isMounted) return;
            const count = results.detections ? results.detections.length : 0;
            setFaceCount(count);
            setIsFaceValid(count === 1);
          });

          detectorRef.current = faceDetection;
          setModelLoading(false);

          timerRef.current = setInterval(async () => {
            if (videoRef.current && videoRef.current.readyState >= 2 && detectorRef.current) {
              try {
                await detectorRef.current.send({ image: videoRef.current });
              } catch (e) {}
            }
          }, 350);
        } else {
          setModelLoading(false);
          setIsFaceValid(true);
          setFaceCount(1);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Camera Init Error:', err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setCameraStatus('denied');
          setErrorMessage('Camera or microphone permission was denied. Please allow camera and microphone access in your browser settings to proceed.');
        } else {
          setCameraStatus('error');
          setErrorMessage(`Unable to access camera: ${err.message}`);
        }
        setModelLoading(false);
      }
    }

    initCameraAndDetector();

    return () => {
      isMounted = false;
      if (timerRef.current) clearInterval(timerRef.current);
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (e) {}
      }
    };
  }, []);

  const handleCapturePhoto = () => {
    if (!videoRef.current || !isFaceValid) return;

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current || document.createElement('canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      setCapturedPhoto(dataUrl);
    } catch (e) {
      console.error('Error capturing photo:', e);
    }
  };

  const handleStartFullscreen = async () => {
    setStartingInterview(true);
    try {
      // 1. Mark verification complete on backend
      await verifyMockInterviewPhotoApi(session.session_id);

      // 2. Request Fullscreen
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen().catch((err) => {
          console.warn('Fullscreen request bypassed or denied:', err);
        });
      }

      // 3. Callback to begin interview
      if (onBeginInterview) {
        onBeginInterview({
          ...session,
          verification_completed: true,
          photo_verified: true,
          verificationPhoto: capturedPhoto,
          mediaStream: streamRef.current
        });
      }
    } catch (err) {
      console.error('Failed to start mock interview session:', err);
      setErrorMessage('Failed to start interview. Please try again.');
    } finally {
      setStartingInterview(false);
    }
  };

  const handleCancelVerification = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <div className="ai-card" style={{ maxWidth: '850px', margin: '0 auto' }}>
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <ShieldCheck size={20} className="text-primary" />
            <span>Pre-Interview Camera & Candidate Verification</span>
          </h3>
          <p className="card-subtitle">
            Verify your camera presence and capture a pre-interview photograph before launching fullscreen mode.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginTop: '10px' }}>
        {/* Left Column: Video Feed & Detection Overlay */}
        <div>
          <div style={{
            position: 'relative',
            width: '100%',
            aspectRatio: '4/3',
            background: '#0f172a',
            borderRadius: '12px',
            overflow: 'hidden',
            border: isFaceValid ? '2.5px solid var(--success)' : '2px solid var(--border-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <video
              ref={videoRef}
              playsInline
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: 'scaleX(-1)',
                display: cameraStatus === 'active' ? 'block' : 'none'
              }}
            />

            {/* Hidden canvas for snapshot capture */}
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {/* Camera Status Overlays */}
            {cameraStatus === 'requesting' && (
              <div style={{ textAlign: 'center', color: '#94a3b8', padding: '20px' }}>
                <RefreshCw size={36} className="spin" style={{ marginBottom: '12px', margin: '0 auto' }} />
                <div style={{ fontWeight: '700' }}>Requesting Camera Access...</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>Please allow camera and microphone access when prompted by your browser.</div>
              </div>
            )}

            {cameraStatus === 'denied' && (
              <div style={{ textAlign: 'center', color: '#f87171', padding: '20px' }}>
                <AlertCircle size={40} style={{ marginBottom: '12px', margin: '0 auto' }} />
                <div style={{ fontWeight: '800' }}>Camera Permission Blocked</div>
                <div style={{ fontSize: '12px', marginTop: '6px', color: '#cbd5e1' }}>
                  Enable camera access in your browser site permissions to continue.
                </div>
              </div>
            )}

            {/* Live Presence Overlay Badge */}
            {cameraStatus === 'active' && (
              <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(4px)',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '700',
                color: isFaceValid ? '#4ade80' : '#f87171',
                border: `1px solid ${isFaceValid ? '#22c55e' : '#ef4444'}`
              }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: isFaceValid ? '#22c55e' : '#ef4444',
                  display: 'inline-block'
                }} />
                <span>
                  {modelLoading
                    ? 'Loading Detector...'
                    : isFaceValid
                    ? '1 Candidate Present'
                    : faceCount === 0
                    ? 'No Face Detected'
                    : `${faceCount} Faces Detected (Single Face Required)`}
                </span>
              </div>
            )}
          </div>

          {/* Photo Capture Controls */}
          <div style={{ marginTop: '12px' }}>
            <button
              type="button"
              onClick={handleCapturePhoto}
              disabled={!isFaceValid || cameraStatus !== 'active'}
              className="btn-secondary"
              style={{
                width: '100%',
                padding: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                border: capturedPhoto ? '1.5px solid var(--success)' : '1.5px solid var(--border-light)'
              }}
            >
              <Camera size={16} />
              <span>{capturedPhoto ? 'Retake Verification Photograph' : 'Capture Verification Photograph'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Verification Status & Instructions */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '800', marginBottom: '10px' }}>
              Verification Checklist
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: '8px',
                background: cameraStatus === 'active' ? 'var(--bg-surface-secondary)' : 'var(--bg-surface)',
                border: '1px solid var(--border-light)'
              }}>
                {cameraStatus === 'active' ? (
                  <CheckCircle2 size={18} color="var(--success)" />
                ) : (
                  <AlertCircle size={18} color="var(--text-muted)" />
                )}
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Camera & Microphone Connected</span>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: '8px',
                background: isFaceValid ? 'var(--bg-surface-secondary)' : 'var(--bg-surface)',
                border: '1px solid var(--border-light)'
              }}>
                {isFaceValid ? (
                  <CheckCircle2 size={18} color="var(--success)" />
                ) : (
                  <AlertCircle size={18} color="var(--text-muted)" />
                )}
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Single Candidate In Frame</span>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: '8px',
                background: capturedPhoto ? 'var(--bg-surface-secondary)' : 'var(--bg-surface)',
                border: '1px solid var(--border-light)'
              }}>
                {capturedPhoto ? (
                  <CheckCircle2 size={18} color="var(--success)" />
                ) : (
                  <AlertCircle size={18} color="var(--text-muted)" />
                )}
                <span style={{ fontSize: '13px', fontWeight: '600' }}>Pre-Interview Photograph Captured</span>
              </div>
            </div>

            {/* Captured Photo Preview Thumbnail */}
            {capturedPhoto && (
              <div style={{
                marginTop: '16px',
                padding: '12px',
                borderRadius: '10px',
                background: 'var(--bg-surface-secondary)',
                border: '1.5px solid var(--success)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <img
                  src={capturedPhoto}
                  alt="Captured Verification"
                  style={{ width: '64px', height: '48px', objectFit: 'cover', borderRadius: '6px', transform: 'scaleX(-1)' }}
                />
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '800', color: 'var(--success)' }}>
                    Photograph Verified
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Captured for session #{session.session_id} event records
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Start Actions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              type="button"
              onClick={handleStartFullscreen}
              disabled={!capturedPhoto || !isFaceValid || startingInterview}
              className="btn-primary"
              style={{
                width: '100%',
                padding: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                fontSize: '14px',
                fontWeight: '800'
              }}
            >
              <Maximize2 size={18} />
              <span>{startingInterview ? 'Launching Fullscreen...' : 'Start Mock Interview (Fullscreen)'}</span>
            </button>

            <button
              type="button"
              onClick={handleCancelVerification}
              className="btn-secondary"
              style={{ width: '100%', padding: '10px', fontSize: '13px' }}
            >
              <ArrowLeft size={15} />
              <span>Cancel & Return to Setup</span>
            </button>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="alert-error" style={{ marginTop: '16px' }}>
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
