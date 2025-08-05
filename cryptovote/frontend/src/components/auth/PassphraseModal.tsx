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
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg w-full max-w-md">
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
              className="auth-input mb-2 w-full"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (mode === 'get') {
                    handleSubmit();
                  } else if (mode === 'set' && confirmInputRef.current) {
                    confirmInputRef.current.focus();
                  }
                }
              }}
            />

            {/* Second input only in registration */}
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
                className="auth-input mb-2 w-full"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
              />
            )}

            {error && <div className="text-red-500 text-sm mb-2">{error}</div>}

            <div className="flex justify-end gap-2">
              <button
                onClick={handleCancel}
                className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-500 text-gray-800 dark:text-gray-200
                  hover:bg-teal-400 hover:text-white dark:hover:bg-teal-400"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="w-full py-2 rounded bg-teal-600 hover:bg-teal-500 dark:hover:bg-teal-500 text-white"
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
