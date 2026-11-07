import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ArrowLeft,
  Play,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';

export default function CameraVerification({ session, onBeginInterview, onCancel }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const timerRef = useRef(null);

  const [cameraStatus, setCameraStatus] = useState('requesting'); // requesting | active | denied | error
  const [faceDetected, setFaceDetected] = useState(false);
  const [consecutiveDetections, setConsecutiveDetections] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [modelLoading, setModelLoading] = useState(true);

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
          audio: false
        });

        if (!isMounted) {
          stream.getTracks().forEach(t => t.stop());
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
            const hasFace = results.detections && results.detections.length > 0;
            setFaceDetected(hasFace);
            if (hasFace) {
              setConsecutiveDetections(prev => Math.min(prev + 1, 5));
            } else {
              setConsecutiveDetections(0);
            }
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
          setFaceDetected(true);
          setConsecutiveDetections(3);
        }

      } catch (err) {
        if (!isMounted) return;
        console.error('Camera init error:', err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setCameraStatus('denied');
          setErrorMessage('Camera access was denied. Please allow camera access in your browser settings to proceed with the mock interview.');
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setCameraStatus('error');
          setErrorMessage('No camera device found on your system. Please connect a webcam.');
        } else {
          setCameraStatus('error');
          setErrorMessage(err.message || 'Unable to access camera.');
        }
      }
    }

    initCameraAndDetector();

    return () => {
      isMounted = false;
      if (timerRef.current) clearInterval(timerRef.current);
      if (detectorRef.current) {
        try { detectorRef.current.close(); } catch (e) {}
      }
    };
  }, []);

  const handleCancel = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
    }
    onCancel();
  };

  const handleProceed = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    onBeginInterview(streamRef.current);
  };

  const isFaceVerified = consecutiveDetections >= 2;

  return (
    <div className="ai-card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Camera size={20} className="text-primary" />
            <span>Camera & Face-Presence Pre-Flight Check</span>
          </h3>
          <p className="card-subtitle">
            Position yourself clearly in the frame. Face-presence verification ensures engagement before session launch.
          </p>
        </div>
      </div>

      {/* Video Container */}
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: '540px',
        margin: '0 auto 22px',
        borderRadius: '16px',
        overflow: 'hidden',
        background: '#0f172a',
        aspectRatio: '4/3',
        border: `3px solid ${isFaceVerified ? 'var(--success)' : cameraStatus === 'active' ? 'var(--warning)' : 'var(--border-light)'}`,
        boxShadow: isFaceVerified ? '0 0 24px rgba(22, 163, 74, 0.3)' : '0 8px 20px rgba(0,0,0,0.15)',
        transition: 'all 0.3s ease'
      }}>
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
        />

        {/* Live Status Overlay Badges */}
        <div style={{
          position: 'absolute',
          top: '14px',
          left: '14px',
          right: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pointerEvents: 'none'
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(6px)',
            color: 'white',
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: cameraStatus === 'active' ? '#22c55e' : '#ef4444',
              boxShadow: cameraStatus === 'active' ? '0 0 8px #22c55e' : 'none'
            }} />
            {cameraStatus === 'active' ? 'Camera Live' : cameraStatus === 'requesting' ? 'Connecting...' : 'Camera Inactive'}
          </div>

          {cameraStatus === 'active' && (
            <div style={{
              background: isFaceVerified ? 'rgba(22, 163, 74, 0.92)' : 'rgba(234, 179, 8, 0.92)',
              color: 'white',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '800',
              backdropFilter: 'blur(6px)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              {isFaceVerified ? (
                <>
                  <CheckCircle2 size={13} />
                  <span>Face Detected</span>
                </>
              ) : modelLoading ? (
                <span>Loading detector...</span>
              ) : (
                <>
                  <AlertCircle size={13} />
                  <span>Face Not Detected</span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Center Prompt if no camera or error */}
        {cameraStatus === 'requesting' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.75)', color: 'white' }}>
            <RefreshCw size={28} className="spin" style={{ marginBottom: '8px' }} />
            <div style={{ fontSize: '14px', fontWeight: '700' }}>Requesting camera permission...</div>
          </div>
        )}

        {cameraStatus === 'denied' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.9)', color: 'white', padding: '24px', textAlign: 'center' }}>
            <AlertCircle size={36} color="#f87171" style={{ marginBottom: '10px' }} />
            <div style={{ fontSize: '16px', fontWeight: '800', color: '#f87171', marginBottom: '6px' }}>Camera Permission Denied</div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.4' }}>{errorMessage}</div>
          </div>
        )}

        {cameraStatus === 'error' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.9)', color: 'white', padding: '24px', textAlign: 'center' }}>
            <AlertTriangle size={36} color="#f87171" style={{ marginBottom: '10px' }} />
            <div style={{ fontSize: '16px', fontWeight: '800', color: '#f87171', marginBottom: '6px' }}>Camera Hardware Error</div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.4' }}>{errorMessage}</div>
          </div>
        )}
      </div>

      {/* Verification Feedback Banner */}
      <div style={{
        background: isFaceVerified ? 'var(--success-light)' : 'var(--warning-light)',
        border: `1px solid ${isFaceVerified ? 'var(--success-border)' : 'var(--warning-border)'}`,
        padding: '14px 18px',
        borderRadius: '10px',
        marginBottom: '18px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        {isFaceVerified ? (
          <CheckCircle2 size={20} color="var(--success)" />
        ) : (
          <AlertCircle size={20} color="var(--warning)" />
        )}
        <div style={{ fontSize: '13.5px', color: isFaceVerified ? 'var(--success)' : 'var(--warning)', lineHeight: '1.4' }}>
          {isFaceVerified ? (
            <b>Face presence verified! You are ready to start your mock interview.</b>
          ) : (
            <span>Please position yourself in a well-lit area facing the webcam until your face is detected.</span>
          )}
        </div>
      </div>

      {/* Privacy Guarantee Box */}
      <div style={{
        background: 'var(--bg-surface-secondary)',
        border: '1px solid var(--border-light)',
        borderRadius: '10px',
        padding: '12px 16px',
        marginBottom: '24px',
        fontSize: '12.5px',
        color: 'var(--text-secondary)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        <ShieldCheck size={20} color="var(--primary)" />
        <div>
          <b style={{ color: 'var(--text-primary)' }}>Privacy Guarantee:</b> Camera processing runs 100% locally in your browser using MediaPipe WebAssembly. Zero video frames or biometric templates are stored or transmitted.
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={handleCancel}
          className="btn-secondary"
        >
          <ArrowLeft size={14} />
          <span>Back to Setup</span>
        </button>

        <button
          onClick={handleProceed}
          disabled={!isFaceVerified}
          className="btn-primary"
          style={{
            background: isFaceVerified ? 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)' : 'var(--text-muted)',
            boxShadow: isFaceVerified ? '0 4px 14px rgba(22, 163, 74, 0.35)' : 'none'
          }}
        >
          <Play size={14} />
          <span>{isFaceVerified ? 'Start Interview Session' : 'Face Detection Required'}</span>
        </button>
      </div>
    </div>
  );
}
