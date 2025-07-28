import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import ntuLogo from '../../assets/logo/ntu_logo.png';
import cryptovoteLogo from '../../assets/logo/cryptovote_logo.png';
import '../../styles/onboarding.css';

const OnboardingLandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/onboarding/1');
  };

  return (
    <motion.div
      onClick={handleClick}
      className="relative flex flex-col justify-center items-center h-screen bg-white cursor-pointer"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6, ease: 'easeInOut' }}
    >
      <img src={ntuLogo} alt="NTU Logo" className="w-32 mb-4" />
      <img src={cryptovoteLogo} alt="CryptoVote Logo" className="w-40" />
      <p className="absolute bottom-10 text-gray-600 italic text-sm md:text-base">
        Click anywhere to continue
      </p>
    </motion.div>
  );
};

export default OnboardingLandingPage;
