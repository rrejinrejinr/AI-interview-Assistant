import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, ArrowLeft, Pencil, X, Check } from 'lucide-react';
import { queryRagApi, getLlmStatusApi } from '../services/api';
import SafeMarkdown from './SafeMarkdown';

export default function AiTechBot({ activeResumeId, resumes = [], onBack }) {
  const [selectedResumeId, setSelectedResumeId] = useState(activeResumeId ? String(activeResumeId) : '');
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [hoveredMsgId, setHoveredMsgId] = useState(null);
  const [llmStatus, setLlmStatus] = useState(null);

  // Editing state for user messages
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState('');

  const messagesEndRef = useRef(null);
  const editTextareaRef = useRef(null);
  const inputTextareaRef = useRef(null);

  useEffect(() => {
    getLlmStatusApi()
      .then((data) => setLlmStatus(data))
      .catch((err) => console.warn('Failed to load LLM diagnostic status:', err));
  }, []);

  useEffect(() => {
    if (activeResumeId) {
      setSelectedResumeId(String(activeResumeId));
    } else {
      setSelectedResumeId('');
    }
  }, [activeResumeId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (editingId !== null && editTextareaRef.current) {
      editTextareaRef.current.focus();
      editTextareaRef.current.style.height = 'auto';
      editTextareaRef.current.style.height = editTextareaRef.current.scrollHeight + 'px';
    }
  }, [editingId]);

  const buildHistoryPayload = (msgList) =>
    msgList.slice(-8).map((m) => ({ sender: m.sender, text: m.text }));

  const submitQuestion = async (queryText) => {
    const q = (queryText || '').trim();
    if (!q || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: q
    };

    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInputQuery('');
    if (inputTextareaRef.current) {
      inputTextareaRef.current.style.height = 'auto';
    }
    setLoading(true);

    try {
      const historyPayload = buildHistoryPayload(nextMessages);

      const res = await queryRagApi(
        q,
        selectedResumeId ? parseInt(selectedResumeId, 10) : null,
        historyPayload
      );

      const aiMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: res.answer,
        citations: res.citations || [],
        retrievedCount: res.retrieved_count || 1,
        provider: res.provider,
        model: res.model
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Tech Bot Error:', err);
      const errMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: 'I encountered an issue querying the technical knowledge base. Please verify your query and try again.'
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setInputQuery(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
  };

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inputQuery.trim() && !loading) {
        submitQuestion(inputQuery);
      }
    }
  };

  const handleSendMessage = (e) => {
    if (e) e.preventDefault();
    if (inputQuery.trim() && !loading) {
      submitQuestion(inputQuery);
    }
  };

  const handleStartEdit = (msg) => {
    if (loading) return;
    setEditingId(msg.id);
    setEditingText(msg.text);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingText('');
  };

  const handleSaveEdit = async (editedMsgId) => {
    const trimmed = editingText.trim();
    if (!trimmed || loading) return;

    const editIdx = messages.findIndex((m) => m.id === editedMsgId);
    if (editIdx === -1) return;

    const beforeEdit = messages.slice(0, editIdx);
    const updatedUserMsg = { ...messages[editIdx], text: trimmed };
    const truncatedMessages = [...beforeEdit, updatedUserMsg];

    setMessages(truncatedMessages);
    setEditingId(null);
    setEditingText('');
    setLoading(true);

    try {
      const historyPayload = buildHistoryPayload(truncatedMessages);

      const res = await queryRagApi(
        trimmed,
        selectedResumeId ? parseInt(selectedResumeId, 10) : null,
        historyPayload
      );

      const newAiMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: res.answer,
        citations: res.citations || [],
        retrievedCount: res.retrieved_count || 1,
        provider: res.provider,
        model: res.model
      };

      setMessages((prev) => [...prev, newAiMsg]);
    } catch (err) {
      console.error('Tech Bot Edit Error:', err);
      const errMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: 'I encountered an issue generating a response. Please try again.'
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleEditKeyDown = (e, msgId) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit(msgId);
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

  const handleEditTextareaChange = (e) => {
    setEditingText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      {/* Top Header Card */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '14px 20px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)',
          borderRadius: '10px',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="btn-secondary"
              style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}
            >
              <ArrowLeft size={14} />
              <span>Back</span>
            </button>
          )}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              AI Tech Bot
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
              Technical Assistant
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {llmStatus && (
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: llmStatus.has_api_key ? 'var(--success)' : 'var(--text-muted)',
                background: llmStatus.has_api_key ? 'var(--success-light)' : 'var(--bg-surface-secondary)',
                border: `1px solid ${
                  llmStatus.has_api_key ? 'var(--success-border)' : 'var(--border-light)'
                }`,
                padding: '4px 10px',
                borderRadius: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: llmStatus.has_api_key ? 'var(--success)' : 'var(--text-muted)'
                }}
              />
              <span>{llmStatus.has_api_key ? 'Online' : 'Offline'}</span>
            </div>
          )}

          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              background: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-light)',
              padding: '5px 12px',
              borderRadius: '16px',
              fontWeight: 500
            }}
          >
            {resumes.find((r) => String(r.id) === String(selectedResumeId))?.filename || 'General CS'}
          </div>
        </div>
      </div>

      {/* Main Chat Container */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '620px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)',
          borderRadius: '10px',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-sm)',
          position: 'relative'
        }}
      >
        {/* Messages Scroll Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}
        >
          {/* Simple Empty State (No buttons, no prompt pills) */}
          {messages.length === 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                flex: 1,
                padding: '40px 20px',
                textAlign: 'center'
              }}
            >
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '8px',
                  background: 'var(--bg-surface-secondary)',
                  border: '1px solid var(--border-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '10px'
                }}
              >
                <Bot size={20} style={{ color: 'var(--primary)' }} />
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 700, margin: '0 0 4px', color: 'var(--text-primary)' }}>
                AI Tech Bot
              </h4>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                Ask me a technical question.
              </p>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg) => {
            if (msg.sender === 'user') {
              return (
                <div
                  key={msg.id}
                  onMouseEnter={() => setHoveredMsgId(msg.id)}
                  onMouseLeave={() => setHoveredMsgId(null)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-end',
                    width: '100%'
                  }}
                >
                  <div
                    style={{
                      maxWidth: '75%',
                      minWidth: '120px',
                      background: 'var(--primary, #2563eb)',
                      color: '#ffffff',
                      padding: '10px 14px',
                      borderRadius: '10px 10px 2px 10px',
                      fontSize: '13.5px',
                      lineHeight: 1.5,
                      position: 'relative',
                      wordBreak: 'break-word',
                      boxShadow: 'var(--shadow-sm)'
                    }}
                  >
                    {editingId === msg.id ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <textarea
                          ref={editTextareaRef}
                          value={editingText}
                          onChange={handleEditTextareaChange}
                          onKeyDown={(e) => handleEditKeyDown(e, msg.id)}
                          rows={1}
                          style={{
                            width: '100%',
                            background: 'rgba(255, 255, 255, 0.15)',
                            border: '1px solid rgba(255, 255, 255, 0.5)',
                            borderRadius: '6px',
                            color: '#ffffff',
                            fontFamily: 'inherit',
                            fontSize: '13.5px',
                            lineHeight: 1.5,
                            padding: '6px 8px',
                            resize: 'none',
                            outline: 'none',
                            boxSizing: 'border-box'
                          }}
                        />
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                          <button
                            type="button"
                            onClick={handleCancelEdit}
                            style={{
                              background: 'rgba(255, 255, 255, 0.2)',
                              border: 'none',
                              borderRadius: '4px',
                              color: '#ffffff',
                              cursor: 'pointer',
                              padding: '3px 8px',
                              fontSize: '11px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '3px'
                            }}
                          >
                            <X size={11} />
                            <span>Cancel</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSaveEdit(msg.id)}
                            disabled={!editingText.trim()}
                            style={{
                              background: '#ffffff',
                              border: 'none',
                              borderRadius: '4px',
                              color: 'var(--primary, #2563eb)',
                              cursor: editingText.trim() ? 'pointer' : 'not-allowed',
                              padding: '3px 8px',
                              fontSize: '11px',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              gap: '3px',
                              opacity: editingText.trim() ? 1 : 0.6
                            }}
                          >
                            <Check size={11} />
                            <span>Send</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                        {hoveredMsgId === msg.id && !loading && (
                          <button
                            type="button"
                            onClick={() => handleStartEdit(msg)}
                            style={{
                              position: 'absolute',
                              top: '6px',
                              left: '-52px',
                              background: 'var(--bg-surface)',
                              border: '1px solid var(--border-light)',
                              borderRadius: '4px',
                              padding: '2px 6px',
                              fontSize: '11px',
                              fontWeight: 600,
                              color: 'var(--text-secondary)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '3px',
                              boxShadow: 'var(--shadow-sm)'
                            }}
                            title="Edit message"
                          >
                            <Pencil size={11} />
                            <span>Edit</span>
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            }

            // AI assistant message
            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start',
                  width: '100%',
                  maxWidth: '90%'
                }}
              >
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '6px',
                    background: 'var(--bg-surface-secondary)',
                    border: '1px solid var(--border-light)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px'
                  }}
                >
                  <Bot size={15} style={{ color: 'var(--primary)' }} />
                </div>

                <div
                  style={{
                    flex: 1,
                    background: 'var(--bg-surface-secondary)',
                    border: '1px solid var(--border-light)',
                    borderRadius: '2px 10px 10px 10px',
                    padding: '12px 16px',
                    fontSize: '13.5px',
                    lineHeight: 1.6,
                    color: 'var(--text-primary)',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                >
                  <SafeMarkdown content={msg.text} />

                  {/* Subtle sources and answering provider attribution */}
                  <div
                    style={{
                      marginTop: '8px',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '6px'
                    }}
                  >
                    {msg.citations && msg.citations.length > 0 && (
                      <span>Sources: {msg.citations.join(', ')}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Minimal Loading State */}
          {loading && (
            <div
              style={{
                display: 'flex',
                gap: '10px',
                alignItems: 'center',
                color: 'var(--text-secondary)',
                fontSize: '13px'
              }}
            >
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  background: 'var(--bg-surface-secondary)',
                  border: '1px solid var(--border-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}
              >
                <Bot size={15} style={{ color: 'var(--primary)' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                <span>Thinking</span>
                <span style={{ letterSpacing: '2px', fontWeight: 700 }}>...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ChatGPT-style Auto-resizing Input Area at Bottom */}
        <form
          onSubmit={handleSendMessage}
          style={{
            padding: '10px 14px',
            borderTop: '1px solid var(--border-light)',
            background: 'var(--bg-surface)',
            display: 'flex',
            gap: '8px',
            alignItems: 'flex-end',
            position: 'sticky',
            bottom: 0,
            zIndex: 10
          }}
        >
          <textarea
            ref={inputTextareaRef}
            rows={1}
            placeholder="Ask a technical question..."
            value={inputQuery}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
            style={{
              flex: 1,
              padding: '9px 12px',
              fontSize: '13.5px',
              lineHeight: 1.5,
              borderRadius: '6px',
              border: '1.5px solid var(--border-light)',
              background: 'var(--input-bg, var(--bg-surface))',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              resize: 'none',
              outline: 'none',
              maxHeight: '140px',
              overflowY: 'auto',
              boxSizing: 'border-box',
              transition: 'border-color 0.15s, box-shadow 0.15s'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--primary)';
              e.target.style.boxShadow = '0 0 0 2px var(--primary-light, rgba(37, 99, 235, 0.15))';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--border-light)';
              e.target.style.boxShadow = 'none';
            }}
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="btn-primary"
            style={{
              padding: '9px 16px',
              fontSize: '13px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              height: '38px',
              flexShrink: 0
            }}
          >
            <Send size={14} />
            <span>{loading ? 'Thinking...' : 'Send'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
