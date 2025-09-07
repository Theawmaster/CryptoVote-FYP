// src/hooks/usePaillierKey.ts
import { useEffect, useState } from "react";
import { fetchPaillierKey } from "../services/paillier";

export function usePaillierKey(enabled: boolean) {
  const [nDec, setNDec]   = useState<string | null>(null);
  const [keyId, setKeyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!enabled) return;
      try {
        const k = await fetchPaillierKey();
        const n = BigInt("0x" + k.nHex).toString(10);
        if (alive) { setNDec(n); setKeyId(k.key_id); }
      } catch (e: any) {
        if (alive) setError(e?.message || "Failed to fetch Paillier key");
      }
    })();
    return () => { alive = false; };
  }, [enabled]);

  return { nDec, keyId, error };
}
