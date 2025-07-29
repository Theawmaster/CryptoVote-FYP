import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import e2eLogo from '../../assets/logo/E2E_logo.gif'; 
import '../../styles/onboarding.css';

const Onboarding2: React.FC = () => {
  const navigate = useNavigate();

  return (
    <motion.div
      className="onboarding-page relative flex flex-col justify-center items-center h-screen bg-white dark:bg-gray-700 text-black dark:text-white text-center px-6"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >
      <img
        src={e2eLogo}
        alt="End-to-End Encryption Logo"
        className="w-45 md:w-56 lg:w-64 mb-10 animate-pulse"
      />

      <h2 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-300 mb-6">
        End-to-End Encryption
      </h2>

      <p className="text-base md:text-lg text-gray-700 mb-16 max-w-5xl leading-relaxed dark:text-gray-200 text-center">
        Data is encrypted from the voter's device to the server. This ensures the transaction is not compromised.
      </p>

      <div className="absolute bottom-8 flex justify-between w-full px-10">
        <button
          className="text-teal-600 px-4 py-2 rounded hover:bg-teal-500 hover:text-white transition-colors duration-200"
          onClick={() => navigate('/auth')}
        >
          Skip
        </button>
        <button
          className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-500 transition"
          onClick={() => navigate('/onboarding/3')}
        >
          Next →
        </button>
      </div>
    </motion.div>
  );
};

export default Onboarding2;
