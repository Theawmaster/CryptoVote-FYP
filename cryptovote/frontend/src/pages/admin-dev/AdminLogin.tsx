// src/pagesfe_dev_ver_1/admin-dev/AdminLogin.tsx
import React from 'react';
import RoleSelect from '../../components/RoleSelect';
import { motion } from 'framer-motion';
import ntuLogo from '../../assets/logo/ntu_logo.png';
import cryptovoteLogo from '../../assets/logo/cryptovote_logo.png';
import '../../styles/auth.css';

const Brand: React.FC = () => (
    <div className="mb-6 text-center">
      {/* Use valid Tailwind sizes (w-42 doesn't exist) */}
      <img
        src={ntuLogo}
        alt="NTU Logo"
        className="mx-auto h-auto w-40 sm:w-44 md:w-48"
      />
      <img
        src={cryptovoteLogo}
        alt="CryptoVote Logo"
        className="mx-auto mt-3 h-auto w-24 sm:w-28 md:w-32"
      />
      <div className="mt-3 text-2xl md:text-3xl font-bold tracking-tight">
        Admin Developer Authentication
      </div>
    </div>
  );

const AdminLogin: React.FC = () => {
  return (
    <motion.div
      className="relative min-h-screen flex items-center justify-center bg-white dark:bg-gray-700 text-black dark:text-white px-4"
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
    >
      <div className="auth-header">
        <div className="auth-bar">
            <RoleSelect size="sm" />
        </div>
    </div>
      <div className="w-full max-w-md rounded-2xl shadow-xl p-8 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-700">
      <Brand />
        <div className="text-xl font-semibold mb-4">Admin Login</div>
        <input
          type="email"
          placeholder="Admin email"
          className="w-full mb-3 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
        />
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="OTP"
            className="flex-1 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800"
          />
          <button className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-700">Get OTP</button>
        </div>
        <button className="w-full py-2 rounded bg-teal-600 text-white hover:bg-teal-500">Login</button>
      </div>
    </motion.div>
  );
};

export default AdminLogin;
