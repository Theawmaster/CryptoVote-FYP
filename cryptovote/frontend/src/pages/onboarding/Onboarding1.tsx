import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import '../../styles/onboarding.css';

import intuitiveLogo from '../../assets/logo/onboarding.gif'; 

const Onboarding1: React.FC = () => {
  const navigate = useNavigate();

  return (
    <motion.div
      className="onboarding-landing relative flex flex-col justify-center items-center h-screen bg-white dark:bg-gray-700 text-black dark:text-white text-center px-6"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >
      <img
        src={intuitiveLogo}
        alt="Intuitive Logo"
        className="w-40 md:w-56 lg:w-64 mb-10 animate-bounce"
      />

      <h2 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-300 mb-6">Intuitive Process</h2>

      <ol className="text-base md:text-lg text-gray-700 space-y-4 mb-16 max-w-2xl text-left dark:text-gray-200 leading-relaxed">
        <li>1. Log in to begin voting process or register if you don't have an account.</li>
        <li>2. Click on your preferred candidate then submit it.</li>
        <li>3. Entire process would take less than 10 minutes.</li>
      </ol>

      <div className="absolute bottom-8 flex justify-between w-full px-10">
        <button
          className="text-teal-600 px-4 py-2 rounded hover:bg-teal-500 hover:text-white transition-colors duration-200"
          onClick={() => navigate('/auth')}
        >
          Skip
        </button>
        <button
          className="bg-teal-600 text-white px-4 py-2 rounded hover:bg-teal-500"
          onClick={() => navigate('/onboarding/2')}
        >
          Next →
        </button>
      </div>
    </motion.div>
  );
};

export default Onboarding1;
