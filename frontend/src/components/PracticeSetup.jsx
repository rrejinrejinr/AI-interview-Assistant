import React, { useState, useEffect } from 'react';
import {
  Layers,
  Calculator,
  BookOpen,
  FileText,
  Play,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { startPracticeApi, getResumeDetailsApi } from '../services/api';

const PRACTICE_CATEGORIES = [
  {
    id: 'aptitude',
    title: 'Aptitude',
    desc: 'Improve quantitative and logical reasoning.',
    detail: 'Arithmetic, percentages, series, time & work, probability & logical puzzles.',
    icon: Calculator,
    color: '#3b82f6'
  },
  {
    id: 'fundamental_concepts',
    title: 'Fundamental Concepts',
    desc: 'Strengthen core CS and programming concepts.',
    detail: 'OOP, DBMS, OS, Computer Networks, Data Structures & Web Architecture.',
    icon: BookOpen,
    color: '#8b5cf6'
  },
  {
    id: 'resume_based',
    title: 'Resume Based',
    desc: 'Practice questions generated from your own resume.',
    detail: 'Tailored questions derived strictly from your verified skills, projects & role.',
    icon: FileText,
    color: '#f59e0b'
  }
];

export default function PracticeSetup({ resumes = [], activeResumeId, onPracticeStarted, onNavigateToUpload, onBack }) {
  const [step, setStep] = useState('landing'); // 'landing' (pick category) | 'configure'
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedResumeId, setSelectedResumeId] = useState(activeResumeId ? String(activeResumeId) : '');
  const [questionCount, setQuestionCount] = useState(10); // 10, 20, 30
  const [difficulty, setDifficulty] = useState('Medium'); // Easy, Medium, Hard
  const [resumeProfile, setResumeProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (activeResumeId) {
      setSelectedResumeId(String(activeResumeId));
    } else {
      setSelectedResumeId('');
      setResumeProfile(null);
    }
  }, [activeResumeId]);

  useEffect(() => {
    if (!selectedResumeId) return;
    getResumeDetailsApi(parseInt(selectedResumeId, 10))
      .then((data) => setResumeProfile(data))
      .catch((err) => console.error('Error fetching resume for practice setup:', err));
  }, [selectedResumeId]);

  const handleSelectCategory = (catId) => {
    setSelectedCategory(catId);
    setError(null);
    setStep('configure');
  };

  const handleStart = async (e) => {
    e.preventDefault();
    if (selectedCategory === 'resume_based' && !selectedResumeId) {
      setError('Please select an uploaded resume document for Resume Based practice.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resumeIdInt = selectedResumeId ? parseInt(selectedResumeId, 10) : undefined;
      const sessionData = await startPracticeApi(
        resumeIdInt,
        parseInt(questionCount, 10),
        difficulty,
        'Technical',
        undefined,
        selectedCategory
      );
      if (onPracticeStarted) {
        onPracticeStarted(sessionData);
      }
    } catch (err) {
      console.error('Start Practice Error:', err);
      const msg = err.response?.data?.detail || 'Failed to initialize practice session.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const currentCatObj = PRACTICE_CATEGORIES.find((c) => c.id === selectedCategory) || PRACTICE_CATEGORIES[0];
  const CategoryIcon = currentCatObj.icon;
  const activeResumeObj = resumes.find(r => String(r.id) === String(selectedResumeId)) || resumeProfile;

  // STEP 1: Practice Zone Landing Screen (4 Clean Cards)
  if (step === 'landing') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="ai-card">
          <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
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
                  <Layers size={22} className="text-primary" />
                  <span>Practice Zone</span>
                </h3>
                <p className="card-subtitle">
                  Choose how you want to practice. Select a category below to configure difficulty and question count.
                </p>
              </div>
            </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--bg-surface-secondary)',
                border: '1px solid var(--border-light)',
                padding: '6px 14px',
                borderRadius: '20px',
                fontSize: '12.5px'
              }}>
                <FileText size={14} className="text-primary" />
                <span style={{ color: 'var(--text-secondary)' }}>Active Resume:</span>
                <b style={{ color: 'var(--text-primary)' }}>{activeResumeObj?.filename || 'No Resume Uploaded'}</b>
              </div>
            </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '16px',
            marginTop: '12px'
          }}>
            {PRACTICE_CATEGORIES.map((cat) => {
              const IconComp = cat.icon;
              return (
                <div
                  key={cat.id}
                  onClick={() => handleSelectCategory(cat.id)}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1.5px solid var(--border-light)',
                    borderRadius: '14px',
                    padding: '20px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--primary)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-light)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                  }}
                >
                  <div>
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '10px',
                      background: 'var(--primary-light)',
                      color: 'var(--primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '14px'
                    }}>
                      <IconComp size={22} />
                    </div>

                    <h4 style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 6px' }}>
                      {cat.title}
                    </h4>

                    <p style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', margin: '0 0 8px', lineHeight: '1.4' }}>
                      {cat.desc}
                    </p>

                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0, lineHeight: '1.45' }}>
                      {cat.detail}
                    </p>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: '18px',
                    paddingTop: '12px',
                    borderTop: '1px solid var(--border-light)',
                    fontSize: '12.5px',
                    fontWeight: '700',
                    color: 'var(--primary)'
                  }}>
                    <span>Select Category</span>
                    <ChevronRight size={16} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // STEP 2: Configure Category, Difficulty & Question Count (Aptitude, Fundamental Concepts, Resume Based)
  return (
    <div className="ai-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <CategoryIcon size={13} />
              <span>{currentCatObj.title}</span>
            </span>
          </div>
          <h3 className="card-title">
            <span>Configure Practice Session</span>
          </h3>
          <p className="card-subtitle">
            {currentCatObj.desc}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setStep('landing')}
          className="btn-secondary"
          style={{ padding: '8px 14px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ArrowLeft size={14} />
          <span>Change Category</span>
        </button>
      </div>

      <form onSubmit={handleStart} style={{ display: 'flex', flexDirection: 'column', gap: '22px', marginTop: '10px' }}>
        {/* If Resume Based: Active Resume Preview */}
        {selectedCategory === 'resume_based' && (
          <div>
            <label className="form-label">Active Candidate Resume</label>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-surface-secondary)',
              border: '1px solid var(--border-light)',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '13px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <FileText size={16} className="text-primary" style={{ flexShrink: 0 }} />
                <span style={{ fontWeight: '700', color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                  {activeResumeObj?.filename || (selectedResumeId ? `Resume #${selectedResumeId}` : 'No Resume Uploaded')}
                </span>
              </div>
            </div>

            {!selectedResumeId && (
              <div style={{ fontSize: '12.5px', color: 'var(--danger)', marginTop: '8px' }}>
                Please upload your resume to continue. <button type="button" onClick={onNavigateToUpload} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', textDecoration: 'underline', fontWeight: '700', padding: 0 }}>Upload Resume</button>
              </div>
            )}

            {resumeProfile && (
              <div style={{
                background: 'var(--bg-surface-secondary)',
                border: '1px solid var(--border-light)',
                padding: '12px 16px',
                borderRadius: '10px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '10px',
                marginTop: '10px'
              }}>
                <div>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)' }}>PREDICTED ROLE</span>
                  <div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--primary)' }}>
                    {resumeProfile.predicted_role || 'Software Engineer'}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)' }}>EXTRACTED SKILLS</span>
                  <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)' }}>
                    {resumeProfile.skills_list?.length || 0} skills detected
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Difficulty Selection: Easy, Medium, Hard */}
        <div>
          <label className="form-label">Select Difficulty Level *</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '4px' }}>
            {[
              { id: 'Easy', label: 'Easy', desc: 'Core fundamentals & direct questions' },
              { id: 'Medium', label: 'Medium', desc: 'Practical reasoning & scenario problems' },
              { id: 'Hard', label: 'Hard', desc: 'Complex multi-step & optimization challenges' }
            ].map((d) => {
              const isSelected = difficulty === d.id;
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDifficulty(d.id)}
                  style={{
                    padding: '14px 12px',
                    borderRadius: '12px',
                    border: isSelected ? '2px solid var(--primary)' : '1.5px solid var(--border-light)',
                    background: isSelected ? 'var(--primary-light)' : 'var(--bg-surface)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-primary)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.18s ease'
                  }}
                >
                  <div style={{ fontWeight: '800', fontSize: '14px', marginBottom: '2px' }}>{d.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.3' }}>{d.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Number of Questions: 10, 20, 30 */}
        <div>
          <label className="form-label">Number of Questions *</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '4px' }}>
            {[10, 20, 30].map((count) => {
              const isSelected = questionCount === count;
              return (
                <button
                  key={count}
                  type="button"
                  onClick={() => setQuestionCount(count)}
                  style={{
                    padding: '14px 12px',
                    borderRadius: '12px',
                    border: isSelected ? '2px solid var(--primary)' : '1.5px solid var(--border-light)',
                    background: isSelected ? 'var(--primary-light)' : 'var(--bg-surface)',
                    color: isSelected ? 'var(--primary)' : 'var(--text-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '2px',
                    transition: 'all 0.18s ease'
                  }}
                >
                  <span style={{ fontSize: '18px', fontWeight: '900' }}>{count}</span>
                  <span style={{ fontSize: '11.5px', fontWeight: '700' }}>Questions</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Row */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
          <button
            type="button"
            onClick={() => setStep('landing')}
            className="btn-secondary"
            style={{ padding: '12px 20px', fontSize: '13px' }}
          >
            Back
          </button>

          <button
            type="submit"
            disabled={loading || (selectedCategory === 'resume_based' && !selectedResumeId)}
            className="btn-primary"
            style={{
              flex: 1,
              padding: '12px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '800'
            }}
          >
            <Play size={16} />
            <span>{loading ? 'Synthesizing Questions...' : `Start Practice (${questionCount} Questions)`}</span>
          </button>
        </div>
      </form>

      {error && (
        <div className="alert-error" style={{ marginTop: '16px' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
