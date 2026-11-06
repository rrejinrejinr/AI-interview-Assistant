import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Mail,
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Eye,
  Settings,
  User,
  Briefcase,
  GraduationCap,
  Code,
  Award,
  Layers,
  ArrowLeft,
  History,
  Send,
  Sparkles
} from 'lucide-react';
import {
  generateResumePdfApi,
  getBuiltResumesHistoryApi,
  resendResumeEmailApi,
  fetchResumePdfBlobApi,
  getResumeDownloadUrl,
  getActiveResumeApi,
  getResumeDetailsApi
} from '../services/api';

const TEMPLATES = [
  { id: 'Modern', name: 'Modern', desc: 'Contemporary header banner card with primary accent and skill badges' },
  { id: 'Simple', name: 'Simple ATS', desc: 'Clean, linear ATS layout with classic horizontal divider rules' },
  { id: 'Minimal', name: 'Minimal', desc: 'Typography-focused, airy whitespace layout with elegant simplicity' },
  { id: 'Fresher', name: 'Fresher / Graduate', desc: 'Optimized for students; highlights Education and Projects first' },
  { id: 'Technical', name: 'Technical / Engineer', desc: 'Categorized technical architecture, languages, and system skills first' }
];

const FONTS = [
  { id: 'Helvetica', name: 'Helvetica (Standard Sans-Serif)' },
  { id: 'Arial', name: 'Arial (Clean ATS)' },
  { id: 'Calibri', name: 'Calibri (Modern Executive)' },
  { id: 'Times New Roman', name: 'Times New Roman (Classic Serif)' },
  { id: 'Georgia', name: 'Georgia (Editorial Serif)' }
];

const COLOR_PRESETS = [
  { name: 'Slate Navy', value: '#1e293b' },
  { name: 'Royal Blue', value: '#1e3a8a' },
  { name: 'Deep Emerald', value: '#065f46' },
  { name: 'Indigo', value: '#3730a3' },
  { name: 'Charcoal', value: '#27272a' }
];

export default function ResumeBuilder({ user, onBack }) {
  const [activeTab, setActiveTab] = useState('editor'); // 'editor' | 'history'
  const [editorSection, setEditorSection] = useState('personal'); // 'design' | 'personal' | 'summary' | 'skills' | 'experience' | 'projects' | 'education' | 'extras'
  
  // Resume Data State — Initialized completely empty
  const [templateId, setTemplateId] = useState('Modern');
  const [fontFamily, setFontFamily] = useState('Helvetica');
  const [primaryColor, setPrimaryColor] = useState('#1e293b');
  const [resumeTitle, setResumeTitle] = useState('');

  const [personalInfo, setPersonalInfo] = useState({
    name: '',
    title: '',
    email: '',
    phone: '',
    location: '',
    linkedin: '',
    github: '',
    portfolio: ''
  });

  const [summary, setSummary] = useState('');
  const [skills, setSkills] = useState(''); // Flat comma-separated skills (starts completely empty)
  const [customCategories, setCustomCategories] = useState([]); // Optional custom domains [{ name: '', items: '' }]
  const [experience, setExperience] = useState([]);
  const [projects, setProjects] = useState([]);
  const [education, setEducation] = useState([]);
  const [certifications, setCertifications] = useState([]);
  const [achievements, setAchievements] = useState([]);

  // Auto-fill state
  const [autofillLoading, setAutofillLoading] = useState(false);
  const [autofillMessage, setAutofillMessage] = useState(null);

  const handleAutofillFromActiveResume = async () => {
    setAutofillLoading(true);
    setAutofillMessage(null);
    try {
      const activeRes = await getActiveResumeApi();
      if (!activeRes || !activeRes.active_resume_id) {
        setAutofillMessage({ type: 'warning', text: 'No active resume selected. Please upload a resume and set it as active first.' });
        return;
      }
      const details = await getResumeDetailsApi(activeRes.active_resume_id);
      if (details) {
        setPersonalInfo(prev => ({
          ...prev,
          name: details.candidate_info?.name || prev.name || '',
          email: details.candidate_info?.email || prev.email || '',
          phone: details.candidate_info?.phone || prev.phone || '',
          title: details.predicted_role || prev.title || 'Software Engineer',
          location: details.candidate_info?.location || prev.location || '',
          linkedin: details.candidate_info?.linkedin || prev.linkedin || '',
          github: details.candidate_info?.github || prev.github || '',
          portfolio: details.candidate_info?.portfolio || prev.portfolio || ''
        }));

        if (details.candidate_info?.summary) {
          setSummary(details.candidate_info.summary);
        }

        if (details.skills_list && details.skills_list.length > 0) {
          setSkills(details.skills_list.join(', '));
          setCustomCategories([]);
        }

        setAutofillMessage({
          type: 'success',
          text: `Auto-filled information from Active Resume (${details.filename || 'Active Resume'}).`
        });
      }
    } catch (err) {
      console.error('Autofill error:', err);
      setAutofillMessage({ type: 'error', text: 'Unable to auto-fill from active resume.' });
    } finally {
      setAutofillLoading(false);
      setTimeout(() => setAutofillMessage(null), 6000);
    }
  };

  // Generation & History State
  const [generating, setGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState(null);
  const [generateError, setGenerateError] = useState(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [loadingPdfBlob, setLoadingPdfBlob] = useState(false);
  const [previewResumeItem, setPreviewResumeItem] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [resendingId, setResendingId] = useState(null);
  const [resendStatus, setResendStatus] = useState(null);

  useEffect(() => {
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
    };
  }, [pdfBlobUrl]);

  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  const loadPdfBlob = async (resumeId) => {
    setLoadingPdfBlob(true);
    try {
      const blobData = await fetchResumePdfBlobApi(resumeId);
      const blob = new Blob([blobData], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setPdfBlobUrl(prevUrl => {
        if (prevUrl) URL.revokeObjectURL(prevUrl);
        return url;
      });
      return url;
    } catch (err) {
      console.error('Error fetching resume PDF blob:', err);
      return null;
    } finally {
      setLoadingPdfBlob(false);
    }
  };

  const triggerDownload = (url, filename) => {
    if (!url) return;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'Resume.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadDirect = async (resumeId, filename) => {
    try {
      const blobData = await fetchResumePdfBlobApi(resumeId);
      const blob = new Blob([blobData], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      triggerDownload(url, filename || `Resume_${resumeId}.pdf`);
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      console.error('Error downloading resume:', err);
    }
  };

  const handlePreviewHistoryResume = async (resumeItem) => {
    setPreviewResumeItem(resumeItem);
    await loadPdfBlob(resumeItem.id);
  };

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getBuiltResumesHistoryApi();
      setHistoryList(data);
    } catch (err) {
      console.error('Error fetching resume history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleGeneratePdf = async () => {
    setGenerating(true);
    setGenerateError(null);
    setGenerateResult(null);

    // Prepare skills representation without artificial category names
    let formattedSkills;
    const validCustom = customCategories.filter(c => c.name.trim() && c.items.trim());
    if (validCustom.length > 0) {
      const catObj = {};
      if (skills && skills.trim()) {
        catObj['General'] = skills.trim();
      }
      validCustom.forEach(c => {
        catObj[c.name.trim()] = c.items.trim();
      });
      formattedSkills = catObj;
    } else {
      formattedSkills = skills.trim();
    }

    const payload = {
      template_id: templateId,
      font_family: fontFamily,
      primary_color: primaryColor,
      title: resumeTitle || `${personalInfo.name || 'Candidate'} Resume`,
      personal_info: personalInfo,
      summary: summary,
      skills: formattedSkills,
      experience: experience,
      projects: projects,
      education: education,
      certifications: certifications,
      achievements: achievements,
      custom_sections: []
    };

    try {
      const res = await generateResumePdfApi(payload);
      setGenerateResult(res);
      const filename = `${personalInfo.name || 'Candidate'}_Resume_${templateId}.pdf`;
      const blobUrl = await loadPdfBlob(res.resume_id);
      if (blobUrl) {
        triggerDownload(blobUrl, filename);
      }
    } catch (err) {
      console.error('PDF Generation Error:', err);
      setGenerateError(err.response?.data?.detail || err.message || 'Failed to generate resume PDF. Please check your inputs and try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleResendEmail = async (resumeId) => {
    setResendingId(resumeId);
    setResendStatus(null);
    try {
      const res = await resendResumeEmailApi(resumeId);
      setResendStatus({ success: res.email_sent, msg: res.message || res.email_status });
      if (activeTab === 'history') loadHistory();
    } catch (err) {
      console.error('Resend email error:', err);
      setResendStatus({ success: false, msg: 'Failed to send email. Please check your SMTP settings.' });
    } finally {
      setResendingId(null);
    }
  };

  // Helper functions for updating lists
  const handleAddExperience = () => {
    setExperience(prev => [
      ...prev,
      {
        title: '',
        company: '',
        location: '',
        duration: '',
        bullets: ['']
      }
    ]);
  };

  const handleRemoveExperience = (idx) => {
    setExperience(prev => prev.filter((_, i) => i !== idx));
  };

  const handleAddProject = () => {
    setProjects(prev => [
      ...prev,
      {
        name: '',
        tech_stack: '',
        duration: '',
        link: '',
        bullets: ['']
      }
    ]);
  };

  const handleRemoveProject = (idx) => {
    setProjects(prev => prev.filter((_, i) => i !== idx));
  };

  const handleAddEducation = () => {
    setEducation(prev => [
      ...prev,
      {
        degree: '',
        institution: '',
        location: '',
        duration: '',
        grade: ''
      }
    ]);
  };

  const handleRemoveEducation = (idx) => {
    setEducation(prev => prev.filter((_, i) => i !== idx));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header & Navigation Bar */}
      <div className="ai-card" style={{ padding: '18px 22px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
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
              <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <FileText size={22} className="text-primary" />
                <span>ATS-Compliant Resume Builder</span>
              </h3>
              <p className="card-subtitle" style={{ margin: '2px 0 0' }}>
                Build professional, single/multi-page A4 resumes with 5 structural templates, live preview, direct PDF export, and automatic email delivery.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => setActiveTab('editor')}
              className={`btn-secondary ${activeTab === 'editor' ? 'active' : ''}`}
              style={{
                background: activeTab === 'editor' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                color: activeTab === 'editor' ? 'white' : 'var(--text-secondary)',
                borderColor: activeTab === 'editor' ? 'var(--primary)' : 'var(--border-light)',
                padding: '8px 14px',
                fontSize: '12.5px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Eye size={14} />
              <span>Resume Editor & Live Preview</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`btn-secondary ${activeTab === 'history' ? 'active' : ''}`}
              style={{
                background: activeTab === 'history' ? 'var(--primary)' : 'var(--bg-surface-secondary)',
                color: activeTab === 'history' ? 'white' : 'var(--text-secondary)',
                borderColor: activeTab === 'history' ? 'var(--primary)' : 'var(--border-light)',
                padding: '8px 14px',
                fontSize: '12.5px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <History size={14} />
              <span>Built Resumes History</span>
            </button>
          </div>
        </div>
      </div>

      {/* GENERATE RESULT BANNER & PDF VIEWER */}
      {generateResult && (
        <div className="ai-card" style={{ padding: '20px', border: '1.5px solid var(--primary-border, rgba(59, 130, 246, 0.4))', background: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={22} className="text-primary" />
              <div>
                <div style={{ fontWeight: '800', fontSize: '15px', color: 'var(--text-primary)' }}>Resume PDF Generated & Compiled Successfully!</div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Template: <b>{generateResult.template_id}</b> • Font: <b>{generateResult.font_family}</b> • Document ID #{generateResult.resume_id}
                </div>
                <div style={{ fontSize: '12px', marginTop: '3px', color: 'var(--text-muted)' }}>
                  {generateResult.email_sent ? (
                    <span>Email delivery: Dispatched PDF copy to <b>{generateResult.user_email}</b></span>
                  ) : (
                    <span>Email status: {generateResult.email_status || 'PDF saved to your account'}</span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => handleDownloadDirect(generateResult.resume_id, `${personalInfo.name || 'Candidate'}_Resume_${templateId}.pdf`)}
                className="btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '13px' }}
              >
                <Download size={15} />
                <span>Download PDF</span>
              </button>
              <button
                type="button"
                onClick={() => handleResendEmail(generateResult.resume_id)}
                disabled={resendingId === generateResult.resume_id}
                className="btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', fontSize: '13px' }}
              >
                <Mail size={15} />
                <span>{resendingId === generateResult.resume_id ? 'Sending...' : 'Email Copy'}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setGenerateResult(null);
                  if (pdfBlobUrl) {
                    URL.revokeObjectURL(pdfBlobUrl);
                    setPdfBlobUrl(null);
                  }
                }}
                className="btn-secondary"
                style={{ padding: '8px 14px', fontSize: '13px' }}
              >
                Continue Editing
              </button>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
              Compiled PDF Document Preview
            </div>
            {loadingPdfBlob ? (
              <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-surface-secondary)', borderRadius: '8px', color: 'var(--text-muted)' }}>
                Loading PDF preview...
              </div>
            ) : pdfBlobUrl ? (
              <iframe
                src={pdfBlobUrl}
                title="Compiled Resume PDF"
                style={{
                  width: '100%',
                  height: '540px',
                  border: '1px solid var(--border-light)',
                  borderRadius: '8px',
                  background: '#525659'
                }}
              />
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', background: 'var(--bg-surface-secondary)', borderRadius: '8px' }}>
                <p style={{ color: 'var(--text-secondary)', margin: '0 0 10px' }}>PDF generated successfully.</p>
                <button
                  type="button"
                  onClick={() => loadPdfBlob(generateResult.resume_id)}
                  className="btn-secondary"
                  style={{ fontSize: '12.5px', padding: '6px 14px' }}
                >
                  Reload Preview
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {generateError && (
        <div className="alert-error" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle size={18} />
          <span>{generateError}</span>
        </div>
      )}

      {resendStatus && (
        <div className={resendStatus.success ? 'alert-success' : 'alert-error'} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {resendStatus.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{resendStatus.msg}</span>
        </div>
      )}

      {/* TAB 1: RESUME EDITOR & LIVE PREVIEW (2 COLUMNS) */}
      {activeTab === 'editor' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 1.1fr) minmax(360px, 0.9fr)', gap: '20px', alignItems: 'start' }}>
          
          {/* LEFT COLUMN: FORM EDITOR */}
          <div className="ai-card" style={{ padding: '20px' }}>
            {/* Editor Top Toolbar with Optional Auto-fill */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
              <span style={{ fontSize: '13px', fontWeight: '800', color: 'var(--text-primary)' }}>
                Editor Sections
              </span>
              <button
                type="button"
                onClick={handleAutofillFromActiveResume}
                disabled={autofillLoading}
                className="btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  fontSize: '12px',
                  borderColor: 'var(--primary-border, rgba(59, 130, 246, 0.3))',
                  color: 'var(--primary)',
                  background: 'var(--primary-light, rgba(59, 130, 246, 0.08))'
                }}
              >
                <Sparkles size={13} />
                <span>{autofillLoading ? 'Fetching active resume...' : 'Auto-fill from Active Resume'}</span>
              </button>
            </div>

            {autofillMessage && (
              <div
                className={autofillMessage.type === 'success' ? 'alert-success' : autofillMessage.type === 'warning' ? 'alert-warning' : 'alert-error'}
                style={{ marginBottom: '12px', padding: '8px 12px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                {autofillMessage.type === 'success' ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                <span>{autofillMessage.text}</span>
              </div>
            )}

            {/* Section Tabs */}
            <div style={{
              display: 'flex',
              gap: '6px',
              overflowX: 'auto',
              paddingBottom: '12px',
              marginBottom: '16px',
              borderBottom: '1px solid var(--border-light)'
            }}>
              {[
                { id: 'design', label: 'Design & Font', icon: Settings },
                { id: 'personal', label: 'Contact', icon: User },
                { id: 'summary', label: 'Summary', icon: FileText },
                { id: 'skills', label: 'Skills', icon: Layers },
                { id: 'experience', label: 'Experience', icon: Briefcase },
                { id: 'projects', label: 'Projects', icon: Code },
                { id: 'education', label: 'Education', icon: GraduationCap },
                { id: 'extras', label: 'Certifications', icon: Award }
              ].map(sec => {
                const Icon = sec.icon;
                const isActiveSec = editorSection === sec.id;
                return (
                  <button
                    key={sec.id}
                    onClick={() => setEditorSection(sec.id)}
                    style={{
                      background: isActiveSec ? 'var(--primary-light, rgba(59, 130, 246, 0.1))' : 'transparent',
                      color: isActiveSec ? 'var(--primary)' : 'var(--text-secondary)',
                      border: `1px solid ${isActiveSec ? 'var(--primary-border, rgba(59, 130, 246, 0.3))' : 'transparent'}`,
                      borderRadius: '8px',
                      padding: '7px 12px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <Icon size={14} />
                    <span>{sec.label}</span>
                  </button>
                );
              })}
            </div>

            {/* SECTION 1: DESIGN & TEMPLATES */}
            {editorSection === 'design' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <div>
                  <label className="form-label" style={{ fontWeight: '800' }}>Choose Template Style</label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px' }}>
                    {TEMPLATES.map(t => (
                      <div
                        key={t.id}
                        onClick={() => setTemplateId(t.id)}
                        style={{
                          background: templateId === t.id ? 'var(--primary-light, rgba(59, 130, 246, 0.08))' : 'var(--bg-surface-secondary)',
                          border: `1.5px solid ${templateId === t.id ? 'var(--primary)' : 'var(--border-light)'}`,
                          borderRadius: '10px',
                          padding: '12px 14px',
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: '800', fontSize: '13.5px', color: 'var(--text-primary)' }}>{t.name}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>{t.desc}</div>
                        </div>
                        {templateId === t.id && <CheckCircle2 size={18} className="text-primary" />}
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div>
                    <label className="form-label" style={{ fontWeight: '800' }}>Font Family</label>
                    <select
                      value={fontFamily}
                      onChange={(e) => setFontFamily(e.target.value)}
                      className="form-select"
                    >
                      {FONTS.map(f => (
                        <option key={f.id} value={f.id}>{f.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="form-label" style={{ fontWeight: '800' }}>Primary Accent Color</label>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px' }}>
                      {COLOR_PRESETS.map(c => (
                        <button
                          key={c.value}
                          type="button"
                          onClick={() => setPrimaryColor(c.value)}
                          title={c.name}
                          style={{
                            width: '26px',
                            height: '26px',
                            borderRadius: '50%',
                            background: c.value,
                            border: primaryColor === c.value ? '2px solid white' : '1px solid var(--border-light)',
                            outline: primaryColor === c.value ? '2px solid var(--primary)' : 'none',
                            cursor: 'pointer'
                          }}
                        />
                      ))}
                      <input
                        type="color"
                        value={primaryColor}
                        onChange={(e) => setPrimaryColor(e.target.value)}
                        style={{ width: '32px', height: '32px', padding: 0, border: 'none', background: 'transparent', cursor: 'pointer' }}
                        title="Custom Color"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="form-label">Resume Document Title</label>
                  <input
                    type="text"
                    value={resumeTitle}
                    onChange={(e) => setResumeTitle(e.target.value)}
                    className="form-input"
                    placeholder="e.g. John Doe - Full Stack Developer"
                  />
                </div>
              </div>
            )}

            {/* SECTION 2: PERSONAL / CONTACT */}
            {editorSection === 'personal' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label className="form-label">Full Name *</label>
                    <input
                      type="text"
                      value={personalInfo.name}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, name: e.target.value })}
                      className="form-input"
                      placeholder="e.g. Alex Mercer"
                      required
                    />
                  </div>

                  <div>
                    <label className="form-label">Target Professional Title</label>
                    <input
                      type="text"
                      value={personalInfo.title}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, title: e.target.value })}
                      className="form-input"
                      placeholder="e.g. Senior Software Engineer"
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label className="form-label">Email Address *</label>
                    <input
                      type="email"
                      value={personalInfo.email}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                      className="form-input"
                      placeholder="alex@example.com"
                      required
                    />
                  </div>

                  <div>
                    <label className="form-label">Phone Number</label>
                    <input
                      type="text"
                      value={personalInfo.phone}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, phone: e.target.value })}
                      className="form-input"
                      placeholder="+1 (555) 012-3456"
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Location (City, State / Country)</label>
                  <input
                    type="text"
                    value={personalInfo.location}
                    onChange={(e) => setPersonalInfo({ ...personalInfo, location: e.target.value })}
                    className="form-input"
                    placeholder="e.g. Austin, TX"
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label className="form-label">LinkedIn URL</label>
                    <input
                      type="text"
                      value={personalInfo.linkedin}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, linkedin: e.target.value })}
                      className="form-input"
                      placeholder="linkedin.com/in/alex"
                    />
                  </div>

                  <div>
                    <label className="form-label">GitHub URL</label>
                    <input
                      type="text"
                      value={personalInfo.github}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, github: e.target.value })}
                      className="form-input"
                      placeholder="github.com/alex"
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Portfolio Website / Link</label>
                  <input
                    type="text"
                    value={personalInfo.portfolio}
                    onChange={(e) => setPersonalInfo({ ...personalInfo, portfolio: e.target.value })}
                    className="form-input"
                    placeholder="alexmercer.dev"
                  />
                </div>
              </div>
            )}

            {/* SECTION 3: SUMMARY */}
            {editorSection === 'summary' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label className="form-label">Executive / Professional Summary</label>
                  <textarea
                    rows={7}
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    className="form-textarea"
                    placeholder="Write a concise 3-4 sentence professional summary highlighting your core skills, years of experience, and primary achievements..."
                  />
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Tip: Focus on quantifiable impact and primary technologies matching your target job role.
                  </div>
                </div>
              </div>
            )}

            {/* SECTION 4: SKILLS */}
            {editorSection === 'skills' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label className="form-label" style={{ fontWeight: '800' }}>
                    Technical Skills (Comma-separated)
                  </label>
                  <textarea
                    rows={4}
                    value={skills}
                    onChange={(e) => setSkills(e.target.value)}
                    className="form-textarea"
                    placeholder="e.g. Java, Python, React, FastAPI, PostgreSQL, Docker, Git, REST APIs, System Design"
                  />
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Enter your skills separated by commas. These will be formatted naturally on your resume without artificial category headers.
                  </div>
                </div>

                {/* Optional Custom Categories */}
                <div style={{ borderTop: '1px dashed var(--border-light)', paddingTop: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label className="form-label" style={{ fontWeight: '700', margin: 0 }}>
                      Categorized Domains (Optional)
                    </label>
                    <button
                      type="button"
                      onClick={() => setCustomCategories(prev => [...prev, { name: '', items: '' }])}
                      className="btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '11.5px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Plus size={13} />
                      <span>Add Domain Category</span>
                    </button>
                  </div>

                  {customCategories.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {customCategories.map((cat, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-surface-secondary)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <input
                              type="text"
                              value={cat.name}
                              onChange={(e) => {
                                const updated = [...customCategories];
                                updated[idx].name = e.target.value;
                                setCustomCategories(updated);
                              }}
                              placeholder="Domain (e.g. Backend, Cloud, Databases)"
                              style={{ fontWeight: '700', fontSize: '12.5px', background: 'transparent', border: 'none', color: 'var(--primary)', width: '80%' }}
                            />
                            <button
                              type="button"
                              onClick={() => setCustomCategories(prev => prev.filter((_, i) => i !== idx))}
                              style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}
                              title="Delete Domain"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                          <input
                            type="text"
                            value={cat.items}
                            onChange={(e) => {
                              const updated = [...customCategories];
                              updated[idx].items = e.target.value;
                              setCustomCategories(updated);
                            }}
                            className="form-input"
                            placeholder="Comma-separated items (e.g. PostgreSQL, Redis, MongoDB)"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* SECTION 5: EXPERIENCE */}
            {editorSection === 'experience' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {experience.map((exp, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-surface-secondary)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontWeight: '800', fontSize: '13px', color: 'var(--text-primary)' }}>Role #{idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveExperience(idx)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}
                        title="Delete Role"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="text"
                        placeholder="Job Title"
                        value={exp.title}
                        onChange={(e) => {
                          const updated = [...experience];
                          updated[idx].title = e.target.value;
                          setExperience(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Company Name"
                        value={exp.company}
                        onChange={(e) => {
                          const updated = [...experience];
                          updated[idx].company = e.target.value;
                          setExperience(updated);
                        }}
                        className="form-input"
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="text"
                        placeholder="Location (e.g. San Francisco, CA)"
                        value={exp.location}
                        onChange={(e) => {
                          const updated = [...experience];
                          updated[idx].location = e.target.value;
                          setExperience(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Duration (e.g. Jun 2022 - Present)"
                        value={exp.duration}
                        onChange={(e) => {
                          const updated = [...experience];
                          updated[idx].duration = e.target.value;
                          setExperience(updated);
                        }}
                        className="form-input"
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px', display: 'block' }}>
                        Responsibility Bullet Points (one per line)
                      </label>
                      <textarea
                        rows={3}
                        value={Array.isArray(exp.bullets) ? exp.bullets.join('\n') : exp.bullets}
                        onChange={(e) => {
                          const updated = [...experience];
                          updated[idx].bullets = e.target.value.split('\n');
                          setExperience(updated);
                        }}
                        className="form-textarea"
                        placeholder="Enter accomplishment bullet points..."
                      />
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={handleAddExperience}
                  className="btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px' }}
                >
                  <Plus size={15} />
                  <span>Add Work Experience</span>
                </button>
              </div>
            )}

            {/* SECTION 6: PROJECTS */}
            {editorSection === 'projects' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {projects.map((proj, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-surface-secondary)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontWeight: '800', fontSize: '13px', color: 'var(--text-primary)' }}>Project #{idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveProject(idx)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}
                        title="Delete Project"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="text"
                        placeholder="Project Name"
                        value={proj.name}
                        onChange={(e) => {
                          const updated = [...projects];
                          updated[idx].name = e.target.value;
                          setProjects(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Tech Stack (e.g. React, Node, PostgreSQL)"
                        value={proj.tech_stack}
                        onChange={(e) => {
                          const updated = [...projects];
                          updated[idx].tech_stack = e.target.value;
                          setProjects(updated);
                        }}
                        className="form-input"
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="text"
                        placeholder="Duration / Date"
                        value={proj.duration}
                        onChange={(e) => {
                          const updated = [...projects];
                          updated[idx].duration = e.target.value;
                          setProjects(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Project Link / Repo URL"
                        value={proj.link}
                        onChange={(e) => {
                          const updated = [...projects];
                          updated[idx].link = e.target.value;
                          setProjects(updated);
                        }}
                        className="form-input"
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '4px', display: 'block' }}>
                        Project Highlights (one per line)
                      </label>
                      <textarea
                        rows={3}
                        value={Array.isArray(proj.bullets) ? proj.bullets.join('\n') : proj.bullets}
                        onChange={(e) => {
                          const updated = [...projects];
                          updated[idx].bullets = e.target.value.split('\n');
                          setProjects(updated);
                        }}
                        className="form-textarea"
                        placeholder="Engineered high throughput API..."
                      />
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={handleAddProject}
                  className="btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px' }}
                >
                  <Plus size={15} />
                  <span>Add Project</span>
                </button>
              </div>
            )}

            {/* SECTION 7: EDUCATION */}
            {editorSection === 'education' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {education.map((edu, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-surface-secondary)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{ fontWeight: '800', fontSize: '13px', color: 'var(--text-primary)' }}>Education #{idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveEducation(idx)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}
                        title="Delete Education"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="text"
                        placeholder="Degree / Certificate (e.g. B.S. in CS)"
                        value={edu.degree}
                        onChange={(e) => {
                          const updated = [...education];
                          updated[idx].degree = e.target.value;
                          setEducation(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Institution / University"
                        value={edu.institution}
                        onChange={(e) => {
                          const updated = [...education];
                          updated[idx].institution = e.target.value;
                          setEducation(updated);
                        }}
                        className="form-input"
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                      <input
                        type="text"
                        placeholder="Year / Duration (e.g. 2020 - 2024)"
                        value={edu.duration}
                        onChange={(e) => {
                          const updated = [...education];
                          updated[idx].duration = e.target.value;
                          setEducation(updated);
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Score / GPA (e.g. GPA: 3.8/4.0)"
                        value={edu.grade}
                        onChange={(e) => {
                          const updated = [...education];
                          updated[idx].grade = e.target.value;
                          setEducation(updated);
                        }}
                        className="form-input"
                      />
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={handleAddEducation}
                  className="btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px' }}
                >
                  <Plus size={15} />
                  <span>Add Education Record</span>
                </button>
              </div>
            )}

            {/* SECTION 8: CERTIFICATIONS & ACHIEVEMENTS */}
            {editorSection === 'extras' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label className="form-label" style={{ fontWeight: '800' }}>Certifications (one per line)</label>
                  <textarea
                    rows={4}
                    value={certifications.join('\n')}
                    onChange={(e) => setCertifications(e.target.value.split('\n'))}
                    className="form-textarea"
                    placeholder="AWS Certified Solutions Architect..."
                  />
                </div>

                <div>
                  <label className="form-label" style={{ fontWeight: '800' }}>Key Achievements & Honors (one per line)</label>
                  <textarea
                    rows={4}
                    value={achievements.join('\n')}
                    onChange={(e) => setAchievements(e.target.value.split('\n'))}
                    className="form-textarea"
                    placeholder="Hackathon Winner, Dean's Honor List..."
                  />
                </div>
              </div>
            )}

            {/* Generate PDF Button in Left Column */}
            <div style={{ marginTop: '22px', borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
              <button
                type="button"
                onClick={handleGeneratePdf}
                disabled={generating}
                className="btn-primary"
                style={{ width: '100%', padding: '14px', fontSize: '14px', fontWeight: '800', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
              >
                <Download size={18} />
                <span>{generating ? 'Compiling ReportLab PDF & Dispatching Email...' : 'Generate & Download PDF Resume'}</span>
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN: LIVE ATS-COMPLIANT PREVIEW */}
          <div className="ai-card" style={{ padding: '24px', maxHeight: '820px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid var(--border-light)', paddingBottom: '10px' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                LIVE PREVIEW ({templateId} • {fontFamily})
              </span>
              <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: '700' }}>
                A4 Standard ATS View
              </span>
            </div>

            {/* Resume Sheet Preview */}
            <div style={{
              background: '#ffffff',
              color: '#0f172a',
              padding: '24px',
              borderRadius: '8px',
              boxShadow: '0 4px 14px rgba(0,0,0,0.1)',
              fontFamily: fontFamily === 'Georgia' || fontFamily === 'Times New Roman' ? 'Georgia, serif' : 'Arial, sans-serif',
              fontSize: '12px',
              lineHeight: '1.45'
            }}>
              {/* Header based on Template */}
              {templateId === 'Modern' ? (
                <div style={{ background: primaryColor, color: 'white', padding: '16px 20px', borderRadius: '6px', marginBottom: '16px' }}>
                  <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '800', letterSpacing: '0.5px' }}>{personalInfo.name || 'Candidate Name'}</h1>
                  <div style={{ fontSize: '13px', opacity: 0.9, marginTop: '2px' }}>{personalInfo.title}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '11px', marginTop: '8px', opacity: 0.85 }}>
                    {personalInfo.email && <span>{personalInfo.email}</span>}
                    {personalInfo.phone && <span>• {personalInfo.phone}</span>}
                    {personalInfo.location && <span>• {personalInfo.location}</span>}
                    {personalInfo.linkedin && <span>• {personalInfo.linkedin}</span>}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: templateId === 'Minimal' ? 'left' : 'center', marginBottom: '16px', borderBottom: templateId === 'Simple' ? `2px solid ${primaryColor}` : 'none', paddingBottom: '10px' }}>
                  <h1 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: primaryColor }}>{personalInfo.name || 'Candidate Name'}</h1>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginTop: '2px' }}>{personalInfo.title}</div>
                  <div style={{ display: 'flex', justifyContent: templateId === 'Minimal' ? 'flex-start' : 'center', flexWrap: 'wrap', gap: '8px', fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                    {personalInfo.email && <span>{personalInfo.email}</span>}
                    {personalInfo.phone && <span>| {personalInfo.phone}</span>}
                    {personalInfo.location && <span>| {personalInfo.location}</span>}
                    {personalInfo.linkedin && <span>| {personalInfo.linkedin}</span>}
                  </div>
                </div>
              )}

              {/* Summary */}
              {summary && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Professional Summary
                  </div>
                  <p style={{ margin: 0, fontSize: '11.5px', color: '#334155', lineHeight: '1.5' }}>{summary}</p>
                </div>
              )}

              {/* Technical Template: Skills Top */}
              {templateId === 'Technical' && ((skills && skills.trim()) || customCategories.some(c => c.name.trim() && c.items.trim())) && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Technical Core Competencies
                  </div>
                  {customCategories.some(c => c.name.trim() && c.items.trim()) ? (
                    <>
                      {skills && skills.trim() && (
                        <div style={{ fontSize: '11px', marginBottom: '3px', color: '#1e293b' }}>
                          <b>Core:</b> {skills}
                        </div>
                      )}
                      {customCategories.filter(c => c.name.trim() && c.items.trim()).map((c, i) => (
                        <div key={i} style={{ fontSize: '11px', marginBottom: '3px', color: '#1e293b' }}>
                          <b>{c.name}:</b> {c.items}
                        </div>
                      ))}
                    </>
                  ) : (
                    <div style={{ fontSize: '11px', color: '#1e293b', lineHeight: '1.6' }}>
                      {skills.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean).join(' • ')}
                    </div>
                  )}
                </div>
              )}

              {/* Fresher Template: Education First */}
              {templateId === 'Fresher' && education.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Education & Academic Qualifications
                  </div>
                  {education.map((edu, idx) => (
                    <div key={idx} style={{ marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '11.5px' }}>
                        <span>{edu.degree}</span>
                        <span style={{ color: '#64748b' }}>{edu.duration}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#475569' }}>
                        <span>{edu.institution} {edu.location ? `• ${edu.location}` : ''}</span>
                        <span><b>{edu.grade}</b></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Experience */}
              {experience.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Work Experience
                  </div>
                  {experience.map((exp, idx) => (
                    <div key={idx} style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '11.5px' }}>
                        <span>{exp.title}</span>
                        <span style={{ color: '#64748b' }}>{exp.duration}</span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#475569', fontStyle: 'italic', marginBottom: '3px' }}>
                        {exp.company} {exp.location ? `• ${exp.location}` : ''}
                      </div>
                      <ul style={{ margin: '0 0 0 16px', padding: 0, fontSize: '11px', color: '#334155' }}>
                        {(Array.isArray(exp.bullets) ? exp.bullets : (exp.bullets || '').split('\n')).filter(b => b.trim()).map((b, bIdx) => (
                          <li key={bIdx} style={{ marginBottom: '2px' }}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}

              {/* Projects */}
              {projects.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Projects & Technical Implementations
                  </div>
                  {projects.map((proj, idx) => (
                    <div key={idx} style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '11.5px' }}>
                        <span>{proj.name}</span>
                        <span style={{ color: '#64748b' }}>{proj.duration}</span>
                      </div>
                      {proj.tech_stack && (
                        <div style={{ fontSize: '10.5px', color: '#475569', marginBottom: '2px' }}>
                          <b>Tech Stack:</b> {proj.tech_stack}
                        </div>
                      )}
                      <ul style={{ margin: '0 0 0 16px', padding: 0, fontSize: '11px', color: '#334155' }}>
                        {(Array.isArray(proj.bullets) ? proj.bullets : (proj.bullets || '').split('\n')).filter(b => b.trim()).map((b, bIdx) => (
                          <li key={bIdx} style={{ marginBottom: '2px' }}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}

              {/* Standard Templates: Skills */}
              {templateId !== 'Technical' && ((skills && skills.trim()) || customCategories.some(c => c.name.trim() && c.items.trim())) && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Technical Skills
                  </div>
                  {customCategories.some(c => c.name.trim() && c.items.trim()) ? (
                    <>
                      {skills && skills.trim() && (
                        <div style={{ fontSize: '11px', marginBottom: '2px', color: '#1e293b' }}>
                          <b>Core:</b> {skills}
                        </div>
                      )}
                      {customCategories.filter(c => c.name.trim() && c.items.trim()).map((c, i) => (
                        <div key={i} style={{ fontSize: '11px', marginBottom: '2px', color: '#1e293b' }}>
                          <b>{c.name}:</b> {c.items}
                        </div>
                      ))}
                    </>
                  ) : (
                    <div style={{ fontSize: '11px', color: '#1e293b', lineHeight: '1.6' }}>
                      {skills.split(/[,;\n]+/).map(s => s.trim()).filter(Boolean).join(' • ')}
                    </div>
                  )}
                </div>
              )}

              {/* Standard Templates: Education */}
              {templateId !== 'Fresher' && education.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Education
                  </div>
                  {education.map((edu, idx) => (
                    <div key={idx} style={{ marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '11.5px' }}>
                        <span>{edu.degree}</span>
                        <span style={{ color: '#64748b' }}>{edu.duration}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#475569' }}>
                        <span>{edu.institution} {edu.location ? `• ${edu.location}` : ''}</span>
                        <span><b>{edu.grade}</b></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Certifications & Achievements */}
              {(certifications.length > 0 || achievements.length > 0) && (
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', color: primaryColor, borderBottom: `1px solid ${primaryColor}40`, paddingBottom: '3px', marginBottom: '6px' }}>
                    Certifications & Achievements
                  </div>
                  <ul style={{ margin: '0 0 0 16px', padding: 0, fontSize: '11px', color: '#334155' }}>
                    {certifications.filter(c => c.trim()).map((c, idx) => (
                      <li key={idx} style={{ marginBottom: '2px' }}>{c}</li>
                    ))}
                    {achievements.filter(a => a.trim()).map((a, idx) => (
                      <li key={idx} style={{ marginBottom: '2px' }}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: BUILT RESUMES HISTORY */}
      {activeTab === 'history' && (
        <div className="ai-card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)' }}>
                Previously Built Resumes
              </h4>
              <p className="card-subtitle">
                Download past generated PDF resumes or resend copies directly to your registered email.
              </p>
            </div>
            <button onClick={loadHistory} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
              Refresh History
            </button>
          </div>

          {loadingHistory ? (
            <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
              Loading built resumes history...
            </div>
          ) : historyList.length > 0 ? (
            <div>
              <div className="table-container">
                <table className="ai-table">
                  <thead>
                    <tr>
                      <th>Title / Role</th>
                      <th>Template</th>
                      <th>Font</th>
                      <th>Created Date</th>
                      <th>Email Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyList.map(r => (
                      <tr key={r.id}>
                        <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{r.title}</td>
                        <td>
                          <span className="badge-medium">{r.template_id}</span>
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{r.font_family}</td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td>
                          <span className={r.email_sent ? 'badge-status-resolved' : 'badge-status-open'}>
                            {r.email_sent ? 'Delivered' : 'Pending/Retry'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              type="button"
                              onClick={() => handlePreviewHistoryResume(r)}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11.5px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                              <Eye size={13} />
                              <span>Preview</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDownloadDirect(r.id, `${r.title || 'Resume'}_${r.template_id}.pdf`)}
                              className="btn-primary"
                              style={{ padding: '4px 10px', fontSize: '11.5px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                              <Download size={13} />
                              <span>PDF</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleResendEmail(r.id)}
                              disabled={resendingId === r.id}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '11.5px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                              <Mail size={13} />
                              <span>{resendingId === r.id ? 'Sending...' : 'Email'}</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {previewResumeItem && (
                <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', border: '1.5px solid var(--border-light)', background: 'var(--bg-surface)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div>
                      <span style={{ fontWeight: '800', fontSize: '14px', color: 'var(--text-primary)' }}>
                        Previewing: {previewResumeItem.title} ({previewResumeItem.template_id} • {previewResumeItem.font_family})
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        onClick={() => handleDownloadDirect(previewResumeItem.id, `${previewResumeItem.title || 'Resume'}_${previewResumeItem.template_id}.pdf`)}
                        className="btn-primary"
                        style={{ padding: '4px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Download size={13} />
                        <span>Download PDF</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setPreviewResumeItem(null);
                          if (pdfBlobUrl) {
                            URL.revokeObjectURL(pdfBlobUrl);
                            setPdfBlobUrl(null);
                          }
                        }}
                        className="btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                      >
                        Close Preview
                      </button>
                    </div>
                  </div>

                  {loadingPdfBlob ? (
                    <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-surface-secondary)', borderRadius: '8px', color: 'var(--text-muted)' }}>
                      Loading PDF preview...
                    </div>
                  ) : pdfBlobUrl ? (
                    <iframe
                      src={pdfBlobUrl}
                      title="History Resume PDF Preview"
                      style={{
                        width: '100%',
                        height: '520px',
                        border: '1px solid var(--border-light)',
                        borderRadius: '8px',
                        background: '#525659'
                      }}
                    />
                  ) : null}
                </div>
              )}
            </div>
          ) : (
          <div className="empty-state">
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
              <FileText size={40} color="var(--text-muted)" />
            </div>
            <div className="empty-title">No Built Resumes Found</div>
            <div className="empty-desc">You have not generated any resumes with the Resume Builder yet.</div>
            <button onClick={() => setActiveTab('editor')} className="btn-primary">
              Create Your First Resume
            </button>
          </div>
        )}
      </div>
    )}
    </div>
  );
}
