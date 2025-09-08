import React, { useEffect, useRef, useState } from 'react';
import '../../styles/auth.css';
import '../../styles/voter-auth.css';
import { useNavigate } from 'react-router-dom'; 

import Toast from '../ui/Toast';
import { handleLogin } from '../../services/voter/handleLogin';
import { handleOtpVerify } from '../../services/voter/handleOtpVerify';

type ToastKind = 'success' | 'error' | 'info';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState(() => localStorage.getItem('voterEmail') || '');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpStage, setOtpStage] = useState(false);
  const [waitSecs, setWaitSecs] = useState<number>(0);

  const navigate = useNavigate(); 

  const [toast, setToast] = useState<{ type: ToastKind; msg: string } | null>(null);
  const showToast = (type: ToastKind, msg: string, ms = 3000) => {
    setToast({ type, msg });
    window.clearTimeout((showToast as any)._t);
    (showToast as any)._t = window.setTimeout(() => setToast(null), ms);
  };

  const startCooldown = (secs: number) => {
    const s = Math.max(1, Math.min(secs || 5, 60)); // clamp 1..60s, default 5
    setWaitSecs(s);
    const id = window.setInterval(() => {
      setWaitSecs(prev => {
        if (prev <= 1) { window.clearInterval(id); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  const emailRef = useRef<HTMLInputElement | null>(null);
  const otpRef = useRef<HTMLInputElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);


  useEffect(() => {
    emailRef.current?.focus();
    return () => {
      window.clearTimeout((showToast as any)._t);
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    localStorage.setItem('voterEmail', email);
  }, [email]);

  useEffect(() => {
  const msg = sessionStorage.getItem('toast.msg');
  const kind = (sessionStorage.getItem('toast.kind') as 'success'|'error'|'info') || 'info';
  if (msg) {
    showToast(kind, msg);
    sessionStorage.removeItem('toast.msg');
    sessionStorage.removeItem('toast.kind');
  }
}, []);

  const onLogin = async () => {
    if (!email.trim()) {
      showToast('error', 'Please enter your NTU email.');
      emailRef.current?.focus();
      return;
    }
    if (waitSecs > 0) return;
    setLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await handleLogin(email, showToast, setOtpStage, controller.signal);
      setTimeout(() => otpRef.current?.focus(), 0);
    } catch (e: any) {
      if (e?.code === 'RATE_LIMIT') {
        const secs = Number(e?.retryAfter ?? 5);
        startCooldown(secs);
        showToast('info', `Too many requests. Please wait ${secs}s and try again.`);
      } else {
        showToast('error', e?.message || 'Unexpected error during login.');
      }
      console.error('[voter] login error:', e);
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
    if (waitSecs > 0) return;
    setLoading(true);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await handleOtpVerify(
        email,
        otp,
        showToast,
        () => {
          try { sessionStorage.removeItem('voter.email'); } catch {}
          sessionStorage.setItem('justLoggedIn', '1');
          navigate('/voter', { replace: true, state: { justLoggedIn: true } });
        },
        controller.signal
      );
    } catch (e: any) {
      if (e?.code === 'RATE_LIMIT') {
        const secs = Number(e?.retryAfter ?? 5);
        startCooldown(secs);
        showToast('info', `Too many requests. Please wait ${secs}s and try again.`);
      } else {
        showToast('error', e?.message || 'OTP verification failed.');
      }
      console.error('[voter] otp error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!otpStage ? (
        <form className="auth-form" onSubmit={(e) => { e.preventDefault(); onLogin(); }} noValidate>
          <div className="auth-form-title">Welcome back</div>
          <label className="sr-only" htmlFor="voter-email">Email</label>
          <input
            id="voter-email"
            ref={emailRef}
            type="email"
            inputMode="email"
            autoComplete="off"
            placeholder="Enter NTU email"
            className="auth-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="auth-submit" disabled={loading} aria-busy={loading}>
            {loading ? 'Logging in…' : 'Login'}
          </button>
        </form>
      ) : (
        <form className="auth-form" onSubmit={(e) => { e.preventDefault(); onVerifyOtp(); }} noValidate>
          <div className="auth-form-title">Enter OTP</div>
          <label className="sr-only" htmlFor="voter-otp">OTP</label>
          <input
            id="voter-otp"
            ref={otpRef}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="Enter OTP from authenticator app"
            className="auth-input"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="auth-submit" disabled={loading} aria-busy={loading}>
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
    </>
  );
};

export default LoginForm;
