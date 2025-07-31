import React from 'react';
import '../styles/auth.css';
import '../styles/voter-auth.css';

type Props = { onSubmit?: () => void };

const RegisterForm: React.FC<Props> = ({ onSubmit }) => (
  <form className="space-y-3">
    <div className="text-lg font-semibold">Create Account</div>
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
      Verify & Register
    </button>
  </form>
);

export default RegisterForm;
