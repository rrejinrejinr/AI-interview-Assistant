import React, { useState, useEffect } from 'react';
import { Video, ShieldCheck, AlertCircle, ArrowRight, ArrowLeft, FileText, CheckCircle2, Lock, Camera } from 'lucide-react';
import { startMockInterviewApi, getResumeDetailsApi, getActiveResumeDetailsApi } from '../services/api';

export default function MockInterviewSetup({ resumes = [], activeResumeId, onProceedToVerification, onNavigateToUpload, onBack }) {
  const [selectedResumeId, setSelectedResumeId] = useState(activeResumeId ? String(activeResumeId) : '');
  const [difficulty, setDifficulty] = useState('Medium');
  const [resumeProfile, setResumeProfile] = useState(null);
  const [loadingResume, setLoadingResume] = useState(Boolean(activeResumeId));
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

  // Fetch full details of active/selected resume for Mock Interview questions
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
        console.error('Error fetching resume for mock interview:', err);
        setResumeProfile(null);
      })
      .finally(() => {
        if (isMounted) setLoadingResume(false);
      });

    return () => { isMounted = false; };
  }, [selectedResumeId]);

  const handleStartSetup = async (e) => {
    e.preventDefault();
    const effId = selectedResumeId || activeResumeId;
    if (!effId) {
      setError('No resume uploaded yet. Please upload your resume to get started.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const sessionData = await startMockInterviewApi(
        effId ? parseInt(effId, 10) : undefined,
        difficulty
      );
      if (onProceedToVerification) {
        onProceedToVerification(sessionData);
      }
    } catch (err) {
      console.error('Start Mock Interview Error:', err);
      const msg = err.response?.data?.detail || 'Failed to initialize mock interview.';
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
    <div className="ai-card">
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
              <Video size={20} className="text-primary" />
              <span>Formal 30-Question Mock Interview Setup</span>
            </h3>
            <p className="card-subtitle">
              A comprehensive, monitored technical interview generated strictly from your active uploaded resume.
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

      <form onSubmit={handleStartSetup} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Fixed 30 Questions Notice Banner */}
        <div style={{
          background: 'var(--primary-light)',
          border: '1.5px solid var(--primary)',
          borderRadius: '12px',
          padding: '16px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px'
        }}>
          <ShieldCheck size={28} className="text-primary" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: '800', fontSize: '14px', color: 'var(--primary)', marginBottom: '2px' }}>
              Standard 30-Question Assessment
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              Every mock interview contains exactly 30 questions derived strictly from your verified skills, projects, and work experience.
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

        {/* Candidate Profile Preview Capsule */}
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
                Target Role
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

            <div>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Experience Level
              </span>
              <div style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {resumeProfile.candidate_info?.years_of_experience || 'Not specified'}
              </div>
            </div>
          </div>
        )}

        {/* Difficulty Selection */}
        <div>
          <label className="form-label">Interview Difficulty Level *</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '6px' }}>
            {[
              { id: 'Easy', label: 'Easy', desc: 'Core fundamentals, syntax, standard library usage & basic definitions' },
              { id: 'Medium', label: 'Medium', desc: 'Practical engineering, scenario trade-offs, testing & architecture' },
              { id: 'Hard', label: 'Hard', desc: 'Distributed systems, high concurrency, performance optimization & deep debugging' }
            ].map((d) => {
              const isSelected = difficulty === d.id;
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDifficulty(d.id)}
                  style={{
                    padding: '16px 14px',
                    borderRadius: '12px',
                    border: isSelected ? '2px solid var(--primary)' : '1.5px solid var(--border-light)',
                    background: isSelected ? 'var(--primary-light)' : 'var(--bg-surface)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-primary)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.18s'
                  }}
                >
                  <div style={{ fontWeight: '800', fontSize: '14px', marginBottom: '4px' }}>{d.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.35' }}>{d.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Integrity & Camera Requirements Brief */}
        <div style={{
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: '12px',
          padding: '14px 16px'
        }}>
          <div style={{ fontWeight: '700', fontSize: '13px', color: 'var(--text-primary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Lock size={15} className="text-primary" />
            <span>Interview Integrity & Proctoring Requirements</span>
          </div>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <li>Pre-interview camera check and one verification photograph capture.</li>
            <li>Interview will launch in browser Fullscreen mode.</li>
            <li>Continuous client-side MediaPipe face presence monitoring (no biometric face databases or facial recognition).</li>
            <li>Sustained face absence or multiple faces will trigger interview termination and dispatch a notification email.</li>
          </ul>
        </div>

        <button
          type="submit"
          disabled={loading || !selectedResumeId}
          className="btn-primary"
          style={{ width: '100%', padding: '14px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
        >
          <Camera size={18} />
          <span>{loading ? 'Synthesizing 30 Questions...' : 'Proceed to Camera Verification'}</span>
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
