import { useEffect, useRef } from "react";

type Opts = {
  enabled?: boolean;
  onAttempt?: () => void;       // show toast/modal
  beforeUnloadMessage?: string; // optional native “leave site?” prompt
};

export function useBackForwardLock({
  enabled = true,
  onAttempt,
  beforeUnloadMessage,
}: Opts) {
  const armedRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    const pushFence = () => {
      try {
        // push current URL so Back goes to our fence instead of a real page
        window.history.pushState({ __bf_lock: Date.now() }, "", window.location.href);
      } catch {/* ignore */}
    };

    // arm 2 fences for reliability
    pushFence();
    setTimeout(pushFence, 0);
    armedRef.current = true;

    const handlePop = () => {
      if (!armedRef.current) return;
      // 1) notify UI
      onAttempt?.();
      // 2) cancel Back by going forward
      try { window.history.forward(); } catch {/* ignore */}
      // 3) re-arm a fresh fence
      setTimeout(pushFence, 0);
    };

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!beforeUnloadMessage) return;
      e.preventDefault();
      // required for Chrome to show prompt
      e.returnValue = beforeUnloadMessage;
      return beforeUnloadMessage;
    };

    // when restored from BFCache (Safari/Firefox), re-arm fences
    const handlePageShow = (evt: PageTransitionEvent) => {
      const persisted = (evt as any).persisted;
      if (persisted) {
        setTimeout(() => { pushFence(); pushFence(); }, 0);
      }
    };

    window.addEventListener("popstate", handlePop);
    if (beforeUnloadMessage) window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pageshow", handlePageShow as any);

    return () => {
      armedRef.current = false;
      window.removeEventListener("popstate", handlePop);
      if (beforeUnloadMessage) window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pageshow", handlePageShow as any);
    };
  }, [enabled, onAttempt, beforeUnloadMessage]);
}
