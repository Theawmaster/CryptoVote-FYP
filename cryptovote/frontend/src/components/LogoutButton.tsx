import React from 'react';
import { useNavigate } from 'react-router-dom';
import Toast from './ui/Toast';

const LogoutButton: React.FC<{ onLogoutSuccess?: () => void }> = ({ onLogoutSuccess }) => {
  const navigate = useNavigate();
  const [toast, setToast] = React.useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [busy, setBusy] = React.useState(false); // prevent double-clicks

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const handleLogout = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await fetch('/logout/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({}),
      });

      // Try to parse JSON safely
      let data: any = {};
      try { data = await res.json(); } catch { /* ignore */ }

      if (!res.ok) throw new Error(data?.error || 'Logout failed');

      showToast('success', 'Logout successful');
      onLogoutSuccess?.();

      // Give the toast a moment, then navigate
      setTimeout(() => {
        navigate('/auth/admin', { replace: true });
      }, 600);
    } catch (e) {
      showToast('error', 'Error logging out');
      setBusy(false);
    }
  };

  return (
    <>
      <button className="auth-submit danger" onClick={handleLogout} disabled={busy}>
        {busy ? 'Logging out…' : 'Log Out'}
      </button>
      {toast && (
        <Toast
          type={toast.type}
          message={toast.msg}
          duration={3000}
          onClose={() => setToast(null)}
        />
      )}
    </>
  );
};

export default LogoutButton;
