import React, { useState } from 'react';
import {
  BrainCircuit,
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  CheckCircle2,
  AlertCircle,
  ArrowLeft
} from 'lucide-react';
import { loginApi, registerApi, verifyOtpApi } from '../services/api';

export default function Auth({ onLoginSuccess }) {
  const [view, setView] = useState('login'); // login | register | verify

  // Sign In form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Create Account form state — starts completely empty
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);

  // OTP Verification state
  const [verifyEmail, setVerifyEmail] = useState('');
  const [otp, setOtp] = useState('');

  // Global feedback state
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const extractErrorMessage = (err, defaultMsg) => {
    if (!err.response) {
      if (err.message && (err.message.includes('Network') || err.code === 'ERR_NETWORK')) {
        return 'Unable to reach backend server. Please verify the API server is running on port 8000.';
      }
      return err.message || 'Unable to connect to the server. Please check your network connection.';
    }
    const detail = err.response.data?.detail;
    if (detail) {
      if (Array.isArray(detail)) {
        return detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      }
      if (typeof detail === 'string') {
        return detail;
      }
    }
    return defaultMsg;
  };

  const handleSwitchToLogin = () => {
    setView('login');
    setError(null);
    setMessage(null);
    // Guarantee registration fields are cleared
    setRegisterName('');
    setRegisterEmail('');
    setRegisterPassword('');
    setShowRegisterPassword(false);
  };

  const handleSwitchToRegister = () => {
    setView('register');
    setError(null);
    setMessage(null);
    // Guarantee all Create Account fields start completely empty
    setRegisterName('');
    setRegisterEmail('');
    setRegisterPassword('');
    setShowRegisterPassword(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const cleanEmail = loginEmail.trim();
      const data = await loginApi(cleanEmail, loginPassword);
      localStorage.setItem('token', data.access_token);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(extractErrorMessage(err, 'Login failed. Please check your credentials.'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const cleanEmail = registerEmail.trim();
      const cleanName = registerName.trim();
      const data = await registerApi(cleanName, cleanEmail, registerPassword);
      setMessage(data.message || 'Verification code sent to your email.');
      setVerifyEmail(cleanEmail);
      // Clear registration form immediately upon successful submission
      setRegisterName('');
      setRegisterEmail('');
      setRegisterPassword('');
      setShowRegisterPassword(false);
      setOtp('');
      setView('verify');
    } catch (err) {
      setError(extractErrorMessage(err, 'Registration failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const cleanEmail = verifyEmail.trim();
      const data = await verifyOtpApi(cleanEmail, otp.trim());
      setMessage(data.message || 'Email verified successfully! You can now sign in.');
      setOtp('');
      setLoginEmail(cleanEmail);
      setLoginPassword('');
      setView('login');
    } catch (err) {
      setError(extractErrorMessage(err, 'Verification failed. Invalid or expired OTP.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.35)',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        {/* Brand Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          padding: '28px 24px 22px',
          textAlign: 'center',
          color: 'white',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #38bdf8 0%, #2563eb 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 12px',
            boxShadow: '0 4px 16px rgba(56, 189, 248, 0.4)'
          }}>
            <BrainCircuit size={26} color="#ffffff" />
          </div>
          <h2 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: '800', letterSpacing: '-0.3px' }}>
            AI Interview Assistant
          </h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>
            Resume Screening • ATS Optimization • Practice
          </p>
        </div>

        {/* Form Container */}
        <div style={{ padding: '28px 28px 32px' }}>
          {/* Tab Switcher */}
          {view !== 'verify' && (
            <div style={{
              display: 'flex',
              background: '#f1f5f9',
              padding: '4px',
              borderRadius: '10px',
              marginBottom: '22px'
            }}>
              <button
                type="button"
                onClick={handleSwitchToLogin}
                style={{
                  flex: 1,
                  padding: '9px 0',
                  border: 'none',
                  background: view === 'login' ? 'white' : 'transparent',
                  color: view === 'login' ? '#0f172a' : '#64748b',
                  fontWeight: '700',
                  fontSize: '13.5px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  boxShadow: view === 'login' ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s'
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={handleSwitchToRegister}
                style={{
                  flex: 1,
                  padding: '9px 0',
                  border: 'none',
                  background: view === 'register' ? 'white' : 'transparent',
                  color: view === 'register' ? '#0f172a' : '#64748b',
                  fontWeight: '700',
                  fontSize: '13.5px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  boxShadow: view === 'register' ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s'
                }}
              >
                Create Account
              </button>
            </div>
          )}

          {/* Alerts */}
          {error && (
            <div style={{
              background: '#fef2f2',
              color: '#991b1b',
              border: '1px solid #fecaca',
              padding: '11px 14px',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div style={{
              background: '#f0fdf4',
              color: '#166534',
              border: '1px solid #bbf7d0',
              padding: '11px 14px',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <CheckCircle2 size={16} />
              <span>{message}</span>
            </div>
          )}

          {/* VIEW: LOGIN */}
          {view === 'login' && (
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="name@example.com"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '8px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '700', color: '#334155' }}>Password</label>
                </div>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showLoginPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      padding: '11px 40px 11px 14px',
                      borderRadius: '8px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '14px',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#64748b'
                    }}
                  >
                    {showLoginPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: loading ? '#94a3b8' : 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '700',
                  fontSize: '14.5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                  marginTop: '6px'
                }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          )}

          {/* VIEW: REGISTER */}
          {view === 'register' && (
            <form onSubmit={handleRegister} autoComplete="off" style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="Jane Doe"
                  value={registerName}
                  onChange={(e) => setRegisterName(e.target.value)}
                  autoComplete="off"
                  required
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '8px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="name@example.com"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  autoComplete="off"
                  required
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '8px',
                    border: '1.5px solid #cbd5e1',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#334155', marginBottom: '6px' }}>
                  Create Account Password
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showRegisterPassword ? 'text' : 'password'}
                    placeholder="Minimum 6 characters"
                    value={registerPassword}
                    onChange={(e) => setRegisterPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                    style={{
                      width: '100%',
                      padding: '11px 40px 11px 14px',
                      borderRadius: '8px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '14px',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#64748b'
                    }}
                  >
                    {showRegisterPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: loading ? '#94a3b8' : 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '700',
                  fontSize: '14.5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                  marginTop: '6px'
                }}
              >
                {loading ? 'Sending verification code...' : 'Register & Verify Email'}
              </button>
            </form>
          )}

          {/* VIEW: VERIFY OTP */}
          {view === 'verify' && (
            <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                  <Mail size={32} color="#2563eb" />
                </div>
                <h3 style={{ margin: '0 0 6px', fontSize: '17px', color: '#0f172a', fontWeight: '800' }}>
                  Verify Your Email
                </h3>
                <p style={{ margin: 0, fontSize: '13px', color: '#64748b', lineHeight: '1.4' }}>
                  We sent a 6-digit verification code to<br />
                  <b style={{ color: '#0f172a' }}>{verifyEmail}</b>
                </p>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: '700', color: '#475569', textAlign: 'center', marginBottom: '8px' }}>
                  Enter 6-Digit Verification Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="------"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  required
                  autoFocus
                  style={{
                    width: '100%',
                    padding: '12px',
                    textAlign: 'center',
                    fontSize: '24px',
                    letterSpacing: '10px',
                    fontWeight: '800',
                    borderRadius: '8px',
                    border: '2px solid #2563eb',
                    outline: 'none',
                    background: '#f8fafc',
                    color: '#0f172a',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                style={{
                  width: '100%',
                  padding: '12px',
                  background: loading || otp.length !== 6 ? '#94a3b8' : 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '700',
                  fontSize: '14.5px',
                  cursor: loading || otp.length !== 6 ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 12px rgba(22, 163, 74, 0.3)'
                }}
              >
                {loading ? 'Verifying...' : 'Verify Code & Activate Account'}
              </button>

              <p style={{ textAlign: 'center', fontSize: '13px', margin: '4px 0 0' }}>
                <span
                  style={{ color: '#2563eb', cursor: 'pointer', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  onClick={handleSwitchToLogin}
                >
                  <ArrowLeft size={14} />
                  <span>Back to Sign In</span>
                </span>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
