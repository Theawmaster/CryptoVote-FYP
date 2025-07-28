import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import secureLogo from '../../assets/logo/secure.gif'; // update with actual path
import '../../styles/onboarding.css';

const Onboarding3: React.FC = () => {
  const navigate = useNavigate();

  return (
    <motion.div
      className="onboarding-page relative flex flex-col justify-center items-center h-screen bg-white text-center px-6"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >

    <div className="bg-white p-4 rounded-lg shadow-md mb-10">
        <img
            src={secureLogo}
            alt="Secure Mechanism Logo"
            className="w-44 md:w-56 lg:w-64"
        />
    </div>

      <h2 className="text-2xl md:text-3xl font-semibold text-gray-800 mb-6">
        Secure Mechanism
      </h2>

      <p className="text-base md:text-lg text-gray-700 mb-16 max-w-3xl leading-relaxed text-left">
        State of the art cryptography methods like <span className="font-medium">homomorphic encryption</span>,
        <span className="font-medium">blind signature</span>, <span className="font-medium"> zero-knowledge proofs </span>
        and more to ensure the security and integrity of the voting process.
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
          onClick={() => navigate('/onboarding/4')}
        >
          Next →
        </button>
      </div>
    </motion.div>
  );
};

export default Onboarding3;
