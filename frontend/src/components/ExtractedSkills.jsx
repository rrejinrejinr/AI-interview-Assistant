import React, { useState, useEffect } from 'react';
import { Layers, FileText, ArrowRight } from 'lucide-react';
import { getResumeDetailsApi, getActiveResumeDetailsApi } from '../services/api';

const CATEGORY_STYLES = {
  'Programming': { bg: 'var(--primary-light)', color: 'var(--primary)', border: 'var(--primary-border)' },
  'Frontend': { bg: 'rgba(249, 115, 22, 0.12)', color: '#f97316', border: 'rgba(249, 115, 22, 0.3)' },
  'Backend': { bg: 'var(--success-light)', color: 'var(--success)', border: 'var(--success-border)' },
  'AI/ML': { bg: 'rgba(124, 58, 237, 0.15)', color: '#7c3aed', border: 'rgba(124, 58, 237, 0.3)' },
  'ML Libraries': { bg: 'var(--warning-light)', color: 'var(--warning)', border: 'var(--warning-border)' },
  'Data': { bg: 'rgba(2, 132, 199, 0.15)', color: '#0284c7', border: 'rgba(2, 132, 199, 0.3)' },
  'Cloud/DevOps': { bg: 'var(--danger-light)', color: 'var(--danger)', border: 'var(--danger-border)' },
  'Databases': { bg: 'var(--bg-surface-secondary)', color: 'var(--text-secondary)', border: 'var(--border-light)' },
  'Tools': { bg: 'rgba(20, 184, 166, 0.12)', color: '#14b8a6', border: 'rgba(20, 184, 166, 0.3)' },
  'Frameworks': { bg: 'var(--success-light)', color: 'var(--success)', border: 'var(--success-border)' }
};


export default function ExtractedSkills({ activeResumeId, resumes = [], onNavigateToUpload }) {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(Boolean(activeResumeId));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!activeResumeId) {
      setProfileData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    getResumeDetailsApi(activeResumeId)
      .then((data) => {
        if (!isMounted) return;
        setProfileData(data);
      })
      .catch((err) => {
        if (!isMounted) return;
        const msg = err.response?.data?.detail;
        if (err.response?.status === 400 || err.response?.status === 404 || msg?.includes('upload your resume')) {
          setProfileData(null);
        } else {
          setError(msg || 'Failed to load resume details.');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [activeResumeId]);

  const totalSkills = Object.values(profileData?.categorized_skills || {}).reduce((acc, l) => acc + l.length, 0);
  const activeResumeObj = resumes.find((r) => String(r.id) === String(activeResumeId || profileData?.id));
  const currentFilename = profileData?.filename || activeResumeObj?.filename;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="ai-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={20} className="text-primary" />
              <span>Extracted Skills</span>
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Technical skills detected and categorized from your active uploaded resume.
            </p>
          </div>

          {/* Read-only active resume badge */}
          {currentFilename && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-light)',
              padding: '6px 14px', borderRadius: '20px', fontSize: '12.5px'
            }}>
              <FileText size={14} className="text-primary" />
              <span style={{ color: 'var(--text-secondary)' }}>Active Resume:</span>
              <b style={{ color: 'var(--text-primary)' }}>{currentFilename}</b>
            </div>
          )}
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '14px', fontWeight: '600' }}>Loading extracted skills...</div>
          </div>
        ) : error ? (
          <div className="alert-error">{error}</div>
        ) : !profileData ? (
          <div className="empty-state">
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
              <FileText size={36} color="var(--text-muted)" />
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
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
                {totalSkills} skill{totalSkills !== 1 ? 's' : ''} extracted from {profileData.filename}
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Grouped by category</span>
            </div>

            {profileData.categorized_skills && Object.keys(profileData.categorized_skills).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(profileData.categorized_skills).map(([category, skills]) => {
                  const style = CATEGORY_STYLES[category] || {
                    bg: 'var(--bg-surface-secondary)',
                    color: 'var(--text-secondary)',
                    border: 'var(--border-light)'
                  };
                  return (
                    <div
                      key={category}
                      style={{ border: `1px solid ${style.border}`, borderRadius: '8px', padding: '10px 14px', background: 'var(--bg-card-subtle)' }}
                    >
                      <div style={{ fontSize: '11px', fontWeight: '800', color: style.color, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                        {category} ({skills.length})
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {skills.map((skill) => (
                          <span
                            key={skill}
                            className="skill-chip"
                            style={{ background: style.bg, color: style.color, border: `1px solid ${style.border}`, fontSize: '12px' }}
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ padding: '16px', background: 'var(--bg-surface-secondary)', borderRadius: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
                No standardized technical skills detected in this resume.
              </div>
            )}

            {profileData.predicted_role && (
              <div style={{ padding: '14px 16px', background: 'var(--bg-surface-secondary)', border: '1px solid var(--border-light)', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                  Predicted Role
                </div>
                <div style={{ fontSize: '15px', fontWeight: '800', color: 'var(--primary)' }}>
                  {profileData.predicted_role}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
