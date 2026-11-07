import React, { useState, useEffect } from 'react';
import {
  FileUp,
  User,
  Target,
  Layers,
  Video,
  MessagesSquare,
  Bot,
  Compass,
  History as HistoryIcon,
  HelpCircle,
  Sun,
  Moon,
  Menu,
  BrainCircuit,
  Activity
} from 'lucide-react';

import Sidebar from './components/sidebar';
import UploadResume from './components/UploadResume';
import CandidateProfile from './components/CandidateProfile';
import ExtractedSkills from './components/ExtractedSkills';
import AtsCard from './components/atscard';

// Practice Components
import PracticeSetup from './components/PracticeSetup';
import PracticeSession from './components/PracticeSession';
import PracticeReport from './components/PracticeReport';

// Dedicated Mock Interview Components (30-Question Resume-Only Screen)
import MockInterviewSetup from './components/MockInterviewSetup';
import MockInterviewVerification from './components/MockInterviewVerification';
import MockInterviewSession from './components/MockInterviewSession';
import MockInterviewReport from './components/MockInterviewReport';

// Dedicated AI One-to-One Interview Components (Conversational Voice/Text HR)
import AIOneToOneSetup from './components/AIOneToOneSetup';
import AIOneToOneInterview from './components/AIOneToOneInterview';
import AIOneToOneReport from './components/AIOneToOneReport';

import AiTechBot from './components/AiTechBot';
import Recommendations from './components/Recommendations';
import History from './components/History';
import HelpSupport from './components/HelpSupport';
import ResumeBuilder from './components/ResumeBuilder';
import Auth from './components/Auth';

import { checkHealthApi, getUserResumesApi, getMeApi, getPracticeSessionApi, getActiveResumeApi } from './services/api';
import './styles/dashboard.css';

const TAB_TITLES = {
  upload: 'Resume Document Upload',
  candidate_profile: 'User Profile',
  extracted_skills: 'Extracted Skills',
  resume_builder: 'ATS-Compliant Resume Builder',
  ats: 'ATS Resume & Job Match Optimization',
  practice: 'Technical Practice & Skill Evaluation',
  mock_interview: 'Formal 30-Question Mock Interview',
  ai_one_to_one: 'HR Interview',
  ai_tech_bot: 'AI Tech Bot',
  recommendations: 'AI Career Recommendations & Roadmap',
  history: 'Application Activity & History Records',
  support: 'Help & Support Center'
};

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('upload'); // Default to upload
  const [resumesList, setResumesList] = useState([]);
  // Always null on mount — the backend is the sole source of truth.
  // Active resume is ONLY set when the user uploads a resume in the current session.
  // Historical resumes from previous sessions must NOT be auto-activated.
  const [activeResumeId, setActiveResumeId] = useState(null);
  const [healthStatus, setHealthStatus] = useState('Checking...');
  const [authLoading, setAuthLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Theme Management (Light / Dark)
  const [theme, setTheme] = useState(() => localStorage.getItem('app_theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  const toggleTheme = (newTheme) => {
    setTheme(newTheme);
  };

  // Practice Flow State Machine: 'setup' -> 'session' -> 'report'
  const [practiceStage, setPracticeStage] = useState('setup');
  const [activePracticeSession, setActivePracticeSession] = useState(null);
  const [practiceReport, setPracticeReport] = useState(null);

  // Mock Interview Flow State Machine: 'setup' -> 'verification' -> 'session' -> 'report'
  const [mockStage, setMockStage] = useState('setup');
  const [activeMockSession, setActiveMockSession] = useState(null);
  const [mockReport, setMockReport] = useState(null);

  // AI One-to-One Flow State Machine: 'setup' -> 'interview' -> 'report'
  const [aiInterviewStage, setAiInterviewStage] = useState('setup');
  const [activeAiSession, setActiveAiSession] = useState(null);
  const [aiReport, setAiReport] = useState(null);

  /**
   * Fetch the user's resume list and active resume ID from the backend.
   * The backend is the sole source of truth — no localStorage fallback and
   * no automatic selection of resumes[0] as a default.
   */
  const fetchUserData = async () => {
    try {
      const [resumes, activeRes] = await Promise.all([
        getUserResumesApi().catch(() => []),
        getActiveResumeApi().catch(() => null)
      ]);
      const validResumes = Array.isArray(resumes) ? resumes : [];
      setResumesList(validResumes);

      // Use only what the backend explicitly says is active.
      // If the backend returns null (e.g. right after login), show empty state.
      const resolvedActiveId = activeRes?.active_resume_id ?? null;
      setActiveResumeId(resolvedActiveId);
    } catch (err) {
      console.error('Error fetching user data:', err);
    }
  };

  useEffect(() => {
    checkHealthApi()
      .then((d) => setHealthStatus(`Online (Port ${d.port})`))
      .catch(() => setHealthStatus('Offline'));

    const token = localStorage.getItem('token');
    if (token) {
      getMeApi()
        .then((u) => {
          setUser(u);
          // u.active_resume_id is null after login (backend clears it).
          // fetchUserData will read the backend active state for the current session.
          fetchUserData();
        })
        .catch(() => {
          localStorage.removeItem('token');
          setActiveResumeId(null);
        })
        .finally(() => setAuthLoading(false));
    } else {
      setAuthLoading(false);
    }
  }, []);

  const handleLoginSuccess = (u) => {
    setUser(u);
    // Backend cleared active_resume_id on login — mirror that in React state.
    setActiveResumeId(null);
    setResumesList([]);
    fetchUserData();
  };

  const handleSetActiveResume = (newId) => {
    setActiveResumeId(newId);
    if (newId) {
      localStorage.setItem('active_resume_id', String(newId));
    }
    fetchUserData();
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('active_resume_id');
    setUser(null);
    setResumesList([]);
    setActiveResumeId(null);
    setPracticeStage('setup');
    setActivePracticeSession(null);
    setPracticeReport(null);
    setMockStage('setup');
    setActiveMockSession(null);
    setMockReport(null);
    setAiInterviewStage('setup');
    setActiveAiSession(null);
    setAiReport(null);
    setActiveTab('upload');
  };

  const handleUploadComplete = (data) => {
    const newId = data.resume_id || data.active_resume_id;
    if (newId) {
      setActiveResumeId(newId);
    }
    fetchUserData();
  };

  const handleNavigateToProfile = () => {
    setActiveTab('candidate_profile');
  };

  // Practice session transitions
  const handlePracticeStarted = (sessionData) => {
    setActivePracticeSession(sessionData);
    setPracticeStage('session');
  };

  const handlePracticeCompleted = (reportData) => {
    setPracticeReport(reportData);
    setPracticeStage('report');
    fetchUserData();
  };

  const handleRestartPractice = () => {
    setPracticeStage('setup');
    setActivePracticeSession(null);
    setPracticeReport(null);
  };

  const handleResumePractice = async (sessionId) => {
    try {
      const sessionData = await getPracticeSessionApi(sessionId);
      setActivePracticeSession(sessionData);
      setPracticeStage('session');
      setActiveTab('practice');
    } catch (err) {
      console.error('Failed to resume practice session:', err);
    }
  };

  // Mock interview transitions
  const handleProceedToMockVerification = (sessionData) => {
    setActiveMockSession(sessionData);
    setMockStage('verification');
  };

  const handleBeginMockInterview = (verifiedSession) => {
    setActiveMockSession(verifiedSession);
    setMockStage('session');
  };

  const handleMockInterviewComplete = (reportData) => {
    setMockReport(reportData);
    setMockStage('report');
    fetchUserData();
  };

  const handleMockInterviewRejected = (rejectedData) => {
    setMockReport({
      ...rejectedData,
      status: 'REJECTED_INTEGRITY_VIOLATION',
      integrity_status: 'REJECTED'
    });
    setMockStage('report');
    fetchUserData();
  };

  const handleRestartMockInterview = () => {
    setMockStage('setup');
    setActiveMockSession(null);
    setMockReport(null);
  };

  // AI One-to-One interview transitions
  const handleAiInterviewStarted = (sessionData) => {
    setActiveAiSession(sessionData);
    setAiInterviewStage('interview');
  };

  const handleAiInterviewCompleted = (reportData) => {
    setAiReport(reportData);
    setAiInterviewStage('report');
    fetchUserData();
  };

  const handleRestartAiInterview = () => {
    setAiInterviewStage('setup');
    setActiveAiSession(null);
    setAiReport(null);
  };

  if (authLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#0f172a',
        color: 'white',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '14px' }}>
            <BrainCircuit size={42} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '16px', fontWeight: '700' }}>Initializing AI Interview Assistant...</div>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>Connecting to system services...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Auth onLoginSuccess={handleLoginSuccess} />;
  }

  const isMockExamSession = activeTab === 'mock_interview' && mockStage === 'session';

  return (
    <div className={`app-container ${isMockExamSession ? 'exam-mode-container' : ''}`}>
      {/* Left Sidebar (Hidden during exam) */}
      {!isMockExamSession && (
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tabId) => setActiveTab(tabId)}
          user={user}
          onLogout={handleLogout}
          resumesCount={resumesList.length}
          theme={theme}
          onToggleTheme={toggleTheme}
          isOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Main Content Area */}
      <div className={`app-main ${isMockExamSession ? 'exam-mode-main' : ''}`}>
        {/* Top Header (Hidden during exam) */}
        {!isMockExamSession && (
          <header className="app-header">
            <div className="header-left">
              <button
                className="mobile-nav-toggle"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle navigation"
              >
                <Menu size={20} />
              </button>
              <h1 className="header-greeting">{TAB_TITLES[activeTab] || 'Assistant'}</h1>
            </div>

            <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Profile Button */}
              <button
                onClick={() => setActiveTab('candidate_profile')}
                className="header-profile-btn"
                style={{
                  background: activeTab === 'candidate_profile' ? 'var(--primary-light, rgba(59, 130, 246, 0.12))' : 'var(--bg-surface-secondary)',
                  border: activeTab === 'candidate_profile' ? '1px solid var(--primary, #3b82f6)' : '1px solid var(--border-light)',
                  borderRadius: '20px',
                  padding: '6px 14px',
                  fontSize: '12.5px',
                  fontWeight: '700',
                  color: activeTab === 'candidate_profile' ? 'var(--primary, #3b82f6)' : 'var(--text-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease'
                }}
                title="User Profile"
              >
                <User size={14} className={activeTab === 'candidate_profile' ? 'text-primary' : ''} />
                <span>Profile</span>
              </button>

              {/* Quick Light/Dark Toggle in Header */}
              <button
                onClick={() => toggleTheme(theme === 'light' ? 'dark' : 'light')}
                style={{
                  background: 'var(--bg-surface-secondary)',
                  border: '1px solid var(--border-light)',
                  borderRadius: '20px',
                  padding: '6px 14px',
                  fontSize: '12.5px',
                  fontWeight: '700',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
              >
                {theme === 'light' ? <Moon size={13} /> : <Sun size={13} />}
                <span>{theme === 'light' ? 'Dark' : 'Light'}</span>
              </button>
            </div>
          </header>
        )}

        {/* Content Container */}
        <main className={`content-wrapper ${isMockExamSession ? 'exam-mode-content' : ''}`}>
          {/* TAB 1: UPLOAD RESUME */}
          {activeTab === 'upload' && (
            <UploadResume
              onUploadComplete={handleUploadComplete}
              onNavigateToProfile={handleNavigateToProfile}
              onNavigateToSkills={() => setActiveTab('extracted_skills')}
              onNavigateToAts={() => setActiveTab('ats')}
            />
          )}

          {/* TAB 2: USER PROFILE */}
          {activeTab === 'candidate_profile' && (
            <CandidateProfile
              onNavigateToUpload={() => setActiveTab('upload')}
              onBack={() => setActiveTab('upload')}
            />
          )}

          {/* TAB: EXTRACTED SKILLS */}
          {activeTab === 'extracted_skills' && (
            <ExtractedSkills
              activeResumeId={activeResumeId}
              resumes={resumesList}
              onNavigateToUpload={() => setActiveTab('upload')}
            />
          )}

          {/* TAB: RESUME BUILDER */}
          {activeTab === 'resume_builder' && (
            <ResumeBuilder
              user={user}
              onBack={() => setActiveTab('upload')}
            />
          )}

          {/* TAB 3: ATS ANALYSIS */}
          {activeTab === 'ats' && (
            <AtsCard
              activeResumeId={activeResumeId}
              resumes={resumesList}
              onNavigateToUpload={() => setActiveTab('upload')}
              onBack={() => setActiveTab('upload')}
            />
          )}

          {/* TAB 4: PRACTICE (Aptitude, Fundamental Concepts, Resume Based) */}
          {activeTab === 'practice' && (
            <div>
              {practiceStage === 'setup' && (
                <PracticeSetup
                  resumes={resumesList}
                  activeResumeId={activeResumeId}
                  onPracticeStarted={handlePracticeStarted}
                  onNavigateToUpload={() => setActiveTab('upload')}
                  onBack={() => setActiveTab('upload')}
                />
              )}

              {practiceStage === 'session' && activePracticeSession && (
                <PracticeSession
                  session={activePracticeSession}
                  onPracticeComplete={handlePracticeCompleted}
                  onExitPractice={handleRestartPractice}
                />
              )}

              {practiceStage === 'report' && practiceReport && (
                <PracticeReport
                  report={practiceReport}
                  onRestart={handleRestartPractice}
                />
              )}
            </div>
          )}

          {/* TAB 5: MOCK INTERVIEW (30 Resume Questions, Camera, Fullscreen, MediaPipe) */}
          {activeTab === 'mock_interview' && (
            <div>
              {mockStage === 'setup' && (
                <MockInterviewSetup
                  resumes={resumesList}
                  activeResumeId={activeResumeId}
                  onProceedToVerification={handleProceedToMockVerification}
                  onNavigateToUpload={() => setActiveTab('upload')}
                  onBack={() => setActiveTab('upload')}
                />
              )}

              {mockStage === 'verification' && activeMockSession && (
                <MockInterviewVerification
                  session={activeMockSession}
                  onBeginInterview={handleBeginMockInterview}
                  onCancel={handleRestartMockInterview}
                />
              )}

              {mockStage === 'session' && activeMockSession && (
                <MockInterviewSession
                  session={activeMockSession}
                  onInterviewComplete={handleMockInterviewComplete}
                  onInterviewRejected={handleMockInterviewRejected}
                  onExitSession={handleRestartMockInterview}
                />
              )}

              {mockStage === 'report' && mockReport && (
                <MockInterviewReport
                  report={mockReport}
                  onStartNew={handleRestartMockInterview}
                  onReturnToHistory={() => setActiveTab('history')}
                />
              )}
            </div>
          )}

          {/* TAB 6: AI ONE-TO-ONE INTERVIEW (Voice / Text Conversational HR) */}
          {activeTab === 'ai_one_to_one' && (
            <div>
              {aiInterviewStage === 'setup' && (
                <AIOneToOneSetup
                  resumes={resumesList}
                  activeResumeId={activeResumeId}
                  onInterviewStarted={handleAiInterviewStarted}
                  onNavigateToUpload={() => setActiveTab('upload')}
                  onBack={() => setActiveTab('upload')}
                />
              )}

              {aiInterviewStage === 'interview' && activeAiSession && (
                <AIOneToOneInterview
                  session={activeAiSession}
                  onInterviewComplete={handleAiInterviewCompleted}
                  onCancel={handleRestartAiInterview}
                />
              )}

              {aiInterviewStage === 'report' && aiReport && (
                <AIOneToOneReport
                  report={aiReport}
                  onStartNew={handleRestartAiInterview}
                  onReturnToHistory={() => setActiveTab('history')}
                />
              )}
            </div>
          )}

          {/* TAB 7: AI TECH BOT */}
          {activeTab === 'ai_tech_bot' && (
            <AiTechBot
              activeResumeId={activeResumeId}
              resumes={resumesList}
              onBack={() => setActiveTab('upload')}
            />
          )}

          {/* TAB 8: AI RECOMMENDATIONS */}
          {activeTab === 'recommendations' && (
            <Recommendations
              resumes={resumesList}
              activeResumeId={activeResumeId}
              onNavigateToUpload={() => setActiveTab('upload')}
              onBack={() => setActiveTab('upload')}
            />
          )}

          {/* TAB 9: HISTORY (5 Subtabs: Resumes, ATS, Practice, Mock, AI One-to-One) */}
          {activeTab === 'history' && (
            <History
              onNavigateToUpload={() => setActiveTab('upload')}
              onNavigateToPractice={() => {
                setActiveTab('practice');
                setPracticeStage('setup');
              }}
              onResumePractice={handleResumePractice}
              onNavigateToMock={() => {
                setActiveTab('mock_interview');
                setMockStage('setup');
              }}
              onNavigateToAiInterview={() => {
                setActiveTab('ai_one_to_one');
                setAiInterviewStage('setup');
              }}
            />
          )}

          {/* TAB 10: HELP & SUPPORT */}
          {activeTab === 'support' && (
            <HelpSupport
              user={user}
              onBack={() => setActiveTab('upload')}
            />
          )}
        </main>
      </div>
    </div>
  );
}
