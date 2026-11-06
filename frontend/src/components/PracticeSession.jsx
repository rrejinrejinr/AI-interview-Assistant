import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Send,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  LogOut
} from 'lucide-react';
import { submitPracticeAnswerApi, completePracticeApi, exitPracticeApi } from '../services/api';

export default function PracticeSession({ session, onPracticeComplete, onExitPractice }) {
  const questions = session.questions || [];
  const totalQuestions = Number(session.question_count) || questions.length || 0;
  const isFundamentalOrResume = session.question_source === 'fundamental_concepts' || session.question_source === 'resume_based';

  // Helper to determine if an evaluation is correct
  const checkIsCorrect = (ansData, answerText) => {
    if (!ansData) return false;
    if (ansData.is_correct !== undefined && ansData.is_correct !== null) {
      return Boolean(ansData.is_correct);
    }
    if (ansData.result_status === 'Correct') return true;
    if (ansData.result_status === 'Incorrect') return false;
    if (ansData.marks_awarded !== undefined && ansData.marks_awarded > 0) return true;
    if (typeof ansData.combined_score === 'number') {
      return ansData.combined_score >= 50;
    }
    if (ansData.feedback && typeof ansData.feedback === 'string') {
      if (ansData.feedback.trim().toLowerCase().startsWith('correct')) return true;
      if (ansData.feedback.trim().toLowerCase().startsWith('incorrect')) return false;
    }
    if (ansData.correct_option && answerText) {
      return answerText.trim().toUpperCase().startsWith(ansData.correct_option.trim().toUpperCase());
    }
    return false;
  };

  // Determine initial question index (if resuming, jump to first unanswered question)
  const initialIndex = () => {
    const firstUnanswered = questions.findIndex((q) => !q.answered);
    return firstUnanswered >= 0 ? firstUnanswered : 0;
  };

  const [currentIndex, setCurrentIndex] = useState(initialIndex);

  // Track evaluations per question ID so stats are accurate as session progresses and when answers are updated
  const [evaluationsMap, setEvaluationsMap] = useState(() => {
    const map = {};
    questions.forEach((q) => {
      if (q.answered && q.answer_details) {
        map[q.id] = {
          ...q.answer_details,
          is_correct: checkIsCorrect(q.answer_details, q.answer_details.user_answer)
        };
      }
    });
    return map;
  });

  const [userAnswer, setUserAnswer] = useState(() => {
    const initIdx = initialIndex();
    const firstQ = questions[initIdx];
    return firstQ?.answered && firstQ?.answer_details?.user_answer ? firstQ.answer_details.user_answer : '';
  });

  const [evaluation, setEvaluation] = useState(() => {
    const initIdx = initialIndex();
    const firstQ = questions[initIdx];
    return firstQ?.answered && firstQ?.answer_details ? firstQ.answer_details : null;
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showExitModal, setShowExitModal] = useState(false);
  const [exiting, setExiting] = useState(false);

  // Speech-to-text state
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef(null);
  const baseTextRef = useRef('');

  const currentQuestion = questions[currentIndex] || {};
  const isLastQuestion = currentIndex >= totalQuestions - 1;

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = 0; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        const base = baseTextRef.current ? baseTextRef.current.trim() + ' ' : '';
        const full = (base + finalTranscript + interimTranscript).trim();
        setUserAnswer(full);
      };

      recognition.onerror = (e) => {
        console.warn('Speech Recognition Error:', e.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.warn('Speech init failed:', err);
      setSpeechSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    };
  }, []);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Voice input is not supported in this browser. Please type your answer.');
      return;
    }

    if (isRecording) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
      baseTextRef.current = userAnswer.trim();
    } else {
      try {
        baseTextRef.current = userAnswer.trim();
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
      }
    }
  };

  const handleSubmitAnswer = async (e) => {
    if (e) e.preventDefault();
    if (!userAnswer.trim() || loading || !currentQuestion) return;

    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
    }

    setLoading(true);
    setError(null);

    try {
      const res = await submitPracticeAnswerApi(
        session.session_id,
        currentQuestion.id,
        userAnswer.trim()
      );
      const isCorrect = checkIsCorrect(res, userAnswer.trim());
      const maxMarks = res.max_marks ?? currentQuestion.max_marks ?? 2;
      const marksAwarded = res.marks_awarded !== undefined ? res.marks_awarded : (isCorrect ? maxMarks : 0);

      const evaluatedDetails = {
        ...res,
        user_answer: userAnswer.trim(),
        is_correct: isCorrect,
        marks_awarded: marksAwarded,
        max_marks: maxMarks,
        result_status: isCorrect ? 'Correct' : 'Incorrect'
      };

      setEvaluation(evaluatedDetails);
      currentQuestion.answered = true;
      currentQuestion.answer_details = evaluatedDetails;

      setEvaluationsMap((prev) => ({
        ...prev,
        [currentQuestion.id]: evaluatedDetails
      }));
    } catch (err) {
      console.error('Practice submit answer error:', err);
      setError(err.response?.data?.detail || 'Failed to evaluate practice answer.');
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = () => {
    if (isLastQuestion) {
      handleFinishPractice();
      return;
    }
    const nextIdx = currentIndex + 1;
    setCurrentIndex(nextIdx);
    const nextQ = questions[nextIdx];
    const existing = nextQ ? (evaluationsMap[nextQ.id] || (nextQ.answered ? nextQ.answer_details : null)) : null;
    if (existing) {
      setEvaluation(existing);
      setUserAnswer(existing.user_answer || '');
    } else {
      setEvaluation(null);
      setUserAnswer('');
    }
    baseTextRef.current = '';
    setError(null);
  };

  const handleFinishPractice = async () => {
    setLoading(true);
    setError(null);
    try {
      const report = await completePracticeApi(session.session_id);
      if (onPracticeComplete) {
        onPracticeComplete(report);
      }
    } catch (err) {
      console.error('Complete practice error:', err);
      setError(err.response?.data?.detail || 'Failed to complete practice session.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmExit = async () => {
    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
    }

    setExiting(true);
    try {
      await exitPracticeApi(session.session_id);
    } catch (err) {
      console.error('Exit Practice API Error:', err);
    } finally {
      setExiting(false);
      setShowExitModal(false);
      if (onExitPractice) {
        onExitPractice();
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '850px', margin: '0 auto' }}>
      {/* Top Action Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setShowExitModal(true)}
          className="btn-secondary"
          style={{
            padding: '8px 14px',
            fontSize: '12.5px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--danger)',
            borderColor: 'var(--border-light)'
          }}
        >
          <LogOut size={14} />
          <span>Exit Practice</span>
        </button>
      </div>

      {/* Main Question & Answer Card */}
      <div className="ai-card">
        {/* Question Title */}
        <div style={{
          background: 'var(--bg-surface-secondary)',
          border: '1px solid var(--border-light)',
          borderRadius: '12px',
          padding: '18px 20px',
          marginBottom: '20px'
        }}>
          <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Question #{currentIndex + 1} • {currentQuestion?.category || 'Technical Concept'}
          </span>
          <h3 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '6px', lineHeight: '1.45' }}>
            {currentQuestion?.question_text}
          </h3>
        </div>

        {/* If Question has 4 Options (Aptitude MCQ) */}
        {currentQuestion.options && Array.isArray(currentQuestion.options) && currentQuestion.options.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
            <label className="form-label" style={{ marginBottom: '4px' }}>Select the Correct Option *</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
              {currentQuestion.options.map((opt, idx) => {
                const optLetter = opt.trim().charAt(0).toUpperCase();
                const isSelected = userAnswer.trim().toUpperCase().startsWith(optLetter) || userAnswer.trim() === opt.trim();
                const isEvaluated = Boolean(evaluation);
                const isCorrectOpt = evaluation && (
                  evaluation.correct_option === optLetter || 
                  (evaluation.feedback && evaluation.feedback.includes(`Option ${optLetter}`))
                );

                let cardBg = 'var(--bg-surface)';
                let cardBorder = 'var(--border-light)';
                let cardColor = 'var(--text-primary)';

                if (isSelected && !isEvaluated) {
                  cardBg = 'var(--primary-light, rgba(59, 130, 246, 0.08))';
                  cardBorder = 'var(--primary, #3b82f6)';
                } else if (isEvaluated) {
                  if (isCorrectOpt) {
                    cardBg = 'var(--success-light, rgba(16, 185, 129, 0.12))';
                    cardBorder = 'var(--success, #10b981)';
                  } else if (isSelected && !isCorrectOpt) {
                    cardBg = 'var(--danger-light, rgba(239, 68, 68, 0.12))';
                    cardBorder = 'var(--danger, #ef4444)';
                  }
                }

                return (
                  <div
                    key={idx}
                    onClick={() => {
                      if (!loading) {
                        setUserAnswer(opt);
                      }
                    }}
                    style={{
                      background: cardBg,
                      border: `1.5px solid ${cardBorder}`,
                      borderRadius: '10px',
                      padding: '14px 16px',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? 'var(--shadow-sm)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '50%',
                        border: `1.5px solid ${isSelected ? (isEvaluated ? (isCorrectOpt ? 'var(--success)' : 'var(--danger)') : 'var(--primary)') : 'var(--border-light)'}`,
                        background: isSelected ? (isEvaluated ? (isCorrectOpt ? 'var(--success)' : 'var(--danger)') : 'var(--primary)') : 'transparent',
                        color: isSelected ? 'white' : 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '11px',
                        fontWeight: '800',
                        flexShrink: 0
                      }}>
                        {optLetter}
                      </div>
                      <span style={{ fontSize: '13.5px', fontWeight: isSelected ? '700' : '500', color: cardColor }}>
                        {opt.includes('.') ? opt.substring(opt.indexOf('.') + 1).trim() : opt}
                      </span>
                    </div>

                    {isEvaluated && isCorrectOpt && (
                      <span className="badge badge-success" style={{ fontSize: '11px', fontWeight: '800' }}>
                        Correct
                      </span>
                    )}
                    {isEvaluated && isSelected && !isCorrectOpt && (
                      <span className="badge badge-danger" style={{ fontSize: '11px', fontWeight: '800' }}>
                        Your Choice
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Action Row for MCQs */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginTop: '12px' }}>
              <button
                type="button"
                onClick={handleSubmitAnswer}
                disabled={!userAnswer.trim() || loading}
                className="btn-primary"
                style={{ padding: '10px 22px', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Send size={14} />
                <span>{loading ? 'Evaluating...' : evaluation ? 'Update Selection' : 'Submit Option'}</span>
              </button>

              {evaluation && (
                <button
                  type="button"
                  onClick={handleNextQuestion}
                  className="btn-primary"
                  style={{
                    background: 'var(--success)',
                    borderColor: 'var(--success)',
                    padding: '10px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <span>{isLastQuestion ? 'Finish Practice Session' : 'Next Question'}</span>
                  <ArrowRight size={15} />
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Standard / Coding Answer Input Area */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label" style={{ margin: 0 }}>
                {currentQuestion.problem_type === 'coding' ? 'Your Code Implementation / Solution' : 'Your Answer'}
              </label>
              {currentQuestion.problem_type !== 'coding' && (
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={isRecording ? 'btn-danger' : 'btn-secondary'}
                  style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    borderRadius: '8px'
                  }}
                >
                  {isRecording ? <MicOff size={14} /> : <Mic size={14} />}
                  <span>{isRecording ? 'Stop Speaking' : 'Start Speaking'}</span>
                </button>
              )}
            </div>

            <textarea
              rows={currentQuestion.problem_type === 'coding' ? 8 : 4}
              placeholder={
                currentQuestion.problem_type === 'coding'
                  ? "// Type your code solution here...\ndef solution():\n    pass"
                  : "Type your response here, or click 'Start Speaking' to dictate using your microphone..."
              }
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              disabled={loading}
              className="form-textarea"
              style={{
                fontSize: currentQuestion.problem_type === 'coding' ? '13px' : '13.5px',
                lineHeight: '1.5',
                fontFamily: currentQuestion.problem_type === 'coding' ? 'Consolas, Monaco, "Courier New", monospace' : 'inherit',
                background: currentQuestion.problem_type === 'coding' ? 'var(--bg-surface-secondary)' : 'var(--bg-surface)'
              }}
            />

            {/* Action Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={handleSubmitAnswer}
                disabled={!userAnswer.trim() || loading}
                className="btn-primary"
                style={{ padding: '10px 22px', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Send size={14} />
                <span>{loading ? 'Evaluating...' : evaluation ? 'Update & Re-evaluate' : 'Submit Answer'}</span>
              </button>

              {evaluation && (
                <button
                  type="button"
                  onClick={handleNextQuestion}
                  className="btn-primary"
                  style={{
                    background: 'var(--success)',
                    borderColor: 'var(--success)',
                    padding: '10px 22px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <span>{isLastQuestion ? 'Finish Practice Session' : 'Next Question'}</span>
                  <ArrowRight size={15} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Real-time Evaluation Card */}
        {evaluation && (() => {
          const isCorrect = checkIsCorrect(evaluation, userAnswer);
          const maxMarks = evaluation.max_marks ?? currentQuestion.max_marks ?? 2;
          const marksAwarded = evaluation.marks_awarded !== undefined ? evaluation.marks_awarded : (isCorrect ? maxMarks : 0);

          return (
            <div style={{
              marginTop: '22px',
              padding: '16px 18px',
              borderRadius: '12px',
              background: 'var(--bg-surface-secondary)',
              border: isFundamentalOrResume
                ? (isCorrect ? '1.5px solid var(--success, #10b981)' : '1.5px solid var(--danger, #ef4444)')
                : '1.5px solid var(--border-light)'
            }}>
              {isFundamentalOrResume ? (
                <div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '10px',
                    flexWrap: 'wrap',
                    gap: '10px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isCorrect ? (
                        <CheckCircle2 size={18} color="var(--success)" />
                      ) : (
                        <AlertCircle size={18} color="var(--danger)" />
                      )}
                      <span style={{
                        fontWeight: '800',
                        fontSize: '14px',
                        color: isCorrect ? 'var(--success)' : 'var(--danger)'
                      }}>
                        {isCorrect ? 'Correct Answer' : 'Incorrect Answer'}
                      </span>
                    </div>

                    <div style={{
                      padding: '4px 12px',
                      borderRadius: '8px',
                      background: isCorrect
                        ? 'var(--success-light, rgba(16, 185, 129, 0.12))'
                        : 'var(--danger-light, rgba(239, 68, 68, 0.12))',
                      border: `1px solid ${isCorrect ? 'var(--success)' : 'var(--danger)'}`,
                      color: isCorrect ? 'var(--success)' : 'var(--danger)',
                      fontWeight: '800',
                      fontSize: '13px'
                    }}>
                      Marks Awarded: {marksAwarded} / {maxMarks}
                    </div>
                  </div>

                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                    <strong>Feedback:</strong> {evaluation.feedback}
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <CheckCircle2 size={18} color="var(--success)" />
                    <span style={{ fontWeight: '800', fontSize: '13.5px' }}>Answer Evaluated</span>
                  </div>

                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                    <strong>Feedback:</strong> {evaluation.feedback}
                  </div>
                </div>
              )}
            </div>
          );
        })()}

        {error && (
          <div className="alert-error" style={{ marginTop: '16px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* EXIT CONFIRMATION MODAL */}
      {showExitModal && (
        <div
          className="ai-modal-backdrop"
          onClick={() => setShowExitModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(15, 23, 42, 0.72)',
            backdropFilter: 'blur(5px)',
            WebkitBackdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 99999,
            padding: '16px',
            boxSizing: 'border-box'
          }}
        >
          <div
            className="ai-modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--bg-surface, #ffffff)',
              color: 'var(--text-primary)',
              borderRadius: '16px',
              border: '1px solid var(--border-light)',
              padding: '30px 24px',
              width: '100%',
              maxWidth: '460px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
              margin: 'auto',
              boxSizing: 'border-box'
            }}
          >
            <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: '52px',
                height: '52px',
                borderRadius: '50%',
                background: 'var(--primary-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '14px'
              }}>
                <LogOut size={26} className="text-primary" />
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '8px', color: 'var(--text-primary)' }}>
                Exit Practice Session?
              </h3>

              <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: '0 0 24px', maxWidth: '380px' }}>
                Your completed answers and progress will be saved. You can resume this session anytime from your History records.
              </p>

              <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={() => setShowExitModal(false)}
                  className="btn-secondary"
                  style={{ flex: 1, padding: '11px', fontWeight: '700', fontSize: '13.5px' }}
                >
                  Continue Practice
                </button>
                <button
                  type="button"
                  onClick={handleConfirmExit}
                  disabled={exiting}
                  className="btn-danger"
                  style={{ flex: 1, padding: '11px', fontWeight: '700', fontSize: '13.5px' }}
                >
                  {exiting ? 'Saving...' : 'Exit Practice'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
