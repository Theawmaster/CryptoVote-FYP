// src/hooks/useSessionTimeout.tsx
import { useEffect, useRef, useState } from "react";

type Status = {
  logged_in: boolean;
  server_now?: number;
  idle_remaining?: number;
  absolute_remaining?: number;
  warn_after_secs?: number;
};

const STATUS_URL = "/session/status";
const PING_URL   = "/session/ping";
const LOGOUT_URL = "/logout/";
const LOGIN_PATH = "/auth";

export function useSessionTimeout() {
  // ---- singleton per window (prevents StrictMode/HMR double-mount spam) ----
  const isPrimary = useRef(false);
  if (!(window as any).__cvSessionPrimary) {
    (window as any).__cvSessionPrimary = true;
    isPrimary.current = true;
  }

  const [showWarn, setShowWarn] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  const pollTimer = useRef<number | null>(null);
  const warnTimer = useRef<number | null>(null);
  const tickTimer = useRef<number | null>(null);
  const redirectingRef = useRef(false);
  const abortCtrlRef = useRef<AbortController | null>(null);

  function clearTimers() {
    if (pollTimer.current) window.clearTimeout(pollTimer.current);
    if (warnTimer.current) window.clearTimeout(warnTimer.current);
    if (tickTimer.current) window.clearInterval(tickTimer.current);
    pollTimer.current = warnTimer.current = tickTimer.current = null;
  }

  function clearAbort() {
    try { abortCtrlRef.current?.abort(); } catch {}
    abortCtrlRef.current = null;
  }

  async function fetchStatus(): Promise<Status | null> {
    if (!isPrimary.current || redirectingRef.current) return null;
    clearAbort();
    const ctrl = new AbortController();
    abortCtrlRef.current = ctrl;

    try {
      const r = await fetch(STATUS_URL, {
        credentials: "include",
        headers: { "X-Background-Poll": "1" },
        signal: ctrl.signal,
      });
      if (r.status === 401) {
        // hard stop: no more timers, abort outstanding, single redirect
        redirectingRef.current = true;
        clearTimers();
        clearAbort();
        setShowWarn(false);
        setSecondsLeft(null);
        (window as any).__cvSessionPrimary = false; // release singleton for next page
        window.location.replace(LOGIN_PATH);
        return null;
      }
      const j = await r.json();
      return j?.logged_in ? j : null;
    } catch {
      return null;
    }
  }

  async function ping() {
    if (!isPrimary.current) return;
    // close the modal immediately for snappy UX
    setShowWarn(false);
    setSecondsLeft(null);
    try {
      await fetch(PING_URL, { method: "POST", credentials: "include" });
      const s = await fetchStatus();
      planNext(s);
    } catch {
      softPoll(5);
    }
  }

  function startTicking(fromSeconds: number) {
    setSecondsLeft(fromSeconds);
    if (tickTimer.current) window.clearInterval(tickTimer.current);
    tickTimer.current = window.setInterval(() => {
      setSecondsLeft((s) => (s == null ? null : Math.max(0, s - 1)));
    }, 1000) as unknown as number;
  }

  function softPoll(nextExpiry: number) {
    const interval = nextExpiry > 30 ? 5000 : 2000;
    if (pollTimer.current) window.clearTimeout(pollTimer.current);
    pollTimer.current = window.setTimeout(async () => {
      const s = await fetchStatus();
      planNext(s);
    }, interval) as unknown as number;
  }

  function planNext(status: Status | null) {
    if (!isPrimary.current || redirectingRef.current) return;
    clearTimers();

    if (!status?.logged_in) {
      setShowWarn(false);
      setSecondsLeft(null);
      return;
    }

    const idle = Math.max(0, status.idle_remaining ?? 0);
    const abs  = Math.max(0, status.absolute_remaining ?? 0);
    const nextExpiry = Math.min(idle, abs);
    const serverWarn = status.warn_after_secs ?? 60;
    const threshold  = Math.max(30, Math.min(serverWarn, Math.max(0, nextExpiry - 5)));

    if (nextExpiry <= threshold) {
      setShowWarn(true);
      startTicking(nextExpiry);
      softPoll(nextExpiry);
      return;
    }

    const msUntilWarn = (nextExpiry - threshold) * 1000;
    warnTimer.current = window.setTimeout(async () => {
      const s = await fetchStatus();
      planNext(s);
    }, msUntilWarn) as unknown as number;

    // periodic refresh in case of clock drift / throttling
    pollTimer.current = window.setTimeout(async () => {
      const s = await fetchStatus();
      planNext(s);
    }, 15000) as unknown as number;

    setShowWarn(false);
    setSecondsLeft(null);
  }

  // lifecycle
  useEffect(() => {
    if (!isPrimary.current) return;
    let alive = true;
    (async () => {
      const s = await fetchStatus();
      if (!alive) return;
      planNext(s);
    })();
    return () => {
      alive = false;
      clearTimers();
      clearAbort();
      if (isPrimary.current) (window as any).__cvSessionPrimary = false;
    };
  }, []);

  // resync when focus/visibility changes
  useEffect(() => {
    if (!isPrimary.current) return;
    const nudge = () => { fetchStatus().then(planNext); };
    window.addEventListener("focus", nudge);
    document.addEventListener("visibilitychange", nudge);
    return () => {
      window.removeEventListener("focus", nudge);
      document.removeEventListener("visibilitychange", nudge);
    };
  }, []);

  // if countdown hits 0 while open, confirm once with server
  useEffect(() => {
    if (!isPrimary.current) return;
    if (showWarn && secondsLeft === 0) fetchStatus().then(planNext);
  }, [showWarn, secondsLeft]);

  return {
    showWarn,
    secondsLeft,
    staySignedIn: ping,
    logoutNow: () => {
      redirectingRef.current = true;
      clearTimers();
      clearAbort();
      fetch(LOGOUT_URL, { method: "POST", credentials: "include" })
        .finally(() => { (window as any).__cvSessionPrimary = false; window.location.replace(LOGIN_PATH); });
    },
  };
}
