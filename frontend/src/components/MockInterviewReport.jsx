import React from 'react';
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  ArrowLeft,
  FileText,
  ShieldCheck,
  HelpCircle
} from 'lucide-react';

export default function MockInterviewReport({ report, onStartNew, onReturnToHistory }) {
  if (!report) {
    return (
      <div className="ai-card">
        <div className="empty-state">
          <HelpCircle size={40} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
          <div className="empty-title">No Mock Interview Report Available</div>
          <div className="empty-desc">Please complete or select a mock interview session to view performance metrics.</div>
        </div>
      </div>
    );
  }

  const isRejected = report.status === 'REJECTED_INTEGRITY_VIOLATION' || report.integrity_status === 'REJECTED';
  const isExited = report.status === 'EXITED_BY_CANDIDATE';
  const qaList = report.questions_and_answers || [];

  const totalQuestions = report.total_questions || report.num_questions || 30;
  const correctCount = report.correct_count !== undefined
    ? report.correct_count
    : qaList.filter(q => q.is_correct || q.result_status === 'Correct' || (q.combined_score && q.combined_score >= 48)).length;

  const scorePercentage = report.percentage !== undefined
    ? report.percentage
    : Math.round((correctCount / (totalQuestions || 30)) * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Rejection Alert Header if session was rejected */}
      {isRejected && (
        <div style={{
          background: '#fef2f2',
          border: '1.5px solid #ef4444',
          borderRadius: '10px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '14px'
        }}>
          <XCircle size={24} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#991b1b', margin: '0 0 4px' }}>
              Interview Terminated — Integrity Requirements Not Satisfied
            </h3>
            <p style={{ fontSize: '13px', color: '#7f1d1d', lineHeight: '1.4', margin: '0 0 6px' }}>
              <strong>Reason:</strong> {report.rejection_reason || 'Face presence was not continuously detected in camera frame.'}
            </p>
            <div style={{ fontSize: '12px', color: '#991b1b' }}>
              Questions Completed: {report.questions_completed || 0} / {totalQuestions} • Status: REJECTED
            </div>
          </div>
        </div>
      )}

      {/* Exited Alert Header if session was exited by candidate */}
      {isExited && (
        <div style={{
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: '10px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <ShieldCheck size={22} className="text-primary" style={{ flexShrink: 0 }} />
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)', margin: '0 0 2px' }}>
              Mock Interview Exited
            </h4>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: 0 }}>
              Session was exited before completion. Answered questions have been recorded.
            </p>
          </div>
        </div>
      )}

      {/* Main Scorecard Header */}
      <div className="ai-card" style={{ padding: '24px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '20px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="badge badge-primary">Mock Interview</span>
              <span className="badge badge-neutral">Difficulty: {report.difficulty || 'Medium'}</span>
              <span className={`badge ${isRejected ? 'badge-danger' : isExited ? 'badge-neutral' : 'badge-success'}`}>
                {isRejected ? 'Rejected' : isExited ? 'Exited' : 'Completed'}
              </span>
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 4px' }}>
              Mock Interview Result
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Resume: {report.resume_filename || 'Candidate Resume'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={onStartNew}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', fontSize: '13px' }}
            >
              <RotateCcw size={15} />
              <span>Start New Mock Interview</span>
            </button>
            {onReturnToHistory && (
              <button
                type="button"
                onClick={onReturnToHistory}
                className="btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', fontSize: '13px' }}
              >
                <ArrowLeft size={15} />
                <span>Return to History</span>
              </button>
            )}
          </div>
        </div>

        {/* Primary Result Banner: Correct X/30 & Score Y% */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: '10px',
          padding: '20px'
        }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Result
            </div>
            <div style={{ fontSize: '26px', fontWeight: '900', color: 'var(--text-primary)', marginTop: '4px' }}>
              Correct: {correctCount} / {totalQuestions}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {correctCount >= 20 ? 'Strong Performance' : correctCount >= 10 ? 'Average Performance' : 'Needs Practice'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Score
            </div>
            <div style={{ fontSize: '26px', fontWeight: '900', color: scorePercentage >= 60 ? 'var(--success)' : 'var(--primary)', marginTop: '4px' }}>
              {scorePercentage}%
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Based on factual and resume consistency evaluation
            </div>
          </div>
        </div>
      </div>

      {/* All 30 Questions Review */}
      <div className="ai-card" style={{ padding: '24px' }}>
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} className="text-primary" />
            <span>Questions & Answers Review ({qaList.length || 30})</span>
          </h3>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: 0 }}>
            Compare your submitted responses against the expected answers.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {qaList.map((item, idx) => {
            const qNum = item.order_index || idx + 1;
            const isCorrect = item.is_correct === true || item.result_status === 'Correct' || (item.combined_score && item.combined_score >= 48);
            const userAns = item.user_answer;
            const expectedAns = item.expected_answer || item.ideal_answer || 'Standard technical solution and architectural best practices.';

            return (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface-secondary)',
                  border: `1px solid ${isCorrect ? 'var(--border-light)' : 'rgba(239, 68, 68, 0.25)'}`,
                  borderRadius: '10px',
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}
              >
                {/* Question Header & Status Badge */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ fontSize: '13.5px', fontWeight: '700', color: 'var(--text-primary)', flex: 1 }}>
                    <span style={{ color: 'var(--primary)', marginRight: '6px' }}>Question {qNum}:</span>
                    {item.question_text}
                  </div>
                  <div>
                    {isCorrect ? (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: 'rgba(34, 197, 94, 0.15)',
                        color: '#16a34a',
                        border: '1px solid rgba(34, 197, 94, 0.3)',
                        borderRadius: '6px',
                        padding: '3px 8px',
                        fontSize: '11.5px',
                        fontWeight: '700'
                      }}>
                        <CheckCircle2 size={13} />
                        <span>Correct</span>
                      </span>
                    ) : (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: 'rgba(239, 68, 68, 0.12)',
                        color: '#dc2626',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        borderRadius: '6px',
                        padding: '3px 8px',
                        fontSize: '11.5px',
                        fontWeight: '700'
                      }}>
                        <XCircle size={13} />
                        <span>Incorrect</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Candidate's Answer */}
                <div style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  fontSize: '12.5px'
                }}>
                  <div style={{ fontWeight: '700', color: 'var(--text-muted)', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase' }}>
                    Your Answer
                  </div>
                  <div style={{ color: userAns ? 'var(--text-primary)' : 'var(--text-muted)', fontStyle: userAns ? 'normal' : 'italic', lineHeight: '1.4' }}>
                    {userAns || 'No answer provided.'}
                  </div>
                </div>

                {/* Expected / Correct Answer */}
                <div style={{
                  background: 'rgba(37, 99, 235, 0.04)',
                  border: '1px solid rgba(37, 99, 235, 0.15)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  fontSize: '12.5px'
                }}>
                  <div style={{ fontWeight: '700', color: 'var(--primary)', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase' }}>
                    Correct / Expected Answer
                  </div>
                  <div style={{ color: 'var(--text-primary)', lineHeight: '1.45' }}>
                    {expectedAns}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
