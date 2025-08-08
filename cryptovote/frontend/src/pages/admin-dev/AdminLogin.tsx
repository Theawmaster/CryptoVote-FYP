// src/pagesfe_dev_ver_1/admin-dev/AdminLogin.tsx
import React, { useState } from 'react';
import { openPassphraseModal } from '../../components/auth/PassphraseModal';
import Toast from '../../components/ui/Toast';
import { getFromIndexedDB } from '../../utils/indexeddb-utils';
import { decryptPrivateKey, importPrivateKeyFromPEM, signNonce } from '../../utils/crypto-utils';
import '../../styles/auth.css';
import '../../styles/admin-auth.css';

import RoleSelect from '../../components/RoleSelect';
import { motion } from 'framer-motion';
import Brand from '../../components/Brand';
import { useNavigate } from 'react-router-dom';

const LOGIN_URL = '/admin-login';
const OTP_URL = '/2fa-verify';

const AdminLogin: React.FC = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpStage, setOtpStage] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);
  const navigate = useNavigate();

  const showToast = (type: 'success' | 'error' | 'info', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const pickPrivateKeyFile = () => {
    return new Promise<string>((resolve, reject) => {
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.pem';
      fileInput.onchange = async (e: any) => {
        const file = e.target.files[0];
        if (!file) return reject('No file selected');
        const pem = await file.text();
        resolve(pem);
      };
      fileInput.click();
    });
  };

  const handleLogin = async () => {
    if (!email.trim()) {
      showToast('error', 'Please enter your NTU email.');
      return;
    }
    // Optional UX guard (not security)
    if (!email.toLowerCase().includes('admin')) {
      showToast('error', 'This login is for admin accounts only.');
      return;
    }

    setLoading(true);
    try {
      // Step 1: Request nonce (admin endpoint)
      const nonceRes = await fetch(LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email }),
      });
      const nonceData = await nonceRes.json();

      if (!nonceRes.ok || !nonceData?.nonce) {
        showToast('error', nonceData?.error || 'Unable to request nonce.');
        return;
      }

      // Step 2: Load private key
      let privateKey: CryptoKey | null = null;
      const encryptedKey = await getFromIndexedDB('cryptoVoteKeys', 'encryptedPrivateKey');

      if (encryptedKey) {
        showToast('info', 'Found encrypted key. Please enter your passphrase.');
        const passphrase = await openPassphraseModal({
          onCancel: async () => showToast('error', 'Cancelled.'),
          mode: 'get',
        });
        if (!passphrase) return;
        try {
          const decryptedPem = await decryptPrivateKey(encryptedKey, passphrase);
          privateKey = await importPrivateKeyFromPEM(decryptedPem);
        } catch {
          showToast('error', 'Incorrect passphrase or corrupt key.');
          return;
        }
      } else {
        showToast('info', 'No saved key. Please upload your private key.');
        try {
          const pem = await pickPrivateKeyFile();
          privateKey = await importPrivateKeyFromPEM(pem);
        } catch (err) {
          showToast('error', String(err));
          return;
        }
      }

      if (!privateKey) {
        showToast('error', 'Private key unavailable.');
        return;
      }

      // Step 3: Sign nonce
      const signedNonce = await signNonce(privateKey, nonceData.nonce);

      // Step 4: Send signed nonce (admin endpoint)
      const loginRes = await fetch(LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, signed_nonce: signedNonce }),
      });
      const loginData = await loginRes.json();

      if (!loginRes.ok) {
        showToast('error', loginData?.error || 'Login failed.');
        return;
      }

      showToast('success', 'Signature verified. Please enter OTP.');
      setOtpStage(true);
    } catch (err) {
      console.error(err);
      showToast('error', 'Unexpected error during login.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpVerify = async () => {
    if (!otp.trim()) {
      showToast('error', 'Please enter OTP.');
      return;
    }

    setLoading(true);
    try {
      const otpRes = await fetch(OTP_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, otp }),
      });
      const otpData = await otpRes.json();

      if (!otpRes.ok) {
        showToast('error', otpData?.error || 'OTP verification failed.');
        return;
      }

      // Require admin role from backend
      if (otpData.role !== 'admin') {
        showToast('error', 'Access denied. You are not an admin.');
        return;
      }

      showToast('success', '2FA successful. Access granted.');
      navigate('/admin/landing', { replace: true, state: { email } });
    } catch {
      showToast('error', 'Unexpected error during OTP verification.');
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
      <div className="admin-card">
        <Brand title="Admin Developer Authentication" />
        {!otpStage ? (
          <form onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
            <div className="admin-title">Admin Login</div>
            <input
              type="email"
              placeholder="Enter NTU email"
              className="admin-input mb-3"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button className="admin-submit" disabled={loading}>
              {loading ? 'Logging in…' : 'Login'}
            </button>
          </form>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); handleOtpVerify(); }}>
            <div className="admin-title">Enter OTP</div>
            <input
              type="text"
              placeholder="OTP"
              className="admin-input mb-3"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />
            <button className="admin-submit" disabled={loading}>
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
