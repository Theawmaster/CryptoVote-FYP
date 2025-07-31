import React, { useState } from 'react';
import '../styles/auth.css';
import '../styles/voter-auth.css';

type Props = { onSubmit?: () => void };

const REGISTER_URL = 'http://localhost:5010/register/';
const VERIFY_URL = 'http://localhost:5010/register/verify-email';

const RegisterForm: React.FC<Props> = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(''); // token pasted by the user
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [loadingToken, setLoadingToken] = useState(false);

  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  // QR modal state
  const [showQr, setShowQr] = useState(false);
  const [totpUri, setTotpUri] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    window.setTimeout(() => setToast(null), 3000);
  };

  // Spinner component for loading states
  const Spinner = () => (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
    </svg>
  );

  // 1) Verify Email (POST /register/)
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

      let data: any = null;
      try { data = await res.json(); } catch {}

      if (!res.ok) {
        const backendErr = (data?.error || '').toString().toLowerCase();
        if (backendErr.includes('invalid email domain')) {
          showToast('error', 'Please use your NTU email');
        } else {
          showToast('error', 'Error, please try again later');
        }
        return;
      }

      showToast('success', data?.message || 'Verification email sent. Check your inbox.');
    } catch {
      showToast('error', 'Error, please try again later');
    } finally {
      setLoadingEmail(false);
    }
  };

  // 2) Verify Token (GET /register/verify-email?token=...)
  const handleVerifyToken = async () => {
    const token = otp.trim();
    setLoadingToken(true);

    try {
      const url = `${VERIFY_URL}?token=${encodeURIComponent(token)}`;
      const res = await fetch(url, { method: 'GET' });

      let data: any = null;
      try { data = await res.json(); } catch {}

      if (!res.ok) {
        if (res.status === 400) {
          // server text: "Verification token is missing"
          showToast('error', 'Verification token is missing');
        } else if (res.status === 404) {
          // server text: "Invalid or expired token"
          showToast('error', 'Invalid or expired token');
        } else {
          showToast('error', 'Error, please try again later');
        }
        return;
      }

      // success
      const uri = data?.totp_uri as string | undefined;
      if (!uri) {
        showToast('error', 'Error, please try again later');
        return;
      }

      setTotpUri(uri);

      // Generate QR image (data URL)
      try {
        const { default: QRCode } = await import('qrcode');
        const dataUrl = await QRCode.toDataURL(uri);
        setQrDataUrl(dataUrl);
      } catch {
        // If the library fails for any reason, we can still show the raw URI
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

        <div className="auth-row">
          <input
            type="email"
            placeholder="Enter NTU email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="auth-input flex-1"
            inputMode="email"
            autoComplete="email"
            disabled={loadingEmail} 
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();         // stop the outer form from submitting
                handleVerifyEmail();        // trigger the email verification
              }
            }}
          />
          <button
            type="button"
            onClick={handleVerifyEmail}
            disabled={loadingEmail}
            className="auth-row-btn disabled:opacity-60 disabled:cursor-not-allowed"
            aria-busy={loadingEmail}
          >
            {loadingEmail ? (
            <span className="flex items-center gap-2">
              <Spinner />
              <span>Sending…</span>
            </span>
          ) : (
            'Verify Email'
          )}
          </button>
        </div>

        <div className="auth-row">
          <input
            type="text"
            placeholder="Paste Token here"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            className="auth-input flex-1"
            inputMode="text"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();         // stop the outer form from submitting
                handleVerifyToken();        // trigger the token verification
              }
            }}
          />
          <button
            type="button"
            onClick={handleVerifyToken}
            disabled={loadingToken}
            className="auth-row-btn disabled:opacity-60 disabled:cursor-not-allowed"
            aria-busy={loadingToken}
          >
            {loadingToken ? (
            <span className="flex items-center gap-2">
              <Spinner />
              <span>Verifying…</span>
            </span>
          ) : (
            'Verify Token'
          )}
          </button>
        </div>
      </form>

      {/* Lightweight toast */}
      {toast && (
        <div
          className={[
            'fixed left-1/2 -translate-x-1/2 bottom-6 z-50',
            'px-4 py-3 rounded-lg shadow-lg text-white',
            toast.type === 'success' ? 'bg-teal-600' : 'bg-red-600',
          ].join(' ')}
          role="status"
          aria-live="polite"
        >
          {toast.msg}
        </div>
      )}

      {/* QR Modal */}
      {showQr && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-2xl w-full max-w-sm text-center">
            <h3 className="text-lg font-semibold mb-2">
              Scan with your authenticator
            </h3>

            {qrDataUrl ? (
              <img src={qrDataUrl} alt="TOTP QR" className="mx-auto mb-3 w-56 h-56" />
            ) : (
              <div className="w-56 h-56 mx-auto mb-3 rounded bg-gray-200 dark:bg-gray-700 animate-pulse" />
            )}

            {/* Always show raw URI as fallback / for manual entry */}
            {totpUri && (
              <p className="text-xs text-gray-600 dark:text-gray-300 break-all mb-3">
                {totpUri}
              </p>
            )}

            <div className="flex justify-center gap-2">
              {qrDataUrl && (
                <a
                  href={qrDataUrl}
                  download="cryptovote-totp.png"
                  className="px-3 py-2 rounded bg-teal-600 text-white hover:bg-teal-500"
                >
                  Download
                </a>
              )}
              <button
                onClick={() => setShowQr(false)}
                className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-700 hover:bg-teal-400bg-gray-200 dark:bg-gray-500 text-gray-800 dark:text-gray-200
                           hover:bg-teal-400 hover:text-white dark:hover:bg-teal-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default RegisterForm;
