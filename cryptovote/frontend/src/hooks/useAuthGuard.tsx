// hooks/useAuthGuard.ts
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function useEnsureVoter(redirectTo: string = '/auth') {
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    const kickToLogin = async (msg: string) => {
      // 1) stash toast for the login page
      sessionStorage.setItem('toast.msg', msg);
      sessionStorage.setItem('toast.kind', 'info'); // or 'error'

      // 2) try to flip DB flags + clear server session
      try {
        // if your /logout/ requires email for voters, pull from localStorage
        const email = localStorage.getItem('voterEmail') || undefined;
        await fetch('/logout/', {
          method: 'POST',
          credentials: 'include',
          keepalive: true,
          headers: email ? { 'Content-Type': 'application/json' } : undefined,
          body: email ? JSON.stringify({ email }) : undefined,
        }).catch(() => {});
      } finally {
        if (!cancelled) navigate(redirectTo, { replace: true });
      }
    };

    (async () => {
      try {
        let r = await fetch('/whoami', { credentials: 'include' });
        if (r.status === 503) {
          // transient DB disconnect; quick retry
          await new Promise(res => setTimeout(res, 350));
          r = await fetch('/whoami', { credentials: 'include' });
        }
        const j = await r.json().catch(() => ({}));
        const ok = r.ok && j.role === 'voter' && j.twofa === true;
        if (!ok) return kickToLogin('You have been logged out. Please sign in again.');
      } catch {
        return kickToLogin('You have been logged out. Please sign in again.');
      }
    })();

    return () => { cancelled = true; };
  }, [navigate, redirectTo]);
}
