import React, { useState, useEffect } from 'react';
import {
  Compass,
  Target,
  Map,
  FileText,
  AlertCircle,
  RotateCcw,
  Key,
  TrendingUp,
  Edit3,
  ArrowLeft,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import {
  analyzeRecommendationsApi,
  analyzeResumeImprovementsApi,
  getActiveResumeDetailsApi,
  getResumeDetailsApi
} from '../services/api';

const SUBTABS = [
  { id: 'gaps', label: 'Skill Gaps', icon: Target },
  { id: 'roadmap', label: 'Learning Roadmap', icon: Map },
  { id: 'resume', label: 'Resume Improvements', icon: FileText }
];

export default function Recommendations({ resumes = [], activeResumeId, onNavigateToUpload, onBack }) {
  const [selectedResumeId, setSelectedResumeId] = useState(
    activeResumeId ? String(activeResumeId) : ''
  );
  const [resumeProfile, setResumeProfile] = useState(null);
  const [loadingResume, setLoadingResume] = useState(Boolean(activeResumeId));
  const [activeSubtab, setActiveSubtab] = useState('gaps');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [gapData, setGapData] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [resumeAdvice, setResumeAdvice] = useState(null);

  // Sync selectedResumeId strictly with activeResumeId
  useEffect(() => {
    if (activeResumeId) {
      setSelectedResumeId(String(activeResumeId));
    } else {
      setSelectedResumeId('');
      setResumeProfile(null);
      setGapData(null);
      setRoadmapData(null);
      setResumeAdvice(null);
      setLoadingResume(false);
    }
  }, [activeResumeId]);

  // Reset analysis when resume ID changes to avoid showing stale data
  useEffect(() => {
    setGapData(null);
    setRoadmapData(null);
    setResumeAdvice(null);
  }, [selectedResumeId]);

  // Auto-fetch active resume on mount / when selectedResumeId changes
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
      .catch(() => {
        if (isMounted) setResumeProfile(null);
      })
      .finally(() => {
        if (isMounted) setLoadingResume(false);
      });

    return () => { isMounted = false; };
  }, [selectedResumeId]);

  /**
   * Safely normalizes arbitrary priority formats (string, object, number, array, JSON string)
   * into a canonical 'High', 'Medium', or 'Low' string. Never throws or crashes React.
   */
  const normalizePriority = (priority) => {
    if (priority === null || priority === undefined) return 'Medium';

    if (typeof priority === 'string') {
      const trimmed = priority.trim();
      if (!trimmed) return 'Medium';
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        try {
          return normalizePriority(JSON.parse(trimmed));
        } catch {
          // not JSON, fallback to string check
        }
      }
      const s = trimmed.toLowerCase();
      if (s.includes('high') || s.includes('urgent') || s.includes('critical') || s === 'p1') {
        return 'High';
      }
      if (s.includes('low') || s === 'p3' || s.includes('minor')) {
        return 'Low';
      }
      return 'Medium';
    }

    if (typeof priority === 'object') {
      if (Array.isArray(priority)) {
        return priority.length > 0 ? normalizePriority(priority[0]) : 'Medium';
      }
      const candidateKeys = ['level', 'priority', 'value', 'urgency', 'name', 'text', 'status', 'val', 'label'];
      for (const key of candidateKeys) {
        if (priority[key] !== undefined && priority[key] !== null) {
          const res = normalizePriority(priority[key]);
          if (res) return res;
        }
      }
      for (const val of Object.values(priority)) {
        if (typeof val === 'string' || typeof val === 'number') {
          return normalizePriority(val);
        }
      }
      return 'Medium';
    }

    if (typeof priority === 'number') {
      if (priority === 1) return 'High';
      if (priority === 2) return 'Medium';
      if (priority === 3) return 'Low';
      return 'Medium';
    }

    return 'Medium';
  };

  const priorityBadge = (priority) => {
    const p = normalizePriority(priority);
    if (p === 'High') return <span className="badge-high">High Priority</span>;
    if (p === 'Medium') return <span className="badge-medium">Medium Priority</span>;
    return <span className="badge-low">Low Priority</span>;
  };

  const runFullAnalysis = async (rId) => {
    const effectiveId = rId || resumeProfile?.id;
    if (!effectiveId) return;
    setLoading(true);
    setError(null);
    try {
      const resId = parseInt(effectiveId, 10);
      const [gaps, resumeTips] = await Promise.all([
        analyzeRecommendationsApi(resId),
        analyzeResumeImprovementsApi(resId)
      ]);

      // Normalize skill gaps safely so rendering never encounters raw objects
      const rawGaps = Array.isArray(gaps?.skill_gaps)
        ? gaps.skill_gaps
        : (Array.isArray(gaps?.gaps) ? gaps.gaps : []);

      const sanitizedGaps = rawGaps.map((gap, idx) => {
        const skill = typeof gap?.skill === 'object'
          ? (gap.skill?.name || gap.skill?.skill || JSON.stringify(gap.skill))
          : (gap?.skill || `Skill Gap #${idx + 1}`);
        const p = normalizePriority(gap?.priority);
        const why = typeof gap?.why_it_matters === 'object'
          ? (gap.why_it_matters?.reason || gap.why_it_matters?.text || JSON.stringify(gap.why_it_matters))
          : (gap?.why_it_matters || 'Important for target role preparation.');
        const rawTopics = gap?.topics_to_learn || gap?.topics || [];
        const topics = Array.isArray(rawTopics)
          ? rawTopics.map(t => typeof t === 'object' ? (t?.name || t?.title || JSON.stringify(t)) : String(t))
          : (typeof rawTopics === 'string' ? rawTopics.split(',').map(s => s.trim()) : []);
        const relevance = typeof gap?.interview_relevance === 'object'
          ? (gap.interview_relevance?.text || JSON.stringify(gap.interview_relevance))
          : gap?.interview_relevance;

        return {
          ...gap,
          skill: String(skill),
          priority: p,
          why_it_matters: String(why),
          topics_to_learn: topics,
          interview_relevance: relevance ? String(relevance) : null
        };
      });

      // Normalize roadmap steps safely
      const rawRoadmap = Array.isArray(gaps?.learning_roadmap)
        ? gaps.learning_roadmap
        : (Array.isArray(gaps?.roadmap) ? gaps.roadmap : []);

      const sanitizedRoadmap = rawRoadmap.map((step, idx) => {
        const stepNum = step?.step_number || idx + 1;
        const skill = typeof step?.skill === 'object'
          ? (step.skill?.name || JSON.stringify(step.skill))
          : (step?.skill || `Milestone ${idx + 1}`);
        const p = normalizePriority(step?.priority);
        const timeframe = typeof step?.timeframe === 'object'
          ? (step.timeframe?.duration || JSON.stringify(step.timeframe))
          : (step?.timeframe || `Weeks ${idx * 2 + 1}-${idx * 2 + 2}`);
        const reason = typeof step?.reason === 'object'
          ? (step.reason?.text || JSON.stringify(step.reason))
          : (step?.reason || 'Build critical core competency.');
        const rawMilestones = step?.learning_milestones || step?.milestones || [];
        const milestones = Array.isArray(rawMilestones)
          ? rawMilestones.map(m => typeof m === 'object' ? (m?.title || m?.milestone || JSON.stringify(m)) : String(m))
          : (typeof rawMilestones === 'string' ? rawMilestones.split(',').map(s => s.trim()) : []);

        return {
          ...step,
          step_number: stepNum,
          skill: String(skill),
          priority: p,
          timeframe: String(timeframe),
          reason: String(reason),
          learning_milestones: milestones
        };
      });

      setGapData({
        ...gaps,
        skill_gaps: sanitizedGaps,
        gap_summary: typeof gaps?.gap_summary === 'string'
          ? gaps.gap_summary
          : (typeof gaps?.summary === 'string' ? gaps.summary : 'Prioritized skill gap analysis based on your active resume.')
      });
      setRoadmapData(sanitizedRoadmap);
      setResumeAdvice(resumeTips || {});
    } catch (err) {
      console.error('Recommendations Error:', err);
      const extractErrorMessage = (error) => {
        const detail = error?.response?.data?.detail;
        if (!detail) {
          return error?.response?.data?.message || error?.message || 'Failed to generate career recommendations. Please verify your connection and try again.';
        }
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
          return detail.map(d => (typeof d?.msg === 'string' ? d.msg : JSON.stringify(d))).join('; ');
        }
        if (typeof detail === 'object') {
          return detail.msg || detail.message || JSON.stringify(detail);
        }
        return String(detail);
      };
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Auto-run analysis when resume is resolved
  useEffect(() => {
    if (selectedResumeId && !loadingResume) {
      runFullAnalysis(selectedResumeId);
    }
  }, [selectedResumeId, loadingResume]);

  const activeResumeObj =
    resumes.find((r) => String(r.id) === String(selectedResumeId)) || resumeProfile;

  // --- Loading state while fetching active resume ---
  if (loadingResume) {
    return (
      <div className="ai-card">
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '14px', fontWeight: '600' }}>Loading your active resume...</div>
        </div>
      </div>
    );
  }

  // --- No resume state ---
  if (!selectedResumeId && !resumeProfile) {
    return (
      <div className="ai-card">
        <div className="empty-state">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
            <Compass size={40} color="var(--text-muted)" />
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
      {/* Header */}
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
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
              <Compass size={20} className="text-primary" />
              <span>Personalized AI Career Recommendations</span>
            </h3>
            <p className="card-subtitle">
              Personalized skill-gap analysis, step-by-step career roadmaps, and actionable resume
              optimization suggestions.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Read-only active resume pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-light)',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12.5px'
            }}
          >
            <FileText size={14} className="text-primary" />
            <span style={{ color: 'var(--text-secondary)' }}>Active Resume:</span>
            <b style={{ color: 'var(--text-primary)' }}>
              {activeResumeObj?.filename || resumeProfile?.filename || 'Active Resume'}
            </b>
          </div>

          <button
            onClick={() => runFullAnalysis(selectedResumeId || resumeProfile?.id)}
            disabled={loading}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '12.5px' }}
          >
            <RotateCcw size={13} />
            <span>{loading ? 'Analyzing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Target Profile Banner */}
      {gapData && (
        <div
          style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            color: 'white',
            borderRadius: '12px',
            padding: '16px 22px',
            marginBottom: '22px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px'
          }}
        >
          <div>
            <span
              style={{
                fontSize: '11px',
                color: '#94a3b8',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: '700'
              }}
            >
              TARGET ROLE PROFILE
            </span>
            <h4 style={{ margin: '2px 0 0', fontSize: '18px', fontWeight: '800' }}>
              {gapData.target_role}
            </h4>
          </div>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>Current Skills</span>
              <b style={{ fontSize: '14px', color: '#4ade80' }}>
                {gapData.current_skills?.length || 0} detected
              </b>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>Identified Gaps</span>
              <b style={{ fontSize: '14px', color: '#f87171' }}>
                {gapData.missing_skills?.length || 0} skills
              </b>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>
                Intelligence Engine
              </span>
              <span
                style={{
                  fontSize: '11.5px',
                  background: 'rgba(255,255,255,0.15)',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontWeight: '700'
                }}
              >
                {gapData.source?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Subtab Buttons */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--border-light)',
          paddingBottom: '12px',
          marginBottom: '20px',
          flexWrap: 'wrap'
        }}
      >
        {SUBTABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSubtab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubtab(tab.id)}
              style={{
                padding: '9px 18px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '700',
                background: isActive ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                color: isActive ? 'white' : 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '7px',
                transition: 'all 0.15s'
              }}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {error && (
        <div
          className="alert-error"
          style={{
            marginBottom: '18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '10px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
          <button
            onClick={() => runFullAnalysis(selectedResumeId || resumeProfile?.id)}
            className="btn-secondary"
            style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={13} />
            <span>Try Again</span>
          </button>
        </div>
      )}

      {loading && (
        <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          <p style={{ margin: 0, fontSize: '13.5px', fontWeight: '600' }}>
            Generating career benchmarks and resume recommendations...
          </p>
        </div>
      )}

      {/* SUBTAB 1 — SKILL GAPS */}
      {!loading && activeSubtab === 'gaps' && (
        <div>
          <h4 style={{ margin: '0 0 6px', color: 'var(--text-primary)', fontSize: '15px', fontWeight: '800' }}>
            Prioritized Skill Gaps
          </h4>
          <p style={{ margin: '0 0 16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            {gapData?.gap_summary || 'Analyzing industry benchmarks against your resume...'}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(gapData?.skill_gaps || []).map((gap, i) => (
              <div
                key={i}
                style={{
                  border: '1px solid var(--border-light)',
                  borderRadius: '10px',
                  padding: '16px 18px',
                  background: 'var(--bg-card-subtle)'
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}
                >
                  <span style={{ fontSize: '15.5px', fontWeight: '800', color: 'var(--text-primary)' }}>
                    {gap.skill}
                  </span>
                  {priorityBadge(gap.priority)}
                </div>
                <p style={{ margin: '0 0 10px', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  <b>Why it matters:</b> {gap.why_it_matters}
                </p>
                {gap.topics_to_learn && Array.isArray(gap.topics_to_learn) && gap.topics_to_learn.length > 0 && (
                  <div style={{ marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)' }}>
                      Recommended Topics:{' '}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                      {gap.topics_to_learn.join(' • ')}
                    </span>
                  </div>
                )}
                {gap.interview_relevance && (
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--success)',
                      fontStyle: 'italic',
                      marginTop: '4px'
                    }}
                  >
                    Interview Context: {gap.interview_relevance}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUBTAB 2 — LEARNING ROADMAP */}
      {!loading && activeSubtab === 'roadmap' && (
        <div>
          <h4 style={{ margin: '0 0 6px', color: 'var(--text-primary)', fontSize: '15px', fontWeight: '800' }}>
            Step-by-Step Career Learning Roadmap
          </h4>
          <p style={{ margin: '0 0 18px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Structured milestone progression tailored to bridge your target role requirements.
          </p>
          <div
            style={{
              position: 'relative',
              paddingLeft: '24px',
              borderLeft: '3px solid var(--primary)',
              marginLeft: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}
          >
            {(roadmapData || []).map((step, i) => (
              <div
                key={i}
                style={{
                  position: 'relative',
                  background: 'var(--bg-card-subtle)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '12px',
                  padding: '18px 20px'
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    left: '-37px',
                    top: '18px',
                    width: '26px',
                    height: '26px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    fontWeight: '800'
                  }}
                >
                  {step.step_number || i + 1}
                </span>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                    flexWrap: 'wrap',
                    gap: '8px'
                  }}
                >
                  <span style={{ fontSize: '15.5px', fontWeight: '800', color: 'var(--text-primary)' }}>
                    {step.skill}
                  </span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span
                      style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        background: 'var(--bg-surface-secondary)',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        fontWeight: '600'
                      }}
                    >
                      {step.timeframe}
                    </span>
                    {priorityBadge(step.priority)}
                  </div>
                </div>
                <p style={{ margin: '0 0 10px', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {step.reason}
                </p>
                {step.learning_milestones && Array.isArray(step.learning_milestones) && step.learning_milestones.length > 0 && (
                  <div>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)' }}>
                      Key Milestones:
                    </span>
                    <ul
                      style={{
                        margin: '4px 0 0',
                        paddingLeft: '20px',
                        fontSize: '12.5px',
                        color: 'var(--text-secondary)',
                        lineHeight: '1.5'
                      }}
                    >
                      {step.learning_milestones.map((m, mi) => (
                        <li key={mi} style={{ marginBottom: '2px' }}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUBTAB 3 — RESUME IMPROVEMENTS */}
      {!loading && activeSubtab === 'resume' && resumeAdvice && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div
            style={{
              background: 'var(--success-light)',
              border: '1px solid var(--success-border)',
              borderRadius: '10px',
              padding: '16px 18px',
              color: 'var(--success)',
              fontSize: '13.5px',
              lineHeight: '1.5'
            }}
          >
            <b>Executive Summary:</b> {resumeAdvice.summary}
          </div>

          {resumeAdvice.missing_keywords?.length > 0 && (
            <div style={{ border: '1px solid var(--border-light)', borderRadius: '10px', padding: '16px 18px' }}>
              <h5
                style={{
                  margin: '0 0 10px',
                  color: 'var(--text-primary)',
                  fontSize: '14.5px',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Key size={15} className="text-primary" />
                <span>Recommended Industry Keywords</span>
              </h5>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {resumeAdvice.missing_keywords.map((kw, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'var(--primary-light)',
                      color: 'var(--primary)',
                      border: '1px solid var(--primary-border)',
                      padding: '5px 12px',
                      borderRadius: '16px',
                      fontSize: '12px',
                      fontWeight: '700'
                    }}
                  >
                    + {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {resumeAdvice.achievement_suggestions?.length > 0 && (
            <div
              style={{
                border: '1px solid var(--border-light)',
                borderRadius: '10px',
                padding: '16px 18px',
                background: 'var(--bg-card-subtle)'
              }}
            >
              <h5
                style={{
                  margin: '0 0 10px',
                  color: 'var(--text-primary)',
                  fontSize: '14.5px',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <TrendingUp size={15} className="text-primary" />
                <span>Actionable Suggestions to Quantify Impact</span>
              </h5>
              <ul
                style={{
                  margin: 0,
                  paddingLeft: '20px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.6'
                }}
              >
                {resumeAdvice.achievement_suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {resumeAdvice.weak_bullet_points?.length > 0 && (
            <div style={{ border: '1px solid var(--border-light)', borderRadius: '10px', padding: '16px 18px' }}>
              <h5
                style={{
                  margin: '0 0 10px',
                  color: 'var(--text-primary)',
                  fontSize: '14.5px',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Edit3 size={15} className="text-primary" />
                <span>Bullet Phrasing &amp; Strong Action Verbs</span>
              </h5>
              <ul
                style={{
                  margin: 0,
                  paddingLeft: '20px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.6'
                }}
              >
                {resumeAdvice.weak_bullet_points.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
