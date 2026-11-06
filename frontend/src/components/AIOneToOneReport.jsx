import React from 'react';
import {
  Award,
  CheckCircle2,
  TrendingUp,
  RotateCcw,
  ArrowLeft,
  MessagesSquare,
  Sparkles,
  Bot,
  User,
  HelpCircle
} from 'lucide-react';

export default function AIOneToOneReport({ report, onStartNew, onReturnToHistory }) {
  if (!report) {
    return (
      <div className="ai-card">
        <div className="empty-state">
          <HelpCircle size={40} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
          <div className="empty-title">No HR Interview Report Available</div>
          <div className="empty-desc">Please complete or select an HR interview session to view performance metrics.</div>
        </div>
      </div>
    );
  }

  const transcript = report.conversation_transcript || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      {/* Report Summary Card */}
      <div className="ai-card">
        <div className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span className="badge badge-primary">HR Interview</span>
              <span className="badge badge-success">Completed</span>
            </div>
            <h3 className="card-title">
              <Sparkles size={22} className="text-primary" />
              <span>HR Interview Evaluation</span>
            </h3>
            <p className="card-subtitle">
              HR readiness assessment for: {report.resume_filename || 'Candidate Resume'} ({report.predicted_role || 'Software Engineer'})
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={onStartNew}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 16px' }}
            >
              <RotateCcw size={15} />
              <span>Start New Interview</span>
            </button>
            {onReturnToHistory && (
              <button
                type="button"
                onClick={onReturnToHistory}
                className="btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 16px' }}
              >
                <ArrowLeft size={15} />
                <span>Return to History</span>
              </button>
            )}
          </div>
        </div>

        {/* Executive Summary Quote */}
        {report.summary && (
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            borderRadius: '10px',
            padding: '14px 18px',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            lineHeight: '1.5',
            marginTop: '8px'
          }}>
            <strong>Evaluator Overview:</strong> {report.summary}
          </div>
        )}

        {/* Top Metric Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginTop: '16px'
        }}>
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '18px',
            borderRadius: '12px'
          }}>
            <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Overall Readiness
            </span>
            <div style={{ fontSize: '28px', fontWeight: '900', color: 'var(--primary)', marginTop: '4px' }}>
              {report.overall_score || 0}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Aggregate HR evaluation
            </div>
          </div>

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '18px',
            borderRadius: '12px'
          }}>
            <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Communication Score
            </span>
            <div style={{ fontSize: '28px', fontWeight: '900', color: 'var(--text-primary)', marginTop: '4px' }}>
              {report.communication_score || 0}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Verbal flow and substantive depth
            </div>
          </div>

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '18px',
            borderRadius: '12px'
          }}>
            <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Response Clarity
            </span>
            <div style={{ fontSize: '28px', fontWeight: '900', color: 'var(--text-primary)', marginTop: '4px' }}>
              {report.response_clarity_score || 0}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              STAR structure & professional framing
            </div>
          </div>
        </div>

        {/* Strengths & Improvements */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '16px',
          marginTop: '20px'
        }}>
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '18px 20px',
            borderRadius: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <CheckCircle2 size={18} color="var(--success)" />
              <span style={{ fontWeight: '800', fontSize: '14px' }}>Candidate Strengths</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              {(report.strengths || []).map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '18px 20px',
            borderRadius: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <TrendingUp size={18} color="var(--warning)" />
              <span style={{ fontWeight: '800', fontSize: '14px' }}>Areas for Growth</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              {(report.improvement_areas || []).map((imp, idx) => (
                <li key={idx}>{imp}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Transcript Review Card */}
      <div className="ai-card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <MessagesSquare size={18} className="text-primary" />
              <span>Full Interview Conversation Transcript</span>
            </h3>
            <p className="card-subtitle">
              Chronological log of questions and candidate responses.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {transcript.map((item, idx) => {
            const isAi = item.speaker === 'ai_interviewer';
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  gap: '12px',
                  alignSelf: isAi ? 'flex-start' : 'flex-end',
                  maxWidth: '85%'
                }}
              >
                {isAi && (
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <Bot size={16} color="#ffffff" />
                  </div>
                )}

                <div style={{
                  background: isAi ? 'var(--bg-surface-secondary)' : 'var(--primary)',
                  color: isAi ? 'var(--text-primary)' : '#ffffff',
                  border: isAi ? '1px solid var(--border-light)' : 'none',
                  padding: '12px 16px',
                  borderRadius: isAi ? '4px 14px 14px 14px' : '14px 4px 14px 14px',
                  fontSize: '13px',
                  lineHeight: '1.45'
                }}>
                  <div style={{
                    fontSize: '10.5px',
                    fontWeight: '700',
                    color: isAi ? 'var(--primary)' : 'rgba(255, 255, 255, 0.8)',
                    marginBottom: '3px'
                  }}>
                    {isAi ? 'AI HR Interviewer' : 'Candidate Response'}
                  </div>
                  <div>{item.text}</div>
                </div>

                {!isAi && (
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--bg-surface-secondary)',
                    border: '1px solid var(--border-light)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <User size={16} color="var(--primary)" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
