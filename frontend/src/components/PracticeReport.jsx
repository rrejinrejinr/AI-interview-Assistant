import React from 'react';
import { CheckCircle2, AlertCircle, RotateCcw, FileText } from 'lucide-react';

/**
 * Default passing threshold percentage for Aptitude practice sessions.
 * Configurable via props or report payload (defaults to 50% passing threshold).
 */
const DEFAULT_PASSING_PERCENT = 50;

export default function PracticeReport({ report, onRestart, passThreshold = DEFAULT_PASSING_PERCENT }) {
  if (!report) return null;

  const getScoreColor = (score) => {
    if (score >= 75) return 'var(--success)';
    if (score >= 50) return 'var(--warning)';
    return 'var(--danger)';
  };

  const questionsAndAnswers = report.questions_and_answers || [];
  const totalQuestions = Number(report.question_count) || questionsAndAnswers.length || 0;

  const checkQuestionCorrect = (item) => {
    if (!item) return false;
    if (item.is_correct !== undefined && item.is_correct !== null) {
      return Boolean(item.is_correct);
    }
    if (item.result_status === 'Correct') return true;
    if (item.result_status === 'Incorrect') return false;
    if (typeof item.feedback === 'string') {
      const fb = item.feedback.trim().toLowerCase();
      if (fb.startsWith('correct')) return true;
      if (fb.startsWith('incorrect')) return false;
    }
    if (typeof item.combined_score === 'number') {
      return item.combined_score >= 50;
    }
    return false;
  };

  const isAnswered = (item) => {
    if (!item) return false;
    if (item.answered !== undefined) return Boolean(item.answered);
    if (item.user_answer && item.user_answer.trim() !== '') return true;
    if (item.feedback && item.feedback !== 'Unanswered question.') return true;
    return false;
  };

  const correctCount = report.correct_count !== undefined
    ? Number(report.correct_count)
    : questionsAndAnswers.filter((item) => isAnswered(item) && checkQuestionCorrect(item)).length;

  const wrongCount = report.wrong_count !== undefined
    ? Number(report.wrong_count)
    : questionsAndAnswers.filter((item) => isAnswered(item) && !checkQuestionCorrect(item)).length;

  const isFundamentalOrResume = report.question_source === 'fundamental_concepts' || report.question_source === 'resume_based';
  const totalMarks = report.total_marks || (totalQuestions * 2);
  const earnedMarks = report.earned_marks !== undefined ? Number(report.earned_marks) : (correctCount * 2);

  const bannerTitle = isFundamentalOrResume
    ? (report.question_source === 'fundamental_concepts' ? 'FUNDAMENTAL CONCEPTS PRACTICE EVALUATION REPORT' : 'RESUME-BASED PRACTICE EVALUATION REPORT')
    : (report.question_source === 'problem_solving' ? 'PROBLEM SOLVING PRACTICE EVALUATION REPORT' : 'APTITUDE PRACTICE EVALUATION REPORT');

  // Passing criteria: percentage of correct answers out of total questions
  const userPercentage = totalQuestions > 0 ? (correctCount / totalQuestions) * 100 : 0;
  const effectiveThreshold = Number(report.pass_threshold ?? report.pass_percentage ?? passThreshold);
  const isPass = report.is_passed !== undefined
    ? Boolean(report.is_passed)
    : userPercentage >= effectiveThreshold;

  const motivationalMessage = isPass
    ? "Congratulations! You passed the test. Keep up the great work!"
    : " try your best next time. ";

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Top Banner Report */}
      <div className="ai-card" style={{ border: `2px solid ${isPass ? 'var(--success)' : 'var(--danger)'}` }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: 'white',
          padding: '24px 28px',
          borderRadius: '12px',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '700' }}>
              {bannerTitle}
            </span>
            <h3 style={{ margin: '4px 0 6px', fontSize: '20px', fontWeight: '800' }}>
              {report.practice_type || 'Practice'} Practice ({report.difficulty || 'Medium'})
            </h3>
            <span style={{ fontSize: '13px', color: '#cbd5e1' }}>
              {report.resume_filename && report.resume_filename !== 'General' ? `Target Resume: ${report.resume_filename} • ` : ''}
              {report.total_answered !== undefined ? report.total_answered : (correctCount + wrongCount)} / {totalQuestions} Questions Answered
            </span>
          </div>

          <div style={{
            background: isPass ? 'var(--success)' : 'var(--danger)',
            padding: '12px 28px',
            borderRadius: '16px',
            textAlign: 'center',
            boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
            minWidth: '120px'
          }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', fontWeight: '800', letterSpacing: '0.5px', opacity: 0.9 }}>
              Result Status
            </div>
            <div style={{ fontSize: '32px', fontWeight: '900', lineHeight: 1.1, letterSpacing: '1px' }}>
              {isPass ? 'PASS' : 'FAIL'}
            </div>
          </div>
        </div>

        {/* Results Summary: Key Statistics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(auto-fit, minmax(180px, 1fr))`,
          gap: '14px',
          marginBottom: '20px'
        }}>
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 20px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Correct Answers
            </div>
            <div style={{ fontSize: '24px', fontWeight: '900', color: 'var(--success)' }}>
              {correctCount} / {totalQuestions}
            </div>
          </div>

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 20px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Wrong Answers
            </div>
            <div style={{ fontSize: '24px', fontWeight: '900', color: 'var(--danger)' }}>
              {wrongCount}
            </div>
          </div>

          {isFundamentalOrResume && (
            <div style={{
              background: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-light)',
              padding: '16px 20px',
              borderRadius: '12px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Total Marks
              </div>
              <div style={{ fontSize: '24px', fontWeight: '900', color: 'var(--primary)' }}>
                {earnedMarks} / {totalMarks}
              </div>
            </div>
          )}

          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 20px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
              Total Questions
            </div>
            <div style={{ fontSize: '24px', fontWeight: '900', color: 'var(--text-primary)' }}>
              {totalQuestions}
            </div>
          </div>
        </div>

        {/* Motivational Message */}
        <div style={{
          background: isPass ? 'var(--success-light, rgba(16, 185, 129, 0.1))' : 'var(--danger-light, rgba(239, 68, 68, 0.1))',
          border: `1px solid ${isPass ? 'var(--success-border, var(--success))' : 'var(--danger-border, var(--danger))'}`,
          borderRadius: '10px',
          padding: '12px 18px',
          marginBottom: '22px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {isPass ? <CheckCircle2 size={18} color="var(--success)" /> : <AlertCircle size={18} color="var(--danger)" />}
          <span style={{
            fontSize: '14px',
            fontWeight: '700',
            color: isPass ? 'var(--success)' : 'var(--danger)'
          }}>
            {motivationalMessage}
          </span>
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button onClick={onRestart} className="btn-primary" style={{ padding: '12px 28px' }}>
            <RotateCcw size={16} />
            <span>Start New Practice Session</span>
          </button>
        </div>
      </div>

      {/* Question by Question Breakdown */}
      {questionsAndAnswers.length > 0 && (
        <div className="ai-card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <FileText size={18} className="text-primary" />
                <span>Question-by-Question Evaluation Breakdown</span>
              </h3>
              <p className="card-subtitle">Detailed answers and individual AI evaluations</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {questionsAndAnswers.map((item, idx) => (
              <div
                key={idx}
                style={{
                  border: '1px solid var(--border-light)',
                  borderRadius: '12px',
                  padding: '18px',
                  background: 'var(--bg-card-subtle)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ fontSize: '14.5px', fontWeight: '800', color: 'var(--text-primary)' }}>
                    #{item.order_index} • {item.question_text}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isFundamentalOrResume && (
                      <span style={{
                        padding: '3px 10px',
                        borderRadius: '12px',
                        fontWeight: '800',
                        fontSize: '12px',
                        background: checkQuestionCorrect(item) ? 'var(--success-light, rgba(16, 185, 129, 0.15))' : 'var(--danger-light, rgba(239, 68, 68, 0.15))',
                        color: checkQuestionCorrect(item) ? 'var(--success)' : 'var(--danger)',
                        border: `1px solid ${checkQuestionCorrect(item) ? 'var(--success)' : 'var(--danger)'}`
                      }}>
                        Marks: {item.marks_awarded !== undefined ? item.marks_awarded : (checkQuestionCorrect(item) ? (item.max_marks || 2) : 0)} / {item.max_marks || 2}
                      </span>
                    )}
                    <span style={{
                      padding: '3px 10px',
                      borderRadius: '12px',
                      fontWeight: '800',
                      fontSize: '12.5px',
                      background: getScoreColor(item.combined_score),
                      color: 'white'
                    }}>
                      {item.combined_score?.toFixed(1) || 0}%
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '10px' }}>
                  Category: <b>{item.category || 'General'}</b> • Difficulty: <b>{item.difficulty}</b>
                </div>

                <div style={{ background: 'var(--bg-surface)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-light)', marginBottom: '8px', fontSize: '13px', lineHeight: '1.5' }}>
                  <span style={{ fontWeight: '700', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Your Answer:</span>
                  <div style={{ color: 'var(--text-primary)' }}>{item.user_answer || <span style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>Unanswered</span>}</div>
                </div>

                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  <b>Feedback:</b> {item.feedback}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
