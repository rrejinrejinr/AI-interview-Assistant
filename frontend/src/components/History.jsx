import React, { useState, useEffect } from 'react';
import {
  History as HistoryIcon,
  FileText,
  Target,
  Video,
  Layers,
  MessagesSquare,
  RotateCcw,
  CheckCircle2,
  X,
  ChevronRight,
  AlertCircle,
  XCircle,
  ShieldCheck,
  Play
} from 'lucide-react';
import {
  getUserResumesApi,
  getAtsHistoryApi,
  getMockInterviewSessionsApi,
  getMockInterviewReportApi,
  getPracticeSessionsApi,
  getPracticeReportApi,
  getAiInterviewSessionsApi,
  getAiInterviewReportApi
} from '../services/api';
import MockInterviewReport from './MockInterviewReport';
import PracticeReport from './PracticeReport';
import AIOneToOneReport from './AIOneToOneReport';

export default function History({
  onNavigateToProfile,
  onNavigateToUpload,
  onNavigateToPractice,
  onResumePractice,
  onNavigateToMock,
  onNavigateToAiInterview
}) {
  const [activeTab, setActiveTab] = useState('resumes'); // resumes | ats | practice | mock | ai_interview
  const [resumes, setResumes] = useState([]);
  const [atsHistory, setAtsHistory] = useState([]);
  const [practiceList, setPracticeList] = useState([]);
  const [mockList, setMockList] = useState([]);
  const [aiInterviewList, setAiInterviewList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modal report states
  const [selectedAtsResult, setSelectedAtsResult] = useState(null);
  const [selectedMockReport, setSelectedMockReport] = useState(null);
  const [selectedPracticeReport, setSelectedPracticeReport] = useState(null);
  const [selectedAiReport, setSelectedAiReport] = useState(null);

  const fetchAllHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resList, atsList, pracList, mList, aiList] = await Promise.all([
        getUserResumesApi().catch(() => []),
        getAtsHistoryApi().catch(() => []),
        getPracticeSessionsApi().catch(() => []),
        getMockInterviewSessionsApi().catch(() => []),
        getAiInterviewSessionsApi().catch(() => [])
      ]);
      setResumes(resList);
      setAtsHistory(atsList);
      setPracticeList(pracList);
      setMockList(mList);
      setAiInterviewList(aiList);
    } catch (err) {
      console.error('History Fetch Error:', err);
      setError('Failed to load history records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllHistory();
  }, []);

  const handleViewMockReport = async (sessionId) => {
    try {
      const rep = await getMockInterviewReportApi(sessionId);
      setSelectedMockReport(rep);
    } catch (err) {
      console.error('Failed to load mock interview report:', err);
    }
  };

  const handleViewPracticeReport = async (sessionId) => {
    try {
      const rep = await getPracticeReportApi(sessionId);
      setSelectedPracticeReport(rep);
    } catch (err) {
      console.error('Failed to load practice report:', err);
    }
  };

  const handleViewAiReport = async (sessionId) => {
    try {
      const rep = await getAiInterviewReportApi(sessionId);
      setSelectedAiReport(rep);
    } catch (err) {
      console.error('Failed to load AI interview report:', err);
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

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return 'var(--text-muted)';
    if (score >= 75) return 'var(--success)';
    if (score >= 50) return 'var(--warning)';
    return '#ef4444';
  };

  const resetModals = () => {
    setSelectedAtsResult(null);
    setSelectedMockReport(null);
    setSelectedPracticeReport(null);
    setSelectedAiReport(null);
  };

  const formatSourceLabel = (src) => {
    if (!src) return 'Practice';
    if (src === 'aptitude') return 'Aptitude';
    if (src === 'fundamental_concepts') return 'Fundamental Concepts';
    if (src === 'problem_solving') return 'Problem Solving';
    if (src === 'resume_based') return 'Resume Based';
    return src;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Header Card */}
      <div className="ai-card">
        <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 className="card-title">
              <HistoryIcon size={20} className="text-primary" />
              <span>Application Activity & History Records</span>
            </h3>
            <p className="card-subtitle">
              Browse previously indexed resumes, ATS evaluations, practice sessions, mock interviews, and AI conversations.
            </p>
          </div>

          <button onClick={fetchAllHistory} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '12.5px' }}>
            <RotateCcw size={13} />
            <span>{loading ? 'Refreshing...' : 'Refresh History'}</span>
          </button>
        </div>

        {/* History Subtabs (5 tabs) */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-light)', paddingBottom: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <button
            className={`btn-secondary ${activeTab === 'resumes' ? 'active' : ''}`}
            onClick={() => { setActiveTab('resumes'); resetModals(); }}
            style={{
              background: activeTab === 'resumes' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
              color: activeTab === 'resumes' ? 'white' : 'var(--text-secondary)',
              borderColor: activeTab === 'resumes' ? 'var(--primary)' : 'var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <FileText size={14} />
            <span>Uploaded Resumes ({resumes.length})</span>
          </button>

          <button
            className={`btn-secondary ${activeTab === 'ats' ? 'active' : ''}`}
            onClick={() => { setActiveTab('ats'); resetModals(); }}
            style={{
              background: activeTab === 'ats' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
              color: activeTab === 'ats' ? 'white' : 'var(--text-secondary)',
              borderColor: activeTab === 'ats' ? 'var(--primary)' : 'var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Target size={14} />
            <span>ATS Analyses ({atsHistory.length})</span>
          </button>

          <button
            className={`btn-secondary ${activeTab === 'practice' ? 'active' : ''}`}
            onClick={() => { setActiveTab('practice'); resetModals(); }}
            style={{
              background: activeTab === 'practice' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
              color: activeTab === 'practice' ? 'white' : 'var(--text-secondary)',
              borderColor: activeTab === 'practice' ? 'var(--primary)' : 'var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Layers size={14} />
            <span>Practice Sessions ({practiceList.length})</span>
          </button>

          <button
            className={`btn-secondary ${activeTab === 'mock' ? 'active' : ''}`}
            onClick={() => { setActiveTab('mock'); resetModals(); }}
            style={{
              background: activeTab === 'mock' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
              color: activeTab === 'mock' ? 'white' : 'var(--text-secondary)',
              borderColor: activeTab === 'mock' ? 'var(--primary)' : 'var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Video size={14} />
            <span>Mock Interviews ({mockList.length})</span>
          </button>

          <button
            className={`btn-secondary ${activeTab === 'ai_interview' ? 'active' : ''}`}
            onClick={() => { setActiveTab('ai_interview'); resetModals(); }}
            style={{
              background: activeTab === 'ai_interview' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
              color: activeTab === 'ai_interview' ? 'white' : 'var(--text-secondary)',
              borderColor: activeTab === 'ai_interview' ? 'var(--primary)' : 'var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <MessagesSquare size={14} />
            <span>HR Interview ({aiInterviewList.length})</span>
          </button>
        </div>

        {error && (
          <div className="alert-error" style={{ marginBottom: '16px' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* TAB 1: RESUMES */}
        {activeTab === 'resumes' && (
          <div>
            {resumes.length === 0 ? (
              <div className="empty-state">
                <FileText size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
                <div className="empty-title">No Uploaded Resumes</div>
                <div className="empty-desc">Upload your resume to index skills, run ATS scores, and practice mock interviews.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {resumes.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      background: 'var(--bg-surface-secondary)',
                      border: '1px solid var(--border-light)',
                      borderRadius: '10px',
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>{r.filename}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Target Role: <strong>{r.predicted_role || 'Software Engineer'}</strong> • Uploaded: {formatDate(r.created_at)}
                      </div>
                    </div>
                    {onNavigateToProfile && (
                      <button
                        onClick={() => onNavigateToProfile(r.id)}
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        View Profile
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ATS ANALYSES */}
        {activeTab === 'ats' && (
          <div>
            {atsHistory.length === 0 ? (
              <div className="empty-state">
                <Target size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
                <div className="empty-title">No ATS Match History</div>
                <div className="empty-desc">Run an ATS analysis against target job descriptions to track match scores.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {atsHistory.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      background: 'var(--bg-surface-secondary)',
                      border: '1px solid var(--border-light)',
                      borderRadius: '10px',
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>
                        {item.job_title || 'Target Job Position'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Resume: {item.resume_filename || 'Candidate Resume'} • Analyzed: {formatDate(item.created_at)}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <span style={{ fontSize: '16px', fontWeight: '900', color: getScoreColor(item.ats_score) }}>
                        {item.ats_score}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: PRACTICE SESSIONS */}
        {activeTab === 'practice' && (
          <div>
            {practiceList.length === 0 ? (
              <div className="empty-state">
                <Layers size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
                <div className="empty-title">No Practice Sessions Recorded</div>
                <div className="empty-desc">Practice technical interview questions with instant AI feedback.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {practiceList.map((item) => {
                  const isExited = item.status === 'EXITED_BY_CANDIDATE';
                  const isCompleted = item.status === 'completed';
                  const canResume = (isExited || item.status === 'in_progress') && item.total_answered < item.question_count;

                  return (
                    <div
                      key={item.session_id}
                      style={{
                        background: 'var(--bg-surface-secondary)',
                        border: '1px solid var(--border-light)',
                        borderRadius: '10px',
                        padding: '14px 18px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '12px'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>
                            {formatSourceLabel(item.question_source)}
                          </span>
                          <span className={`badge ${isCompleted ? 'badge-success' : isExited ? 'badge-neutral' : 'badge-primary'}`}>
                            {isCompleted ? 'Completed' : isExited ? 'Exited' : 'In Progress'}
                          </span>
                        </div>

                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Difficulty: {item.difficulty} • Progress: {item.total_answered} / {item.question_count} Questions • Date: {formatDate(item.started_at)}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {item.overall_score !== null && item.overall_score > 0 && (
                          <span style={{ fontSize: '15px', fontWeight: '800', color: getScoreColor(item.overall_score) }}>
                            {item.overall_score}%
                          </span>
                        )}

                        {canResume && onResumePractice && (
                          <button
                            onClick={() => onResumePractice(item.session_id)}
                            className="btn-primary"
                            style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Play size={13} />
                            <span>Resume Practice</span>
                          </button>
                        )}

                        <button
                          onClick={() => handleViewPracticeReport(item.session_id)}
                          className="btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                          View Report
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: MOCK INTERVIEWS */}
        {activeTab === 'mock' && (
          <div>
            {mockList.length === 0 ? (
              <div className="empty-state">
                <Video size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
                <div className="empty-title">No Mock Interviews Recorded</div>
                <div className="empty-desc">Take a formal 30-question proctored technical mock interview.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {mockList.map((item) => {
                  const isRej = item.status === 'REJECTED_INTEGRITY_VIOLATION' || item.integrity_status === 'REJECTED';
                  const isExited = item.status === 'EXITED_BY_CANDIDATE';
                  const isCompleted = item.status === 'completed';

                  return (
                    <div
                      key={item.session_id}
                      style={{
                        background: 'var(--bg-surface-secondary)',
                        border: isRej ? '1.5px solid #ef4444' : '1px solid var(--border-light)',
                        borderRadius: '10px',
                        padding: '14px 18px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '12px'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>
                            Mock Interview #{item.session_id} (30 Questions)
                          </span>
                          <span className={`badge ${isRej ? 'badge-danger' : isExited ? 'badge-neutral' : 'badge-success'}`}>
                            {isRej ? 'Rejected (Integrity Violation)' : isExited ? 'Exited by Candidate' : 'Completed'}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Resume: {item.resume_filename || 'Resume'} • Difficulty: {item.difficulty} • Date: {formatDate(item.started_at)}
                          {isRej && item.rejection_reason && (
                            <span style={{ color: '#ef4444', display: 'block', marginTop: '2px' }}>
                              Reason: {item.rejection_reason}
                            </span>
                          )}
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {!isRej && item.overall_score !== null && item.overall_score > 0 && (
                          <span style={{ fontSize: '15px', fontWeight: '800', color: getScoreColor(item.overall_score) }}>
                            {item.overall_score}%
                          </span>
                        )}
                        <button
                          onClick={() => handleViewMockReport(item.session_id)}
                          className="btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                          View Report
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 5: HR INTERVIEWS */}
        {activeTab === 'ai_interview' && (
          <div>
            {aiInterviewList.length === 0 ? (
              <div className="empty-state">
                <MessagesSquare size={36} color="var(--text-muted)" style={{ margin: '0 auto 10px' }} />
                <div className="empty-title">No HR Interviews Recorded</div>
                <div className="empty-desc">Practice HR interviews with adaptive AI questioning and voice input.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {aiInterviewList.map((item) => (
                  <div
                    key={item.session_id}
                    style={{
                      background: 'var(--bg-surface-secondary)',
                      border: '1px solid var(--border-light)',
                      borderRadius: '10px',
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>
                        HR Interview #{item.session_id}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Resume: {item.resume_filename || 'Candidate Resume'} • Date: {formatDate(item.started_at)}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      {item.overall_score !== null && item.overall_score > 0 && (
                        <span style={{ fontSize: '15px', fontWeight: '800', color: getScoreColor(item.overall_score) }}>
                          {item.overall_score}%
                        </span>
                      )}
                      <button
                        onClick={() => handleViewAiReport(item.session_id)}
                        className="btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        View Report
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* MODAL: MOCK INTERVIEW REPORT */}
      {selectedMockReport && (
        <div className="ai-modal-backdrop" onClick={() => setSelectedMockReport(null)}>
          <div className="ai-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
              <button onClick={() => setSelectedMockReport(null)} className="btn-secondary" style={{ padding: '6px 12px' }}>
                <X size={16} /> Close Report
              </button>
            </div>
            <MockInterviewReport report={selectedMockReport} onStartNew={() => { setSelectedMockReport(null); if (onNavigateToMock) onNavigateToMock(); }} />
          </div>
        </div>
      )}

      {/* MODAL: PRACTICE REPORT */}
      {selectedPracticeReport && (
        <div className="ai-modal-backdrop" onClick={() => setSelectedPracticeReport(null)}>
          <div className="ai-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
              <button onClick={() => setSelectedPracticeReport(null)} className="btn-secondary" style={{ padding: '6px 12px' }}>
                <X size={16} /> Close Report
              </button>
            </div>
            <PracticeReport report={selectedPracticeReport} onStartNew={() => { setSelectedPracticeReport(null); if (onNavigateToPractice) onNavigateToPractice(); }} />
          </div>
        </div>
      )}

      {/* MODAL: AI ONE-TO-ONE REPORT */}
      {selectedAiReport && (
        <div className="ai-modal-backdrop" onClick={() => setSelectedAiReport(null)}>
          <div className="ai-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
              <button onClick={() => setSelectedAiReport(null)} className="btn-secondary" style={{ padding: '6px 12px' }}>
                <X size={16} /> Close Report
              </button>
            </div>
            <AIOneToOneReport report={selectedAiReport} onStartNew={() => { setSelectedAiReport(null); if (onNavigateToAiInterview) onNavigateToAiInterview(); }} />
          </div>
        </div>
      )}
    </div>
  );
}
