import React, { useState, useEffect } from 'react';
import { MessagesSquare, Mic, AlertCircle, ArrowRight, ArrowLeft, FileText, CheckCircle2, UserCheck, Sparkles } from 'lucide-react';
import { startAiInterviewApi, getResumeDetailsApi, getActiveResumeDetailsApi } from '../services/api';

export default function AIOneToOneSetup({ resumes = [], activeResumeId, onInterviewStarted, onNavigateToUpload, onBack }) {
  const [selectedResumeId, setSelectedResumeId] = useState(activeResumeId ? String(activeResumeId) : '');
  const [resumeProfile, setResumeProfile] = useState(null);
  const [loadingResume, setLoadingResume] = useState(Boolean(activeResumeId));
  const [micStatus, setMicStatus] = useState('unchecked'); // unchecked | ready | denied
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync strictly with activeResumeId
  useEffect(() => {
    if (activeResumeId) {
      setSelectedResumeId(String(activeResumeId));
    } else {
      setSelectedResumeId('');
      setResumeProfile(null);
      setLoadingResume(false);
    }
  }, [activeResumeId]);

  // Fetch full details of active/selected resume for AI One-to-One setup
  useEffect(() => {
    if (!selectedResumeId) {
      setResumeProfile(null);
      setLoadingResume(false);
      return;
    }

    let isMounted = true;
    setLoadingResume(true);

    getResumeDetailsApi(parseInt(selectedResumeId, 10))
      .then((data) => {
        if (!isMounted) return;
        setResumeProfile(data);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Error fetching resume for AI One-to-One setup:', err);
        setResumeProfile(null);
      })
      .finally(() => {
        if (isMounted) setLoadingResume(false);
      });

    return () => { isMounted = false; };
  }, [selectedResumeId]);

  const testMicrophone = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicStatus('ready');
      stream.getTracks().forEach((t) => t.stop());
    } catch (err) {
      console.warn('Microphone permission error:', err);
      setMicStatus('denied');
    }
  };

  const handleStart = async (e) => {
    e.preventDefault();
    const effId = selectedResumeId || activeResumeId;
    if (!effId) {
      setError('No resume uploaded yet. Please upload your resume to get started.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const sessionData = await startAiInterviewApi(
        effId ? parseInt(effId, 10) : undefined
      );
      if (onInterviewStarted) {
        onInterviewStarted(sessionData);
      }
    } catch (err) {
      console.error('Start AI Interview Error:', err);
      const msg = err.response?.data?.detail || 'Failed to start HR interview session.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const activeResumeObj = resumes.find(r => String(r.id) === String(selectedResumeId)) || resumeProfile;
  const currentFilename = resumeProfile?.filename || activeResumeObj?.filename;

  if (loadingResume) {
    return (
      <div className="ai-card">
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '14px', fontWeight: '600' }}>Loading active candidate resume...</div>
        </div>
      </div>
    );
  }

  if (!selectedResumeId && !resumeProfile) {
    return (
      <div className="ai-card">
        <div className="empty-state">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
            <FileText size={40} color="var(--text-muted)" />
          </div>
          <div className="empty-title" style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>
            No resume uploaded yet. Please upload your resume to get started.
          </div>
          {onNavigateToUpload && (
            <button onClick={onNavigateToUpload} className="btn-primary" style={{ marginTop: '14px' }}>
              <span>Upload Resume</span>
              <ArrowRight size={15} />
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="ai-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {onBack && (
            <button
              onClick={onBack}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 14px', fontSize: '13px' }}
            >
              <ArrowLeft size={16} />
              <span>Back</span>
            </button>
          )}
          <div>
            <h3 className="card-title">
              <MessagesSquare size={20} className="text-primary" />
              <span>HR Interview Setup</span>
            </h3>
            <p className="card-subtitle">
              An interactive, voice-enabled HR interview with adaptive follow-up questioning tailored to your resume.
            </p>
          </div>
        </div>

        {/* Read-Only Active Resume Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          padding: '6px 14px',
          borderRadius: '20px',
          fontSize: '12.5px'
        }}>
          <FileText size={14} className="text-primary" />
          <span style={{ color: 'var(--text-secondary)' }}>Active Resume:</span>
          <b style={{ color: 'var(--text-primary)' }}>{currentFilename || 'Active Resume'}</b>
        </div>
      </div>

      <form onSubmit={handleStart} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Interactive Feature Banner */}
        <div style={{
          background: 'var(--primary-light)',
          border: '1.5px solid var(--primary)',
          borderRadius: '12px',
          padding: '16px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <Sparkles size={28} className="text-primary" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: '800', fontSize: '14px', color: 'var(--primary)', marginBottom: '2px' }}>
              Adaptive HR Interview
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              The AI interviewer listens to your verbal or typed responses, understands your context, and asks dynamic follow-up questions just like an experienced technical recruiter.
            </div>
          </div>
        </div>

        {/* Active Candidate Resume Card */}
        <div>
          <label className="form-label">Active Candidate Resume</label>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '12px 16px',
            borderRadius: '10px',
            fontSize: '13.5px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
              <FileText size={18} className="text-primary" style={{ flexShrink: 0 }} />
              <span style={{ fontWeight: '700', color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {currentFilename || (selectedResumeId ? `Resume #${selectedResumeId}` : 'Active Resume')}
              </span>
            </div>
          </div>
        </div>

        {/* Candidate Profile Preview */}
        {resumeProfile && (
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 18px',
            borderRadius: '12px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px'
          }}>
            <div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Interviewing For
              </span>
              <div style={{ fontSize: '14px', fontWeight: '800', color: 'var(--primary)', marginTop: '2px' }}>
                {resumeProfile.predicted_role || 'Software Engineer'}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Candidate Name
              </span>
              <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {resumeProfile.candidate_info?.name || 'Verified Candidate'}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Verified Skills
              </span>
              <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--success)', marginTop: '2px' }}>
                {resumeProfile.skills_list?.length || 0} skills detected
              </div>
            </div>
          </div>
        )}

        {/* Microphone Check Widget */}
        <div style={{
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: '12px',
          padding: '16px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <div>
            <div style={{ fontWeight: '700', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mic size={16} className="text-primary" />
              <span>Microphone & Speech Input Check</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              You can speak your answers or type them. Speech transcripts can be reviewed and edited before submitting.
            </div>
          </div>

          <button
            type="button"
            onClick={testMicrophone}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '12px' }}
          >
            {micStatus === 'ready' ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)', fontWeight: '700' }}>
                <CheckCircle2 size={14} /> Mic Ready
              </span>
            ) : micStatus === 'denied' ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontWeight: '700' }}>
                <AlertCircle size={14} /> Permission Denied
              </span>
            ) : (
              'Test Microphone'
            )}
          </button>
        </div>

        <button
          type="submit"
          disabled={loading || (!selectedResumeId && !resumeProfile)}
          className="btn-primary"
          style={{ width: '100%', padding: '14px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
        >
          <MessagesSquare size={18} />
          <span>{loading ? 'Initializing Interviewer...' : 'Start HR Interview'}</span>
          <ArrowRight size={16} />
        </button>
      </form>

      {error && (
        <div className="alert-error" style={{ marginTop: '16px' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
