// src/pagesfe_dev_ver_1/admin-dev/AdminLogin.tsx
import React from 'react';
import RoleSelect from '../../components/RoleSelect';
import { motion } from 'framer-motion';
import Brand from '../../components/Brand';
import '../../styles/auth.css';
import '../../styles/admin-auth.css';

const AdminLogin: React.FC = () => {
  return (
    <motion.div
      className="admin-screen"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="auth-header">
        <div className="auth-bar">
            <RoleSelect size="sm" />
        </div>
    </div>
      <div className="admin-card">
      <Brand title="Admin Developer Authentication" />
        <div className="admin-title">Admin Login</div>
        <input
          type="email"
          placeholder="Admin email"
          className="admin-input mb-3"
        />
        <div className="admin-otp-row">
          <input
            type="text"
            placeholder="OTP"
            className="admin-input flex-1"
          />
          <button className="admin-otp-btn">Get OTP</button>
        </div>
        <button className="admin-submit">Login</button>
      </div>
    </motion.div>
  );
};

export default AdminLogin;
