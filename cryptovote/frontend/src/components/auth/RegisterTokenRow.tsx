import React from 'react';
import Spinner from '../ui/Spinner';
import '../../styles/register-row.css'; // <-- import the new CSS

type Props = {
  token: string;
  setToken: (v: string) => void;
  loading: boolean;
  onVerify: () => void;
};

const RegisterTokenRow: React.FC<Props> = ({ token, setToken, loading, onVerify }) => {
  return (
    <div className="register-row">
      <input
        type="text"
        placeholder="Paste Token here"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        className="register-input"
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
        className="register-btn"
        aria-busy={loading}
      >
        {loading ? (
          <span className="register-btn-content">
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
