import React from 'react';
import {
  FileText,
  Award,
  Brain,
  Key,
  CheckCircle2,
  TrendingUp,
  RotateCcw
} from 'lucide-react';

const scoreColor = (score) => {
  if (!score && score !== 0) return 'var(--text-muted)';
  if (score >= 75) return 'var(--success)';
  if (score >= 50) return 'var(--warning)';
  return 'var(--danger)';
};

const scoreLabel = (score) => {
  if (!score && score !== 0) return 'N/A';
  if (score >= 80) return 'Excellent Readiness';
  if (score >= 65) return 'Good Alignment';
  if (score >= 50) return 'Fair (Needs Practice)';
  return 'Requires Fundamental Review';
};

export default function InterviewReport({ report, qaDetails, onStartNew }) {
  if (!report) return null;
  const overall = report.overall_score ?? 0;

  return (
    <div className="ai-card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <FileText size={20} className="text-primary" />
            <span>Technical Interview Performance Report</span>
          </h3>
          <p className="card-subtitle">
            Comprehensive evaluation metrics powered by sentence-transformers semantic analysis and keyword coverage.
          </p>
        </div>
        <button onClick={onStartNew} className="btn-primary" style={{ padding: '9px 18px', fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          <RotateCcw size={14} />
          <span>Start New Interview</span>
        </button>
      </div>

      {/* 4 Score Metrics Grid */}
      <div className="metrics-grid" style={{ marginBottom: '22px' }}>
        <div className="metric-card" style={{ border: `2px solid ${scoreColor(overall)}` }}>
          <div className="metric-header">
            <span className="metric-label">Overall Performance</span>
            <span className="metric-icon"><Award size={18} color={scoreColor(overall)} /></span>
          </div>
          <div className="metric-value" style={{ color: scoreColor(overall) }}>
            {overall?.toFixed(0)} <span style={{ fontSize: '16px', color: 'var(--text-muted)' }}>/ 100</span>
          </div>
          <div className="metric-sub" style={{ color: scoreColor(overall), fontWeight: '700' }}>
            {scoreLabel(overall)}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Avg Semantic Match</span>
            <span className="metric-icon"><Brain size={18} color="var(--primary)" /></span>
          </div>
          <div className="metric-value" style={{ color: 'var(--primary)' }}>
            {report.avg_semantic_score ? `${report.avg_semantic_score.toFixed(0)}%` : 'N/A'}
          </div>
          <div className="metric-sub">
            Dense Vector Cosine Similarity
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Avg Keyword Coverage</span>
            <span className="metric-icon"><Key size={18} color="var(--success)" /></span>
          </div>
          <div className="metric-value" style={{ color: 'var(--success)' }}>
            {report.avg_keyword_score ? `${report.avg_keyword_score.toFixed(0)}%` : 'N/A'}
          </div>
          <div className="metric-sub">
            Technical Keyword Match
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Questions Evaluated</span>
            <span className="metric-icon"><FileText size={18} color="var(--text-secondary)" /></span>
          </div>
          <div className="metric-value">
            {report.questions_answered || qaDetails?.length || 0}
          </div>
          <div className="metric-sub">
            Complete Session
          </div>
        </div>
      </div>

      {/* Strengths & Improvement Areas Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--success-light)', border: '1px solid var(--success-border)', padding: '18px 20px', borderRadius: '12px' }}>
          <h4 style={{ margin: '0 0 10px', color: 'var(--success)', fontSize: '14.5px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={16} />
            <span>Highlighted Strengths</span>
          </h4>
          {report.strengths && report.strengths.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--success)', fontSize: '13px', lineHeight: '1.6' }}>
              {report.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: 0, color: 'var(--success)', fontSize: '13px' }}>Continue practicing to develop clear standout strengths.</p>
          )}
        </div>

        <div style={{ background: 'var(--warning-light)', border: '1px solid var(--warning-border)', padding: '18px 20px', borderRadius: '12px' }}>
          <h4 style={{ margin: '0 0 10px', color: 'var(--warning)', fontSize: '14.5px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <TrendingUp size={16} />
            <span>Key Improvement Opportunities</span>
          </h4>
          {report.improvement_areas && report.improvement_areas.length > 0 ? (
            <ul style={{ margin: 0, paddingLeft: '18px', color: 'var(--warning)', fontSize: '13px', lineHeight: '1.6' }}>
              {report.improvement_areas.map((area, i) => (
                <li key={i}>{area}</li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: 0, color: 'var(--warning)', fontSize: '13px' }}>Outstanding performance! No critical knowledge deficiencies found.</p>
          )}
        </div>
      </div>

      {/* Per-Question Breakdown */}
      <div>
        <h4 style={{ color: 'var(--text-primary)', fontSize: '15px', fontWeight: '800', marginBottom: '14px' }}>
          Question-by-Question Breakdown
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {(qaDetails || []).map((qa, idx) => (
            <div
              key={idx}
              style={{
                background: 'var(--bg-card-subtle)',
                border: '1px solid var(--border-light)',
                borderLeft: `4px solid ${scoreColor(qa.combined_score)}`,
                padding: '16px 18px',
                borderRadius: '10px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  Q{idx + 1}: {qa.question}
                </span>
                <span style={{
                  padding: '3px 10px',
                  borderRadius: '12px',
                  background: `${scoreColor(qa.combined_score)}15`,
                  color: scoreColor(qa.combined_score),
                  fontWeight: '800',
                  fontSize: '13px'
                }}>
                  Score: {qa.combined_score?.toFixed(0) ?? 'N/A'}/100
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                <b>Feedback:</b> {qa.feedback?.replace(/ \[Evaluation:.*?\]/, '')}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
