
import React from 'react';
import '../styles/auth.css';
import '../styles/voter-auth.css';

type Props = { onSubmit?: () => void };

const LoginForm: React.FC<Props> = ({ onSubmit }) => (
  <form className="auth-form">
    <div className="auth-form-title">Welcome back</div>
    <input
      type="email"
      placeholder="Enter NTU email"
      className="auth-input"
    />
    <div className="auth-row">
      <input
        type="text"
        placeholder="Enter OTP"
        className="auth-input flex-1"
      />
      <button type="button" className="auth-row-btn">
        Get OTP
      </button>
    </div>
    <button
      type="button"
      onClick={onSubmit}
      className="auth-submit"
    >
      Login
    </button>
  </form>
);

export default LoginForm;
