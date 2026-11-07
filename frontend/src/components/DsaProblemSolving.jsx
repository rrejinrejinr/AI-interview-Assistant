import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  CheckCircle2,
  Clock,
  Circle,
  Play,
  RotateCcw,
  ExternalLink,
  Search,
  Filter,
  ArrowLeft,
  RefreshCw,
  Code,
  BookOpen,
  Award,
  Check,
  ChevronDown,
  ChevronRight,
  Layers,
  AlertTriangle,
  AlertCircle,
  X,
  Terminal,
  Sparkles,
  Send,
  BarChart2
} from 'lucide-react';
import {
  getDsaTopicsApi,
  getDsaProblemsApi,
  getDsaProblemDetailApi,
  updateDsaProblemStatusApi,
  getDsaProgressApi,
  executeDsaCodeApi,
  submitDsaCodeApi,
  getDsaJudge0StatusApi
} from '../services/api';

const DIFFICULTY_COLORS = {
  Easy: { bg: 'var(--success-light)', color: 'var(--success)', border: 'var(--success-border)' },
  Medium: { bg: 'var(--warning-light)', color: 'var(--warning)', border: 'var(--warning-border)' },
  Hard: { bg: 'var(--danger-light)', color: 'var(--danger)', border: 'var(--danger-border)' }
};

export default function DsaProblemSolving({ onBack }) {
  // Navigation / View states: 'list' | 'solve'
  const [currentView, setCurrentView] = useState('list');
  const [activeProblemRef, setActiveProblemRef] = useState(null);
  const [problemDetail, setProblemDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Data states
  const [topics, setTopics] = useState([]);
  const [problems, setProblems] = useState([]);
  const [progressStats, setProgressStats] = useState(null);
  const [judge0Status, setJudge0Status] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedTopics, setSelectedTopics] = useState([]); // array of topic slugs or names
  const [difficultyFilter, setDifficultyFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // Code editor states (when in 'solve' view)
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [execResult, setExecResult] = useState(null);
  const [activeTestTab, setActiveTestTab] = useState(0);
  const [statusUpdating, setStatusUpdating] = useState(false);

  // Fetch initial data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [topicsRes, progressRes, judge0Res] = await Promise.all([
        getDsaTopicsApi().catch(() => []),
        getDsaProgressApi().catch(() => null),
        getDsaJudge0StatusApi().catch(() => ({ available: false }))
      ]);
      setTopics(topicsRes || []);
      setProgressStats(progressRes);
      setJudge0Status(judge0Res);
    } catch (err) {
      console.error('Error loading DSA data:', err);
      setError('Failed to load DSA topics and progress.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch problems whenever filters change
  const fetchProblems = async () => {
    try {
      const params = {};
      if (selectedTopics.length > 0) {
        params.topic = selectedTopics.join(',');
      }
      if (difficultyFilter !== 'All') {
        params.difficulty = difficultyFilter;
      }
      if (statusFilter !== 'All') {
        params.status = statusFilter.toLowerCase();
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }

      const res = await getDsaProblemsApi(params);
      setProblems(res.problems || []);
    } catch (err) {
      console.error('Error fetching problems:', err);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [selectedTopics, difficultyFilter, statusFilter, searchQuery]);

  // Load problem details when entering solve view
  const openProblem = async (problemRef) => {
    setActiveProblemRef(problemRef);
    setLoadingDetail(true);
    setCurrentView('solve');
    setExecResult(null);
    setActiveTestTab(0);
    try {
      const detail = await getDsaProblemDetailApi(problemRef);
      setProblemDetail(detail);

      // Pre-fill code with latest submission or starter code
      const defaultLang = 'python';
      setSelectedLanguage(defaultLang);
      if (detail.latest_submission?.code && detail.latest_submission.language.toLowerCase() === defaultLang) {
        setCode(detail.latest_submission.code);
      } else if (detail.starter_code && detail.starter_code[defaultLang]) {
        setCode(detail.starter_code[defaultLang]);
      } else {
        setCode('# Write your code here\n');
      }

      // Pre-fill custom input with sample test case input if available
      if (detail.sample_test_cases && detail.sample_test_cases.length > 0) {
        setCustomInput(detail.sample_test_cases[0].input || '');
      } else {
        setCustomInput('');
      }
    } catch (err) {
      console.error('Failed to load problem detail:', err);
      setError('Failed to load problem details.');
    } finally {
      setLoadingDetail(false);
    }
  };

  // Language switch handler
  const handleLanguageChange = (newLang) => {
    setSelectedLanguage(newLang);
    if (problemDetail?.starter_code && problemDetail.starter_code[newLang]) {
      setCode(problemDetail.starter_code[newLang]);
    } else {
      setCode(`// Write your ${newLang} solution here\n`);
    }
    setExecResult(null);
  };

  // Reset starter code
  const handleResetCode = () => {
    if (problemDetail?.starter_code && problemDetail.starter_code[selectedLanguage]) {
      setCode(problemDetail.starter_code[selectedLanguage]);
      setExecResult(null);
    }
  };

  // Update Problem Status (Solved / Attempted / Unsolved)
  const handleStatusChange = async (problemId, newStatus) => {
    setStatusUpdating(true);
    try {
      const updated = await updateDsaProblemStatusApi(problemId, newStatus);
      // Update local problem list
      setProblems((prev) =>
        prev.map((p) => (p.id === problemId ? { ...p, status: newStatus } : p))
      );
      // Update problemDetail if currently viewing
      if (problemDetail && problemDetail.id === problemId) {
        setProblemDetail((prev) => ({
          ...prev,
          user_progress: {
            ...prev.user_progress,
            status: newStatus,
            solved_at: updated.solved_at
          }
        }));
      }
      // Refresh progress metrics
      const newStats = await getDsaProgressApi().catch(() => null);
      if (newStats) setProgressStats(newStats);
      // Refresh topics to update solved badges
      const newTopics = await getDsaTopicsApi().catch(() => null);
      if (newTopics) setTopics(newTopics);
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setStatusUpdating(false);
    }
  };

  // Execute custom code via Judge0
  const handleRunCode = async () => {
    if (!code.trim() || !problemDetail) return;
    setExecuting(true);
    setExecResult(null);
    try {
      const res = await executeDsaCodeApi(problemDetail.id, code, selectedLanguage, customInput);
      setExecResult({
        type: 'run',
        verdict: res.success ? (res.status_description || 'Finished') : (res.error_type || 'Execution Error'),
        stdout: res.stdout,
        stderr: res.stderr || res.compile_output || res.message,
        execution_time_ms: res.execution_time_ms,
        memory_kb: res.memory_kb,
        success: res.success,
        error_type: res.error_type
      });
    } catch (err) {
      console.error('Run code error:', err);
      setExecResult({
        type: 'run',
        verdict: 'Execution Error',
        stderr: err.response?.data?.detail || err.message || 'Failed to communicate with execution server.',
        success: false
      });
    } finally {
      setExecuting(false);
    }
  };

  // Submit Solution via Judge0 evaluation
  const handleSubmitCode = async () => {
    if (!code.trim() || !problemDetail) return;
    setSubmitting(true);
    setExecResult(null);
    setActiveTestTab(0);
    try {
      const res = await submitDsaCodeApi(problemDetail.id, code, selectedLanguage);
      setExecResult({
        type: 'submit',
        verdict: res.verdict,
        passed: res.passed,
        passed_count: res.passed_count,
        total_count: res.total_count,
        results: res.results || [],
        error_message: res.error_message
      });

      // Update problem status locally
      if (res.user_status) {
        setProblemDetail((prev) => ({
          ...prev,
          user_progress: {
            ...prev.user_progress,
            status: res.user_status
          }
        }));
        setProblems((prev) =>
          prev.map((p) => (p.id === problemDetail.id ? { ...p, status: res.user_status } : p))
        );
      }

      // Refresh overall stats
      const newStats = await getDsaProgressApi().catch(() => null);
      if (newStats) setProgressStats(newStats);
      const newTopics = await getDsaTopicsApi().catch(() => null);
      if (newTopics) setTopics(newTopics);
    } catch (err) {
      console.error('Submit solution error:', err);
      setExecResult({
        type: 'submit',
        verdict: 'Submission Failed',
        passed: false,
        error_message: err.response?.data?.detail || err.message || 'Failed to submit solution.'
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Quick Start Practice button handler
  const handleQuickPractice = () => {
    // Pick the first unsolved problem from current filtered list, or first problem
    const unsolved = problems.find((p) => p.status === 'unsolved') || problems[0];
    if (unsolved) {
      openProblem(unsolved.id);
    }
  };

  // Reset all filters
  const handleResetFilters = () => {
    setSelectedTopics([]);
    setDifficultyFilter('All');
    setStatusFilter('All');
    setSearchQuery('');
  };

  // Topic click toggle
  const toggleTopicSelection = (slug) => {
    setSelectedTopics((prev) => {
      if (prev.includes(slug)) {
        return prev.filter((s) => s !== slug);
      } else {
        return [...prev, slug];
      }
    });
  };

  // Handle Tab key in code editor textarea
  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        e.target.selectionStart = e.target.selectionEnd = start + 4;
      }, 0);
    }
  };

  // 
  // RENDER: PROBLEM SOLVING WORKSPACE VIEW
  // 
  if (currentView === 'solve') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Workspace Top Navigation Bar */}
        <div className="ai-card" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                onClick={() => {
                  setCurrentView('list');
                  fetchProblems();
                }}
                className="btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 12px', fontSize: '13px' }}
              >
                <ArrowLeft size={16} />
                <span>Problem List</span>
              </button>

              {loadingDetail ? (
                <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>Loading problem...</div>
              ) : problemDetail ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                    {problemDetail.title}
                  </h3>
                  <span
                    className="badge"
                    style={{
                      background: DIFFICULTY_COLORS[problemDetail.difficulty]?.bg || 'var(--bg-surface-secondary)',
                      color: DIFFICULTY_COLORS[problemDetail.difficulty]?.color || 'var(--text-primary)',
                      border: `1px solid ${DIFFICULTY_COLORS[problemDetail.difficulty]?.border || 'var(--border-light)'}`,
                      fontSize: '11px',
                      fontWeight: '800',
                      padding: '2px 8px',
                      borderRadius: '12px'
                    }}
                  >
                    {problemDetail.difficulty}
                  </span>
                </div>
              ) : null}
            </div>

            {problemDetail && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {/* External LeetCode Button */}
                <a
                  href={problemDetail.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '7px 12px',
                    fontSize: '12.5px',
                    color: '#f59e0b',
                    borderColor: 'rgba(245, 158, 11, 0.4)',
                    textDecoration: 'none'
                  }}
                  title="Practice this exact problem on LeetCode"
                >
                  <ExternalLink size={14} />
                  <span>Open in LeetCode</span>
                </a>

                {/* Status Toggle Dropdown */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600' }}>Status:</span>
                  <select
                    value={problemDetail.user_progress?.status || 'unsolved'}
                    onChange={(e) => handleStatusChange(problemDetail.id, e.target.value)}
                    disabled={statusUpdating}
                    className="form-select"
                    style={{
                      padding: '5px 10px',
                      fontSize: '12px',
                      fontWeight: '700',
                      borderRadius: '8px',
                      width: 'auto'
                    }}
                  >
                    <option value="unsolved">⚪ Unsolved</option>
                    <option value="attempted">⏳ Attempted</option>
                    <option value="solved">✅ Solved</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        {loadingDetail || !problemDetail ? (
          <div className="ai-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw size={32} className="spin" style={{ margin: '0 auto 16px', display: 'block', color: 'var(--primary)' }} />
            <div style={{ fontSize: '15px', fontWeight: '700' }}>Loading problem specification & templates...</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 45%) 1fr', gap: '16px' }}>
            {/* LEFT COLUMN: Problem Details, Examples & Constraints */}
            <div className="ai-card" style={{ padding: '24px', overflowY: 'auto', maxHeight: 'calc(100vh - 200px)' }}>
              {/* Topic Tags */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                {problemDetail.topic_tags?.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      background: 'var(--primary-light)',
                      color: 'var(--primary)',
                      border: '1px solid var(--primary-border)',
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '3px 8px',
                      borderRadius: '6px'
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Description */}
              <div style={{ marginBottom: '22px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Problem Description
                </h4>
                <div style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.65', whiteSpace: 'pre-line' }}>
                  {problemDetail.description}
                </div>
              </div>

              {/* Examples */}
              {problemDetail.examples && problemDetail.examples.length > 0 && (
                <div style={{ marginBottom: '22px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Examples
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {problemDetail.examples.map((ex, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--bg-surface-secondary)',
                          border: '1px solid var(--border-light)',
                          borderRadius: '8px',
                          padding: '12px 14px',
                          fontSize: '12.5px',
                          fontFamily: 'var(--font-mono)'
                        }}
                      >
                        <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
                          Example {idx + 1}:
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Input: </span>
                          <span style={{ color: 'var(--text-primary)' }}>{ex.input}</span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Output: </span>
                          <span style={{ color: 'var(--success)', fontWeight: '700' }}>{ex.output}</span>
                        </div>
                        {ex.explanation && (
                          <div style={{ marginTop: '4px', color: 'var(--text-secondary)', fontSize: '12px', fontStyle: 'italic', fontFamily: 'var(--font-sans)' }}>
                            <span style={{ fontWeight: '600' }}>Explanation: </span>
                            {ex.explanation}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Constraints */}
              {problemDetail.constraints && problemDetail.constraints.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Constraints
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {problemDetail.constraints.map((c, i) => (
                      <li key={i} style={{ fontFamily: 'var(--font-mono)' }}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Execution Notice / LeetCode External Notice */}
              <div
                style={{
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid var(--primary-border)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  marginTop: '16px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <Terminal size={15} className="text-primary" />
                  <span style={{ fontSize: '12.5px', fontWeight: '800', color: 'var(--primary)' }}>
                    Practice Environment
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.45' }}>
                  {problemDetail.supports_execution
                    ? 'Write your solution on the right and run code or submit test cases. Submissions are verified against test benchmarks.'
                    : 'This problem is marked for external practice. Solve directly on LeetCode and mark your status as Solved when done.'}
                </p>
              </div>
            </div>

            {/* RIGHT COLUMN: Code Editor, Language Selection & Execution Console */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="ai-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Editor Header: Language selector and Reset button */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Code size={16} className="text-primary" />
                    <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>Language:</span>
                    <select
                      value={selectedLanguage}
                      onChange={(e) => handleLanguageChange(e.target.value)}
                      className="form-select"
                      style={{ padding: '6px 12px', fontSize: '13px', width: 'auto', minWidth: '130px' }}
                    >
                      <option value="python">Python 3</option>
                      <option value="javascript">JavaScript (Node.js)</option>
                      <option value="java">Java</option>
                      <option value="cpp">C++ (GCC)</option>
                    </select>
                  </div>

                  <button
                    onClick={handleResetCode}
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}
                    title="Reset starter template code"
                  >
                    <RotateCcw size={13} />
                    <span>Reset Code</span>
                  </button>
                </div>

                {/* Monospace Code Editor Area */}
                <div style={{ position: 'relative' }}>
                  <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Write your code here..."
                    spellCheck="false"
                    style={{
                      width: '100%',
                      minHeight: '360px',
                      height: '380px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      padding: '14px 16px',
                      borderRadius: '8px',
                      border: '1.5px solid var(--border-light)',
                      background: 'var(--bg-app)',
                      color: 'var(--text-primary)',
                      resize: 'vertical',
                      whiteSpace: 'pre',
                      tabSize: 4
                    }}
                  />
                </div>

                {/* Custom Input Toggle & Box */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setShowCustomInput(!showCustomInput)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: 0
                      }}
                    >
                      {showCustomInput ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span>Custom Test Input (stdin)</span>
                    </button>
                  </div>

                  {showCustomInput && (
                    <textarea
                      value={customInput}
                      onChange={(e) => setCustomInput(e.target.value)}
                      placeholder="Enter custom stdin test input..."
                      rows={3}
                      style={{
                        width: '100%',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid var(--border-light)',
                        background: 'var(--bg-surface-secondary)',
                        color: 'var(--text-primary)',
                        marginBottom: '4px'
                      }}
                    />
                  )}
                </div>

                {/* Editor Action Buttons */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={handleRunCode}
                    disabled={executing || submitting}
                    className="btn-secondary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      fontSize: '13px',
                      fontWeight: '700'
                    }}
                  >
                    {executing ? (
                      <>
                        <RefreshCw size={14} className="spin" />
                        <span>Running...</span>
                      </>
                    ) : (
                      <>
                        <Play size={14} />
                        <span>Run Code</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={handleSubmitCode}
                    disabled={executing || submitting}
                    className="btn-primary"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 20px',
                      fontSize: '13px',
                      fontWeight: '700'
                    }}
                  >
                    {submitting ? (
                      <>
                        <RefreshCw size={14} className="spin" />
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <Send size={14} />
                        <span>Submit Solution</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* EXECUTION RESULTS CONSOLE */}
              {execResult && (
                <div className="ai-card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Terminal size={18} className="text-primary" />
                      <h4 style={{ fontSize: '15px', fontWeight: '800', color: 'var(--text-primary)', margin: 0 }}>
                        {execResult.type === 'run' ? 'Test Run Output' : 'Submission Evaluation'}
                      </h4>
                    </div>

                    {/* Verdict Pill */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        className="badge"
                        style={{
                          background:
                            execResult.verdict === 'Accepted'
                              ? 'var(--success-light)'
                              : execResult.verdict === 'Service Unavailable'
                              ? 'rgba(234, 179, 8, 0.15)'
                              : 'var(--danger-light)',
                          color:
                            execResult.verdict === 'Accepted'
                              ? 'var(--success)'
                              : execResult.verdict === 'Service Unavailable'
                              ? '#d97706'
                              : 'var(--danger)',
                          border: `1px solid ${
                            execResult.verdict === 'Accepted'
                              ? 'var(--success-border)'
                              : execResult.verdict === 'Service Unavailable'
                              ? '#fde68a'
                              : 'var(--danger-border)'
                          }`,
                          fontSize: '12px',
                          fontWeight: '800',
                          padding: '4px 10px',
                          borderRadius: '12px'
                        }}
                      >
                        {execResult.verdict}
                      </span>

                      {execResult.type === 'submit' && execResult.total_count > 0 && (
                        <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                          {execResult.passed_count} / {execResult.total_count} Passed
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Service Unavailable Message */}
                  {execResult.verdict === 'Service Unavailable' && (
                    <div
                      style={{
                        background: 'rgba(234, 179, 8, 0.1)',
                        border: '1px solid rgba(234, 179, 8, 0.3)',
                        borderRadius: '8px',
                        padding: '12px 16px',
                        marginBottom: '14px',
                        fontSize: '12.5px',
                        color: 'var(--text-primary)'
                      }}
                    >
                      <div style={{ fontWeight: '700', color: '#b45309', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <AlertTriangle size={15} />
                        <span>Judge0 Execution Engine Offline</span>
                      </div>
                      <div>
                        The local Judge0 Docker service is not currently reachable at <code>http://localhost:2358</code>.
                        You can still practice this question directly on LeetCode using the <b>Open in LeetCode</b> link and mark your status as <b>Solved</b> above!
                      </div>
                    </div>
                  )}

                  {/* Run Output */}
                  {execResult.type === 'run' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {execResult.stdout !== undefined && (
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>
                            Standard Output (stdout)
                          </div>
                          <pre
                            style={{
                              background: 'var(--bg-surface-secondary)',
                              padding: '10px 12px',
                              borderRadius: '6px',
                              fontSize: '12.5px',
                              fontFamily: 'var(--font-mono)',
                              margin: 0,
                              overflowX: 'auto',
                              color: 'var(--text-primary)'
                            }}
                          >
                            {execResult.stdout || '(Empty output)'}
                          </pre>
                        </div>
                      )}

                      {execResult.stderr && (
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--danger)', textTransform: 'uppercase', marginBottom: '4px' }}>
                            Errors / Warnings (stderr)
                          </div>
                          <pre
                            style={{
                              background: 'var(--danger-light)',
                              color: 'var(--danger)',
                              padding: '10px 12px',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontFamily: 'var(--font-mono)',
                              margin: 0,
                              overflowX: 'auto'
                            }}
                          >
                            {execResult.stderr}
                          </pre>
                        </div>
                      )}

                      {execResult.execution_time_ms !== undefined && (
                        <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', marginTop: '4px' }}>
                          Runtime: {execResult.execution_time_ms} ms &nbsp;•&nbsp; Memory: {execResult.memory_kb || 0} KB
                        </div>
                      )}
                    </div>
                  )}

                  {/* Submission Test Cases Output */}
                  {execResult.type === 'submit' && execResult.results && execResult.results.length > 0 && (
                    <div>
                      {/* Test Case Tab Selectors */}
                      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', overflowX: 'auto', paddingBottom: '4px' }}>
                        {execResult.results.map((r, idx) => (
                          <button
                            key={idx}
                            onClick={() => setActiveTestTab(idx)}
                            style={{
                              padding: '5px 12px',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: '700',
                              border: activeTestTab === idx ? '1px solid var(--primary)' : '1px solid var(--border-light)',
                              background: activeTestTab === idx ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                              color: activeTestTab === idx ? 'var(--primary)' : 'var(--text-secondary)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px'
                            }}
                          >
                            {r.passed ? (
                              <CheckCircle2 size={13} color="var(--success)" />
                            ) : (
                              <X size={13} color="var(--danger)" />
                            )}
                            <span>Case {idx + 1}</span>
                          </button>
                        ))}
                      </div>

                      {/* Active Test Case Detail */}
                      {execResult.results[activeTestTab] && (
                        <div
                          style={{
                            background: 'var(--bg-surface-secondary)',
                            borderRadius: '8px',
                            padding: '14px',
                            fontSize: '12.5px',
                            fontFamily: 'var(--font-mono)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px'
                          }}
                        >
                          <div>
                            <span style={{ color: 'var(--text-muted)', fontWeight: '600' }}>Input: </span>
                            <span style={{ color: 'var(--text-primary)' }}>{execResult.results[activeTestTab].input || '(none)'}</span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)', fontWeight: '600' }}>Expected Output: </span>
                            <span style={{ color: 'var(--success)', fontWeight: '700' }}>{execResult.results[activeTestTab].expected_output}</span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)', fontWeight: '600' }}>Your Output: </span>
                            <span
                              style={{
                                color: execResult.results[activeTestTab].passed ? 'var(--success)' : 'var(--danger)',
                                fontWeight: '700'
                              }}
                            >
                              {execResult.results[activeTestTab].actual_output || '(no output)'}
                            </span>
                          </div>

                          {execResult.results[activeTestTab].stderr && (
                            <div style={{ marginTop: '4px' }}>
                              <span style={{ color: 'var(--danger)', fontWeight: '700' }}>Error: </span>
                              <pre style={{ margin: '4px 0 0', color: 'var(--danger)', fontSize: '11.5px' }}>
                                {execResult.results[activeTestTab].stderr}
                              </pre>
                            </div>
                          )}

                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                            Runtime: {execResult.results[activeTestTab].execution_time_ms || 0} ms &nbsp;•&nbsp; Memory: {execResult.results[activeTestTab].memory_kb || 0} KB
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 
  // RENDER: PROBLEM LIST & TOPIC SELECTION VIEW
  // 
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* HEADER BANNER */}
      <div className="ai-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              {onBack && (
                <button
                  onClick={onBack}
                  className="btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '6px 12px', fontSize: '12px' }}
                >
                  <ArrowLeft size={14} />
                  <span>Categories</span>
                </button>
              )}
              <h3 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Terminal size={22} className="text-primary" />
                <span>Topic-Based DSA Problem Solving</span>
              </h3>
            </div>
            <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', margin: 0, maxWidth: '750px' }}>
              Master foundational and advanced Data Structures & Algorithms. Select topics, filter by difficulty, test code against benchmarks via Judge0, or practice directly on LeetCode.
            </p>
          </div>

          {/* Judge0 Status Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '700',
              background: judge0Status?.available ? 'var(--success-light)' : 'var(--bg-surface-secondary)',
              color: judge0Status?.available ? 'var(--success)' : 'var(--text-muted)',
              border: `1px solid ${judge0Status?.available ? 'var(--success-border)' : 'var(--border-light)'}`
            }}
            title={judge0Status?.available ? 'Judge0 code execution engine is online' : 'Judge0 is offline. External LeetCode practice and manual tracking are active.'}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: judge0Status?.available ? 'var(--success)' : 'var(--text-muted)'
              }}
            />
            <span>{judge0Status?.available ? 'Judge0 Online' : 'External LeetCode Mode'}</span>
          </div>
        </div>

        {/* PROGRESS METRICS OVERVIEW */}
        {progressStats && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
              marginTop: '20px',
              paddingTop: '18px',
              borderTop: '1px solid var(--border-light)'
            }}
          >
            {/* Total Solved Card */}
            <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px 16px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Total Solved
              </div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--primary)', marginTop: '4px' }}>
                {progressStats.total_solved} <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: '600' }}>/ {progressStats.total_problems}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {progressStats.overall_percentage}% completion rate
              </div>
            </div>

            {/* Easy Card */}
            <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px 16px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--success)', textTransform: 'uppercase' }}>
                Easy Problems
              </div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
                {progressStats.by_difficulty?.Easy?.solved || 0} <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: '600' }}>/ {progressStats.by_difficulty?.Easy?.total || 0}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {progressStats.by_difficulty?.Easy?.percentage || 0}% solved
              </div>
            </div>

            {/* Medium Card */}
            <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px 16px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--warning)', textTransform: 'uppercase' }}>
                Medium Problems
              </div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
                {progressStats.by_difficulty?.Medium?.solved || 0} <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: '600' }}>/ {progressStats.by_difficulty?.Medium?.total || 0}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {progressStats.by_difficulty?.Medium?.percentage || 0}% solved
              </div>
            </div>

            {/* Hard Card */}
            <div style={{ background: 'var(--bg-surface-secondary)', padding: '14px 16px', borderRadius: '10px' }}>
              <div style={{ fontSize: '11.5px', fontWeight: '700', color: 'var(--danger)', textTransform: 'uppercase' }}>
                Hard Problems
              </div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--text-primary)', marginTop: '4px' }}>
                {progressStats.by_difficulty?.Hard?.solved || 0} <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: '600' }}>/ {progressStats.by_difficulty?.Hard?.total || 0}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {progressStats.by_difficulty?.Hard?.percentage || 0}% solved
              </div>
            </div>
          </div>
        )}
      </div>

      {/* TOPIC SELECTION GRID (20 Major DSA Topics) */}
      <div className="ai-card" style={{ padding: '22px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h4 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} className="text-primary" />
              <span>Select DSA Topics ({topics.length})</span>
            </h4>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: 0 }}>
              Click topics to filter the problem library. Select multiple topics to practice specific algorithm patterns.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {selectedTopics.length > 0 && (
              <button
                onClick={() => setSelectedTopics([])}
                className="btn-secondary"
                style={{ padding: '5px 10px', fontSize: '12px' }}
              >
                Clear Selection ({selectedTopics.length})
              </button>
            )}
            <button
              onClick={() => setSelectedTopics(topics.map((t) => t.slug))}
              className="btn-secondary"
              style={{ padding: '5px 10px', fontSize: '12px' }}
            >
              Select All
            </button>
          </div>
        </div>

        {/* 20 Topics Badges / Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '10px'
          }}
        >
          {topics.map((topic) => {
            const isSelected = selectedTopics.includes(topic.slug);
            return (
              <div
                key={topic.id}
                onClick={() => toggleTopicSelection(topic.slug)}
                style={{
                  background: isSelected ? 'var(--primary-light)' : 'var(--bg-surface-secondary)',
                  border: isSelected ? '1.5px solid var(--primary)' : '1px solid var(--border-light)',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span
                    style={{
                      fontSize: '12.5px',
                      fontWeight: isSelected ? '800' : '700',
                      color: isSelected ? 'var(--primary)' : 'var(--text-primary)'
                    }}
                  >
                    {topic.name}
                  </span>
                  {isSelected && <Check size={14} color="var(--primary)" />}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>{topic.total_problems} problems</span>
                  {topic.solved_count > 0 && (
                    <span style={{ color: 'var(--success)', fontWeight: '700' }}>
                      {topic.solved_count} solved
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* FILTER BAR & PROBLEM CATALOG */}
      <div className="ai-card" style={{ padding: '22px' }}>
        {/* Filter Controls Row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', flex: 1 }}>
            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: '240px', flex: '1 1 240px' }}>
              <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search problem title or pattern..."
                className="form-control"
                style={{ paddingLeft: '34px', fontSize: '13px' }}
              />
              {searchQuery && (
                <X
                  size={14}
                  onClick={() => setSearchQuery('')}
                  style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', cursor: 'pointer', color: 'var(--text-muted)' }}
                />
              )}
            </div>

            {/* Difficulty Filter */}
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="form-select"
              style={{ width: 'auto', minWidth: '130px', fontSize: '13px' }}
            >
              <option value="All">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-select"
              style={{ width: 'auto', minWidth: '120px', fontSize: '13px' }}
            >
              <option value="All">All Status</option>
              <option value="Solved">Solved</option>
              <option value="Unsolved">Unsolved</option>
              <option value="Attempted">Attempted</option>
            </select>

            {/* Reset Filters */}
            {(selectedTopics.length > 0 || difficultyFilter !== 'All' || statusFilter !== 'All' || searchQuery) && (
              <button
                onClick={handleResetFilters}
                className="btn-secondary"
                style={{ padding: '7px 12px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <RotateCcw size={13} />
                <span>Reset</span>
              </button>
            )}
          </div>

          {/* Quick Start Practice Action */}
          <button
            onClick={handleQuickPractice}
            disabled={problems.length === 0}
            className="btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              padding: '8px 18px',
              fontSize: '13px',
              fontWeight: '700'
            }}
          >
            <Play size={15} />
            <span>Start Practice</span>
          </button>
        </div>

        {/* Matching Count */}
        <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginBottom: '14px', fontWeight: '600' }}>
          Showing {problems.length} problem{problems.length !== 1 ? 's' : ''} matching criteria
          {selectedTopics.length > 0 && ` across ${selectedTopics.length} selected topic(s)`}
        </div>

        {/* Problems Table */}
        {problems.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
            <Terminal size={36} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
            <div style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
              No problems found
            </div>
            <div style={{ fontSize: '13px', marginBottom: '14px' }}>
              Try adjusting your topic selection, difficulty filter, or search keywords.
            </div>
            <button onClick={handleResetFilters} className="btn-secondary" style={{ fontSize: '12.5px' }}>
              Reset All Filters
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1.5px solid var(--border-light)', color: 'var(--text-muted)', fontSize: '11.5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  <th style={{ padding: '10px 12px', width: '40px' }}>Status</th>
                  <th style={{ padding: '10px 14px' }}>Problem Title</th>
                  <th style={{ padding: '10px 14px' }}>Topic Tags</th>
                  <th style={{ padding: '10px 14px', width: '100px' }}>Difficulty</th>
                  <th style={{ padding: '10px 14px', width: '220px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {problems.map((p) => {
                  const isSolved = p.status === 'solved';
                  const isAttempted = p.status === 'attempted';
                  const diffStyle = DIFFICULTY_COLORS[p.difficulty] || DIFFICULTY_COLORS.Medium;

                  return (
                    <tr
                      key={p.id}
                      style={{
                        borderBottom: '1px solid var(--border-light)',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-secondary)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      {/* Status Icon */}
                      <td style={{ padding: '12px' }}>
                        {isSolved ? (
                          <CheckCircle2 size={18} color="var(--success)" title="Solved" />
                        ) : isAttempted ? (
                          <Clock size={18} color="var(--warning)" title="Attempted" />
                        ) : (
                          <Circle size={18} color="var(--text-muted)" opacity={0.4} title="Unsolved" />
                        )}
                      </td>

                      {/* Title */}
                      <td style={{ padding: '12px 14px' }}>
                        <div
                          onClick={() => openProblem(p.id)}
                          style={{
                            fontWeight: '700',
                            color: 'var(--text-primary)',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--primary)')}
                          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                        >
                          <span>{p.title}</span>
                        </div>
                      </td>

                      {/* Topic Tags */}
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {p.topic_tags?.map((tag) => (
                            <span
                              key={tag}
                              style={{
                                background: 'var(--bg-surface-secondary)',
                                color: 'var(--text-secondary)',
                                border: '1px solid var(--border-light)',
                                fontSize: '11px',
                                padding: '2px 6px',
                                borderRadius: '4px'
                              }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* Difficulty Badge */}
                      <td style={{ padding: '12px 14px' }}>
                        <span
                          style={{
                            background: diffStyle.bg,
                            color: diffStyle.color,
                            border: `1px solid ${diffStyle.border}`,
                            fontSize: '11px',
                            fontWeight: '800',
                            padding: '3px 8px',
                            borderRadius: '12px',
                            display: 'inline-block'
                          }}
                        >
                          {p.difficulty}
                        </span>
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                          {/* Solve Button */}
                          <button
                            onClick={() => openProblem(p.id)}
                            className="btn-primary"
                            style={{
                              padding: '5px 12px',
                              fontSize: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <Code size={13} />
                            <span>Solve</span>
                          </button>

                          {/* LeetCode Direct Link */}
                          <a
                            href={p.external_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-secondary"
                            style={{
                              padding: '5px 8px',
                              fontSize: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              color: '#f59e0b',
                              borderColor: 'rgba(245, 158, 11, 0.3)',
                              textDecoration: 'none'
                            }}
                            title="Open on LeetCode in new tab"
                          >
                            <ExternalLink size={13} />
                          </a>

                          {/* Quick Status Toggle Button */}
                          <button
                            onClick={() => handleStatusChange(p.id, isSolved ? 'unsolved' : 'solved')}
                            className="btn-secondary"
                            style={{
                              padding: '5px 8px',
                              fontSize: '11px',
                              color: isSolved ? 'var(--success)' : 'var(--text-muted)'
                            }}
                            title={isSolved ? 'Click to mark as Unsolved' : 'Click to mark as Solved'}
                          >
                            {isSolved ? <Check size={13} /> : 'Mark'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
