import React from 'react';
import Spinner from '../ui/Spinner';

type Props = {
  email: string;
  setEmail: (v: string) => void;
  loading: boolean;
  onVerify: () => void;
};

const RegisterEmailRow: React.FC<Props> = ({ email, setEmail, loading, onVerify }) => {
  return (
    <div className="auth-row">
      <input
        type="email"
        placeholder="Enter NTU email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="auth-input flex-1"
        inputMode="email"
        autoComplete="email"
        disabled={loading}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            onVerify();
          }
        }}
      />
      <button
        type="button"
        onClick={onVerify}
        disabled={loading}
        className="auth-row-btn disabled:opacity-60 disabled:cursor-not-allowed"
        aria-busy={loading}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <Spinner />
            <span>Sending…</span>
          </span>
        ) : (
          'Verify Email'
        )}
      </button>
    </div>
  );
};

export default RegisterEmailRow;
