import React, { useState } from 'react';
import { motion, AnimatePresence, Variants } from 'framer-motion';
import RoleSelect from '../../components/RoleSelect';
import Brand from '../../components/Brand';
import registerLogo from '../../assets/logo/register.gif';
import loginLogo from '../../assets/logo/login.gif';
import RegisterForm from '../../components/RegisterForm';
import LoginForm from '../../components/LoginForm';
import '../../styles/auth.css';
import '../../styles/voter-auth.css';
// import ConfirmationModal from '../../components/auth/ConfirmationModal';
import ContactUsButton from '../../services/ContactUsButton';

type Mode = 'register' | 'login';

const LoginCTA: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <div className="auth-panel">
    <Brand title="Voter Authentication" />
    <h2 className="auth-h2">Welcome back!</h2>
    <p className="auth-copy">
      Click the button below to get yourself logged in to start voting!
    </p>
    <button
      onClick={onClick}
      className="auth-cta"
    >
      Go to log in
    </button>
    <ContactUsButton />
  </div>
);

const RegisterCTA: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <div className="auth-panel">
    <Brand title="Voter Authentication" />
    <h2 className="auth-h2">Welcome onboard!</h2>
    <p className="auth-copy">
      Click the button below to register and cast your vote safely with us!
    </p>
    <button
      onClick={onClick}
      className="auth-cta"
    >
      Go to register
    </button>
    <ContactUsButton />
  </div>
);

const VoterAuth: React.FC = () => {
  const [mode, setMode] = useState<Mode>('register');

  // Glass covers the INACTIVE side.
  const overlayX = mode === 'register' ? '0%' : '100%';
  const overlaySideClass =
    mode === 'register' ? 'auth-overlay--left' : 'auth-overlay--right';

  // Page transition variants
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
      className="auth-screen"
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
      <div className="auth-split">
        {/* LEFT PANEL */}
        <section className="auth-pane auth-pane--left">
          {mode === 'register' ? (
            // Register mode → left shows CTA to log in
            <LoginCTA onClick={() => setMode('login')} />
          ) : (
            // Login mode → left shows the Login form
            <div className="auth-panel">
              <img
                src={loginLogo}
                alt="Register Logo"
                className="auth-illust"
              />
              <LoginForm />
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
            <div className="auth-panel">
              <img
                src={registerLogo}
                alt="Register Logo"
                className="auth-illust"
              />
              <RegisterForm onSubmit={() => console.log('register submit')} />
              <p className="auth-subtle mt-4">
                Upon verification of token, please proceed to log in.
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
            className="auth-overlay-wrap"
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
