import React, { useState } from 'react';
import { motion, AnimatePresence, Variants } from 'framer-motion';
import RoleSelect from '../../components/RoleSelect';
import ntuLogo from '../../assets/logo/ntu_logo.png';
import registerLogo from '../../assets/logo/register.gif';
import loginLogo from '../../assets/logo/login.gif';
import cryptovoteLogo from '../../assets/logo/cryptovote_logo.png';
import RegisterForm from './RegisterForm';
import LoginForm from './LoginForm';
import '../../styles/auth.css';

type Mode = 'register' | 'login';

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
      Voter Authentication
    </div>
  </div>
);

const LoginCTA: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <div className="w-full max-w-md relative z-20">
    <Brand />
    <h2 className="text-2xl md:text-3xl font-semibold mb-4">Welcome back!</h2>
    <p className="text-sm md:text-base text-gray-600 dark:text-gray-300 mb-6">
      Click the button below to get yourself logged in to start voting.
    </p>
    <button
      onClick={onClick}
      className="px-5 py-2 rounded bg-teal-600 text-white hover:bg-teal-700"
    >
      Log in
    </button>
  </div>
);

const RegisterCTA: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <div className="w-full max-w-md relative z-20">
    <Brand />
    <h2 className="text-2xl md:text-3xl font-semibold mb-4">Welcome onboard!</h2>
    <p className="text-sm md:text-base text-gray-600 dark:text-gray-300 mb-6">
      Click the button below to register and cast your vote safely with us!
    </p>
    <button
      onClick={onClick}
      className="px-5 py-2 rounded bg-teal-600 text-white hover:bg-teal-700"
    >
      Register
    </button>
  </div>
);

const VoterAuth: React.FC = () => {
  const [mode, setMode] = useState<Mode>('register');

  // Glass covers the INACTIVE side.
  const overlayX = mode === 'register' ? '0%' : '100%';
  const overlaySideClass =
    mode === 'register' ? 'auth-overlay--left' : 'auth-overlay--right';

  // Type the variants so 'spring' stays a literal, not widened to string
  const pageVariants: Variants = {
    initial: { x: 24},
    animate: {
      x: 0,
      transition: { type: 'spring', stiffness: 120, damping: 20, mass: 0.7 },
    },
    exit: {
      x: -24,
      transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
    },
  };

  return (
    <motion.div
      className="relative h-screen w-screen overflow-hidden bg-white dark:bg-gray-700 text-black dark:text-white"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {/* Centered control bar: Role tab */}
      <div className="auth-header">
        <div className="auth-bar">
          <RoleSelect size="sm" />
          {/* if you want Register/Login tabs here, add them on the right */}
        </div>
      </div>

      {/* FULL PAGE SPLIT */}
      <div className="relative grid grid-rows-[1fr,1fr] md:grid-rows-1 md:grid-cols-2 h-full w-full">
        {/* LEFT PANEL */}
        <section className="auth-pane auth-pane--left">
          {mode === 'register' ? (
            // Register mode → left shows CTA to log in
            <LoginCTA onClick={() => setMode('login')} />
          ) : (
            // Login mode → left shows the Login form
            <div className="w-full max-w-md relative z-20">
              <img
                src={loginLogo}
                alt="Register Logo"
                className="mx-auto h-auto w-40 sm:w-44 md:w-48"
              />
              <LoginForm onSubmit={() => console.log('login submit')} />
              <p className="auth-subtle mt-4">
                Returning voters can log in directly with OTP.
              </p>
            </div>
          )}
        </section>

        {/* RIGHT PANEL */}
        <section className="auth-pane auth-pane--right">
          {mode === 'register' ? (
            // Register mode → right has Register form
            <div className="w-full max-w-md relative z-20">
              <img
                src={registerLogo}
                alt="Register Logo"
                className="mx-auto h-auto w-40 sm:w-44 md:w-48"
              />
              <RegisterForm onSubmit={() => console.log('register submit')} />
              <p className="auth-subtle mt-4">
                Only NTU emails are allowed. OTP will be sent to your inbox.
              </p>
            </div>
          ) : (
            // Login mode → right shows CTA to register
            <RegisterCTA onClick={() => setMode('register')} />
          )}
        </section>

        {/* Sliding glass overlay (kept BELOW content) */}
        <AnimatePresence initial={false} mode="wait">
          <motion.div
            key={mode}
            className="absolute inset-y-0 left-0 hidden md:block md:w-1/2 pointer-events-none z-10"
            initial={{ x: mode === 'register' ? '100%' : '0%' }}
            animate={{ x: overlayX }}
            exit={{ opacity: 0 }}
            transition={{ type: 'tween', duration: 0.25, ease: 'easeInOut' }}
          >
            <div className={`auth-overlay ${overlaySideClass}`} />
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default VoterAuth;
