import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import '../../styles/voter-auth.css';

export function openPassphraseModal({
  onCancel,
  mode = 'set', // 'set' for registration, 'get' for login
}: {
  onCancel: () => Promise<void>;
  mode?: 'set' | 'get';
}): Promise<string | null> {
  return new Promise((resolve) => {
    const Modal = () => {
      const [pass1, setPass1] = useState('');
      const [pass2, setPass2] = useState('');
      const [error, setError] = useState('');
      const confirmInputRef = useRef<HTMLInputElement>(null);

      // Password strength check
      const validatePassphrase = (p: string) => {
        const strong = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{12,}$/;
        return strong.test(p);
      };

      const cleanup = () => {
        document.body.removeChild(container);
      };

      const handleSubmit = () => {
        if (mode === 'set') {
          if (pass1 !== pass2) return setError('Passphrases do not match.');
          if (!validatePassphrase(pass1))
            return setError('Must be ≥12 chars, include upper, lower, digit, special char.');
          resolve(pass1);
        } else {
          if (!pass1.trim()) return setError('Please enter your passphrase.');
          resolve(pass1);
        }
        cleanup();
      };

      const handleCancel = async () => {
        await onCancel();
        resolve(null);
        cleanup();
      };

      // Cancel on refresh / close
      useEffect(() => {
        const handleBeforeUnload = async (e: BeforeUnloadEvent) => {
          e.preventDefault();
          await onCancel();
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => {
          window.removeEventListener('beforeunload', handleBeforeUnload);
        };
      }, []);

      return (
        <div className="auth-modal-overlay">
          <div className="auth-modal-card">
            <h2 className="text-lg font-bold mb-2">
              {mode === 'set' ? 'Set Passphrase' : 'Enter Passphrase'}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              {mode === 'set'
                ? 'Your private key will be encrypted with this passphrase. Without it, the key is unrecoverable.'
                : 'Enter your passphrase to decrypt and use your stored private key.'}
            </p>

            {/* First input */}
            <input
              type="password"
              placeholder={mode === 'set' ? 'Enter passphrase' : 'Retrieve passphrase'}
              value={pass1}
              onChange={(e) => {
                setPass1(e.target.value);
                if (error) setError('');
              }}
              className="auth-input mb-2"
            />

            {/* Second input only for registration */}
            {mode === 'set' && (
              <input
                type="password"
                placeholder="Confirm passphrase"
                value={pass2}
                ref={confirmInputRef}
                onChange={(e) => {
                  setPass2(e.target.value);
                  if (error) setError('');
                }}
                className="auth-input mb-2"
              />
            )}

            {error && <div className="text-red-500 text-sm mb-2">{error}</div>}

            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancel}
                className="auth-row-btn"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="auth-submit"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      );
    };

    const container = document.createElement('div');
    document.body.appendChild(container);
    const root = createRoot(container);
    root.render(<Modal />);
  });
}
