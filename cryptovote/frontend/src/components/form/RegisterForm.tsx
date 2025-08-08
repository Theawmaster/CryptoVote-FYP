import React, { useState } from 'react';
import '../../styles/auth.css';
import '../../styles/voter-auth.css';

import RegisterEmailRow from '../../components/auth/RegisterEmailRow';
import RegisterTokenRow from '../../components/auth/RegisterTokenRow';
import Toast from '../../components/ui/Toast';
import QrModal from '../../components/auth/QrModal';

import { openPassphraseModal } from '../../components/auth/PassphraseModal';
import { encryptPrivateKey, downloadPem, decryptPrivateKey } from '../../utils/crypto-utils';
import { saveToIndexedDB } from '../../utils/indexeddb-utils';

type Props = { onSubmit?: () => void };

const REGISTER_URL = '/register/';
const VERIFY_URL = '/register/verify-email';


const RegisterForm: React.FC<Props> = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState(''); // token pasted by the user

  const [loadingEmail, setLoadingEmail] = useState(false);
  const [loadingToken, setLoadingToken] = useState(false);

  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);

  // QR modal state
  const [showQr, setShowQr] = useState(false);
  const [totpUri, setTotpUri] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);

  const showToast = (type: 'success' | 'error' | 'info', msg: string) => {
    setToast({ type, msg });
  };

// POST /register/
const handleVerifyEmail = async () => {
  const normalized = email.trim().toLowerCase();
  if (!normalized) {
    showToast('error', 'Please enter your NTU email.');
    return;
  }

  setLoadingEmail(true);
  try {
    const res = await fetch(REGISTER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: normalized, vote_role: 'voter' }),
    });

    const data = await res.json();
    if (!res.ok) {
      const backendErr = (data?.error || '').toLowerCase();
      if (backendErr.includes('invalid email domain')) {
        showToast('error', 'Please use your NTU email');
      } else {
        showToast('error', 'Error, please try again later');
      }
      return;
    }

    showToast('success', data?.message || 'Verification email sent.');

    let privateKeyPem = data?.private_key;
    if (privateKeyPem) {

      // 1. Ask for passphrase via secure modal
      const passphrase = await openPassphraseModal({
        onCancel: async () => {
          // If modal closed (user refreshes/closes tab before OK), cancel registration
          try {
            await fetch(`${REGISTER_URL}cancel`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: normalized }),
            });
          } catch {}
          showToast('error', 'Passphrase setup cancelled. Registration aborted.');
        },
        mode: 'set'
      });
    
      if (!passphrase) {
        return; // Cancel already handled in onCancel
      }     

      // 2. Force PEM download
      downloadPem(privateKeyPem);
      showToast('info', 'PEM file for verification has been downloaded.');

      // 3. Encrypt private key
      const encrypted = await encryptPrivateKey(privateKeyPem, passphrase);

      const decryptedTest = await decryptPrivateKey(encrypted, passphrase);
      console.log("🛠️ Decrypted PEM after encrypt (register):", decryptedTest);
      console.log("✅ Match with original:", decryptedTest === privateKeyPem);

      // 4. Store in IndexedDB
      await saveToIndexedDB('cryptoVoteKeys', { id: 'encryptedPrivateKey', ...encrypted });
      
      console.log('Encrypted private key stored in IndexedDB');

      // 5. Clear from memory
      privateKeyPem = null;

      showToast('info', 'Proceed to Verification of Token after downloading PEM.');
    }
  } catch {
    showToast('error', 'Error, please try again later');
  } finally {
    setLoadingEmail(false);
  }
};

  // GET /register/verify-email?token=...
  const handleVerifyToken = async () => {
    const t = token.trim();
    setLoadingToken(true);

    try {
      const url = `${VERIFY_URL}?token=${encodeURIComponent(t)}`;
      const res = await fetch(url, { method: 'GET' });

      let data: any = null;
      try { data = await res.json(); } catch {}

      if (!res.ok) {
        if (res.status === 400) {
          showToast('error', 'Verification token is missing');
        } else if (res.status === 404) {
          showToast('error', 'Invalid or expired token');
        } else {
          showToast('error', 'Error, please try again later');
        }
        return;
      }

      const uri = data?.totp_uri as string | undefined;
      if (!uri) {
        showToast('error', 'Error, please try again later');
        return;
      }

      setTotpUri(uri);

      // Generate QR (data URL) locally
      try {
        const { default: QRCode } = await import('qrcode');
        const dataUrl = await QRCode.toDataURL(uri);
        setQrDataUrl(dataUrl);
      } catch {
        setQrDataUrl(null);
      }

      showToast('success', data?.message || 'Email verified successfully. QR image will be generated to set up your authenticator for you to log in.');
      setShowQr(true);
    } catch {
      showToast('error', 'Error, please try again later');
    } finally {
      setLoadingToken(false);
    }
  };

  return (
    <>
      <form className="auth-form">
        <div className="auth-form-title">Create Account</div>

        <RegisterEmailRow
          email={email}
          setEmail={setEmail}
          loading={loadingEmail}
          onVerify={handleVerifyEmail}
        />

        <RegisterTokenRow
          token={token}
          setToken={setToken}
          loading={loadingToken}
          onVerify={handleVerifyToken}
        />

      </form>

      {toast && (
        <Toast
          type={toast.type}
          message={toast.msg}
          duration={3000}
          onClose={() => setToast(null)}
        />
      )}

      <QrModal
        open={showQr}
        onClose={() => setShowQr(false)}
        totpUri={totpUri}
        qrDataUrl={qrDataUrl}
      />
    </>
  );
};

export default RegisterForm;
