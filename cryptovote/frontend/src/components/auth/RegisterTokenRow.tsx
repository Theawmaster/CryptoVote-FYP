import React from 'react';
import Spinner from '../ui/Spinner';

type Props = {
  token: string;
  setToken: (v: string) => void;
  loading: boolean;
  onVerify: () => void;
};

const RegisterTokenRow: React.FC<Props> = ({ token, setToken, loading, onVerify }) => {
  return (
    <div className="auth-row">
      <input
        type="text"
        placeholder="Paste Token here"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        className="auth-input flex-1"
        inputMode="text"
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
            <span>Verifying…</span>
          </span>
        ) : (
          'Verify Token'
        )}
      </button>
    </div>
  );
};

export default RegisterTokenRow;
