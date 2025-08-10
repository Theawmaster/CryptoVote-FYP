import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

import Brand from '../../components/Brand';
import RoleSelect from '../../components/RoleSelect';
import Toast from '../../components/ui/Toast';

import { handleLogin } from '../../services/admin/handleLogin';
import { handleOtpVerify } from '../../services/admin/handleOtpVerify';

import '../../styles/auth.css';
import '../../styles/admin-auth.css';

type ToastKind = 'success' | 'error' | 'info';

const AdminLogin: React.FC = () => {
  const navigate = useNavigate();

  // form state
  const [email, setEmail] = useState(() => localStorage.getItem('adminEmail') || '');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpStage, setOtpStage] = useState(false);

  // toast
  const [toast, setToast] = useState<{ type: ToastKind; msg: string } | null>(null);
  const showToast = (type: ToastKind, msg: string, ms = 3000) => {
    setToast({ type, msg });
    window.clearTimeout((showToast as any)._t);
    (showToast as any)._t = window.setTimeout(() => setToast(null), ms);
  };

  const emailRef = useRef<HTMLInputElement | null>(null);
  const otpRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    emailRef.current?.focus();
    return () => window.clearTimeout((showToast as any)._t);
  }, []);

  useEffect(() => {
    localStorage.setItem('adminEmail', email);
  }, [email]);

  const onLogin = async () => {
    if (!email.trim()) {
      showToast('error', 'Please enter your NTU email.');
      emailRef.current?.focus();
      return;
    }
    setLoading(true);
    try {
      await handleLogin(
        email,
        (t, m) => showToast(t as ToastKind, m),
        (next) => setOtpStage(next)
      );
      if (!otpStage) {
        // when we flip to OTP stage, focus the input
        setTimeout(() => otpRef.current?.focus(), 0);
      }
    } catch (e: any) {
      showToast('error', e?.message || 'Unexpected error during login.');
    } finally {
      setLoading(false);
    }
  };

  const onVerifyOtp = async () => {
    if (!otp.trim()) {
      showToast('error', 'Please enter OTP.');
      otpRef.current?.focus();
      return;
    }
    setLoading(true);
    try {
      await handleOtpVerify(
        email,
        otp,
        (t, m) => showToast(t as ToastKind, m),
        (path, opts) => navigate(path, opts)
      );
    } catch (e: any) {
      showToast('error', e?.message || 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="admin-screen"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="auth-header">
        <div className="auth-bar">
          <RoleSelect size="sm" />
        </div>
      </div>

      <div className="admin-card" role="form" aria-labelledby="admin-auth-title">
        <Brand title="Admin Developer Authentication" />

        {!otpStage ? (
          <form
            onSubmit={(e) => { e.preventDefault(); onLogin(); }}
            noValidate
          >
            <div id="admin-auth-title" className="admin-title">Admin Login</div>
            <label className="sr-only" htmlFor="admin-email">NTU Email</label>
            <input
              id="admin-email"
              ref={emailRef}
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="Enter NTU email"
              className="admin-input mb-3"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <button className="admin-submit" disabled={loading} aria-busy={loading}>
              {loading ? 'Logging in…' : 'Login'}
            </button>
          </form>
        ) : (
          <form
            onSubmit={(e) => { e.preventDefault(); onVerifyOtp(); }}
            noValidate
          >
            <div className="admin-title">Enter OTP</div>
            <label className="sr-only" htmlFor="admin-otp">One-Time Password</label>
            <input
              id="admin-otp"
              ref={otpRef}
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              placeholder="OTP"
              className="admin-input mb-3"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              disabled={loading}
            />
            <button className="admin-submit" disabled={loading} aria-busy={loading}>
              {loading ? 'Verifying…' : 'Verify OTP'}
            </button>
          </form>
        )}

        {toast && (
          <Toast
            type={toast.type}
            message={toast.msg}
            duration={3000}
            onClose={() => setToast(null)}
          />
        )}
      </div>
    </motion.div>
  );
};

export default AdminLogin;
