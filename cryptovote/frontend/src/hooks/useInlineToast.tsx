// src/hooks/useInlineToast.ts
import { useCallback, useRef, useState } from 'react';

export type Toast = { type: 'info' | 'error' | 'success'; msg: string } | null;

export function useInlineToast() {
  const [toast, setToast] = useState<Toast>(null);
  const tRef = useRef<number | null>(null);

  const show = useCallback((type: 'info' | 'error' | 'success', msg: string) => {
    setToast({ type, msg });
    if (tRef.current) window.clearTimeout(tRef.current);
    tRef.current = window.setTimeout(() => setToast(null), 3200);
  }, []);

  return { toast, show };
}
