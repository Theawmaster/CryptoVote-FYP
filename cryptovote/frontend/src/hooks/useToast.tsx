import { useCallback, useState } from 'react';

export type ToastState = { type: 'success'|'error'|'info'; msg: string } | null;

export function useToast() {
  const [toast, setToast] = useState<ToastState>(null);
  const show = useCallback((type: 'success'|'error'|'info', msg: string, ms = 3000) => {
    setToast({ type, msg });
    window.setTimeout(() => setToast(null), ms);
  }, []);
  return { toast, show, clear: () => setToast(null) };
}
