import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, FileCheck, Layers, Target } from 'lucide-react';
import { uploadResumeApi } from '../services/api';

export default function UploadResume({ onUploadComplete, onNavigateToProfile, onNavigateToSkills, onNavigateToAts }) {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selected) => {
    const ext = selected.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) {
      setError('Please select a valid PDF or DOCX resume document.');
      return;
    }
    if (selected.size > 5 * 1024 * 1024) {
      setError('File exceeds maximum size of 5MB.');
      return;
    }
    setFile(selected);
    setError(null);
    setUploadedData(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or drop a PDF/DOCX file first.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await uploadResumeApi(file);
      setUploadedData(data);
      if (onUploadComplete) {
        onUploadComplete(data);
      }
    } catch (err) {
      console.error('Upload Error:', err);
      const msg = err.response?.data?.detail || 'Failed to process resume document. Ensure it is not an image scan.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Upload Box Card */}
      <div className="ai-card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <UploadCloud size={20} className="text-primary" />
              <span>Resume Document Upload</span>
            </h3>
            <p className="card-subtitle">
              Upload your resume to analyze your skills, experience, and career profile.
            </p>
          </div>
        </div>

        <form onSubmit={handleUpload}>
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragging ? 'var(--primary)' : file ? 'var(--success)' : 'var(--border-light)'}`,
              background: isDragging ? 'var(--primary-light)' : file ? 'var(--success-light)' : 'var(--bg-surface-secondary)',
              borderRadius: '14px',
              padding: '44px 20px',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              marginBottom: '18px'
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '14px' }}>
              {file ? (
                <FileCheck size={48} color="var(--success)" />
              ) : (
                <UploadCloud size={48} color="var(--primary)" />
              )}
            </div>

            {file ? (
              <div>
                <div style={{ fontSize: '16px', fontWeight: '800', color: 'var(--success)', marginBottom: '4px' }}>
                  {file.name}
                </div>
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                  {(file.size / 1024).toFixed(1)} KB • Document Selected
                </div>
                <span style={{ fontSize: '12.5px', color: 'var(--primary)', fontWeight: '700', marginTop: '8px', display: 'inline-block' }}>
                  Click to choose a different file
                </span>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '16px', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Drag & Drop Resume Here
                </div>
                <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto 12px', lineHeight: '1.5' }}>
                  Upload your resume to analyze your skills, experience, and career profile.
                </p>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginBottom: '14px' }}>
                  <span style={{ background: 'var(--border-light)', color: 'var(--text-secondary)', padding: '3px 10px', borderRadius: '6px', fontSize: '11.5px', fontWeight: '700' }}>
                    PDF
                  </span>
                  <span style={{ background: 'var(--border-light)', color: 'var(--text-secondary)', padding: '3px 10px', borderRadius: '6px', fontSize: '11.5px', fontWeight: '700' }}>
                    DOCX
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px', alignSelf: 'center' }}>Max 5MB</span>
                </div>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                >
                  <FileText size={15} />
                  <span>Browse Resume</span>
                </button>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className="btn-primary"
            style={{ width: '100%', padding: '13px' }}
          >
            {loading ? 'Analyzing Document & Extracting Profile...' : 'Upload & Process Resume'}
          </button>
        </form>

        {error && (
          <div className="alert-error" style={{ marginTop: '16px' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Processing Status & Next Step Card */}
      {uploadedData && (
        <div className="ai-card" style={{ border: '2px solid var(--success-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <span style={{ fontSize: '11.5px', fontWeight: '800', color: 'var(--success)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                STATUS: PROCESSED
              </span>
              <h4 style={{ margin: '4px 0 0', fontSize: '17px', fontWeight: '800', color: 'var(--text-primary)' }}>
                {uploadedData.filename}
              </h4>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {onNavigateToSkills && (
                <button
                  type="button"
                  onClick={onNavigateToSkills}
                  className="btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '8px 14px' }}
                >
                  <Layers size={15} className="text-primary" />
                  <span>View Extracted Skills</span>
                </button>
              )}
              {onNavigateToAts && (
                <button
                  type="button"
                  onClick={onNavigateToAts}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', padding: '8px 14px' }}
                >
                  <Target size={15} />
                  <span>Run ATS Analysis</span>
                  <ArrowRight size={15} />
                </button>
              )}
            </div>
          </div>

          {/* Checklist */}
          <div style={{
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 20px',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13.5px', color: 'var(--success)', fontWeight: '700' }}>
              <CheckCircle2 size={16} />
              <span>Resume uploaded successfully</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13.5px', color: 'var(--success)', fontWeight: '700' }}>
              <CheckCircle2 size={16} />
              <span>Resume text extracted ({uploadedData.extracted_text_preview?.length || 0}+ characters)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13.5px', color: 'var(--success)', fontWeight: '700' }}>
              <CheckCircle2 size={16} />
              <span>Skills extracted ({uploadedData.skills_list?.length || 0} skills detected)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13.5px', color: 'var(--success)', fontWeight: '700' }}>
              <CheckCircle2 size={16} />
              <span>Candidate profile generated</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13.5px', color: 'var(--success)', fontWeight: '700' }}>
              <CheckCircle2 size={16} />
              <span>Role prediction completed ({uploadedData.predicted_role || 'Classified'})</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
