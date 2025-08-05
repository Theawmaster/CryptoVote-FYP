import React, { useState } from 'react';
import '../styles/auth.css';
import '../styles/voter-auth.css';

import { openPassphraseModal } from '../components/auth/PassphraseModal';
import Toast from '../components/ui/Toast';
import { getFromIndexedDB } from '../utils/indexeddb-utils';
import { decryptPrivateKey, importPrivateKeyFromPEM, signNonce } from '../utils/crypto-utils';

const LOGIN_URL = 'http://localhost:5010/login';
const OTP_URL = 'http://localhost:5010/2fa-verify';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpStage, setOtpStage] = useState(false);

  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);

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
        if (!file) {
          reject('No file selected');
          return;
        }
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
  
    setLoading(true);
    try {
      // Step 1: Request nonce
      const nonceRes = await fetch(LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const nonceData = await nonceRes.json();
  
      if (!nonceRes.ok || !nonceData?.nonce) {
        showToast('error', nonceData?.error || 'Unable to request nonce.');
        return;
      }
  
      let privateKey: CryptoKey | null = null;
  
      // Step 2: Retrieve private key
      const encryptedKey = await getFromIndexedDB('cryptoVoteKeys', 'encryptedPrivateKey');
      if (encryptedKey) {
        showToast('info', 'Found encrypted key in secure storage. Please enter passphrase.');
        const passphrase = await openPassphraseModal({
          onCancel: async () => {
            showToast('error', 'Passphrase entry cancelled.');
          },
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
        showToast('info', 'No saved key found. Please upload your private key file.');
        try {
          const pem = await pickPrivateKeyFile(); // waits until file is chosen
          privateKey = await importPrivateKeyFromPEM(pem);
        } catch (err) {
          showToast('error', String(err));
          return;
        }
      }
  
      // Step 3: Sign nonce
      if (!privateKey) {
        showToast('error', 'Private key not available.');
        return;
      }
      const signedNonce = await signNonce(privateKey, nonceData.nonce);
      console.log("Signed nonce:", signedNonce); // Debugging line
  
      // Step 4: Send signed nonce
      const loginRes = await fetch(LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, signed_nonce: signedNonce }),
      });
      const loginData = await loginRes.json();
  
      if (!loginRes.ok) {
        showToast('error', loginData?.error || 'Login failed.');
        return;
      }
  
      showToast('success', 'Signature verified. Please enter OTP.');
      setOtpStage(true); // Switch to OTP stage
  
    } catch (err) {
      showToast('error', 'Unexpected error during login.');
      console.error(err);
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
        body: JSON.stringify({ email, otp }),
      });
      const otpData = await otpRes.json();

      if (!otpRes.ok) {
        showToast('error', otpData?.error || 'OTP verification failed.');
        return;
      }

      showToast('success', '2FA successful. Access granted.');
      // TODO: Redirect to dashboard

    } catch {
      showToast('error', 'Unexpected error during OTP verification.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!otpStage ? (
        <form className="auth-form" onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
          <div className="auth-form-title">Welcome back</div>
          <input
            type="email"
            placeholder="Enter NTU email"
            className="auth-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Logging in…' : 'Login'}
          </button>
        </form>
      ) : (
        <form className="auth-form" onSubmit={(e) => { e.preventDefault(); handleOtpVerify(); }}>
          <div className="auth-form-title">Enter OTP</div>
          <input
            type="text"
            placeholder="Enter OTP from authenticator app"
            className="auth-input"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
          />
          <button type="submit" className="auth-submit" disabled={loading}>
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
