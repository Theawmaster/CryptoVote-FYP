import React, { useEffect, useRef, useState } from 'react';
import '../../styles/auth.css';
import '../../styles/voter-auth.css';

import RegisterEmailRow from '../../components/auth/RegisterEmailRow';
import RegisterTokenRow from '../../components/auth/RegisterTokenRow';
import Toast from '../../components/ui/Toast';
import QrModal from '../../components/auth/QrModal';

import { openPassphraseModal } from '../../components/auth/PassphraseModal';
import { encryptPrivateKey, downloadPem, decryptPrivateKey } from '../../utils/crypto-utils';
import { saveToIndexedDB } from '../../utils/indexeddb-utils';

import { requestRegistration, cancelRegistration } from '../../services/voter/registerEmail';
import { verifyRegistrationToken } from '../../services/voter/verifyRegistrationToken';
import { toDataUrl } from '../../utils/qr';

type Props = { onSubmit?: () => void };

const RegisterForm: React.FC<Props> = ({ onSubmit }) => {
  const [email, setEmail] = useState(() => localStorage.getItem('voterEmail') || '');
  const [token, setToken] = useState('');

  const [loadingEmail, setLoadingEmail] = useState(false);
  const [loadingToken, setLoadingToken] = useState(false);

  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);

  const [showQr, setShowQr] = useState(false);
  const [totpUri, setTotpUri] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);

  const regAbortRef = useRef<AbortController | null>(null);
  const verAbortRef = useRef<AbortController | null>(null);

  const showToast = (type: 'success' | 'error' | 'info', msg: string, ms = 3200) => {
    setToast({ type, msg });
    window.clearTimeout((showToast as any)._t);
    (showToast as any)._t = window.setTimeout(() => setToast(null), ms);
  };

  useEffect(() => {
    return () => {
      regAbortRef.current?.abort();
      verAbortRef.current?.abort();
      window.clearTimeout((showToast as any)._t);
    };
  }, []);

  useEffect(() => {
    localStorage.setItem('voterEmail', email);
  }, [email]);

  // POST /register/
  const handleVerifyEmail = async () => {
    const normalized = email.trim().toLowerCase();
    if (!normalized) {
      showToast('error', 'Please enter your NTU email.');
      return;
    }

    setLoadingEmail(true);
    const controller = new AbortController();
    regAbortRef.current = controller;

    try {
      const data = await requestRegistration(normalized, controller.signal);
      showToast('success', data?.message || 'Verification email sent.');

      let privateKeyPem = data?.private_key || null;
      if (privateKeyPem) {
        // 1) passphrase
        const passphrase = await openPassphraseModal({
          onCancel: async () => {
            await cancelRegistration(normalized);
            showToast('error', 'Passphrase setup cancelled. Registration aborted.');
          },
          mode: 'set',
        });
        if (!passphrase) return; // cancel handler already fired

        // 2) force download
        downloadPem(privateKeyPem);
        showToast('info', 'PEM file downloaded for verification.');

        // 3) encrypt + sanity check
        const encrypted = await encryptPrivateKey(privateKeyPem, passphrase);
        const decryptedTest = await decryptPrivateKey(encrypted, passphrase);
        console.log('🔐 decrypted matches original:', decryptedTest === privateKeyPem);

        // 4) store to IndexedDB
        await saveToIndexedDB('cryptoVoteKeys', { id: 'encryptedPrivateKey', ...encrypted });

        // 5) clear from memory
        privateKeyPem = null;

        showToast('info', 'Proceed to paste your email verification token.');
      }
    } catch (e: any) {
      const msg =
        e?.message?.toLowerCase?.().includes('invalid email domain')
          ? 'Please use your NTU email.'
          : e?.message || 'Error, please try again later.';
      showToast('error', msg);
    } finally {
      setLoadingEmail(false);
    }
  };

  // GET /register/verify-email?token=...
  const handleVerifyToken = async () => {
    const t = token.trim();
    if (!t) {
      showToast('error', 'Please paste the verification token from your email.');
      return;
    }

    setLoadingToken(true);
    const controller = new AbortController();
    verAbortRef.current = controller;

    try {
      const data = await verifyRegistrationToken(t, controller.signal);

      const uri = data?.totp_uri;
      if (!uri) {
        showToast('error', 'Unexpected response from server.');
        return;
      }

      setTotpUri(uri);
      setQrDataUrl(await toDataUrl(uri));
      setShowQr(true);

      showToast('success', data?.message || 'Email verified. Scan the QR to set up 2FA.');
      onSubmit?.();
    } catch (e: any) {
      // map common statuses already handled by apiJson; provide friendly text
      const msg = /missing/i.test(e?.message)
        ? 'Verification token is missing.'
        : /expired|not found|invalid/i.test(e?.message)
        ? 'Invalid or expired token.'
        : e?.message || 'Error, please try again later.';
      showToast('error', msg);
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
