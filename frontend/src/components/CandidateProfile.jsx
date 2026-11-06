import React, { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Camera,
  Trash2,
  Save,
  Calendar,
  Globe
} from 'lucide-react';
import {
  getUserProfileApi,
  updateUserProfileApi,
  uploadProfilePhotoApi,
  deleteProfilePhotoApi
} from '../services/api';

export default function CandidateProfile({ onNavigateToUpload, onBack }) {
  // User Profile Form State
  const [userProfile, setUserProfile] = useState({
    name: '',
    email: '',
    phone: '',
    location: '',
    date_of_birth: '',
    degree: '',
    college: '',
    branch: '',
    graduation_year: '',
    cgpa: '',
    target_role: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
    profile_photo: null
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState(null);
  const [error, setError] = useState(null);

  // Load User Profile on mount
  useEffect(() => {
    getUserProfileApi()
      .then((data) => {
        if (data) {
          setUserProfile({
            name: data.name || '',
            email: data.email || '',
            phone: data.phone || '',
            location: data.location || '',
            date_of_birth: data.date_of_birth || '',
            degree: data.degree || '',
            college: data.college || '',
            branch: data.branch || '',
            graduation_year: data.graduation_year || '',
            cgpa: data.cgpa || '',
            target_role: data.target_role || '',
            linkedin_url: data.linkedin_url || '',
            github_url: data.github_url || '',
            portfolio_url: data.portfolio_url || '',
            profile_photo: data.profile_photo || null
          });
        }
      })
      .catch((err) => console.error('Error fetching user profile:', err));
  }, []);

  const handleProfileFieldChange = (field, value) => {
    setUserProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setError('Photo size must be less than 2MB.');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64Photo = reader.result;
      setUserProfile((prev) => ({ ...prev, profile_photo: base64Photo }));
      try {
        await uploadProfilePhotoApi(base64Photo);
        setProfileSuccessMsg('Profile photo updated.');
        setTimeout(() => setProfileSuccessMsg(null), 3000);
      } catch (err) {
        console.error('Error saving profile photo:', err);
      }
    };
    reader.readAsDataURL(file);
  };

  const handlePhotoRemove = async () => {
    setUserProfile((prev) => ({ ...prev, profile_photo: null }));
    try {
      await deleteProfilePhotoApi();
      setProfileSuccessMsg('Profile photo removed.');
      setTimeout(() => setProfileSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Error deleting photo:', err);
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileSuccessMsg(null);
    setError(null);

    try {
      await updateUserProfileApi({
        name: userProfile.name,
        phone: userProfile.phone,
        location: userProfile.location,
        date_of_birth: userProfile.date_of_birth,
        degree: userProfile.degree,
        college: userProfile.college,
        branch: userProfile.branch,
        graduation_year: userProfile.graduation_year,
        cgpa: userProfile.cgpa,
        target_role: userProfile.target_role,
        linkedin_url: userProfile.linkedin_url,
        github_url: userProfile.github_url,
        portfolio_url: userProfile.portfolio_url
      });
      setProfileSuccessMsg('Profile information saved successfully.');
      setTimeout(() => setProfileSuccessMsg(null), 4000);
    } catch (err) {
      console.error('Error saving profile:', err);
      setError('Failed to save profile information. Please try again.');
    } finally {
      setSavingProfile(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="ai-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-primary)', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <User size={20} className="text-primary" />
              <span>User Profile</span>
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Manage your personal information, education details, and portfolio links.
            </p>
          </div>

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
        </div>

        {profileSuccessMsg && (
          <div className="alert-success" style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={16} />
            <span>{profileSuccessMsg}</span>
          </div>
        )}

        {error && (
          <div className="alert-error" style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Profile Photo Row */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            background: 'var(--bg-surface-secondary)',
            border: '1px solid var(--border-light)',
            padding: '16px 20px',
            borderRadius: '10px'
          }}>
            <div style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: 'var(--bg-surface)',
              border: '2px dashed var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              flexShrink: 0
            }}>
              {userProfile.profile_photo ? (
                <img
                  src={userProfile.profile_photo}
                  alt="Profile"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <User size={32} color="var(--text-muted)" />
              )}
            </div>

            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
                Profile Photo (Optional)
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Upload a JPEG or PNG image under 2MB.
              </div>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <label className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <Camera size={14} />
                  <span>Choose Photo</span>
                  <input type="file" accept="image/*" onChange={handlePhotoUpload} style={{ display: 'none' }} />
                </label>
                {userProfile.profile_photo && (
                  <button
                    type="button"
                    onClick={handlePhotoRemove}
                    className="btn-danger"
                    style={{ padding: '6px 12px', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Trash2 size={14} />
                    <span>Remove Photo</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Personal Details */}
          <div>
            <div style={{ fontSize: '12.5px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
              Personal Details
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
              <div>
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  value={userProfile.name}
                  onChange={(e) => handleProfileFieldChange('name', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  value={userProfile.email}
                  disabled
                  className="form-input"
                  style={{ background: 'var(--bg-surface-secondary)', opacity: 0.8 }}
                />
              </div>

              <div>
                <label className="form-label">Phone Number</label>
                <input
                  type="text"
                  value={userProfile.phone}
                  onChange={(e) => handleProfileFieldChange('phone', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Location / City</label>
                <input
                  type="text"
                  value={userProfile.location}
                  onChange={(e) => handleProfileFieldChange('location', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Date of Birth</label>
                <input
                  type="date"
                  value={userProfile.date_of_birth}
                  onChange={(e) => handleProfileFieldChange('date_of_birth', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>

          {/* Education Details */}
          <div>
            <div style={{ fontSize: '12.5px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
              Education
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
              <div>
                <label className="form-label">Degree</label>
                <input
                  type="text"
                  value={userProfile.degree}
                  onChange={(e) => handleProfileFieldChange('degree', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">College / University</label>
                <input
                  type="text"
                  value={userProfile.college}
                  onChange={(e) => handleProfileFieldChange('college', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Branch / Specialization</label>
                <input
                  type="text"
                  value={userProfile.branch}
                  onChange={(e) => handleProfileFieldChange('branch', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Graduation Year</label>
                <input
                  type="text"
                  value={userProfile.graduation_year}
                  onChange={(e) => handleProfileFieldChange('graduation_year', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">CGPA / Percentage</label>
                <input
                  type="text"
                  value={userProfile.cgpa}
                  onChange={(e) => handleProfileFieldChange('cgpa', e.target.value)}

                  className="form-input"
                />
              </div>
            </div>
          </div>

          {/* Target Role & Links */}
          <div>
            <div style={{ fontSize: '12.5px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
              Target Role & Professional Links
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
              <div>
                <label className="form-label">Target Role</label>
                <input
                  type="text"
                  value={userProfile.target_role}
                  onChange={(e) => handleProfileFieldChange('target_role', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">LinkedIn URL</label>
                <input
                  type="url"
                  value={userProfile.linkedin_url}
                  onChange={(e) => handleProfileFieldChange('linkedin_url', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">GitHub URL</label>
                <input
                  type="url"
                  value={userProfile.github_url}
                  onChange={(e) => handleProfileFieldChange('github_url', e.target.value)}

                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Portfolio Website URL</label>
                <input
                  type="url"
                  value={userProfile.portfolio_url}
                  onChange={(e) => handleProfileFieldChange('portfolio_url', e.target.value)}

                  className="form-input"
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
            <button
              type="submit"
              disabled={savingProfile}
              className="btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px', fontSize: '13.5px' }}
            >
              <Save size={16} />
              <span>{savingProfile ? 'Saving Profile...' : 'Save Profile'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
