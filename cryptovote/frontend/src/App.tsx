import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { FaMoon, FaSun } from 'react-icons/fa6';
import OnboardingLandingPage from './pages/onboarding/OnboardingLandingPage';
import Onboarding1 from './pages/onboarding/Onboarding1';
import Onboarding2 from './pages/onboarding/Onboarding2';
import Onboarding3 from './pages/onboarding/Onboarding3';
import Onboarding4 from './pages/onboarding/Onboarding4';

import VoterAuth from './pages/voter/VoterAuth';
import AdminLogin from './pages/admin-dev/AdminLogin';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<OnboardingLandingPage />} />
        <Route path="/onboarding/1" element={<Onboarding1 />} />
        <Route path="/onboarding/2" element={<Onboarding2 />} />
        <Route path="/onboarding/3" element={<Onboarding3 />} />
        <Route path="/onboarding/4" element={<Onboarding4 />} />

        <Route path="/auth" element={<VoterAuth />} />
        <Route path="/auth/voter" element={<VoterAuth />} />
        <Route path="/auth/admin" element={<AdminLogin />} />
      </Routes>
    </AnimatePresence>
  );
}

const MoonIcon = FaMoon as unknown as React.FC<{ size?: number }>;
const SunIcon = FaSun as unknown as React.FC<{ size?: number }>;

function App() {

  const [darkMode, setDarkMode] = useState(false);

  // Load dark mode preference from localStorage on initial render
  useEffect(() => {
    const stored = localStorage.getItem('darkMode');
    if (stored === 'true') 
      setDarkMode(true); 
    }, []);

  // Save dark mode preference to localStorage whenever it changes
  useEffect(() => {
    const html = document.documentElement;
    if (darkMode) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  
  return (
    <Router>
      <div className="relative min-h-screen bg-white dark:bg-gray-900 text-black dark:text-white transition-colors duration-300">
        {/* Toggle Button */}
        <button
          className="absolute top-4 right-4 z-50 w-16 h-8 
          bg-gray-300 hover:bg-teal-500 
          dark:bg-gray-400 dark:hover:bg-teal-400 
          rounded-full flex items-center px-1 shadow-inner transition-all"        
          onClick={() => setDarkMode(!darkMode)}
        >
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center text-white transform transition-transform duration-300 ${
              darkMode ? 'translate-x-8 bg-gray-300 text-gray-800' : 'bg-yellow-400 text-yellow-800'
            }`}
          >
            {darkMode ? <MoonIcon size={20} /> : <SunIcon size={20} />}
          </div>
        </button>

        <AnimatedRoutes />
      </div>
    </Router>
  );
}

export default App;
