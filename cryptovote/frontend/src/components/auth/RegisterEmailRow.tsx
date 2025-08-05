import React from 'react';
import Spinner from '../ui/Spinner';
import '../../styles/register-row.css'; // <-- import the new CSS

type Props = {
  email: string;
  setEmail: (v: string) => void;
  loading: boolean;
  onVerify: () => void;
};

const RegisterEmailRow: React.FC<Props> = ({ email, setEmail, loading, onVerify }) => {
  return (
    <div className="register-row">
      <input
        type="email"
        placeholder="Enter NTU email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="register-input"
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
        className="register-btn"
        aria-busy={loading}
      >
        {loading ? (
          <span className="register-btn-content">
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
