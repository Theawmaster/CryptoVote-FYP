// src/hooks/useVoterMe.ts
import { useEffect, useState } from 'react';
import { getJSON } from '../services/voter/http';

export function useVoterMe<T = any>() {
  const [me, setMe] = useState<T | null>(null);
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await getJSON<T>('/whoami');
        if (alive) setMe(data);
      } catch {
        if (alive) setMe(null);
      }
    })();
    return () => { alive = false; };
  }, []);
  return me;
}
