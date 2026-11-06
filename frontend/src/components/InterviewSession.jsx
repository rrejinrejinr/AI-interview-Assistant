import React, { useState, useEffect, useRef } from 'react';
import {
  Video,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  MessageSquare,
  Send,
  Award
} from 'lucide-react';
import { submitAnswerApi, completeInterviewApi, getFollowupQuestionApi } from '../services/api';

const scoreColor = (score) => {
  if (score === null || score === undefined) return 'var(--text-muted)';
  if (score >= 75) return 'var(--success)';
  if (score >= 50) return 'var(--warning)';
  return 'var(--danger)';
};

export default function InterviewSession({ session, cameraStream, onInterviewComplete }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);
  const [allEvaluations, setAllEvaluations] = useState([]);

  // Follow-up state
  const [followupQ, setFollowupQ] = useState(null);
  const [loadingFollowup, setLoadingFollowup] = useState(false);

  // PiP Camera & Face Monitoring State
  const pipVideoRef = useRef(null);
  const monitorTimerRef = useRef(null);
  const [facePresent, setFacePresent] = useState(true);
  const [missingFaceCount, setMissingFaceCount] = useState(0);
  const [showFaceWarning, setShowFaceWarning] = useState(false);

  const questions = session.questions || [];
  const currentQ = followupQ || questions[currentIdx];
  const isLastQ = currentIdx === questions.length - 1 && !followupQ;
  const progress = Math.round(((allEvaluations.length) / questions.length) * 100);

  useEffect(() => {
    let isMounted = true;

    if (cameraStream && pipVideoRef.current) {
      pipVideoRef.current.srcObject = cameraStream;
      pipVideoRef.current.play().catch(() => {});
    }

    if (cameraStream && window.FaceDetection) {
      const faceDetector = new window.FaceDetection({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`
      });

      faceDetector.setOptions({
        model: 'short',
        minDetectionConfidence: 0.5
      });

      faceDetector.onResults((results) => {
        if (!isMounted) return;
        const detected = results.detections && results.detections.length > 0;
        setFacePresent(detected);

        if (!detected) {
          setMissingFaceCount((prev) => {
            const next = prev + 1;
            if (next >= 2) setShowFaceWarning(true);
            return next;
          });
        } else {
          setMissingFaceCount(0);
          setShowFaceWarning(false);
        }
      });

      monitorTimerRef.current = setInterval(async () => {
        if (pipVideoRef.current && pipVideoRef.current.readyState >= 2) {
          try {
            await faceDetector.send({ image: pipVideoRef.current });
          } catch (e) {}
        }
      }, 4000);
    }

    return () => {
      isMounted = false;
      if (monitorTimerRef.current) clearInterval(monitorTimerRef.current);
      if (cameraStream) {
        cameraStream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [cameraStream]);

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) {
      setError('Please provide a substantive answer before submitting.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await submitAnswerApi(session.session_id, currentQ.id || questions[currentIdx].id, answer);
      setEvaluation(result);
      setAllEvaluations((prev) => [...prev, { ...result, question: currentQ.question }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to evaluate answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAskFollowup = async () => {
    setLoadingFollowup(true);
    try {
      const res = await getFollowupQuestionApi(
        session.resume_id,
        currentQ.question,
        answer
      );
      setFollowupQ({
        id: currentQ.id,
        question: res.question,
        category: res.category || 'Follow-Up',
        difficulty: res.difficulty || 'Medium'
      });
      setEvaluation(null);
      setAnswer('');
    } catch (err) {
      console.error('Follow-up error:', err);
    } finally {
      setLoadingFollowup(false);
    }
  };

  const handleNext = () => {
    setEvaluation(null);
    setAnswer('');
    setFollowupQ(null);
    setError(null);
    setCurrentIdx((prev) => prev + 1);
  };

  const handleComplete = async () => {
    setCompleting(true);
    setError(null);
    try {
      if (cameraStream) {
        cameraStream.getTracks().forEach((t) => t.stop());
      }
      const report = await completeInterviewApi(session.session_id);
      onInterviewComplete(report, allEvaluations);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to finalize interview report.');
    } finally {
      setCompleting(false);
    }
  };

  if (!currentQ) return null;

  return (
    <div className="ai-card" style={{ position: 'relative' }}>
      {/* Top Header & PiP Camera Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', gap: '16px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '13px', fontWeight: '800', color: 'var(--text-primary)' }}>
              Question {currentIdx + 1} of {questions.length}
            </span>
            <span style={{ padding: '3px 10px', borderRadius: '12px', background: 'var(--primary-light)', fontSize: '12px', fontWeight: '700', color: 'var(--primary)' }}>
              {currentQ.question_type || session.interview_type}
            </span>
            <span style={{ padding: '3px 10px', borderRadius: '12px', background: 'var(--warning-light)', fontSize: '12px', fontWeight: '700', color: 'var(--warning)' }}>
              {currentQ.difficulty || session.difficulty}
            </span>
            {followupQ && (
              <span style={{ padding: '3px 10px', borderRadius: '12px', background: 'var(--success-light)', fontSize: '12px', fontWeight: '800', color: 'var(--success)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <MessageSquare size={12} />
                <span>AI Follow-Up</span>
              </span>
            )}
          </div>
          <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Session Completion: <b>{progress}%</b>
          </div>
        </div>

        {/* PiP Camera Preview */}
        {cameraStream && (
          <div style={{
            position: 'relative',
            width: '150px',
            height: '112px',
            borderRadius: '12px',
            overflow: 'hidden',
            background: '#0f172a',
            border: `2.5px solid ${facePresent ? 'var(--success)' : 'var(--danger)'}`,
            flexShrink: 0,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
          }}>
            <video
              ref={pipVideoRef}
              playsInline
              muted
              autoPlay
              style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
            />
            <div style={{
              position: 'absolute',
              bottom: '4px',
              left: '4px',
              right: '4px',
              background: 'rgba(15, 23, 42, 0.85)',
              color: 'white',
              fontSize: '10px',
              fontWeight: '700',
              padding: '2px 6px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              justifyContent: 'center'
            }}>
              <span style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: facePresent ? '#22c55e' : '#ef4444',
                display: 'inline-block'
              }} />
              {facePresent ? 'Face Detected' : 'Not Visible'}
            </div>
          </div>
        )}
      </div>

      {/* Face Absence Warning */}
      {showFaceWarning && (
        <div className="alert-error" style={{ marginBottom: '16px' }}>
          <AlertCircle size={16} />
          <span><b>Candidate presence check:</b> Please ensure your face is clearly visible to the webcam.</span>
        </div>
      )}

      {/* Progress Bar */}
      <div style={{ background: 'var(--border-light)', height: '6px', borderRadius: '3px', marginBottom: '20px', overflow: 'hidden' }}>
        <div style={{
          background: 'var(--primary)',
          height: '100%',
          width: `${progress}%`,
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* Question Card */}
      <div style={{
        background: 'var(--bg-card-subtle)',
        border: '1.5px solid var(--border-light)',
        borderLeft: '4px solid var(--primary)',
        padding: '18px 20px',
        borderRadius: '12px',
        marginBottom: '20px'
      }}>
        <p style={{ margin: 0, fontSize: '16.5px', color: 'var(--text-primary)', lineHeight: '1.6', fontWeight: '700' }}>
          {currentQ.question}
        </p>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', display: 'block' }}>
          Focus Domain: <b>{currentQ.category || 'General Technical'}</b>
        </span>
      </div>

      {/* Answer Form */}
      {!evaluation && (
        <div>
          <label className="form-label">Your Answer (Be detailed and provide technical context):</label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your response here... Explain core principles, design considerations, and concrete technical examples."
            className="form-textarea"
            style={{ minHeight: '140px' }}
          />

          {error && (
            <div className="alert-error" style={{ marginTop: '12px' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button
            onClick={handleSubmitAnswer}
            disabled={loading}
            className="btn-primary"
            style={{ marginTop: '16px', padding: '12px 28px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            <Send size={15} />
            <span>{loading ? 'Evaluating Response with ML Engine...' : 'Submit Answer for Evaluation'}</span>
          </button>
        </div>
      )}

      {/* Evaluation Results Card */}
      {evaluation && (
        <div style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border-light)', padding: '20px', borderRadius: '12px' }}>
          <h4 style={{ margin: '0 0 14px', color: 'var(--text-primary)', fontSize: '16px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Award size={18} className="text-primary" />
            <span>Real-Time Answer Evaluation Score</span>
          </h4>

          {/* 3 Metric Score Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '16px' }}>
            <div style={{ textAlign: 'center', padding: '14px', background: 'var(--bg-surface)', borderRadius: '10px', border: `2px solid ${scoreColor(evaluation.combined_score)}` }}>
              <div style={{ fontSize: '26px', fontWeight: '900', color: scoreColor(evaluation.combined_score) }}>
                {evaluation.combined_score?.toFixed(0)}
              </div>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)', marginTop: '2px', textTransform: 'uppercase' }}>
                Overall Score
              </div>
            </div>

            <div style={{ textAlign: 'center', padding: '14px', background: 'var(--bg-surface)', borderRadius: '10px', border: '2px solid var(--primary-border)' }}>
              <div style={{ fontSize: '26px', fontWeight: '900', color: 'var(--primary)' }}>
                {evaluation.semantic_score?.toFixed(0)}
              </div>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)', marginTop: '2px', textTransform: 'uppercase' }}>
                Semantic Match
              </div>
            </div>

            <div style={{ textAlign: 'center', padding: '14px', background: 'var(--bg-surface)', borderRadius: '10px', border: '2px solid var(--success-border)' }}>
              <div style={{ fontSize: '26px', fontWeight: '900', color: 'var(--success)' }}>
                {evaluation.keyword_score?.toFixed(0)}
              </div>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)', marginTop: '2px', textTransform: 'uppercase' }}>
                Keyword Coverage
              </div>
            </div>
          </div>

          {/* Detailed Feedback */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '14px 16px', borderRadius: '10px', marginBottom: '14px', fontSize: '13.5px', color: 'var(--text-primary)', lineHeight: '1.6' }}>
            <b>Feedback:</b> {evaluation.feedback}
          </div>

          {/* Keywords Covered */}
          {evaluation.matched_keywords?.length > 0 && (
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '12.5px', color: 'var(--success)', fontWeight: '700' }}>Covered Keywords: </span>
              <span style={{ fontSize: '12.5px', color: 'var(--text-primary)' }}>{evaluation.matched_keywords.join(', ')}</span>
            </div>
          )}

          {/* Missing Keywords */}
          {evaluation.missing_keywords?.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <span style={{ fontSize: '12.5px', color: 'var(--warning)', fontWeight: '700' }}>Areas to Strengthen: </span>
              <span style={{ fontSize: '12.5px', color: 'var(--text-primary)' }}>{evaluation.missing_keywords.slice(0, 4).join(', ')}</span>
            </div>
          )}

          {/* Action Row */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
            {!followupQ && (
              <button
                onClick={handleAskFollowup}
                disabled={loadingFollowup}
                className="btn-secondary"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <MessageSquare size={14} />
                <span>{loadingFollowup ? 'Generating Question...' : 'Ask AI Follow-Up'}</span>
              </button>
            )}

            {!isLastQ && (
              <button
                onClick={handleNext}
                className="btn-primary"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <span>Next Question</span>
                <ArrowRight size={14} />
              </button>
            )}

            {isLastQ && (
              <button
                onClick={handleComplete}
                disabled={completing}
                className="btn-primary"
                style={{
                  background: completing ? 'var(--text-muted)' : 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <CheckCircle2 size={15} />
                <span>{completing ? 'Compiling Final Report...' : 'Complete Interview & View Report'}</span>
              </button>
            )}
          </div>

          {error && (
            <div className="alert-error" style={{ marginTop: '12px' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
