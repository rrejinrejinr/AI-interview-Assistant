import React, { useState, useEffect, useRef } from 'react';
import {
  HelpCircle,
  MessageSquare,
  AlertTriangle,
  Send,
  CheckCircle2,
  Clock,
  LifeBuoy,
  FileText,
  User,
  Mail,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check
} from 'lucide-react';
import { submitSupportTicketApi, querySupportChatApi } from '../services/api';

const CATEGORIES = [
  'Authentication & OTP',
  'Resume Upload & Parsing',
  'Candidate Profile & Active Resume',
  'ATS Analysis & Matching',
  'Practice Sessions & Question Engine',
  'Mock Interview & Camera Verification',
  'HR Interview & Audio',
  'Resume Builder & PDF Export',
  'AI Tech Bot & Recommendations',
  'General Technical Issue'
];

export default function HelpSupport({ user, onBack }) {
  const [activeTab, setActiveTab] = useState('chat'); // chat | report

  // Support Chatbot State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'How can we help you today? You can ask about Login/OTP, Resume Upload, Active Resume selection, ATS Scoring, Practice Sessions, Camera Verification, Resume Builder, or submit an official support ticket.'
    }
  ]);
  const [chatQuery, setChatQuery] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Complaint Form State - always starts completely empty (no prefilled name or email)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    category: '',
    subject: '',
    description: ''
  });
  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticketSuccess, setTicketSuccess] = useState(null);
  const [ticketError, setTicketError] = useState(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  const handleSendChat = async (e) => {
    e.preventDefault();
    const q = chatQuery.trim();
    if (!q || chatLoading) return;

    const userMsg = { id: Date.now(), sender: 'user', text: q };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatQuery('');
    setChatLoading(true);

    try {
      const res = await querySupportChatApi(q);
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: res.answer,
        suggestedAction: res.suggested_action
      };
      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Support Chat Error:', err);
      const errMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: 'Unable to process query at the moment. Please use the "Report a Problem" tab to submit a support ticket directly to our team.'
      };
      setChatMessages((prev) => [...prev, errMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSubmitComplaint = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setTicketError('Please provide your full name.');
      return;
    }
    if (!formData.email.trim()) {
      setTicketError('Please provide your account email.');
      return;
    }
    if (!formData.category) {
      setTicketError('Please select an issue category.');
      return;
    }
    if (!formData.subject.trim() || !formData.description.trim()) {
      setTicketError('Please provide both a subject and a detailed description of the issue.');
      return;
    }
    if (formData.description.trim().length < 10) {
      setTicketError('Please provide a more detailed description (at least 10 characters).');
      return;
    }

    setTicketLoading(true);
    setTicketError(null);
    setTicketSuccess(null);

    try {
      const res = await submitSupportTicketApi(
        formData.name.trim(),
        formData.email.trim(),
        formData.category,
        formData.subject.trim(),
        formData.description.trim()
      );
      setTicketSuccess(res);
      // Form fields are cleared after successful submission
      setFormData({
        name: '',
        email: '',
        category: '',
        subject: '',
        description: ''
      });
    } catch (err) {
      console.error('Complaint Submission Error:', err);
      // Safely extract a readable string from any error shape.
      // FastAPI 422 returns detail as an array of {type, loc, msg, input, ctx} objects.
      // Rendering that array directly causes "Objects are not valid as a React child".
      const extractErrorMessage = (error) => {
        const detail = error?.response?.data?.detail;
        if (!detail) {
          return error?.response?.data?.message
            || error?.message
            || 'Failed to submit complaint. Please try again.';
        }
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
          // Extract the human-readable "msg" field from each Pydantic validation error
          return detail.map(d => {
            const field = Array.isArray(d.loc) ? d.loc.filter(l => l !== 'body').join(' → ') : '';
            const msg = typeof d.msg === 'string' ? d.msg : JSON.stringify(d.msg);
            return field ? `${field}: ${msg}` : msg;
          }).join('; ');
        }
        if (typeof detail === 'object') {
          return detail.msg || detail.message || JSON.stringify(detail);
        }
        return String(detail);
      };
      setTicketError(extractErrorMessage(err));
    } finally {
      setTicketLoading(false);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Card */}
      <div className="ai-card">
        <div className="card-header" style={{ marginBottom: 0, flexWrap: 'wrap', gap: '12px' }}>
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
                <HelpCircle size={20} className="text-primary" />
                <span>Help & Support Center</span>
              </h3>
              <p className="card-subtitle">
                Interactive assistant, problem reporting desk, and official complaint tracking.
              </p>
            </div>
          </div>

          {/* Subtabs */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setActiveTab('chat')}
              className={`btn-secondary ${activeTab === 'chat' ? 'active' : ''}`}
              style={{
                background: activeTab === 'chat' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                color: activeTab === 'chat' ? 'white' : 'var(--text-secondary)',
                borderColor: activeTab === 'chat' ? 'var(--primary)' : 'var(--border-light)',
                padding: '8px 14px',
                fontSize: '12.5px'
              }}
            >
              <MessageSquare size={14} />
              <span>Support Chatbot</span>
            </button>

            <button
              onClick={() => setActiveTab('report')}
              className={`btn-secondary ${activeTab === 'report' ? 'active' : ''}`}
              style={{
                background: activeTab === 'report' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                color: activeTab === 'report' ? 'white' : 'var(--text-secondary)',
                borderColor: activeTab === 'report' ? 'var(--primary)' : 'var(--border-light)',
                padding: '8px 14px',
                fontSize: '12.5px'
              }}
            >
              <AlertTriangle size={14} />
              <span>Report a Problem</span>
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: SUPPORT CHATBOT */}
      {activeTab === 'chat' && (
        <div className="chat-container">
          <div className="chat-messages">
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`chat-bubble ${msg.sender === 'user' ? 'user' : 'assistant'}`}>
                <div style={{ fontSize: '11px', fontWeight: '800', marginBottom: '4px', opacity: 0.8, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  {msg.sender === 'user' ? (
                    <>
                      <User size={12} />
                      <span>You</span>
                    </>
                  ) : (
                    <>
                      <LifeBuoy size={12} />
                      <span>Support Assistant</span>
                    </>
                  )}
                </div>
                <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>
                {msg.suggestedAction && (
                  <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--border-light)', fontSize: '12px' }}>
                    <button
                      type="button"
                      onClick={() => setActiveTab('report')}
                      style={{
                        background: 'var(--primary-light)',
                        color: 'var(--primary)',
                        border: '1px solid var(--primary-border)',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '11.5px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <span>Report a Problem</span>
                      <ArrowRight size={12} />
                    </button>
                  </div>
                )}
              </div>
            ))}

            {chatLoading && (
              <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <LifeBuoy size={16} className="text-primary" />
                <span>Checking support knowledge base...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleSendChat} className="chat-input-area">
            <input
              type="text"
              placeholder="Describe your question (e.g. ATS scoring, voice recording, resume builder, or camera verification)..."
              value={chatQuery}
              onChange={(e) => setChatQuery(e.target.value)}
              className="form-input"
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              disabled={chatLoading || !chatQuery.trim()}
              className="btn-primary"
              style={{ padding: '0 24px' }}
            >
              <Send size={15} />
              <span>{chatLoading ? 'Sending...' : 'Send'}</span>
            </button>
          </form>
        </div>
      )}

      {/* TAB 2: REPORT A PROBLEM (COMPLAINT FORM) */}
      {activeTab === 'report' && (
        <div className="ai-card">
          <div className="card-header">
            <div>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)' }}>
                Submit a Support Complaint
              </h4>
              <p className="card-subtitle">
                Your ticket will be recorded in our system and automatically routed to our support team for review.
              </p>
            </div>
          </div>

          {ticketSuccess && (
            <div
              className={ticketSuccess.email_dispatched ? "alert-success" : "alert-warning"}
              style={{
                marginBottom: '18px',
                padding: '16px 18px',
                borderRadius: '8px',
                border: ticketSuccess.email_dispatched ? '1px solid var(--success-border)' : '1px solid var(--warning-border)',
                background: ticketSuccess.email_dispatched ? 'var(--success-light)' : 'var(--warning-light)',
                color: ticketSuccess.email_dispatched ? 'var(--success)' : 'var(--warning)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}
            >
              <CheckCircle2 size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <h4 style={{ margin: '0 0 4px', fontSize: '15px', fontWeight: '800' }}>
                  Complaint submitted successfully!
                </h4>
                <div style={{ fontSize: '13px', marginTop: '2px', color: 'var(--text-primary)' }}>
                  Ticket ID: <b style={{ fontFamily: 'var(--font-mono, monospace)', color: 'var(--primary)' }}>{ticketSuccess.ticket_id}</b>
                </div>
                {ticketSuccess.email_dispatched ? (
                  <div style={{ marginTop: '6px', fontSize: '12.5px', color: 'var(--success)', fontWeight: '600' }}>
                    Email notification delivered successfully.
                  </div>
                ) : (
                  <div style={{ marginTop: '6px', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                    Your complaint has been saved. Email notification is pending.
                  </div>
                )}
              </div>
            </div>
          )}

          {ticketError && (
            <div className="alert-error" style={{ marginBottom: '18px' }}>
              <AlertCircle size={18} />
              <span>{ticketError}</span>
            </div>
          )}

          <form onSubmit={handleSubmitComplaint} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div>
                <label className="form-label">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="Your Full Name"
                />
              </div>

              <div>
                <label className="form-label">Account Email *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="form-input"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div>
                <label className="form-label">Issue Category *</label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="form-select"
                >
                  <option value="">-- Select Issue Category --</option>
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label">Subject *</label>
                <input
                  type="text"
                  required
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="form-input"
                  placeholder="Brief summary of the issue"
                />
              </div>
            </div>

            <div>
              <label className="form-label">Detailed Description of Problem *</label>
              <textarea
                rows={6}
                required
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="form-textarea"
                placeholder="Please describe what occurred, the steps to reproduce, and any error message you encountered..."
              />
            </div>

            <button
              type="submit"
              disabled={ticketLoading}
              className="btn-primary"
              style={{ width: '100%', padding: '13px', fontSize: '13.5px', fontWeight: '700' }}
            >
              <Send size={15} />
              <span>{ticketLoading ? 'Submitting...' : 'Submit'}</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
