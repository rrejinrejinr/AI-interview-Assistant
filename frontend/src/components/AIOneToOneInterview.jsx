import React, { useState, useEffect, useRef } from 'react';
import {
  MessagesSquare,
  Mic,
  MicOff,
  Send,
  ArrowRight,
  Bot,
  User,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Award,
  Volume2,
  VolumeX,
  RotateCcw,
  RefreshCw,
  Radio
} from 'lucide-react';
import { sendAiInterviewMessageApi, completeAiInterviewApi } from '../services/api';

export default function AIOneToOneInterview({ session, onInterviewComplete, onCancel }) {
  const [transcript, setTranscript] = useState(session.conversation_transcript || []);
  const [candidateMessage, setCandidateMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [ttsSupported, setTtsSupported] = useState(typeof window !== 'undefined' && 'speechSynthesis' in window);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [activeSpeakingText, setActiveSpeakingText] = useState(null);
  const [sending, setSending] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState(null);
  const [failedMessage, setFailedMessage] = useState(null);

  const recognitionRef = useRef(null);
  const chatEndRef = useRef(null);
  const hasSpokenInitialRef = useRef(false);
  const baseTextRef = useRef('');

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, sending]);

  // Determine current HR stage based on candidate turns
  const getInterviewStage = () => {
    if (isComplete) return 'Interview Concluded';
    const candidateTurns = transcript.filter((t) => t.speaker === 'candidate').length;
    if (candidateTurns === 0) return 'Opening & Greeting';
    if (candidateTurns <= 2) return 'Introduction & Background';
    if (candidateTurns <= 4) return 'Project & Technical Experience';
    if (candidateTurns <= 5) return 'Behavioral & Situational';
    return 'Final Thoughts & Wrap-up';
  };

  // -------------------------------------------------------------
  // Text-to-Speech (TTS) Engine: HR Interviewer Speaks Aloud
  // -------------------------------------------------------------
  const speakText = (text) => {
    if (!text || isMuted || typeof window === 'undefined' || !window.speechSynthesis) return;

    try {
      window.speechSynthesis.cancel(); // Stop any currently active speech immediately

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.lang = 'en-US';

      // Pick a natural English voice if available in the candidate's browser
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) =>
          (v.name.includes('Google') ||
            v.name.includes('Natural') ||
            v.name.includes('Samantha') ||
            v.name.includes('Jenny') ||
            v.name.includes('David') ||
            v.name.includes('Guy') ||
            v.lang === 'en-US' ||
            v.lang.startsWith('en')) &&
          !v.name.includes('Zira')
      );
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        setActiveSpeakingText(text);
      };
      utterance.onend = () => {
        setIsSpeaking(false);
        setActiveSpeakingText(null);
      };
      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis event error:', e);
        setIsSpeaking(false);
        setActiveSpeakingText(null);
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn('Failed to speak HR response:', err);
      setIsSpeaking(false);
      setActiveSpeakingText(null);
    }
  };

  // Auto-speak opening HR greeting/question on initial mount
  useEffect(() => {
    if (hasSpokenInitialRef.current) return;
    const initialText =
      session.first_message ||
      (transcript.length > 0 && transcript[0].speaker === 'ai_interviewer' ? transcript[0].text : null);

    if (initialText) {
      hasSpokenInitialRef.current = true;
      // Slight delay to allow audio context & voices to initialize
      const timer = setTimeout(() => {
        speakText(initialText);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [session, transcript]);

  // Voice Controls: Toggle Mute / Unmute
  const toggleMute = () => {
    if (!isMuted) {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
      setActiveSpeakingText(null);
      setIsMuted(true);
    } else {
      setIsMuted(false);
    }
  };

  // Voice Controls: Replay Last HR Interviewer Question
  const replayLastQuestion = () => {
    const aiMessages = transcript.filter((t) => t.speaker === 'ai_interviewer');
    const lastAiText = aiMessages.length > 0 ? aiMessages[aiMessages.length - 1].text : session.first_message;
    if (lastAiText) {
      speakText(lastAiText);
    }
  };

  // -------------------------------------------------------------
  // Speech Recognition (Microphone Voice Input)
  // -------------------------------------------------------------
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
          const itemText = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += itemText + ' ';
          } else {
            interimTranscript += itemText;
          }
        }

        const base = baseTextRef.current ? baseTextRef.current.trim() + ' ' : '';
        const full = (base + finalTranscript + interimTranscript).trim();
        setCandidateMessage(full);
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
      console.warn('Speech recognition init failed:', err);
      setSpeechSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Cleanup on unmount or interview completion
  useEffect(() => {
    if (isComplete) {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsRecording(false);
      setIsSpeaking(false);
    }
  }, [isComplete]);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Voice input is not supported in this browser. Please type your answer into the text box.');
      return;
    }

    if (isRecording) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
      baseTextRef.current = candidateMessage.trim();
    } else {
      try {
        // Stop any active TTS so interviewer speech does not bleed into candidate mic
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel();
          setIsSpeaking(false);
          setActiveSpeakingText(null);
        }
        baseTextRef.current = candidateMessage.trim();
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
    }
  };

  // -------------------------------------------------------------
  // Submission & Retry Logic
  // -------------------------------------------------------------
  const handleSendMessage = async () => {
    const textToSend = candidateMessage.trim() || (failedMessage ? failedMessage.trim() : '');
    if (!textToSend || sending || isComplete) return;

    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsRecording(false);
    }

    const messageText = textToSend;
    setSending(true);
    setError(null);
    setFailedMessage(null);

    try {
      const res = await sendAiInterviewMessageApi(session.session_id, messageText);
      setTranscript(res.conversation_transcript || []);
      setCandidateMessage('');
      baseTextRef.current = '';

      if (res.is_complete) {
        setIsComplete(true);
      }

      // Automatically speak the new HR interviewer response aloud
      if (res.ai_message && !isMuted) {
        speakText(res.ai_message);
      }
    } catch (err) {
      console.error('Send AI Message Error:', err);
      // Preserve candidate text so the answer is never lost
      setFailedMessage(messageText);
      if (!candidateMessage) {
        setCandidateMessage(messageText);
      }
      const errDetail =
        err.response?.data?.detail ||
        'The AI Interviewer was temporarily unavailable. Please click Retry to send your response again.';
      setError(errDetail);
    } finally {
      setSending(false);
    }
  };

  const handleFinishAndEvaluate = async () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }
    setSending(true);
    try {
      const report = await completeAiInterviewApi(session.session_id);
      if (onInterviewComplete) {
        onInterviewComplete(report);
      }
    } catch (err) {
      console.error('Complete AI Interview Error:', err);
      setError('Failed to compile final evaluation report. Please try again.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header bar */}
      <div className="ai-card" style={{ padding: '14px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-primary">HR Interview</span>
              <span className={`badge ${isComplete ? 'badge-success' : 'badge-neutral'}`}>
                {isComplete ? 'Interview Concluded' : 'In Progress'}
              </span>
              {isSpeaking && (
                <span
                  className="badge badge-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', animation: 'pulse 1.5s infinite' }}
                >
                  <Radio size={12} />
                  <span>HR Speaking...</span>
                </span>
              )}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Candidate: <strong>{session.resume_filename || 'Candidate Resume'}</strong> ({session.predicted_role || 'Software Engineer'})
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Audio TTS Controls */}
            {ttsSupported && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <button
                  type="button"
                  onClick={replayLastQuestion}
                  disabled={isSpeaking || isComplete}
                  className="btn-secondary"
                  title="Replay latest HR question aloud"
                  style={{
                    padding: '7px 12px',
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  <RotateCcw size={13} />
                  <span>Replay Voice</span>
                </button>

                <button
                  type="button"
                  onClick={toggleMute}
                  className={isMuted ? 'btn-danger' : 'btn-secondary'}
                  title={isMuted ? 'Unmute HR Voice' : 'Mute HR Voice'}
                  style={{
                    padding: '7px 12px',
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  {isMuted ? <VolumeX size={13} /> : <Volume2 size={13} />}
                  <span>{isMuted ? 'Unmute' : 'Mute'}</span>
                </button>
              </div>
            )}

            {isComplete ? (
              <button
                type="button"
                onClick={handleFinishAndEvaluate}
                disabled={sending}
                className="btn-primary"
                style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Award size={15} />
                <span>{sending ? 'Compiling Report...' : 'View Full Report'}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinishAndEvaluate}
                disabled={sending}
                className="btn-secondary"
                style={{ padding: '8px 14px', fontSize: '12.5px' }}
              >
                Finish Early & Evaluate
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Dialogue stream (Left) + Candidate & Interview Info (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: '16px', alignItems: 'start' }}>
        {/* Left Column: Chat Dialogue & Input */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Dialogue Thread */}
          <div
            className="ai-card"
            style={{
              minHeight: '360px',
              maxHeight: '480px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              padding: '18px'
            }}
          >
            {transcript.map((item, idx) => {
              const isAi = item.speaker === 'ai_interviewer';
              const isItemSpeaking = activeSpeakingText === item.text && isSpeaking;

              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    gap: '10px',
                    alignSelf: isAi ? 'flex-start' : 'flex-end',
                    maxWidth: '88%'
                  }}
                >
                  {isAi && (
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}
                    >
                      <Bot size={16} color="#ffffff" />
                    </div>
                  )}

                  <div
                    style={{
                      background: isAi ? 'var(--bg-surface-secondary)' : 'var(--primary)',
                      color: isAi ? 'var(--text-primary)' : '#ffffff',
                      border: isItemSpeaking
                        ? '1.5px solid var(--primary)'
                        : isAi
                        ? '1px solid var(--border-light)'
                        : 'none',
                      padding: '12px 14px',
                      borderRadius: isAi ? '4px 14px 14px 14px' : '14px 4px 14px 14px',
                      fontSize: '13px',
                      lineHeight: '1.45',
                      boxShadow: isItemSpeaking ? '0 0 10px rgba(var(--primary-rgb, 59, 130, 246), 0.25)' : 'none',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div
                      style={{
                        fontSize: '10.5px',
                        fontWeight: '700',
                        color: isAi ? 'var(--primary)' : 'rgba(255, 255, 255, 0.85)',
                        marginBottom: '3px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <span>{isAi ? 'AI HR Interviewer' : 'Your Response'}</span>
                      {isAi && ttsSupported && (
                        <button
                          type="button"
                          onClick={() => speakText(item.text)}
                          title="Replay this question aloud"
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--primary)',
                            cursor: 'pointer',
                            padding: '2px',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          <Volume2 size={12} />
                        </button>
                      )}
                    </div>
                    <div>{item.text}</div>
                  </div>

                  {!isAi && (
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: 'var(--bg-surface-secondary)',
                        border: '1px solid var(--border-light)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}
                    >
                      <User size={16} color="var(--primary)" />
                    </div>
                  )}
                </div>
              );
            })}

            {sending && (
              <div style={{ display: 'flex', gap: '10px', alignSelf: 'flex-start', maxWidth: '80%' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}
                >
                  <Bot size={16} color="#ffffff" />
                </div>
                <div
                  style={{
                    background: 'var(--bg-surface-secondary)',
                    border: '1px solid var(--border-light)',
                    padding: '10px 14px',
                    borderRadius: '4px 14px 14px 14px',
                    fontSize: '12.5px',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Sparkles size={14} className="text-primary" />
                  <span>Interviewer is analyzing your response...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Candidate Input Area */}
          {!isComplete ? (
            <div className="ai-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label className="form-label" style={{ margin: 0, fontSize: '12px' }}>
                    Your Response (Voice or Typed)
                  </label>
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className={isRecording ? 'btn-danger' : 'btn-secondary'}
                    style={{
                      padding: '5px 12px',
                      fontSize: '11.5px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      borderRadius: '8px',
                      boxShadow: isRecording ? '0 0 10px rgba(239, 68, 68, 0.4)' : 'none'
                    }}
                  >
                    {isRecording ? <MicOff size={13} /> : <Mic size={13} />}
                    <span>{isRecording ? 'Listening... Click to Stop' : 'Start Speaking'}</span>
                  </button>
                </div>

                <textarea
                  rows={3}
                  placeholder="Click 'Start Speaking' to speak your answer via microphone, or type here. You can review and edit before submitting..."
                  value={candidateMessage}
                  onChange={(e) => setCandidateMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                      handleSendMessage();
                    }
                  }}
                  disabled={sending}
                  className="form-textarea"
                  style={{ fontSize: '13px', lineHeight: '1.45' }}
                />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Press <strong>Ctrl + Enter</strong> to submit, or click Submit Response.
                  </span>
                  <button
                    type="button"
                    onClick={handleSendMessage}
                    disabled={(!candidateMessage.trim() && !failedMessage) || sending}
                    className="btn-primary"
                    style={{ padding: '9px 18px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
                  >
                    <Send size={13} />
                    <span>{sending ? 'Sending...' : 'Submit Response'}</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="ai-card" style={{ textAlign: 'center', padding: '24px' }}>
              <CheckCircle2 size={36} color="var(--success)" style={{ margin: '0 auto 8px' }} />
              <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 4px' }}>
                HR Interview Concluded
              </h4>
              <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', maxWidth: '450px', margin: '0 auto 16px' }}>
                Great job completing the interview! Your answers have been recorded and evaluated across communication clarity, technical depth, and resume alignment.
              </p>
              <button
                type="button"
                onClick={handleFinishAndEvaluate}
                disabled={sending}
                className="btn-primary"
                style={{ padding: '10px 20px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <Award size={15} />
                <span>{sending ? 'Compiling Report...' : 'Generate Full Evaluation Report'}</span>
              </button>
            </div>
          )}

          {/* Graceful Error Display with Clear Retry Action */}
          {error && (
            <div
              className="alert-error"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '10px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
              <button
                type="button"
                onClick={handleSendMessage}
                disabled={sending}
                className="btn-primary"
                style={{
                  padding: '5px 12px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  background: '#b91c1c',
                  borderColor: '#991b1b'
                }}
              >
                <RefreshCw size={12} className={sending ? 'spin' : ''} />
                <span>Retry</span>
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Candidate Info & Stage Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="ai-card" style={{ padding: '16px' }}>
            <h4
              style={{
                fontSize: '11.5px',
                fontWeight: '800',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                margin: '0 0 12px'
              }}
            >
              Interview Session
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)' }}>CANDIDATE</span>
                <div style={{ fontSize: '12.5px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                  {session.resume_filename || 'Candidate Resume'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)' }}>TARGET ROLE</span>
                <div style={{ fontSize: '12.5px', fontWeight: '800', color: 'var(--primary)', marginTop: '2px' }}>
                  {session.predicted_role || 'Software Engineer'}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)' }}>CURRENT STAGE</span>
                <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                  {getInterviewStage()}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)' }}>MICROPHONE</span>
                <div
                  style={{
                    fontSize: '11.5px',
                    fontWeight: '700',
                    color: isRecording ? 'var(--danger)' : speechSupported ? 'var(--success)' : 'var(--text-muted)',
                    marginTop: '2px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: isRecording ? 'var(--danger)' : speechSupported ? 'var(--success)' : 'var(--text-muted)'
                    }}
                  />
                  <span>{isRecording ? 'Listening...' : speechSupported ? 'Ready' : 'Not Supported'}</span>
                </div>
              </div>

              <div>
                <span style={{ fontSize: '10.5px', fontWeight: '700', color: 'var(--text-muted)' }}>HR VOICE</span>
                <div
                  style={{
                    fontSize: '11.5px',
                    fontWeight: '700',
                    color: isMuted ? 'var(--text-muted)' : isSpeaking ? 'var(--primary)' : 'var(--success)',
                    marginTop: '2px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: isMuted ? 'var(--text-muted)' : isSpeaking ? 'var(--primary)' : 'var(--success)'
                    }}
                  />
                  <span>{isMuted ? 'Muted' : isSpeaking ? 'Speaking...' : 'Voice Enabled'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
