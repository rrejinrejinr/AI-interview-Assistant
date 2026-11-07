import React, { useState } from 'react';
import { Video, Camera, AlertCircle, ArrowRight } from 'lucide-react';
import { startInterviewApi } from '../services/api';

const TYPES = ['Technical', 'Behavioral', 'HR', 'Mixed'];
const DIFFICULTIES = ['Easy', 'Medium', 'Hard'];
const Q_COUNTS = [3, 5, 7, 10];

export default function InterviewSetup({ resumes, onSessionCreated }) {
  const [resumeId, setResumeId] = useState(resumes && resumes[0]?.id ? String(resumes[0].id) : '');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewType, setInterviewType] = useState('Technical');
  const [difficulty, setDifficulty] = useState('Medium');
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    if (!resumeId) {
      setError('Please select an active resume first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const session = await startInterviewApi(
        parseInt(resumeId, 10),
        jobDescription || null,
        interviewType,
        difficulty,
        numQuestions
      );
      onSessionCreated(session);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize interview session.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Video size={20} className="text-primary" />
            <span>AI Mock Interview Configuration</span>
          </h3>
          <p className="card-subtitle">
            Configure a personalized, resume-targeted technical screen with real-time answer scoring and face presence monitoring.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert-error" style={{ marginBottom: '18px' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Active Resume Card */}
      <div className="form-group">
        <label className="form-label">Active Candidate Resume</label>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          padding: '10px 14px',
          borderRadius: '8px',
          fontSize: '13px'
        }}>
          <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>
            {resumes.find(r => String(r.id) === String(resumeId))?.filename || (resumeId ? `Resume #${resumeId}` : 'No Resume Selected')}
          </span>
        </div>
      </div>

      {/* Optional Job Description */}
      <div className="form-group">
        <label className="form-label">Job Description (Optional — Sharpens Question Relevance)</label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste job description to tailor interview questions specifically to the position's stack..."
          className="form-textarea"
          style={{ minHeight: '80px' }}
        />
      </div>

      {/* Interview Type Selector */}
      <div className="form-group">
        <label className="form-label">Interview Type</label>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {TYPES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setInterviewType(t)}
              style={{
                padding: '9px 18px',
                borderRadius: '8px',
                border: '1.5px solid',
                borderColor: interviewType === t ? 'var(--primary)' : 'var(--border-light)',
                background: interviewType === t ? 'var(--primary-light)' : 'var(--bg-surface)',
                color: interviewType === t ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Difficulty Selector */}
      <div className="form-group">
        <label className="form-label">Difficulty Level</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          {DIFFICULTIES.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDifficulty(d)}
              style={{
                padding: '9px 18px',
                borderRadius: '8px',
                border: '1.5px solid',
                borderColor: difficulty === d ? 'var(--primary)' : 'var(--border-light)',
                background: difficulty === d ? 'var(--primary-light)' : 'var(--bg-surface)',
                color: difficulty === d ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Number of Questions */}
      <div className="form-group" style={{ marginBottom: '24px' }}>
        <label className="form-label">Question Count</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          {Q_COUNTS.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setNumQuestions(n)}
              style={{
                padding: '9px 20px',
                borderRadius: '8px',
                border: '1.5px solid',
                borderColor: numQuestions === n ? 'var(--primary)' : 'var(--border-light)',
                background: numQuestions === n ? 'var(--primary-light)' : 'var(--bg-surface)',
                color: numQuestions === n ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {n} Questions
            </button>
          ))}
        </div>
      </div>

      {/* Proceed Button */}
      <button
        onClick={handleStart}
        disabled={loading || !resumeId}
        className="btn-primary"
        style={{ width: '100%', padding: '13px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
      >
        <Camera size={16} />
        <span>{loading ? 'Generating Personalized Questions...' : 'Proceed to Camera Verification'}</span>
        <ArrowRight size={16} />
      </button>
    </div>
  );
}
