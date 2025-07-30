import React from 'react';

type Props = { onSubmit?: () => void };

const RegisterForm: React.FC<Props> = ({ onSubmit }) => (
  <form className="space-y-3">
    <div className="text-lg font-semibold">Create Account</div>
    <input
      type="email"
      placeholder="Enter NTU email"
      className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
    />
    <div className="flex gap-2">
      <input
        type="text"
        placeholder="Enter OTP"
        className="flex-1 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
      />
      <button type="button" className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-700">
        Get OTP
      </button>
    </div>
    <button
      type="button"
      onClick={onSubmit}
      className="w-full py-2 rounded bg-teal-600 text-white hover:bg-teal-500"
    >
      Verify & Register
    </button>
  </form>
);

export default RegisterForm;
