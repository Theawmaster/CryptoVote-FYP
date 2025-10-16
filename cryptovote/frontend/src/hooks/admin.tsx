import { useEffect, useMemo, useRef, useState } from 'react';
import { apiGet } from '../services/api';
import type { AdminMe, Election, Suspicious } from '../services/admin/types';

export function useAdminMe() {
  const [me, setMe] = useState<AdminMe | null>(null);
  useEffect(() => { (async () => {
    try { setMe(await apiGet<AdminMe>('/admin/me')); } catch {}
  })(); }, []);
  // tick every 60s so relative time updates
  const [, setTick] = useState(0);
  useEffect(() => { const id = setInterval(()=>setTick(t=>t+1), 60000); return ()=>clearInterval(id); }, []);
  return me;
}

export function useElections() {
  const [data, setData] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const c = new AbortController();
    abortRef.current = c;

    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const res = await apiGet<{ elections: Election[] }>('/admin/elections', { signal: c.signal });
        setData(res.elections || []);
      } catch (e: any) {
        if (
          e.name === 'AbortError' ||
          e.code === 'CANCELLED' ||
          e.message === 'Request cancelled.'
        )
          return; // ignore cancel/abort
        setErr(e.message || 'Failed to load elections');
      } finally {
        setLoading(false);
      }
    })();

    return () => c.abort();
  }, []);

  return { data, loading, err };
}

export function useSuspicious() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<Suspicious[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  async function refreshCount() {
    try { const r = await apiGet<{count: number}>('/admin/security/suspicious/count'); setCount(r.count ?? 0); }
    catch {}
  }
  async function loadList() {
    setLoading(true);
    try { const r = await apiGet<{items: Suspicious[]}>('/admin/security/suspicious?limit=50'); setItems(r.items ?? []); }
    catch { setItems([]); }
    setLoading(false);
  }

  useEffect(() => {
    refreshCount();
    const id = setInterval(refreshCount, 15000);
    return () => clearInterval(id);
  }, []);

  return { count, items, open, setOpen, loading, loadList };
}
