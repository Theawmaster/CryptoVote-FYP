import { useCallback, useEffect, useState } from 'react';
import { getElectionStatus } from '../services/admin/electionActions';
import type { ElectionStatus } from '../services/admin/types';

export function useElectionStatus(electionId: string) {
  const [status, setStatus] = useState<ElectionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const s = await getElectionStatus(electionId);
      setStatus(s);
    } finally {
      setLoading(false);
    }
  }, [electionId]);

  useEffect(() => { if (electionId) { void refresh(); } }, [electionId, refresh]);

  return { status, loading, refresh };
}
