import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import verificationGif from '../../assets/logo/verified.gif';
import '../../styles/onboarding.css';

const Onboarding4: React.FC = () => {
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
        src={verificationGif}
        alt="Verification"
        className="w-44 md:w-56 lg:w-64 mb-10 rounded-xl shadow-lg bg-white dark:bg-gray-700"
      />
        <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-300">Two Factor Authentication</h2>
        <p className="text-gray-600 max-w-xl mb-10 text-sm md:text-base dark:text-gray-200">
            Email with One-Time Password (OTP) is used to ensure only you are accessing the voting system.
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
                onClick={() => navigate('/auth')}
                >
                Next →
                </button>
            </div>
    </motion.div>
  );
};

export default Onboarding4;
