import React, { useState, useEffect } from 'react';
import {
  Target,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  ArrowLeft,
  RefreshCw,
  Info,
  User,
  Edit3,
  Briefcase,
  Search,
  ArrowRight
} from 'lucide-react';
import { analyzeAtsApi, getResumeDetailsApi, getActiveResumeDetailsApi } from '../services/api';

export default function AtsCard({ activeResumeId, resumes = [], onNavigateToUpload, onBack }) {
  const [selectedResumeId, setSelectedResumeId] = useState(activeResumeId ? String(activeResumeId) : '');
  const [selectedResumeProfile, setSelectedResumeProfile] = useState(null);
  const [loadingResume, setLoadingResume] = useState(Boolean(activeResumeId));
  const [jobTitle, setJobTitle] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [atsResult, setAtsResult] = useState(null);
  const [roleOverride, setRoleOverride] = useState('');   // User-entered role to override inferred
  const [showRoleEdit, setShowRoleEdit] = useState(false);
  const [analyzedResumeId, setAnalyzedResumeId] = useState(null);

  // Sync strictly with activeResumeId
  useEffect(() => {
    if (activeResumeId) {
      setSelectedResumeId(String(activeResumeId));
    } else {
      setSelectedResumeId('');
      setSelectedResumeProfile(null);
      setAtsResult(null);
      setAnalyzedResumeId(null);
      setLoadingResume(false);
    }
  }, [activeResumeId]);

  // Reset previous analysis when switching resumes to prevent showing stale results
  useEffect(() => {
    setAtsResult(null);
    setError(null);
    setRoleOverride('');
    setShowRoleEdit(false);
  }, [selectedResumeId]);

  // Fetch full details of active/selected resume for Candidate Snapshot
  useEffect(() => {
    if (!selectedResumeId) {
      setSelectedResumeProfile(null);
      setLoadingResume(false);
      return;
    }

    let isMounted = true;
    setLoadingResume(true);

    getResumeDetailsApi(parseInt(selectedResumeId, 10))
      .then((data) => {
        if (!isMounted) return;
        setSelectedResumeProfile(data);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Error fetching resume snapshot for ATS:', err);
        setSelectedResumeProfile(null);
      })
      .finally(() => {
        if (isMounted) setLoadingResume(false);
      });

    return () => { isMounted = false; };
  }, [selectedResumeId]);

  const handleAnalyze = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (loading) return; // Prevent duplicate API calls from repeated clicks
    const effResumeId = selectedResumeId || activeResumeId || selectedResumeProfile?.id;
    if (!effResumeId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await analyzeAtsApi(
        parseInt(effResumeId, 10),
        jobTitle.trim() || undefined,
        jobDescription.trim() || undefined
      );
      setAtsResult(data);
      setAnalyzedResumeId(String(effResumeId));
    } catch (err) {
      console.error('ATS Error:', err);
      const msg = err.response?.data?.detail || err.message || 'Unable to complete ATS analysis. Please verify your connection and try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const safeFixed = (val, digits = 1) => {
    const n = Number(val);
    return isNaN(n) ? '0.0' : n.toFixed(digits);
  };

  const parseSkillsList = (skills) => {
    if (!skills) return [];
    if (Array.isArray(skills)) {
      return skills.map((s) => (typeof s === 'object' && s !== null ? (s.name || s.skill || JSON.stringify(s)) : String(s))).filter(Boolean);
    }
    if (typeof skills === 'object' && skills !== null) {
      try {
        return Object.values(skills).flat().map((s) => (typeof s === 'object' && s !== null ? (s.name || s.skill || JSON.stringify(s)) : String(s))).filter(Boolean);
      } catch {
        return [];
      }
    }
    if (typeof skills === 'string') {
      try {
        const parsed = JSON.parse(skills);
        if (Array.isArray(parsed)) return parseSkillsList(parsed);
        if (typeof parsed === 'object' && parsed !== null) return parseSkillsList(parsed);
      } catch {
        return skills.split(',').map((s) => s.trim()).filter(Boolean);
      }
    }
    return [];
  };

  const getScoreColor = (score) => {
    const num = Number(score || 0);
    if (num >= 75) return 'var(--success, #10b981)';
    if (num >= 50) return 'var(--warning, #f59e0b)';
    return 'var(--danger, #ef4444)';
  };

  const getSourceBadge = (source) => {
    const badges = {
      user_selected:  { label: 'Selected by you',      color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
      resume_explicit:{ label: 'Stated in resume',     color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
      resume_inferred:{ label: 'Inferred from resume', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)'  },
      not_found:      { label: 'Not found',            color: '#6b7280', bg: 'rgba(107,114,128,0.12)' },
    };
    return badges[source] || badges.not_found;
  };

  const handleReanalyze = async (overrideRole) => {
    if (!selectedResumeId) return;
    setLoading(true);
    setError(null);
    setShowRoleEdit(false);
    try {
      const effectiveTitle = overrideRole || jobTitle.trim() || undefined;
      const data = await analyzeAtsApi(
        parseInt(selectedResumeId, 10),
        effectiveTitle,
        jobDescription.trim() || undefined
      );
      setAtsResult(data);
      setAnalyzedResumeId(String(selectedResumeId));
      if (overrideRole) setRoleOverride(overrideRole);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Unable to complete ATS analysis.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const activeResumeObj = resumes.find((r) => String(r.id) === String(selectedResumeId)) || selectedResumeProfile;

  const isResumeOnlyMode = atsResult && atsResult.analysis_mode === 'Resume-only analysis';
  const isRoleOnlyMode = atsResult && atsResult.analysis_mode === 'Resume + Target Role';
  const isJdMatchMode = atsResult && (atsResult.analysis_mode === 'Resume + Job Description' || atsResult.analysis_mode === 'Resume + Target Role + Job Description');
  const hasJD = jobDescription.trim().length > 0;
  const hasTitle = jobTitle.trim().length > 0;

  // Derived role display info from result
  const resultTargetRole = atsResult?.target_role || null;
  const resultRoleSource = atsResult?.target_role_source || 'not_found';
  const resultRoleUnclear = atsResult?.target_role_unclear || false;
  const hasRoleMatch = atsResult?.role_match_score != null;
  const resumeQualityScore = atsResult?.resume_quality_score;
  const roleMatchScore = atsResult?.role_match_score;

  if (loadingResume) {
    return (
      <div className="ai-card">
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '14px', fontWeight: '600' }}>Loading your active resume...</div>
        </div>
      </div>
    );
  }

  if (!selectedResumeId && !selectedResumeProfile) {
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
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
            <h3 style={{ margin: 0, fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Target size={22} className="text-primary" />
              <span>ATS Resume Analysis</span>
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Score your resume against a job description or target role.
            </p>
          </div>
        </div>

        {/* Active Resume Badge */}
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
          <b style={{ color: 'var(--text-primary)' }}>{selectedResumeProfile?.filename || activeResumeObj?.filename || 'Active Resume'}</b>
        </div>
      </div>

      {/* Error Card */}
      {error && !loading && (
        <div className="ai-card" style={{ border: '1.5px solid var(--danger, #ef4444)', background: 'var(--danger-light, rgba(239, 68, 68, 0.08))' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <div style={{
              background: 'var(--danger, #ef4444)',
              color: 'white',
              borderRadius: '50%',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <AlertCircle size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h4 style={{ margin: '0 0 6px', fontSize: '15px', fontWeight: '800', color: 'var(--danger, #ef4444)' }}>
                Analysis Failed
              </h4>
              <p style={{ margin: '0 0 14px', fontSize: '13.5px', color: 'var(--text-primary)', lineHeight: '1.5' }}>
                {error}
              </p>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={handleAnalyze}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '13px' }}
                >
                  <RefreshCw size={15} />
                  <span>Try Again</span>
                </button>
                <button
                  type="button"
                  onClick={() => setError(null)}
                  className="btn-secondary"
                  style={{ padding: '8px 16px', fontSize: '13px' }}
                >
                  Edit Input
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Indicator while calculation is running */}
      {loading && (
        <div className="ai-card" style={{ textAlign: 'center', padding: '36px 20px', background: 'var(--bg-card-subtle)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          <h4 style={{ margin: '0 0 6px', fontSize: '15px', fontWeight: '800', color: 'var(--text-primary)' }}>
            Calculating ATS Score...
          </h4>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
            Analyzing resume keyword density, section structure, and role alignment.
          </p>
        </div>
      )}

      {/* Input Form */}
      {(selectedResumeId || selectedResumeProfile) && !atsResult && (
        <div className="ai-card">
          <form onSubmit={handleAnalyze} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
              {/* Active Resume (read-only) */}
              <div>
                <label className="form-label">Active Resume</label>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: 'var(--bg-surface-secondary)',
                  border: '1px solid var(--border-light)',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  fontSize: '13px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                    <FileText size={16} className="text-primary" style={{ flexShrink: 0 }} />
                    <span style={{ fontWeight: '700', color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                      {selectedResumeProfile?.filename || activeResumeObj?.filename || (selectedResumeId ? `Resume #${selectedResumeId}` : 'Active Resume')}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="form-label">Target Job Title (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Software Engineer, Data Scientist"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div>
              <label className="form-label">Job Description (Optional)</label>
              <textarea
                rows={6}
                placeholder="Paste the job description here for a more accurate match analysis."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="form-textarea"
              />
            </div>

            {!hasJD && !hasTitle && (
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                background: 'var(--primary-light, rgba(59, 130, 246, 0.08))',
                border: '1px solid var(--primary-border, rgba(59, 130, 246, 0.2))',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '12.5px',
                color: 'var(--text-secondary)'
              }}>
                <Info size={15} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '1px' }} />
                <span>
                  Without a job description or target role, the analysis evaluates your resume's general structure and skill breadth only. For a role-specific match score, add a job title or paste a job description.
                </span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !selectedResumeId}
              className="btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '14px', fontWeight: '700' }}
            >
              {loading ? 'Analyzing...' : 'Run ATS Analysis'}
            </button>
          </form>
        </div>
      )}

      {/* Resume Snapshot (shown before analysis) */}
      {selectedResumeProfile && !atsResult && (
        <div className="ai-card" style={{ background: 'var(--bg-card-subtle)' }}>
          <div className="card-header" style={{ marginBottom: '12px' }}>
            <div>
              <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Search size={16} className="text-primary" />
                <span>Resume Snapshot</span>
              </h4>
              <p className="card-subtitle">{selectedResumeProfile.filename}</p>
            </div>
            {selectedResumeProfile.confidence_level && (
              <span className="badge-medium">{selectedResumeProfile.confidence_level} Confidence</span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Predicted Role
              </div>
              <div style={{ fontSize: '16px', fontWeight: '800', color: 'var(--primary)', margin: '4px 0 8px' }}>
                {selectedResumeProfile.predicted_role || 'Not detected'}
              </div>
            </div>

            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                Skills Detected ({selectedResumeProfile.skills_list?.length || 0})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', maxHeight: '100px', overflowY: 'auto' }}>
                {selectedResumeProfile.skills_list && selectedResumeProfile.skills_list.length > 0 ? (
                  selectedResumeProfile.skills_list.map((skill) => (
                    <span
                      key={skill}
                      style={{
                        background: 'var(--bg-surface-secondary)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-light)',
                        padding: '3px 8px',
                        borderRadius: '12px',
                        fontSize: '11.5px',
                        fontWeight: '600'
                      }}
                    >
                      {skill}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No skills extracted.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ATS Result Report */}
      {atsResult && (
        <div className="ai-card">
          {/* Actions row */}
          <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
            <button
              onClick={() => setAtsResult(null)}
              className="btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 14px', fontSize: '13px' }}
            >
              <ArrowLeft size={16} />
              <span>New Analysis</span>
            </button>
          </div>

          {/* Score Banner */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '20px 24px',
            borderRadius: '12px',
            marginBottom: '16px',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  background: 'var(--primary-light, rgba(59, 130, 246, 0.12))',
                  color: 'var(--primary, #3b82f6)',
                  border: '1px solid var(--primary-border, rgba(59, 130, 246, 0.25))'
                }}>
                  {atsResult.assessment_mode || (isResumeOnlyMode
                    ? 'General Resume Quality'
                    : isRoleOnlyMode
                    ? 'Role Skill Coverage'
                    : 'Job-Description Match')}
                </span>
              </div>
              <h3 style={{ margin: '4px 0 4px', fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)' }}>
                {isResumeOnlyMode
                  ? 'Resume Quality Assessment'
                  : isRoleOnlyMode
                  ? `Role Compatibility: ${resultTargetRole || atsResult.job_title || jobTitle}`
                  : `Job Match: ${resultTargetRole || atsResult.job_title || jobTitle || 'Target Position'}`}
              </h3>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Resume: <b style={{ color: 'var(--text-primary)' }}>{atsResult.resume_filename || activeResumeObj?.filename || 'Resume'}</b>
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              {/* Score Display (Clean percentage, no colored classification box) */}
              <div style={{
                textAlign: 'center',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-light)',
                padding: '14px 24px',
                borderRadius: '12px',
                minWidth: '120px'
              }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: '800', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  {isResumeOnlyMode ? 'Quality Score' : isRoleOnlyMode ? 'Role Match' : 'ATS Score'}
                </div>
                <div style={{ fontSize: '32px', fontWeight: '900', lineHeight: 1.1, color: 'var(--text-primary)' }}>
                  {safeFixed(atsResult.ats_score, 0)}%
                </div>
              </div>

              {/* Tier score mini-cards (only shown when both are present) */}
              {resumeQualityScore != null && roleMatchScore != null && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                    borderRadius: '8px', padding: '6px 12px', fontSize: '12px'
                  }}>
                    <span style={{ color: 'var(--text-muted)', fontWeight: '600', minWidth: '110px' }}>Resume Quality</span>
                    <span style={{ fontWeight: '800', color: 'var(--text-primary)' }}>{safeFixed(resumeQualityScore, 0)}%</span>
                  </div>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                    borderRadius: '8px', padding: '6px 12px', fontSize: '12px'
                  }}>
                    <span style={{ color: 'var(--text-muted)', fontWeight: '600', minWidth: '110px' }}>Role Match</span>
                    <span style={{ fontWeight: '800', color: 'var(--text-primary)' }}>{safeFixed(roleMatchScore, 0)}%</span>
                  </div>
                </div>
              )}
            </div>
          </div>



          {/* Target Role Banner with source badge + optional role edit */}
          {(resultTargetRole || resultRoleUnclear) && (() => {
            const badge = getSourceBadge(resultRoleSource);
            return (
              <div style={{
                marginBottom: '16px', padding: '14px 16px',
                background: 'var(--bg-surface-secondary)',
                border: `1px solid ${resultRoleUnclear ? 'rgba(245,158,11,0.3)' : 'var(--border-light)'}`,
                borderRadius: '10px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <Briefcase size={15} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                    <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      {resultTargetRole || 'Target role unclear'}
                    </span>
                    <span style={{
                      fontSize: '11px', fontWeight: '700', padding: '2px 8px',
                      borderRadius: '10px', background: badge.bg, color: badge.color
                    }}>
                      {badge.label}
                    </span>
                    {resultRoleUnclear && (
                      <span style={{ fontSize: '11.5px', color: 'var(--warning, #f59e0b)', fontStyle: 'italic' }}>
                        — Select a role for a more accurate score
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setShowRoleEdit(v => !v)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '5px',
                      background: 'transparent', border: '1px solid var(--border-light)',
                      color: 'var(--text-secondary)', borderRadius: '6px', padding: '4px 10px',
                      fontSize: '12px', fontWeight: '600', cursor: 'pointer'
                    }}
                  >
                    <Edit3 size={12} />
                    Change Role
                  </button>
                </div>

                {showRoleEdit && (
                  <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="e.g. Machine Learning Engineer"
                      value={roleOverride}
                      onChange={e => setRoleOverride(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && roleOverride.trim()) handleReanalyze(roleOverride.trim()); }}
                      className="form-input"
                      style={{ flex: 1, minWidth: '200px', padding: '7px 12px', fontSize: '13px' }}
                    />
                    <button
                      onClick={() => handleReanalyze(roleOverride.trim())}
                      disabled={!roleOverride.trim() || loading}
                      className="btn-primary"
                      style={{ padding: '7px 14px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '5px' }}
                    >
                      <RefreshCw size={13} />
                      Re-analyze
                    </button>
                    <button
                      onClick={() => setShowRoleEdit(false)}
                      className="btn-secondary"
                      style={{ padding: '7px 10px', fontSize: '13px' }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Candidate Profile (from uploaded resume) */}
          {(() => {
            const ci = atsResult?.candidate_info || {};
            // Use the backend-resolved target_role directly (priority already handled server-side)
            const targetRoleDisplay = resultTargetRole || 'Not provided';
            const hasTargetRole = Boolean(resultTargetRole);

            const fields = [
              { label: 'Name',             value: ci.name            },
              { label: 'Email',            value: ci.email           },
              { label: 'Phone',            value: ci.phone           },
              { label: 'Degree',           value: ci.degree          },
              { label: 'College / School', value: ci.college         },
              { label: 'Graduation Year',  value: ci.graduation_year },
              { label: 'Target Role',      value: targetRoleDisplay, isRoleField: true, hasValue: hasTargetRole },
              { label: 'Location',         value: ci.location        },
            ];

            const anyFound = fields.some(f => f.isRoleField ? f.hasValue : Boolean(f.value));

            return (
              <div style={{ marginBottom: '16px', padding: '16px', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-light)', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                  <User size={15} style={{ color: 'var(--primary)' }} />
                  <span style={{ fontSize: '13px', fontWeight: '800', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                    Candidate Profile
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '500', marginLeft: '4px' }}>
                    · From uploaded resume
                  </span>
                </div>
                {anyFound ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
                    {fields.map(({ label, value, isRoleField, hasValue }) => {
                      const isPresent = isRoleField ? hasValue : Boolean(value);
                      const displayVal = isRoleField ? value : (value || 'Not found');
                      return (
                        <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                            {label}
                          </span>
                          <span style={{
                            fontSize: '13px',
                            fontWeight: '600',
                            color: isPresent ? 'var(--text-primary)' : 'var(--text-muted)',
                            fontStyle: isPresent ? 'normal' : 'italic'
                          }}>
                            {displayVal}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Candidate details could not be extracted from this resume.
                  </span>
                )}
              </div>
            );
          })()}


          {/* Skills Found */}
          {(() => {
            const matchedSkills = parseSkillsList(atsResult.matched_skills);
            return matchedSkills.length > 0 ? (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--success, #10b981)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={15} />
                  <span>Skills Found ({matchedSkills.length})</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {matchedSkills.map((skill) => (
                    <span
                      key={skill}
                      style={{
                        background: 'var(--success-light, rgba(16, 185, 129, 0.1))',
                        color: 'var(--success, #10b981)',
                        border: '1px solid var(--success-border, rgba(16, 185, 129, 0.3))',
                        padding: '5px 12px',
                        borderRadius: '16px',
                        fontSize: '12.5px',
                        fontWeight: '700'
                      }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : null;
          })()}

          {/* Missing Skills (only when a comparison was possible) */}
          {!isResumeOnlyMode && (() => {
            const missingSkills = parseSkillsList(atsResult.missing_skills);
            return (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--warning, #f59e0b)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <XCircle size={15} />
                  <span>Missing Skills ({missingSkills.length})</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {missingSkills.length > 0 ? (
                    missingSkills.map((skill) => (
                      <span
                        key={skill}
                        style={{
                          background: 'var(--warning-light, rgba(245, 158, 11, 0.1))',
                          color: 'var(--warning, #f59e0b)',
                          border: '1px solid var(--warning-border, rgba(245, 158, 11, 0.3))',
                          padding: '5px 12px',
                          borderRadius: '16px',
                          fontSize: '12.5px',
                          fontWeight: '700'
                        }}
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '13px', color: 'var(--success, #10b981)', fontWeight: '700' }}>
                      All key skills from the job description are present in your resume.
                    </span>
                  )}
                </div>
              </div>
            );
          })()}


          {/* Footer */}
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setAtsResult(null)}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 18px' }}
            >
              <RefreshCw size={15} />
              <span>Analyze Again</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
