// src/App.tsx
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
import AdminLanding from './pages/admin-dev/AdminLandingPage';
import AdminElectionPage from './pages/admin-dev/AdminElectionPage';

import VoterLandingPage from './pages/voter/VoterLandingPage';
import VoterBallotPage from './pages/voter/VoterBallotPage';
import VoteCompletePage from './pages/voter/VoteCompletePage';

import { CredentialProvider } from './ctx/CredentialContext';
import { useSessionTimeout } from './hooks/useSessionTimeout';

// import the modal styles ONCE (global)
import './styles/session-timeout.css';

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

        <Route path="/admin/landing" element={<AdminLanding />} />
        <Route path="/admin/manage/:electionId" element={<AdminElectionPage />} />

        <Route path="/voter" element={<VoterLandingPage />} />
        <Route path="/voter/elections/:id" element={<VoterBallotPage />} />
        <Route path="/voter/elections/:id/complete" element={<VoteCompletePage />} />
      </Routes>
    </AnimatePresence>
  );
}

const MoonIcon = FaMoon as unknown as React.FC<{ size?: number }>;
const SunIcon  = FaSun  as unknown as React.FC<{ size?: number }>;

export default function App() {
  const [darkMode, setDarkMode] = useState(false);

  // --- session timeout hook (frontend idle + absolute timer) ---
  const { showWarn, secondsLeft, staySignedIn, logoutNow } = useSessionTimeout();

  // load dark preference
  useEffect(() => {
    const stored = localStorage.getItem('darkMode');
    if (stored === 'true') setDarkMode(true);
  }, []);

  // apply + persist dark preference
  useEffect(() => {
    const html = document.documentElement;
    if (darkMode) html.classList.add('dark');
    else html.classList.remove('dark');
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  return (
    <CredentialProvider>
      <Router>
        <div className="relative min-h-screen bg-white dark:bg-gray-900 text-black dark:text-white transition-colors duration-300">
          {/* Theme toggle */}
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

          {/* Routes */}
          <AnimatedRoutes />

          {/* Session timeout modal (appears above all routes) */}
          {showWarn && (
            <div
              className="session-modal-backdrop"
              role="dialog"
              aria-modal="true"
              onKeyDown={(e) => {
                if (e.key === 'Escape') staySignedIn();
              }}
            >
              <div className="session-modal">
                <h3>Stay signed in?</h3>
                <p>
                  Your session will expire in <b>{secondsLeft ?? 60}</b> seconds due to inactivity.
                </p>
                <div className="session-actions">
                  <button className="btn btn-outline" onClick={logoutNow}>Log out</button>
                  <button className="btn btn-primary" onClick={staySignedIn}>Stay signed in</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </Router>
    </CredentialProvider>
  );
}
