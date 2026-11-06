import React from 'react';
import {
  FileUp,
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
  LogOut,
  BrainCircuit,
  FileText
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    title: 'Resume & Profile',
    items: [
      { id: 'upload', label: 'Resume Upload', icon: FileUp },
      { id: 'extracted_skills', label: 'Extracted Skills', icon: Layers },
      { id: 'resume_builder', label: 'Resume Builder', icon: FileText }
    ]
  },
  {
    title: 'Interview & Practice',
    items: [
      { id: 'ats', label: 'ATS Analysis', icon: Target },
      { id: 'practice', label: 'Practice', icon: Layers },
      { id: 'mock_interview', label: 'Mock Interview', icon: Video },
      { id: 'ai_one_to_one', label: 'HR Interview', icon: MessagesSquare }
    ]
  },
  {
    title: 'AI Intelligence & Records',
    items: [
      { id: 'ai_tech_bot', label: 'AI Tech Bot', icon: Bot },
      { id: 'recommendations', label: 'AI Recommendations', icon: Compass },
      { id: 'history', label: 'History', icon: HistoryIcon },
      { id: 'support', label: 'Help & Support', icon: HelpCircle }
    ]
  }
];


export default function Sidebar({
  activeTab,
  onSelectTab,
  user,
  onLogout,
  resumesCount,
  theme,
  onToggleTheme,
  isOpen,
  onCloseMobile
}) {
  const userInitials = (user?.name || 'Candidate')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            zIndex: 35,
            backdropFilter: 'blur(2px)'
          }}
        />
      )}

      <aside className={`app-sidebar ${isOpen ? 'open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <BrainCircuit size={20} color="#ffffff" />
          </div>
          <div>
            <h2 className="sidebar-title">AI Interview</h2>
            <span className="sidebar-subtitle">Assistant Pro</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          {NAV_SECTIONS.map((section, idx) => (
            <div key={idx}>
              <div className="nav-section-title">{section.title}</div>
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      onSelectTab(item.id);
                      if (onCloseMobile) onCloseMobile();
                    }}
                  >
                    <span className="nav-icon">
                      <Icon size={18} />
                    </span>
                    <span>{item.label}</span>
                    {item.id === 'upload' && resumesCount > 0 && (
                      <span className="nav-badge">{resumesCount}</span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer: Theme, User & Logout */}
        <div className="sidebar-footer">
          {/* Light / Dark Mode Toggle */}
          <div className="theme-toggle-bar">
            <button
              className={`theme-btn ${theme === 'light' ? 'active' : ''}`}
              onClick={() => onToggleTheme('light')}
            >
              <Sun size={14} />
              <span>Light</span>
            </button>
            <button
              className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
              onClick={() => onToggleTheme('dark')}
            >
              <Moon size={14} />
              <span>Dark</span>
            </button>
          </div>

          {/* User Profile Capsule */}
          <div
            className="user-profile-capsule"
            onClick={() => {
              onSelectTab('candidate_profile');
              if (onCloseMobile) onCloseMobile();
            }}
            style={{ cursor: 'pointer' }}
            title="View User Profile"
          >
            <div className="user-avatar">{userInitials}</div>
            <div className="user-info">
              <span className="user-name">{user?.name || 'Candidate'}</span>
              <span className="user-email">{user?.email || ''}</span>
            </div>
          </div>

          {/* Logout */}
          <button className="btn-logout" onClick={onLogout}>
            <LogOut size={15} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}